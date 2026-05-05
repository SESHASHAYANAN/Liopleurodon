import asyncio
import httpx
from config import get_settings

async def main():
    settings = get_settings()
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"https://generativelanguage.googleapis.com/v1beta/models?key={settings.GEMINI_API_KEY}",
        )
        for m in resp.json().get('models', []):
            if 'embed' in m['name'] or 'embedding' in m['name']:
                print(m['name'], m['supportedGenerationMethods'])

asyncio.run(main())
