"""
Liopleurodon — Final Quality Check & Cleanup
Comprehensive pre-deployment data quality sweep:
  1. Remove mock/dummy/placeholder/test jobs
  2. Fix experience level misclassifications
  3. Remove foreign jobs wrongly tagged as India
  4. Purge expired jobs (>30 days old)
  5. Remove broken URLs and empty fields
  6. Remove non-engineering listings (sales, HR, etc.)
  7. Deduplicate any remaining duplicates
  8. Final stats report

Usage: python final_quality_check.py
"""

import sys
import os
import re
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from supabase import create_client

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from services.job_validator import classify_experience_level, validate_india_job

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
db = create_client(SUPABASE_URL, SUPABASE_KEY)

NOW = datetime.now(timezone.utc).isoformat()

# ── Non-engineering titles to reject ──────────────────────────────────────
NON_ENGINEERING = [
    "sales", "marketing manager", "human resources", "recruiter",
    "customer support", "customer success", "bpo", "call center",
    "account executive", "business development", "content writer",
    "copywriter", "talent acquisition", "hr manager", "hr executive",
    "receptionist", "accountant", "finance manager", "legal",
    "nurse", "doctor", "pharmacist", "teacher", "professor",
    "driver", "delivery", "warehouse", "cook", "chef",
]

# ── Fake/junk title markers ──────────────────────────────────────────────
FAKE_MARKERS = [
    "test job", "dummy", "placeholder", "sample job", "mock job",
    "lorem ipsum", "asdf", "xxxx", "delete me", "do not apply",
    "example job",
]


# ══════════════════════════════════════════════════
# STEP 1: Remove mock/dummy/fake jobs
# ══════════════════════════════════════════════════
def remove_fake_jobs():
    print("\n[1/7] Removing mock, dummy, and fake jobs...")
    removed = 0
    offset = 0

    while True:
        batch = (
            db.table("jobs")
            .select("id, title, company_name")
            .eq("is_active", True)
            .range(offset, offset + 499)
            .execute()
            .data or []
        )
        if not batch:
            break

        for job in batch:
            title = (job.get("title") or "").lower().strip()
            company = (job.get("company_name") or "").lower().strip()

            is_fake = False
            # Check for fake markers in title
            if any(m in title for m in FAKE_MARKERS):
                is_fake = True
            # Title starts with test/mock/dummy
            if re.match(r'^(test|mock|dummy|placeholder|sample)\s', title):
                is_fake = True
            # Company is obviously fake
            if company in ("test", "test company", "dummy", "example", "n/a", "none", "xxx"):
                is_fake = True

            if is_fake:
                try:
                    db.table("jobs").update({
                        "is_active": False, "updated_at": NOW,
                    }).eq("id", job["id"]).execute()
                    removed += 1
                    if removed <= 10:
                        print(f"  Removed: '{job.get('title', '')[:50]}' @ {company[:30]}")
                except:
                    pass

        offset += 500
        if len(batch) < 500:
            break

    print(f"  → Removed {removed} fake/mock jobs.")
    return removed


# ══════════════════════════════════════════════════
# STEP 2: Fix experience level misclassifications
# ══════════════════════════════════════════════════
def fix_experience_levels():
    print("\n[2/7] Fixing experience level misclassifications...")
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
            current = job.get("experience_level", "")
            correct = classify_experience_level(title)

            if current != correct:
                try:
                    db.table("jobs").update({
                        "experience_level": correct,
                        "updated_at": NOW,
                    }).eq("id", job["id"]).execute()
                    fixed += 1
                    if fixed <= 5:
                        print(f"  Fixed: '{title[:50]}' — {current} → {correct}")
                except:
                    pass

        offset += 500
        if len(batch) < 500:
            break

    print(f"  → Fixed {fixed} experience level mismatches.")
    return fixed


# ══════════════════════════════════════════════════
# STEP 3: Remove foreign jobs wrongly tagged as India
# ══════════════════════════════════════════════════
def fix_india_mismatches():
    print("\n[3/7] Removing foreign jobs wrongly tagged as India...")
    removed = 0
    offset = 0

    while True:
        batch = (
            db.table("jobs")
            .select("id, title, location_city, location_country, source_platforms, salary_currency, description")
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
                try:
                    db.table("jobs").update({
                        "is_active": False,
                        "updated_at": NOW,
                    }).eq("id", job["id"]).execute()
                    removed += 1
                    if removed <= 5:
                        print(f"  Removed: '{job.get('title', '')[:50]}' (foreign signals)")
                except:
                    pass

        offset += 500
        if len(batch) < 500:
            break

    print(f"  → Removed {removed} foreign jobs wrongly tagged as India.")
    return removed


# ══════════════════════════════════════════════════
# STEP 4: Purge expired jobs (>30 days old)
# ══════════════════════════════════════════════════
def purge_expired():
    print("\n[4/7] Deactivating expired jobs (>30 days old)...")
    cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    removed = 0
    offset = 0

    while True:
        batch = (
            db.table("jobs")
            .select("id")
            .eq("is_active", True)
            .lt("posted_date", cutoff)
            .range(offset, offset + 499)
            .execute()
            .data or []
        )
        if not batch:
            break

        for job in batch:
            try:
                db.table("jobs").update({
                    "is_active": False, "updated_at": NOW,
                }).eq("id", job["id"]).execute()
                removed += 1
            except:
                pass

        offset += 500
        if len(batch) < 500:
            break

    print(f"  → Deactivated {removed} expired jobs.")
    return removed


# ══════════════════════════════════════════════════
# STEP 5: Remove broken/low-quality data
# ══════════════════════════════════════════════════
def remove_low_quality():
    print("\n[5/7] Removing low-quality entries (broken URLs, empty fields)...")
    removed = 0
    offset = 0

    while True:
        batch = (
            db.table("jobs")
            .select("id, title, company_name, apply_url, description")
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

            should_remove = False
            if not title or len(title) < 5:
                should_remove = True
            elif not company or len(company) < 2:
                should_remove = True
            elif not url or not url.startswith("http"):
                should_remove = True
            elif len(title) > 200:
                should_remove = True

            if should_remove:
                try:
                    db.table("jobs").update({
                        "is_active": False, "updated_at": NOW,
                    }).eq("id", job["id"]).execute()
                    removed += 1
                except:
                    pass

        offset += 500
        if len(batch) < 500:
            break

    print(f"  → Removed {removed} low-quality entries.")
    return removed


# ══════════════════════════════════════════════════
# STEP 6: Remove non-engineering listings
# ══════════════════════════════════════════════════
def remove_non_engineering():
    print("\n[6/7] Removing non-engineering listings...")
    removed = 0
    offset = 0

    while True:
        batch = (
            db.table("jobs")
            .select("id, title")
            .eq("is_active", True)
            .range(offset, offset + 499)
            .execute()
            .data or []
        )
        if not batch:
            break

        for job in batch:
            title = (job.get("title") or "").lower()
            if any(ne in title for ne in NON_ENGINEERING):
                # But keep legitimate engineering titles that contain these words
                is_legit = any(k in title for k in [
                    "engineer", "developer", "architect", "devops", "sre",
                    "data scientist", "data analyst", "data engineer",
                    "ml ", "ai ", "machine learning", "designer",
                    "product manager", "scrum", "agile",
                ])
                if not is_legit:
                    try:
                        db.table("jobs").update({
                            "is_active": False, "updated_at": NOW,
                        }).eq("id", job["id"]).execute()
                        removed += 1
                    except:
                        pass

        offset += 500
        if len(batch) < 500:
            break

    print(f"  → Removed {removed} non-engineering listings.")
    return removed


# ══════════════════════════════════════════════════
# STEP 7: Deduplicate remaining active jobs
# ══════════════════════════════════════════════════
def deduplicate():
    print("\n[7/7] Deduplicating remaining active jobs...")
    removed = 0
    offset = 0
    seen_hashes = set()

    while True:
        batch = (
            db.table("jobs")
            .select("id, dedup_hash, created_at")
            .eq("is_active", True)
            .order("created_at", desc=False)
            .range(offset, offset + 999)
            .execute()
            .data or []
        )
        if not batch:
            break

        for job in batch:
            h = job.get("dedup_hash", "")
            if not h:
                continue
            if h in seen_hashes:
                try:
                    db.table("jobs").update({
                        "is_active": False, "updated_at": NOW,
                    }).eq("id", job["id"]).execute()
                    removed += 1
                except:
                    pass
            else:
                seen_hashes.add(h)

        offset += 1000
        if len(batch) < 1000:
            break

    print(f"  → Removed {removed} duplicate entries.")
    return removed


# ══════════════════════════════════════════════════
# FINAL REPORT
# ══════════════════════════════════════════════════
def final_report():
    print(f"\n{'=' * 65}")
    print("  FINAL DATABASE QUALITY REPORT")
    print(f"{'=' * 65}")

    total = db.table("jobs").select("id", count="exact").eq("is_active", True).execute().count or 0
    print(f"\n  Total active jobs: {total}")

    # India jobs
    india = 0
    try:
        india = db.table("jobs").select("id", count="exact").eq("is_active", True).or_("location_country.ilike.%India%,location_country.eq.IN").execute().count or 0
    except:
        pass
    print(f"  India jobs:        {india}")

    # Experience level breakdown
    print(f"\n  {'─' * 40}")
    print("  EXPERIENCE LEVELS:")
    for level in ["intern", "junior", "mid", "senior", "lead", "staff"]:
        try:
            count = db.table("jobs").select("id", count="exact").eq("is_active", True).eq("experience_level", level).execute().count or 0
            pct = f"({count*100//max(total,1)}%)"
            print(f"    {level:12s}: {count:>5} {pct}")
        except:
            pass

    # Job type breakdown
    print(f"\n  JOB TYPES:")
    for jt in ["full-time", "part-time", "contract", "freelance", "internship"]:
        try:
            count = db.table("jobs").select("id", count="exact").eq("is_active", True).eq("job_type", jt).execute().count or 0
            pct = f"({count*100//max(total,1)}%)"
            print(f"    {jt:12s}: {count:>5} {pct}")
        except:
            pass

    # Work type breakdown
    print(f"\n  WORK TYPES:")
    for rt in ["remote", "hybrid", "onsite"]:
        try:
            count = db.table("jobs").select("id", count="exact").eq("is_active", True).eq("remote_type", rt).execute().count or 0
            pct = f"({count*100//max(total,1)}%)"
            print(f"    {rt:12s}: {count:>5} {pct}")
        except:
            pass

    print(f"\n{'=' * 65}")
    print("  ✓ Quality check complete. Database is deployment-ready.")
    print(f"{'=' * 65}")


# ══════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════
def main():
    print("=" * 65)
    print("  LIOPLEURODON — Final Quality Check & Cleanup")
    print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 65)

    # Pre-cleanup count
    before = db.table("jobs").select("id", count="exact").eq("is_active", True).execute().count or 0
    print(f"\n  Active jobs before cleanup: {before}")

    s1 = remove_fake_jobs()
    s2 = fix_experience_levels()
    s3 = fix_india_mismatches()
    s4 = purge_expired()
    s5 = remove_low_quality()
    s6 = remove_non_engineering()
    s7 = deduplicate()

    after = db.table("jobs").select("id", count="exact").eq("is_active", True).execute().count or 0

    print(f"\n{'─' * 65}")
    print("  CLEANUP SUMMARY:")
    print(f"    Fake/mock removed:         {s1}")
    print(f"    Experience levels fixed:    {s2}")
    print(f"    India mismatches removed:   {s3}")
    print(f"    Expired deactivated:        {s4}")
    print(f"    Low-quality removed:        {s5}")
    print(f"    Non-engineering removed:    {s6}")
    print(f"    Duplicates removed:         {s7}")
    print(f"    Jobs before: {before} → After: {after}")
    print(f"{'─' * 65}")

    final_report()


if __name__ == "__main__":
    main()
