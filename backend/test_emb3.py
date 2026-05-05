import asyncio
import httpx
from config import get_settings

async def main():
    settings = get_settings()
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-2:embedContent?key={settings.GEMINI_API_KEY}",
            json={
                "model": "models/gemini-embedding-2",
                "content": {"parts": [{"text": "hello"}]},
            },
        )
        print("status:", resp.status_code)
        if resp.status_code == 200:
            data = resp.json()
            emb = data.get("embedding", {}).get("values")
            print("dim:", len(emb) if emb else "none")

asyncio.run(main())
