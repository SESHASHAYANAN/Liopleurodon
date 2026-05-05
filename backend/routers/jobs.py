"""
Liopleurodon — Jobs Router
Search, filter, and retrieve job listings.
Featured (⭐) jobs appear first, then newest scraped jobs on top.
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
    """Search and filter jobs with pagination.
    Featured jobs sort to top, then by posted_date desc (newest first).
    """
    db = get_supabase_admin()

    # ─── Featured Jobs Query ─────────────────────────────────
    # First, try to get featured jobs (if is_featured column exists)
    featured_jobs = []
    try:
        feat_query = db.table("jobs").select("*").eq("is_active", True).eq("is_featured", True)
        # Apply same text search filter to featured
        if q:
            feat_query = feat_query.or_(f"title.ilike.%{q}%,company_name.ilike.%{q}%,description.ilike.%{q}%")
        if location:
            feat_query = feat_query.or_(f"location_city.ilike.%{location}%,location_country.ilike.%{location}%")
        if remote_type:
            feat_query = feat_query.eq("remote_type", remote_type)
        if experience_level:
            feat_query = feat_query.eq("experience_level", experience_level)
        if job_type:
            feat_query = feat_query.eq("job_type", job_type)
        if visa_sponsorship is not None:
            feat_query = feat_query.eq("visa_sponsorship", visa_sponsorship)
        if relocation_support is not None:
            feat_query = feat_query.eq("relocation_support", relocation_support)
        if company_type:
            feat_query = feat_query.eq("company_type", company_type)

        feat_query = feat_query.order("created_at", desc=True).limit(50)
        feat_result = feat_query.execute()
        featured_jobs = feat_result.data or []

        # Mark each featured job so frontend knows
        for fj in featured_jobs:
            fj["_is_featured"] = True
    except Exception:
        # is_featured column may not exist — gracefully skip
        featured_jobs = []

    # ─── Regular Jobs Query ──────────────────────────────────
    query = db.table("jobs").select("*", count="exact").eq("is_active", True)

    # Exclude featured jobs from regular query to avoid duplicates
    try:
        query = query.neq("is_featured", True)
    except Exception:
        pass

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

    # Sorting — always newest first for regular jobs
    desc = sort_order == "desc"
    query = query.order(sort_by, desc=desc)

    # Pagination
    offset = (page - 1) * per_page
    query = query.range(offset, offset + per_page - 1)

    result = query.execute()
    regular_jobs = result.data or []

    # ─── Combine: Featured first (page 1 only), then regular ─
    if page == 1:
        # Deduplicate: remove any regular jobs that are also in featured
        featured_ids = {fj["id"] for fj in featured_jobs}
        regular_jobs = [j for j in regular_jobs if j["id"] not in featured_ids]

        # Mark new scraped jobs (scraped within last 10 minutes)
        ten_min_ago = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
        for job in regular_jobs:
            created = job.get("created_at", "")
            if created and created > ten_min_ago:
                job["_is_new"] = True

        combined = featured_jobs + regular_jobs
    else:
        # Mark new scraped jobs on subsequent pages too
        ten_min_ago = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
        for job in regular_jobs:
            created = job.get("created_at", "")
            if created and created > ten_min_ago:
                job["_is_new"] = True
        combined = regular_jobs

    total_count = (result.count or 0) + len(featured_jobs)

    return {
        "jobs": combined,
        "total": total_count,
        "page": page,
        "per_page": per_page,
        "total_pages": (total_count + per_page - 1) // per_page,
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
        visa = db.table("jobs").select("id", count="exact").eq("is_active", True).eq("visa_sponsorship", True).execute()
        relo = db.table("jobs").select("id", count="exact").eq("is_active", True).eq("relocation_support", True).execute()

        # Count featured jobs
        featured_count = 0
        try:
            feat = db.table("jobs").select("id", count="exact").eq("is_active", True).eq("is_featured", True).execute()
            featured_count = feat.count or 0
        except Exception:
            pass

        return {
            "total_jobs": total.count or 0,
            "remote_jobs": remote.count or 0,
            "vc_backed_jobs": vc.count or 0,
            "stealth_jobs": stealth.count or 0,
            "big_tech_jobs": big_tech.count or 0,
            "visa_jobs": visa.count or 0,
            "relo_jobs": relo.count or 0,
            "featured_jobs": featured_count,
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
