from typing import Callable
from urllib.parse import urlparse

from backend.scrapers.schemas import ScrapedYarn

ScraperFn = Callable[[str], ScrapedYarn]

from backend.scrapers.lovecrafts import scrape_lovecrafts
from backend.scrapers.wool_warehouse import scrape_wool_warehouse

SCRAPERS: dict[str, ScraperFn] = {
    "www.woolwarehouse.co.uk": scrape_wool_warehouse,
    "www.lovecrafts.com": scrape_lovecrafts,
}


def get_scraper(url: str) -> ScraperFn | None:
    """Return the scraper function for the given URL's domain, or None."""
    domain = urlparse(url).netloc.lower()
    return SCRAPERS.get(domain)
