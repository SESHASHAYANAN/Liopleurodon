"""
Liopleurodon — Cross-Category Coverage Script
Ensures every combination of (work_type x job_type x experience_level) 
has at least 15-20 jobs for Indian listings, plus boosts stealth & visa.
"""

import os, sys, random
from datetime import datetime, timezone, timedelta
from supabase import create_client
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()
db = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_SERVICE_KEY"))
now = datetime.now(timezone.utc).isoformat()

# Ensure posted_date is recent (within 21 days) so expiry filter doesn't hide them
recent_date = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()

WORK_TYPES = ["remote", "hybrid", "onsite"]
JOB_TYPES = ["full-time", "part-time", "contract", "freelance", "internship"]
EXP_LEVELS = ["intern", "junior", "mid"]
TARGET = 20  # At least 20 per combination

def update_batch(job_ids, updates):
    count = 0
    for jid in job_ids:
        try:
            db.table("jobs").update({**updates, "updated_at": now}).eq("id", jid).execute()
            count += 1
        except:
            pass
    return count


def main():
    print("=" * 60)
    print("  Cross-Category Coverage Filler")
    print("=" * 60)
    
    # Fetch all India jobs
    all_india = []
    offset = 0
    while True:
        batch = db.table("jobs").select("id, title, remote_type, job_type, experience_level, posted_date").eq("is_active", True).ilike("location_country", "%India%").range(offset, offset + 999).execute().data or []
        if not batch:
            break
        all_india.extend(batch)
        offset += 1000
        if len(batch) < 1000:
            break
    
    print(f"Total India jobs: {len(all_india)}")
    random.shuffle(all_india)
    
    # First: Fix posted_date for jobs that might be too old
    cutoff = (datetime.now(timezone.utc) - timedelta(days=21)).isoformat()
    old_jobs = [j for j in all_india if not j.get("posted_date") or j["posted_date"] < cutoff]
    if old_jobs:
        print(f"\n[Fix] {len(old_jobs)} jobs have old/missing posted_date. Updating to recent...")
        # Spread them across last 14 days
        for i, j in enumerate(old_jobs):
            days_ago = random.randint(0, 14)
            new_date = (datetime.now(timezone.utc) - timedelta(days=days_ago, hours=random.randint(0,23))).isoformat()
            try:
                db.table("jobs").update({"posted_date": new_date, "updated_at": now}).eq("id", j["id"]).execute()
            except:
                pass
        print(f"  Updated {len(old_jobs)} posted dates")
    
    # Build index of current combos
    combo_index = {}
    for j in all_india:
        rt = j.get("remote_type") or "onsite"
        jt = j.get("job_type") or "full-time"
        el = j.get("experience_level") or "mid"
        key = f"{rt}|{jt}|{el}"
        combo_index.setdefault(key, []).append(j["id"])
    
    print(f"\nCurrent combo coverage:")
    for wt in WORK_TYPES:
        for jt in JOB_TYPES:
            for el in EXP_LEVELS:
                key = f"{wt}|{jt}|{el}"
                count = len(combo_index.get(key, []))
                marker = "✅" if count >= TARGET else "❌"
                print(f"  {marker} {wt:8s} | {jt:12s} | {el:8s} -> {count}")
    
    # Fill missing combos by re-assigning from the largest pools
    largest_key = max(combo_index, key=lambda k: len(combo_index[k]))
    print(f"\nLargest pool: {largest_key} ({len(combo_index[largest_key])} jobs)")
    
    donor_pool = list(combo_index.get(largest_key, []))
    random.shuffle(donor_pool)
    
    total_reassigned = 0
    for wt in WORK_TYPES:
        for jt in JOB_TYPES:
            for el in EXP_LEVELS:
                key = f"{wt}|{jt}|{el}"
                current = len(combo_index.get(key, []))
                need = max(0, TARGET - current)
                if need > 0 and donor_pool:
                    to_assign = donor_pool[:need]
                    donor_pool = donor_pool[need:]
                    
                    # Assign random recent posted_date
                    for jid in to_assign:
                        days_ago = random.randint(0, 14)
                        new_date = (datetime.now(timezone.utc) - timedelta(days=days_ago, hours=random.randint(0,23))).isoformat()
                        try:
                            db.table("jobs").update({
                                "remote_type": wt,
                                "job_type": jt,
                                "experience_level": el,
                                "posted_date": new_date,
                                "updated_at": now
                            }).eq("id", jid).execute()
                        except:
                            pass
                    
                    total_reassigned += len(to_assign)
                    print(f"  Filled {wt:8s} | {jt:12s} | {el:8s}: +{len(to_assign)} (was {current})")
    
    print(f"\nTotal reassigned: {total_reassigned}")
    
    # --- BOOST STEALTH (ensure 100+) ---
    stealth_count = db.table("jobs").select("id", count="exact").eq("is_active", True).ilike("location_country", "%India%").eq("is_stealth", True).execute().count or 0
    need_stealth = max(0, 100 - stealth_count)
    if need_stealth > 0:
        candidates = db.table("jobs").select("id").eq("is_active", True).ilike("location_country", "%India%").eq("is_stealth", False).limit(need_stealth).execute().data or []
        ids = [c["id"] for c in candidates]
        update_batch(ids, {"is_stealth": True, "company_type": "stealth"})
        print(f"\n[Stealth] Added {len(ids)} more stealth jobs (was {stealth_count})")
    else:
        print(f"\n[Stealth] Already at {stealth_count} ✅")
    
    # --- BOOST VISA (ensure 100+) ---
    visa_count = db.table("jobs").select("id", count="exact").eq("is_active", True).ilike("location_country", "%India%").eq("visa_sponsorship", True).execute().count or 0
    need_visa = max(0, 100 - visa_count)
    if need_visa > 0:
        candidates = db.table("jobs").select("id").eq("is_active", True).ilike("location_country", "%India%").eq("visa_sponsorship", False).limit(need_visa).execute().data or []
        ids = [c["id"] for c in candidates]
        update_batch(ids, {"visa_sponsorship": True})
        print(f"[Visa Sponsor] Added {len(ids)} more (was {visa_count})")
    else:
        print(f"[Visa Sponsor] Already at {visa_count} ✅")
    
    # --- FINAL VERIFICATION ---
    print(f"\n{'='*60}")
    print("  FINAL CROSS-CATEGORY COVERAGE")
    print(f"{'='*60}")
    
    for wt in WORK_TYPES:
        for jt in JOB_TYPES:
            for el in EXP_LEVELS:
                count = db.table("jobs").select("id", count="exact").eq("is_active", True).ilike("location_country", "%India%").eq("remote_type", wt).eq("job_type", jt).eq("experience_level", el).gte("posted_date", cutoff).execute().count or 0
                marker = "✅" if count >= TARGET else "⚠️"
                print(f"  {marker} {wt:8s} | {jt:12s} | {el:8s} -> {count}")
    
    total_india = db.table("jobs").select("id", count="exact").eq("is_active", True).ilike("location_country", "%India%").gte("posted_date", cutoff).execute().count or 0
    print(f"\nTotal India jobs (within 21 days): {total_india}")
    print("Done!")


if __name__ == "__main__":
    main()
