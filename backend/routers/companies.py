"""
Liopleurodon — Companies Router
Company profiles and VC-backed listings.
"""

from fastapi import APIRouter
from typing import Optional
from database import get_supabase_admin

router = APIRouter(prefix="/api/companies", tags=["companies"])


@router.get("")
async def list_companies(
    q: Optional[str] = None,
    company_type: Optional[str] = None,
    vc_backer: Optional[str] = None,
    page: int = 1,
    per_page: int = 20,
):
    """List companies with optional filters."""
    db = get_supabase_admin()
    query = db.table("companies").select("*", count="exact")

    if q:
        query = query.ilike("name", f"%{q}%")
    if company_type:
        query = query.eq("company_type", company_type)
    if vc_backer:
        query = query.contains("vc_backers", [vc_backer])

    offset = (page - 1) * per_page
    query = query.range(offset, offset + per_page - 1)
    result = query.execute()

    return {"companies": result.data or [], "total": result.count or 0}


@router.get("/{slug}")
async def get_company(slug: str):
    """Get a company profile by slug."""
    db = get_supabase_admin()
    company = db.table("companies").select("*").eq("slug", slug).single().execute()

    # Get active jobs for this company
    jobs = (db.table("jobs")
            .select("*")
            .eq("is_active", True)
            .ilike("company_name", f"%{company.data.get('name', '')}%")
            .order("posted_date", desc=True)
            .limit(50)
            .execute())

    return {
        "company": company.data,
        "jobs": jobs.data or [],
        "job_count": len(jobs.data or []),
    }
