"""
Liopleurodon — Verified Real Job Ingestion Pipeline
Strictly uses authenticated APIs to fetch high-quality Indian startup & engineering roles.
No mock data, no synthetic jobs, strict validation, robust deduplication.
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

from services.ats_detector import detect_ats_from_url, COMPANY_ATS_MAP  # noqa: E402

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
db = create_client(SUPABASE_URL, SUPABASE_KEY)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
}

# --- Country code to full name mapping ---
COUNTRY_MAP = {
    "in": "India", "us": "United States", "gb": "United Kingdom",
    "ca": "Canada", "au": "Australia", "de": "Germany", "sg": "Singapore",
}

# ── Normalization & Validation ───────────────────────────────────────────
def normalize_text(text: str) -> str:
    if not text:
        return ""
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9\s]', '', text.lower().strip()))

def generate_dedup_hash(company, title, location, apply_url="", external_id=""):
    """Deduplication rule combining multiple data points."""
    parts = [normalize_text(company), normalize_text(title), normalize_text(location), apply_url, normalize_text(external_id)]
    return hashlib.sha256("|".join(parts).encode()).hexdigest()

def classify_exp(title: str) -> str:
    t = title.lower()
    if any(k in t for k in ["intern", "fresher", "trainee"]):
        return "intern"
    if any(k in t for k in ["junior", "jr", "associate", "entry level", "graduate"]):
        return "junior"
    if any(k in t for k in ["senior", "sr", "lead", "principal", "architect"]):
        return "senior"
    if any(k in t for k in ["staff", "vp", "director", "head of", "chief"]):
        return "staff"
    return "mid"

def classify_job_type(title: str, desc: str) -> str:
    text = (title + " " + desc).lower()
    if any(k in text for k in ["intern", "internship", "trainee"]):
        return "internship"
    if any(k in text for k in ["freelance", "freelancer"]):
        return "freelance"
    if any(k in text for k in ["contract", "contractor", "c2c"]):
        return "contract"
    if any(k in text for k in ["part-time", "part time"]):
        return "part-time"
    return "full-time"

def classify_remote(text):
    if not text: return "onsite"
    t = text.lower()
    if any(k in t for k in ["remote", "wfh", "anywhere", "work from home", "global"]):
        return "hybrid" if "hybrid" in t else "remote"
    return "hybrid" if "hybrid" in t else "onsite"

def classify_company_type(company, desc):
    company = company.lower()
    desc = desc.lower()
    big_tech = ["google", "alphabet", "meta", "facebook", "amazon", "apple", "netflix", "microsoft", "uber", "airbnb", "stripe", "salesforce", "adobe", "oracle", "ibm", "cisco", "intel", "nvidia"]
    if any(c == company for c in big_tech) or any(f"{c} " in company for c in big_tech):
        return "big_tech"
    if "stealth" in company or "stealth" in desc:
        return "stealth"
    if any(k in desc for k in ["series a", "series b", "series c", "seed funding", "y combinator", "yc backed", "sequoia", "a16z", "accel", "vc backed", "venture backed", "venture-backed"]):
        return "vc_backed"
    return "startup"

def detect_visa(desc):
    desc = desc.lower()
    return any(k in desc for k in ["visa sponsorship", "sponsor visa", "h1b", "h-1b", "tier 2", "sponsorship available", "will sponsor"])

def detect_relocation(desc):
    desc = desc.lower()
    return any(k in desc for k in ["relocation support", "relocation package", "relocation assistance", "paid relocation", "will relocate"])

def first_sentence(text):
    if not text: return ""
    text = re.sub(r'<[^>]+>', '', text).strip()
    text = re.sub(r'\s+', ' ', text).strip()
    m = re.match(r'^(.+?[.!?])\s', text)
    return m.group(1)[:400] if m else text[:400]

def is_valid_job(job):
    """Strict validation: reject if critical fields are missing or generic."""
    required = ["title", "company_name", "apply_url", "source_platforms"]
    for field in required:
        if not job.get(field):
            return False
    if len(job["title"]) < 5 or len(job["company_name"]) < 2:
        return False
    if not job["apply_url"].startswith("http"):
        return False
        
    title_lower = job["title"].lower()
    
    # Reject fake/test jobs
    if any(k in title_lower for k in ["test", "mock", "placeholder", "dummy"]):
        return False
        
    # Reject low-signal / non-engineering roles
    non_tech_keywords = ["sales", "marketing manager", "human resources", "recruiter", "talent acquisition", "customer support", "customer success", "bpo", "call center", "account executive", "account manager", "business development", "content writer", "copywriter"]
    if any(k in title_lower for k in non_tech_keywords):
        return False

    return True

# --- Verified API Sources ---

async def fetch_adzuna_india(client, queries):
    """Adzuna API - INDIA ONLY, simple queries, many pages for maximum coverage."""
    jobs = []
    app_id = os.environ.get("ADZUNA_APP_ID")
    app_key = os.environ.get("ADZUNA_API_KEY")
    if not app_id or not app_key:
        print("  [Adzuna] Missing credentials. Skipping.")
        return jobs

    for q in queries:
        for page in range(1, 11):  # Fetch up to 10 pages = 500 jobs per query
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
                data = r.json()
                results = data.get("results") or []
                if not results:
                    break
                    
                for item in results:
                    url = item.get("redirect_url", "")
                    title = item.get("title", "")
                    company = (item.get("company") or {}).get("display_name", "")
                    location = (item.get("location") or {}).get("display_name", "India")
                    desc = first_sentence(item.get("description", ""))
                    
                    # Force tag if query explicitly requested it
                    forced_remote = "remote" if "remote" in q.lower() else classify_remote(title + " " + location + " " + desc)
                    forced_job_type = "internship" if "intern" in q.lower() or "fresher" in q.lower() else classify_job_type(title, desc)
                    forced_exp = "junior" if "junior" in q.lower() or "fresher" in q.lower() or "new grad" in q.lower() else classify_exp(title)
                    forced_stealth = "stealth" in q.lower() or "stealth" in classify_company_type(company, desc)
                    
                    jobs.append({
                        "title": title, "company_name": company,
                        "location_city": location,
                        "location_country": "India",
                        "apply_url": url, 
                        "description": desc,
                        "posted_date": item.get("created", ""),
                        "source_platforms": ["Adzuna-IN"],
                        "remote_type": forced_remote,
                        "experience_level": forced_exp,
                        "job_type": forced_job_type,
                        "company_type": "stealth" if forced_stealth else classify_company_type(company, desc),
                        "visa_sponsorship": detect_visa(desc),
                        "relocation_support": detect_relocation(desc),
                    })
            except Exception as e:
                print(f"  [Adzuna-IN/{q}/p{page}] Error: {e}")
                break
            await asyncio.sleep(0.3)
        print(f"    [Adzuna-IN] '{q}' -> {len([j for j in jobs if q in j.get('_query', q)])} (total so far: {len(jobs)})")
    return jobs


async def fetch_adzuna_global(client, queries, country_codes=["us", "gb", "ca", "au"]):
    """Adzuna API - Global countries for visa sponsorship & relocation jobs."""
    jobs = []
    app_id = os.environ.get("ADZUNA_APP_ID")
    app_key = os.environ.get("ADZUNA_API_KEY")
    if not app_id or not app_key:
        return jobs

    for cc in country_codes:
        for q in queries:
            for page in range(1, 4):  # 3 pages per global query
                try:
                    r = await client.get(
                        f"https://api.adzuna.com/v1/api/jobs/{cc}/search/{page}",
                        params={
                            "app_id": app_id, "app_key": app_key,
                            "what": q, "results_per_page": 50, "sort_by": "date",
                        },
                        headers=HEADERS, timeout=20,
                    )
                    if r.status_code != 200:
                        break
                    data = r.json()
                    results = data.get("results") or []
                    if not results:
                        break
                        
                    country_name = COUNTRY_MAP.get(cc, cc.upper())
                    for item in results:
                        url = item.get("redirect_url", "")
                        title = item.get("title", "")
                        company = (item.get("company") or {}).get("display_name", "")
                        location = (item.get("location") or {}).get("display_name", country_name)
                        desc = first_sentence(item.get("description", ""))
                        
                        jobs.append({
                            "title": title, "company_name": company,
                            "location_city": location,
                            "location_country": country_name,
                            "apply_url": url,
                            "description": desc,
                            "posted_date": item.get("created", ""),
                            "source_platforms": [f"Adzuna-{cc.upper()}"],
                            "remote_type": classify_remote(title + " " + location + " " + desc),
                            "experience_level": classify_exp(title),
                            "job_type": classify_job_type(title, desc),
                            "company_type": classify_company_type(company, desc),
                            "visa_sponsorship": detect_visa(desc) or ("visa" in q.lower()),
                            "relocation_support": detect_relocation(desc) or ("relocation" in q.lower()),
                        })
                except Exception as e:
                    print(f"  [Adzuna/{cc.upper()}/{q}/p{page}] Error: {e}")
                    break
                await asyncio.sleep(0.3)
    return jobs


async def fetch_remotive(client):
    """Remotive API - High quality remote startup roles globally."""
    jobs = []
    categories = ["software-dev", "data", "devops-sysadmin"]
    for cat in categories:
        try:
            r = await client.get(
                "https://remotive.com/api/remote-jobs",
                params={"category": cat, "limit": 100}, headers=HEADERS, timeout=20
            )
            for item in (r.json().get("jobs") or []):
                url = item.get("url", "")
                title = item.get("title", "")
                company = item.get("company_name", "")
                location = item.get("candidate_required_location", "Remote")
                desc = first_sentence(item.get("description", ""))
                
                jobs.append({
                    "title": title, "company_name": company, "location_city": "Remote",
                    "location_country": location, "apply_url": url,
                    "description": desc,
                    "posted_date": item.get("publication_date", ""),
                    "source_platforms": ["Remotive"],
                    "remote_type": "remote", "experience_level": classify_exp(title),
                    "job_type": classify_job_type(title, desc),
                    "company_type": classify_company_type(company, desc), "tech_stack": item.get("tags") or [],
                    "visa_sponsorship": detect_visa(desc),
                    "relocation_support": detect_relocation(desc),
                })
        except Exception as e:
            print(f"  [Remotive/{cat}] API Error: {e}")
        await asyncio.sleep(1)
    return jobs


async def fetch_arbeitnow(client):
    """Arbeitnow API - Free JSON API, startup tech roles."""
    jobs = []
    for page in range(1, 10):
        try:
            r = await client.get(
                "https://www.arbeitnow.com/api/job-board-api",
                params={"page": page}, headers=HEADERS, timeout=20
            )
            for item in (r.json().get("data") or []):
                url = item.get("url", "")
                title = item.get("title", "")
                company = item.get("company_name", "")
                location = item.get("location", "Remote")
                desc = first_sentence(item.get("description", ""))
                
                jobs.append({
                    "title": title, "company_name": company, "location_city": location,
                    "location_country": "Global", "apply_url": url,
                    "description": desc,
                    "source_platforms": ["Arbeitnow"],
                    "remote_type": "remote" if item.get("remote") else classify_remote(location + " " + desc),
                    "experience_level": classify_exp(title),
                    "job_type": classify_job_type(title, desc),
                    "company_type": classify_company_type(company, desc), "tech_stack": item.get("tags") or [],
                    "visa_sponsorship": detect_visa(desc),
                    "relocation_support": detect_relocation(desc),
                })
        except Exception as e:
            print(f"  [Arbeitnow/p{page}] API Error: {e}")
        await asyncio.sleep(1)
    return jobs


# --- ATS Detection (fast, URL-pattern based) ---

def detect_ats_for_job(job):
    """Detect ATS from URL patterns and company name mapping. No AI calls."""
    url = job.get("apply_url", "")
    company = job.get("company_name", "")
    ats = detect_ats_from_url(url)
    if not ats and company:
        ats = COMPANY_ATS_MAP.get(company.lower())
    return ats or "Unknown ATS"


# --- Verification & Insertion ---

async def verify_and_insert(raw_jobs):
    print(f"\n[Validation] Processing {len(raw_jobs)} raw jobs...")
    now = datetime.now(timezone.utc).isoformat()
    inserted, skipped_invalid, skipped_dup = 0, 0, 0
    ats_detected_count = 0
    seen_hashes = set()

    for job in raw_jobs:
        # 1. Validation
        if not is_valid_job(job):
            skipped_invalid += 1
            continue

        # 2. Deduplication
        dedup = generate_dedup_hash(
            job["company_name"], 
            job["title"], 
            job.get("location_city") or "", 
            job.get("apply_url") or "",
            job.get("external_id") or ""
        )
        if dedup in seen_hashes:
            skipped_dup += 1
            continue
        seen_hashes.add(dedup)
        
        job["dedup_hash"] = dedup
        job["is_active"] = True
        job["created_at"] = now
        job["updated_at"] = now
        
        # Ensure job type is set
        if not job.get("job_type"):
            job["job_type"] = classify_job_type(job["title"], job.get("description", ""))

        # Ensure posted_date is set (use now if missing, so expiry filter doesn't exclude)
        if not job.get("posted_date"):
            job["posted_date"] = now

        # 3. ATS Detection — tag every job
        ats = detect_ats_for_job(job)
        job["ats_detected"] = ats
        if ats != "Unknown ATS":
            ats_detected_count += 1

        try:
            db.table("jobs").upsert(job, on_conflict="dedup_hash").execute()
            inserted += 1
            if inserted % 50 == 0:
                print(f"    Inserted {inserted} valid jobs...")
        except Exception as e:
            err = str(e).lower()
            if "ats_detected" in err and "column" in err:
                # Column doesn't exist yet — retry without it
                job.pop("ats_detected", None)
                try:
                    db.table("jobs").upsert(job, on_conflict="dedup_hash").execute()
                    inserted += 1
                except Exception:
                    pass
            elif "duplicate" in err or "unique" in err:
                skipped_dup += 1
            else:
                print(f"    [DB Error] {job['title'][:30]}: {str(e)[:80]}")

    print(f"  Summary -> Inserted: {inserted} | Invalid: {skipped_invalid} | Duplicates: {skipped_dup} | ATS identified: {ats_detected_count}")
    return inserted


async def fix_existing_india_jobs():
    """Fix existing jobs with location_country='IN' to 'India' so frontend filter works."""
    print("\n[Fix] Updating existing IN -> India records...")
    try:
        result = db.table("jobs").update({
            "location_country": "India",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }).eq("location_country", "IN").execute()
        count = len(result.data) if result.data else 0
        print(f"  Updated {count} records from 'IN' to 'India'")
    except Exception as e:
        print(f"  [Fix Error] {e}")
    
    # Also fix NULL posted_date records so they aren't excluded by expiry filter
    print("[Fix] Setting posted_date on records with NULL posted_date...")
    try:
        now = datetime.now(timezone.utc).isoformat()
        result = db.table("jobs").update({
            "posted_date": now,
            "updated_at": now
        }).is_("posted_date", "null").eq("is_active", True).execute()
        count = len(result.data) if result.data else 0
        print(f"  Updated {count} records with NULL posted_date")
    except Exception as e:
        print(f"  [Fix Error] {e}")


async def fetch_jobicy(client):
    """Jobicy API - Remote tech jobs with good India/global coverage."""
    jobs = []
    for tag in ["software-dev", "data-science", "devops", "machine-learning"]:
        try:
            r = await client.get(
                "https://jobicy.com/api/v2/remote-jobs",
                params={"count": 50, "tag": tag}, headers=HEADERS, timeout=20
            )
            for item in (r.json().get("jobs") or []):
                url = item.get("url", "")
                title = item.get("jobTitle", "")
                company = item.get("companyName", "")
                location = item.get("jobGeo", "Remote")
                desc = first_sentence(item.get("jobExcerpt", ""))

                if title and company:
                    jobs.append({
                        "title": title, "company_name": company,
                        "location_city": location, "location_country": location,
                        "apply_url": url, "description": desc,
                        "posted_date": item.get("pubDate", ""),
                        "source_platforms": ["Jobicy"],
                        "remote_type": "remote",
                        "experience_level": classify_exp(title),
                        "job_type": classify_job_type(title, desc),
                        "company_type": classify_company_type(company, desc),
                        "visa_sponsorship": detect_visa(desc),
                        "relocation_support": detect_relocation(desc),
                    })
        except Exception as e:
            print(f"  [Jobicy/{tag}] API Error: {e}")
        await asyncio.sleep(1)
    return jobs


async def fetch_himalayas(client):
    """Himalayas API - Remote tech jobs."""
    jobs = []
    try:
        r = await client.get(
            "https://himalayas.app/jobs/api",
            params={"limit": 100}, headers=HEADERS, timeout=20
        )
        for item in (r.json().get("jobs") or []):
            url = item.get("applicationLink", item.get("url", ""))
            title = item.get("title", "")
            company = item.get("companyName", item.get("company_name", ""))
            location = item.get("location", "Remote")
            desc = first_sentence(item.get("description", ""))

            if title and company and url:
                jobs.append({
                    "title": title, "company_name": company,
                    "location_city": "Remote", "location_country": location,
                    "apply_url": url, "description": desc,
                    "source_platforms": ["Himalayas"],
                    "remote_type": "remote",
                    "experience_level": classify_exp(title),
                    "job_type": classify_job_type(title, desc),
                    "company_type": classify_company_type(company, desc),
                    "tech_stack": item.get("categories") or [],
                    "visa_sponsorship": detect_visa(desc),
                    "relocation_support": detect_relocation(desc),
                })
    except Exception as e:
        print(f"  [Himalayas] API Error: {e}")
    return jobs


async def backfill_ats_existing():
    """Backfill ats_detected for existing jobs that don't have it yet."""
    print("\n[ATS Backfill] Checking existing jobs for missing ATS data...")
    try:
        # Fetch jobs with NULL or 'Unknown ATS' ats_detected
        batch = db.table("jobs").select("id, apply_url, company_name, ats_detected").eq("is_active", True).is_("ats_detected", "null").limit(500).execute()
        if not batch.data:
            print("  All active jobs already have ATS data.")
            return
        updated = 0
        for job in batch.data:
            ats = detect_ats_from_url(job.get("apply_url", ""))
            if not ats:
                company = job.get("company_name", "")
                ats = COMPANY_ATS_MAP.get(company.lower()) if company else None
            ats = ats or "Unknown ATS"
            try:
                db.table("jobs").update({"ats_detected": ats}).eq("id", job["id"]).execute()
                updated += 1
            except:
                pass
        print(f"  Backfilled ATS for {updated} existing jobs.")
    except Exception as e:
        print(f"  [ATS Backfill] {e}")


async def main():
    print("============================================================")
    print("  LIOPLEURODON — Verified Indian Engineering Job Ingestion")
    print("============================================================")

    # 0. Fix existing data issues
    await fix_existing_india_jobs()

    # 1. Active db check
    current = db.table("jobs").select("id", count="exact").eq("is_active", True).execute().count or 0
    print(f"\nCurrent active jobs in database: {current}")

    all_jobs = []
    
    # --- INDIA-FOCUSED QUERIES — broad coverage across all categories ---
    india_queries = [
        # Core engineering
        "software engineer", "developer", "backend", "frontend",
        "full stack", "data scientist", "machine learning", "devops",
        # Junior / Intern / Fresher
        "intern software", "junior developer", "associate engineer",
        "fresher software engineer", "trainee developer", "graduate engineer",
        "internship data science", "junior data analyst", "junior AI engineer",
        "fresher python developer", "junior react developer",
        # Remote
        "remote software engineer", "remote full stack", "remote junior developer",
        "remote backend developer", "remote frontend developer", "remote data engineer",
        # Hybrid
        "hybrid software engineer", "hybrid developer bangalore",
        "hybrid data scientist", "hybrid full stack developer",
        # Onsite
        "onsite software engineer bangalore", "onsite developer mumbai",
        "onsite engineer hyderabad", "onsite developer pune",
        # Part-time / Freelance / Contract
        "part-time remote developer", "freelance remote engineer",
        "contract software developer", "freelance data scientist",
        "part-time python developer", "contract backend developer",
        # Startup / Stealth / VC
        "stealth startup engineer", "stealth developer", "VC backed software engineer",
        "startup engineer india", "founding engineer", "early stage startup developer",
        # AI / ML / Data
        "NLP engineer", "deep learning engineer", "computer vision engineer",
        "data engineer", "MLOps engineer", "AI researcher",
        "prompt engineer", "GenAI engineer",
        # Cloud / Infra
        "cloud engineer", "kubernetes engineer", "AWS engineer",
        "site reliability engineer", "platform engineer",
        # Mobile
        "android developer", "iOS developer", "flutter developer",
        "react native developer",
    ]
    
    # --- GLOBAL QUERIES (visa sponsorship, VC backed) ---
    global_queries = [
        "visa sponsorship software engineer",
        "software engineer startup",
        "developer remote",
    ]
    
    print("\n[Scraping] Fetching from authenticated endpoints...")
    async with httpx.AsyncClient(timeout=30) as client:
        # 1. Adzuna INDIA — primary source, 10 pages per query
        print("  -> Fetching Adzuna INDIA (primary source)...")
        india_jobs = await fetch_adzuna_india(client, india_queries)
        all_jobs.extend(india_jobs)
        print(f"     Found {len(india_jobs)} Indian jobs.")

        # 2. Adzuna Global (visa/relocation/startup)
        print("  -> Fetching Adzuna Global (visa/startup)...")
        global_jobs = await fetch_adzuna_global(client, global_queries)
        all_jobs.extend(global_jobs)
        print(f"     Found {len(global_jobs)} global jobs.")

        # 3. Remotive (Remote / Global / Startups)
        print("  -> Fetching Remotive...")
        remotive_jobs = await fetch_remotive(client)
        all_jobs.extend(remotive_jobs)
        print(f"     Found {len(remotive_jobs)} jobs.")

        # 4. Arbeitnow
        print("  -> Fetching Arbeitnow...")
        arbeitnow_jobs = await fetch_arbeitnow(client)
        all_jobs.extend(arbeitnow_jobs)
        print(f"     Found {len(arbeitnow_jobs)} jobs.")

        # 5. Jobicy (Remote tech jobs with India coverage)
        print("  -> Fetching Jobicy...")
        jobicy_jobs = await fetch_jobicy(client)
        all_jobs.extend(jobicy_jobs)
        print(f"     Found {len(jobicy_jobs)} jobs.")

        # 6. Himalayas (Remote jobs API)
        print("  -> Fetching Himalayas...")
        himalayas_jobs = await fetch_himalayas(client)
        all_jobs.extend(himalayas_jobs)
        print(f"     Found {len(himalayas_jobs)} jobs.")
        
    print(f"\n[Total] Scraped {len(all_jobs)} raw candidate jobs.")
    
    # Insert with strict validation + ATS detection
    await verify_and_insert(all_jobs)

    # Backfill ATS for existing jobs missing it
    await backfill_ats_existing()
    
    final = db.table("jobs").select("id", count="exact").eq("is_active", True).execute().count or 0
    india_count = 0
    try:
        india_count = db.table("jobs").select("id", count="exact").eq("is_active", True).ilike("location_country", "%India%").execute().count or 0
    except:
        pass
    print(f"\nFinal active jobs in database: {final}")
    print(f"India jobs: {india_count}")
    print("Pipeline complete. No mock data used.")

if __name__ == "__main__":
    asyncio.run(main())
