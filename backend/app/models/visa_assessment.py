from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, List
from datetime import datetime
from .enums import VisaCategory, ConfidenceBand


class Signal(BaseModel):
    type: str  # positive, negative, neutral
    description: str
    source: Optional[str] = None
    confidence: Optional[int] = Field(None, ge=0, le=100)


class Evidence(BaseModel):
    url: str
    title: str
    excerpt: Optional[str] = None
    date: Optional[str] = None
    relevance: str = "medium"  # high, medium, low


class VisaAssessmentBase(BaseModel):
    visa_category: VisaCategory
    confidence_score_0_100: int = Field(..., ge=0, le=100)
    confidence_band: ConfidenceBand
    reasons_short: str
    reasons_long: str
    evidence_links_json: Optional[List[Evidence]] = Field(default_factory=list)
    signals_json: Optional[Dict[str, List[Signal]]] = Field(
        default_factory=lambda: {
            "positive": [],
            "negative": [],
            "neutral": []
        }
    )
    model_version: str

    @field_validator('confidence_band', mode='before')
    @classmethod
    def determine_confidence_band(cls, v, info):
        # If confidence_band is already set, use it
        if v and v in [b.value for b in ConfidenceBand]:
            return v

        # Otherwise, determine from score
        score = info.data.get('confidence_score_0_100', 0)
        if score >= 90:
            return ConfidenceBand.HIGH
        elif score >= 70:
            return ConfidenceBand.MID
        elif score >= 40:
            return ConfidenceBand.LOW
        else:
            return ConfidenceBand.NO_HISTORY


class VisaAssessmentCreate(VisaAssessmentBase):
    listing_id: int
    assessed_at_utc: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class VisaAssessment(VisaAssessmentBase):
    id: int
    listing_id: int
    assessed_at_utc: str
    human_override_category: Optional[str] = None
    human_override_note: Optional[str] = None
    created_at: str

    model_config = {"from_attributes": True}


class VisaAssessmentResponse(VisaAssessment):
    pass


class OverrideRequest(BaseModel):
    category: VisaCategory
    note: str = Field(..., min_length=10)
