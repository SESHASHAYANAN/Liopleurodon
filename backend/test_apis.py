"""
Liopleurodon — API Connectivity Diagnostic
-------------------------------------------
Run this script to verify that all configured job APIs are reachable
and returning data. Useful for debugging scraper issues in development.

Usage:
    cd backend && python test_apis.py
"""

import os
import httpx
from dotenv import load_dotenv

load_dotenv()


def test_adzuna_india():
    print("=== ADZUNA INDIA ===")
    r = httpx.get(
        "https://api.adzuna.com/v1/api/jobs/in/search/1",
        params={
            "app_id":          os.getenv("ADZUNA_APP_ID"),
            "app_key":         os.getenv("ADZUNA_API_KEY"),
            "what":            "software engineer",
            "results_per_page": 50,
            "sort_by":         "date",
        },
        timeout=20,
    )
    data = r.json()
    results = data.get("results", [])
    print(f"  Total count: {data.get('count', 0)}")
    print(f"  Page results: {len(results)}")
    for j in results[:3]:
        co  = (j.get("company") or {}).get("display_name", "")
        loc = (j.get("location") or {}).get("display_name", "")
        print(f"    {j.get('title', '')[:60]} | {co} | {loc}")


def test_adzuna_query_coverage():
    print("\n=== ADZUNA INDIA — QUERY COVERAGE ===")
    queries = [
        "developer", "backend", "frontend", "data scientist",
        "devops", "machine learning", "intern", "junior engineer",
    ]
    for q in queries:
        try:
            r = httpx.get(
                "https://api.adzuna.com/v1/api/jobs/in/search/1",
                params={
                    "app_id":          os.getenv("ADZUNA_APP_ID"),
                    "app_key":         os.getenv("ADZUNA_API_KEY"),
                    "what":            q,
                    "results_per_page": 50,
                },
                timeout=20,
            )
            data = r.json()
            print(f"  '{q}': {data.get('count', 0)} total, {len(data.get('results', []))} returned")
        except Exception as e:
            print(f"  '{q}': ERROR — {e}")


def test_remotive():
    print("\n=== REMOTIVE ===")
    try:
        r = httpx.get(
            "https://remotive.com/api/remote-jobs",
            params={"category": "software-dev", "limit": 50},
            timeout=20,
        )
        jobs = r.json().get("jobs", [])
        india_jobs = [
            j for j in jobs
            if "india" in (j.get("candidate_required_location") or "").lower()
        ]
        print(f"  Got {len(jobs)} remote dev jobs")
        print(f"  India-eligible: {len(india_jobs)}")
    except Exception as e:
        print(f"  ERROR: {e}")


def test_arbeitnow():
    print("\n=== ARBEITNOW ===")
    try:
        r = httpx.get(
            "https://www.arbeitnow.com/api/job-board-api",
            params={"page": 1},
            timeout=20,
        )
        jobs = r.json().get("data", [])
        print(f"  Got {len(jobs)} jobs")
    except Exception as e:
        print(f"  ERROR: {e}")


def test_jsearch():
    print("\n=== JSEARCH ===")
    api_key = os.getenv("JSEARCH_API_KEY")
    if not api_key:
        print("  JSEARCH_API_KEY not set — skipping.")
        return
    try:
        r = httpx.get(
            "https://jsearch.p.rapidapi.com/search",
            params={"query": "software engineer in India", "page": "1", "num_pages": "1"},
            headers={
                "X-RapidAPI-Key":  api_key,
                "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
            },
            timeout=30,
        )
        jobs = r.json().get("data", [])
        print(f"  Status: {r.status_code} | Got {len(jobs)} jobs")
        for j in jobs[:3]:
            print(f"    {j.get('job_title', '')[:50]} | {j.get('employer_name', '')} | {j.get('job_city', '')}, {j.get('job_country', '')}")
    except Exception as e:
        print(f"  ERROR: {e}")


def test_findwork():
    print("\n=== FINDWORK ===")
    fwkey = os.getenv("FINDWORK_API_KEY")
    if not fwkey:
        print("  FINDWORK_API_KEY not set — skipping.")
        return
    try:
        r = httpx.get(
            "https://findwork.dev/api/jobs/",
            params={"search": "software engineer", "location": "india"},
            headers={"Authorization": f"Token {fwkey}"},
            timeout=20,
        )
        results = r.json().get("results", [])
        print(f"  Status: {r.status_code} | Got {len(results)} jobs")
        for j in results[:3]:
            print(f"    {j.get('role', '')[:50]} | {j.get('company_name', '')} | {j.get('location', '')}")
    except Exception as e:
        print(f"  ERROR: {e}")


def test_database():
    print("\n=== SUPABASE DB CHECK ===")
    from supabase import create_client
    db = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])

    total  = db.table("jobs").select("id", count="exact").eq("is_active", True).execute()
    india  = db.table("jobs").select("id", count="exact").eq("is_active", True).ilike("location_country", "%india%").execute()
    print(f"  Total active jobs:        {total.count}")
    print(f"  India jobs (non-expired): {india.count}")

    sample   = db.table("jobs").select("location_country").eq("is_active", True).limit(50).execute()
    countries = {j.get("location_country") for j in (sample.data or [])}
    print(f"  Sample location_country values: {countries}")


def main():
    test_adzuna_india()
    test_adzuna_query_coverage()
    test_remotive()
    test_arbeitnow()
    test_jsearch()
    test_findwork()
    test_database()


if __name__ == "__main__":
    main()
