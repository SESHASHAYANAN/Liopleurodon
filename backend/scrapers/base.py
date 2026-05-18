"""
Liopleurodon — Base Scraper
Abstract base class for all job scrapers.
"""

from abc import ABC, abstractmethod
from typing import Optional


class BaseScraper(ABC):
    """Base class for all job source scrapers."""

    @abstractmethod
    async def scrape(
        self,
        query: str = "software engineer",
        location: str = "",
        page: int = 1,
        num_results: int = 20,
    ) -> list[dict]:
        """Scrape jobs from the source. Returns list of raw job dicts."""
        pass

    @abstractmethod
    def get_source_name(self) -> str:
        """Return the name of this source (e.g., 'JSearch', 'Adzuna')."""
        pass

    def is_configured(self) -> bool:
        """Check if the scraper has required API keys configured."""
        return True
