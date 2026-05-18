"""
Liopleurodon — TheirStack Scraper
315K+ sources, 200 free credits/month.
"""

import httpx
from scrapers.base import BaseScraper
from config import get_settings


class TheirStackScraper(BaseScraper):
    BASE_URL = "https://api.theirstack.com/v1/jobs/search"

    async def scrape(self, query="software engineer", location="", page=1, num_results=20) -> list[dict]:
        settings = get_settings()
        if not settings.THEIRSTACK_API_KEY:
            return []

        try:
            payload = {
                "job_title_or": [query],
                "limit": num_results,
                "offset": (page - 1) * num_results,
                "posted_at_max_age_days": 30,
                "order_by": [{"desc": True, "field": "date_posted"}],
            }
            if location:
                payload["job_location_pattern_or"] = [location]

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    self.BASE_URL,
                    headers={
                        "Authorization": f"Bearer {settings.THEIRSTACK_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                data = resp.json()
                return data.get("data", [])
        except Exception as e:
            print(f"TheirStack scraper error: {e}")
            return []

    def get_source_name(self) -> str:
        return "TheirStack"

    def is_configured(self) -> bool:
        return bool(get_settings().THEIRSTACK_API_KEY)
