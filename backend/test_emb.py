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
                "outputDimensionality": 1536,
            },
        )
        print(resp.status_code, resp.text)

asyncio.run(main())
