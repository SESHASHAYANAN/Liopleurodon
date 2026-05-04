"""
Liopleurodon — Findwork Scraper
Hacker News Jobs, GitHub Jobs, tech stack tags.
"""

import httpx
from scrapers.base import BaseScraper
from config import get_settings


class FindworkScraper(BaseScraper):
    BASE_URL = "https://findwork.dev/api/jobs/"

    async def scrape(self, query="software engineer", location="", page=1, num_results=20) -> list[dict]:
        settings = get_settings()
        if not settings.FINDWORK_API_KEY:
            return []

        try:
            params = {
                "search": query,
                "page": page,
            }
            if location:
                params["location"] = location

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    self.BASE_URL,
                    headers={"Authorization": f"Token {settings.FINDWORK_API_KEY}"},
                    params=params,
                )
                data = resp.json()
                return data.get("results", [])
        except Exception as e:
            print(f"Findwork scraper error: {e}")
            return []

    def get_source_name(self) -> str:
        return "Findwork"

    def is_configured(self) -> bool:
        return bool(get_settings().FINDWORK_API_KEY)
