"""
Liopleurodon — JSearch Scraper (RapidAPI)
Pulls from Google Jobs, LinkedIn, Indeed, Glassdoor simultaneously.
"""

import httpx
from scrapers.base import BaseScraper
from config import get_settings


class JSearchScraper(BaseScraper):
    BASE_URL = "https://jsearch.p.rapidapi.com/search"

    async def scrape(self, query="software engineer", location="", page=1, num_results=20) -> list[dict]:
        settings = get_settings()
        if not settings.JSEARCH_API_KEY:
            return []

        search_query = query
        if location:
            search_query = f"{query} in {location}"

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    self.BASE_URL,
                    headers={
                        "X-RapidAPI-Key": settings.JSEARCH_API_KEY,
                        "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
                    },
                    params={
                        "query": search_query,
                        "page": str(page),
                        "num_pages": "1",
                        "date_posted": "month",
                    },
                )
                data = resp.json()
                return data.get("data", [])
        except Exception as e:
            print(f"JSearch scraper error: {e}")
            return []

    def get_source_name(self) -> str:
        return "JSearch"

    def is_configured(self) -> bool:
        return bool(get_settings().JSEARCH_API_KEY)
