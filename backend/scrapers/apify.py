"""
Liopleurodon — Apify Scraper
LinkedIn + Indeed + Glassdoor scraper via Apify actors.
"""

import httpx
import asyncio
from scrapers.base import BaseScraper
from config import get_settings


class ApifyScraper(BaseScraper):
    BASE_URL = "https://api.apify.com/v2"
    # Apify actor IDs for different sources
    LINKEDIN_ACTOR = "anchor/linkedin-job-scraper"
    INDEED_ACTOR = "misceres/indeed-scraper"

    async def scrape(self, query="software engineer", location="", page=1, num_results=20) -> list[dict]:
        settings = get_settings()
        if not settings.APIFY_TOKEN:
            return []

        results = []
        try:
            # Run LinkedIn scraper
            linkedin_jobs = await self._run_actor(
                self.LINKEDIN_ACTOR,
                {"searchQueries": [query], "location": location or "United States", "maxResults": num_results},
                settings.APIFY_TOKEN,
            )
            results.extend(linkedin_jobs)
        except Exception as e:
            print(f"Apify LinkedIn error: {e}")

        return results

    async def _run_actor(self, actor_id: str, input_data: dict, token: str) -> list[dict]:
        """Run an Apify actor and get results."""
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                # Start the actor run
                resp = await client.post(
                    f"{self.BASE_URL}/acts/{actor_id}/runs",
                    params={"token": token},
                    json=input_data,
                )
                run_data = resp.json().get("data", {})
                run_id = run_data.get("id")
                if not run_id:
                    return []

                # Wait for completion (poll every 5 seconds, max 60 seconds)
                for _ in range(12):
                    await asyncio.sleep(5)
                    status_resp = await client.get(
                        f"{self.BASE_URL}/actor-runs/{run_id}",
                        params={"token": token},
                    )
                    status = status_resp.json().get("data", {}).get("status")
                    if status == "SUCCEEDED":
                        break
                    elif status in ("FAILED", "ABORTED", "TIMED-OUT"):
                        return []

                # Get results from dataset
                dataset_id = run_data.get("defaultDatasetId")
                if not dataset_id:
                    return []

                items_resp = await client.get(
                    f"{self.BASE_URL}/datasets/{dataset_id}/items",
                    params={"token": token, "format": "json"},
                )
                return items_resp.json() if isinstance(items_resp.json(), list) else []
        except Exception as e:
            print(f"Apify actor run error: {e}")
            return []

    def get_source_name(self) -> str:
        return "Apify"

    def is_configured(self) -> bool:
        return bool(get_settings().APIFY_TOKEN)
