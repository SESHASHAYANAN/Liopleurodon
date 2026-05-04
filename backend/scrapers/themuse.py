"""
Liopleurodon — The Muse Scraper
Company culture, team info, job levels, free.
"""

import httpx
from scrapers.base import BaseScraper
from config import get_settings


class TheMuseScraper(BaseScraper):
    BASE_URL = "https://www.themuse.com/api/public/jobs"

    async def scrape(self, query="software engineer", location="", page=1, num_results=20) -> list[dict]:
        try:
            params = {
                "page": page,
                "descending": "true",
            }
            if location:
                params["location"] = location

            # The Muse uses category for filtering
            category_map = {
                "software": "Software Engineering",
                "engineer": "Software Engineering",
                "data": "Data Science",
                "design": "Design",
                "product": "Product",
                "marketing": "Marketing",
            }
            for keyword, category in category_map.items():
                if keyword in query.lower():
                    params["category"] = category
                    break

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(self.BASE_URL, params=params)
                data = resp.json()
                return data.get("results", [])
        except Exception as e:
            print(f"The Muse scraper error: {e}")
            return []

    def get_source_name(self) -> str:
        return "The Muse"

    def is_configured(self) -> bool:
        return True  # The Muse API is free, no key required for basic access
