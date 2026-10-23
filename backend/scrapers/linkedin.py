"""
Liopleurodon — LinkedIn Scraper (via Apify)
Uses Apify LinkedIn Jobs Scraper actor.
"""

import httpx
import asyncio
from scrapers.base import BaseScraper
from scrapers.apify import linkedin_job_rows
from config import get_settings


class LinkedInScraper(BaseScraper):
    BASE_URL = "https://api.apify.com/v2"
    ACTOR_ID = "johnvc~linkedin-jobs-api"

    async def scrape(self, query="software engineer", location="", page=1, num_results=20) -> list[dict]:
        settings = get_settings()
        if not settings.APIFY_TOKEN:
            return []

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(
                    f"{self.BASE_URL}/acts/{self.ACTOR_ID}/run-sync-get-dataset-items",
                    params={"token": settings.APIFY_TOKEN, "timeout": 60},
                    json={
                        "keyword": query,
                        "location": location or "United States",
                        "maxJobs": min(num_results, 25),
                    },
                )
                # run-sync-get-dataset-items answers 201 on success
                if resp.status_code in (200, 201):
                    data = resp.json()
                    return linkedin_job_rows(data) if isinstance(data, list) else []
                return []
        except Exception as e:
            print(f"LinkedIn scraper error: {e}")
            return []

    def get_source_name(self) -> str:
        return "LinkedIn"

    def is_configured(self) -> bool:
        return bool(get_settings().APIFY_TOKEN)
