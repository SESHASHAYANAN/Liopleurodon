"""
Liopleurodon — ATS Detector Service
Identifies the Applicant Tracking System (ATS) used by a company
from the job's apply URL. Uses fast URL pattern matching first,
then company-name lookup, then Groq AI for ambiguous cases.
"""

import re
import httpx
import json
from typing import Optional
from config import get_settings


# ─── URL Pattern Rules ────────────────────────────────────────────
# Each rule: (compiled regex on URL, ATS name)
# Ordered by specificity — first match wins.
ATS_URL_PATTERNS = [
    # Greenhouse
    (re.compile(r'greenhouse\.io', re.I), 'Greenhouse'),
    (re.compile(r'boards\.greenhouse', re.I), 'Greenhouse'),
    (re.compile(r'job-boards\.greenhouse', re.I), 'Greenhouse'),

    # Lever
    (re.compile(r'lever\.co', re.I), 'Lever'),
    (re.compile(r'jobs\.lever\.co', re.I), 'Lever'),

    # Workday
    (re.compile(r'myworkdayjobs\.com', re.I), 'Workday'),
    (re.compile(r'workday\.com', re.I), 'Workday'),
    (re.compile(r'wd\d+\.myworkdayjobs', re.I), 'Workday'),

    # Ashby
    (re.compile(r'ashbyhq\.com', re.I), 'Ashby'),
    (re.compile(r'jobs\.ashbyhq', re.I), 'Ashby'),

    # iCIMS
    (re.compile(r'icims\.com', re.I), 'iCIMS'),
    (re.compile(r'jobs-.*\.icims\.com', re.I), 'iCIMS'),
    (re.compile(r'careers-.*\.icims\.com', re.I), 'iCIMS'),

    # Taleo (Oracle)
    (re.compile(r'taleo\.net', re.I), 'Taleo'),
    (re.compile(r'oracle.*taleo', re.I), 'Taleo'),
    (re.compile(r'taleo\.oracle', re.I), 'Taleo'),

    # SmartRecruiters
    (re.compile(r'smartrecruiters\.com', re.I), 'SmartRecruiters'),
    (re.compile(r'jobs\.smartrecruiters', re.I), 'SmartRecruiters'),

    # Workable
    (re.compile(r'workable\.com', re.I), 'Workable'),
    (re.compile(r'apply\.workable', re.I), 'Workable'),

    # BambooHR
    (re.compile(r'bamboohr\.com', re.I), 'BambooHR'),

    # JazzHR
    (re.compile(r'jazzhr\.com', re.I), 'JazzHR'),
    (re.compile(r'app\.jazz\.co', re.I), 'JazzHR'),

    # Breezy HR
    (re.compile(r'breezy\.hr', re.I), 'Breezy HR'),

    # Jobvite
    (re.compile(r'jobvite\.com', re.I), 'Jobvite'),
    (re.compile(r'jobs\.jobvite', re.I), 'Jobvite'),

    # Recruitee
    (re.compile(r'recruitee\.com', re.I), 'Recruitee'),

    # Personio
    (re.compile(r'personio\.de', re.I), 'Personio'),
    (re.compile(r'jobs\.personio', re.I), 'Personio'),

    # Rippling
    (re.compile(r'rippling\.com', re.I), 'Rippling'),

    # Gusto
    (re.compile(r'gusto\.com', re.I), 'Gusto'),

    # Deel
    (re.compile(r'deel\.com', re.I), 'Deel'),

    # SuccessFactors (SAP)
    (re.compile(r'successfactors\.com', re.I), 'SAP SuccessFactors'),
    (re.compile(r'sap\..*career', re.I), 'SAP SuccessFactors'),

    # Wellfound (AngelList)
    (re.compile(r'wellfound\.com', re.I), 'Wellfound'),
    (re.compile(r'angel\.co', re.I), 'Wellfound'),

    # LinkedIn
    (re.compile(r'linkedin\.com', re.I), 'LinkedIn Jobs'),

    # Indeed
    (re.compile(r'indeed\.com', re.I), 'Indeed'),
    (re.compile(r'indeed\.co', re.I), 'Indeed'),

    # ZipRecruiter
    (re.compile(r'ziprecruiter\.com', re.I), 'ZipRecruiter'),

    # Glassdoor
    (re.compile(r'glassdoor\.com', re.I), 'Glassdoor'),
    (re.compile(r'glassdoor\.co', re.I), 'Glassdoor'),

    # Naukri
    (re.compile(r'naukri\.com', re.I), 'Naukri'),

    # YCombinator
    (re.compile(r'workatastartup\.com', re.I), 'YC Work at a Startup'),
    (re.compile(r'ycombinator\.com', re.I), 'YC Jobs'),

    # Web3 Career
    (re.compile(r'web3\.career', re.I), 'Web3 Career'),

    # Simplify
    (re.compile(r'simplify\.jobs', re.I), 'Simplify'),

    # Adzuna (redirect URLs — most common in our dataset)
    (re.compile(r'adzuna\.com', re.I), 'Adzuna'),
    (re.compile(r'adzuna\.co', re.I), 'Adzuna'),
    (re.compile(r'adzuna\.in', re.I), 'Adzuna'),

    # Remotive
    (re.compile(r'remotive\.com', re.I), 'Remotive'),
    (re.compile(r'remotive\.io', re.I), 'Remotive'),

    # RemoteOK
    (re.compile(r'remoteok\.com', re.I), 'RemoteOK'),
    (re.compile(r'remoteok\.io', re.I), 'RemoteOK'),

    # Arbeitnow
    (re.compile(r'arbeitnow\.com', re.I), 'Arbeitnow'),

    # Indian Platforms
    (re.compile(r'instahyre\.com', re.I), 'Instahyre'),
    (re.compile(r'cutshort\.io', re.I), 'CutShort'),
    (re.compile(r'hirist\.com', re.I), 'Hirist'),
    (re.compile(r'hirist\.tech', re.I), 'Hirist'),
    (re.compile(r'hackerearth\.com', re.I), 'HackerEarth'),
    (re.compile(r'hackerrank\.com', re.I), 'HackerRank'),
    (re.compile(r'internshala\.com', re.I), 'Internshala'),
    (re.compile(r'foundit\.in', re.I), 'Foundit'),
    (re.compile(r'shine\.com', re.I), 'Shine'),
    (re.compile(r'timesjobs\.com', re.I), 'TimesJobs'),
    (re.compile(r'iimjobs\.com', re.I), 'IIMJobs'),
    (re.compile(r'freshersworld\.com', re.I), 'Freshersworld'),
    (re.compile(r'hasjob\.co', re.I), 'HasJob'),
    (re.compile(r'karkidi\.com', re.I), 'Karkidi'),

    # Global Job Boards & ATS
    (re.compile(r'applytojob\.com', re.I), 'ApplyToJob'),
    (re.compile(r'teamtailor\.com', re.I), 'Teamtailor'),
    (re.compile(r'pinpointhq\.com', re.I), 'Pinpoint'),
    (re.compile(r'comeet\.co', re.I), 'Comeet'),
    (re.compile(r'hirebridge\.com', re.I), 'Hirebridge'),
    (re.compile(r'paylocity\.com', re.I), 'Paylocity'),
    (re.compile(r'paycom\.com', re.I), 'Paycom'),
    (re.compile(r'ultipro\.com', re.I), 'UKG (UltiPro)'),
    (re.compile(r'adp\.com', re.I), 'ADP'),
    (re.compile(r'ceridian\.com', re.I), 'Ceridian Dayforce'),
    (re.compile(r'eightfold\.ai', re.I), 'Eightfold AI'),
    (re.compile(r'jobsoid\.com', re.I), 'Jobsoid'),
    (re.compile(r'zohorecruit', re.I), 'Zoho Recruit'),
    (re.compile(r'avature\.net', re.I), 'Avature'),
    (re.compile(r'dice\.com', re.I), 'Dice'),
    (re.compile(r'monster\.com', re.I), 'Monster'),
    (re.compile(r'monster\.co', re.I), 'Monster'),
    (re.compile(r'hired\.com', re.I), 'Hired'),
    (re.compile(r'triplebyte\.com', re.I), 'Triplebyte'),
    (re.compile(r'dover\.com', re.I), 'Dover'),
    (re.compile(r'gem\.com', re.I), 'Gem'),
    (re.compile(r'freshteam\.com', re.I), 'Freshteam'),
    (re.compile(r'zoho\.com.*recruit', re.I), 'Zoho Recruit'),
    (re.compile(r'applyboard\.com', re.I), 'ApplyBoard'),
    (re.compile(r'dealls\.com', re.I), 'Dealls'),
    (re.compile(r'getclera\.com', re.I), 'Clera'),
    (re.compile(r'dataannotation\.tech', re.I), 'Direct Apply'),

    # Himalayas
    (re.compile(r'himalayas\.app', re.I), 'Himalayas'),

    # Jobicy
    (re.compile(r'jobicy\.com', re.I), 'Jobicy'),

    # Arc.dev
    (re.compile(r'arc\.dev', re.I), 'Arc.dev'),

    # AI-Jobs
    (re.compile(r'ai-jobs\.net', re.I), 'AI-Jobs.net'),

    # Additional ATS patterns (common in redirect URLs)
    (re.compile(r'careers\.google\.com', re.I), 'Google Careers'),
    (re.compile(r'careers\.microsoft\.com', re.I), 'Microsoft Careers'),
    (re.compile(r'amazon\.jobs', re.I), 'Amazon Jobs'),
    (re.compile(r'jobs\.apple\.com', re.I), 'Apple Careers'),
    (re.compile(r'metacareers\.com', re.I), 'Meta Careers'),
    (re.compile(r'careers\.meta\.com', re.I), 'Meta Careers'),
    (re.compile(r'netflix\.com/jobs', re.I), 'Netflix Jobs'),
    (re.compile(r'jobs\.netflix\.com', re.I), 'Netflix Jobs'),

    # Company career pages (common patterns)
    (re.compile(r'careers\.[a-z]+\.(com|io|co|in)', re.I), 'Company Career Page'),
    (re.compile(r'[a-z]+\.com/careers', re.I), 'Company Career Page'),
    (re.compile(r'[a-z]+\.com/jobs', re.I), 'Company Career Page'),
    (re.compile(r'jobs\.[a-z]+\.(com|io|co|in)', re.I), 'Company Career Page'),
]

# ─── Company-Name-to-ATS Mapping ─────────────────────────────────
# Known big companies and which ATS they use.
# Keys are matched as substrings of the company name (case-insensitive).
COMPANY_ATS_MAP = {
    # FAANG / Big Tech
    "google": "Google Careers", "alphabet": "Google Careers",
    "meta": "Meta Careers", "facebook": "Meta Careers",
    "amazon": "Amazon Jobs", "apple": "Apple Careers",
    "microsoft": "Microsoft Careers", "netflix": "Netflix Jobs",
    # Greenhouse users
    "uber": "Greenhouse", "airbnb": "Greenhouse",
    "stripe": "Greenhouse", "coinbase": "Greenhouse",
    "figma": "Greenhouse", "notion": "Greenhouse",
    "discord": "Greenhouse", "ramp": "Greenhouse",
    "brex": "Greenhouse", "rippling": "Greenhouse",
    "databricks": "Greenhouse", "snowflake": "Greenhouse",
    "datadog": "Greenhouse", "dbt labs": "Greenhouse",
    "phonepe": "Greenhouse", "dream11": "Greenhouse",
    "postman": "Greenhouse", "browserstack": "Greenhouse",
    "thoughtspot": "Greenhouse", "chargebee": "Greenhouse",
    "hasura": "Greenhouse", "moengage": "Greenhouse",
    "twilio": "Greenhouse", "cloudflare": "Greenhouse",
    "canva": "Greenhouse", "gitlab": "Greenhouse",
    "plaid": "Greenhouse", "airtable": "Greenhouse",
    "hashicorp": "Greenhouse", "elastic": "Greenhouse",
    # Lever users
    "swiggy": "Lever", "zomato": "Lever",
    "razorpay": "Lever", "ola": "Lever",
    "meesho": "Lever", "cred": "Lever",
    "byju's": "Lever", "unacademy": "Lever",
    "sharechat": "Lever", "sprinklr": "Lever",
    "clevertap": "Lever", "urbancompany": "Lever",
    "licious": "Lever", "groww": "Lever",
    "shopify": "Lever", "lyft": "Lever",
    "slack": "Lever", "asana": "Lever",
    # Workday users
    "salesforce": "Workday", "adobe": "Workday",
    "ibm": "Workday", "cisco": "Workday",
    "intel": "Workday", "nvidia": "Workday",
    "qualcomm": "Workday", "cognizant": "Workday",
    "accenture": "Workday", "ey": "Workday",
    "kpmg": "Workday", "pwc": "Workday",
    "jpmorgan": "Workday", "goldman sachs": "Workday",
    "bank of america": "Workday", "atlassian": "Workday",
    "vmware": "Workday", "dell": "Workday",
    "hp": "Workday", "honeywell": "Workday",
    "siemens": "Workday", "philips": "Workday",
    "bosch": "Workday", "samsung": "Workday",
    # Taleo (Oracle)
    "oracle": "Taleo",
    # SAP SuccessFactors
    "sap": "SAP SuccessFactors",
    # iCIMS users
    "morgan stanley": "iCIMS",
    # SmartRecruiters
    "capgemini": "SmartRecruiters", "visa": "SmartRecruiters",
    # Indian IT companies (multiple name variants)
    "infosys": "Infosys Careers", "tcs": "TCS iON",
    "tata consultancy": "TCS iON", "tata elxsi": "Tata Elxsi Careers",
    "wipro": "Wipro Careers", "hcl": "HCL Careers",
    "tech mahindra": "Tech Mahindra Careers",
    "mindtree": "Mindtree Careers", "mphasis": "Mphasis Careers",
    "l&t": "L&T Careers", "larsen": "L&T Careers",
    "persistent": "Persistent Careers", "ltimindtree": "LTIMindtree Careers",
    "hexaware": "Hexaware Careers", "cyient": "Cyient Careers",
    "birlasoft": "Birlasoft Careers", "zensar": "Zensar Careers",
    "coforge": "Coforge Careers", "niit": "NIIT Careers",
    "sonata software": "Sonata Careers", "happiest minds": "Happiest Minds Careers",
    "muthoot": "Company Career Page", "reliance": "Reliance Careers",
    "mahindra": "Mahindra Careers", "bajaj": "Bajaj Careers",
    "aditya birla": "Aditya Birla Careers", "tata": "Tata Careers",
    # Indian Startups
    "flipkart": "Flipkart Careers", "paytm": "Paytm Careers",
    "zerodha": "Zerodha Careers", "nykaa": "Nykaa Careers",
    "freshworks": "Freshteam", "zoho": "Zoho Recruit",
    "turing": "Turing Platform",
    "upgrad": "UpGrad Careers", "vedantu": "Vedantu Careers",
    "dunzo": "Lever", "jupiter": "Lever",
    "slice": "Lever", "rupeek": "Lever",
    # Consulting
    "deloitte": "Deloitte Careers",
    "mckinsey": "McKinsey Careers",
    "bain": "Bain Careers",
    "bcg": "BCG Careers",
}


def detect_ats_from_url(apply_url: Optional[str]) -> Optional[str]:
    """
    Detect ATS from the apply URL using pattern matching.
    Returns the ATS name or None if no pattern matches.
    """
    if not apply_url:
        return None

    for pattern, ats_name in ATS_URL_PATTERNS:
        if pattern.search(apply_url):
            return ats_name

    return None


def detect_ats_from_company(company_name: str) -> Optional[str]:
    """
    Detect ATS from the company name using substring matching.
    More flexible than exact match — handles 'Infosys Limited',
    'Tata Consultancy Services', etc.
    """
    if not company_name:
        return None

    company_lower = company_name.lower().strip()

    # 1. Try exact match first
    if company_lower in COMPANY_ATS_MAP:
        return COMPANY_ATS_MAP[company_lower]

    # 2. Try substring match (handles "Infosys Limited", "TCS BPS", etc.)
    for key, ats in COMPANY_ATS_MAP.items():
        if key in company_lower:
            return ats

    return None


def detect_ats_complete(company_name: str, apply_url: str) -> str:
    """
    Complete ATS detection: URL patterns → company lookup → domain inference.
    For job aggregator URLs (Adzuna, Indeed, LinkedIn), prefers the company's
    own ATS over the aggregator name when the company is known.
    Returns a definitive ATS name (never None).
    """
    # Job aggregators — if the URL is from one of these, the company's own
    # ATS is more informative than just "Adzuna" or "Indeed"
    AGGREGATORS = {"Adzuna", "Indeed", "LinkedIn Jobs", "ZipRecruiter",
                   "Glassdoor", "Monster", "Dice", "Remotive", "RemoteOK",
                   "Arbeitnow", "Himalayas", "Jobicy", "Arc.dev", "AI-Jobs.net"}

    # Step 1: URL pattern matching
    url_ats = detect_ats_from_url(apply_url)

    # Step 2: Company name lookup
    company_ats = detect_ats_from_company(company_name)

    # If URL matches an aggregator but we know the company's ATS, prefer that
    if url_ats and url_ats in AGGREGATORS and company_ats:
        return company_ats

    # If URL matches a specific ATS platform (Greenhouse, Lever, etc.), use it
    if url_ats:
        return url_ats

    # If we know the company's ATS, use it
    if company_ats:
        return company_ats

    # Step 3: Infer from URL domain structure
    if apply_url:
        ats = _infer_ats_from_domain(apply_url)
        if ats:
            return ats

    return "Unknown ATS"


def _infer_ats_from_domain(url: str) -> Optional[str]:
    """
    Last-resort ATS inference from URL domain structure.
    Catches patterns like 'company.recruiterbox.com', 'apply.company.com', etc.
    """
    url_lower = url.lower()

    # Known ATS subdomains in URLs
    subdomain_ats = {
        "recruiterbox": "Recruiterbox",
        "recruitcrm": "RecruitCRM",
        "breezyhr": "Breezy HR",
        "hire.lever": "Lever",
        "jobs.lever": "Lever",
        "boards.greenhouse": "Greenhouse",
        "app.greenhouse": "Greenhouse",
        "career.workday": "Workday",
        "myworkday": "Workday",
        "successfactors": "SAP SuccessFactors",
        "smartrecruiters": "SmartRecruiters",
        "bamboohr": "BambooHR",
        "jazzhr": "JazzHR",
        "ashbyhq": "Ashby",
        "jobvite": "Jobvite",
        "recruitee": "Recruitee",
        "workable": "Workable",
        "teamtailor": "Teamtailor",
        "personio": "Personio",
        "pinpointhq": "Pinpoint",
        "freshteam": "Freshteam",
    }

    for keyword, ats in subdomain_ats.items():
        if keyword in url_lower:
            return ats

    return None


async def detect_ats_with_ai(company_name: str, apply_url: str) -> Optional[str]:
    """
    Fallback: Use Groq AI to identify the ATS from the URL and company name.
    Only called when URL pattern matching fails.
    """
    settings = get_settings()
    if not settings.GROQ_API_KEY or not apply_url:
        return None

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You identify Applicant Tracking Systems (ATS) from job application URLs. "
                                "Given a company name and apply URL, return ONLY a JSON object: "
                                '{"ats": "ATS Name"} or {"ats": null} if unknown. '
                                "Common ATS: Workday, Greenhouse, Lever, iCIMS, Taleo, SmartRecruiters, "
                                "Workable, Ashby, BambooHR, JazzHR, Jobvite, Recruitee, Personio. "
                                "Job boards like LinkedIn, Indeed, ZipRecruiter are valid answers too. "
                                "If it's a company's own career page, respond with \"Company Career Page\"."
                            ),
                        },
                        {
                            "role": "user",
                            "content": f"Company: {company_name}\nApply URL: {apply_url}",
                        },
                    ],
                    "temperature": 0.0,
                    "max_tokens": 50,
                    "response_format": {"type": "json_object"},
                },
            )
            data = resp.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "{}")
            result = json.loads(content)
            return result.get("ats")
    except Exception as e:
        print(f"[ATS Detector] Groq AI fallback error: {e}")
        return None


async def detect_ats(company_name: str, apply_url: Optional[str]) -> Optional[str]:
    """
    Detect ATS using URL patterns first, then Groq AI fallback.
    Returns the ATS name or Unknown ATS.
    """
    # Step 1: Fast complete detection (URL + company + domain inference)
    ats = detect_ats_complete(company_name or "", apply_url or "")
    if ats and ats != "Unknown ATS":
        return ats

    if not apply_url:
        return "Unknown ATS"

    # Step 2: Groq AI fallback for unknown URLs
    ats = await detect_ats_with_ai(company_name, apply_url)
    return ats or "Unknown ATS"


async def detect_ats_batch(jobs: list) -> list:
    """
    Detect ATS for a batch of jobs. Uses URL patterns for most,
    and batches unknown URLs for a single Groq AI call.
    Returns the jobs list with 'ats_detected' field added.
    """
    unknown_jobs = []

    for job in jobs:
        apply_url = job.get("apply_url", "")
        company_name = job.get("company_name", "")

        ats = detect_ats_complete(company_name, apply_url)
        if ats and ats != "Unknown ATS":
            job["ats_detected"] = ats
        else:
            unknown_jobs.append(job)

    # Batch AI detection for unknown URLs
    if unknown_jobs:
        ats_results = await _batch_detect_ats_groq(unknown_jobs)
        for job, ats_name in zip(unknown_jobs, ats_results):
            job["ats_detected"] = ats_name or "Unknown ATS"

    # Ensure all jobs have an ats_detected field
    for job in jobs:
        if not job.get("ats_detected"):
            job["ats_detected"] = "Unknown ATS"

    return jobs


async def _batch_detect_ats_groq(jobs: list) -> list:
    """
    Batch detect ATS for multiple jobs using a single Groq API call.
    Returns a list of ATS names (or None) in the same order.
    """
    settings = get_settings()
    if not settings.GROQ_API_KEY or not jobs:
        return [None] * len(jobs)

    # Build a compact list for the prompt
    job_entries = []
    for i, job in enumerate(jobs[:30]):  # Cap at 30 per batch
        job_entries.append({
            "idx": i,
            "company": job.get("company_name", "Unknown"),
            "url": job.get("apply_url", ""),
        })

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You identify Applicant Tracking Systems (ATS) from job application URLs. "
                                "Given a list of jobs with company names and apply URLs, return a JSON object: "
                                '{"results": [{"idx": 0, "ats": "ATS Name"}, ...]}. '
                                "Use null for ats if you cannot determine it. "
                                "Common ATS: Workday, Greenhouse, Lever, iCIMS, Taleo, SmartRecruiters, "
                                "Workable, Ashby, BambooHR, JazzHR, Jobvite, Recruitee, Personio. "
                                "Job boards (LinkedIn, Indeed, ZipRecruiter, Adzuna, Naukri) are valid answers. "
                                "Company's own career pages → \"Company Career Page\"."
                            ),
                        },
                        {
                            "role": "user",
                            "content": json.dumps(job_entries),
                        },
                    ],
                    "temperature": 0.0,
                    "max_tokens": 1000,
                    "response_format": {"type": "json_object"},
                },
            )
            data = resp.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "{}")
            parsed = json.loads(content)
            results = parsed.get("results", [])

            # Map results back by idx
            ats_map = {r["idx"]: r.get("ats") for r in results}
            return [ats_map.get(i) for i in range(len(jobs))]

    except Exception as e:
        print(f"[ATS Detector] Batch Groq error: {e}")
        return [None] * len(jobs)
