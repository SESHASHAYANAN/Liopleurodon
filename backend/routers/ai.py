"""
Liopleurodon — AI Router
AI-powered job matching, summarization, resume analysis.
"""

from fastapi import APIRouter, UploadFile, File, Header
from typing import Optional
from services.ai_service import (
    summarize_job, extract_skills, parse_resume,
    match_job_to_resume, generate_job_insights,
)
from services.embedding_service import match_resume_to_jobs
from database import get_supabase_admin

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/summarize")
async def summarize(job_id: str):
    """Summarize a job description."""
    db = get_supabase_admin()
    result = db.table("jobs").select("description").eq("id", job_id).single().execute()
    if not result.data:
        return {"error": "Job not found"}

    summary = await summarize_job(result.data.get("description", ""))
    return {"summary": summary}


@router.post("/extract-skills")
async def extract(job_id: str):
    """Extract skills from a job description."""
    db = get_supabase_admin()
    result = db.table("jobs").select("description").eq("id", job_id).single().execute()
    if not result.data:
        return {"error": "Job not found"}

    skills = await extract_skills(result.data.get("description", ""))
    return skills


@router.post("/parse-resume")
async def parse_resume_file(file: UploadFile = File(...)):
    """Parse an uploaded resume file."""
    content = await file.read()
    text = content.decode("utf-8", errors="ignore")
    parsed = await parse_resume(text)
    return {"resume": parsed}


@router.post("/match-jobs")
async def match_jobs(resume_text: str, limit: int = 20):
    """Find jobs matching resume text using pgvector."""
    jobs = await match_resume_to_jobs(resume_text, limit)
    return {"matched_jobs": jobs}


@router.get("/insights/{job_id}")
async def get_insights(job_id: str):
    """Get AI-generated insights for a job."""
    db = get_supabase_admin()
    result = db.table("jobs").select("*").eq("id", job_id).single().execute()
    if not result.data:
        return {"error": "Job not found"}

    insights = await generate_job_insights(result.data)
    return {"insights": insights}
