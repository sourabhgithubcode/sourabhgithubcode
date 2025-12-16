import pytest
from app.core.utils import (
    normalize_location,
    normalize_work_mode,
    generate_url_hash,
    generate_listing_hash,
    clean_html_text,
    extract_domain,
    validate_listing_data
)


class TestNormalization:
    """Test data normalization functions"""

    def test_normalize_location_with_commas(self):
        result = normalize_location("New York, NY, USA")
        assert result == "New York, NY, USA"

    def test_normalize_location_empty(self):
        result = normalize_location("")
        assert result == "Unknown"

    def test_normalize_location_none(self):
        result = normalize_location(None)
        assert result == "Unknown"

    def test_normalize_work_mode_remote(self):
        assert normalize_work_mode("remote") == "Remote"
        assert normalize_work_mode("REMOTE") == "Remote"
        assert normalize_work_mode("work from home remote") == "Remote"

    def test_normalize_work_mode_hybrid(self):
        assert normalize_work_mode("hybrid") == "Hybrid"
        assert normalize_work_mode("Hybrid work") == "Hybrid"

    def test_normalize_work_mode_onsite(self):
        assert normalize_work_mode("on-site") == "On-site"
        assert normalize_work_mode("onsite") == "On-site"
        assert normalize_work_mode("in office") == "On-site"

    def test_normalize_work_mode_unknown(self):
        assert normalize_work_mode("") == "Unknown"
        assert normalize_work_mode(None) == "Unknown"
        assert normalize_work_mode("flexible") == "Unknown"


class TestHashing:
    """Test hash generation functions"""

    def test_generate_url_hash_consistency(self):
        url1 = "https://example.com/job/123"
        url2 = "https://example.com/job/123"
        assert generate_url_hash(url1) == generate_url_hash(url2)

    def test_generate_url_hash_case_insensitive(self):
        url1 = "https://Example.com/Job/123"
        url2 = "https://example.com/job/123"
        assert generate_url_hash(url1) == generate_url_hash(url2)

    def test_generate_listing_hash(self):
        hash1 = generate_listing_hash("Software Engineer", "TechCorp", "2024-01-01")
        hash2 = generate_listing_hash("Software Engineer", "TechCorp", "2024-01-01")
        assert hash1 == hash2

    def test_generate_listing_hash_different_dates(self):
        hash1 = generate_listing_hash("Software Engineer", "TechCorp", "2024-01-01")
        hash2 = generate_listing_hash("Software Engineer", "TechCorp", "2024-01-02")
        assert hash1 != hash2


class TestTextCleaning:
    """Test text cleaning functions"""

    def test_clean_html_text_removes_tags(self):
        html = "<p>Hello <strong>world</strong></p>"
        result = clean_html_text(html)
        assert "<" not in result
        assert ">" not in result
        assert "Hello" in result
        assert "world" in result

    def test_clean_html_text_removes_scripts(self):
        html = "<p>Text</p><script>alert('xss')</script>"
        result = clean_html_text(html)
        assert "alert" not in result
        assert "Text" in result

    def test_clean_html_text_empty(self):
        assert clean_html_text("") == ""
        assert clean_html_text(None) == ""


class TestDomainExtraction:
    """Test domain extraction"""

    def test_extract_domain(self):
        assert extract_domain("https://www.example.com/path") == "example.com"
        assert extract_domain("https://example.com") == "example.com"
        assert extract_domain("http://subdomain.example.com") == "subdomain.example.com"

    def test_extract_domain_removes_www(self):
        assert extract_domain("https://www.example.com") == "example.com"


class TestValidation:
    """Test listing validation"""

    def test_validate_listing_data_valid(self):
        data = {
            "title": "Software Engineer",
            "company_name": "TechCorp",
            "apply_url": "https://example.com/apply",
            "description_text": "This is a great opportunity for software engineers to work on cutting-edge technology.",
            "location": "New York, NY",
            "work_mode": "Remote",
        }
        is_valid, flags = validate_listing_data(data)
        assert is_valid
        assert len(flags) == 0

    def test_validate_listing_data_missing_title(self):
        data = {
            "company_name": "TechCorp",
            "apply_url": "https://example.com/apply",
        }
        is_valid, flags = validate_listing_data(data)
        assert "missing_title" in flags

    def test_validate_listing_data_short_description(self):
        data = {
            "title": "Engineer",
            "company_name": "TechCorp",
            "apply_url": "https://example.com/apply",
            "description_text": "Short",
        }
        is_valid, flags = validate_listing_data(data)
        assert "short_description" in flags

    def test_validate_listing_data_too_many_unknowns(self):
        data = {
            "title": "Engineer",
            "company_name": "TechCorp",
            "apply_url": "https://example.com/apply",
            "description_text": "A good description that is long enough to pass validation.",
            "location": "Unknown",
            "work_mode": "Unknown",
            "employment_type": "Unknown",
            "posted_date": "Unknown",
            "salary_text": "Unknown",
        }
        is_valid, flags = validate_listing_data(data)
        assert "too_many_unknowns" in flags


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
