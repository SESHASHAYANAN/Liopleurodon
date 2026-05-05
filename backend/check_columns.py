"""Run migration 002 to add is_featured and last_seen_at columns."""
import os
from dotenv import load_dotenv
load_dotenv()

from supabase import create_client

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_KEY")
db = create_client(url, key)

# Add columns via RPC or direct SQL
# Since supabase-py doesn't support raw SQL easily, we'll test if columns exist
# and let the seed data / scraper handle gracefully

print("Testing if is_featured column exists...")
try:
    result = db.table("jobs").select("is_featured").limit(1).execute()
    print(f"is_featured column exists. Result: {result.data}")
except Exception as e:
    print(f"is_featured column does not exist: {e}")
    print("Please run this SQL in the Supabase SQL Editor:")
    print("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS is_featured BOOLEAN DEFAULT false;")
    print("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS last_seen_at TIMESTAMPTZ;")

print("\nTesting if last_seen_at column exists...")
try:
    result = db.table("jobs").select("last_seen_at").limit(1).execute()
    print(f"last_seen_at column exists. Result: {result.data}")
except Exception as e:
    print(f"last_seen_at column does not exist: {e}")
