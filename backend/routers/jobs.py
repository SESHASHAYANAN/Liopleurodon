"""
Liopleurodon — Jobs Router
Search, filter, and retrieve job listings.
"""

from fastapi import APIRouter, Query
from typing import Optional
from datetime import datetime, timezone, timedelta
from database import get_supabase_admin

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("")
async def search_jobs(
    q: Optional[str] = None,
    location: Optional[str] = None,
    remote_type: Optional[str] = None,
    experience_level: Optional[str] = None,
    job_type: Optional[str] = None,
    salary_min: Optional[float] = None,
    salary_max: Optional[float] = None,
    visa_sponsorship: Optional[bool] = None,
    relocation_support: Optional[bool] = None,
    company_type: Optional[str] = None,
    vc_backer: Optional[str] = None,
    tech_stack: Optional[str] = None,
    source: Optional[str] = None,
    posted_within: Optional[str] = None,
    page: int = 1,
    per_page: int = 20,
    sort_by: str = "posted_date",
    sort_order: str = "desc",
):
    """Search and filter jobs with pagination."""
    db = get_supabase_admin()
    query = db.table("jobs").select("*", count="exact").eq("is_active", True)

    # Text search
    if q:
        query = query.or_(f"title.ilike.%{q}%,company_name.ilike.%{q}%,description.ilike.%{q}%")

    # Filters
    if location:
        query = query.or_(f"location_city.ilike.%{location}%,location_country.ilike.%{location}%")
    if remote_type:
        query = query.eq("remote_type", remote_type)
    if experience_level:
        query = query.eq("experience_level", experience_level)
    if job_type:
        query = query.eq("job_type", job_type)
    if salary_min:
        query = query.gte("salary_min", salary_min)
    if salary_max:
        query = query.lte("salary_max", salary_max)
    if visa_sponsorship is not None:
        query = query.eq("visa_sponsorship", visa_sponsorship)
    if relocation_support is not None:
        query = query.eq("relocation_support", relocation_support)
    if company_type:
        query = query.eq("company_type", company_type)
    if vc_backer:
        query = query.eq("vc_backer", vc_backer)
    if tech_stack:
        tags = [t.strip() for t in tech_stack.split(",")]
        query = query.contains("tech_stack", tags)
    if source:
        query = query.contains("source_platforms", [source])
    if posted_within:
        now = datetime.now(timezone.utc)
        delta_map = {"24h": timedelta(hours=24), "week": timedelta(weeks=1), "month": timedelta(days=30)}
        delta = delta_map.get(posted_within, timedelta(days=30))
        cutoff = (now - delta).isoformat()
        query = query.gte("posted_date", cutoff)

    # Sorting
    desc = sort_order == "desc"
    query = query.order(sort_by, desc=desc)

    # Pagination
    offset = (page - 1) * per_page
    query = query.range(offset, offset + per_page - 1)

    result = query.execute()

    return {
        "jobs": result.data or [],
        "total": result.count or 0,
        "page": page,
        "per_page": per_page,
        "total_pages": ((result.count or 0) + per_page - 1) // per_page,
    }


@router.get("/stats")
async def get_job_stats():
    """Get job statistics for the sidebar."""
    db = get_supabase_admin()

    try:
        total = db.table("jobs").select("id", count="exact").eq("is_active", True).execute()
        remote = db.table("jobs").select("id", count="exact").eq("is_active", True).eq("remote_type", "remote").execute()
        vc = db.table("jobs").select("id", count="exact").eq("is_active", True).eq("company_type", "vc_backed").execute()
        stealth = db.table("jobs").select("id", count="exact").eq("is_active", True).eq("is_stealth", True).execute()
        big_tech = db.table("jobs").select("id", count="exact").eq("is_active", True).eq("company_type", "big_tech").execute()

        return {
            "total_jobs": total.count or 0,
            "remote_jobs": remote.count or 0,
            "vc_backed_jobs": vc.count or 0,
            "stealth_jobs": stealth.count or 0,
            "big_tech_jobs": big_tech.count or 0,
        }
    except Exception as e:
        return {"total_jobs": 0, "error": str(e)}


@router.get("/{job_id}")
async def get_job(job_id: str):
    """Get a single job by ID."""
    db = get_supabase_admin()
    result = db.table("jobs").select("*").eq("id", job_id).single().execute()
    return result.data


@router.get("/{job_id}/similar")
async def get_similar_jobs(job_id: str, limit: int = 10):
    """Get similar jobs using pgvector similarity."""
    from services.embedding_service import find_similar_jobs
    similar = await find_similar_jobs(job_id, limit)
    return {"similar_jobs": similar}
