import asyncio
import httpx
from config import get_settings

async def main():
    settings = get_settings()
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={settings.GEMINI_API_KEY}",
            json={
                "model": "models/text-embedding-004",
                "content": {"parts": [{"text": "hello"}]},
                "outputDimensionality": 768,
            },
        )
        print("text-embedding-004 status:", resp.status_code)
        
        resp2 = await client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-1536:embedContent?key={settings.GEMINI_API_KEY}",
            json={
                "model": "models/gemini-embedding-1536",
                "content": {"parts": [{"text": "hello"}]},
            },
        )
        print("gemini-embedding-1536 status:", resp2.status_code)

        resp3 = await client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={settings.GEMINI_API_KEY}",
            json={
                "model": "models/text-embedding-004",
                "content": {"parts": [{"text": "hello"}]},
            },
        )
        print("text-embedding-004 no dim status:", resp3.status_code)

asyncio.run(main())
