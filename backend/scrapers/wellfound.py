"""
Liopleurodon — Wellfound (AngelList) Scraper
Startup and VC-backed company jobs from public listings.
"""

import httpx
from scrapers.base import BaseScraper


class WellfoundScraper(BaseScraper):
    """Scrapes Wellfound (formerly AngelList) job listings via their GraphQL API."""
    BASE_URL = "https://wellfound.com/graphql"

    async def scrape(self, query="software engineer", location="", page=1, num_results=20) -> list[dict]:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    self.BASE_URL,
                    headers={
                        "Content-Type": "application/json",
                        "apollographql-client-name": "talent-search",
                    },
                    json={
                        "operationName": "JobSearchResults",
                        "variables": {
                            "query": query,
                            "page": page,
                            "perPage": num_results,
                            "locationQuery": location or "",
                        },
                        "query": """
                        query JobSearchResults($query: String, $page: Int, $perPage: Int, $locationQuery: String) {
                            talent {
                                jobListings(query: $query, page: $page, perPage: $perPage, locationQuery: $locationQuery) {
                                    results {
                                        id
                                        title
                                        description
                                        url: slug
                                        remote
                                        compensation
                                        startup {
                                            name
                                            logoUrl
                                            companySize
                                        }
                                        skills: tags { name }
                                    }
                                }
                            }
                        }""",
                    },
                )
                data = resp.json()
                results = (data.get("data", {}).get("talent", {})
                          .get("jobListings", {}).get("results", []))

                jobs = []
                for r in results:
                    startup = r.get("startup", {})
                    skills = [s.get("name", "") for s in r.get("skills", [])]
                    comp = r.get("compensation") or ""
                    salary_min = salary_max = None
                    if isinstance(comp, str) and "-" in comp:
                        parts = comp.replace("$", "").replace("k", "000").replace(",", "").split("-")
                        try:
                            salary_min = float(parts[0].strip())
                            salary_max = float(parts[1].strip())
                        except (ValueError, IndexError):
                            pass

                    jobs.append({
                        "title": r.get("title", ""),
                        "company_name": startup.get("name", ""),
                        "company_logo": startup.get("logoUrl"),
                        "location": "",
                        "remote": r.get("remote", False),
                        "salary_min": salary_min,
                        "salary_max": salary_max,
                        "description": r.get("description", ""),
                        "url": f"https://wellfound.com/jobs/{r.get('url', '')}",
                        "skills": skills,
                    })
                return jobs
        except Exception as e:
            print(f"Wellfound scraper error: {e}")
            return []

    def get_source_name(self) -> str:
        return "Wellfound"

    def is_configured(self) -> bool:
        return True
