import sys
import os
import random
import uuid
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

sys.path.append(os.path.abspath("backend"))
load_dotenv(os.path.abspath("backend/.env"))

from backend.database import get_supabase_admin

TITLES = [
    "Software Engineer", "Senior Software Engineer", "Data Scientist", "Product Manager", 
    "Machine Learning Engineer", "Frontend Developer", "Backend Developer", "DevOps Engineer", 
    "Security Analyst", "Full Stack Developer", "AI Engineer", "Data Engineer", "Cloud Architect",
    "UX Researcher", "Product Designer", "Systems Engineer", "Site Reliability Engineer",
    "Staff Software Engineer", "Principal Engineer", "Junior Developer"
]

COMPANIES_INDIA = ["Flipkart", "Zomato", "Cred", "Razorpay", "Ola", "Swiggy", "Paytm", "Zerodha", "Groww", "Pine Labs"]
COMPANIES_BIG_TECH = ["Google", "Amazon", "Meta", "Apple", "Microsoft", "Netflix", "Uber", "Airbnb"]
COMPANIES_YC = ["Stripe", "Coinbase", "Dropbox", "Reddit", "Rippling", "Brex", "Deel", "Scale AI"]
COMPANIES_STEALTH = ["Stealth Startup", "NewCo", "Secret Project AI", "Stealth Web3", "AI Stealth"]

CITIES_INDIA = ["Bangalore", "Mumbai", "Delhi", "Hyderabad", "Pune", "Chennai", "Gurgaon", "Noida"]
CITIES_US = ["San Francisco", "New York", "Seattle", "Austin", "Boston", "Chicago"]
CITIES_GLOBAL = ["London", "Berlin", "Singapore", "Tokyo", "Toronto", "Sydney", "Dubai"]

TECH_STACKS = [
    ["Python", "Django", "PostgreSQL"],
    ["React", "Node.js", "MongoDB"],
    ["Java", "Spring Boot", "MySQL"],
    ["Go", "Kubernetes", "AWS"],
    ["Rust", "WebAssembly", "C++"],
    ["TypeScript", "Next.js", "Tailwind"],
    ["Python", "PyTorch", "CUDA"],
    ["Ruby", "Ruby on Rails", "Redis"],
    ["Vue", "Laravel", "PHP"]
]

def generate_job():
    job_type_rand = random.random()
    if job_type_rand < 0.3:
        company = random.choice(COMPANIES_INDIA)
        country = "India"
        city = random.choice(CITIES_INDIA)
        comp_type = "startup"
        vc = None
        stealth = False
    elif job_type_rand < 0.5:
        company = random.choice(COMPANIES_BIG_TECH)
        country = random.choice(["US", "India", "UK", "Singapore", "Germany"])
        city = random.choice(CITIES_US if country == "US" else CITIES_INDIA if country == "India" else CITIES_GLOBAL)
        comp_type = "big_tech"
        vc = None
        stealth = False
    elif job_type_rand < 0.7:
        company = random.choice(COMPANIES_YC)
        country = random.choice(["US", "India", "UK", "Singapore"])
        city = random.choice(CITIES_US if country == "US" else CITIES_INDIA if country == "India" else CITIES_GLOBAL)
        comp_type = "vc_backed"
        vc = "Y Combinator"
        stealth = False
    else:
        company = random.choice(COMPANIES_STEALTH)
        country = random.choice(["US", "India", "UK", "Germany"])
        city = random.choice(CITIES_US if country == "US" else CITIES_INDIA if country == "India" else CITIES_GLOBAL)
        comp_type = "stealth"
        vc = None
        stealth = True
        
    title = random.choice(TITLES)
    exp = random.choice(["intern", "junior", "mid", "senior", "lead", "staff", "principal"])
    
    # Adjust title based on exp
    if exp == "senior" and "Senior" not in title: title = "Senior " + title
    if exp == "junior" and "Junior" not in title: title = "Junior " + title
    
    salary_min = random.randint(30, 150) * 1000
    salary_max = salary_min + random.randint(20, 80) * 1000
    
    posted = datetime.now(timezone.utc) - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))
    
    return {
        "title": title,
        "company_name": company,
        "company_type": comp_type,
        "vc_backer": vc,
        "location_city": city,
        "location_country": country,
        "remote_type": random.choice(["remote", "hybrid", "onsite"]),
        "visa_sponsorship": random.random() < 0.15,
        "relocation_support": random.random() < 0.25,
        "salary_min": salary_min,
        "salary_max": salary_max,
        "salary_currency": "USD" if country == "US" else "INR" if country == "India" else "EUR",
        "experience_level": exp,
        "job_type": random.choice(["full-time", "contract", "internship", "part-time"]),
        "description": f"Join {company} as a {title} in {city}, {country}. You will work on cutting edge technology...",
        "tech_stack": random.choice(TECH_STACKS),
        "source_platforms": ["LinkedIn", "Wellfound", "Greenhouse"],
        "posted_date": posted.isoformat(),
        "is_stealth": stealth,
        "is_active": True,
        "dedup_hash": str(uuid.uuid4())
    }

def main():
    db = get_supabase_admin()
    
    # Generate 1000 jobs
    new_jobs = [generate_job() for _ in range(1000)]
    
    # Insert in batches of 100
    for i in range(0, 1000, 100):
        batch = new_jobs[i:i+100]
        db.table("jobs").insert(batch).execute()
        print(f"Inserted batch {i//100 + 1}/10")
        
    print("Successfully injected 1000 new jobs!")

if __name__ == "__main__":
    main()
