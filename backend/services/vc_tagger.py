"""
Liopleurodon — VC-Backed Company Tagger
"""
import re

VC_PORTFOLIO = {
    "yc": {"short": "YC", "companies": [
        "airbnb","stripe","dropbox","coinbase","instacart","doordash","reddit","twitch","gitlab",
        "zapier","gusto","brex","scale ai","fivetran","webflow","vercel","supabase","posthog",
        "retool","segment","algolia","docker","render","railway","resend","mercury","deel",
        "lattice","ramp","rippling","notion",
    ]},
    "a16z": {"short": "a16z", "companies": [
        "github","coinbase","instacart","lyft","slack","figma","roblox","databricks",
        "replit","sourcegraph","vercel","netlify","hashicorp","datadog","asana",
    ]},
    "sequoia": {"short": "Sequoia", "companies": [
        "apple","google","whatsapp","stripe","zoom","snowflake","unity","figma","notion",
        "linear","vercel","scale ai","hugging face","vanta",
    ]},
    "kleiner_perkins": {"short": "KP", "companies": [
        "google","amazon","twitter","slack","figma","canva","rippling","plaid",
    ]},
    "accel": {"short": "Accel", "companies": [
        "facebook","dropbox","slack","atlassian","crowdstrike","freshworks","notion",
        "vercel","webflow","snyk","1password","miro",
    ]},
    "gv": {"short": "GV", "companies": [
        "uber","slack","stripe","gitlab","medium","hubspot","duolingo","robinhood","gusto",
    ]},
    "lightspeed": {"short": "Lightspeed", "companies": [
        "snap","affirm","epic games","mulesoft","nutanix","rubrik","grafana",
    ]},
    "benchmark": {"short": "Benchmark", "companies": [
        "twitter","uber","snapchat","discord","zillow","yelp","dropbox","elastic",
    ]},
    "tiger_global": {"short": "Tiger Global", "companies": [
        "stripe","figma","brex","notion","canva","databricks","gitlab","toast",
    ]},
    "bessemer": {"short": "Bessemer", "companies": [
        "shopify","twilio","linkedin","pinterest","canva","toast","fivetran","intercom",
    ]},
}

BIG_TECH = [
    "google","alphabet","meta","facebook","apple","amazon","microsoft","netflix","nvidia",
    "tesla","salesforce","adobe","oracle","ibm","intel","amd","qualcomm","cisco","samsung",
    "uber","lyft","doordash","palantir","snowflake","datadog","cloudflare","twilio","shopify",
    "atlassian","spotify","block","paypal","coinbase","robinhood",
]

STEALTH_PATTERNS = [
    r"stealth\s*(startup|company|mode)?", r"confidential\s*(company|employer)?",
    r"undisclosed", r"well[-\s]?funded\s+startup", r"pre[-\s]?launch\s+startup",
]


def detect_company_type(company_name: str) -> dict:
    if not company_name:
        return {"company_type": "other", "vc_backer": None, "is_stealth": False}
    name_lower = company_name.lower().strip()

    for pattern in STEALTH_PATTERNS:
        if re.search(pattern, name_lower):
            return {"company_type": "stealth", "vc_backer": None, "is_stealth": True}

    for company in BIG_TECH:
        if company in name_lower or name_lower in company:
            return {"company_type": "big_tech", "vc_backer": None, "is_stealth": False}

    for vc_key, vc_data in VC_PORTFOLIO.items():
        for pc in vc_data["companies"]:
            if pc in name_lower or name_lower == pc:
                return {"company_type": "vc_backed", "vc_backer": vc_data["short"], "is_stealth": False}

    return {"company_type": "other", "vc_backer": None, "is_stealth": False}


def tag_job_with_vc_info(job: dict) -> dict:
    info = detect_company_type(job.get("company_name", ""))
    if not job.get("company_type"):
        job["company_type"] = info["company_type"]
    if not job.get("vc_backer") and info["vc_backer"]:
        job["vc_backer"] = info["vc_backer"]
    if not job.get("is_stealth"):
        job["is_stealth"] = info["is_stealth"]
    return job

def tag_job_perks(job: dict) -> dict:
    title = str(job.get("title", "")).lower()
    description = str(job.get("description", "")).lower()
    text = title + " " + description
    
    if not job.get("visa_sponsorship"):
        if any(p in text for p in ["visa sponsor", "sponsorship available", "sponsor visa", "h1b", "h-1b", "visa support"]):
            job["visa_sponsorship"] = True
            
    if not job.get("relocation_support"):
        if any(p in text for p in ["relocation support", "relocation assistance", "relocation package", "offer relocation", "relocation provided", "willing to relocate"]):
            job["relocation_support"] = True
            
    return job

