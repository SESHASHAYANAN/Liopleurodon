"""
Liopleurodon — AI Service
Integrates Groq (LLaMA 3.3 70B), Gemini 1.5 Flash, and OpenRouter for AI features.
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
