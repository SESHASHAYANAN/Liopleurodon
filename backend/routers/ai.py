"""
Liopleurodon — AI Router
AI-powered job matching, summarization, resume analysis.
Supports PDF resume upload for AI matching via Groq/OpenRouter.
"""

from fastapi import APIRouter, UploadFile, File, Header, Form
from typing import Optional
from services.ai_service import (
    summarize_job, extract_skills, parse_resume,
    match_job_to_resume, generate_job_insights,
    match_resume_to_jobs_ai,
)
from pydantic import BaseModel
from services.embedding_service import match_resume_to_jobs
from database import get_supabase_admin
import io

class MatchJobsRequest(BaseModel):
    resume_text: str
    limit: int = 20

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
    """Parse an uploaded resume file (text or PDF)."""
    content = await file.read()

    # Check if it's a PDF
    if file.filename and file.filename.lower().endswith('.pdf'):
        text = _extract_pdf_text(content)
    else:
        text = content.decode("utf-8", errors="ignore")

    parsed = await parse_resume(text)
    return {"resume": parsed, "raw_text": text[:2000]}


@router.post("/match-jobs")
async def match_jobs(req: MatchJobsRequest):
    """Find jobs matching resume text using pgvector."""
    jobs = await match_resume_to_jobs(req.resume_text, req.limit)
    return {"matched_jobs": jobs}


@router.post("/match-resume-pdf")
async def match_resume_pdf(file: UploadFile = File(...), limit: int = Form(20)):
    """
    Upload a PDF resume and get AI-matched jobs.
    Uses Groq (primary) and OpenRouter (fallback) for matching.
    """
    try:
        # 1. Read file content
        content = await file.read()
        filename = file.filename or "resume.pdf"
        print(f"[Match] Received file: {filename} ({len(content)} bytes)")

        # 2. Extract text from PDF
        if filename.lower().endswith('.pdf'):
            resume_text = _extract_pdf_text(content)
        else:
            resume_text = content.decode("utf-8", errors="ignore")

        if not resume_text or len(resume_text.strip()) < 50:
            return {"error": "Could not extract enough text from the uploaded file. Please try a different file.", "matched_jobs": []}

        print(f"[Match] Extracted {len(resume_text)} chars from resume")

        # 3. Parse resume into structured profile
        parsed_resume = await parse_resume(resume_text)
        if not isinstance(parsed_resume, dict):
            print(f"[Match] Warning: parsed_resume is {type(parsed_resume).__name__}, converting to empty dict")
            parsed_resume = {}
        print(f"[Match] Resume parsed: {len(parsed_resume.get('skills', []))} skills, level={parsed_resume.get('experience_level', 'unknown')}")

        # 4. Fetch active & recent jobs from database (last 30 days only)
        from datetime import datetime, timezone, timedelta
        cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        db = get_supabase_admin()
        jobs_result = (db.table("jobs")
                       .select("id, title, company_name, company_logo_url, location_city, location_country, "
                               "remote_type, salary_min, salary_max, salary_currency, experience_level, "
                               "job_type, description, tech_stack, apply_url, visa_sponsorship, "
                               "relocation_support, source_platforms, posted_date, is_featured, vc_backer, company_type")
                       .eq("is_active", True)
                       .gte("posted_date", cutoff)
                       .order("posted_date", desc=True)
                       .limit(200)
                       .execute())

        all_jobs = jobs_result.data or []
        print(f"[Match] Fetched {len(all_jobs)} active jobs (posted after {cutoff[:10]})")

        if not all_jobs:
            return {
                "parsed_resume": parsed_resume,
                "resume_preview": resume_text[:1000],
                "matched_jobs": [],
                "message": "No active jobs found to match against."
            }

        # 5. AI matching using Groq/OpenRouter
        matched = await match_resume_to_jobs_ai(resume_text, parsed_resume, all_jobs, limit)
        print(f"[Match] AI matching complete: {len(matched)} matched jobs returned")

        return {
            "parsed_resume": parsed_resume,
            "resume_preview": resume_text[:1000],
            "matched_jobs": matched,
            "total_jobs_analyzed": len(all_jobs),
            "filename": filename,
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[Match] Fatal error: {e}")
        return {
            "error": f"Resume matching failed: {str(e)}",
            "matched_jobs": [],
            "parsed_resume": {},
        }


@router.get("/insights/{job_id}")
async def get_insights(job_id: str):
    """Get AI-generated insights for a job."""
    db = get_supabase_admin()
    result = db.table("jobs").select("*").eq("id", job_id).single().execute()
    if not result.data:
        return {"error": "Job not found"}

    insights = await generate_job_insights(result.data)
    return {"insights": insights}


def _extract_pdf_text(pdf_bytes: bytes) -> str:
    """Extract text from PDF bytes using PyPDF2."""
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(io.BytesIO(pdf_bytes))
        text_parts = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        return "\n".join(text_parts)
    except ImportError:
        # PyPDF2 not installed — try basic text extraction
        try:
            return pdf_bytes.decode("utf-8", errors="ignore")
        except Exception:
            return ""
    except Exception as e:
        print(f"PDF extraction error: {e}")
        return ""
