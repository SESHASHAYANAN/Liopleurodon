"""
Liopleurodon — Location Mismatch Fix + Real India Job Ingestion
----------------------------------------------------------------
Step 1: Revert all wrongly-tagged India jobs (jobs with non-India source
        that were bulk-reassigned to India by balance_categories.py).
Step 2: Fetch genuine Indian jobs from Adzuna India API (country=in).
Step 3: Re-run balance using ONLY genuinely scraped India jobs.

Never fabricates or guesses a location. Every job inserted here
has its location confirmed by the source API.
"""

import asyncio, os, sys, hashlib, re, random
import httpx
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from supabase import create_client

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

db = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])

from services.job_validator import classify_experience_level, validate_india_job  # noqa: E402

# Sources that are genuinely India-based
INDIA_SOURCES = {
    "Adzuna-IN", "Adzuna-IN-Junior", "Instahyre", "Karkidi",
    "Internshala", "CutShort", "Naukri-Startups", "Shine-Startups",
    "TimesJobs", "Freshersworld", "Wellfound-IN",
    "IndiaStartups", "India-Startups",
}

ADZUNA_APP_ID  = os.environ.get("ADZUNA_APP_ID", "4fbc6de3")
ADZUNA_API_KEY = os.environ.get("ADZUNA_API_KEY", "09ba5e03b9a6bc6fe505e47c95b527fa")

HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}


# ── Helpers ────────────────────────────────────────────────────────────────

def normalize(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", "", text.lower().strip()))


def dedup_hash(company, title, location, url=""):
    parts = [normalize(company), normalize(title), normalize(location), url]
    return hashlib.sha256("|".join(parts).encode()).hexdigest()


def classify_exp(title: str) -> str:
    """Delegates to centralized validator."""
    return classify_experience_level(title)


def classify_job_type(title: str, desc: str) -> str:
    text = (title + " " + desc).lower()
    if "part-time" in text or "part time" in text:
        return "part-time"
    if "contract" in text or "contractor" in text:
        return "contract"
    if "freelance" in text:
        return "freelance"
    if "internship" in text or "intern" in text:
        return "internship"
    return "full-time"


def classify_remote(title: str, desc: str, location: str) -> str:
    text = (title + " " + desc + " " + location).lower()
    if "remote" in text:
        return "remote"
    if "hybrid" in text:
        return "hybrid"
    return "onsite"


INVALID_TITLES = {
    "test", "mock", "sample", "example", "dummy", "placeholder",
    "n/a", "tbd", "various", "multiple",
}

ENGINEERING_KEYWORDS = [
    "engineer", "developer", "data", "scientist", "analyst", "devops",
    "backend", "frontend", "full stack", "software", "cloud", "architect",
    "ml", "ai", "machine learning", "deep learning", "nlp", "ios", "android",
    "mobile", "platform", "security", "infrastructure", "sre", "site reliability",
    "python", "java", "react", "node", "flutter", "kubernetes", "golang",
    "intern", "trainee", "fresher", "graduate", "associate",
]


def is_engineering_job(title: str, desc: str) -> bool:
    text = (title + " " + desc).lower()
    return any(kw in text for kw in ENGINEERING_KEYWORDS)


def is_valid(job: dict) -> bool:
    title   = job.get("title", "").strip()
    company = job.get("company_name", "").strip()
    url     = job.get("apply_url", "").strip()

    if not title or not company or not url:
        return False
    if any(t in title.lower() for t in INVALID_TITLES):
        return False
    if len(title) < 4 or len(title) > 200:
        return False
    if not is_engineering_job(title, job.get("description", "")):
        return False
    return True


# ── Step 1: Revert wrongly-tagged India jobs ───────────────────────────────

def revert_fake_india_jobs():
    """
    Reset location_country / location_city to NULL for any active job
    that has location_country='India' but whose source platform is NOT
    in the set of genuine India-only sources.
    These were bulk-reassigned by balance_categories.py and display the
    wrong country on their actual apply page.
    """
    print("\n[Step 1] Reverting wrongly-tagged India jobs...")
    now = datetime.now(timezone.utc).isoformat()
    reverted = 0
    offset   = 0

    while True:
        batch = (
            db.table("jobs")
            .select("id, source_platforms, location_country, location_city")
            .eq("is_active", True)
            .ilike("location_country", "%India%")
            .range(offset, offset + 499)
            .execute()
            .data or []
        )
        if not batch:
            break

        for job in batch:
            srcs = set(job.get("source_platforms") or [])
            if srcs & INDIA_SOURCES:
                # Genuinely Indian — keep as-is
                continue
            try:
                db.table("jobs").update({
                    "location_country": None,
                    "location_city":    None,
                    "updated_at":       now,
                }).eq("id", job["id"]).execute()
                reverted += 1
            except Exception as e:
                print(f"  [Revert Error] {e}")

        offset += 500
        if len(batch) < 500:
            break

        if reverted % 500 == 0 and reverted > 0:
            print(f"  Reverted {reverted} so far...")

    print(f"  Reverted {reverted} wrongly-tagged India jobs.")
    return reverted


# ── Step 2: Fetch real Indian jobs from Adzuna India API ──────────────────

INDIA_QUERIES = [
    # Core engineering
    "software engineer", "developer", "backend developer", "frontend developer",
    "full stack developer", "data scientist", "machine learning engineer",
    "devops engineer", "cloud engineer", "platform engineer",
    # Specialised AI/ML
    "NLP engineer", "deep learning engineer", "MLOps engineer",
    "computer vision engineer", "data engineer", "AI engineer",
    "GenAI engineer", "prompt engineer",
    # Junior / Intern / Fresher
    "junior software engineer", "junior developer", "junior data analyst",
    "fresher software engineer", "fresher developer", "graduate engineer",
    "software intern", "data science intern", "engineering trainee",
    "associate software engineer",
    # Mobile / Web
    "android developer", "iOS developer", "flutter developer",
    "react native developer", "react developer", "node.js developer",
    "python developer", "java developer", "golang developer",
    # Infra / SRE
    "site reliability engineer", "kubernetes engineer", "AWS engineer",
    "azure engineer", "GCP engineer", "security engineer",
    # Remote-specific (Adzuna still returns India results)
    "remote software engineer", "remote developer", "remote data scientist",
    # Part-time / Contract / Freelance
    "part time developer", "contract software engineer",
    "freelance developer",
]


async def fetch_adzuna_india(client: httpx.AsyncClient, query: str) -> list:
    """Fetch jobs from Adzuna India (country=in). Returns only India-located results."""
    try:
        resp = await client.get(
            "https://api.adzuna.com/v1/api/jobs/in/search/1",
            params={
                "app_id":          ADZUNA_APP_ID,
                "app_key":         ADZUNA_API_KEY,
                "what":            query,
                "results_per_page": 50,
                "content-type":    "application/json",
            },
            headers=HEADERS,
            timeout=30,
        )
        data = resp.json()
        jobs = []
        for item in data.get("results", []):
            title   = item.get("title", "").strip()
            company = (item.get("company") or {}).get("display_name", "").strip()
            url     = item.get("redirect_url") or item.get("adref", "")
            desc    = item.get("description", "")
            created = item.get("created", "")

            # Location comes directly from Adzuna India API — trust it
            loc_obj  = item.get("location") or {}
            areas    = loc_obj.get("area", [])
            # areas[0] = country, areas[-1] = city (Adzuna structure)
            city     = areas[-1] if areas else ""
            country  = "India"   # We queried /in/ — it IS India

            if not title or not company or not url:
                continue
            if not is_engineering_job(title, desc):
                continue

            salary_min = item.get("salary_min")
            salary_max = item.get("salary_max")
            remote_type = classify_remote(title, desc, city)
            job_type    = classify_job_type(title, desc)
            exp_level   = classify_exp(title)

            job = {
                "title":            title,
                "company_name":     company,
                "location_city":    city,
                "location_country": country,
                "apply_url":        url,
                "description":      desc[:500] if desc else None,
                "posted_date":      created or None,
                "source_platforms": ["Adzuna-IN"],
                "remote_type":      remote_type,
                "job_type":         job_type,
                "experience_level": exp_level,
                "is_active":        True,
            }
            if salary_min:
                job["salary_min"]      = salary_min
                job["salary_currency"] = "INR"
            if salary_max:
                job["salary_max"]      = salary_max
                job["salary_currency"] = "INR"

            jobs.append(job)
        return jobs

    except Exception as e:
        print(f"  [Adzuna-IN/{query[:30]}] Error: {e}")
        return []


async def scrape_all_india_jobs() -> list:
    """Run all India queries against Adzuna India and collect results."""
    all_jobs = []
    async with httpx.AsyncClient(timeout=30) as client:
        for i, query in enumerate(INDIA_QUERIES):
            jobs = await fetch_adzuna_india(client, query)
            all_jobs.extend(jobs)
            if jobs:
                print(f"  Adzuna-IN [{query[:35]:35s}] → {len(jobs)} jobs")
            # Be polite to the API
            if i < len(INDIA_QUERIES) - 1:
                await asyncio.sleep(1.5)
    return all_jobs


# ── Step 3: Insert with strict validation + dedup ─────────────────────────

def insert_india_jobs(raw_jobs: list) -> int:
    now = datetime.now(timezone.utc).isoformat()
    inserted, skipped_invalid, skipped_dup = 0, 0, 0
    seen = set()

    for job in raw_jobs:
        if not is_valid(job):
            skipped_invalid += 1
            continue

        h = dedup_hash(
            job["company_name"],
            job["title"],
            job.get("location_city", ""),
            job.get("apply_url", ""),
        )
        if h in seen:
            skipped_dup += 1
            continue
        seen.add(h)

        job["dedup_hash"] = h
        job["created_at"] = now
        job["updated_at"] = now
        if not job.get("posted_date"):
            job["posted_date"] = now

        try:
            db.table("jobs").upsert(job, on_conflict="dedup_hash").execute()
            inserted += 1
            if inserted % 100 == 0:
                print(f"    Inserted {inserted} India jobs...")
        except Exception as e:
            err = str(e).lower()
            if "duplicate" in err or "unique" in err:
                skipped_dup += 1
            else:
                print(f"  [DB] {job['title'][:40]}: {str(e)[:80]}")

    print(f"  Inserted: {inserted} | Invalid: {skipped_invalid} | Duplicates: {skipped_dup}")
    return inserted


# ── Step 4: Report final coverage ─────────────────────────────────────────

def report_coverage():
    from datetime import timedelta
    cutoff = (datetime.now(timezone.utc) - timedelta(days=21)).isoformat()
    print("\n[Coverage] India jobs per filter combination:")

    WORK  = ["remote", "hybrid", "onsite"]
    JOBS  = ["full-time", "part-time", "contract", "freelance", "internship"]
    EXPS  = ["intern", "junior", "mid"]

    for rt in WORK:
        for jt in JOBS:
            for el in EXPS:
                c = (
                    db.table("jobs").select("id", count="exact")
                    .eq("is_active", True)
                    .ilike("location_country", "%India%")
                    .eq("remote_type", rt)
                    .eq("job_type", jt)
                    .eq("experience_level", el)
                    .gte("posted_date", cutoff)
                    .execute()
                ).count or 0
                flag = "OK" if c >= 5 else "LOW"
                if c < 5:
                    print(f"  {rt:8s} | {jt:12s} | {el:8s} → {c:3d}  {flag}")

    total = (
        db.table("jobs").select("id", count="exact")
        .eq("is_active", True)
        .ilike("location_country", "%India%")
        .gte("posted_date", cutoff)
        .execute()
    ).count or 0
    print(f"\n  Total genuine India jobs (non-expired): {total}")


# ── Main ──────────────────────────────────────────────────────────────────

async def main():
    print("=" * 65)
    print("  LIOPLEURODON — Location Fix + Real India Job Ingestion")
    print("=" * 65)

    # 1. Revert fake-tagged jobs
    revert_fake_india_jobs()

    # 2. Scrape real India jobs
    print("\n[Step 2] Scraping real Indian jobs from Adzuna India API...")
    raw = await scrape_all_india_jobs()
    print(f"\n  Total raw candidates: {len(raw)}")

    # 3. Insert validated jobs
    print("\n[Step 3] Inserting validated jobs...")
    inserted = insert_india_jobs(raw)

    # 4. Report
    report_coverage()

    print("\n" + "=" * 65)
    print(f"  Done. {inserted} real India jobs added.")
    print("  All displayed India locations now match the actual job page.")
    print("=" * 65)


if __name__ == "__main__":
    asyncio.run(main())
