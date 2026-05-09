"""
Liopleurodon — AI Service
Integrates Groq (LLaMA 3.3 70B), Gemini 1.5 Flash, and OpenRouter for AI features.
Includes deterministic algorithmic resume-job matching engine.
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
    """Parse resume text using Gemini 1.5 Flash, with Groq fallback."""
    settings = get_settings()
    if not resume_text:
        return {}

    # Try Gemini first
    if settings.GEMINI_API_KEY:
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
                parsed = json.loads(text.strip())
                if parsed and parsed.get("skills"):
                    print(f"[Resume] Parsed via Gemini: {len(parsed.get('skills', []))} skills found")
                    return parsed
        except Exception as e:
            print(f"Gemini resume parse error: {e}")

    # Fallback to Groq
    if settings.GROQ_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
                    json={
                        "model": "llama-3.3-70b-versatile",
                        "messages": [
                            {"role": "system", "content": 'You parse resumes into structured JSON. Return ONLY a JSON object: {"name": "", "email": "", "skills": ["skill1"], "experience_years": 0, "experience_level": "junior|mid|senior|staff", "education": ["degree"], "work_history": [{"company": "", "title": "", "duration": ""}], "summary": "brief summary"}'},
                            {"role": "user", "content": f"Parse this resume:\n\n{resume_text[:5000]}"},
                        ],
                        "temperature": 0.1,
                        "max_tokens": 1500,
                        "response_format": {"type": "json_object"},
                    },
                )
                data = resp.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "{}")
                parsed = json.loads(content)
                print(f"[Resume] Parsed via Groq: {len(parsed.get('skills', []))} skills found")
                return parsed
        except Exception as e:
            print(f"Groq resume parse error: {e}")

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


# ═══════════════════════════════════════════════════════════════════
# DETERMINISTIC RESUME ↔ JOB MATCHING ENGINE
# No external API calls — instant, reliable, resume-specific results
# ═══════════════════════════════════════════════════════════════════

_KNOWN_TECH = {
    "python","java","javascript","typescript","c++","c#","go","golang","rust","ruby",
    "swift","kotlin","scala","php","perl","r","matlab","lua","dart","elixir",
    "react","angular","vue","svelte","next.js","nuxt","gatsby","remix",
    "node.js","node","express","fastapi","django","flask","spring","rails",
    "html","css","sass","tailwind","bootstrap",
    "sql","mysql","postgresql","postgres","mongodb","redis","elasticsearch",
    "dynamodb","cassandra","sqlite","firebase","supabase",
    "aws","azure","gcp","docker","kubernetes","terraform","ansible",
    "jenkins","ci/cd","github actions","gitlab ci",
    "git","linux","bash","shell",
    "tensorflow","pytorch","scikit-learn","pandas","numpy","spark","airflow",
    "machine learning","deep learning","nlp","computer vision","data science",
    "figma","sketch","adobe xd",
    "graphql","rest","api","grpc","websocket",
    "agile","scrum","jira","confluence",
    "selenium","cypress","jest","mocha","pytest",
    "solidity","ethereum","blockchain","web3",
    "opencv","ros","cuda",
}


def _extract_skills_from_text(text: str) -> set:
    """Extract tech skills from raw text by matching against known skills."""
    text_lower = text.lower()
    found = set()
    for skill in _KNOWN_TECH:
        if skill in text_lower:
            found.add(skill)
    return found


def _detect_level(resume_text: str, parsed: dict) -> str:
    """Detect candidate experience level."""
    level = str(parsed.get("experience_level", "")).lower().strip()
    if level in ("intern", "junior", "mid", "senior", "staff"):
        return level

    text = resume_text.lower()
    years = parsed.get("experience_years", 0)
    if not isinstance(years, (int, float)):
        try:
            years = int(years)
        except (ValueError, TypeError):
            years = 0

    if any(w in text for w in ["intern", "fresher", "student", "graduating", "trainee"]):
        return "intern"
    if any(w in text for w in ["junior", "entry level", "entry-level", "associate", "graduate"]):
        return "junior"
    if any(w in text for w in ["senior", "sr.", "lead", "principal", "architect"]):
        return "senior"
    if any(w in text for w in ["staff", "director", "vp ", "head of", "cto"]):
        return "staff"

    if years <= 1:
        return "junior"
    elif years <= 4:
        return "mid"
    elif years <= 8:
        return "senior"
    return "staff"


def _detect_domain(skills: set, text: str) -> str:
    """Detect primary domain from skills and text."""
    text_lower = text.lower()
    domains = {
        "frontend": {"react", "angular", "vue", "svelte", "html", "css", "next.js", "tailwind", "frontend"},
        "backend": {"node.js", "express", "django", "flask", "fastapi", "spring", "rails", "backend"},
        "fullstack": {"fullstack", "full-stack", "full stack"},
        "data": {"pandas", "numpy", "spark", "airflow", "data science", "machine learning", "tensorflow", "pytorch"},
        "devops": {"docker", "kubernetes", "terraform", "ci/cd", "devops", "sre"},
        "mobile": {"swift", "kotlin", "react native", "flutter", "ios", "android"},
        "security": {"security", "penetration", "cybersecurity", "siem"},
        "design": {"figma", "sketch", "ux", "ui design", "prototyping"},
    }
    best_domain = "general"
    best_score = 0
    for domain, keywords in domains.items():
        score = sum(1 for k in keywords if k in text_lower or k in skills)
        if score > best_score:
            best_score = score
            best_domain = domain
    return best_domain if best_score >= 2 else "general"


_LEVEL_ALLOWED = {
    "intern": {"intern", "junior", "entry", "entry-level", "fresher", "trainee", ""},
    "junior": {"intern", "junior", "entry", "entry-level", "mid", "associate", ""},
    "mid":    {"junior", "mid", "senior", ""},
    "senior": {"mid", "senior", "lead", "staff", "principal", ""},
    "staff":  {"senior", "lead", "staff", "principal", "director", ""},
}

_SENIOR_TITLE_WORDS = [
    "senior", "sr.", "sr ", "lead", "principal", "staff", "director",
    "head ", "vp ", "architect", "manager", "expert", "distinguished",
]

_NON_TECH_TITLES = [
    "sales", "marketing", "hr ", "human resources", "recruiter", "accountant",
    "nurse", "teacher", "driver", "cook", "janitor", "cashier", "legal",
    "receptionist", "secretary", "warehouse", "customer service", "retail",
]

_LEVEL_BONUS = {
    "intern": {"intern": 20, "junior": 10, "mid": -5,  "senior": -30, "staff": -40, "lead": -30, "": 0},
    "junior": {"intern": 5,  "junior": 20, "mid": 5,   "senior": -25, "staff": -35, "lead": -25, "": 0},
    "mid":    {"intern": -10,"junior": 5,  "mid": 20,  "senior": 5,   "staff": -10, "lead": 0,   "": 0},
    "senior": {"intern": -25,"junior": -15,"mid": 5,   "senior": 20,  "staff": 10,  "lead": 15,  "": 0},
    "staff":  {"intern": -30,"junior": -25,"mid": -10,  "senior": 10,  "staff": 20,  "lead": 15,  "": 0},
}


async def match_resume_to_jobs_ai(resume_text: str, parsed_resume: dict, jobs: list, limit: int = 20) -> list:
    """
    Deterministic multi-signal job matching — no external API calls for scoring.

    Scoring formula (0-100):
      Skill overlap:        0-40 pts  (% of job's tech stack matched)
      Title relevance:      0-20 pts  (resume titles vs job title words)
      Level compatibility:  0-20 pts  (intern↔intern = 20, junior↔senior = 0)
      Domain match:         0-10 pts  (frontend↔frontend = 10)
      Description keywords: 0-10 pts  (candidate skills in job description)

    Hard filters remove incompatible jobs before scoring.
    """
    if not isinstance(parsed_resume, dict):
        parsed_resume = {}

    # ── 1. Build candidate profile from BOTH parsed data AND raw text ──
    parsed_skills = set()
    raw_skills = parsed_resume.get("skills", [])
    if isinstance(raw_skills, list):
        parsed_skills = {s.lower().strip() for s in raw_skills if isinstance(s, str)}
    text_skills = _extract_skills_from_text(resume_text)
    candidate_skills = parsed_skills | text_skills

    candidate_level = _detect_level(resume_text, parsed_resume)
    candidate_domain = _detect_domain(candidate_skills, resume_text)
    allowed_levels = _LEVEL_ALLOWED.get(candidate_level, {"junior", "mid", "senior", ""})
    is_tech = len(candidate_skills) >= 3

    resume_lower = resume_text.lower()
    resume_words = set(resume_lower.split())

    # Extract past job title words for title matching
    past_title_words = set()
    for w in (parsed_resume.get("work_history") or []):
        if isinstance(w, dict):
            for word in str(w.get("title", "")).lower().split():
                if len(word) > 3:
                    past_title_words.add(word)

    print(f"[Match] Profile: {len(candidate_skills)} skills, level={candidate_level}, domain={candidate_domain}")
    print(f"[Match] Skills: {sorted(candidate_skills)[:12]}...")

    # ── 2. Score every job ─────────────────────────────────────────────
    scored = []
    skipped = 0

    for job in jobs:
        job_title = (job.get("title") or "").lower()
        job_level = (job.get("experience_level") or "").lower().strip()
        job_desc = (job.get("description") or "").lower()
        job_tech = {t.lower() for t in (job.get("tech_stack") or [])}

        # ── Hard filters ──────────────────────────────────────────
        if job_level and job_level not in allowed_levels:
            skipped += 1
            continue

        if candidate_level in ("intern", "junior"):
            if any(w in job_title for w in _SENIOR_TITLE_WORDS):
                skipped += 1
                continue
            if any(s in job_desc for s in ["5+ years", "7+ years", "8+ years", "10+ years"]):
                skipped += 1
                continue

        if is_tech and any(nt in job_title for nt in _NON_TECH_TITLES):
            skipped += 1
            continue

        # ── Signal 1: Skill overlap (0-40 pts) ───────────────────
        if job_tech:
            matched = candidate_skills & job_tech
            missing = job_tech - candidate_skills
            overlap = len(matched) / len(job_tech) if job_tech else 0
            skill_score = round(overlap * 40)
        else:
            matched = {s for s in candidate_skills if s in job_desc}
            missing = set()
            skill_score = min(20, len(matched) * 4)

        # ── Signal 2: Title relevance (0-20 pts) ────────────────
        title_score = 0
        job_words = {w for w in job_title.split() if len(w) > 3}
        title_score += min(10, len(past_title_words & job_words) * 5)
        title_score += min(10, sum(2 for w in job_words if w in resume_words))

        # ── Signal 3: Level compatibility (0-20 pts) ────────────
        raw_bonus = _LEVEL_BONUS.get(candidate_level, {}).get(job_level, 0)
        level_score = max(0, min(20, raw_bonus + 10))

        # ── Signal 4: Domain match (0-10 pts) ───────────────────
        job_domain = _detect_domain(job_tech, job_title + " " + job_desc[:200])
        if job_domain == candidate_domain:
            domain_score = 10
        elif job_domain == "general" or candidate_domain == "general":
            domain_score = 5
        else:
            domain_score = 0

        # ── Signal 5: Description keywords (0-10 pts) ───────────
        desc_hits = sum(1 for s in candidate_skills if s in job_desc)
        desc_score = min(10, desc_hits * 2)

        # ── Total ────────────────────────────────────────────────
        total = skill_score + title_score + level_score + domain_score + desc_score

        # Build reasoning
        parts = []
        if matched:
            parts.append(f"{len(matched)} matching skills")
        if raw_bonus >= 10:
            parts.append("great level fit")
        if domain_score >= 8:
            parts.append(f"{candidate_domain} domain")
        if not parts:
            parts.append("some relevance found")
        reasoning = " · ".join(parts)

        # Tier
        if total >= 70:
            tier = "perfect"
        elif total >= 50:
            tier = "strong"
        elif total >= 30:
            tier = "good"
        else:
            tier = "weak"

        scored.append({
            "job": job,
            "score": total,
            "matched": sorted(matched)[:10],
            "missing": sorted(missing)[:5] if isinstance(missing, set) else [],
            "reasoning": reasoning,
            "tier": tier,
            "level_match": job_level == candidate_level,
        })

    # ── 3. Sort and return ─────────────────────────────────────────────
    scored.sort(key=lambda x: (x["score"], x["job"].get("posted_date", "")), reverse=True)

    results = []
    for entry in scored[:limit]:
        job = dict(entry["job"])
        job["match_score"] = entry["score"]
        job["match_reasoning"] = entry["reasoning"]
        job["matching_skills"] = entry["matched"]
        job["missing_skills"] = entry["missing"]
        job["match_tier"] = entry["tier"]
        job["level_match"] = entry["level_match"]
        results.append(job)

    tier_counts = {}
    for r in results:
        t = r.get("match_tier", "weak")
        tier_counts[t] = tier_counts.get(t, 0) + 1

    print(f"[Match] Filtered: {len(jobs)} → {len(scored)} (skipped {skipped})")
    print(f"[Match] Results: {len(results)} — {tier_counts}")
    if results:
        print(f"[Match] Top 3: {[(r.get('title','?'), r['match_score']) for r in results[:3]]}")

    return results


# ═══════════════════════════════════════════════════════════════════
# OTHER AI SERVICES (insights, summarization)
# ═══════════════════════════════════════════════════════════════════

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
