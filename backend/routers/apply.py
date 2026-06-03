"""
Liopleurodon — Apply Router
Handles in-app direct apply via official ATS Job Board APIs.
Provides endpoints for form retrieval, application submission,
status checking, user profile management, and live browser automation.
"""

from fastapi import APIRouter, Header, UploadFile, File, Form
from typing import Optional
from datetime import datetime, timezone
from database import get_supabase_admin, get_supabase
from services.direct_apply.base import (
    CandidateProfile, SUPPORTED_PROVIDERS, detect_direct_apply_support,
)
from services.direct_apply.greenhouse import GreenhouseProvider
from services.direct_apply.lever import LeverProvider

router = APIRouter(prefix="/api/apply", tags=["apply"])

# Initialize providers
PROVIDERS = {
    "greenhouse": GreenhouseProvider(),
    "lever": LeverProvider(),
}


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


def _get_provider(ats_name: str):
    """Get the correct provider instance for an ATS."""
    key = (ats_name or "").lower().strip()
    return PROVIDERS.get(key)


@router.get("/supported")
async def get_supported_ats():
    """List all ATS platforms that support in-app direct apply."""
    return {
        "supported_providers": list(SUPPORTED_PROVIDERS),
        "providers": [
            {
                "name": "Greenhouse",
                "slug": "greenhouse",
                "description": "Job Board API — supports resume upload, custom questions, and cover letter",
                "coverage": "30+ major tech companies (Uber, Airbnb, Stripe, Coinbase, etc.)",
            },
            {
                "name": "Lever",
                "slug": "lever",
                "description": "Postings API — supports resume upload, LinkedIn profiles, and additional info",
                "coverage": "20+ companies (Shopify, Lyft, Swiggy, Razorpay, etc.)",
            },
        ],
    }


@router.get("/{job_id}/check")
async def check_direct_apply(job_id: str):
    """
    Check if a specific job supports in-app direct apply.
    Returns support status, provider info, and form fields if supported.
    """
    db = get_supabase_admin()
    result = db.table("jobs").select("*").eq("id", job_id).single().execute()
    job = result.data

    if not job:
        return {"supported": False, "reason": "Job not found"}

    ats = job.get("direct_apply_ats", "")
    apply_url = job.get("apply_url", "")

    # Check if it's a supported ATS
    support_info = detect_direct_apply_support(ats, apply_url)

    if not support_info:
        return {
            "supported": False,
            "ats_detected": ats,
            "reason": f"ATS '{ats}' does not support in-app apply. Use external link.",
            "apply_url": apply_url,
        }

    provider = _get_provider(support_info["direct_apply_ats"])
    if not provider:
        return {
            "supported": False,
            "ats_detected": ats,
            "reason": "Provider not yet implemented",
        }

    return {
        "supported": True,
        "ats_detected": ats,
        "provider": support_info["direct_apply_ats"],
        "provider_name": provider.get_provider_name(),
    }



# ─── Profile loader helper ───────────────────────────────────────

def _load_profile_from_db(db, user_id: str, profile: dict) -> dict:
    """Fill empty profile fields from database."""
    try:
        result = db.table("user_profiles").select("*").eq("id", user_id).single().execute()
        saved = result.data or {}
        for key in ["full_name", "email", "phone", "linkedin_url", "portfolio_url", "location", "current_company"]:
            if not profile.get(key):
                profile[key] = saved.get(key, "")
        if not profile.get("cover_letter"):
            profile["cover_letter"] = saved.get("cover_letter_default", "")
    except Exception:
        pass
    return profile


@router.get("/{job_id}/form")
async def get_apply_form(job_id: str, authorization: str = Header("")):
    """
    Get the application form fields for a job.
    Returns pre-filled values from the user's profile if authenticated.
    """
    db = get_supabase_admin()
    result = db.table("jobs").select("*").eq("id", job_id).single().execute()
    job = result.data

    if not job:
        return {"error": "Job not found"}, 404

    ats = job.get("direct_apply_ats") or ""
    apply_url = job.get("apply_url") or ""
    
    if not ats:
        return {
            "supported": False,
            "fields": [],
            "reason": "No ATS platform detected for this job. Cannot auto-apply.",
        }

    support_info = detect_direct_apply_support(ats, apply_url)

    if not support_info:
        return {
            "supported": False,
            "fields": [],
            "reason": f"ATS '{ats}' does not support in-app apply",
        }

    provider = _get_provider(support_info["direct_apply_ats"])
    if not provider:
        return {"supported": False, "fields": [], "reason": "Provider not implemented"}

    # Fetch form fields from ATS
    fields = await provider.get_application_form(job)

    # Pre-fill from user profile if authenticated
    prefill = {}
    user_id = _get_user_id(authorization)
    if user_id:
        try:
            profile_result = (db.table("user_profiles")
                              .select("*")
                              .eq("id", user_id)
                              .single()
                              .execute())
            profile = profile_result.data or {}
            prefill = {
                "first_name": (profile.get("full_name") or "").split(" ")[0],
                "last_name": " ".join((profile.get("full_name") or "").split(" ")[1:]),
                "name": profile.get("full_name", ""),
                "email": profile.get("email", ""),
                "phone": profile.get("phone", ""),
                "linkedin_url": profile.get("linkedin_url", ""),
                "urls[LinkedIn]": profile.get("linkedin_url", ""),
                "portfolio_url": profile.get("portfolio_url", ""),
                "urls[Portfolio]": profile.get("portfolio_url", ""),
                "org": profile.get("current_company", ""),
                "location": profile.get("location", ""),
                "cover_letter": profile.get("cover_letter_default", ""),
                "comments": profile.get("cover_letter_default", ""),
            }

            # Get default resume
            resume_result = (db.table("user_resumes")
                             .select("*")
                             .eq("user_id", user_id)
                             .eq("is_default", True)
                             .limit(1)
                             .execute())
            if resume_result.data:
                prefill["resume_url"] = resume_result.data[0].get("file_url", "")
                prefill["resume_filename"] = resume_result.data[0].get("file_name", "")

        except Exception as e:
            print(f"[Apply] Profile prefill error: {e}")

    # Check if already applied
    already_applied = False
    if user_id:
        try:
            app_check = (db.table("user_applications")
                         .select("id")
                         .eq("user_id", user_id)
                         .eq("job_id", job_id)
                         .execute())
            already_applied = bool(app_check.data)
        except Exception:
            pass

    return {
        "supported": True,
        "provider": support_info["direct_apply_ats"],
        "provider_name": provider.get_provider_name(),
        "fields": [
            {
                "name": f.name,
                "label": f.label,
                "field_type": f.field_type,
                "required": f.required,
                "options": f.options,
                "description": f.description,
                "auto_fillable": f.auto_fillable,
                "prefill_value": prefill.get(f.name, ""),
            }
            for f in fields
        ],
        "prefill": prefill,
        "already_applied": already_applied,
        "job": {
            "id": job.get("id"),
            "title": job.get("title"),
            "company_name": job.get("company_name"),
            "company_logo_url": job.get("company_logo_url"),
            "location_city": job.get("location_city"),
            "location_country": job.get("location_country"),
            "remote_type": job.get("remote_type"),
            "salary_min": job.get("salary_min"),
            "salary_max": job.get("salary_max"),
            "salary_currency": job.get("salary_currency"),
            "ats_detected": job.get("ats_detected"),
            "experience_level": job.get("experience_level"),
            "job_type": job.get("job_type"),
            "tech_stack": job.get("tech_stack"),
            "description": job.get("description"),
            "requirements": job.get("requirements"),
            "apply_url": job.get("apply_url"),
        },
    }


@router.post("/{job_id}/submit")
async def submit_application(
    job_id: str,
    authorization: str = Header(""),
    full_name: str = Form(""),
    email: str = Form(""),
    phone: str = Form(""),
    linkedin_url: str = Form(""),
    portfolio_url: str = Form(""),
    location: str = Form(""),
    current_company: str = Form(""),
    cover_letter: str = Form(""),
    custom_answers: str = Form("{}"),
    resume: Optional[UploadFile] = File(None),
    resume_url: str = Form(""),
    resume_filename: str = Form(""),
):
    """
    Submit a job application via the ATS proxy.
    Accepts multipart/form-data with resume file upload.
    Returns step-by-step progress and final result.
    """
    import json

    # Auth check
    user_id = _get_user_id(authorization)
    if not user_id:
        return {"error": "Authentication required to apply", "message": "Authentication required to apply", "success": False}

    db = get_supabase_admin()

    # Fetch job
    result = db.table("jobs").select("*").eq("id", job_id).single().execute()
    job = result.data
    if not job:
        return {"error": "Job not found", "message": "Job not found", "success": False}

    # Clean up any previous failed/stale applications so user can retry
    try:
        existing = (db.table("user_applications")
                    .select("id, status")
                    .eq("user_id", user_id)
                    .eq("job_id", job_id)
                    .execute())
        if existing.data:
            # Delete failed attempts so user can retry
            for row in existing.data:
                if row.get("status") in ("failed", None):
                    db.table("user_applications").delete().eq("id", row["id"]).execute()
    except Exception:
        pass

    # Determine provider
    ats = job.get("direct_apply_ats") or ""
    apply_url = job.get("apply_url") or ""
    
    if not ats:
        return {
            "error": "No ATS platform detected for this job",
            "message": "No ATS platform detected for this job. Please apply externally.",
            "success": False,
            "apply_url": apply_url,
        }

    support_info = detect_direct_apply_support(ats, apply_url)

    if not support_info:
        return {
            "error": f"ATS '{ats}' does not support in-app apply",
            "message": f"ATS '{ats}' does not support in-app apply",
            "success": False,
            "apply_url": apply_url,
        }

    provider = _get_provider(support_info["direct_apply_ats"])
    if not provider:
        return {"error": "Provider not implemented", "message": "Provider not implemented", "success": False}

    # Parse custom answers
    try:
        answers = json.loads(custom_answers) if custom_answers else {}
    except json.JSONDecodeError:
        answers = {}

    # Build candidate profile
    candidate = CandidateProfile(
        full_name=full_name,
        email=email,
        phone=phone,
        linkedin_url=linkedin_url,
        portfolio_url=portfolio_url,
        location=location,
        current_company=current_company,
        cover_letter=cover_letter,
        resume_url=resume_url,
        resume_filename=resume.filename if resume else resume_filename,
        custom_answers=answers,
    )

    # Read resume bytes if file provided
    resume_bytes = None
    if resume:
        resume_bytes = await resume.read()
    elif resume_url:
        # Fetch resume from Supabase Storage URL
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(resume_url)
                if resp.status_code == 200:
                    resume_bytes = resp.content
        except Exception as e:
            print(f"[Apply] Failed to fetch resume from URL: {e}")

    # Submit via provider
    apply_result = await provider.submit_application(candidate, job, resume_bytes)

    # Track the application in our database
    try:
        db.table("user_applications").insert({
            "user_id": user_id,
            "job_id": job_id,
            "status": "applied" if apply_result.success else "failed",
            "apply_method": f"direct_{support_info['direct_apply_ats']}",
            "ats_response": apply_result.ats_response,
            "resume_used": resume_url or (resume.filename if resume else None),
            "cover_letter_used": cover_letter if cover_letter else None,
            "submission_steps": apply_result.steps_completed,
            "notes": apply_result.message,
        }).execute()
    except Exception as e:
        print(f"[Apply] Tracking insert error: {e}")

    # Update user profile with latest info (save for next apply)
    try:
        update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
        if phone:
            update_data["phone"] = phone
        if linkedin_url:
            update_data["linkedin_url"] = linkedin_url
        if portfolio_url:
            update_data["portfolio_url"] = portfolio_url
        if location:
            update_data["location"] = location
        if current_company:
            update_data["current_company"] = current_company

        db.table("user_profiles").update(update_data).eq("id", user_id).execute()
    except Exception:
        pass

    return {
        "success": apply_result.success,
        "provider": apply_result.provider,
        "message": apply_result.message,
        "candidate_id": apply_result.candidate_id,
        "application_id": apply_result.application_id,
        "steps": apply_result.steps_completed,
        "error_code": apply_result.error_code,
    }


@router.get("/profile")
async def get_apply_profile(authorization: str = Header("")):
    """Get current user's profile for auto-apply."""
    user_id = _get_user_id(authorization)
    if not user_id:
        return {"error": "Unauthorized", "success": False}

    db = get_supabase_admin()
    try:
        result = db.table("user_profiles").select("*").eq("id", user_id).single().execute()
        profile = result.data or {}
        
        # Also fetch default resume
        resume_result = (db.table("user_resumes")
                        .select("*")
                        .eq("user_id", user_id)
                        .eq("is_default", True)
                        .limit(1)
                        .execute())
        resume = resume_result.data[0] if resume_result.data else None
        
        return {
            "success": True,
            "profile": {
                "full_name": profile.get("full_name", ""),
                "email": profile.get("email", ""),
                "phone": profile.get("phone", ""),
                "linkedin_url": profile.get("linkedin_url", ""),
                "portfolio_url": profile.get("portfolio_url", ""),
                "location": profile.get("location", ""),
                "current_company": profile.get("current_company", ""),
                "cover_letter_default": profile.get("cover_letter_default", ""),
                "resume_url": resume.get("file_url", "") if resume else "",
                "resume_filename": resume.get("file_name", "") if resume else "",
            }
        }
    except Exception as e:
        return {"error": str(e), "success": False}


@router.post("/profile/update")
async def update_apply_profile(
    authorization: str = Header(""),
    full_name: str = Form(""),
    phone: str = Form(""),
    linkedin_url: str = Form(""),
    portfolio_url: str = Form(""),
    location: str = Form(""),
    current_company: str = Form(""),
    cover_letter_default: str = Form(""),
):
    """Update user profile fields used for direct apply."""
    user_id = _get_user_id(authorization)
    if not user_id:
        return {"error": "Unauthorized"}, 401

    db = get_supabase_admin()
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}

    if full_name:
        update_data["full_name"] = full_name
    if phone:
        update_data["phone"] = phone
    if linkedin_url:
        update_data["linkedin_url"] = linkedin_url
    if portfolio_url:
        update_data["portfolio_url"] = portfolio_url
    if location:
        update_data["location"] = location
    if current_company:
        update_data["current_company"] = current_company
    if cover_letter_default:
        update_data["cover_letter_default"] = cover_letter_default

    try:
        db.table("user_profiles").update(update_data).eq("id", user_id).execute()
        return {"success": True}
    except Exception as e:
        return {"error": str(e), "success": False}


@router.post("/resume/upload")
async def upload_resume(
    authorization: str = Header(""),
    resume: UploadFile = File(...),
    is_default: bool = Form(True),
):
    """
    Upload a resume file to Supabase Storage.
    Stores metadata in user_resumes table.
    """
    user_id = _get_user_id(authorization)
    if not user_id:
        return {"error": "Unauthorized"}, 401

    # Validate file
    if not resume.filename:
        return {"error": "No file provided", "success": False}

    allowed_types = {".pdf", ".doc", ".docx"}
    ext = "." + resume.filename.rsplit(".", 1)[-1].lower() if "." in resume.filename else ""
    if ext not in allowed_types:
        return {"error": f"Invalid file type. Allowed: {', '.join(allowed_types)}", "success": False}

    content = await resume.read()
    if len(content) > 5 * 1024 * 1024:  # 5MB limit
        return {"error": "File too large (max 5MB)", "success": False}

    db = get_supabase_admin()

    # Store in Supabase Storage
    import uuid
    file_path = f"resumes/{user_id}/{uuid.uuid4().hex}_{resume.filename}"

    try:
        db.storage.from_("resumes").upload(
            file_path,
            content,
            {"content-type": resume.content_type or "application/pdf"},
        )
        file_url = f"{db.supabase_url}/storage/v1/object/public/resumes/{file_path}"
    except Exception as e:
        # Fallback: store as base64 reference
        file_url = f"storage://{file_path}"
        print(f"[Apply] Storage upload error (non-fatal): {e}")

    # If setting as default, unset other defaults first
    if is_default:
        try:
            db.table("user_resumes").update({"is_default": False}).eq("user_id", user_id).execute()
        except Exception:
            pass

    # Insert resume record
    try:
        db.table("user_resumes").insert({
            "user_id": user_id,
            "file_name": resume.filename,
            "file_url": file_url,
            "file_size": len(content),
            "is_default": is_default,
        }).execute()

        # Also update the profile's resume_url
        if is_default:
            db.table("user_profiles").update({
                "resume_url": file_url,
            }).eq("id", user_id).execute()

        return {
            "success": True,
            "file_url": file_url,
            "file_name": resume.filename,
            "file_size": len(content),
        }
    except Exception as e:
        return {"error": str(e), "success": False}


@router.get("/resumes")
async def get_resumes(authorization: str = Header("")):
    """Get all resumes for the current user."""
    user_id = _get_user_id(authorization)
    if not user_id:
        return {"error": "Unauthorized"}, 401

    db = get_supabase_admin()
    result = (db.table("user_resumes")
              .select("*")
              .eq("user_id", user_id)
              .order("uploaded_at", desc=True)
              .execute())

    return {"resumes": result.data or []}


@router.get("/history")
async def get_apply_history(authorization: str = Header("")):
    """Get all direct-apply application history for the current user."""
    user_id = _get_user_id(authorization)
    if not user_id:
        return {"error": "Unauthorized"}, 401

    db = get_supabase_admin()
    result = (db.table("user_applications")
              .select("*, jobs(*)")
              .eq("user_id", user_id)
              .neq("apply_method", "external")
              .order("applied_at", desc=True)
              .execute())

    return {"applications": result.data or []}
