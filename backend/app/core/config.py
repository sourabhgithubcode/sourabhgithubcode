from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Database
    database_url: str = "sqlite:///./database/listings.db"

    # API Keys
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None

    # Scraping
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    rate_limit_requests_per_minute: int = 30
    request_timeout_seconds: int = 30

    # AI Enrichment
    ai_model: str = "claude-3-5-sonnet-20241022"
    ai_max_retries: int = 3
    ai_cache_hours: int = 24
    ai_confidence_evidence_threshold: int = 60

    # Scheduling
    scrape_interval_hours: int = 6
    assessment_batch_size: int = 10

    # Storage
    raw_html_path: str = "./scraped_data/html"
    raw_json_path: str = "./scraped_data/json"

    # Frontend
    frontend_url: str = "http://localhost:3000"
    backend_url: str = "http://localhost:8000"

    # Logging
    log_level: str = "INFO"


settings = Settings()
