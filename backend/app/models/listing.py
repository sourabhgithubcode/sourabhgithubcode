from pydantic import BaseModel, Field, HttpUrl, field_validator
from typing import Optional, List
from datetime import datetime
from .enums import WorkMode, VisaCategory, ConfidenceBand


class ListingBase(BaseModel):
    source: str
    source_listing_id: Optional[str] = None
    source_url_hash: str
    title: str
    company_name: str
    location: str = "Unknown"
    work_mode: WorkMode = WorkMode.UNKNOWN
    employment_type: str = "Unknown"
    posted_date: str = "Unknown"
    apply_url: str
    description_text: str = ""
    requirements_text: str = ""
    salary_text: str = "Unknown"
    raw_html_path: Optional[str] = None
    raw_json_path: Optional[str] = None
    data_quality_flags: Optional[List[str]] = Field(default_factory=list)

    @field_validator('work_mode', mode='before')
    @classmethod
    def normalize_work_mode(cls, v):
        if isinstance(v, str):
            v_lower = v.lower().strip()
            if 'remote' in v_lower:
                return WorkMode.REMOTE
            elif 'hybrid' in v_lower:
                return WorkMode.HYBRID
            elif 'on-site' in v_lower or 'onsite' in v_lower or 'office' in v_lower:
                return WorkMode.ONSITE
        return WorkMode.UNKNOWN


class ListingCreate(ListingBase):
    scraped_at_utc: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class Listing(ListingBase):
    id: int
    scraped_at_utc: str
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class ListingResponse(Listing):
    visa_assessment: Optional['VisaAssessmentResponse'] = None


class ListingFilters(BaseModel):
    keyword: Optional[str] = None
    location: Optional[str] = None
    work_mode: Optional[WorkMode] = None
    visa_category: Optional[VisaCategory] = None
    confidence_band: Optional[ConfidenceBand] = None
    source: Optional[str] = None
    posted_date_start: Optional[str] = None
    posted_date_end: Optional[str] = None
    min_confidence_score: Optional[int] = Field(None, ge=0, le=100)
    max_confidence_score: Optional[int] = Field(None, ge=0, le=100)
    sort_by: str = Field(default="scraped_at_utc", pattern="^(posted_date|confidence_score|scraped_at_utc)$")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")
    limit: int = Field(default=50, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


# Avoid circular import
from .visa_assessment import VisaAssessmentResponse
ListingResponse.model_rebuild()
