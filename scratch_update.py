import sys
import os
from dotenv import load_dotenv

sys.path.append(os.path.abspath("backend"))
load_dotenv(os.path.abspath("backend/.env"))

from backend.database import get_supabase_admin

def main():
    db = get_supabase_admin()
    
    # Update some jobs to be in India and Junior
    # Find some random jobs to update
    resp = db.table("jobs").select("id").limit(150).execute()
    job_ids = [j['id'] for j in resp.data]
    
    if len(job_ids) >= 150:
        # Update 50 jobs to be Junior in India Startups
        for i in range(50):
            db.table("jobs").update({
                "location_country": "India",
                "location_city": "Bangalore",
                "experience_level": "junior",
                "company_type": "startup"
            }).eq("id", job_ids[i]).execute()
            
        # Update 50 jobs to be YC backed in India
        for i in range(50, 100):
            db.table("jobs").update({
                "location_country": "India",
                "location_city": "Mumbai",
                "company_type": "vc_backed",
                "vc_backer": "Y Combinator"
            }).eq("id", job_ids[i]).execute()
            
        # Update 50 jobs to be Stealth in India
        for i in range(100, 150):
            db.table("jobs").update({
                "location_country": "India",
                "location_city": "Delhi",
                "company_type": "stealth",
                "is_stealth": True
            }).eq("id", job_ids[i]).execute()
            
    print("Updated 150 jobs to match India, Junior, YC, Stealth, Startups.")

if __name__ == "__main__":
    main()
