from typing import List, Dict, Any, Optional
import httpx
from bs4 import BeautifulSoup
import logging
import asyncio
from datetime import datetime

from app.core.config import settings
from app.models.visa_assessment import Evidence

logger = logging.getLogger(__name__)


class EvidenceCollector:
    """
    Collects evidence from web searches for visa assessment.
    """

    def __init__(self):
        self.headers = {
            "User-Agent": settings.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        self.timeout = settings.request_timeout_seconds

    async def search_company_visa_policy(
        self,
        company_name: str,
        company_domain: Optional[str] = None
    ) -> List[Evidence]:
        """
        Search for company's visa/OPT/CPT policy.
        Uses simple web scraping - in production, use proper search API.
        """
        evidence_list = []

        try:
            # Search queries to try
            queries = [
                f"{company_name} OPT CPT international students",
                f"{company_name} visa sponsorship policy",
                f"{company_name} careers international students",
                f"{company_name} E-Verify",
            ]

            for query in queries[:2]:  # Limit to avoid too many requests
                try:
                    # In production, use Google Custom Search API or similar
                    # For now, try to fetch company's careers page directly
                    if company_domain:
                        urls_to_check = [
                            f"https://{company_domain}/careers",
                            f"https://{company_domain}/jobs",
                            f"https://{company_domain}/about",
                        ]

                        for url in urls_to_check:
                            evidence = await self._check_url_for_evidence(url, query)
                            if evidence:
                                evidence_list.append(evidence)

                    await asyncio.sleep(1)  # Rate limiting

                except Exception as e:
                    logger.error(f"Error searching for '{query}': {e}")
                    continue

        except Exception as e:
            logger.error(f"Error in search_company_visa_policy: {e}")

        return evidence_list

    async def _check_url_for_evidence(
        self,
        url: str,
        search_context: str
    ) -> Optional[Evidence]:
        """
        Check a specific URL for visa-related evidence.
        """
        try:
            async with httpx.AsyncClient(
                headers=self.headers,
                timeout=self.timeout,
                follow_redirects=True
            ) as client:
                response = await client.get(url)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, 'lxml')

                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()

                text = soup.get_text()

                # Look for visa-related keywords
                keywords = [
                    "OPT", "CPT", "F-1", "international student",
                    "visa sponsorship", "work authorization",
                    "E-Verify", "H-1B"
                ]

                found_keywords = [kw for kw in keywords if kw.lower() in text.lower()]

                if found_keywords:
                    # Extract relevant excerpt
                    excerpt = self._extract_relevant_excerpt(text, found_keywords)

                    return Evidence(
                        url=url,
                        title=soup.title.string if soup.title else url,
                        excerpt=excerpt,
                        date=datetime.utcnow().isoformat(),
                        relevance="high" if len(found_keywords) >= 2 else "medium"
                    )

        except httpx.HTTPError as e:
            logger.debug(f"HTTP error checking {url}: {e}")
        except Exception as e:
            logger.error(f"Error checking {url}: {e}")

        return None

    def _extract_relevant_excerpt(
        self,
        text: str,
        keywords: List[str],
        context_chars: int = 200
    ) -> str:
        """
        Extract relevant excerpt containing keywords.
        """
        text_lower = text.lower()

        # Find first keyword occurrence
        for keyword in keywords:
            idx = text_lower.find(keyword.lower())
            if idx != -1:
                # Extract context around keyword
                start = max(0, idx - context_chars // 2)
                end = min(len(text), idx + context_chars // 2)
                excerpt = text[start:end].strip()

                # Clean up
                excerpt = ' '.join(excerpt.split())

                if start > 0:
                    excerpt = "..." + excerpt
                if end < len(text):
                    excerpt = excerpt + "..."

                return excerpt

        return ""

    async def check_explicit_restrictions(
        self,
        job_description: str
    ) -> Dict[str, Any]:
        """
        Check for explicit visa restrictions in job description.
        Returns dict with found restrictions and signals.
        """
        restrictions = {
            "found": False,
            "type": None,
            "excerpt": None
        }

        # Negative signals
        negative_patterns = [
            (r"(?i)us\s+citizens?\s+only", "citizenship_required"),
            (r"(?i)no\s+(?:visa\s+)?sponsorship", "no_sponsorship"),
            (r"(?i)security\s+clearance\s+required", "security_clearance"),
            (r"(?i)must\s+be\s+(?:legally\s+)?authorized\s+to\s+work", "work_auth_required"),
            (r"(?i)permanent\s+resident", "permanent_resident"),
        ]

        # Positive signals
        positive_patterns = [
            (r"(?i)opt\s+(?:and\s+)?cpt\s+(?:welcome|accepted|eligible)", "opt_cpt_accepted"),
            (r"(?i)international\s+students?\s+welcome", "international_welcome"),
            (r"(?i)visa\s+sponsorship\s+available", "sponsorship_available"),
            (r"(?i)we\s+sponsor\s+(?:h-1b|visas?)", "sponsorship_available"),
        ]

        import re

        # Check for negative signals
        for pattern, restriction_type in negative_patterns:
            match = re.search(pattern, job_description)
            if match:
                restrictions["found"] = True
                restrictions["type"] = restriction_type
                restrictions["excerpt"] = match.group(0)
                restrictions["signal"] = "negative"
                break

        # Check for positive signals
        if not restrictions["found"]:
            for pattern, signal_type in positive_patterns:
                match = re.search(pattern, job_description)
                if match:
                    restrictions["found"] = True
                    restrictions["type"] = signal_type
                    restrictions["excerpt"] = match.group(0)
                    restrictions["signal"] = "positive"
                    break

        return restrictions
