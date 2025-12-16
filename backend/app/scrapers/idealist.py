from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import re
import logging

from .base import BaseScraper
from app.core.utils import normalize_location, clean_html_text

logger = logging.getLogger(__name__)


class IdealistScraper(BaseScraper):
    """
    Scraper for Idealist.org volunteer and job listings.
    Note: This is a template implementation. Actual selectors will need
    to be adjusted based on Idealist's current HTML structure.
    """

    def __init__(self):
        super().__init__("idealist")
        self.base_url = "https://www.idealist.org"

    async def get_listing_urls(
        self,
        search_terms: str = "volunteer",
        location: str = "United States",
        max_pages: int = 5
    ) -> List[str]:
        """
        Get listing URLs from Idealist search results.
        """
        listing_urls = []

        # Build search URL
        # Note: Adjust parameters based on actual Idealist search URL structure
        search_url = f"{self.base_url}/en/volunteer-opportunities?q={search_terms}&locationString={location}"

        for page in range(1, max_pages + 1):
            page_url = f"{search_url}&page={page}"
            logger.info(f"Fetching search page {page}: {page_url}")

            html = await self.fetch(page_url)
            if not html:
                logger.warning(f"Failed to fetch search page {page}")
                break

            # Parse search results
            soup = BeautifulSoup(html, 'lxml')

            # Find listing links - adjust selector based on actual HTML structure
            # This is a template - actual selectors need to be verified
            listings = soup.select('a[href*="/volunteer/"], a[href*="/nonprofit-job/"]')

            if not listings:
                logger.info(f"No more listings found on page {page}")
                break

            for link in listings:
                href = link.get('href')
                if href:
                    # Make absolute URL
                    if href.startswith('/'):
                        href = self.base_url + href
                    if href not in listing_urls:
                        listing_urls.append(href)

            logger.info(f"Found {len(listings)} listings on page {page}")

        return listing_urls

    async def parse_listing(self, url: str, html: str) -> Optional[Dict[str, Any]]:
        """
        Parse an Idealist listing page.
        """
        try:
            soup = BeautifulSoup(html, 'lxml')

            # Extract data - these selectors are templates and need to be adjusted
            # based on actual Idealist HTML structure

            # Title
            title_elem = soup.select_one('h1.listing-title, h1[class*="title"], h1')
            title = title_elem.get_text(strip=True) if title_elem else "Unknown"

            # Company/Organization
            company_elem = soup.select_one('.organization-name, .org-name, [class*="organization"]')
            company_name = company_elem.get_text(strip=True) if company_elem else "Unknown"

            # Location
            location_elem = soup.select_one('.location, [class*="location"]')
            location = "Unknown"
            if location_elem:
                location = normalize_location(location_elem.get_text(strip=True))

            # Work mode - try to infer from description
            work_mode = "Unknown"
            description_elem = soup.select_one('.description, .listing-description, [class*="description"]')
            if description_elem:
                desc_text = description_elem.get_text().lower()
                if 'remote' in desc_text:
                    work_mode = "Remote"
                elif 'hybrid' in desc_text:
                    work_mode = "Hybrid"
                elif 'on-site' in desc_text or 'onsite' in desc_text:
                    work_mode = "On-site"

            # Employment type - usually volunteer for Idealist
            employment_type = "Volunteer"
            if '/nonprofit-job/' in url:
                employment_type = "Job"

            # Posted date
            date_elem = soup.select_one('.posted-date, [class*="date"]')
            posted_date = "Unknown"
            if date_elem:
                posted_date = date_elem.get_text(strip=True)

            # Description
            description_text = ""
            if description_elem:
                description_text = clean_html_text(str(description_elem))

            # Requirements - try to find dedicated section
            requirements_elem = soup.select_one('.requirements, [class*="requirements"], [class*="qualifications"]')
            requirements_text = ""
            if requirements_elem:
                requirements_text = clean_html_text(str(requirements_elem))

            # Salary - usually not applicable for volunteer positions
            salary_text = "Unknown"
            salary_elem = soup.select_one('.salary, [class*="compensation"]')
            if salary_elem:
                salary_text = salary_elem.get_text(strip=True)

            # Data quality flags
            data_quality_flags = []
            if len(description_text) < 100:
                data_quality_flags.append("short_description")
            if title == "Unknown":
                data_quality_flags.append("missing_title")
            if company_name == "Unknown":
                data_quality_flags.append("missing_company")

            # Build listing dict
            listing = {
                "source": self.source_name,
                "title": title,
                "company_name": company_name,
                "location": location,
                "work_mode": work_mode,
                "employment_type": employment_type,
                "posted_date": posted_date,
                "description_text": description_text,
                "requirements_text": requirements_text,
                "salary_text": salary_text,
                "data_quality_flags": data_quality_flags,
            }

            return listing

        except Exception as e:
            logger.error(f"Error parsing listing {url}: {e}")
            return None
