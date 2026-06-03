"""
Liopleurodon — Base Apply Provider
Abstract base class for all ATS apply integrations.
Each provider handles candidate profile mapping, document upload,
submission routing, retries, and status syncing.
"""

from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass, field
import re
import httpx


import random as _random

_RESOLVE_UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
]

async def resolve_apply_url(url: str) -> str:
    """
    Follow redirect chains to resolve an aggregator URL (e.g. Adzuna)
    to the final ATS URL (e.g. jobs.lever.co/...).
    Returns the final URL after all redirects, or the original URL on error.
    Uses retry logic with UA rotation for resilience against rate limits.
    """
    if not url:
        return url
    import asyncio
    max_retries = 3
    for attempt in range(max_retries):
        try:
            ua = _RESOLVE_UAS[attempt % len(_RESOLVE_UAS)]
            async with httpx.AsyncClient(
                timeout=15,
                follow_redirects=True,
                headers={"User-Agent": ua}
            ) as client:
                # Use GET (not HEAD) — many aggregators/CDNs respond differently to HEAD
                resp = await client.get(url, headers={"Accept": "text/html"})
                if resp.status_code in (429, 503, 403) and attempt < max_retries - 1:
                    wait = (2 ** attempt) + _random.uniform(0.5, 2.0)
                    print(f"[Apply] URL resolve got {resp.status_code}, retrying in {wait:.1f}s...")
                    await asyncio.sleep(wait)
                    continue
                resolved = str(resp.url)
                if resolved != url:
                    print(f"[Apply] Resolved URL: {url[:60]}... → {resolved[:80]}")
                return resolved
        except Exception as e:
            if attempt < max_retries - 1:
                wait = (2 ** attempt) + _random.uniform(0.5, 1.5)
                print(f"[Apply] URL resolution error (attempt {attempt+1}): {e}, retrying in {wait:.1f}s")
                await asyncio.sleep(wait)
                continue
            print(f"[Apply] URL resolution failed for {url[:60]}: {e}")
            return url
    return url


@dataclass
class CandidateProfile:
    """Standardized candidate profile for cross-ATS submission."""
    full_name: str
    email: str
    phone: str = ""
    linkedin_url: str = ""
    portfolio_url: str = ""
    location: str = ""
    current_company: str = ""
    cover_letter: str = ""
    resume_url: str = ""
    resume_filename: str = ""
    custom_answers: dict = field(default_factory=dict)


@dataclass
class ApplyResult:
    """Standardized result from an ATS submission."""
    success: bool
    provider: str
    message: str
    candidate_id: Optional[str] = None
    application_id: Optional[str] = None
    ats_response: Optional[dict] = None
    steps_completed: list = field(default_factory=list)
    error_code: Optional[str] = None


@dataclass
class FormField:
    """A field in the ATS application form."""
    name: str
    label: str
    field_type: str  # text, email, phone, file, textarea, select, checkbox
    required: bool = False
    options: list = field(default_factory=list)  # for select fields
    max_length: Optional[int] = None
    description: str = ""
    auto_fillable: bool = False  # can be pre-filled from profile


# ─── ATS URL Parsers ─────────────────────────────────────────────

def extract_greenhouse_ids(url: str) -> Optional[tuple]:
    """
    Extract board_token and job_id from a Greenhouse URL.
    Patterns:
      - boards.greenhouse.io/company/jobs/12345
      - job-boards.greenhouse.io/company/jobs/12345
      - boards-api.greenhouse.io/v1/boards/company/jobs/12345
    """
    if not url:
        return None
    patterns = [
        r'boards\.greenhouse\.io/([^/]+)/jobs/(\d+)',
        r'job-boards\.greenhouse\.io/([^/]+)/jobs/(\d+)',
        r'greenhouse\.io/([^/]+)/jobs/(\d+)',
        r'boards-api\.greenhouse\.io/v1/boards/([^/]+)/jobs/(\d+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url, re.I)
        if match:
            return (match.group(1), match.group(2))
    return None


def extract_lever_ids(url: str) -> Optional[tuple]:
    """
    Extract company_slug and posting_id from a Lever URL.
    Patterns:
      - jobs.lever.co/company/uuid
      - lever.co/company/uuid
    """
    if not url:
        return None
    patterns = [
        r'jobs\.lever\.co/([^/]+)/([a-f0-9-]+)',
        r'lever\.co/([^/]+)/([a-f0-9-]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url, re.I)
        if match:
            return (match.group(1), match.group(2))
    return None


def extract_ashby_ids(url: str) -> Optional[tuple]:
    """
    Extract company and job_posting_id from an Ashby URL.
    Patterns:
      - jobs.ashbyhq.com/company/uuid
    """
    if not url:
        return None
    match = re.search(r'jobs\.ashbyhq\.com/([^/]+)/([a-f0-9-]+)', url, re.I)
    if match:
        return (match.group(1), match.group(2))
    return None


def extract_workable_ids(url: str) -> Optional[tuple]:
    """
    Extract company and job_shortcode from a Workable URL.
    Patterns:
      - apply.workable.com/company/j/SHORTCODE
      - company.workable.com/j/SHORTCODE
    """
    if not url:
        return None
    patterns = [
        r'apply\.workable\.com/([^/]+)/j/([A-Za-z0-9]+)',
        r'([^.]+)\.workable\.com/j/([A-Za-z0-9]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url, re.I)
        if match:
            return (match.group(1), match.group(2))
    return None


def extract_smartrecruiters_ids(url: str) -> Optional[tuple]:
    """
    Extract company and posting_id from a SmartRecruiters URL.
    Patterns:
      - jobs.smartrecruiters.com/Company/uuid
    """
    if not url:
        return None
    match = re.search(r'jobs\.smartrecruiters\.com/([^/]+)/([a-f0-9-]+)', url, re.I)
    if match:
        return (match.group(1), match.group(2))
    return None


def extract_bamboohr_ids(url: str) -> Optional[tuple]:
    """
    Extract company_domain and job_id from a BambooHR URL.
    Patterns:
      - company.bamboohr.com/careers/123
      - company.bamboohr.com/jobs/view.php?id=123
    """
    if not url:
        return None
    patterns = [
        r'([^.]+)\.bamboohr\.com/careers/(\d+)',
        r'([^.]+)\.bamboohr\.com/jobs/view\.php\?id=(\d+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url, re.I)
        if match:
            return (match.group(1), match.group(2))
    return None


def extract_recruitee_ids(url: str) -> Optional[tuple]:
    """
    Extract company and offer_slug from a Recruitee URL.
    Patterns:
      - company.recruitee.com/o/job-slug
    """
    if not url:
        return None
    match = re.search(r'([^.]+)\.recruitee\.com/o/([^/\?]+)', url, re.I)
    if match:
        return (match.group(1), match.group(2))
    return None


def extract_breezyhr_ids(url: str) -> Optional[tuple]:
    """
    Extract company and position_id from a Breezy HR URL.
    Patterns:
      - company.breezy.hr/p/uuid
    """
    if not url:
        return None
    match = re.search(r'([^.]+)\.breezy\.hr/p/([a-f0-9]+)', url, re.I)
    if match:
        return (match.group(1), match.group(2))
    return None


# ─── Provider-to-Extractor Map ───────────────────────────────────

ATS_EXTRACTORS = {
    "Greenhouse": extract_greenhouse_ids,
    "Lever": extract_lever_ids,
    "Ashby": extract_ashby_ids,
    "Workable": extract_workable_ids,
    "SmartRecruiters": extract_smartrecruiters_ids,
    "BambooHR": extract_bamboohr_ids,
    "Recruitee": extract_recruitee_ids,
    "Breezy HR": extract_breezyhr_ids,
}

# Providers that we fully support for direct apply (Phase 1+2)
SUPPORTED_PROVIDERS = {"Greenhouse", "Lever"}


def detect_direct_apply_support(ats_detected: str, apply_url: str) -> Optional[dict]:
    """
    Check if a job supports direct apply based on its ATS detection.
    Returns support info even if URL IDs can't be extracted (many jobs
    come through aggregators with redirect URLs that don't match ATS patterns).
    """
    if not ats_detected:
        return None

    for provider_name, extractor in ATS_EXTRACTORS.items():
        if provider_name.lower() in ats_detected.lower() and provider_name in SUPPORTED_PROVIDERS:
            # Try to extract IDs from URL (bonus, not required)
            ids = extractor(apply_url or "") if apply_url else None
            return {
                "direct_apply_supported": True,
                "direct_apply_ats": provider_name.lower(),
                "ats_ids": ids,  # May be None if URL is a redirect
                "apply_url": apply_url or "",
            }
    return None


class BaseApplyProvider(ABC):
    """Abstract base class for ATS apply providers."""

    @abstractmethod
    async def submit_application(
        self,
        candidate: CandidateProfile,
        job: dict,
        resume_bytes: Optional[bytes] = None,
    ) -> ApplyResult:
        """
        Submit an application to the ATS.
        Returns an ApplyResult with success status and tracking info.
        """
        pass

    @abstractmethod
    async def get_application_form(self, job: dict) -> list[FormField]:
        """
        Retrieve the application form fields for a specific job.
        Returns a list of FormField objects describing what the ATS expects.
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the provider name (e.g. 'Greenhouse', 'Lever')."""
        pass

    def supports_job(self, job: dict) -> bool:
        """Check if this provider can handle a specific job."""
        ats = (job.get("ats_detected") or job.get("direct_apply_ats") or "").lower()
        return self.get_provider_name().lower() in ats
