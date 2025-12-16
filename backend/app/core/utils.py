import hashlib
import re
from typing import Optional, Dict, Any
from datetime import datetime
from urllib.parse import urlparse


def normalize_location(location: str) -> str:
    """
    Normalize location to "City, State, Country" format when possible.
    Otherwise, keep raw text or return "Unknown".
    """
    if not location or location.strip() == "":
        return "Unknown"

    location = location.strip()

    # If already looks normalized (has commas), clean it up
    if "," in location:
        parts = [p.strip() for p in location.split(",")]
        parts = [p for p in parts if p]  # Remove empty parts
        return ", ".join(parts)

    return location


def normalize_work_mode(work_mode: Optional[str]) -> str:
    """
    Normalize work_mode to Remote, Hybrid, On-site, or Unknown.
    """
    if not work_mode:
        return "Unknown"

    work_mode_lower = work_mode.lower().strip()

    if "remote" in work_mode_lower:
        return "Remote"
    elif "hybrid" in work_mode_lower:
        return "Hybrid"
    elif any(term in work_mode_lower for term in ["on-site", "onsite", "office", "in-person"]):
        return "On-site"

    return "Unknown"


def normalize_date(date_str: Optional[str]) -> str:
    """
    Try to normalize date to ISO format. Return "Unknown" if parsing fails.
    """
    if not date_str or date_str.strip() == "":
        return "Unknown"

    date_str = date_str.strip()

    # Common patterns to try
    patterns = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%B %d, %Y",
        "%b %d, %Y",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
    ]

    for pattern in patterns:
        try:
            dt = datetime.strptime(date_str, pattern)
            return dt.date().isoformat()
        except ValueError:
            continue

    # Handle relative dates like "2 days ago", "1 week ago"
    relative_match = re.match(r"(\d+)\s+(day|week|month)s?\s+ago", date_str, re.IGNORECASE)
    if relative_match:
        # For now, return as-is since we don't have current date context
        # In production, you'd calculate the actual date
        return "Unknown"

    # If no pattern matches, keep original but mark as potentially invalid
    return date_str if len(date_str) < 50 else "Unknown"


def generate_url_hash(url: str) -> str:
    """
    Generate a hash from URL for deduplication.
    """
    # Normalize URL first
    parsed = urlparse(url)
    normalized_url = f"{parsed.netloc}{parsed.path}".lower()
    # Remove trailing slashes
    normalized_url = normalized_url.rstrip("/")

    return hashlib.sha256(normalized_url.encode()).hexdigest()[:16]


def generate_listing_hash(title: str, company: str, posted_date: str = "") -> str:
    """
    Generate a hash from listing key fields for duplicate detection.
    """
    key = f"{title.lower()}|{company.lower()}|{posted_date}".strip()
    return hashlib.md5(key.encode()).hexdigest()[:12]


def clean_html_text(html: str) -> str:
    """
    Remove HTML tags and clean up text.
    """
    if not html:
        return ""

    # Remove script and style elements
    clean = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    clean = re.sub(r'<style[^>]*>.*?</style>', '', clean, flags=re.DOTALL | re.IGNORECASE)

    # Remove HTML tags
    clean = re.sub(r'<[^>]+>', ' ', clean)

    # Clean up whitespace
    clean = re.sub(r'\s+', ' ', clean)
    clean = clean.strip()

    return clean


def extract_domain(url: str) -> Optional[str]:
    """
    Extract domain from URL.
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        # Remove www.
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except:
        return None


def validate_listing_data(data: Dict[str, Any]) -> tuple[bool, list[str]]:
    """
    Validate listing data and return quality flags.
    """
    flags = []

    # Check required fields
    if not data.get("title"):
        flags.append("missing_title")
    if not data.get("company_name"):
        flags.append("missing_company")
    if not data.get("apply_url"):
        flags.append("missing_apply_url")

    # Check description quality
    description = data.get("description_text", "")
    if len(description) < 50:
        flags.append("short_description")
    if len(description) == 0:
        flags.append("missing_description")

    # Check for suspicious patterns
    if description and len(description) > 10000:
        flags.append("unusually_long_description")

    # Check if too many fields are "Unknown"
    unknown_count = sum(1 for field in ["location", "work_mode", "employment_type", "posted_date", "salary_text"]
                       if data.get(field) == "Unknown")
    if unknown_count >= 4:
        flags.append("too_many_unknowns")

    is_valid = len(flags) < 3  # Allow some quality issues but not too many

    return is_valid, flags
