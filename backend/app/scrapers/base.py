from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import httpx
import asyncio
from datetime import datetime
from pathlib import Path
import json
import logging

from app.core.config import settings
from app.core.utils import generate_url_hash

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple rate limiter for HTTP requests"""

    def __init__(self, requests_per_minute: int):
        self.requests_per_minute = requests_per_minute
        self.min_interval = 60.0 / requests_per_minute
        self.last_request_time = 0

    async def wait(self):
        """Wait if necessary to respect rate limit"""
        now = asyncio.get_event_loop().time()
        time_since_last = now - self.last_request_time

        if time_since_last < self.min_interval:
            wait_time = self.min_interval - time_since_last
            await asyncio.sleep(wait_time)

        self.last_request_time = asyncio.get_event_loop().time()


class BaseScraper(ABC):
    """Base class for all scrapers"""

    def __init__(self, source_name: str):
        self.source_name = source_name
        self.rate_limiter = RateLimiter(settings.rate_limit_requests_per_minute)
        self.headers = {
            "User-Agent": settings.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

        # Ensure storage directories exist
        Path(settings.raw_html_path).mkdir(parents=True, exist_ok=True)
        Path(settings.raw_json_path).mkdir(parents=True, exist_ok=True)

    async def fetch(self, url: str, retries: int = 3) -> Optional[str]:
        """Fetch URL content with retries and rate limiting"""
        await self.rate_limiter.wait()

        for attempt in range(retries):
            try:
                async with httpx.AsyncClient(
                    headers=self.headers,
                    timeout=settings.request_timeout_seconds,
                    follow_redirects=True
                ) as client:
                    response = await client.get(url)
                    response.raise_for_status()
                    return response.text

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:  # Rate limited
                    wait_time = 2 ** attempt
                    logger.warning(f"Rate limited on {url}, waiting {wait_time}s")
                    await asyncio.sleep(wait_time)
                elif e.response.status_code in [403, 401]:  # Blocked
                    logger.error(f"Access blocked for {url}: {e.response.status_code}")
                    return None
                else:
                    logger.error(f"HTTP error fetching {url}: {e}")
                    if attempt == retries - 1:
                        return None

            except Exception as e:
                logger.error(f"Error fetching {url}: {e}")
                if attempt == retries - 1:
                    return None
                await asyncio.sleep(2 ** attempt)

        return None

    def save_raw_html(self, url: str, content: str) -> str:
        """Save raw HTML to file and return path"""
        url_hash = generate_url_hash(url)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.source_name}_{url_hash}_{timestamp}.html"
        filepath = Path(settings.raw_html_path) / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        return str(filepath)

    def save_raw_json(self, url: str, data: Dict[str, Any]) -> str:
        """Save raw JSON to file and return path"""
        url_hash = generate_url_hash(url)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.source_name}_{url_hash}_{timestamp}.json"
        filepath = Path(settings.raw_json_path) / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return str(filepath)

    @abstractmethod
    async def get_listing_urls(self, **kwargs) -> List[str]:
        """
        Get list of listing URLs to scrape.
        Should be implemented by each scraper.
        """
        pass

    @abstractmethod
    async def parse_listing(self, url: str, html: str) -> Optional[Dict[str, Any]]:
        """
        Parse a listing page and return normalized data.
        Should return dict with keys matching ListingCreate schema.
        """
        pass

    async def scrape(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Main scraping method. Returns list of parsed listings.
        """
        logger.info(f"Starting scrape for {self.source_name}")

        try:
            # Get listing URLs
            listing_urls = await self.get_listing_urls(**kwargs)
            logger.info(f"Found {len(listing_urls)} listing URLs")

            # Scrape each listing
            listings = []
            for i, url in enumerate(listing_urls, 1):
                logger.info(f"Scraping listing {i}/{len(listing_urls)}: {url}")

                try:
                    html = await self.fetch(url)
                    if not html:
                        logger.warning(f"Failed to fetch {url}")
                        continue

                    # Save raw HTML
                    html_path = self.save_raw_html(url, html)

                    # Parse listing
                    parsed = await self.parse_listing(url, html)
                    if parsed:
                        parsed['raw_html_path'] = html_path
                        parsed['apply_url'] = url
                        parsed['source_url_hash'] = generate_url_hash(url)
                        listings.append(parsed)
                    else:
                        logger.warning(f"Failed to parse {url}")

                except Exception as e:
                    logger.error(f"Error scraping {url}: {e}")
                    continue

            logger.info(f"Scraped {len(listings)} listings from {self.source_name}")
            return listings

        except Exception as e:
            logger.error(f"Error in scrape for {self.source_name}: {e}")
            raise
