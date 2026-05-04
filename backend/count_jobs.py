from database import get_supabase_admin

def count_jobs():
    db = get_supabase_admin()
    res = db.table("jobs").select("id", count="exact").execute()
    print("Total jobs in DB:", res.count)

if __name__ == "__main__":
    count_jobs()
