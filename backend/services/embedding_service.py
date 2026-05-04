"""
Liopleurodon — Embedding Service
Generate embeddings for pgvector semantic search using Gemini.
"""

import httpx
from config import get_settings


async def generate_embedding(text: str) -> list[float] | None:
    """Generate text embedding using Gemini embedding model."""
    settings = get_settings()
    if not settings.GEMINI_API_KEY or not text:
        return None

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={settings.GEMINI_API_KEY}",
                json={
                    "model": "models/text-embedding-004",
                    "content": {"parts": [{"text": text[:2048]}]},
                    "outputDimensionality": 1536,
                },
            )
            data = resp.json()
            return data.get("embedding", {}).get("values")
    except Exception as e:
        print(f"Embedding generation error: {e}")
        return None


async def find_similar_jobs(job_id: str, limit: int = 10) -> list[dict]:
    """Find similar jobs using pgvector cosine similarity."""
    from database import get_supabase_admin
    db = get_supabase_admin()

    try:
        # Get the embedding for the source job
        result = db.table("jobs").select("embedding").eq("id", job_id).single().execute()
        if not result.data or not result.data.get("embedding"):
            return []

        embedding = result.data["embedding"]

        # Use Supabase RPC for vector similarity search
        result = db.rpc("match_jobs", {
            "query_embedding": embedding,
            "match_threshold": 0.7,
            "match_count": limit,
            "exclude_id": job_id,
        }).execute()

        return result.data or []
    except Exception as e:
        print(f"Similar jobs search error: {e}")
        return []


async def match_resume_to_jobs(resume_text: str, limit: int = 20) -> list[dict]:
    """Find jobs matching a resume using pgvector."""
    embedding = await generate_embedding(resume_text)
    if not embedding:
        return []

    from database import get_supabase_admin
    db = get_supabase_admin()

    try:
        result = db.rpc("match_jobs", {
            "query_embedding": embedding,
            "match_threshold": 0.5,
            "match_count": limit,
            "exclude_id": None,
        }).execute()

        return result.data or []
    except Exception as e:
        print(f"Resume matching error: {e}")
        return []
