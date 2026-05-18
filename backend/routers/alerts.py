"""
Liopleurodon — Alerts Router
Job alert CRUD operations.
"""

from fastapi import APIRouter, Header
from typing import Optional
from database import get_supabase_admin, get_supabase

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


def _get_user_id(authorization: str) -> Optional[str]:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.replace("Bearer ", "")
    try:
        sb = get_supabase()
        user = sb.auth.get_user(token)
        return user.user.id if user and user.user else None
    except Exception:
        return None


@router.get("")
async def get_alerts(authorization: str = Header("")):
    """Get user's job alerts."""
    user_id = _get_user_id(authorization)
    if not user_id:
        return {"error": "Unauthorized"}, 401

    db = get_supabase_admin()
    result = (db.table("job_alerts")
              .select("*")
              .eq("user_id", user_id)
              .order("created_at", desc=True)
              .execute())
    return {"alerts": result.data or []}


@router.post("")
async def create_alert(
    name: str,
    filters: dict,
    frequency: str = "daily",
    authorization: str = Header(""),
):
    """Create a job alert."""
    user_id = _get_user_id(authorization)
    if not user_id:
        return {"error": "Unauthorized"}, 401

    db = get_supabase_admin()
    result = db.table("job_alerts").insert({
        "user_id": user_id,
        "name": name,
        "filters": filters,
        "frequency": frequency,
        "is_active": True,
    }).execute()
    return {"alert": result.data[0] if result.data else {}}


@router.delete("/{alert_id}")
async def delete_alert(alert_id: str, authorization: str = Header("")):
    """Delete a job alert."""
    user_id = _get_user_id(authorization)
    if not user_id:
        return {"error": "Unauthorized"}, 401

    db = get_supabase_admin()
    db.table("job_alerts").delete().eq("id", alert_id).eq("user_id", user_id).execute()
    return {"success": True}
