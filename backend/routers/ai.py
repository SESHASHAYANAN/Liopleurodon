"""
Liopleurodon — AI Router
AI-powered job matching, summarization, resume analysis.
Supports PDF resume upload for AI matching via Groq/OpenRouter.
Includes keyword-based quick matching with quality ratings.
"""

from fastapi import APIRouter, UploadFile, File, Header, Form
from typing import Optional, List
from services.ai_service import (
    summarize_job, extract_skills, parse_resume,
    match_job_to_resume, generate_job_insights,
    match_resume_to_jobs_ai,
)
from pydantic import BaseModel
from services.embedding_service import match_resume_to_jobs
from database import get_supabase_admin
from config import get_settings
from datetime import datetime, timezone, timedelta
import io

class MatchJobsRequest(BaseModel):
    resume_text: str
    limit: int = 20

class KeywordMatchRequest(BaseModel):
    keywords: List[str]
    experience_level: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[str] = None
    remote_type: Optional[str] = None
    limit: int = 30

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


# ═══════════════════════════════════════════════════════════════════
# KEYWORD-BASED AI MATCHING + QUALITY RATING
# ═══════════════════════════════════════════════════════════════════

def _rate_job_quality(job: dict) -> dict:
    """Rate a job's quality (1-5 stars) based on completeness and signals."""
    score = 0
    reasons = []

    # Completeness signals
    if job.get("salary_min") or job.get("salary_max"):
        score += 1
        reasons.append("Salary disclosed")
    if job.get("company_name") and job["company_name"] not in ("", "Indian Company", "Indian Startup", "AI Company"):
        score += 0.5
        reasons.append("Named company")
    if job.get("tech_stack") and len(job.get("tech_stack", [])) >= 2:
        score += 1
        reasons.append("Tech stack listed")
    if job.get("description") and len(str(job.get("description", ""))) > 100:
        score += 0.5
        reasons.append("Detailed description")
    if job.get("apply_url") and "http" in str(job.get("apply_url", "")):
        score += 0.5
        reasons.append("Direct apply link")

    # Trust signals
    if job.get("company_type") == "vc_backed":
        score += 0.5
        reasons.append("VC-backed")
    if job.get("visa_sponsorship"):
        score += 0.3
        reasons.append("Visa sponsorship")
    sources = job.get("source_platforms", [])
    if len(sources) >= 2:
        score += 0.5
        reasons.append("Multi-source verified")

    # Recency bonus
    posted = job.get("posted_date", "")
    if posted:
        try:
            now = datetime.now(timezone.utc)
            posted_dt = datetime.fromisoformat(posted.replace("Z", "+00:00"))
            days_old = (now - posted_dt).days
            if days_old <= 1:
                score += 1
                reasons.append("Posted today")
            elif days_old <= 3:
                score += 0.7
                reasons.append("Posted this week")
            elif days_old <= 7:
                score += 0.3
                reasons.append("Recent")
        except Exception:
            pass

    stars = min(5, max(1, round(score)))
    return {"stars": stars, "reasons": reasons, "raw_score": round(score, 1)}


def _score_job_by_keywords(job: dict, keywords: list, filters: dict) -> dict:
    """Score a job against user keywords with relevance + recency + quality."""
    title = (job.get("title") or "").lower()
    desc = (job.get("description") or "").lower()
    company = (job.get("company_name") or "").lower()
    tech = [t.lower() for t in (job.get("tech_stack") or [])]
    full_text = f"{title} {desc} {company} {' '.join(tech)}"

    # Keyword matching score (0-50)
    kw_lower = [k.lower().strip() for k in keywords if k.strip()]
    matched_kw = []
    for kw in kw_lower:
        if kw in full_text:
            matched_kw.append(kw)
            # Bonus if keyword is in title (more relevant)
            if kw in title:
                matched_kw.append(kw)  # double count for title hits

    kw_score = min(50, len(matched_kw) * (50 // max(len(kw_lower), 1)))

    # Recency score (0-25)
    recency_score = 0
    posted = job.get("posted_date", "")
    days_old = 999
    is_new = False
    if posted:
        try:
            now = datetime.now(timezone.utc)
            posted_dt = datetime.fromisoformat(posted.replace("Z", "+00:00"))
            days_old = (now - posted_dt).days
            if days_old <= 1:
                recency_score = 25
                is_new = True
            elif days_old <= 3:
                recency_score = 20
                is_new = True
            elif days_old <= 7:
                recency_score = 15
            elif days_old <= 14:
                recency_score = 8
            else:
                recency_score = 2
        except Exception:
            recency_score = 5

    # Quality score (0-15)
    quality = _rate_job_quality(job)
    quality_score = quality["stars"] * 3

    # Filter bonus (0-10)
    filter_score = 0
    if filters.get("experience_level") and job.get("experience_level") == filters["experience_level"]:
        filter_score += 5
    if filters.get("remote_type") and job.get("remote_type") == filters["remote_type"]:
        filter_score += 3
    if filters.get("job_type") and job.get("job_type") == filters["job_type"]:
        filter_score += 2

    total = kw_score + recency_score + quality_score + filter_score

    # Tier assignment
    if total >= 70:
        tier = "perfect"
    elif total >= 50:
        tier = "strong"
    elif total >= 30:
        tier = "good"
    else:
        tier = "weak"

    unique_matched = list(set(kw_lower) & set(word for word in full_text.split() if word in set(kw_lower)))
    if not unique_matched:
        unique_matched = [kw for kw in kw_lower if kw in full_text]

    return {
        "match_score": min(100, total),
        "keyword_score": kw_score,
        "recency_score": recency_score,
        "quality_score": quality_score,
        "match_tier": tier,
        "matched_keywords": list(set(unique_matched)),
        "quality_rating": quality,
        "is_new": is_new,
        "days_old": days_old,
    }


@router.post("/keyword-match")
async def keyword_match_jobs(req: KeywordMatchRequest):
    """
    Find and rank jobs by keywords with quality ratings.
    Returns jobs scored by keyword relevance + recency + quality.
    New jobs (posted in last 3 days) get boosted to the top.
    """
    if not req.keywords or len(req.keywords) == 0:
        return {"error": "Please provide at least one keyword", "matched_jobs": []}

    db = get_supabase_admin()
    now = datetime.now(timezone.utc)
    cutoff = (now - timedelta(days=21)).isoformat()

    # Build query with optional filters
    query = (db.table("jobs")
        .select("id, title, company_name, company_logo_url, location_city, location_country, "
                "remote_type, salary_min, salary_max, salary_currency, experience_level, "
                "job_type, description, tech_stack, apply_url, visa_sponsorship, "
                "relocation_support, source_platforms, posted_date, is_featured, "
                "vc_backer, company_type")
        .eq("is_active", True)
        .gte("posted_date", cutoff)
        .order("posted_date", desc=True)
        .limit(500))

    # Apply hard filters
    if req.experience_level:
        query = query.eq("experience_level", req.experience_level)
    if req.location:
        query = query.or_(f"location_city.ilike.%{req.location}%,location_country.ilike.%{req.location}%")
    if req.job_type:
        query = query.eq("job_type", req.job_type)
    if req.remote_type:
        query = query.eq("remote_type", req.remote_type)

    result = query.execute()
    all_jobs = result.data or []

    print(f"[KeywordMatch] {len(req.keywords)} keywords: {req.keywords}")
    print(f"[KeywordMatch] Fetched {len(all_jobs)} jobs to score")

    # Score and rank
    filters = {
        "experience_level": req.experience_level,
        "remote_type": req.remote_type,
        "job_type": req.job_type,
    }

    scored_jobs = []
    for job in all_jobs:
        scoring = _score_job_by_keywords(job, req.keywords, filters)
        if scoring["match_score"] >= 15:  # minimum relevance threshold
            job_with_score = {**job, **scoring}
            scored_jobs.append(job_with_score)

    # Sort: new jobs first within the same tier, then by score
    scored_jobs.sort(key=lambda x: (
        x["match_score"],
        1 if x["is_new"] else 0,
        -x["days_old"],
    ), reverse=True)

    results = scored_jobs[:req.limit]

    # Stats
    tier_counts = {}
    new_count = 0
    for r in results:
        t = r.get("match_tier", "weak")
        tier_counts[t] = tier_counts.get(t, 0) + 1
        if r.get("is_new"):
            new_count += 1

    print(f"[KeywordMatch] Results: {len(results)} jobs, {new_count} new, tiers: {tier_counts}")

    # Generate AI recommendation if Groq is available
    recommendation = ""
    settings = get_settings()
    if settings.GROQ_API_KEY and results:
        try:
            top_titles = [r["title"] for r in results[:5]]
            import httpx
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
                    json={
                        "model": "llama-3.3-70b-versatile",
                        "messages": [
                            {"role": "system", "content": "You are a career advisor. Give a brief 2-sentence recommendation based on the user's keywords and top matched jobs. Be encouraging and specific."},
                            {"role": "user", "content": f"Keywords: {', '.join(req.keywords)}\nTop matches: {', '.join(top_titles)}"}
                        ],
                        "temperature": 0.5,
                        "max_tokens": 150,
                    },
                )
                data = resp.json()
                recommendation = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        except Exception as e:
            print(f"[KeywordMatch] AI recommendation error: {e}")

    return {
        "matched_jobs": results,
        "total_analyzed": len(all_jobs),
        "total_matched": len(scored_jobs),
        "new_jobs_count": new_count,
        "tier_counts": tier_counts,
        "keywords_used": req.keywords,
        "ai_recommendation": recommendation,
    }


@router.get("/trending-keywords")
async def get_trending_keywords():
    """Get trending skills/keywords from recent job postings."""
    db = get_supabase_admin()
    now = datetime.now(timezone.utc)
    cutoff = (now - timedelta(days=7)).isoformat()

    try:
        result = (db.table("jobs")
            .select("tech_stack, title")
            .eq("is_active", True)
            .gte("posted_date", cutoff)
            .limit(200)
            .execute())

        keyword_freq = {}
        for job in (result.data or []):
            for tech in (job.get("tech_stack") or []):
                t = tech.lower().strip()
                if t and len(t) > 1:
                    keyword_freq[t] = keyword_freq.get(t, 0) + 1
            # Also extract from titles
            title = (job.get("title") or "").lower()
            for word in ["python", "react", "node", "java", "aws", "docker", "kubernetes",
                         "typescript", "golang", "rust", "ai", "ml", "data", "cloud",
                         "devops", "fullstack", "frontend", "backend", "mobile"]:
                if word in title:
                    keyword_freq[word] = keyword_freq.get(word, 0) + 1

        sorted_kw = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)[:20]
        return {"trending": [{"keyword": k, "count": v} for k, v in sorted_kw]}
    except Exception as e:
        return {"trending": [], "error": str(e)}

