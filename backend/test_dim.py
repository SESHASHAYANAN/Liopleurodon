import asyncio
from database import get_supabase_admin

async def main():
    db = get_supabase_admin()
    res = db.table("jobs").select("embedding").limit(1).execute()
    if res.data and res.data[0].get("embedding"):
        print("Dim:", len(res.data[0]["embedding"]))
    else:
        print("No embeddings found")

asyncio.run(main())
