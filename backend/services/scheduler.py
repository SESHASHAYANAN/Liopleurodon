"""
Liopleurodon — Scheduler Service
APScheduler cron jobs for periodic scraping from all sources.
"""

import asyncio
from datetime import datetime, timezone
from services.normalizer import (
    normalize_jsearch, normalize_serpapi, normalize_adzuna, normalize_theirstack,
    normalize_apify, normalize_themuse, normalize_findwork, normalize_yc,
    normalize_wellfound, normalize_linkedin, add_dedup_hash,
)
from services.deduplication import merge_job_data
from services.vc_tagger import tag_job_with_vc_info, tag_job_perks
from scrapers.jsearch import JSearchScraper
from scrapers.serpapi import SerpApiScraper
from scrapers.adzuna import AdzunaScraper
from scrapers.theirstack import TheirStackScraper
from scrapers.apify import ApifyScraper
from scrapers.themuse import TheMuseScraper
from scrapers.findwork import FindworkScraper
from scrapers.yc_jobs import YCScraper
from scrapers.wellfound import WellfoundScraper
from scrapers.linkedin import LinkedInScraper


# Scraper instances
SCRAPERS = [
    (JSearchScraper(), normalize_jsearch),
    (SerpApiScraper(), normalize_serpapi),
    (AdzunaScraper(), normalize_adzuna),
    (TheirStackScraper(), normalize_theirstack),
    (ApifyScraper(), normalize_apify),
    (TheMuseScraper(), normalize_themuse),
    (FindworkScraper(), normalize_findwork),
    (YCScraper(), normalize_yc),
    (WellfoundScraper(), normalize_wellfound),
    (LinkedInScraper(), normalize_linkedin),
]

# Search queries to rotate through
SEARCH_QUERIES = [
    "software engineer",
    "software engineer visa sponsorship",
    "software engineer relocation",
    "frontend developer",
    "backend developer",
    "full stack developer",
    "data scientist",
    "machine learning engineer",
    "devops engineer",
    "product designer",
    "product manager",
    "mobile developer",
    "cloud engineer",
    "data engineer",
    "python developer",
    "java developer",
    "react developer",
    "site reliability engineer",
    "security engineer",
    "QA engineer",
    "AI engineer",
    "blockchain developer",
    "iOS developer",
    "Android developer",
    "systems engineer",
    "platform engineer",
    "solutions architect",
    "technical program manager",
    "engineering manager",
]

LOCATIONS = [
    "",
    "India",
    "United States",
    "Europe",
    "Remote",
    "United Kingdom",
    "Canada",
    "Germany",
    "Singapore",
    "Australia",
    "Bangalore",
    "San Francisco",
    "New York",
    "London",
]

last_scrape_status = {
    "last_run": None,
    "status": "idle",
    "jobs_found": 0,
    "jobs_inserted": 0,
    "jobs_updated": 0,
    "errors": [],
}


async def scrape_single_source(scraper, normalizer, query, location=""):
    """Scrape a single source and normalize results."""
    try:
        if not scraper.is_configured():
            return []
        raw_jobs = await scraper.scrape(query=query, location=location)
        normalized = []
        for raw in raw_jobs:
            try:
                job = normalizer(raw)
                job = add_dedup_hash(job)
                job = tag_job_with_vc_info(job)
                job = tag_job_perks(job)
                normalized.append(job)
            except Exception as e:
                print(f"Normalization error in {scraper.get_source_name()}: {e}")
        return normalized
    except Exception as e:
        print(f"Scrape error from {scraper.get_source_name()}: {e}")
        return []


async def scrape_all_sources(query: str = "software engineer", location: str = ""):
    """Scrape all sources in parallel, deduplicate, and insert into Supabase."""
    global last_scrape_status
    last_scrape_status["status"] = "running"
    last_scrape_status["last_run"] = datetime.now(timezone.utc).isoformat()
    last_scrape_status["errors"] = []

    # Run all scrapers in parallel
    tasks = [
        scrape_single_source(scraper, normalizer, query, location)
        for scraper, normalizer in SCRAPERS
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Flatten results
    all_jobs = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            source_name = SCRAPERS[i][0].get_source_name()
            last_scrape_status["errors"].append(f"{source_name}: {str(result)}")
        elif isinstance(result, list):
            all_jobs.extend(result)

    last_scrape_status["jobs_found"] = len(all_jobs)

    # Deduplicate and insert
    inserted, updated = await _deduplicate_and_store(all_jobs)
    last_scrape_status["jobs_inserted"] = inserted
    last_scrape_status["jobs_updated"] = updated
    last_scrape_status["status"] = "completed"

    print(f"Scrape complete: {len(all_jobs)} found, {inserted} inserted, {updated} updated")
    return last_scrape_status


async def _deduplicate_and_store(jobs: list[dict]) -> tuple[int, int]:
    """Deduplicate jobs and store in Supabase."""
    from database import get_supabase_admin

    db = get_supabase_admin()
    inserted = 0
    updated = 0

    for job in jobs:
        if not job.get("dedup_hash") or not job.get("title"):
            continue

        try:
            # Check if job exists
            existing = (db.table("jobs")
                       .select("*")
                       .eq("dedup_hash", job["dedup_hash"])
                       .execute())

            # Clean job data for Supabase
            clean_job = _clean_for_db(job)

            if existing.data and len(existing.data) > 0:
                # Merge and update
                merged = merge_job_data(existing.data[0], clean_job)
                merged.pop("id", None)
                merged.pop("created_at", None)
                merged["updated_at"] = datetime.now(timezone.utc).isoformat()
                (db.table("jobs")
                 .update(merged)
                 .eq("dedup_hash", job["dedup_hash"])
                 .execute())
                updated += 1
            else:
                # Insert new job
                clean_job["created_at"] = datetime.now(timezone.utc).isoformat()
                clean_job["updated_at"] = clean_job["created_at"]
                db.table("jobs").insert(clean_job).execute()
                inserted += 1
        except Exception as e:
            print(f"DB error for {job.get('title', 'unknown')}: {e}")

    return inserted, updated


def _clean_for_db(job: dict) -> dict:
    """Clean job dict for Supabase insertion."""
    clean = {}
    # Fields that match the DB schema
    db_fields = [
        "title", "company_name", "company_logo_url", "company_size",
        "company_industry", "company_type", "vc_backer", "funding_stage",
        "location_city", "location_country", "remote_type",
        "visa_sponsorship", "relocation_support", "work_authorization",
        "salary_min", "salary_max", "salary_currency", "salary_period",
        "experience_level", "years_experience_min", "years_experience_max",
        "job_type", "description", "responsibilities", "requirements",
        "benefits", "skills_required", "skills_preferred", "tech_stack",
        "apply_url", "easy_apply", "source_platforms", "posted_date",
        "expiry_date", "is_stealth", "is_active", "dedup_hash",
        "is_featured", "last_seen_at",
    ]

    for field in db_fields:
        if field in job and job[field] is not None:
            val = job[field]
            # Convert datetime objects to ISO strings
            if isinstance(val, datetime):
                val = val.isoformat()
            clean[field] = val

    return clean


def get_scrape_status() -> dict:
    return last_scrape_status


async def run_periodic_scrapes():
    """Run periodic scrapes cycling through multiple combinations.
    Samples 4 queries x 3 locations = up to 12 scrape rounds per cycle
    to build toward 2,500+ jobs in the database.
    """
    import random
    
    # Pick 4 random queries and 3 random locations for broad coverage
    queries = random.sample(SEARCH_QUERIES, min(4, len(SEARCH_QUERIES)))
    locations = random.sample(LOCATIONS, min(3, len(LOCATIONS)))
    
    for q in queries:
        for loc in locations:
            print(f"[Scheduler] Scraping for query: '{q}', location: '{loc}'")
            await scrape_all_sources(query=q, location=loc)
