from typing import Callable
from urllib.parse import urlparse

from backend.scrapers.schemas import ScrapedYarn

ScraperFn = Callable[[str], ScrapedYarn]

SCRAPERS: dict[str, ScraperFn] = {}


def get_scraper(url: str) -> ScraperFn | None:
    """Return the scraper function for the given URL's domain, or None."""
    domain = urlparse(url).netloc.lower()
    return SCRAPERS.get(domain)
