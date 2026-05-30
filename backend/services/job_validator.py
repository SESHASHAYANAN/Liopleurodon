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
    # Indian states / regions (appear in Adzuna location fields)
    "karnataka", "maharashtra", "tamil nadu", "telangana", "andhra pradesh",
    "west bengal", "rajasthan", "uttar pradesh", "gujarat", "kerala",
    "madhya pradesh", "haryana", "punjab", "bihar", "odisha",
    "india",
}

# ── Foreign markers — ONLY check in job TITLE, not in URLs ────────────────
FOREIGN_TITLE_MARKERS = {
    # Country names that appear in titles like "Software Engineer - UK"
    "uk", "united kingdom", "usa", "united states",
    "canada", "australia", "germany", "france", "netherlands",
    "switzerland", "sweden", "japan", "singapore", "brazil",
    "spain", "italy", "new zealand", "israel",
}

# ── Foreign CITY markers — only for title checks ─────────────────────────
FOREIGN_CITY_MARKERS = {
    "london", "new york", "san francisco", "los angeles", "seattle",
    "austin", "boston", "chicago", "toronto", "vancouver", "montreal",
    "sydney", "melbourne", "berlin", "munich", "amsterdam", "dublin",
    "paris", "zurich", "tokyo",
}

# ── Experience Level Classification ───────────────────────────────────────

PRINCIPAL_PATTERNS = [
    r'\bprincipal\b', r'\bdistinguished\b', r'\bfellow\b',
]

STAFF_PATTERNS = [
    r'\bstaff\b',
    r'\bvp\b', r'\bdirector\b', r'\bchief\b', r'\bhead\s+of\b',
]

LEAD_PATTERNS = [
    r'\blead\b', r'\bteam\s*lead\b', r'\btech\s*lead\b',
    r'\bengineering\s*lead\b', r'\bmanager\b',
]

SENIOR_PATTERNS = [
    r'\bsenior\b', r'\bsr\.?\s', r'\bsr$',
    r'\barchitect\b', r'\bexecutive\b',
]

JUNIOR_PATTERNS = [
    r'\bjunior\b', r'\bjr\.?\s', r'\bjr$',
    r'\bassociate\b', r'\bentry[\s-]?level\b', r'\bgraduate\b',
    r'\bnew\s*grad\b', r'\bfresher\b',
]

INTERN_PATTERNS = [
    r'\bintern\b', r'\binternship\b', r'\btrainee\b',
    r'\bapprentice\b', r'\bco-?op\b',
]


def classify_experience_level(title: str, description: str = "") -> str:
    """
    Classify experience level strictly from the job TITLE.
    Priority: intern > principal > staff > lead > senior > junior > mid (default).
    """
    t = title.lower().strip()
    
    # 1. Intern — highest priority
    if any(re.search(p, t) for p in INTERN_PATTERNS):
        return "intern"
    
    # 2. Principal/Distinguished/Fellow
    if any(re.search(p, t) for p in PRINCIPAL_PATTERNS):
        return "principal"
    
    # 3. Staff/VP/Director/Chief
    if any(re.search(p, t) for p in STAFF_PATTERNS):
        return "staff"
    
    # 4. Lead
    if any(re.search(p, t) for p in LEAD_PATTERNS):
        return "lead"
    
    # 5. Senior
    if any(re.search(p, t) for p in SENIOR_PATTERNS):
        return "senior"
    
    # 6. Junior
    if any(re.search(p, t) for p in JUNIOR_PATTERNS):
        return "junior"
    
    # 7. Default = mid
    return "mid"


def validate_india_job(job: dict) -> bool:
    """
    Validate that a job tagged as India is ACTUALLY an India job.
    Returns False ONLY if there's a POSITIVE foreign signal in the TITLE.
    
    We only check the title for foreign country/city names — NOT URLs,
    because Adzuna uses .co.uk domains for all countries including India.
    """
    title = (job.get("title") or "").lower()
    salary_currency = (job.get("salary_currency") or "").lower()
    
    # 1. Check title for foreign country markers
    #    e.g., "Technical Account Manager - UK" → NOT India
    for marker in FOREIGN_TITLE_MARKERS:
        patterns = [
            rf'\b{re.escape(marker)}\b',           # whole word
            rf'\(\s*{re.escape(marker)}\s*\)',       # in parentheses
            rf'-\s*{re.escape(marker)}\s*$',         # after dash at end
        ]
        for pattern in patterns:
            if re.search(pattern, title):
                return False
    
    # 2. Check title for foreign city markers
    for marker in FOREIGN_CITY_MARKERS:
        if re.search(rf'\b{re.escape(marker)}\b', title):
            return False
    
    # 3. Salary in GBP/EUR = not India (but USD is OK — many India jobs list USD)
    if salary_currency in ("gbp", "eur", "chf", "aud", "cad", "sgd"):
        return False
    
    # 4. Description has £ or € salary = not India
    desc = (job.get("description") or "").lower()[:500]
    if re.search(r'[£€]\s*\d', desc):
        return False
    
    # 5. If sourced from Adzuna-IN, trust it (they queried the /in/ endpoint)
    sources = job.get("source_platforms") or []
    if any("adzuna-in" in s.lower() for s in sources):
        return True
    
    # 6. Default: allow (no foreign signals found)
    return True


# Non-tech / low-quality title markers
NON_TECH_TITLES = [
    "sales", "marketing manager", "human resources", "recruiter",
    "customer support", "customer success", "bpo", "call center",
    "account executive", "business development", "content writer",
    "copywriter", "talent acquisition", "receptionist", "secretary",
    "data entry", "typist", "housekeeping", "driver", "delivery",
    "cook", "chef", "waiter", "cashier", "clerk", "peon",
    "watchman", "guard", "plumber", "electrician", "carpenter",
]


def validate_job_data_quality(job: dict) -> tuple:
    """
    Validate overall job data quality. Returns (is_valid, reason).
    Ensures only high-quality, complete tech job listings pass through.
    """
    title = (job.get("title") or "").strip()
    company = (job.get("company_name") or "").strip()
    apply_url = (job.get("apply_url") or "").strip()
    
    if not title or len(title) < 5:
        return False, "title too short"
    if not company or len(company) < 2:
        return False, "company name too short"
    if not apply_url or not apply_url.startswith("http"):
        return False, "invalid apply_url"
    
    # Reject fake/test jobs — but be careful not to reject "QA Test Engineer"
    title_lower = title.lower()
    if any(title_lower.startswith(m) for m in ["test ", "mock ", "dummy ", "placeholder "]):
        return False, "fake/test job"
    
    # Reject non-tech jobs
    if any(nt in title_lower for nt in NON_TECH_TITLES):
        return False, "non-tech job"
    
    # Reject jobs with too-generic titles (likely spam)
    if title_lower in ["job", "opening", "vacancy", "hiring", "urgent", "required"]:
        return False, "generic/spam title"
    
    # Country-location cross-validation
    country = (job.get("location_country") or "").lower()
    if country in ("india", "in"):
        if not validate_india_job(job):
            return False, "location mismatch: foreign signals in title"
    
    # Auto-correct experience level
    stored_exp = job.get("experience_level", "")
    correct_exp = classify_experience_level(title)
    if stored_exp and stored_exp != correct_exp:
        job["experience_level"] = correct_exp
    
    return True, "ok"


def sanitize_job_before_insert(job: dict) -> dict:
    """
    Sanitize and auto-correct fields before database insertion.
    """
    title = job.get("title", "")
    desc = job.get("description", "")
    
    # 1. Always re-classify experience level from title
    job["experience_level"] = classify_experience_level(title, desc)
    
    # 2. Validate India location if tagged as India
    country = (job.get("location_country") or "").lower()
    if country in ("india", "in"):
        if not validate_india_job(job):
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
