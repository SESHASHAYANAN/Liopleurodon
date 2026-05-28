"""
Liopleurodon — Job Refresh Script
1. Deactivate expired jobs (>21 days old)
2. Scrape real jobs from live APIs
3. Backfill with generated jobs to reach 2000+
"""

import asyncio, sys, os, hashlib, re, random
from services.ats_detector import detect_ats_from_url, COMPANY_ATS_MAP
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import httpx
from datetime import datetime, timezone, timedelta
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
db = create_client(SUPABASE_URL, SUPABASE_KEY)

TARGET = 2100
EXPIRY_DAYS = 21
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def ntxt(text):
    if not text: return ""
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9\s]', '', text.lower().strip()))

def dhash(company, title, city):
    return hashlib.sha256("|".join([ntxt(company), ntxt(title), ntxt(city or ""), ""]).encode()).hexdigest()

def classify_exp(title):
    t = title.lower()
    if any(k in t for k in ["intern", "fresher", "trainee"]): return "intern"
    if any(k in t for k in ["junior", "jr.", "associate", "entry level", "graduate", "new grad"]): return "junior"
    if any(k in t for k in ["senior", "sr.", "lead", "principal", "architect"]): return "senior"
    if any(k in t for k in ["staff", "vp", "director", "head of", "chief"]): return "staff"
    return "mid"

def classify_remote(text):
    if not text: return "onsite"
    t = text.lower()
    if any(k in t for k in ["remote", "wfh", "anywhere"]):
        return "hybrid" if "hybrid" in t else "remote"
    return "hybrid" if "hybrid" in t else "onsite"

def first_sentence(text):
    if not text: return ""
    text = re.sub(r'<[^>]+>', '', text).strip()
    text = re.sub(r'\s+', ' ', text).strip()
    m = re.match(r'^(.+?[.!?])\s', text)
    return m.group(1)[:300] if m else text[:300]

def count_active():
    return db.table("jobs").select("id", count="exact").eq("is_active", True).execute().count or 0


# ══════════════════════════════════════════════════
# STEP 1: Deactivate expired jobs
# ══════════════════════════════════════════════════
def deactivate_expired():
    print("\n[STEP 1] Deactivating expired jobs (>21 days old)...")
    cutoff = (datetime.now(timezone.utc) - timedelta(days=EXPIRY_DAYS)).isoformat()
    now = datetime.now(timezone.utc).isoformat()
    deactivated = 0
    offset = 0
    while True:
        batch = (db.table("jobs").select("id")
                .eq("is_active", True)
                .lt("posted_date", cutoff)
                .range(offset, offset + 99)
                .execute())
        if not batch.data:
            break
        for job in batch.data:
            try:
                db.table("jobs").update({"is_active": False, "updated_at": now}).eq("id", job["id"]).execute()
                deactivated += 1
            except:
                pass
        if deactivated % 50 == 0 and deactivated > 0:
            print(f"  Deactivated {deactivated} so far...")
    print(f"  Deactivated {deactivated} expired jobs.")
    return deactivated


# ══════════════════════════════════════════════════
# STEP 2: Scrape real jobs from live APIs
# ══════════════════════════════════════════════════

async def scrape_adzuna(client, country, country_code, queries):
    jobs = []
    for q in queries:
        try:
            r = await client.get(
                f"https://api.adzuna.com/v1/api/jobs/{country_code}/search/1",
                params={
                    "app_id": os.environ.get("ADZUNA_APP_ID", "9f668b2e"),
                    "app_key": os.environ.get("ADZUNA_API_KEY", "66f090e012038a74211f9b874f473e92"),
                    "what": q, "results_per_page": 25, "sort_by": "date",
                    "content-type": "application/json",
                },
                headers=HEADERS, timeout=20,
            )
            for item in (r.json().get("results") or []):
                url = item.get("redirect_url", "")
                if not url: continue
                title = item.get("title", "")
                company = (item.get("company") or {}).get("display_name", "")
                location = (item.get("location") or {}).get("display_name", country)
                if title and company:
                    jobs.append({
                        "title": title, "company": company, "location": location,
                        "url": url, "desc": first_sentence(item.get("description", "")),
                        "tags": [], "posted": item.get("created", ""),
                        "source": f"Adzuna-{country_code.upper()}",
                        "remote": classify_remote(title + " " + location),
                        "salary_min": item.get("salary_min"),
                        "salary_max": item.get("salary_max"),
                        "salary_currency": "INR" if country_code == "in" else ("USD" if country_code == "us" else "GBP"),
                    })
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"  [Adzuna-{country_code}/{q}] {e}")
    return jobs

async def scrape_remotive(client):
    jobs = []
    for cat in ["software-dev", "data", "devops-sysadmin", "product", "design",
                 "marketing", "customer-support", "finance-legal", "human-resources"]:
        try:
            r = await client.get("https://remotive.com/api/remote-jobs",
                                params={"category": cat, "limit": 50}, headers=HEADERS, timeout=20)
            for item in (r.json().get("jobs") or []):
                url = item.get("url", "")
                if not url: continue
                title = item.get("title", "")
                company = item.get("company_name", "")
                if title and company:
                    jobs.append({
                        "title": title, "company": company,
                        "location": item.get("candidate_required_location", "Remote"),
                        "url": url, "desc": first_sentence(item.get("description", "")),
                        "tags": item.get("tags") or [], "posted": item.get("publication_date", ""),
                        "source": "Remotive", "remote": "remote"
                    })
            await asyncio.sleep(1)
        except Exception as e:
            print(f"  [Remotive/{cat}] {e}")
    return jobs

async def scrape_remoteok(client):
    jobs = []
    try:
        r = await client.get("https://remoteok.com/api",
                            headers={**HEADERS, "Accept": "application/json"}, timeout=20)
        for item in r.json()[1:]:
            url = item.get("url", item.get("apply_url", ""))
            if not url: continue
            title = item.get("position", "")
            company = item.get("company", "")
            if title and company:
                jobs.append({
                    "title": title, "company": company,
                    "location": item.get("location", "Remote"),
                    "url": url, "desc": first_sentence(item.get("description", "")),
                    "tags": [t for t in (item.get("tags") or []) if isinstance(t, str)],
                    "posted": item.get("date", ""), "source": "RemoteOK", "remote": "remote"
                })
    except Exception as e:
        print(f"  [RemoteOK] {e}")
    return jobs

async def scrape_arbeitnow(client):
    jobs = []
    for page in range(1, 6):
        try:
            r = await client.get("https://www.arbeitnow.com/api/job-board-api",
                                params={"page": page}, headers=HEADERS, timeout=20)
            for item in (r.json().get("data") or []):
                url = item.get("url", "")
                if not url: continue
                title = item.get("title", "")
                company = item.get("company_name", "")
                if title and company:
                    jobs.append({
                        "title": title, "company": company, "location": item.get("location", ""),
                        "url": url, "desc": first_sentence(item.get("description", "")),
                        "tags": item.get("tags") or [], "posted": "",
                        "source": "Arbeitnow", "remote": "remote" if item.get("remote") else "onsite"
                    })
            await asyncio.sleep(1)
        except Exception as e:
            print(f"  [Arbeitnow/p{page}] {e}")
    return jobs

async def scrape_jobicy(client):
    jobs = []
    for tag in ["software-dev", "data-science", "devops", "machine-learning", "marketing", "design"]:
        try:
            r = await client.get("https://jobicy.com/api/v2/remote-jobs",
                                params={"count": 50, "tag": tag}, headers=HEADERS, timeout=20)
            for item in (r.json().get("jobs") or []):
                url = item.get("url", "")
                if not url: continue
                title = item.get("jobTitle", "")
                company = item.get("companyName", "")
                if title and company:
                    jobs.append({
                        "title": title, "company": company,
                        "location": item.get("jobGeo", "Remote"),
                        "url": url, "desc": first_sentence(item.get("jobExcerpt", "")),
                        "tags": [], "posted": item.get("pubDate", ""),
                        "source": "Jobicy", "remote": "remote"
                    })
            await asyncio.sleep(1)
        except Exception as e:
            print(f"  [Jobicy/{tag}] {e}")
    return jobs

async def scrape_himalayas(client):
    jobs = []
    try:
        r = await client.get("https://himalayas.app/jobs/api",
                            params={"limit": 50}, headers=HEADERS, timeout=20)
        for item in (r.json().get("jobs") or []):
            url = item.get("applicationLink", item.get("url", ""))
            if not url: continue
            title = item.get("title", "")
            company = item.get("companyName", item.get("company_name", ""))
            if title and company:
                jobs.append({
                    "title": title, "company": company,
                    "location": item.get("location", "Remote"),
                    "url": url, "desc": first_sentence(item.get("description", "")),
                    "tags": item.get("categories") or [], "posted": "",
                    "source": "Himalayas", "remote": "remote"
                })
    except Exception as e:
        print(f"  [Himalayas] {e}")
    return jobs

async def scrape_findwork(client):
    jobs = []
    api_key = os.environ.get("FINDWORK_API_KEY", "")
    if not api_key:
        return jobs
    for search in ["python", "javascript", "react", "machine learning", "data"]:
        try:
            r = await client.get("https://findwork.dev/api/jobs/",
                                params={"search": search, "sort_by": "date"},
                                headers={**HEADERS, "Authorization": f"Token {api_key}"}, timeout=20)
            for item in (r.json().get("results") or []):
                url = item.get("url", "")
                if not url: continue
                title = item.get("role", "")
                company = item.get("company_name", "")
                if title and company:
                    jobs.append({
                        "title": title, "company": company,
                        "location": item.get("location", "Remote"),
                        "url": url, "desc": first_sentence(item.get("text", "")),
                        "tags": item.get("keywords") or [], "posted": item.get("date_posted", ""),
                        "source": "FindWork", "remote": "remote" if item.get("remote") else "onsite"
                    })
            await asyncio.sleep(1)
        except Exception as e:
            print(f"  [FindWork/{search}] {e}")
    return jobs


# ══════════════════════════════════════════════════
# STEP 3: Insert scraped jobs
# ══════════════════════════════════════════════════
def insert_scraped(raw_jobs):
    print(f"\n[STEP 3] Deduplicating and inserting {len(raw_jobs)} scraped jobs...")
    now = datetime.now(timezone.utc).isoformat()
    inserted = 0
    skipped = 0
    seen = set()

    for j in raw_jobs:
        h = dhash(j["company"], j["title"], j.get("location", "").split(",")[0].strip())
        if h in seen:
            skipped += 1
            continue
        seen.add(h)

        city = j.get("location", "").split(",")[0].strip()
        country = j.get("location", "").split(",")[-1].strip() if "," in j.get("location", "") else ""
        exp = classify_exp(j["title"])
        remote = j.get("remote", classify_remote(j.get("location", "") + " " + j["title"]))

        record = {
            "title": j["title"].strip(),
            "company_name": j["company"].strip(),
            "location_city": city or None,
            "location_country": country or None,
            "apply_url": j["url"],
            "description": j.get("desc") or f"{j['title']} at {j['company']}",
            "experience_level": exp,
            "job_type": "internship" if exp == "intern" else "full-time",
            "remote_type": remote,
            "visa_sponsorship": False,
            "relocation_support": False,
            "company_type": "startup",
            "source_platforms": [j["source"]],
            "is_active": True,
            "is_stealth": False,
            "dedup_hash": h,
            "posted_date": j.get("posted") or now,
            "created_at": now,
            "updated_at": now,
        }
        if j.get("tags"):
            record["tech_stack"] = j["tags"][:10]
        if j.get("salary_min"):
            record["salary_min"] = j["salary_min"]
        if j.get("salary_max"):
            record["salary_max"] = j["salary_max"]
        if j.get("salary_currency"):
            record["salary_currency"] = j["salary_currency"]
            record["salary_period"] = "yearly"

        # ATS Detection
        ats = detect_ats_from_url(j.get("url", ""))
        if not ats and j.get("company"):
            ats = COMPANY_ATS_MAP.get(j["company"].lower())
        record["ats_detected"] = ats or "Unknown ATS"

        try:
            db.table("jobs").upsert(record, on_conflict="dedup_hash").execute()
            inserted += 1
            if inserted % 50 == 0:
                print(f"    Inserted {inserted}...", flush=True)
        except Exception as e:
            err = str(e)
            if "ats_detected" in err.lower() and "column" in err.lower():
                record.pop("ats_detected", None)
                try:
                    db.table("jobs").upsert(record, on_conflict="dedup_hash").execute()
                    inserted += 1
                except Exception:
                    skipped += 1
            elif "duplicate" not in err.lower() and "unique" not in err.lower():
                if skipped < 3:
                    print(f"    [ERR] {j['title'][:40]}: {err[:60]}")
                skipped += 1
            else:
                skipped += 1

    print(f"  Inserted: {inserted}, Skipped: {skipped}")
    return inserted


# ══════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════
async def main():
    print("=" * 60)
    print("  LIOPLEURODON — Full Job Refresh")
    print("=" * 60)

    before = count_active()
    print(f"\n  Current active jobs: {before}")

    # Step 1: Remove expired
    deactivated = deactivate_expired()
    after_expire = count_active()
    print(f"  After expiry cleanup: {after_expire}")

    # Step 2: Scrape real jobs
    print("\n[STEP 2] Scraping real jobs from live APIs...")
    all_scraped = []

    india_queries = [
        "AI engineer", "machine learning engineer", "data scientist",
        "software engineer", "python developer", "full stack developer",
        "backend developer", "frontend developer", "devops engineer",
        "NLP engineer", "deep learning", "data engineer",
        "junior software engineer", "fresher developer",
        "cloud engineer", "react developer",
    ]
    us_queries = [
        "AI engineer", "machine learning", "data scientist",
        "software engineer remote", "GenAI engineer", "NLP engineer",
        "MLOps engineer", "full stack developer", "cloud engineer",
    ]
    gb_queries = ["AI engineer", "machine learning", "data scientist", "software engineer"]

    async with httpx.AsyncClient(timeout=25) as client:
        for name, cc, queries in [
            ("India", "in", india_queries),
            ("US", "us", us_queries),
            ("UK", "gb", gb_queries),
        ]:
            print(f"  Scraping Adzuna {name}...", flush=True)
            jobs = await scrape_adzuna(client, name, cc, queries)
            print(f"    => {len(jobs)} jobs")
            all_scraped.extend(jobs)
            await asyncio.sleep(1)

        for name, fn in [
            ("Remotive", scrape_remotive),
            ("RemoteOK", scrape_remoteok),
            ("Arbeitnow", scrape_arbeitnow),
            ("Jobicy", scrape_jobicy),
            ("Himalayas", scrape_himalayas),
            ("FindWork", scrape_findwork),
        ]:
            print(f"  Scraping {name}...", flush=True)
            jobs = await fn(client)
            print(f"    => {len(jobs)} jobs")
            all_scraped.extend(jobs)
            await asyncio.sleep(1)

    print(f"\n  Total scraped: {len(all_scraped)} raw jobs")

    # Step 3: Insert scraped
    scraped_inserted = insert_scraped(all_scraped)
    after_scrape = count_active()
    print(f"  Active after scrape: {after_scrape}")

    final = count_active()
    print(f"\n{'=' * 60}")
    print(f"  REFRESH COMPLETE")
    print(f"  Before:        {before}")
    print(f"  Expired:       {deactivated} deactivated")
    print(f"  Scraped:       {scraped_inserted} new real jobs")
    print(f"  Backfilled:    {backfilled} generated jobs")
    print(f"  Final:         {final} active jobs")
    print(f"  Target:        {TARGET}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    asyncio.run(main())
