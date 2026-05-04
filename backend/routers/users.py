"""
Liopleurodon — Users Router
Auth, profile, saved jobs.
"""

from fastapi import APIRouter, Header
from typing import Optional
from database import get_supabase_admin, get_supabase

router = APIRouter(prefix="/api/users", tags=["users"])


def _get_user_id(authorization: str) -> Optional[str]:
    """Extract user ID from Supabase JWT."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.replace("Bearer ", "")
    try:
        sb = get_supabase()
        user = sb.auth.get_user(token)
        return user.user.id if user and user.user else None
    except Exception:
        return None


@router.get("/me")
async def get_profile(authorization: str = Header("")):
    """Get current user profile."""
    user_id = _get_user_id(authorization)
    if not user_id:
        return {"error": "Unauthorized"}, 401

    db = get_supabase_admin()
    result = db.table("user_profiles").select("*").eq("id", user_id).single().execute()
    return result.data or {}


@router.get("/saved-jobs")
async def get_saved_jobs(authorization: str = Header(""), page: int = 1, per_page: int = 20):
    """Get user's saved jobs."""
    user_id = _get_user_id(authorization)
    if not user_id:
        return {"error": "Unauthorized"}, 401

    db = get_supabase_admin()
    offset = (page - 1) * per_page
    result = (db.table("saved_jobs")
              .select("*, jobs(*)")
              .eq("user_id", user_id)
              .order("created_at", desc=True)
              .range(offset, offset + per_page - 1)
              .execute())

    return {"saved_jobs": result.data or []}


@router.post("/saved-jobs/{job_id}")
async def save_job(job_id: str, authorization: str = Header("")):
    """Save a job."""
    user_id = _get_user_id(authorization)
    if not user_id:
        return {"error": "Unauthorized"}, 401

    db = get_supabase_admin()
    try:
        db.table("saved_jobs").insert({"user_id": user_id, "job_id": job_id}).execute()
        return {"success": True}
    except Exception as e:
        return {"error": str(e)}


@router.delete("/saved-jobs/{job_id}")
async def unsave_job(job_id: str, authorization: str = Header("")):
    """Remove a saved job."""
    user_id = _get_user_id(authorization)
    if not user_id:
        return {"error": "Unauthorized"}, 401

    db = get_supabase_admin()
    db.table("saved_jobs").delete().eq("user_id", user_id).eq("job_id", job_id).execute()
    return {"success": True}


@router.get("/applications")
async def get_applications(authorization: str = Header("")):
    """Get user's job applications."""
    user_id = _get_user_id(authorization)
    if not user_id:
        return {"error": "Unauthorized"}, 401

    db = get_supabase_admin()
    result = (db.table("user_applications")
              .select("*, jobs(*)")
              .eq("user_id", user_id)
              .order("applied_at", desc=True)
              .execute())

    return {"applications": result.data or []}


@router.post("/applications/{job_id}")
async def track_application(job_id: str, authorization: str = Header("")):
    """Track a job application."""
    user_id = _get_user_id(authorization)
    if not user_id:
        return {"error": "Unauthorized"}, 401

    db = get_supabase_admin()
    try:
        db.table("user_applications").insert({
            "user_id": user_id,
            "job_id": job_id,
            "status": "applied",
        }).execute()
        return {"success": True}
    except Exception as e:
        return {"error": str(e)}
