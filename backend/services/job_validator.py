"""
Liopleurodon — Job Validator
Strict validation for country, experience level, and data quality.
Runs BEFORE insertion and can also be used to clean existing records.
"""

import re
from typing import Optional


# ── Indian Cities — canonical list for validation ─────────────────────────
INDIA_CITIES = {
    "mumbai", "delhi", "bangalore", "bengaluru", "hyderabad", "chennai",
    "kolkata", "pune", "ahmedabad", "jaipur", "lucknow", "noida",
    "gurgaon", "gurugram", "chandigarh", "indore", "nagpur", "coimbatore",
    "thiruvananthapuram", "trivandrum", "kochi", "cochin", "bhopal",
    "visakhapatnam", "vizag", "patna", "vadodara", "surat", "mysore",
    "mysuru", "mangalore", "mangaluru", "dehradun", "ranchi", "guwahati",
    "bhubaneswar", "madurai", "tiruchirappalli", "agra", "varanasi",
    "nashik", "rajkot", "jodhpur", "raipur", "amritsar", "navi mumbai",
    "thane", "faridabad", "ghaziabad", "meerut", "greater noida",
    "new delhi", "old delhi", "east delhi", "west delhi",
}

# ── Foreign markers — if ANY of these appear in title, the job is NOT India ─
FOREIGN_COUNTRY_MARKERS = {
    # Country names
    "uk", "united kingdom", "us", "usa", "united states", "america",
    "canada", "australia", "germany", "france", "netherlands", "ireland",
    "switzerland", "sweden", "norway", "denmark", "finland", "japan",
    "singapore", "brazil", "spain", "italy", "poland", "czech",
    "austria", "belgium", "new zealand", "israel", "uae", "dubai",
    "qatar", "saudi", "south korea", "mexico", "portugal",
    # Major foreign cities
    "london", "new york", "san francisco", "los angeles", "seattle",
    "austin", "boston", "chicago", "toronto", "vancouver", "montreal",
    "sydney", "melbourne", "berlin", "munich", "amsterdam", "dublin",
    "paris", "zurich", "stockholm", "oslo", "copenhagen", "helsinki",
    "tokyo", "barcelona", "madrid", "milan", "rome", "prague",
    "warsaw", "lisbon", "vienna", "brussels", "tel aviv",
}

# ── Currency / salary signals for non-India ───────────────────────────────
NON_INDIA_SALARY_SIGNALS = {"gbp", "£", "eur", "€", "usd", "$", "aud", "cad", "sgd", "chf"}

# ── Experience Level Classification ───────────────────────────────────────

# Patterns that indicate SENIOR-level roles (high priority — checked first)
SENIOR_PATTERNS = [
    r'\bsenior\b', r'\bsr\.?\s', r'\blead\b', r'\bprincipal\b',
    r'\bstaff\b', r'\barchitect\b', r'\bdirector\b', r'\bhead\s+of\b',
    r'\bvp\b', r'\bchief\b', r'\bmanager\b', r'\bexecutive\b',
]

# Patterns that indicate LEAD-level roles
LEAD_PATTERNS = [
    r'\blead\b', r'\bteam\s*lead\b', r'\btech\s*lead\b',
    r'\bengineering\s*lead\b', r'\bmanager\b',
]

# Patterns that indicate STAFF-level roles
STAFF_PATTERNS = [
    r'\bstaff\b', r'\bprincipal\b', r'\bdistinguished\b',
    r'\bvp\b', r'\bdirector\b', r'\bchief\b', r'\bhead\s+of\b',
    r'\bfellow\b',
]

# Patterns that indicate JUNIOR-level roles
JUNIOR_PATTERNS = [
    r'\bjunior\b', r'\bjr\.?\s', r'\bjr$',
    r'\bassociate\b', r'\bentry[\s-]?level\b', r'\bgraduate\b',
    r'\bnew\s*grad\b', r'\bfresher\b',
]

# Patterns that indicate INTERN-level roles
INTERN_PATTERNS = [
    r'\bintern\b', r'\binternship\b', r'\btrainee\b',
    r'\bapprentice\b', r'\bco-?op\b',
]


def classify_experience_level(title: str, description: str = "") -> str:
    """
    Classify experience level strictly from the job TITLE.
    Title is the primary signal — description is secondary.
    
    Priority order: intern > staff > lead > senior > junior > mid (default).
    """
    t = title.lower().strip()
    
    # 1. Intern — highest priority (internship is a specific category)
    if any(re.search(p, t) for p in INTERN_PATTERNS):
        return "intern"
    
    # 2. Staff/Principal/VP/Director — very senior
    if any(re.search(p, t) for p in STAFF_PATTERNS):
        return "staff"
    
    # 3. Lead — team/tech/engineering lead
    if any(re.search(p, t) for p in LEAD_PATTERNS):
        return "lead"
    
    # 4. Senior — "senior", "sr.", etc.
    if any(re.search(p, t) for p in SENIOR_PATTERNS):
        return "senior"
    
    # 5. Junior — "junior", "jr.", "associate", "entry-level", "graduate", "fresher"
    if any(re.search(p, t) for p in JUNIOR_PATTERNS):
        return "junior"
    
    # 6. Default = mid
    return "mid"


def validate_india_job(job: dict) -> bool:
    """
    Validate that a job tagged as India is ACTUALLY an India job.
    Returns False if any signal indicates it's a foreign job.
    """
    title = (job.get("title") or "").lower()
    description = (job.get("description") or "").lower()
    location_city = (job.get("location_city") or "").lower()
    apply_url = (job.get("apply_url") or "").lower()
    salary_currency = (job.get("salary_currency") or "").lower()
    
    # 1. Check title for foreign country/city markers
    #    e.g., "Technical Account Manager - UK" → NOT India
    for marker in FOREIGN_COUNTRY_MARKERS:
        # Match whole word or at end after " - " or in parentheses
        patterns = [
            rf'\b{re.escape(marker)}\b',
            rf'\(\s*{re.escape(marker)}\s*\)',
            rf'-\s*{re.escape(marker)}\s*$',
        ]
        for pattern in patterns:
            if re.search(pattern, title):
                return False
    
    # 2. Check salary currency — GBP, EUR, USD = not India
    if salary_currency in NON_INDIA_SALARY_SIGNALS:
        return False
    
    # 3. Check description for strong non-India signals
    #    Look for salary in £, €, $ format
    if re.search(r'[£€]\s*\d', description[:500]):
        return False
    
    # 4. Check apply_url for foreign job board domains
    foreign_domains = [".co.uk", "uk.indeed", "indeed.co.uk", ".de/", ".fr/"]
    if any(d in apply_url for d in foreign_domains):
        return False
    
    # 5. Check location_city — if it's a known foreign city
    for marker in FOREIGN_COUNTRY_MARKERS:
        if marker in location_city:
            return False
    
    # 6. Positive signal: known Indian city
    for city in INDIA_CITIES:
        if city in location_city:
            return True
    
    # 7. If location_city is empty or generic, it's ambiguous — allow it
    return True


def validate_job_data_quality(job: dict) -> tuple[bool, str]:
    """
    Validate overall job data quality. Returns (is_valid, reason).
    Call this BEFORE inserting any job into the database.
    """
    title = (job.get("title") or "").strip()
    company = (job.get("company_name") or "").strip()
    apply_url = (job.get("apply_url") or "").strip()
    
    # Basic required fields
    if not title or len(title) < 5:
        return False, "title too short"
    if not company or len(company) < 2:
        return False, "company name too short"
    if not apply_url or not apply_url.startswith("http"):
        return False, "invalid apply_url"
    
    # Reject fake/test jobs
    fake_markers = ["test", "mock", "placeholder", "dummy", "sample", "example"]
    if any(m in title.lower() for m in fake_markers):
        return False, "fake/test job"
    
    # Country-location cross-validation
    country = (job.get("location_country") or "").lower()
    if country in ("india", "in"):
        if not validate_india_job(job):
            return False, "location mismatch: tagged India but contains foreign signals"
    
    # Experience level must match title
    stored_exp = job.get("experience_level", "")
    correct_exp = classify_experience_level(title, job.get("description", ""))
    if stored_exp and stored_exp != correct_exp:
        # Auto-correct instead of rejecting
        job["experience_level"] = correct_exp
    
    return True, "ok"


def sanitize_job_before_insert(job: dict) -> dict:
    """
    Sanitize and auto-correct fields before database insertion.
    This ensures experience_level, location, etc. are always correct.
    """
    title = job.get("title", "")
    desc = job.get("description", "")
    
    # 1. Always re-classify experience level from title (never trust source data)
    job["experience_level"] = classify_experience_level(title, desc)
    
    # 2. Validate India location if tagged as India
    country = (job.get("location_country") or "").lower()
    if country in ("india", "in"):
        if not validate_india_job(job):
            # Foreign job wrongly tagged as India — clear location
            job["location_country"] = None
            job["location_city"] = None
    
    # 3. Normalize country codes to full names
    country_code_map = {
        "in": "India", "us": "United States", "gb": "United Kingdom",
        "ca": "Canada", "au": "Australia", "de": "Germany",
        "sg": "Singapore", "fr": "France", "nl": "Netherlands",
    }
    if job.get("location_country"):
        lc = job["location_country"].lower().strip()
        if lc in country_code_map:
            job["location_country"] = country_code_map[lc]
    
    # 4. Normalize job_type
    jt = (job.get("job_type") or "").lower().strip()
    type_map = {
        "fulltime": "full-time", "full_time": "full-time", "full time": "full-time",
        "parttime": "part-time", "part_time": "part-time", "part time": "part-time",
        "contractor": "contract", "freelancer": "freelance",
        "intern": "internship",
    }
    job["job_type"] = type_map.get(jt, jt) or "full-time"
    
    # 5. Normalize remote_type
    rt = (job.get("remote_type") or "").lower().strip()
    if rt not in ("remote", "hybrid", "onsite"):
        job["remote_type"] = "onsite"
    
    return job
