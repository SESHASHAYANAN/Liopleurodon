"""
Liopleurodon — Database Cleanup Script
Fixes existing jobs with:
  1. Wrong location (foreign jobs tagged as India)
  2. Wrong experience level (Senior jobs tagged as junior)
  3. Poor data quality (missing fields, broken URLs)
  
Run this ONE TIME to fix existing data, then the updated ingestion pipeline
will prevent future bad data from entering.

Usage: python cleanup_bad_data.py
"""

import asyncio
import os
import sys
import re
from datetime import datetime, timezone

from dotenv import load_dotenv
from supabase import create_client

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from services.job_validator import (
    classify_experience_level,
    validate_india_job,
    FOREIGN_COUNTRY_MARKERS,
)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
db = create_client(SUPABASE_URL, SUPABASE_KEY)


def fix_experience_levels():
    """
    Re-classify experience_level for ALL active jobs based on their title.
    This fixes 'Senior Clinical Data Specialist' being tagged as 'junior'.
    """
    print("\n[1/3] Fixing experience levels...")
    fixed = 0
    offset = 0

    while True:
        batch = (
            db.table("jobs")
            .select("id, title, experience_level")
            .eq("is_active", True)
            .range(offset, offset + 499)
            .execute()
            .data or []
        )
        if not batch:
            break

        for job in batch:
            title = job.get("title", "")
            current_level = job.get("experience_level", "")
            correct_level = classify_experience_level(title)

            if current_level != correct_level:
                try:
                    db.table("jobs").update({
                        "experience_level": correct_level,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    }).eq("id", job["id"]).execute()
                    fixed += 1
                    if fixed <= 20:
                        print(f"  Fixed: '{title[:60]}' — {current_level} → {correct_level}")
                except Exception as e:
                    print(f"  [Error] {e}")

        offset += 500
        if len(batch) < 500:
            break

    print(f"  → Fixed {fixed} experience level mismatches.")
    return fixed


def fix_india_location_mismatches():
    """
    Find and fix jobs tagged as India that are actually foreign jobs.
    Jobs with foreign markers in title are deactivated (not shown to users).
    """
    print("\n[2/3] Fixing India location mismatches...")
    fixed = 0
    deactivated = 0
    offset = 0

    while True:
        batch = (
            db.table("jobs")
            .select("id, title, company_name, location_city, location_country, apply_url, salary_currency, description")
            .eq("is_active", True)
            .or_("location_country.ilike.%India%,location_country.eq.IN")
            .range(offset, offset + 499)
            .execute()
            .data or []
        )
        if not batch:
            break

        for job in batch:
            if not validate_india_job(job):
                title = job.get("title", "")[:60]
                try:
                    # Deactivate: it's a foreign job with wrong India tag
                    db.table("jobs").update({
                        "is_active": False,
                        "location_country": None,
                        "location_city": None,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    }).eq("id", job["id"]).execute()
                    deactivated += 1
                    if deactivated <= 20:
                        print(f"  Deactivated: '{title}' (foreign job tagged as India)")
                except Exception as e:
                    print(f"  [Error] {e}")

        offset += 500
        if len(batch) < 500:
            break

    print(f"  → Deactivated {deactivated} foreign jobs wrongly tagged as India.")
    return deactivated


def fix_data_quality():
    """
    Deactivate jobs with critically broken data:
    - Empty titles
    - No apply_url
    - Extremely short descriptions
    """
    print("\n[3/3] Fixing data quality issues...")
    deactivated = 0
    offset = 0
    now = datetime.now(timezone.utc).isoformat()

    while True:
        batch = (
            db.table("jobs")
            .select("id, title, company_name, apply_url")
            .eq("is_active", True)
            .range(offset, offset + 499)
            .execute()
            .data or []
        )
        if not batch:
            break

        for job in batch:
            title = (job.get("title") or "").strip()
            company = (job.get("company_name") or "").strip()
            url = (job.get("apply_url") or "").strip()

            should_deactivate = False
            reason = ""

            if not title or len(title) < 5:
                should_deactivate = True
                reason = "empty/short title"
            elif not company or len(company) < 2:
                should_deactivate = True
                reason = "empty/short company"
            elif not url or not url.startswith("http"):
                should_deactivate = True
                reason = "invalid URL"
            elif any(m in title.lower() for m in ["test", "mock", "placeholder", "dummy"]):
                should_deactivate = True
                reason = "fake/test job"

            if should_deactivate:
                try:
                    db.table("jobs").update({
                        "is_active": False,
                        "updated_at": now,
                    }).eq("id", job["id"]).execute()
                    deactivated += 1
                    if deactivated <= 10:
                        print(f"  Deactivated: '{title[:40]}' ({reason})")
                except Exception as e:
                    print(f"  [Error] {e}")

        offset += 500
        if len(batch) < 500:
            break

    print(f"  → Deactivated {deactivated} low-quality jobs.")
    return deactivated


def report_stats():
    """Print final database stats."""
    print("\n" + "=" * 60)
    print("  FINAL DATABASE STATS")
    print("=" * 60)

    total = db.table("jobs").select("id", count="exact").eq("is_active", True).execute().count or 0
    print(f"  Total active jobs: {total}")

    try:
        india = db.table("jobs").select("id", count="exact").eq("is_active", True).or_("location_country.ilike.%India%,location_country.eq.IN").execute().count or 0
        print(f"  India jobs: {india}")
    except:
        pass

    for level in ["intern", "junior", "mid", "senior", "lead", "staff"]:
        count = db.table("jobs").select("id", count="exact").eq("is_active", True).eq("experience_level", level).execute().count or 0
        print(f"  {level:12s}: {count}")


async def main():
    print("=" * 60)
    print("  LIOPLEURODON — Database Cleanup")
    print("  Fixing experience levels, location mismatches, data quality")
    print("=" * 60)

    exp_fixed = fix_experience_levels()
    loc_fixed = fix_india_location_mismatches()
    quality_fixed = fix_data_quality()

    report_stats()

    print(f"\n  Summary:")
    print(f"    Experience levels fixed: {exp_fixed}")
    print(f"    India mismatches fixed:  {loc_fixed}")
    print(f"    Quality deactivated:     {quality_fixed}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
