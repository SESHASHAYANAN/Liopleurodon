"""
Liopleurodon — YC Work at a Startup Scraper
Scrapes Y Combinator portfolio job listings.
"""

import httpx
from scrapers.base import BaseScraper


class YCScraper(BaseScraper):
    # YC's public API endpoint for job listings
    BASE_URL = "https://www.workatastartup.com/companies"
    API_URL = "https://45bwzj1sgc-dsn.algolia.net/1/indexes/*/queries"

    async def scrape(self, query="software engineer", location="", page=1, num_results=20) -> list[dict]:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # Use Algolia-powered search that YC uses internally
                resp = await client.post(
                    self.API_URL,
                    headers={
                        "x-algolia-api-key": "NDcyMjRjOGVkNmMzZDkyZDVhODQ1MGQyNGYyYTQ5NmRjMzhhM2Y3NjUxOTkzZTcwNDFiNTdhOGFiZjcwMmIxYXRhZ0ZpbHRlcnM9",
                        "x-algolia-application-id": "45BWZJ1SGC",
                    },
                    json={
                        "requests": [{
                            "indexName": "YCJob_production",
                            "params": f"query={query}&hitsPerPage={num_results}&page={page - 1}",
                        }]
                    },
                )
                data = resp.json()
                results = data.get("results", [{}])[0].get("hits", [])

                # Transform to our expected format
                jobs = []
                for hit in results:
                    jobs.append({
                        "title": hit.get("title", ""),
                        "company_name": hit.get("company_name", ""),
                        "company_logo": hit.get("company_logo_url"),
                        "batch": hit.get("batch", ""),
                        "location": hit.get("location", ""),
                        "remote": hit.get("remote", False),
                        "salary_min": hit.get("salary_min"),
                        "salary_max": hit.get("salary_max"),
                        "experience": hit.get("experience_level"),
                        "description": hit.get("description", ""),
                        "url": hit.get("url", ""),
                        "posted_at": hit.get("created_at"),
                    })
                return jobs
        except Exception as e:
            print(f"YC scraper error: {e}")
            return []

    def get_source_name(self) -> str:
        return "YC"

    def is_configured(self) -> bool:
        return True
