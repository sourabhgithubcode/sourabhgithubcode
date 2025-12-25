"""
Scoring engine for calculating visibility scores and demand metrics.
"""

import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta
from loguru import logger
from sqlalchemy import func
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.database.models import (
    Clinic, Review, SearchTrend, VisibilityScore,
    DemandMetric, CompetitorAnalysis
)
from src.database.init_db import get_session


class ScoringEngine:
    """
    Calculate visibility scores, demand metrics, and competitor analysis.
    """

    def __init__(self):
        self.session = get_session()
        self.calculation_date = date.today()

    def normalize_score(self, value, min_val, max_val):
        """
        Normalize a value to 0-100 scale.
        """
        if max_val == min_val:
            return 50.0

        normalized = ((value - min_val) / (max_val - min_val)) * 100
        return max(0, min(100, normalized))

    def calculate_rating_score(self, clinic):
        """
        Calculate rating score (0-100) based on Google and Yelp ratings.
        """
        ratings = []
        weights = []

        if clinic.google_rating:
            ratings.append(clinic.google_rating)
            weights.append(clinic.google_review_count or 1)

        if clinic.yelp_rating:
            ratings.append(clinic.yelp_rating)
            weights.append(clinic.yelp_review_count or 1)

        if not ratings:
            return 0.0

        # Weighted average
        avg_rating = np.average(ratings, weights=weights)

        # Convert 5-star scale to 0-100
        return (avg_rating / 5.0) * 100

    def calculate_review_volume_score(self, clinic, max_reviews):
        """
        Calculate review volume score (0-100).
        """
        total_reviews = (clinic.google_review_count or 0) + (clinic.yelp_review_count or 0)

        if max_reviews == 0:
            return 0.0

        # Use logarithmic scale for review count
        if total_reviews == 0:
            return 0.0

        score = (np.log1p(total_reviews) / np.log1p(max_reviews)) * 100
        return min(100, score)

    def calculate_recency_score(self, clinic_id):
        """
        Calculate recency score based on recent review activity.
        """
        # Get reviews from last 90 days
        ninety_days_ago = datetime.utcnow() - timedelta(days=90)

        recent_reviews = self.session.query(Review).filter(
            Review.clinic_id == clinic_id,
            Review.review_date >= ninety_days_ago
        ).count()

        # Score based on recent activity (more recent reviews = higher score)
        if recent_reviews == 0:
            return 20.0  # Base score for no recent reviews
        elif recent_reviews < 5:
            return 40.0
        elif recent_reviews < 10:
            return 60.0
        elif recent_reviews < 20:
            return 80.0
        else:
            return 100.0

    def calculate_geographic_score(self, clinic):
        """
        Calculate geographic score based on location competitiveness.
        """
        if not clinic.zip_code:
            return 50.0

        # Count competitors in same ZIP code
        competitors = self.session.query(Clinic).filter(
            Clinic.zip_code == clinic.zip_code,
            Clinic.is_active == True,
            Clinic.id != clinic.id
        ).count()

        # Fewer competitors = higher score
        if competitors == 0:
            return 100.0
        elif competitors < 5:
            return 80.0
        elif competitors < 10:
            return 60.0
        elif competitors < 20:
            return 40.0
        else:
            return 20.0

    def calculate_visibility_scores(self):
        """
        Calculate visibility scores for all active clinics.
        """
        logger.info("Calculating visibility scores...")

        # Get all active clinics
        clinics = self.session.query(Clinic).filter_by(is_active=True).all()

        # Calculate max review count for normalization
        max_reviews = self.session.query(
            func.max(
                func.coalesce(Clinic.google_review_count, 0) +
                func.coalesce(Clinic.yelp_review_count, 0)
            )
        ).scalar() or 1

        scores_created = 0

        for clinic in clinics:
            try:
                # Calculate component scores
                rating_score = self.calculate_rating_score(clinic)
                review_volume_score = self.calculate_review_volume_score(clinic, max_reviews)
                recency_score = self.calculate_recency_score(clinic.id)
                geographic_score = self.calculate_geographic_score(clinic)

                # Calculate overall visibility score (weighted average)
                overall_score = (
                    rating_score * 0.30 +
                    review_volume_score * 0.30 +
                    recency_score * 0.25 +
                    geographic_score * 0.15
                )

                # Check if score already exists for today
                existing_score = self.session.query(VisibilityScore).filter_by(
                    clinic_id=clinic.id,
                    calculation_date=self.calculation_date
                ).first()

                if existing_score:
                    # Update
                    existing_score.rating_score = rating_score
                    existing_score.review_volume_score = review_volume_score
                    existing_score.recency_score = recency_score
                    existing_score.geographic_score = geographic_score
                    existing_score.overall_visibility_score = overall_score
                else:
                    # Create new
                    score = VisibilityScore(
                        clinic_id=clinic.id,
                        calculation_date=self.calculation_date,
                        rating_score=rating_score,
                        review_volume_score=review_volume_score,
                        recency_score=recency_score,
                        geographic_score=geographic_score,
                        overall_visibility_score=overall_score
                    )
                    self.session.add(score)
                    scores_created += 1

            except Exception as e:
                logger.error(f"Failed to calculate score for clinic {clinic.id}: {e}")

        self.session.commit()

        # Calculate rankings
        self.calculate_rankings()

        logger.success(f"✓ Calculated {scores_created} visibility scores")

    def calculate_rankings(self):
        """
        Calculate local and city-wide rankings.
        """
        logger.info("Calculating rankings...")

        # Get all scores for today
        scores = self.session.query(VisibilityScore).filter_by(
            calculation_date=self.calculation_date
        ).all()

        # Group by ZIP code for local rankings
        zip_groups = {}
        for score in scores:
            clinic = self.session.query(Clinic).get(score.clinic_id)
            if clinic and clinic.zip_code:
                if clinic.zip_code not in zip_groups:
                    zip_groups[clinic.zip_code] = []
                zip_groups[clinic.zip_code].append(score)

        # Calculate local rankings
        for zip_code, zip_scores in zip_groups.items():
            sorted_scores = sorted(
                zip_scores,
                key=lambda x: x.overall_visibility_score,
                reverse=True
            )
            for rank, score in enumerate(sorted_scores, 1):
                score.local_rank = rank

        # Calculate city-wide rankings
        sorted_city_scores = sorted(
            scores,
            key=lambda x: x.overall_visibility_score,
            reverse=True
        )
        for rank, score in enumerate(sorted_city_scores, 1):
            score.city_rank = rank

        self.session.commit()

        logger.success("✓ Rankings calculated")

    def calculate_demand_metrics(self):
        """
        Calculate demand metrics for service categories and locations.
        """
        logger.info("Calculating demand metrics...")

        from config.settings import SERVICE_CATEGORIES, CHICAGO_ZIP_CODES

        metrics_created = 0

        # Get recent trend data (last 30 days)
        thirty_days_ago = self.calculation_date - timedelta(days=30)

        for category, keywords in SERVICE_CATEGORIES.items():
            # Calculate aggregate demand for category
            category_demand = self.session.query(
                func.avg(SearchTrend.interest_score)
            ).filter(
                SearchTrend.service_category == category,
                SearchTrend.date >= thirty_days_ago
            ).scalar() or 0

            # Analyze by ZIP code
            for zip_code in CHICAGO_ZIP_CODES:
                try:
                    # Count clinics in ZIP
                    clinic_count = self.session.query(Clinic).filter(
                        Clinic.zip_code == zip_code,
                        Clinic.is_active == True
                    ).count()

                    # Get average rating
                    avg_rating = self.session.query(
                        func.avg(
                            (func.coalesce(Clinic.google_rating, 0) +
                             func.coalesce(Clinic.yelp_rating, 0)) / 2
                        )
                    ).filter(
                        Clinic.zip_code == zip_code,
                        Clinic.is_active == True
                    ).scalar() or 0

                    # Total reviews
                    total_reviews = self.session.query(
                        func.sum(
                            func.coalesce(Clinic.google_review_count, 0) +
                            func.coalesce(Clinic.yelp_review_count, 0)
                        )
                    ).filter(
                        Clinic.zip_code == zip_code,
                        Clinic.is_active == True
                    ).scalar() or 0

                    # Calculate demand-to-competition ratio
                    if clinic_count > 0:
                        demand_ratio = category_demand / clinic_count
                    else:
                        demand_ratio = category_demand  # High opportunity if no competition

                    # Opportunity score (combines demand and low competition)
                    if clinic_count == 0:
                        opportunity_score = category_demand
                    else:
                        # High demand + low competition = high opportunity
                        opportunity_score = (demand_ratio * 0.6) + ((100 - avg_rating) * 0.2) + \
                                          (max(0, 10 - clinic_count) * 4)

                    # Determine trend
                    trend = self.determine_trend(category, thirty_days_ago)

                    # Save metric
                    existing = self.session.query(DemandMetric).filter_by(
                        service_category=category,
                        zip_code=zip_code,
                        calculation_date=self.calculation_date
                    ).first()

                    if existing:
                        existing.search_demand_index = category_demand
                        existing.search_volume_trend = trend
                        existing.clinic_count = clinic_count
                        existing.avg_rating = avg_rating
                        existing.total_review_count = total_reviews
                        existing.demand_to_competition_ratio = demand_ratio
                        existing.opportunity_score = opportunity_score
                    else:
                        metric = DemandMetric(
                            service_category=category,
                            zip_code=zip_code,
                            calculation_date=self.calculation_date,
                            search_demand_index=category_demand,
                            search_volume_trend=trend,
                            clinic_count=clinic_count,
                            avg_rating=avg_rating,
                            total_review_count=total_reviews,
                            demand_to_competition_ratio=demand_ratio,
                            opportunity_score=opportunity_score
                        )
                        self.session.add(metric)
                        metrics_created += 1

                except Exception as e:
                    logger.error(f"Failed to calculate demand for {category} in {zip_code}: {e}")

        self.session.commit()

        logger.success(f"✓ Calculated {metrics_created} demand metrics")

    def determine_trend(self, category, since_date):
        """
        Determine if search trend is increasing, stable, or decreasing.
        """
        trends = self.session.query(SearchTrend).filter(
            SearchTrend.service_category == category,
            SearchTrend.date >= since_date
        ).order_by(SearchTrend.date).all()

        if len(trends) < 7:
            return 'stable'

        # Compare first week vs last week
        first_week = np.mean([t.interest_score for t in trends[:7]])
        last_week = np.mean([t.interest_score for t in trends[-7:]])

        change = ((last_week - first_week) / first_week * 100) if first_week > 0 else 0

        if change > 10:
            return 'increasing'
        elif change < -10:
            return 'decreasing'
        else:
            return 'stable'

    def calculate_competitor_analysis(self):
        """
        Calculate competitor analysis by ZIP code.
        """
        logger.info("Calculating competitor analysis...")

        from config.settings import CHICAGO_ZIP_CODES

        analyses_created = 0

        for zip_code in CHICAGO_ZIP_CODES:
            try:
                # Get all clinics in ZIP
                clinics = self.session.query(Clinic).filter(
                    Clinic.zip_code == zip_code,
                    Clinic.is_active == True
                ).all()

                total_clinics = len(clinics)

                if total_clinics == 0:
                    continue

                # Count by type
                by_type = {}
                for clinic in clinics:
                    clinic_type = clinic.clinic_type or 'unknown'
                    by_type[clinic_type] = by_type.get(clinic_type, 0) + 1

                # Calculate metrics
                ratings = [
                    (c.google_rating or c.yelp_rating or 0)
                    for c in clinics
                ]
                review_counts = [
                    (c.google_review_count or 0) + (c.yelp_review_count or 0)
                    for c in clinics
                ]

                avg_rating = np.mean(ratings) if ratings else 0
                avg_review_count = np.mean(review_counts) if review_counts else 0

                # Top 3 market share
                sorted_reviews = sorted(review_counts, reverse=True)
                top_3_reviews = sum(sorted_reviews[:3])
                total_reviews = sum(review_counts)
                top_3_share = (top_3_reviews / total_reviews * 100) if total_reviews > 0 else 0

                # High-rated count
                high_rated = sum(1 for r in ratings if r >= 4.0)

                # Low review count
                low_review = sum(1 for c in review_counts if c < 10)

                # Save analysis
                existing = self.session.query(CompetitorAnalysis).filter_by(
                    zip_code=zip_code,
                    calculation_date=self.calculation_date
                ).first()

                if existing:
                    existing.total_clinics = total_clinics
                    existing.by_type = by_type
                    existing.avg_rating = avg_rating
                    existing.avg_review_count = avg_review_count
                    existing.top_3_market_share = top_3_share
                    existing.high_rated_count = high_rated
                    existing.low_review_count = low_review
                else:
                    analysis = CompetitorAnalysis(
                        zip_code=zip_code,
                        calculation_date=self.calculation_date,
                        total_clinics=total_clinics,
                        by_type=by_type,
                        avg_rating=avg_rating,
                        avg_review_count=avg_review_count,
                        top_3_market_share=top_3_share,
                        high_rated_count=high_rated,
                        low_review_count=low_review
                    )
                    self.session.add(analysis)
                    analyses_created += 1

            except Exception as e:
                logger.error(f"Failed to analyze {zip_code}: {e}")

        self.session.commit()

        logger.success(f"✓ Calculated {analyses_created} competitor analyses")

    def run_all_calculations(self):
        """
        Run all analysis calculations.
        """
        logger.info("Starting analysis engine...")

        self.calculate_visibility_scores()
        self.calculate_demand_metrics()
        self.calculate_competitor_analysis()

        logger.success("✓ All calculations complete")

    def close(self):
        """Close database session."""
        self.session.close()


if __name__ == "__main__":
    from src.database.init_db import setup_logging

    setup_logging()

    engine = ScoringEngine()
    try:
        engine.run_all_calculations()
    finally:
        engine.close()
