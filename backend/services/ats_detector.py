"""
Liopleurodon — ATS Detector Service
Identifies the Applicant Tracking System (ATS) used by a company
from the job's apply URL. Uses fast URL pattern matching first,
then falls back to Groq AI for ambiguous cases.
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
    (re.compile(r'rippling\.com/.*careers', re.I), 'Rippling'),

    # Gusto
    (re.compile(r'gusto\.com/.*jobs', re.I), 'Gusto'),

    # Deel
    (re.compile(r'deel\.com/.*careers', re.I), 'Deel'),

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

    # ZipRecruiter
    (re.compile(r'ziprecruiter\.com', re.I), 'ZipRecruiter'),

    # Glassdoor
    (re.compile(r'glassdoor\.com', re.I), 'Glassdoor'),

    # Naukri
    (re.compile(r'naukri\.com', re.I), 'Naukri'),

    # YCombinator
    (re.compile(r'workatastartup\.com', re.I), 'YC Work at a Startup'),
    (re.compile(r'ycombinator\.com', re.I), 'YC Jobs'),

    # Web3 Career
    (re.compile(r'web3\.career', re.I), 'Web3 Career'),

    # Simplify
    (re.compile(r'simplify\.jobs', re.I), 'Simplify'),

    # Dealls
    (re.compile(r'dealls\.com', re.I), 'Dealls'),

    # Clera
    (re.compile(r'getclera\.com', re.I), 'Clera'),

    # DataAnnotation
    (re.compile(r'dataannotation\.tech', re.I), 'Direct Apply'),

    # Dice
    (re.compile(r'dice\.com', re.I), 'Dice'),

    # Monster
    (re.compile(r'monster\.com', re.I), 'Monster'),

    # Hired
    (re.compile(r'hired\.com', re.I), 'Hired'),

    # Triplebyte / Karat
    (re.compile(r'triplebyte\.com', re.I), 'Triplebyte'),

    # Dover
    (re.compile(r'dover\.com', re.I), 'Dover'),

    # Gem
    (re.compile(r'gem\.com', re.I), 'Gem'),

    # Freshteam (Freshworks)
    (re.compile(r'freshteam\.com', re.I), 'Freshteam'),

    # Zoho Recruit
    (re.compile(r'zoho\.com.*recruit', re.I), 'Zoho Recruit'),

    # ApplyBoard
    (re.compile(r'applyboard\.com', re.I), 'ApplyBoard'),
]


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
                                '{\"ats\": \"ATS Name\"} or {\"ats\": null} if unknown. '
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
    Returns the ATS name or None.
    """
    if not apply_url:
        return None

    # Step 1: Fast URL pattern matching
    ats = detect_ats_from_url(apply_url)
    if ats:
        return ats

    # Step 2: Groq AI fallback for unknown URLs
    ats = await detect_ats_with_ai(company_name, apply_url)
    return ats


async def detect_ats_batch(jobs: list) -> list:
    """
    Detect ATS for a batch of jobs. Uses URL patterns for most,
    and batches unknown URLs for a single Groq AI call.
    Returns the jobs list with 'ats_detected' field added.
    """
    unknown_jobs = []

    for job in jobs:
        apply_url = job.get("apply_url")
        company_name = job.get("company_name", "")

        ats = detect_ats_from_url(apply_url)
        if ats:
            job["ats_detected"] = ats
        else:
            unknown_jobs.append(job)

    # Batch AI detection for unknown URLs
    if unknown_jobs:
        ats_results = await _batch_detect_ats_groq(unknown_jobs)
        for job, ats_name in zip(unknown_jobs, ats_results):
            job["ats_detected"] = ats_name  # may be None

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
                                '{\"results\": [{\"idx\": 0, \"ats\": \"ATS Name\"}, ...]}. '
                                "Use null for ats if you cannot determine it. "
                                "Common ATS: Workday, Greenhouse, Lever, iCIMS, Taleo, SmartRecruiters, "
                                "Workable, Ashby, BambooHR, JazzHR, Jobvite, Recruitee, Personio. "
                                "Job boards (LinkedIn, Indeed, ZipRecruiter) are valid answers. "
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
