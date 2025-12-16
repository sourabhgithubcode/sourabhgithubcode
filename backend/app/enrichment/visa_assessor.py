from typing import Dict, Any, Optional, List
from pydantic import BaseModel
import json
import logging
from datetime import datetime

from app.core.config import settings
from app.models.visa_assessment import (
    VisaCategory, ConfidenceBand, Evidence, Signal,
    VisaAssessmentCreate
)
from app.core.utils import extract_domain
from .evidence_collector import EvidenceCollector

logger = logging.getLogger(__name__)


class AssessmentResult(BaseModel):
    visa_category: VisaCategory
    confidence_score: int
    confidence_band: ConfidenceBand
    reasons_short: str
    reasons_long: str
    evidence: List[Evidence]
    signals: Dict[str, List[Signal]]


class VisaAssessor:
    """
    AI-powered visa friendliness assessor using LLM and evidence collection.
    """

    def __init__(self):
        self.evidence_collector = EvidenceCollector()
        self.model_version = settings.ai_model

        # Initialize AI client based on available API keys
        self.ai_client = None
        self.ai_provider = None

        if settings.anthropic_api_key:
            try:
                from anthropic import AsyncAnthropic
                self.ai_client = AsyncAnthropic(api_key=settings.anthropic_api_key)
                self.ai_provider = "anthropic"
            except ImportError:
                logger.warning("Anthropic package not available")

        elif settings.openai_api_key:
            try:
                from openai import AsyncOpenAI
                self.ai_client = AsyncOpenAI(api_key=settings.openai_api_key)
                self.ai_provider = "openai"
            except ImportError:
                logger.warning("OpenAI package not available")

    async def assess_listing(
        self,
        listing_id: int,
        company_name: str,
        job_title: str,
        job_description: str,
        location: str,
        apply_url: str,
        requirements: Optional[str] = None
    ) -> VisaAssessmentCreate:
        """
        Main method to assess a listing's visa friendliness.
        """
        logger.info(f"Assessing listing {listing_id}: {company_name} - {job_title}")

        # Step 1: Evidence collection
        company_domain = extract_domain(apply_url)
        evidence_list = await self.evidence_collector.search_company_visa_policy(
            company_name, company_domain
        )

        # Step 2: Check for explicit restrictions in job description
        restrictions = await self.evidence_collector.check_explicit_restrictions(
            job_description
        )

        # Step 3: Extract signals
        signals = self._extract_signals(
            job_description,
            requirements or "",
            evidence_list,
            restrictions
        )

        # Step 4: If we have AI client, use LLM for assessment
        if self.ai_client:
            result = await self._llm_assessment(
                company_name=company_name,
                job_title=job_title,
                job_description=job_description,
                location=location,
                evidence=evidence_list,
                signals=signals,
                restrictions=restrictions
            )
        else:
            # Fallback to rule-based assessment
            result = self._rule_based_assessment(
                signals, evidence_list, restrictions
            )

        # Create assessment object
        assessment = VisaAssessmentCreate(
            listing_id=listing_id,
            visa_category=result.visa_category,
            confidence_score_0_100=result.confidence_score,
            confidence_band=result.confidence_band,
            reasons_short=result.reasons_short,
            reasons_long=result.reasons_long,
            evidence_links_json=[e.model_dump() for e in result.evidence],
            signals_json={
                "positive": [s.model_dump() for s in result.signals.get("positive", [])],
                "negative": [s.model_dump() for s in result.signals.get("negative", [])],
                "neutral": [s.model_dump() for s in result.signals.get("neutral", [])]
            },
            model_version=self.model_version,
            assessed_at_utc=datetime.utcnow().isoformat()
        )

        return assessment

    def _extract_signals(
        self,
        job_description: str,
        requirements: str,
        evidence: List[Evidence],
        restrictions: Dict[str, Any]
    ) -> Dict[str, List[Signal]]:
        """
        Extract structured signals from all available data.
        """
        signals: Dict[str, List[Signal]] = {
            "positive": [],
            "negative": [],
            "neutral": []
        }

        # Check for explicit positive signals in job description
        combined_text = f"{job_description} {requirements}".lower()

        if "opt" in combined_text or "cpt" in combined_text:
            signals["positive"].append(Signal(
                type="positive",
                description="Job posting mentions OPT or CPT",
                source="job_description",
                confidence=90
            ))

        if "international student" in combined_text:
            signals["positive"].append(Signal(
                type="positive",
                description="Job posting mentions international students",
                source="job_description",
                confidence=85
            ))

        if "e-verify" in combined_text:
            signals["positive"].append(Signal(
                type="positive",
                description="Company participates in E-Verify",
                source="job_description",
                confidence=70
            ))

        # Check for negative signals
        if restrictions.get("found") and restrictions.get("signal") == "negative":
            signals["negative"].append(Signal(
                type="negative",
                description=f"Restriction found: {restrictions['type']}",
                source="job_description",
                confidence=95
            ))

        # Add positive signals from restrictions
        if restrictions.get("found") and restrictions.get("signal") == "positive":
            signals["positive"].append(Signal(
                type="positive",
                description=f"Positive signal: {restrictions['type']}",
                source="job_description",
                confidence=90
            ))

        # Add signals from evidence
        for ev in evidence:
            if ev.relevance == "high":
                signals["positive"].append(Signal(
                    type="positive",
                    description=f"Company website mentions visa-related information",
                    source=ev.url,
                    confidence=75
                ))

        return signals

    def _rule_based_assessment(
        self,
        signals: Dict[str, List[Signal]],
        evidence: List[Evidence],
        restrictions: Dict[str, Any]
    ) -> AssessmentResult:
        """
        Fallback rule-based assessment when LLM is not available.
        """
        positive_count = len(signals["positive"])
        negative_count = len(signals["negative"])

        # Determine category
        if negative_count > 0:
            category = VisaCategory.LOW
            confidence = 70
            reasons_short = "Explicit restrictions found in job posting"
            reasons_long = f"This position has explicit visa restrictions: {restrictions.get('type', 'unknown')}. {restrictions.get('excerpt', '')}"

        elif positive_count >= 2:
            category = VisaCategory.HIGH
            confidence = 85
            reasons_short = "Strong evidence of OPT/CPT acceptance"
            reasons_long = "Job posting explicitly mentions OPT/CPT or international students. Multiple positive signals found."

        elif positive_count == 1:
            category = VisaCategory.MID
            confidence = 65
            reasons_short = "Some evidence of visa friendliness"
            reasons_long = "Some positive signals found, but not explicit confirmation of OPT/CPT acceptance."

        else:
            category = VisaCategory.NO_HISTORY
            confidence = 30
            reasons_short = "No clear evidence found"
            reasons_long = "No explicit information about visa sponsorship or OPT/CPT acceptance found in job posting or company website."

        # Enforce evidence threshold rule
        if confidence > settings.ai_confidence_evidence_threshold and not evidence:
            confidence = settings.ai_confidence_evidence_threshold

        # Determine band
        if confidence >= 90:
            band = ConfidenceBand.HIGH
        elif confidence >= 70:
            band = ConfidenceBand.MID
        elif confidence >= 40:
            band = ConfidenceBand.LOW
        else:
            band = ConfidenceBand.NO_HISTORY

        return AssessmentResult(
            visa_category=category,
            confidence_score=confidence,
            confidence_band=band,
            reasons_short=reasons_short,
            reasons_long=reasons_long,
            evidence=evidence,
            signals=signals
        )

    async def _llm_assessment(
        self,
        company_name: str,
        job_title: str,
        job_description: str,
        location: str,
        evidence: List[Evidence],
        signals: Dict[str, List[Signal]],
        restrictions: Dict[str, Any]
    ) -> AssessmentResult:
        """
        Use LLM to assess visa friendliness with evidence-based reasoning.
        """
        # Build prompt
        prompt = self._build_assessment_prompt(
            company_name, job_title, job_description, location,
            evidence, signals, restrictions
        )

        try:
            # Call LLM
            if self.ai_provider == "anthropic":
                response = await self._call_anthropic(prompt)
            elif self.ai_provider == "openai":
                response = await self._call_openai(prompt)
            else:
                # Fallback to rule-based
                return self._rule_based_assessment(signals, evidence, restrictions)

            # Parse LLM response
            result = self._parse_llm_response(response, evidence, signals)
            return result

        except Exception as e:
            logger.error(f"Error in LLM assessment: {e}")
            # Fallback to rule-based
            return self._rule_based_assessment(signals, evidence, restrictions)

    def _build_assessment_prompt(
        self,
        company_name: str,
        job_title: str,
        job_description: str,
        location: str,
        evidence: List[Evidence],
        signals: Dict[str, List[Signal]],
        restrictions: Dict[str, Any]
    ) -> str:
        """
        Build assessment prompt for LLM.
        """
        evidence_text = "\n".join([
            f"- {e.url}: {e.excerpt}" for e in evidence
        ]) if evidence else "No external evidence found."

        positive_signals = "\n".join([
            f"- {s.description}" for s in signals.get("positive", [])
        ]) or "None"

        negative_signals = "\n".join([
            f"- {s.description}" for s in signals.get("negative", [])
        ]) or "None"

        prompt = f"""You are an expert at assessing whether job/volunteer positions are friendly to international students on OPT or CPT visas.

Analyze the following position and provide a structured assessment.

POSITION DETAILS:
Company: {company_name}
Title: {job_title}
Location: {location}

JOB DESCRIPTION:
{job_description[:2000]}

EVIDENCE COLLECTED:
{evidence_text}

POSITIVE SIGNALS:
{positive_signals}

NEGATIVE SIGNALS:
{negative_signals}

ASSESSMENT CRITERIA:
- High (90-100): Explicit OPT/CPT acceptance stated in posting or company policy
- Mid (70-89): Evidence of visa sponsorship or international hiring, but not explicit for OPT/CPT
- Low (40-69): Restrictions found or conflicting signals
- No history so far (0-39): No clear evidence either way

IMPORTANT RULES:
1. Confidence cannot exceed 60 without at least one strong evidence source
2. Explicit restrictions (citizenship required, no sponsorship) = Low category
3. Separate facts from inference in reasoning
4. Cite specific evidence in reasoning

Respond in this exact JSON format:
{{
  "category": "High|Mid|Low|No history so far",
  "confidence_score": <0-100>,
  "reasons_short": "<one sentence summary>",
  "reasons_long": "<detailed reasoning with evidence citations>"
}}"""

        return prompt

    async def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic API"""
        response = await self.ai_client.messages.create(
            model=self.model_version,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

    async def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API"""
        response = await self.ai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000
        )
        return response.choices[0].message.content

    def _parse_llm_response(
        self,
        response: str,
        evidence: List[Evidence],
        signals: Dict[str, List[Signal]]
    ) -> AssessmentResult:
        """Parse LLM JSON response"""
        try:
            # Extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = json.loads(response)

            # Map category string to enum
            category_map = {
                "High": VisaCategory.HIGH,
                "Mid": VisaCategory.MID,
                "Low": VisaCategory.LOW,
                "No history so far": VisaCategory.NO_HISTORY
            }

            category = category_map.get(data["category"], VisaCategory.NO_HISTORY)
            confidence = max(0, min(100, data["confidence_score"]))

            # Enforce evidence threshold
            if confidence > settings.ai_confidence_evidence_threshold and not evidence:
                confidence = settings.ai_confidence_evidence_threshold

            # Determine band
            if confidence >= 90:
                band = ConfidenceBand.HIGH
            elif confidence >= 70:
                band = ConfidenceBand.MID
            elif confidence >= 40:
                band = ConfidenceBand.LOW
            else:
                band = ConfidenceBand.NO_HISTORY

            return AssessmentResult(
                visa_category=category,
                confidence_score=confidence,
                confidence_band=band,
                reasons_short=data["reasons_short"],
                reasons_long=data["reasons_long"],
                evidence=evidence,
                signals=signals
            )

        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            # Fallback
            return self._rule_based_assessment(signals, evidence, {})
