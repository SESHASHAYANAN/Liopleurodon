import asyncio
import os
import sys
from dotenv import load_dotenv

# Add backend dir to path so we can import database
sys.path.append(os.path.abspath("backend"))
load_dotenv(os.path.abspath("backend/.env"))

from backend.database import get_supabase_admin

def main():
    db = get_supabase_admin()
    
    # Check all jobs for location and experience
    resp = db.table("jobs").select("id, title, location_city, location_country, experience_level, company_type").execute()
    jobs = resp.data
    
    print(f"Total jobs: {len(jobs)}")
    
    india_jobs = [j for j in jobs if j.get('location_country') and 'india' in j['location_country'].lower()]
    print(f"India jobs (by country field): {len(india_jobs)}")
    
    junior_jobs = [j for j in jobs if j.get('experience_level') == 'junior']
    print(f"Junior jobs: {len(junior_jobs)}")
    
    india_junior = [j for j in india_jobs if j.get('experience_level') == 'junior']
    print(f"India + Junior: {len(india_junior)}")

    # Check distinct countries
    countries = set(j.get('location_country') for j in jobs)
    print(f"Distinct countries: {countries}")

if __name__ == "__main__":
    main()
