"""
Liopleurodon — Bulk ATS Fix
Re-detects ATS for all active jobs currently showing 'Unknown ATS'.
Uses the improved ATS detector with fixed regex patterns, expanded
company mapping, and domain inference.

Usage: python fix_ats_bulk.py
"""

import sys
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from supabase import create_client

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from services.ats_detector import detect_ats_complete

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
db = create_client(SUPABASE_URL, SUPABASE_KEY)

NOW = datetime.now(timezone.utc).isoformat()


def fix_all_ats():
    """Re-detect ATS for ALL active jobs, not just Unknown ones."""
    print("=" * 65)
    print("  LIOPLEURODON — Bulk ATS Detection Fix")
    print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 65)

    # Count current state
    total_active = db.table("jobs").select("id", count="exact").eq("is_active", True).execute().count or 0
    print(f"\n  Total active jobs: {total_active}")

    fixed = 0
    already_good = 0
    still_unknown = 0
    offset = 0
    ats_counts = {}

    print(f"\n[1/2] Re-detecting ATS for all active jobs...\n")

    while True:
        batch = (
            db.table("jobs")
            .select("id, title, company_name, apply_url, ats_detected")
            .eq("is_active", True)
            .range(offset, offset + 499)
            .execute()
            .data or []
        )
        if not batch:
            break

        for job in batch:
            company = job.get("company_name", "")
            url = job.get("apply_url", "")
            old_ats = job.get("ats_detected", "Unknown ATS")

            new_ats = detect_ats_complete(company, url)

            # Track the ATS
            ats_counts[new_ats] = ats_counts.get(new_ats, 0) + 1

            if new_ats != old_ats:
                try:
                    update_data = {"ats_detected": new_ats, "updated_at": NOW}
                    db.table("jobs").update(update_data).eq("id", job["id"]).execute()
                    fixed += 1

                    if fixed <= 15:
                        print(f"  Fixed: '{job.get('title', '')[:45]}' — {old_ats} → {new_ats}")
                except Exception as e:
                    err = str(e).lower()
                    # If ats_detected column doesn't exist, skip silently
                    if "column" in err and "ats_detected" in err:
                        pass
                    elif fixed < 3:
                        print(f"  [DB Error] {e}")
            else:
                if old_ats == "Unknown ATS":
                    still_unknown += 1
                else:
                    already_good += 1

        offset += 500
        if len(batch) < 500:
            break

        if offset % 2000 == 0:
            print(f"    Processed {offset} jobs... ({fixed} fixed so far)")

    # Final report
    print(f"\n{'=' * 65}")
    print("  ATS DETECTION RESULTS")
    print(f"{'=' * 65}")
    print(f"  Total processed:  {offset}")
    print(f"  Fixed:            {fixed}")
    print(f"  Already correct:  {already_good}")
    print(f"  Still unknown:    {still_unknown}")
    pct_known = ((total_active - still_unknown) * 100) // max(total_active, 1)
    print(f"  Detection rate:   {pct_known}%")

    # Top ATS breakdown
    print(f"\n  {'─' * 40}")
    print("  ATS BREAKDOWN (top 20):")
    sorted_ats = sorted(ats_counts.items(), key=lambda x: x[1], reverse=True)
    for ats_name, count in sorted_ats[:20]:
        pct = count * 100 // max(total_active, 1)
        print(f"    {ats_name:30s}: {count:>5} ({pct}%)")

    print(f"{'=' * 65}")


if __name__ == "__main__":
    fix_all_ats()
