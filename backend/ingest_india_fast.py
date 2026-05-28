"""
Liopleurodon — Fast India Job Ingestion
Quick ingestion: 15 targeted queries, 1 page each = ~750 candidates.
Also re-activates wrongly deactivated India jobs.
"""

import asyncio, sys, os, hashlib, re
import httpx
from datetime import datetime, timezone
from supabase import create_client
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from services.ats_detector import detect_ats_from_url, COMPANY_ATS_MAP
from services.job_validator import classify_experience_level, validate_india_job

db = create_client(os.environ.get("SUPABASE_URL", ""), os.environ.get("SUPABASE_SERVICE_KEY", ""))
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

def ntxt(t):
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9\s]', '', (t or "").lower().strip()))

def dhash(company, title, loc, url=""):
    return hashlib.sha256("|".join([ntxt(company), ntxt(title), ntxt(loc), url]).encode()).hexdigest()

def first_sent(text):
    if not text: return ""
    text = re.sub(r'<[^>]+>', '', text).strip()[:500]
    return re.sub(r'\s+', ' ', text)

def classify_remote(text):
    t = (text or "").lower()
    if "remote" in t or "wfh" in t: return "remote"
    if "hybrid" in t: return "hybrid"
    return "onsite"

def classify_jtype(title, desc):
    t = (title + " " + desc).lower()
    if "intern" in t: return "internship"
    if "contract" in t: return "contract"
    if "part-time" in t or "part time" in t: return "part-time"
    if "freelance" in t: return "freelance"
    return "full-time"

NON_TECH = {"sales", "marketing manager", "human resources", "recruiter", "bpo", "call center", "customer support", "content writer", "copywriter", "talent acquisition"}


def reactivate_india_jobs():
    """Re-activate India jobs wrongly deactivated by cleanup."""
    print("[1] Re-activating wrongly deactivated India jobs...")
    now = datetime.now(timezone.utc).isoformat()
    reactivated = 0
    offset = 0
    while True:
        batch = (db.table("jobs").select("id, title, location_country, source_platforms, salary_currency")
                .eq("is_active", False)
                .or_("location_country.ilike.%India%,location_country.eq.IN")
                .range(offset, offset + 499).execute().data or [])
        if not batch: break
        for job in batch:
            if validate_india_job(job):
                try:
                    db.table("jobs").update({
                        "is_active": True,
                        "experience_level": classify_experience_level(job.get("title", "")),
                        "updated_at": now,
                    }).eq("id", job["id"]).execute()
                    reactivated += 1
                except: pass
        offset += 500
        if len(batch) < 500: break
    print(f"  Re-activated {reactivated} India jobs.")
    return reactivated


async def fetch_adzuna(client, queries):
    """Adzuna India - 50 results per query, single page for speed."""
    jobs = []
    app_id = os.environ.get("ADZUNA_APP_ID", "")
    app_key = os.environ.get("ADZUNA_API_KEY", "")
    if not app_id or not app_key:
        print("  [Adzuna] No credentials. Skipping.")
        return jobs

    for q in queries:
        try:
            r = await client.get(
                f"https://api.adzuna.com/v1/api/jobs/in/search/1",
                params={"app_id": app_id, "app_key": app_key, "what": q,
                        "results_per_page": 50, "sort_by": "date",
                        "content-type": "application/json"},
                headers=HEADERS, timeout=15,
            )
            if r.status_code != 200: continue
            for item in (r.json().get("results") or []):
                url = item.get("redirect_url", "")
                title = item.get("title", "").strip()
                company = (item.get("company") or {}).get("display_name", "").strip()
                areas = (item.get("location") or {}).get("area", [])
                city = areas[-1] if areas else "India"
                desc = first_sent(item.get("description", ""))
                if not title or not company or not url: continue

                jd = {
                    "title": title, "company_name": company,
                    "location_city": city, "location_country": "India",
                    "apply_url": url, "description": desc,
                    "posted_date": item.get("created", ""),
                    "source_platforms": ["Adzuna-IN"],
                    "remote_type": classify_remote(title + " " + city + " " + desc),
                    "experience_level": classify_experience_level(title),
                    "job_type": classify_jtype(title, desc),
                    "salary_min": item.get("salary_min"),
                    "salary_max": item.get("salary_max"),
                    "salary_currency": "INR",
                    "visa_sponsorship": False, "relocation_support": False,
                    "is_active": True,
                }
                if validate_india_job(jd):
                    jobs.append(jd)
            print(f"    '{q}' -> {len([j for j in jobs])} total")
        except Exception as e:
            print(f"    [Adzuna/{q}] {e}")
        await asyncio.sleep(0.2)

    print(f"  [Adzuna-IN] {len(jobs)} total raw jobs")
    return jobs


async def fetch_jsearch(client, queries):
    """JSearch API - India-specific."""
    jobs = []
    api_key = os.environ.get("JSEARCH_API_KEY") or os.environ.get("RAPIDAPI_KEY", "")
    if not api_key:
        print("  [JSearch] No API key. Skipping.")
        return jobs

    for q in queries:
        try:
            r = await client.get(
                "https://jsearch.p.rapidapi.com/search",
                params={"query": q, "num_pages": 1, "country": "in", "date_posted": "month"},
                headers={"X-RapidAPI-Key": api_key, "X-RapidAPI-Host": "jsearch.p.rapidapi.com"},
                timeout=15,
            )
            if r.status_code != 200: continue
            for item in (r.json().get("data") or []):
                title = item.get("job_title", "").strip()
                company = item.get("employer_name", "").strip()
                url = item.get("job_apply_link", "")
                city = item.get("job_city", "") or "India"
                desc = first_sent(item.get("job_description", ""))
                if not title or not company or not url: continue

                jd = {
                    "title": title, "company_name": company,
                    "location_city": city, "location_country": "India",
                    "apply_url": url, "description": desc,
                    "posted_date": item.get("job_posted_at_datetime_utc", ""),
                    "source_platforms": ["JSearch"],
                    "remote_type": "remote" if item.get("job_is_remote") else classify_remote(title),
                    "experience_level": classify_experience_level(title),
                    "job_type": classify_jtype(title, desc),
                    "salary_min": item.get("job_min_salary"),
                    "salary_max": item.get("job_max_salary"),
                    "salary_currency": item.get("job_salary_currency", "INR"),
                    "visa_sponsorship": False, "relocation_support": False,
                    "is_active": True,
                }
                if validate_india_job(jd):
                    jobs.append(jd)
        except Exception as e:
            print(f"    [JSearch/{q[:25]}] {e}")
        await asyncio.sleep(0.5)

    print(f"  [JSearch] {len(jobs)} total raw jobs")
    return jobs


async def insert_jobs(raw_jobs):
    """Validate, dedup, insert."""
    print(f"\n[3] Inserting {len(raw_jobs)} candidates...")
    now = datetime.now(timezone.utc).isoformat()
    inserted, duped = 0, 0
    seen = set()

    for job in raw_jobs:
        title = job.get("title", "")
        if any(nt in title.lower() for nt in NON_TECH): continue
        if len(title) < 5 or not job.get("apply_url", "").startswith("http"): continue

        h = dhash(job["company_name"], title, job.get("location_city", ""), job.get("apply_url", ""))
        if h in seen:
            duped += 1
            continue
        seen.add(h)

        job["dedup_hash"] = h
        job["created_at"] = now
        job["updated_at"] = now
        if not job.get("posted_date"): job["posted_date"] = now
        for k in ["salary_min", "salary_max"]:
            if job.get(k) is None: job.pop(k, None)

        ats = detect_ats_from_url(job.get("apply_url", ""))
        if not ats: ats = COMPANY_ATS_MAP.get(job["company_name"].lower(), None)
        job["ats_detected"] = ats or "Unknown ATS"

        try:
            db.table("jobs").upsert(job, on_conflict="dedup_hash").execute()
            inserted += 1
            if inserted % 50 == 0: print(f"    {inserted} inserted...")
        except Exception as e:
            err = str(e).lower()
            if "ats_detected" in err and "column" in err:
                job.pop("ats_detected", None)
                try:
                    db.table("jobs").upsert(job, on_conflict="dedup_hash").execute()
                    inserted += 1
                except: pass
            elif "duplicate" not in err and "unique" not in err:
                pass

    print(f"  Inserted: {inserted} | Dupes: {duped}")
    return inserted


async def main():
    print("=" * 55)
    print("  LIOPLEURODON — Fast India Job Ingestion")
    print("=" * 55)

    india_before = 0
    try:
        india_before = db.table("jobs").select("id", count="exact").eq("is_active", True).or_("location_country.ilike.%India%,location_country.eq.IN").execute().count or 0
    except: pass
    print(f"\n  India jobs before: {india_before}")

    # Step 1: Re-activate wrongly deactivated
    reactivated = reactivate_india_jobs()

    # Step 2: Scrape
    all_jobs = []
    adzuna_queries = [
        "software engineer", "developer", "backend", "frontend",
        "full stack", "data scientist", "machine learning", "devops",
        "junior developer", "fresher software", "intern software",
        "python developer", "react developer", "cloud engineer",
        "android developer", "data analyst",
    ]
    jsearch_queries = [
        "software engineer India", "developer India", "junior developer India",
        "data scientist India", "python developer India", "react developer India",
        "fresher engineer India", "intern software India",
        "full stack developer India", "machine learning India",
        "backend developer India", "frontend developer India",
    ]

    async with httpx.AsyncClient(timeout=20) as client:
        print("\n[2a] Adzuna India...")
        adzuna = await fetch_adzuna(client, adzuna_queries)
        all_jobs.extend(adzuna)

        print("\n[2b] JSearch...")
        jsearch = await fetch_jsearch(client, jsearch_queries)
        all_jobs.extend(jsearch)

    print(f"\n  Total candidates: {len(all_jobs)}")

    # Step 3: Insert
    inserted = await insert_jobs(all_jobs)

    # Stats
    india_after = 0
    try:
        india_after = db.table("jobs").select("id", count="exact").eq("is_active", True).or_("location_country.ilike.%India%,location_country.eq.IN").execute().count or 0
    except: pass

    print(f"\n{'=' * 55}")
    print(f"  Before:       {india_before}")
    print(f"  Re-activated: {reactivated}")
    print(f"  New inserted: {inserted}")
    print(f"  After:        {india_after}")

    for lvl in ["intern", "junior", "mid", "senior", "lead", "staff"]:
        try:
            c = db.table("jobs").select("id", count="exact").eq("is_active", True).eq("experience_level", lvl).or_("location_country.ilike.%India%,location_country.eq.IN").execute().count or 0
            print(f"  {lvl:12s}: {c}")
        except: pass
    print("=" * 55)


if __name__ == "__main__":
    asyncio.run(main())
