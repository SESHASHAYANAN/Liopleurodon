"""
Liopleurodon — SerpApi Scraper
Google Jobs scraper via SerpApi.
"""

import httpx
from scrapers.base import BaseScraper
from config import get_settings


class SerpApiScraper(BaseScraper):
    BASE_URL = "https://serpapi.com/search"

    async def scrape(self, query="software engineer", location="", page=1, num_results=20) -> list[dict]:
        settings = get_settings()
        if not settings.SERPAPI_KEY:
            return []

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                params = {
                    "engine": "google_jobs",
                    "q": query,
                    "api_key": settings.SERPAPI_KEY,
                    "start": (page - 1) * 10,
                }
                if location:
                    params["location"] = location

                resp = await client.get(self.BASE_URL, params=params)
                data = resp.json()
                return data.get("jobs_results", [])
        except Exception as e:
            print(f"SerpApi scraper error: {e}")
            return []

    def get_source_name(self) -> str:
        return "SerpApi"

    def is_configured(self) -> bool:
        return bool(get_settings().SERPAPI_KEY)
