"""
Liopleurodon — AI Service
Integrates Groq (LLaMA 3.3 70B), Gemini 1.5 Flash, and OpenRouter for AI features.
Includes PDF resume matching via Groq/OpenRouter.
"""

import httpx
import json
from config import get_settings


async def summarize_job(description: str) -> str:
    """Summarize a job description using Groq LLaMA 3.3 70B."""
    settings = get_settings()
    if not settings.GROQ_API_KEY or not description:
        return ""

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": "You are a job description summarizer. Create a concise 3-5 bullet point summary of the key aspects of this job. Focus on: role responsibilities, required skills, compensation highlights, and unique perks. Keep each bullet under 20 words."},
                        {"role": "user", "content": description[:4000]}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 500,
                },
            )
            data = resp.json()
            return data.get("choices", [{}])[0].get("message", {}).get("content", "")
    except Exception as e:
        print(f"Groq summarize error: {e}")
        return await _fallback_summarize(description)


async def extract_skills(description: str) -> dict:
    """Extract required and preferred skills from job description using Groq."""
    settings = get_settings()
    if not settings.GROQ_API_KEY or not description:
        return {"required": [], "preferred": []}

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": 'Extract skills from this job description. Return JSON: {"required": ["skill1", "skill2"], "preferred": ["skill3"]}. Only include technical skills, tools, and frameworks.'},
                        {"role": "user", "content": description[:4000]}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 500,
                    "response_format": {"type": "json_object"},
                },
            )
            data = resp.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "{}")
            return json.loads(content)
    except Exception as e:
        print(f"Groq skills extraction error: {e}")
        return {"required": [], "preferred": []}


async def parse_resume(resume_text: str) -> dict:
    """Parse resume text using Gemini 1.5 Flash."""
    settings = get_settings()
    if not settings.GEMINI_API_KEY or not resume_text:
        return {}

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}",
                json={
                    "contents": [{"parts": [{"text": f"""Parse this resume and extract structured data. Return JSON with:
{{"name": "", "email": "", "skills": [], "experience_years": 0, "experience_level": "", "education": [], "work_history": [{{"company": "", "title": "", "duration": ""}}], "summary": ""}}

Resume:
{resume_text[:6000]}"""}]}],
                    "generationConfig": {"temperature": 0.1, "maxOutputTokens": 1000},
                },
            )
            data = resp.json()
            text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "{}")
            # Extract JSON from potential markdown code block
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            return json.loads(text.strip())
    except Exception as e:
        print(f"Gemini resume parse error: {e}")
        return {}


async def match_job_to_resume(job_description: str, resume_data: dict) -> dict:
    """Score job-candidate fit using Gemini."""
    settings = get_settings()
    if not settings.GEMINI_API_KEY:
        return {"score": 0, "reasoning": "AI matching unavailable"}

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}",
                json={
                    "contents": [{"parts": [{"text": f"""Score how well this candidate matches this job (0-100). Return JSON:
{{"score": 85, "reasoning": "brief explanation", "matching_skills": [], "missing_skills": []}}

Job Description:
{job_description[:3000]}

Candidate Profile:
{json.dumps(resume_data)[:3000]}"""}]}],
                    "generationConfig": {"temperature": 0.2, "maxOutputTokens": 500},
                },
            )
            data = resp.json()
            text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "{}")
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            return json.loads(text.strip())
    except Exception as e:
        print(f"Gemini matching error: {e}")
        return {"score": 0, "reasoning": str(e)}


async def match_resume_to_jobs_ai(resume_text: str, parsed_resume: dict, jobs: list, limit: int = 20) -> list:
    """
    Match resume against jobs using Groq AI (primary) + OpenRouter (fallback).
    Sends batches of jobs for scoring efficiency.
    Returns list of jobs with match scores.
    """
    settings = get_settings()

    # Build compact resume summary for prompts
    resume_summary = json.dumps({
        "skills": parsed_resume.get("skills", []),
        "experience_years": parsed_resume.get("experience_years", 0),
        "experience_level": parsed_resume.get("experience_level", ""),
        "work_history": [
            {"title": w.get("title", ""), "company": w.get("company", "")}
            for w in parsed_resume.get("work_history", [])[:5]
        ],
        "summary": parsed_resume.get("summary", ""),
    })

    # Build compact job list for scoring
    job_summaries = []
    for i, job in enumerate(jobs[:100]):  # Score up to 100 jobs
        job_summaries.append({
            "idx": i,
            "title": job.get("title", ""),
            "company": job.get("company_name", ""),
            "skills": (job.get("tech_stack") or [])[:5],
            "level": job.get("experience_level", ""),
            "desc": (job.get("description") or "")[:200],
        })

    # Score in batches of 20
    all_scores = []
    batch_size = 20
    for batch_start in range(0, len(job_summaries), batch_size):
        batch = job_summaries[batch_start:batch_start + batch_size]
        scores = await _score_batch_groq(resume_summary, resume_text[:2000], batch, settings)
        if not scores:
            scores = await _score_batch_openrouter(resume_summary, resume_text[:2000], batch, settings)
        all_scores.extend(scores)

    # Map scores back to full job data
    scored_jobs = []
    for score_entry in all_scores:
        idx = score_entry.get("idx", -1)
        if 0 <= idx < len(jobs):
            job = dict(jobs[idx])  # copy
            job["match_score"] = score_entry.get("score", 0)
            job["match_reasoning"] = score_entry.get("reasoning", "")
            job["matching_skills"] = score_entry.get("matching_skills", [])
            job["missing_skills"] = score_entry.get("missing_skills", [])
            scored_jobs.append(job)

    # Sort by score descending and return top N
    scored_jobs.sort(key=lambda x: x.get("match_score", 0), reverse=True)
    return scored_jobs[:limit]


async def _score_batch_groq(resume_summary: str, resume_text: str, batch: list, settings) -> list:
    """Score a batch of jobs using Groq."""
    if not settings.GROQ_API_KEY:
        return []

    prompt = f"""Score how well this candidate matches each job (0-100).

CANDIDATE PROFILE:
{resume_summary}

RAW RESUME EXCERPT:
{resume_text[:1500]}

JOBS TO SCORE:
{json.dumps(batch)}

Return a JSON array with one object per job:
[{{"idx": 0, "score": 85, "reasoning": "brief explanation", "matching_skills": ["skill1"], "missing_skills": ["skill2"]}}]

Rules:
- Score 90-100: Perfect match (skills + experience level match)
- Score 70-89: Strong match (most skills match)
- Score 50-69: Partial match (some relevant skills)
- Score 0-49: Weak match
- Consider experience level, skills overlap, and domain relevance"""

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": "You are a job matching AI. Score candidate-job fit. Return ONLY valid JSON array."},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.2,
                    "max_tokens": 3000,
                    "response_format": {"type": "json_object"},
                },
            )
            data = resp.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "[]")
            parsed = json.loads(content)
            # Handle both {scores: [...]} and [...] formats
            if isinstance(parsed, dict):
                return parsed.get("scores", parsed.get("jobs", parsed.get("results", [])))
            return parsed if isinstance(parsed, list) else []
    except Exception as e:
        print(f"Groq batch scoring error: {e}")
        return []


async def _score_batch_openrouter(resume_summary: str, resume_text: str, batch: list, settings) -> list:
    """Fallback: Score a batch of jobs using OpenRouter."""
    if not settings.OPENROUTER_API_KEY:
        return []

    prompt = f"""Score how well this candidate matches each job (0-100).

CANDIDATE:
{resume_summary}

RESUME EXCERPT:
{resume_text[:1000]}

JOBS:
{json.dumps(batch)}

Return a JSON array:
[{{"idx": 0, "score": 85, "reasoning": "brief explanation", "matching_skills": ["skill1"], "missing_skills": ["skill2"]}}]"""

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                    "HTTP-Referer": "https://liopleurodon.app",
                },
                json={
                    "model": "mistralai/mistral-7b-instruct:free",
                    "messages": [
                        {"role": "system", "content": "You are a job matching AI. Return ONLY valid JSON array."},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.2,
                    "max_tokens": 3000,
                },
            )
            data = resp.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "[]")
            # Extract JSON from potential markdown
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            parsed = json.loads(content.strip())
            if isinstance(parsed, dict):
                return parsed.get("scores", parsed.get("jobs", parsed.get("results", [])))
            return parsed if isinstance(parsed, list) else []
    except Exception as e:
        print(f"OpenRouter batch scoring error: {e}")
        return []


async def generate_job_insights(job: dict) -> str:
    """Generate job insights using OpenRouter (Mistral/DeepSeek)."""
    settings = get_settings()
    if not settings.OPENROUTER_API_KEY:
        return ""

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                    "HTTP-Referer": "https://liopleurodon.app",
                },
                json={
                    "model": "mistralai/mistral-7b-instruct:free",
                    "messages": [
                        {"role": "system", "content": "You are a career advisor. Provide brief, actionable insights about this job opportunity in 3-4 bullet points."},
                        {"role": "user", "content": f"Job: {job.get('title')} at {job.get('company_name')}\nDescription: {str(job.get('description', ''))[:2000]}"}
                    ],
                    "temperature": 0.5,
                    "max_tokens": 400,
                },
            )
            data = resp.json()
            return data.get("choices", [{}])[0].get("message", {}).get("content", "")
    except Exception as e:
        print(f"OpenRouter insights error: {e}")
        return ""


async def _fallback_summarize(description: str) -> str:
    """Fallback summarization using OpenRouter."""
    settings = get_settings()
    if not settings.OPENROUTER_API_KEY:
        return ""

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                    "HTTP-Referer": "https://liopleurodon.app",
                },
                json={
                    "model": "mistralai/mistral-7b-instruct:free",
                    "messages": [
                        {"role": "system", "content": "Summarize this job description in 3-5 bullet points. Keep each bullet under 20 words."},
                        {"role": "user", "content": description[:3000]}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 400,
                },
            )
            data = resp.json()
            return data.get("choices", [{}])[0].get("message", {}).get("content", "")
    except Exception as e:
        print(f"OpenRouter fallback error: {e}")
        return ""
