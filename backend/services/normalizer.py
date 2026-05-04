"""
Liopleurodon — Job Normalizer
Transforms raw API responses from all sources into the unified job schema.
"""

from datetime import datetime, timezone
from typing import Optional
from services.deduplication import generate_dedup_hash


def normalize_jsearch(raw: dict) -> dict:
    """Normalize JSearch (RapidAPI) response to unified schema."""
    location_parts = []
    if raw.get("job_city"):
        location_parts.append(raw["job_city"])
    if raw.get("job_country"):
        location_parts.append(raw["job_country"])

    return {
        "title": raw.get("job_title", ""),
        "company_name": raw.get("employer_name", ""),
        "company_logo_url": raw.get("employer_logo"),
        "company_industry": raw.get("employer_company_type"),
        "location_city": raw.get("job_city"),
        "location_country": raw.get("job_country"),
        "remote_type": _detect_remote(raw.get("job_is_remote")),
        "salary_min": raw.get("job_min_salary"),
        "salary_max": raw.get("job_max_salary"),
        "salary_currency": raw.get("job_salary_currency", "USD"),
        "salary_period": raw.get("job_salary_period", "yearly"),
        "job_type": _normalize_job_type(raw.get("job_employment_type")),
        "description": raw.get("job_description"),
        "requirements": raw.get("job_highlights", {}).get("Qualifications", []),
        "responsibilities": raw.get("job_highlights", {}).get("Responsibilities", []),
        "benefits": raw.get("job_highlights", {}).get("Benefits", []),
        "apply_url": raw.get("job_apply_link"),
        "posted_date": _parse_date(raw.get("job_posted_at_datetime_utc")),
        "expiry_date": _parse_date(raw.get("job_offer_expiration_datetime_utc")),
        "source_platforms": ["JSearch"],
        "is_active": True,
    }


def normalize_serpapi(raw: dict) -> dict:
    """Normalize SerpApi Google Jobs response."""
    detected = raw.get("detected_extensions", {})
    return {
        "title": raw.get("title", ""),
        "company_name": raw.get("company_name", ""),
        "location_city": raw.get("location"),
        "description": raw.get("description"),
        "salary_min": detected.get("salary_from"),
        "salary_max": detected.get("salary_to"),
        "job_type": _normalize_job_type(detected.get("schedule_type")),
        "posted_date": _relative_date(detected.get("posted_at")),
        "apply_url": _extract_apply_link(raw.get("apply_options", [])),
        "source_platforms": ["SerpApi"],
        "is_active": True,
    }


def normalize_adzuna(raw: dict) -> dict:
    """Normalize Adzuna API response."""
    company = raw.get("company", {})
    location = raw.get("location", {})
    areas = location.get("area", [])

    return {
        "title": raw.get("title", ""),
        "company_name": company.get("display_name", "Unknown"),
        "location_city": areas[-1] if areas else None,
        "location_country": areas[0] if areas else None,
        "location_coords": {
            "lat": raw.get("latitude"),
            "lng": raw.get("longitude"),
        } if raw.get("latitude") else None,
        "salary_min": raw.get("salary_min"),
        "salary_max": raw.get("salary_max"),
        "salary_currency": "GBP",  # Adzuna defaults to GBP for UK
        "description": raw.get("description"),
        "apply_url": raw.get("redirect_url"),
        "posted_date": _parse_date(raw.get("created")),
        "job_type": _normalize_job_type(raw.get("contract_type")),
        "source_platforms": ["Adzuna"],
        "is_active": True,
    }


def normalize_theirstack(raw: dict) -> dict:
    """Normalize TheirStack API response."""
    return {
        "title": raw.get("job_title", ""),
        "company_name": raw.get("company_name", ""),
        "company_logo_url": raw.get("company_logo"),
        "company_size": raw.get("company_num_employees"),
        "location_city": raw.get("location"),
        "location_country": raw.get("country"),
        "remote_type": "remote" if raw.get("remote") else "onsite",
        "tech_stack": raw.get("technologies", []),
        "description": raw.get("description"),
        "apply_url": raw.get("url"),
        "posted_date": _parse_date(raw.get("date_posted")),
        "source_platforms": ["TheirStack"],
        "is_active": True,
    }


def normalize_apify(raw: dict) -> dict:
    """Normalize Apify LinkedIn/Indeed/Glassdoor scraper response."""
    return {
        "title": raw.get("title", raw.get("jobTitle", "")),
        "company_name": raw.get("company", raw.get("companyName", "")),
        "company_logo_url": raw.get("companyLogo"),
        "location_city": raw.get("location", raw.get("jobLocation", "")),
        "salary_min": raw.get("salaryMin"),
        "salary_max": raw.get("salaryMax"),
        "description": raw.get("description", raw.get("jobDescription", "")),
        "apply_url": raw.get("url", raw.get("jobUrl", "")),
        "posted_date": _parse_date(raw.get("postedAt", raw.get("datePosted"))),
        "source_platforms": ["Apify"],
        "is_active": True,
    }


def normalize_themuse(raw: dict) -> dict:
    """Normalize The Muse API response."""
    company = raw.get("company", {})
    locations = raw.get("locations", [])
    loc_name = locations[0].get("name", "") if locations else ""

    levels = raw.get("levels", [])
    experience = _map_muse_level(levels[0].get("name", "")) if levels else None

    return {
        "title": raw.get("name", ""),
        "company_name": company.get("name", ""),
        "location_city": loc_name,
        "experience_level": experience,
        "job_type": _normalize_job_type(raw.get("type")),
        "description": raw.get("contents", ""),
        "apply_url": raw.get("refs", {}).get("landing_page"),
        "posted_date": _parse_date(raw.get("publication_date")),
        "source_platforms": ["The Muse"],
        "is_active": True,
    }


def normalize_findwork(raw: dict) -> dict:
    """Normalize Findwork.dev API response."""
    return {
        "title": raw.get("role", ""),
        "company_name": raw.get("company_name", ""),
        "company_logo_url": raw.get("logo"),
        "location_city": raw.get("location"),
        "remote_type": "remote" if raw.get("remote") else "onsite",
        "tech_stack": raw.get("keywords", []),
        "description": raw.get("text"),
        "apply_url": raw.get("url"),
        "posted_date": _parse_date(raw.get("date_posted")),
        "source_platforms": ["Findwork"],
        "is_active": True,
    }


def normalize_yc(raw: dict) -> dict:
    """Normalize YC Work at a Startup data."""
    return {
        "title": raw.get("title", ""),
        "company_name": raw.get("company_name", ""),
        "company_logo_url": raw.get("company_logo"),
        "company_type": "vc_backed",
        "vc_backer": f"YC {raw.get('batch', '')}".strip(),
        "location_city": raw.get("location"),
        "remote_type": "remote" if raw.get("remote") else "onsite",
        "salary_min": raw.get("salary_min"),
        "salary_max": raw.get("salary_max"),
        "experience_level": raw.get("experience"),
        "description": raw.get("description"),
        "apply_url": raw.get("url"),
        "posted_date": _parse_date(raw.get("posted_at")),
        "source_platforms": ["YC"],
        "is_active": True,
    }


def normalize_wellfound(raw: dict) -> dict:
    """Normalize Wellfound (AngelList) data."""
    return {
        "title": raw.get("title", ""),
        "company_name": raw.get("company_name", raw.get("startup", {}).get("name", "")),
        "company_logo_url": raw.get("company_logo"),
        "company_type": "startup",
        "location_city": raw.get("location"),
        "remote_type": "remote" if raw.get("remote") else "onsite",
        "salary_min": raw.get("salary_min"),
        "salary_max": raw.get("salary_max"),
        "description": raw.get("description"),
        "apply_url": raw.get("url"),
        "tech_stack": raw.get("skills", []),
        "source_platforms": ["Wellfound"],
        "is_active": True,
    }


def normalize_linkedin(raw: dict) -> dict:
    """Normalize LinkedIn data (via Apify)."""
    return {
        "title": raw.get("title", ""),
        "company_name": raw.get("companyName", ""),
        "company_logo_url": raw.get("companyLogo"),
        "location_city": raw.get("location", ""),
        "salary_min": raw.get("salaryMin"),
        "salary_max": raw.get("salaryMax"),
        "description": raw.get("description", ""),
        "apply_url": raw.get("url", raw.get("applyUrl", "")),
        "posted_date": _parse_date(raw.get("postedAt")),
        "easy_apply": raw.get("easyApply", False),
        "source_platforms": ["LinkedIn"],
        "is_active": True,
    }


def add_dedup_hash(job: dict) -> dict:
    """Add dedup_hash to a normalized job dict."""
    location = job.get("location_city", "") or ""
    posted = ""
    if job.get("posted_date"):
        if isinstance(job["posted_date"], datetime):
            posted = job["posted_date"].strftime("%Y-%m-%d")
        else:
            posted = str(job["posted_date"])[:10]

    job["dedup_hash"] = generate_dedup_hash(
        company_name=job.get("company_name", ""),
        job_title=job.get("title", ""),
        location=location,
        posted_date=posted,
    )
    return job


# ─── Helpers ─────────────────────────────────────────────────────

def _detect_remote(is_remote) -> str:
    if is_remote is True:
        return "remote"
    return "onsite"


def _normalize_job_type(raw_type: Optional[str]) -> Optional[str]:
    if not raw_type:
        return None
    raw_lower = raw_type.lower()
    mapping = {
        "fulltime": "full-time",
        "full_time": "full-time",
        "full-time": "full-time",
        "parttime": "part-time",
        "part_time": "part-time",
        "part-time": "part-time",
        "contract": "contract",
        "contractor": "contract",
        "freelance": "freelance",
        "intern": "internship",
        "internship": "internship",
    }
    return mapping.get(raw_lower, raw_type)


def _parse_date(date_str: Optional[str]) -> Optional[datetime]:
    if not date_str:
        return None
    if isinstance(date_str, datetime):
        return date_str
    for fmt in [
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
        "%d/%m/%Y",
    ]:
        try:
            return datetime.strptime(date_str, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _relative_date(text: Optional[str]) -> Optional[datetime]:
    """Parse relative dates like '3 days ago'."""
    if not text:
        return None
    import re
    now = datetime.now(timezone.utc)
    match = re.search(r'(\d+)\s*(day|hour|week|month)', text.lower())
    if match:
        num = int(match.group(1))
        unit = match.group(2)
        from datetime import timedelta
        deltas = {
            "hour": timedelta(hours=num),
            "day": timedelta(days=num),
            "week": timedelta(weeks=num),
            "month": timedelta(days=num * 30),
        }
        return now - deltas.get(unit, timedelta())
    return None


def _extract_apply_link(options: list) -> Optional[str]:
    if options and len(options) > 0:
        return options[0].get("link")
    return None


def _map_muse_level(level: str) -> Optional[str]:
    mapping = {
        "entry level": "junior",
        "mid level": "mid",
        "senior level": "senior",
        "management": "lead",
        "internship": "intern",
    }
    return mapping.get(level.lower(), None)
