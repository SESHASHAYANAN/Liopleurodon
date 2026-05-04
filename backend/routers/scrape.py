"""
Liopleurodon — Scrape Router
Trigger and monitor scraping operations.
"""

from fastapi import APIRouter
from services.scheduler import scrape_all_sources, get_scrape_status

router = APIRouter(prefix="/api/scrape", tags=["scrape"])


@router.post("/trigger")
async def trigger_scrape(
    query: str = "software engineer",
    location: str = "",
):
    """Manually trigger a scrape from all sources."""
    result = await scrape_all_sources(query=query, location=location)
    return result


@router.get("/status")
async def scrape_status():
    """Get the status of the last scrape run."""
    return get_scrape_status()
