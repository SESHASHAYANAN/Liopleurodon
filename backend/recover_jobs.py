"""
Liopleurodon — Job Recovery Script
Re-activates all valid jobs that were wrongly deactivated by the aggressive
stale marking system. This recovers the ~8,000+ jobs lost due to the
30-minute stale cutoff bug.

Can be run standalone: python recover_jobs.py
Also called automatically on backend startup from main.py
"""

import asyncio
import sys
import os
import re
from datetime import datetime, timezone, timedelta

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Force unbuffered output
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

# Load .env from parent directory (project root)
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)
# Also try local .env
load_dotenv()

from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: SUPABASE_URL or SUPABASE_SERVICE_KEY not set!", flush=True)
    sys.exit(1)

print(f"Connecting to Supabase: {SUPABASE_URL[:30]}...", flush=True)
db = create_client(SUPABASE_URL, SUPABASE_KEY)

# Jobs posted within this many days are eligible for recovery
MAX_AGE_DAYS = 45

# Non-tech titles to skip during recovery
NON_TECH = [
    "sales", "marketing manager", "human resources", "recruiter",
    "customer support", "customer success", "bpo", "call center",
    "account executive", "business development", "content writer",
    "copywriter", "talent acquisition", "receptionist", "secretary",
    "data entry", "typist", "housekeeping",
]


def is_valid_job(job: dict) -> bool:
    """Check if a deactivated job should be re-activated."""
    title = (job.get("title") or "").strip()
    company = (job.get("company_name") or "").strip()
    url = (job.get("apply_url") or "").strip()

    if not title or len(title) < 5:
        return False
    if not company or len(company) < 2:
        return False
    if not url or not url.startswith("http"):
        return False

    title_lower = title.lower()
    if any(nt in title_lower for nt in NON_TECH):
        return False
    if any(title_lower.startswith(m) for m in ["test ", "mock ", "dummy ", "placeholder "]):
        return False

    return True


def classify_experience_level(title: str) -> str:
    """Classify experience level from job title."""
    t = title.lower().strip()
    if any(re.search(p, t) for p in [r'\bintern\b', r'\binternship\b', r'\btrainee\b', r'\bapprentice\b']):
        return "intern"
    if any(re.search(p, t) for p in [r'\bprincipal\b', r'\bdistinguished\b', r'\bfellow\b']):
        return "principal"
    if any(re.search(p, t) for p in [r'\bstaff\b', r'\bvp\b', r'\bdirector\b', r'\bchief\b', r'\bhead\s+of\b']):
        return "staff"
    if any(re.search(p, t) for p in [r'\blead\b', r'\btech\s*lead\b', r'\bmanager\b']):
        return "lead"
    if any(re.search(p, t) for p in [r'\bsenior\b', r'\bsr\.?\s', r'\barchitect\b']):
        return "senior"
    if any(re.search(p, t) for p in [r'\bjunior\b', r'\bjr\.?\s', r'\bassociate\b', r'\bentry[\s-]?level\b', r'\bgraduate\b', r'\bfresher\b']):
        return "junior"
    return "mid"


def classify_job_type(title: str) -> str:
    t = title.lower()
    if any(k in t for k in ["intern", "internship", "trainee"]):
        return "internship"
    if any(k in t for k in ["freelance", "freelancer"]):
        return "freelance"
    if any(k in t for k in ["contract", "contractor"]):
        return "contract"
    if any(k in t for k in ["part-time", "part time"]):
        return "part-time"
    return "full-time"


def normalize_remote_type(remote: str) -> str:
    r = (remote or "").lower().strip()
    if r in ("remote", "hybrid", "onsite"):
        return r
    return "onsite"


async def recover_all_jobs() -> int:
    """
    Re-activate all valid deactivated jobs posted within the last MAX_AGE_DAYS days.
    Returns the number of recovered jobs.
    """
    print("=" * 60, flush=True)
    print("  LIOPLEURODON — Job Recovery", flush=True)
    print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}", flush=True)
    print("=" * 60, flush=True)

    # Count current state
    try:
        active_count = db.table("jobs").select("id", count="exact").eq("is_active", True).execute().count or 0
        inactive_count = db.table("jobs").select("id", count="exact").eq("is_active", False).execute().count or 0
    except Exception as e:
        print(f"  Count query error: {e}", flush=True)
        active_count = 0
        inactive_count = 0

    print(f"\n  Current active: {active_count}", flush=True)
    print(f"  Current inactive: {inactive_count}", flush=True)

    cutoff = (datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)).isoformat()
    now = datetime.now(timezone.utc).isoformat()

    recovered = 0
    skipped = 0
    offset = 0
    batch_size = 200

    print(f"\n[Recovery] Scanning inactive jobs posted after {cutoff[:10]}...", flush=True)

    while True:
        try:
            batch = (
                db.table("jobs")
                .select("id, title, company_name, apply_url, posted_date, experience_level, job_type, remote_type")
                .eq("is_active", False)
                .gte("posted_date", cutoff)
                .range(offset, offset + batch_size - 1)
                .execute()
            )
        except Exception as e:
            print(f"  [Recovery] Query error at offset {offset}: {e}", flush=True)
            break

        if not batch.data:
            print(f"  [Recovery] No more inactive jobs to process at offset {offset}", flush=True)
            break

        print(f"  [Recovery] Processing batch at offset {offset}, {len(batch.data)} jobs...", flush=True)

        for job in batch.data:
            if not is_valid_job(job):
                skipped += 1
                continue

            title = job.get("title", "")
            update_data = {
                "is_active": True,
                "updated_at": now,
                "experience_level": classify_experience_level(title),
                "job_type": classify_job_type(title),
                "remote_type": normalize_remote_type(job.get("remote_type", "")),
            }

            try:
                db.table("jobs").update(update_data).eq("id", job["id"]).execute()
                recovered += 1
                if recovered % 100 == 0:
                    print(f"    Recovered {recovered} jobs so far...", flush=True)
            except Exception:
                skipped += 1

        if len(batch.data) < batch_size:
            break
        offset += batch_size

    # Also fix categorization for active jobs
    print(f"\n[Recovery] Fixing categorization for active jobs...", flush=True)
    fix_offset = 0
    fixed = 0
    while True:
        try:
            batch = (
                db.table("jobs")
                .select("id, title, experience_level, job_type, remote_type")
                .eq("is_active", True)
                .range(fix_offset, fix_offset + batch_size - 1)
                .execute()
            )
        except:
            break

        if not batch.data:
            break

        for job in batch.data:
            title = job.get("title", "")
            correct_exp = classify_experience_level(title)
            correct_jtype = classify_job_type(title)
            correct_remote = normalize_remote_type(job.get("remote_type", ""))

            needs_fix = (
                job.get("experience_level") != correct_exp or
                job.get("remote_type") != correct_remote or
                (not job.get("job_type"))
            )

            if needs_fix:
                try:
                    db.table("jobs").update({
                        "experience_level": correct_exp,
                        "job_type": correct_jtype,
                        "remote_type": correct_remote,
                        "updated_at": now,
                    }).eq("id", job["id"]).execute()
                    fixed += 1
                    if fixed % 200 == 0:
                        print(f"    Fixed {fixed} jobs...", flush=True)
                except:
                    pass

        if len(batch.data) < batch_size:
            break
        fix_offset += batch_size

    # Final stats
    try:
        final_active = db.table("jobs").select("id", count="exact").eq("is_active", True).execute().count or 0
    except:
        final_active = active_count + recovered

    print(f"\n{'=' * 60}", flush=True)
    print(f"  RECOVERY COMPLETE", flush=True)
    print(f"  Before:      {active_count} active", flush=True)
    print(f"  Recovered:   {recovered} jobs re-activated", flush=True)
    print(f"  Fixed:       {fixed} jobs re-categorized", flush=True)
    print(f"  Skipped:     {skipped} invalid/non-tech jobs", flush=True)
    print(f"  After:       {final_active} active", flush=True)
    print(f"{'=' * 60}", flush=True)

    return recovered


async def main():
    await recover_all_jobs()


if __name__ == "__main__":
    asyncio.run(main())
