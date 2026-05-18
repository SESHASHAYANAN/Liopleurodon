"""
Liopleurodon — Adzuna Scraper
16+ countries, salary data, 250 req/day free.
"""

import httpx
from scrapers.base import BaseScraper
from config import get_settings


class AdzunaScraper(BaseScraper):
    BASE_URL = "https://api.adzuna.com/v1/api/jobs"

    async def scrape(self, query="software engineer", location="", page=1, num_results=20) -> list[dict]:
        settings = get_settings()
        if not settings.ADZUNA_APP_ID or not settings.ADZUNA_API_KEY:
            return []

        country = "us"  # Default
        country_map = {
            "uk": "gb", "united kingdom": "gb", "canada": "ca", "australia": "au",
            "germany": "de", "france": "fr", "india": "in", "netherlands": "nl",
            "brazil": "br", "singapore": "sg",
        }
        if location:
            loc_lower = location.lower()
            for key, code in country_map.items():
                if key in loc_lower:
                    country = code
                    break

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    f"{self.BASE_URL}/{country}/search/{page}",
                    params={
                        "app_id": settings.ADZUNA_APP_ID,
                        "app_key": settings.ADZUNA_API_KEY,
                        "what": query,
                        "results_per_page": num_results,
                        "content-type": "application/json",
                    },
                )
                data = resp.json()
                return data.get("results", [])
        except Exception as e:
            print(f"Adzuna scraper error: {e}")
            return []

    def get_source_name(self) -> str:
        return "Adzuna"

    def is_configured(self) -> bool:
        s = get_settings()
        return bool(s.ADZUNA_APP_ID and s.ADZUNA_API_KEY)
