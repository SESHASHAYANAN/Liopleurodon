"""
Liopleurodon — Job Verification Utility
Quick diagnostic script to check active job counts and recent entries.
"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

db = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_SERVICE_KEY"],
)

total = db.table("jobs").select("id", count="exact").eq("is_active", True).execute()
print(f"Total active jobs: {total.count}")

recent = (
    db.table("jobs")
    .select("title, company_name, source_platforms, apply_url")
    .eq("is_active", True)
    .order("created_at", desc=True)
    .limit(10)
    .execute()
)
print("\nNewest 10 jobs:")
for j in recent.data:
    print(f"  - {j['title'][:50]} @ {j['company_name'][:30]} | {j['source_platforms']}")
