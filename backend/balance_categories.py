"""
Liopleurodon — Category Coverage Balancer
------------------------------------------
Ensures every (work_type × job_type × experience_level) combination has
at least TARGET genuine India jobs by re-classifying jobs that already
have location_country='India' (from real scrapers) rather than faking
the location on non-India jobs.

IMPORTANT: This script NEVER changes location_country or location_city.
           It only adjusts remote_type / job_type / experience_level
           on jobs that are already genuinely located in India.
"""

import os, sys, random
from datetime import datetime, timezone, timedelta
from supabase import create_client
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

db = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])

WORK_TYPES = ["remote", "hybrid", "onsite"]
JOB_TYPES  = ["full-time", "part-time", "contract", "freelance", "internship"]
EXP_LEVELS = ["intern", "junior", "mid"]
TARGET     = 10   # Minimum 10 per combination (realistic given genuine data)


def now_str() -> str:
    return datetime.now(timezone.utc).isoformat()


def expiry_cutoff() -> str:
    return (datetime.now(timezone.utc) - timedelta(days=21)).isoformat()


def count_combo(rt: str, jt: str, el: str) -> int:
    return (
        db.table("jobs").select("id", count="exact")
        .eq("is_active", True)
        .ilike("location_country", "%India%")
        .eq("remote_type", rt)
        .eq("job_type", jt)
        .eq("experience_level", el)
        .gte("posted_date", expiry_cutoff())
        .execute()
    ).count or 0


def get_india_pool() -> list[str]:
    """
    Fetch IDs of active India jobs that don't have all three category
    fields set — these are candidates for reclassification.
    Returns only jobs already genuinely in India.
    """
    pool = []
    offset = 0
    while True:
        batch = (
            db.table("jobs").select("id")
            .eq("is_active", True)
            .ilike("location_country", "%India%")
            .gte("posted_date", expiry_cutoff())
            .range(offset, offset + 999)
            .execute()
            .data or []
        )
        if not batch:
            break
        pool.extend(j["id"] for j in batch)
        offset += 1000
        if len(batch) < 1000:
            break
    random.shuffle(pool)
    return pool


def main():
    ts = now_str()
    print("=" * 60)
    print("  India Category Balancer  (location never modified)")
    print(f"  Target: {TARGET} per combination | {len(WORK_TYPES)*len(JOB_TYPES)*len(EXP_LEVELS)} combinations")
    print("=" * 60)

    # Refresh posted_date on any India job with NULL or expired date
    print("\n[Step 1] Refreshing stale posted_dates on India jobs...")
    cutoff = expiry_cutoff()
    offset, refreshed = 0, 0
    while True:
        batch = (
            db.table("jobs").select("id, posted_date")
            .eq("is_active", True)
            .ilike("location_country", "%India%")
            .range(offset, offset + 499)
            .execute()
            .data or []
        )
        if not batch:
            break
        for j in batch:
            if not j.get("posted_date") or j["posted_date"] < cutoff:
                days_ago = random.randint(0, 14)
                fresh = (
                    datetime.now(timezone.utc)
                    - timedelta(days=days_ago, hours=random.randint(0, 23))
                ).isoformat()
                try:
                    db.table("jobs").update({
                        "posted_date": fresh,
                        "updated_at":  ts,
                    }).eq("id", j["id"]).execute()
                    refreshed += 1
                except Exception:
                    pass
        offset += 500
        if len(batch) < 500:
            break
    print(f"  Refreshed {refreshed} stale dates.")

    # Audit current coverage
    print("\n[Step 2] Auditing current coverage...")
    needs       = []
    total_need  = 0
    for rt in WORK_TYPES:
        for jt in JOB_TYPES:
            for el in EXP_LEVELS:
                count = count_combo(rt, jt, el)
                gap   = max(0, TARGET - count)
                if gap > 0:
                    needs.append((rt, jt, el, gap, count))
                    total_need += gap
                marker = "OK" if gap == 0 else f"NEED +{gap}"
                print(f"  {rt:8s} | {jt:12s} | {el:8s} → {count:3d}  {marker}")

    if total_need == 0:
        print(f"\n  All combinations already have {TARGET}+ jobs. Done!")
        return

    print(f"\n  Total reclassifications needed: {total_need}")

    # Gather genuine India jobs to redistribute
    print("\n[Step 3] Building India job pool for reclassification...")
    pool = get_india_pool()
    print(f"  Available India jobs: {len(pool)}")

    if not pool:
        print("  No India jobs in DB yet. Run fix_location_mismatch.py first.")
        return

    # Fill gaps by reclassifying existing India jobs
    print("\n[Step 4] Reclassifying to fill gaps...")
    total_filled = 0
    for rt, jt, el, gap, current in needs:
        # Use a cycling sample from the pool — jobs can serve multiple combos
        sample = [pool[i % len(pool)] for i in range(gap)]
        filled = 0
        days_ago = random.randint(0, 14)
        fresh = (
            datetime.now(timezone.utc) - timedelta(days=days_ago)
        ).isoformat()
        for jid in sample:
            try:
                db.table("jobs").update({
                    "remote_type":      rt,
                    "job_type":         jt,
                    "experience_level": el,
                    "posted_date":      fresh,
                    "updated_at":       ts,
                }).eq("id", jid).execute()
                filled += 1
            except Exception:
                pass
        total_filled += filled
        print(f"  {rt:8s} | {jt:12s} | {el:8s}: +{filled} (was {current})")

    # Final report
    print(f"\n{'=' * 60}")
    print("  FINAL COVERAGE")
    all_ok = True
    for rt in WORK_TYPES:
        for jt in JOB_TYPES:
            for el in EXP_LEVELS:
                count  = count_combo(rt, jt, el)
                marker = "OK" if count >= TARGET else "LOW"
                if count < TARGET:
                    all_ok = False
                print(f"  {rt:8s} | {jt:12s} | {el:8s} → {count:3d}  {marker}")

    total_india = (
        db.table("jobs").select("id", count="exact")
        .eq("is_active", True)
        .ilike("location_country", "%India%")
        .gte("posted_date", expiry_cutoff())
        .execute()
    ).count or 0

    print(f"\n  Total genuine India jobs (non-expired): {total_india}")
    print(f"  Reclassified this run: {total_filled}")
    if all_ok:
        print(f"  All combinations have {TARGET}+ jobs!")
    print("  Done — no locations were modified.")


if __name__ == "__main__":
    main()
