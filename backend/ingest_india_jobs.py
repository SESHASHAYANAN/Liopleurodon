"""
Liopleurodon — Massive India Job Ingestion
Fetches 60+ high-quality Indian engineering jobs from Adzuna India API,
JSearch API, and other sources. Also reactivates wrongly deactivated India jobs.

Usage: python ingest_india_jobs.py
"""

import asyncio
import sys
import os
import hashlib
import re
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

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
db = create_client(SUPABASE_URL, SUPABASE_KEY)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
}

# ── Helpers ───────────────────────────────────────────────────────────────

def normalize_text(text):
    if not text:
        return ""
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9\s]', '', text.lower().strip()))

def dedup_hash(company, title, location, url=""):
    parts = [normalize_text(company), normalize_text(title), normalize_text(location), url]
    return hashlib.sha256("|".join(parts).encode()).hexdigest()

def first_sentence(text):
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text).strip()
    text = re.sub(r'\s+', ' ', text).strip()
    m = re.match(r'^(.+?[.!?])\s', text)
    return m.group(1)[:500] if m else text[:500]

def classify_remote(text):
    if not text:
        return "onsite"
    t = text.lower()
    if any(k in t for k in ["remote", "wfh", "work from home", "anywhere"]):
        return "hybrid" if "hybrid" in t else "remote"
    return "hybrid" if "hybrid" in t else "onsite"

def classify_job_type(title, desc):
    text = (title + " " + desc).lower()
    if any(k in text for k in ["intern", "internship", "trainee"]):
        return "internship"
    if any(k in text for k in ["freelance", "freelancer"]):
        return "freelance"
    if any(k in text for k in ["contract", "contractor"]):
        return "contract"
    if any(k in text for k in ["part-time", "part time"]):
        return "part-time"
    return "full-time"

def classify_company_type(company, desc):
    c = company.lower()
    d = desc.lower()
    big_tech = ["google", "meta", "amazon", "apple", "microsoft", "netflix",
                "uber", "airbnb", "stripe", "salesforce", "adobe", "oracle",
                "ibm", "cisco", "intel", "nvidia", "infosys", "tcs", "wipro",
                "hcl", "cognizant", "tech mahindra", "mindtree", "mphasis"]
    if any(bt in c for bt in big_tech):
        return "big_tech"
    if "stealth" in c:
        return "stealth"
    if any(k in d for k in ["series a", "series b", "y combinator", "yc backed",
                             "sequoia", "a16z", "accel", "vc backed", "venture"]):
        return "vc_backed"
    return "startup"

def detect_visa(desc):
    return any(k in desc.lower() for k in [
        "visa sponsorship", "sponsor visa", "h1b", "tier 2", "sponsorship available"
    ])

def detect_relocation(desc):
    return any(k in desc.lower() for k in [
        "relocation support", "relocation package", "relocation assistance"
    ])

def detect_ats(job):
    url = job.get("apply_url", "")
    company = job.get("company_name", "")
    ats = detect_ats_from_url(url)
    if not ats and company:
        ats = COMPANY_ATS_MAP.get(company.lower())
    return ats or "Unknown ATS"


# ── Step 1: Re-activate wrongly deactivated India jobs ────────────────────

def reactivate_india_jobs():
    """Re-activate India jobs that were wrongly deactivated by the cleanup."""
    print("\n[Step 1] Re-activating wrongly deactivated India jobs...")
    now = datetime.now(timezone.utc).isoformat()
    reactivated = 0
    offset = 0

    while True:
        batch = (
            db.table("jobs")
            .select("id, title, location_city, location_country, source_platforms, salary_currency")
            .eq("is_active", False)
            .or_("location_country.ilike.%India%,location_country.eq.IN")
            .range(offset, offset + 499)
            .execute()
            .data or []
        )
        if not batch:
            break

        for job in batch:
            # Re-validate with the FIXED (less aggressive) validator
            if validate_india_job(job):
                title = job.get("title", "")
                correct_exp = classify_experience_level(title)
                try:
                    db.table("jobs").update({
                        "is_active": True,
                        "experience_level": correct_exp,
                        "updated_at": now,
                    }).eq("id", job["id"]).execute()
                    reactivated += 1
                except Exception as e:
                    pass

        offset += 500
        if len(batch) < 500:
            break

    print(f"  Re-activated {reactivated} legitimate India jobs.")
    return reactivated


# ── Step 2: Fetch from Adzuna India API ───────────────────────────────────

INDIA_QUERIES = [
    # Core engineering
    "software engineer", "developer", "backend developer", "frontend developer",
    "full stack developer", "python developer", "java developer",
    "react developer", "node.js developer", "angular developer",
    # Data / AI / ML
    "data scientist", "data analyst", "data engineer", "machine learning",
    "AI engineer", "NLP engineer", "deep learning", "MLOps",
    "computer vision", "GenAI", "prompt engineer",
    # DevOps / Cloud / Infra
    "devops engineer", "cloud engineer", "AWS engineer", "azure engineer",
    "kubernetes", "platform engineer", "site reliability",
    "infrastructure engineer",
    # Mobile
    "android developer", "iOS developer", "flutter developer",
    "react native developer", "mobile developer",
    # Junior / Intern / Fresher
    "junior developer", "junior software engineer", "junior data analyst",
    "fresher software", "fresher developer", "graduate engineer",
    "trainee developer", "associate engineer", "associate software",
    "intern software", "intern data science", "internship developer",
    "entry level developer", "entry level engineer",
    # Remote / Hybrid
    "remote software engineer", "remote developer", "remote data",
    "hybrid developer", "work from home developer",
    # Specific tech
    "golang developer", "rust developer", "typescript developer",
    "vue.js developer", "spring boot developer", "django developer",
    "fastapi developer", "docker engineer",
    # Product / Design
    "product engineer", "UI engineer", "UX engineer",
    # Security
    "security engineer", "cybersecurity", "penetration tester",
    # QA
    "QA engineer", "automation engineer", "SDET",
]

async def fetch_adzuna_india(client, queries):
    """Fetch from Adzuna India API with multiple pages per query."""
    jobs = []
    app_id = os.environ.get("ADZUNA_APP_ID", "")
    app_key = os.environ.get("ADZUNA_API_KEY", "")
    if not app_id or not app_key:
        print("  [Adzuna] Missing ADZUNA_APP_ID or ADZUNA_API_KEY. Skipping.")
        return jobs

    for q in queries:
        for page in range(1, 6):  # 5 pages per query = 250 results per query
            try:
                r = await client.get(
                    f"https://api.adzuna.com/v1/api/jobs/in/search/{page}",
                    params={
                        "app_id": app_id, "app_key": app_key,
                        "what": q, "results_per_page": 50, "sort_by": "date",
                        "content-type": "application/json",
                    },
                    headers=HEADERS, timeout=20,
                )
                if r.status_code != 200:
                    break
                results = r.json().get("results") or []
                if not results:
                    break

                for item in results:
                    url = item.get("redirect_url", "")
                    title = item.get("title", "").strip()
                    company = (item.get("company") or {}).get("display_name", "").strip()
                    loc_obj = item.get("location") or {}
                    areas = loc_obj.get("area", [])
                    city = areas[-1] if areas else (loc_obj.get("display_name", "") or "India")
                    desc = first_sentence(item.get("description", ""))

                    if not title or not company or not url:
                        continue

                    job_data = {
                        "title": title,
                        "company_name": company,
                        "location_city": city,
                        "location_country": "India",
                        "apply_url": url,
                        "description": desc,
                        "posted_date": item.get("created", ""),
                        "source_platforms": ["Adzuna-IN"],
                        "remote_type": classify_remote(title + " " + city + " " + desc),
                        "experience_level": classify_experience_level(title),
                        "job_type": classify_job_type(title, desc),
                        "company_type": classify_company_type(company, desc),
                        "visa_sponsorship": detect_visa(desc),
                        "relocation_support": detect_relocation(desc),
                        "salary_min": item.get("salary_min"),
                        "salary_max": item.get("salary_max"),
                        "salary_currency": "INR",
                    }

                    # Validate — reject only if title has foreign markers
                    if validate_india_job(job_data):
                        jobs.append(job_data)

            except Exception as e:
                if "429" in str(e) or "rate" in str(e).lower():
                    await asyncio.sleep(5)
                break
            await asyncio.sleep(0.4)

        if len(jobs) % 100 == 0 and len(jobs) > 0:
            print(f"    [Adzuna-IN] {len(jobs)} jobs so far...")

    print(f"  [Adzuna-IN] Total: {len(jobs)} raw jobs from {len(queries)} queries")
    return jobs


# ── Step 3: Fetch from JSearch (RapidAPI) ─────────────────────────────────

JSEARCH_QUERIES = [
    "software engineer India", "developer India", "data scientist India",
    "junior developer India", "intern software India", "fresher engineer India",
    "python developer India", "react developer India", "full stack India",
    "machine learning India", "devops India", "cloud engineer India",
    "android developer India", "flutter developer India",
    "backend developer India", "frontend developer India",
    "data analyst India", "AI engineer India",
]

async def fetch_jsearch(client, queries):
    """Fetch from JSearch API (RapidAPI) — India-specific queries."""
    jobs = []
    api_key = os.environ.get("JSEARCH_API_KEY") or os.environ.get("RAPIDAPI_KEY", "")
    if not api_key:
        print("  [JSearch] Missing JSEARCH_API_KEY. Skipping.")
        return jobs

    for q in queries:
        try:
            r = await client.get(
                "https://jsearch.p.rapidapi.com/search",
                params={
                    "query": q,
                    "num_pages": 2,
                    "page": 1,
                    "country": "in",
                    "date_posted": "month",
                },
                headers={
                    "X-RapidAPI-Key": api_key,
                    "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
                },
                timeout=20,
            )
            if r.status_code != 200:
                continue
            for item in (r.json().get("data") or []):
                title = item.get("job_title", "").strip()
                company = item.get("employer_name", "").strip()
                url = item.get("job_apply_link", "")
                city = item.get("job_city", "")
                country = item.get("job_country", "India")
                desc = first_sentence(item.get("job_description", ""))
                is_remote = item.get("job_is_remote", False)

                if not title or not company or not url:
                    continue

                job_data = {
                    "title": title,
                    "company_name": company,
                    "location_city": city or "India",
                    "location_country": "India",
                    "apply_url": url,
                    "description": desc,
                    "posted_date": item.get("job_posted_at_datetime_utc", ""),
                    "source_platforms": ["JSearch"],
                    "remote_type": "remote" if is_remote else classify_remote(title + " " + desc),
                    "experience_level": classify_experience_level(title),
                    "job_type": classify_job_type(title, desc),
                    "company_type": classify_company_type(company, desc),
                    "visa_sponsorship": detect_visa(desc),
                    "relocation_support": detect_relocation(desc),
                    "salary_min": item.get("job_min_salary"),
                    "salary_max": item.get("job_max_salary"),
                    "salary_currency": item.get("job_salary_currency", "INR"),
                }

                if validate_india_job(job_data):
                    jobs.append(job_data)

        except Exception as e:
            print(f"  [JSearch/{q[:30]}] Error: {e}")
        await asyncio.sleep(1)

    print(f"  [JSearch] Total: {len(jobs)} raw India jobs")
    return jobs


# ── Step 4: Insert validated jobs ─────────────────────────────────────────

async def insert_jobs(raw_jobs):
    """Validate, deduplicate, and insert jobs into the database."""
    print(f"\n[Insert] Processing {len(raw_jobs)} raw jobs...")
    now = datetime.now(timezone.utc).isoformat()
    inserted, skipped_invalid, skipped_dup = 0, 0, 0
    seen_hashes = set()

    # Non-engineering titles to reject
    non_tech = [
        "sales", "marketing manager", "human resources", "recruiter",
        "customer support", "customer success", "bpo", "call center",
        "account executive", "business development", "content writer",
        "copywriter", "talent acquisition",
    ]

    for job in raw_jobs:
        title = job.get("title", "")
        company = job.get("company_name", "")
        url = job.get("apply_url", "")

        # Basic validation
        if not title or not company or not url:
            skipped_invalid += 1
            continue
        if len(title) < 5 or not url.startswith("http"):
            skipped_invalid += 1
            continue
        if any(nt in title.lower() for nt in non_tech):
            skipped_invalid += 1
            continue

        # Dedup
        h = dedup_hash(company, title, job.get("location_city", ""), url)
        if h in seen_hashes:
            skipped_dup += 1
            continue
        seen_hashes.add(h)

        # Ensure fields
        job["dedup_hash"] = h
        job["is_active"] = True
        job["created_at"] = now
        job["updated_at"] = now
        if not job.get("posted_date"):
            job["posted_date"] = now
        if not job.get("experience_level"):
            job["experience_level"] = classify_experience_level(title)
        if not job.get("job_type"):
            job["job_type"] = classify_job_type(title, job.get("description", ""))

        # ATS Detection
        job["ats_detected"] = detect_ats(job)

        # Clean None salary fields (Supabase doesn't like None for numeric)
        for key in ["salary_min", "salary_max"]:
            if job.get(key) is None:
                job.pop(key, None)

        try:
            db.table("jobs").upsert(job, on_conflict="dedup_hash").execute()
            inserted += 1
            if inserted % 50 == 0:
                print(f"    Inserted {inserted} jobs...")
        except Exception as e:
            err = str(e).lower()
            if "ats_detected" in err and "column" in err:
                job.pop("ats_detected", None)
                try:
                    db.table("jobs").upsert(job, on_conflict="dedup_hash").execute()
                    inserted += 1
                except:
                    pass
            elif "duplicate" in err or "unique" in err:
                skipped_dup += 1
            else:
                if skipped_invalid < 5:
                    print(f"    [DB Error] {title[:40]}: {str(e)[:80]}")

    print(f"  Inserted: {inserted} | Invalid: {skipped_invalid} | Duplicates: {skipped_dup}")
    return inserted


# ── Main ──────────────────────────────────────────────────────────────────

async def main():
    print("=" * 65)
    print("  LIOPLEURODON — Massive India Job Ingestion")
    print("=" * 65)

    # Count current India jobs
    india_before = 0
    try:
        india_before = db.table("jobs").select("id", count="exact").eq("is_active", True).or_("location_country.ilike.%India%,location_country.eq.IN").execute().count or 0
    except:
        pass
    print(f"\n  Current active India jobs: {india_before}")

    # Step 1: Re-activate wrongly deactivated India jobs
    reactivated = reactivate_india_jobs()

    # Step 2: Scrape new jobs
    all_jobs = []

    async with httpx.AsyncClient(timeout=30) as client:
        # Adzuna India — primary source
        print("\n[Step 2] Fetching from Adzuna India API...")
        adzuna_jobs = await fetch_adzuna_india(client, INDIA_QUERIES)
        all_jobs.extend(adzuna_jobs)

        # JSearch — secondary source
        print("\n[Step 3] Fetching from JSearch API...")
        jsearch_jobs = await fetch_jsearch(client, JSEARCH_QUERIES)
        all_jobs.extend(jsearch_jobs)

    print(f"\n  Total raw candidates: {len(all_jobs)}")

    # Step 3: Insert validated jobs
    print("\n[Step 4] Inserting validated jobs...")
    inserted = await insert_jobs(all_jobs)

    # Final stats
    india_after = 0
    try:
        india_after = db.table("jobs").select("id", count="exact").eq("is_active", True).or_("location_country.ilike.%India%,location_country.eq.IN").execute().count or 0
    except:
        pass

    # Break down by experience level
    print("\n" + "=" * 65)
    print("  INDIA JOB STATS")
    print("=" * 65)
    print(f"  Before: {india_before}")
    print(f"  Re-activated: {reactivated}")
    print(f"  New inserted: {inserted}")
    print(f"  After: {india_after}")

    for level in ["intern", "junior", "mid", "senior", "lead", "staff"]:
        try:
            count = db.table("jobs").select("id", count="exact").eq("is_active", True).eq("experience_level", level).or_("location_country.ilike.%India%,location_country.eq.IN").execute().count or 0
            print(f"  {level:12s}: {count}")
        except:
            pass

    print("=" * 65)


if __name__ == "__main__":
    asyncio.run(main())
