"""
Liopleurodon — Job Expansion v2
1. Remove all previously added broken "IndiaAI-Curated" jobs
2. Scrape REAL jobs from live free APIs with actual apply URLs
3. Verify each link before inserting
4. Reach 2,900 total
"""

import asyncio, sys, os, hashlib, re
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import httpx
from datetime import datetime, timezone
from supabase import create_client

import os
from dotenv import load_dotenv
load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://ayovlmoyyckxtftbnxmg.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

TARGET = 2900
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

db = create_client(SUPABASE_URL, SUPABASE_KEY)


def ntxt(text):
    if not text: return ""
    text = text.lower().strip()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    return re.sub(r'\s+', ' ', text)


def dhash(company, title, city):
    parts = [ntxt(company), ntxt(title), ntxt(city or ""), ""]
    return hashlib.sha256("|".join(parts).encode()).hexdigest()


def classify_exp(title):
    t = title.lower()
    if any(k in t for k in ["intern", "fresher", "trainee", "apprentice"]):
        return "intern"
    if any(k in t for k in ["junior", "jr.", "jr ", "associate", "entry level", "entry-level", "graduate", "new grad"]):
        return "junior"
    if any(k in t for k in ["senior", "sr.", "sr ", "lead", "principal", "architect"]):
        return "senior"
    if any(k in t for k in ["staff", "vp", "vice president", "director", "head of", "chief"]):
        return "staff"
    return "mid"


def classify_remote(text):
    if not text: return "onsite"
    t = text.lower()
    if any(k in t for k in ["remote", "work from home", "wfh", "anywhere"]):
        if "hybrid" in t: return "hybrid"
        return "remote"
    if "hybrid" in t: return "hybrid"
    return "onsite"


def first_sentence(text):
    if not text: return ""
    text = re.sub(r'<[^>]+>', '', text).strip()
    text = re.sub(r'\s+', ' ', text).strip()
    m = re.match(r'^(.+?[.!?])\s', text)
    if m: return m.group(1)[:300]
    return text[:300]


async def verify_link(client, url):
    """Return True if link responds with status < 400."""
    if not url or len(url) < 10:
        return False
    try:
        r = await client.head(url, follow_redirects=True, timeout=10, headers=HEADERS)
        if r.status_code < 400:
            return True
    except Exception:
        pass
    try:
        r = await client.get(url, follow_redirects=True, timeout=10, headers=HEADERS)
        return r.status_code < 400
    except Exception:
        return False


def count_active():
    r = db.table("jobs").select("id", count="exact").eq("is_active", True).execute()
    return r.count or 0


# ═══════════════════════════════════════════════════════════
# STEP 1: Remove all IndiaAI-Curated broken jobs
# ═══════════════════════════════════════════════════════════
def remove_curated_jobs():
    print("[STEP 1] Removing all IndiaAI-Curated jobs...")
    removed = 0
    offset = 0
    while True:
        batch = (db.table("jobs").select("id")
                .contains("source_platforms", ["IndiaAI-Curated"])
                .range(offset, offset + 99)
                .execute())
        if not batch.data:
            break
        for job in batch.data:
            try:
                db.table("jobs").delete().eq("id", job["id"]).execute()
                removed += 1
            except Exception as e:
                print(f"  [ERR] {e}")
        # Don't increment offset since we're deleting
    print(f"  Removed {removed} IndiaAI-Curated jobs.")
    return removed


# ═══════════════════════════════════════════════════════════
# STEP 2: Scrape REAL jobs from live APIs
# ═══════════════════════════════════════════════════════════

async def scrape_remotive(client):
    """Remotive.com — free API, real job URLs."""
    jobs = []
    for cat in ["software-dev", "data", "devops-sysadmin", "product", "design"]:
        try:
            r = await client.get(
                "https://remotive.com/api/remote-jobs",
                params={"category": cat, "limit": 50},
                headers=HEADERS, timeout=20
            )
            data = r.json()
            for item in (data.get("jobs") or []):
                url = item.get("url", "")
                if not url: continue
                title = item.get("title", "")
                company = item.get("company_name", "")
                location = item.get("candidate_required_location", "Remote")
                desc = first_sentence(item.get("description", ""))
                tags = item.get("tags") or []
                pub = item.get("publication_date", "")
                if title and company:
                    jobs.append({
                        "title": title, "company": company, "location": location,
                        "url": url, "desc": desc, "tags": tags,
                        "posted": pub, "source": "Remotive", "remote": "remote"
                    })
            await asyncio.sleep(1)
        except Exception as e:
            print(f"  [Remotive/{cat}] {e}")
    return jobs


async def scrape_remoteok(client):
    """RemoteOK — free JSON API, real job URLs."""
    jobs = []
    try:
        r = await client.get("https://remoteok.com/api",
                             headers={**HEADERS, "Accept": "application/json"}, timeout=20)
        data = r.json()
        items = data[1:] if len(data) > 1 else []
        for item in items:
            url = item.get("url", item.get("apply_url", ""))
            if not url: continue
            title = item.get("position", "")
            company = item.get("company", "")
            location = item.get("location", "Remote")
            desc = first_sentence(item.get("description", ""))
            tags = [t for t in (item.get("tags") or []) if isinstance(t, str)]
            pub = item.get("date", "")
            if title and company:
                jobs.append({
                    "title": title, "company": company, "location": location or "Remote",
                    "url": url, "desc": desc, "tags": tags,
                    "posted": pub, "source": "RemoteOK", "remote": "remote"
                })
    except Exception as e:
        print(f"  [RemoteOK] {e}")
    return jobs


async def scrape_arbeitnow(client):
    """Arbeitnow — free JSON API."""
    jobs = []
    for page in [1, 2, 3]:
        try:
            r = await client.get("https://www.arbeitnow.com/api/job-board-api",
                                 params={"page": page}, headers=HEADERS, timeout=20)
            data = r.json()
            for item in (data.get("data") or []):
                url = item.get("url", "")
                if not url: continue
                title = item.get("title", "")
                company = item.get("company_name", "")
                location = item.get("location", "")
                desc = first_sentence(item.get("description", ""))
                tags = item.get("tags") or []
                remote = "remote" if item.get("remote") else "onsite"
                if title and company:
                    jobs.append({
                        "title": title, "company": company, "location": location,
                        "url": url, "desc": desc, "tags": tags,
                        "posted": "", "source": "Arbeitnow", "remote": remote
                    })
            await asyncio.sleep(1)
        except Exception as e:
            print(f"  [Arbeitnow/p{page}] {e}")
    return jobs


async def scrape_jobicy(client):
    """Jobicy — free API for remote jobs."""
    jobs = []
    for tag in ["software-dev", "data-science", "devops", "machine-learning"]:
        try:
            r = await client.get("https://jobicy.com/api/v2/remote-jobs",
                                 params={"count": 50, "tag": tag},
                                 headers=HEADERS, timeout=20)
            data = r.json()
            for item in (data.get("jobs") or []):
                url = item.get("url", "")
                if not url: continue
                title = item.get("jobTitle", "")
                company = item.get("companyName", "")
                location = item.get("jobGeo", "Remote")
                desc = first_sentence(item.get("jobExcerpt", ""))
                pub = item.get("pubDate", "")
                if title and company:
                    jobs.append({
                        "title": title, "company": company, "location": location,
                        "url": url, "desc": desc, "tags": [],
                        "posted": pub, "source": "Jobicy", "remote": "remote"
                    })
            await asyncio.sleep(1)
        except Exception as e:
            print(f"  [Jobicy/{tag}] {e}")
    return jobs


async def scrape_himalayas(client):
    """Himalayas.app — free API."""
    jobs = []
    try:
        r = await client.get("https://himalayas.app/jobs/api",
                             params={"limit": 50}, headers=HEADERS, timeout=20)
        data = r.json()
        for item in (data.get("jobs") or []):
            url = item.get("applicationLink", item.get("url", ""))
            if not url: continue
            title = item.get("title", "")
            company = item.get("companyName", item.get("company_name", ""))
            location = item.get("location", "Remote")
            desc = first_sentence(item.get("description", ""))
            cats = item.get("categories") or []
            if title and company:
                jobs.append({
                    "title": title, "company": company, "location": location,
                    "url": url, "desc": desc, "tags": cats,
                    "posted": "", "source": "Himalayas", "remote": "remote"
                })
    except Exception as e:
        print(f"  [Himalayas] {e}")
    return jobs


async def scrape_adzuna_india(client):
    """Adzuna India — real job redirect URLs."""
    jobs = []
    queries = [
        "AI engineer", "machine learning engineer", "data scientist",
        "software engineer", "python developer", "full stack developer",
        "backend developer", "frontend developer", "devops engineer",
        "NLP engineer", "deep learning", "data engineer",
        "junior software engineer", "fresher developer",
        "cloud engineer", "react developer",
    ]
    for q in queries:
        try:
            r = await client.get(
                "https://api.adzuna.com/v1/api/jobs/in/search/1",
                params={
                    "app_id": "9f668b2e",
                    "app_key": "66f090e012038a74211f9b874f473e92",
                    "what": q,
                    "results_per_page": 25,
                    "sort_by": "date",
                    "content-type": "application/json",
                },
                headers=HEADERS, timeout=20,
            )
            data = r.json()
            for item in (data.get("results") or []):
                url = item.get("redirect_url", "")
                if not url: continue
                title = item.get("title", "")
                company = (item.get("company") or {}).get("display_name", "")
                location = (item.get("location") or {}).get("display_name", "India")
                desc = first_sentence(item.get("description", ""))
                sal_min = item.get("salary_min")
                sal_max = item.get("salary_max")
                created = item.get("created", "")
                if title and company:
                    j = {
                        "title": title, "company": company, "location": location,
                        "url": url, "desc": desc, "tags": [],
                        "posted": created, "source": "Adzuna-IN", "remote": "onsite",
                        "salary_min": sal_min, "salary_max": sal_max,
                        "salary_currency": "INR",
                    }
                    jobs.append(j)
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"  [Adzuna-IN/{q}] {e}")
    return jobs


async def scrape_adzuna_us(client):
    """Adzuna US — AI/ML jobs with real links."""
    jobs = []
    queries = ["AI engineer", "machine learning", "data scientist", "software engineer remote",
               "GenAI engineer", "NLP engineer", "MLOps engineer"]
    for q in queries:
        try:
            r = await client.get(
                "https://api.adzuna.com/v1/api/jobs/us/search/1",
                params={
                    "app_id": "9f668b2e",
                    "app_key": "66f090e012038a74211f9b874f473e92",
                    "what": q,
                    "results_per_page": 20,
                    "sort_by": "date",
                    "content-type": "application/json",
                },
                headers=HEADERS, timeout=20,
            )
            data = r.json()
            for item in (data.get("results") or []):
                url = item.get("redirect_url", "")
                if not url: continue
                title = item.get("title", "")
                company = (item.get("company") or {}).get("display_name", "")
                location = (item.get("location") or {}).get("display_name", "USA")
                desc = first_sentence(item.get("description", ""))
                sal_min = item.get("salary_min")
                sal_max = item.get("salary_max")
                created = item.get("created", "")
                if title and company:
                    jobs.append({
                        "title": title, "company": company, "location": location,
                        "url": url, "desc": desc, "tags": [],
                        "posted": created, "source": "Adzuna-US",
                        "remote": classify_remote(title + " " + location),
                        "salary_min": sal_min, "salary_max": sal_max,
                        "salary_currency": "USD",
                    })
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"  [Adzuna-US/{q}] {e}")
    return jobs


async def scrape_adzuna_gb(client):
    """Adzuna UK — AI/ML jobs."""
    jobs = []
    queries = ["AI engineer", "machine learning", "data scientist", "software engineer"]
    for q in queries:
        try:
            r = await client.get(
                "https://api.adzuna.com/v1/api/jobs/gb/search/1",
                params={
                    "app_id": "9f668b2e",
                    "app_key": "66f090e012038a74211f9b874f473e92",
                    "what": q,
                    "results_per_page": 20,
                    "sort_by": "date",
                    "content-type": "application/json",
                },
                headers=HEADERS, timeout=20,
            )
            data = r.json()
            for item in (data.get("results") or []):
                url = item.get("redirect_url", "")
                if not url: continue
                title = item.get("title", "")
                company = (item.get("company") or {}).get("display_name", "")
                location = (item.get("location") or {}).get("display_name", "UK")
                desc = first_sentence(item.get("description", ""))
                created = item.get("created", "")
                if title and company:
                    jobs.append({
                        "title": title, "company": company, "location": location,
                        "url": url, "desc": desc, "tags": [],
                        "posted": created, "source": "Adzuna-GB",
                        "remote": classify_remote(title + " " + location),
                    })
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"  [Adzuna-GB/{q}] {e}")
    return jobs


# ═══════════════════════════════════════════════════════════
# STEP 3: Verify links + Insert
# ═══════════════════════════════════════════════════════════

async def verify_and_insert(raw_jobs, needed):
    """Verify each job URL works, then insert into Supabase."""
    print(f"\n[STEP 3] Verifying links and inserting (need {needed})...")

    now = datetime.now(timezone.utc).isoformat()
    inserted = 0
    skipped_dup = 0
    skipped_broken = 0
    errors = 0
    seen_hashes = set()

    # Deduplicate within batch first
    unique_jobs = []
    for j in raw_jobs:
        h = dhash(j["company"], j["title"], j.get("location", "").split(",")[0].strip())
        if h not in seen_hashes:
            seen_hashes.add(h)
            j["_hash"] = h
            unique_jobs.append(j)

    print(f"  {len(unique_jobs)} unique jobs from {len(raw_jobs)} total scraped.")

    # Verify links in batches of 15
    batch_size = 15
    async with httpx.AsyncClient(timeout=12) as vclient:
        for i in range(0, len(unique_jobs), batch_size):
            if inserted >= needed:
                break

            batch = unique_jobs[i:i + batch_size]
            sem = asyncio.Semaphore(10)

            async def check(j):
                async with sem:
                    return j, await verify_link(vclient, j["url"])

            results = await asyncio.gather(*[check(j) for j in batch], return_exceptions=True)

            for res in results:
                if inserted >= needed:
                    break
                if isinstance(res, Exception):
                    continue
                j, ok = res
                if not ok:
                    skipped_broken += 1
                    continue

                h = j["_hash"]
                city = j.get("location", "").split(",")[0].strip()
                country = j.get("location", "").split(",")[-1].strip() if "," in j.get("location", "") else ""
                exp = classify_exp(j["title"])
                remote = j.get("remote", classify_remote(j.get("location", "") + " " + j["title"]))

                job_record = {
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
                    job_record["tech_stack"] = j["tags"][:10]
                if j.get("salary_min"):
                    job_record["salary_min"] = j["salary_min"]
                if j.get("salary_max"):
                    job_record["salary_max"] = j["salary_max"]
                if j.get("salary_currency"):
                    job_record["salary_currency"] = j["salary_currency"]
                    job_record["salary_period"] = "yearly"

                # Check DB for duplicate
                try:
                    existing = db.table("jobs").select("id").eq("dedup_hash", h).execute()
                    if existing.data and len(existing.data) > 0:
                        skipped_dup += 1
                        continue

                    db.table("jobs").insert(job_record).execute()
                    inserted += 1
                    if inserted % 20 == 0:
                        print(f"    Inserted {inserted}/{needed}...", flush=True)
                except Exception as e:
                    err = str(e)
                    if "duplicate" in err.lower() or "unique" in err.lower():
                        skipped_dup += 1
                    else:
                        errors += 1
                        if errors <= 3:
                            print(f"    [ERR] {j['title'][:40]}: {err[:60]}")

    print(f"  Inserted: {inserted}")
    print(f"  Skipped (duplicate): {skipped_dup}")
    print(f"  Skipped (broken link): {skipped_broken}")
    print(f"  Errors: {errors}")
    return inserted


async def main():
    print("=" * 60)
    print("  LIOPLEURODON — Job Expansion v2 (Real Links)")
    print("=" * 60)

    # Step 1: Remove curated jobs
    before = count_active()
    print(f"\n  Current active jobs: {before}")
    removed = remove_curated_jobs()
    after_remove = count_active()
    print(f"  After removing curated: {after_remove}")

    # Step 2: Scrape real jobs from live APIs
    print("\n[STEP 2] Scraping real jobs from live APIs...")
    all_scraped = []

    async with httpx.AsyncClient(timeout=25) as client:
        # Adzuna India (priority — Indian AI jobs)
        print("  Scraping Adzuna India...", flush=True)
        india_jobs = await scrape_adzuna_india(client)
        print(f"    => {len(india_jobs)} jobs", flush=True)
        all_scraped.extend(india_jobs)

        await asyncio.sleep(1)

        # Adzuna US
        print("  Scraping Adzuna US...", flush=True)
        us_jobs = await scrape_adzuna_us(client)
        print(f"    => {len(us_jobs)} jobs", flush=True)
        all_scraped.extend(us_jobs)

        await asyncio.sleep(1)

        # Adzuna UK
        print("  Scraping Adzuna UK...", flush=True)
        gb_jobs = await scrape_adzuna_gb(client)
        print(f"    => {len(gb_jobs)} jobs", flush=True)
        all_scraped.extend(gb_jobs)

        await asyncio.sleep(1)

        # Remotive
        print("  Scraping Remotive...", flush=True)
        rem_jobs = await scrape_remotive(client)
        print(f"    => {len(rem_jobs)} jobs", flush=True)
        all_scraped.extend(rem_jobs)

        await asyncio.sleep(2)

        # RemoteOK
        print("  Scraping RemoteOK...", flush=True)
        rok_jobs = await scrape_remoteok(client)
        print(f"    => {len(rok_jobs)} jobs", flush=True)
        all_scraped.extend(rok_jobs)

        await asyncio.sleep(1)

        # Arbeitnow
        print("  Scraping Arbeitnow...", flush=True)
        arb_jobs = await scrape_arbeitnow(client)
        print(f"    => {len(arb_jobs)} jobs", flush=True)
        all_scraped.extend(arb_jobs)

        await asyncio.sleep(1)

        # Jobicy
        print("  Scraping Jobicy...", flush=True)
        jcy_jobs = await scrape_jobicy(client)
        print(f"    => {len(jcy_jobs)} jobs", flush=True)
        all_scraped.extend(jcy_jobs)

        await asyncio.sleep(1)

        # Himalayas
        print("  Scraping Himalayas...", flush=True)
        him_jobs = await scrape_himalayas(client)
        print(f"    => {len(him_jobs)} jobs", flush=True)
        all_scraped.extend(him_jobs)

    print(f"\n  Total scraped: {len(all_scraped)} raw jobs")

    # Indian jobs first (priority)
    india_first = [j for j in all_scraped if j["source"] == "Adzuna-IN"]
    rest = [j for j in all_scraped if j["source"] != "Adzuna-IN"]
    ordered = india_first + rest

    # Step 3: Verify and insert
    needed = TARGET - after_remove
    if needed <= 0:
        print(f"\nAlready at {after_remove} jobs. Target is {TARGET}.")
        needed = max(10, needed)  # still add a few

    inserted = await verify_and_insert(ordered, max(needed, 10))

    final = count_active()
    print(f"\n{'=' * 60}")
    print(f"  EXPANSION v2 COMPLETE")
    print(f"  Before:     {before}")
    print(f"  Removed:    {removed} curated fakes")
    print(f"  Added:      {inserted} real verified jobs")
    print(f"  Final:      {final} active jobs")
    print(f"  Target:     {TARGET}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    asyncio.run(main())
