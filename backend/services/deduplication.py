"""
Liopleurodon — Deduplication Service
Generates composite hashes and merges duplicate jobs from multiple sources.
"""

import hashlib
import re
from typing import Optional


def normalize_text(text: str) -> str:
    """Normalize text for consistent hashing."""
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text


def generate_dedup_hash(
    company_name: str,
    job_title: str,
    location: str = "",
    posted_date: str = ""
) -> str:
    """
    Generate a deduplication hash from job attributes.
    Uses SHA-256 of normalized: company_name + job_title + location + posted_date
    """
    parts = [
        normalize_text(company_name),
        normalize_text(job_title),
        normalize_text(location or ""),
        normalize_text(posted_date or ""),
    ]
    composite = "|".join(parts)
    return hashlib.sha256(composite.encode()).hexdigest()


def merge_job_data(existing: dict, new: dict) -> dict:
    """
    Merge two job records, keeping the most complete data from each.
    The existing record is the base; new fields fill in blanks.
    Source platforms are always merged.
    """
    merged = {**existing}

    # Merge source_platforms (always combine)
    existing_sources = set(existing.get("source_platforms", []))
    new_sources = set(new.get("source_platforms", []))
    merged["source_platforms"] = list(existing_sources | new_sources)

    # For all other fields, prefer non-null/non-empty values
    skip_fields = {"id", "dedup_hash", "created_at", "source_platforms"}

    for key, new_val in new.items():
        if key in skip_fields:
            continue

        existing_val = existing.get(key)

        # If existing is empty but new has data, use new
        if _is_empty(existing_val) and not _is_empty(new_val):
            merged[key] = new_val

        # For arrays, merge them (skills, tech_stack, etc.)
        elif isinstance(existing_val, list) and isinstance(new_val, list):
            merged[key] = list(set(existing_val + new_val))

    return merged


def _is_empty(val) -> bool:
    """Check if a value is effectively empty."""
    if val is None:
        return True
    if isinstance(val, str) and val.strip() == "":
        return True
    if isinstance(val, list) and len(val) == 0:
        return True
    return False
