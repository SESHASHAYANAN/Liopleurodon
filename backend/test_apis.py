"""Quick test of all job APIs to see what actually returns data for India."""
import httpx, os, json
from dotenv import load_dotenv
load_dotenv()

# Test Adzuna India
print("=== ADZUNA INDIA ===")
r = httpx.get("https://api.adzuna.com/v1/api/jobs/in/search/1", params={
    "app_id": os.getenv("ADZUNA_APP_ID"),
    "app_key": os.getenv("ADZUNA_API_KEY"),
    "what": "software engineer",
    "results_per_page": 50,
    "sort_by": "date"
}, timeout=20)
data = r.json()
print(f"  Total count: {data.get('count', 0)}")
results = data.get("results", [])
print(f"  Page results: {len(results)}")
for j in results[:3]:
    co = (j.get("company") or {}).get("display_name", "")
    loc = (j.get("location") or {}).get("display_name", "")
    print(f"    {j.get('title', '')[:60]} | {co} | {loc}")

# Test multiple simple queries on Adzuna India
simple_queries = ["developer", "backend", "frontend", "data scientist", "devops", "machine learning", "intern", "junior engineer"]
print("\n=== ADZUNA INDIA - QUERY COVERAGE ===")
for q in simple_queries:
    try:
        r = httpx.get("https://api.adzuna.com/v1/api/jobs/in/search/1", params={
            "app_id": os.getenv("ADZUNA_APP_ID"),
            "app_key": os.getenv("ADZUNA_API_KEY"),
            "what": q, "results_per_page": 50
        }, timeout=20)
        data = r.json()
        print(f"  '{q}': {data.get('count', 0)} total, {len(data.get('results', []))} returned")
    except Exception as e:
        print(f"  '{q}': ERROR - {e}")

# Test Remotive
print("\n=== REMOTIVE ===")
try:
    r = httpx.get("https://remotive.com/api/remote-jobs", params={"category": "software-dev", "limit": 50}, timeout=20)
    jobs = r.json().get("jobs", [])
    print(f"  Got {len(jobs)} remote dev jobs")
    india_jobs = [j for j in jobs if "india" in (j.get("candidate_required_location", "") or "").lower()]
    print(f"  India-eligible: {len(india_jobs)}")
except Exception as e:
    print(f"  ERROR: {e}")

# Test Arbeitnow
print("\n=== ARBEITNOW ===")
try:
    r = httpx.get("https://www.arbeitnow.com/api/job-board-api", params={"page": 1}, timeout=20)
    jobs = r.json().get("data", [])
    print(f"  Got {len(jobs)} jobs")
except Exception as e:
    print(f"  ERROR: {e}")

# Test JSearch
print("\n=== JSEARCH ===")
api_key = os.getenv("JSEARCH_API_KEY")
if api_key:
    try:
        r = httpx.get("https://jsearch.p.rapidapi.com/search", params={
            "query": "software engineer in India", "page": "1", "num_pages": "1"
        }, headers={
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
        }, timeout=30)
        print(f"  Status: {r.status_code}")
        data = r.json()
        jobs = data.get("data", [])
        print(f"  Got {len(jobs)} jobs")
        for j in jobs[:3]:
            print(f"    {j.get('job_title', '')[:50]} | {j.get('employer_name', '')} | {j.get('job_city', '')}, {j.get('job_country', '')}")
    except Exception as e:
        print(f"  ERROR: {e}")

# Test FindWork
print("\n=== FINDWORK ===")
fwkey = os.getenv("FINDWORK_API_KEY")
if fwkey:
    try:
        r = httpx.get("https://findwork.dev/api/jobs/", params={"search": "software engineer", "location": "india"}, 
                      headers={"Authorization": f"Token {fwkey}"}, timeout=20)
        print(f"  Status: {r.status_code}")
        data = r.json()
        results = data.get("results", [])
        print(f"  Got {len(results)} jobs")
        for j in results[:3]:
            print(f"    {j.get('role', '')[:50]} | {j.get('company_name', '')} | {j.get('location', '')}")
    except Exception as e:
        print(f"  ERROR: {e}")

# Check what's in DB for India
print("\n=== SUPABASE DB CHECK ===")
from supabase import create_client
db = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))
# Total
total = db.table("jobs").select("id", count="exact").eq("is_active", True).execute()
print(f"  Total active jobs: {total.count}")
# India location
india = db.table("jobs").select("id", count="exact").eq("is_active", True).ilike("location_country", "%india%").execute()
print(f"  India (country=India): {india.count}")
india2 = db.table("jobs").select("id", count="exact").eq("is_active", True).eq("location_country", "IN").execute()
print(f"  India (country=IN): {india2.count}")
# Check what location_country values exist
sample = db.table("jobs").select("location_country, location_city").eq("is_active", True).limit(20).execute()
countries = set()
for j in sample.data:
    countries.add(j.get("location_country"))
print(f"  Sample countries in DB: {countries}")
