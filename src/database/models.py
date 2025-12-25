"""
Database models for Chicago Clinic Demand Intelligence system.
"""

from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, DateTime,
    Boolean, Text, ForeignKey, Index, Date, JSON
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()


class Clinic(Base):
    """
    Master clinic table combining data from Google Places and Yelp.
    """
    __tablename__ = 'clinics'

    id = Column(Integer, primary_key=True)
    # Identifiers
    google_place_id = Column(String(255), unique=True, index=True)
    yelp_business_id = Column(String(255), unique=True, index=True)

    # Basic Information
    name = Column(String(500), nullable=False)
    address = Column(String(500))
    city = Column(String(100), index=True)
    state = Column(String(50))
    zip_code = Column(String(10), index=True)
    phone = Column(String(50))
    website = Column(String(500))

    # Location
    latitude = Column(Float)
    longitude = Column(Float)

    # Categorization
    clinic_type = Column(String(100), index=True)
    categories = Column(JSON)  # List of all categories

    # Google Places Metrics
    google_rating = Column(Float)
    google_review_count = Column(Integer)
    google_price_level = Column(Integer)

    # Yelp Metrics
    yelp_rating = Column(Float)
    yelp_review_count = Column(Integer)
    yelp_price_level = Column(String(10))

    # Operating Hours
    hours_json = Column(JSON)
    is_open_now = Column(Boolean)

    # Status
    is_active = Column(Boolean, default=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    reviews = relationship('Review', back_populates='clinic', cascade='all, delete-orphan')
    visibility_scores = relationship('VisibilityScore', back_populates='clinic', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Clinic(name='{self.name}', zip='{self.zip_code}')>"


class Review(Base):
    """
    Reviews from Google Places and Yelp.
    """
    __tablename__ = 'reviews'

    id = Column(Integer, primary_key=True)
    clinic_id = Column(Integer, ForeignKey('clinics.id'), nullable=False, index=True)

    # Source
    source = Column(String(50), nullable=False)  # 'google' or 'yelp'
    review_id = Column(String(255), unique=True)

    # Review Content
    author_name = Column(String(255))
    rating = Column(Float, nullable=False)
    text = Column(Text)
    review_date = Column(DateTime)

    # Sentiment Analysis (to be computed)
    sentiment_score = Column(Float)  # -1 to 1
    sentiment_label = Column(String(20))  # positive, neutral, negative

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    clinic = relationship('Clinic', back_populates='reviews')

    # Indexes
    __table_args__ = (
        Index('idx_clinic_source', 'clinic_id', 'source'),
        Index('idx_review_date', 'review_date'),
    )

    def __repr__(self):
        return f"<Review(clinic_id={self.clinic_id}, rating={self.rating}, source='{self.source}')>"


class SearchTrend(Base):
    """
    Google Trends data for service keywords.
    """
    __tablename__ = 'search_trends'

    id = Column(Integer, primary_key=True)

    # Keyword and Location
    keyword = Column(String(255), nullable=False, index=True)
    service_category = Column(String(100), index=True)
    location = Column(String(100))  # Chicago, IL

    # Trend Data
    date = Column(Date, nullable=False, index=True)
    interest_score = Column(Integer)  # 0-100 from Google Trends

    # Rolling averages for analysis
    interest_7day_avg = Column(Float)
    interest_30day_avg = Column(Float)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index('idx_keyword_date', 'keyword', 'date'),
        Index('idx_category_date', 'service_category', 'date'),
    )

    def __repr__(self):
        return f"<SearchTrend(keyword='{self.keyword}', date={self.date}, score={self.interest_score})>"


class VisibilityScore(Base):
    """
    Calculated visibility scores for clinics.
    Daily snapshot of visibility metrics.
    """
    __tablename__ = 'visibility_scores'

    id = Column(Integer, primary_key=True)
    clinic_id = Column(Integer, ForeignKey('clinics.id'), nullable=False, index=True)
    calculation_date = Column(Date, nullable=False, index=True)

    # Component Scores (0-100 scale)
    rating_score = Column(Float)  # Based on ratings from both sources
    review_volume_score = Column(Float)  # Based on number of reviews
    recency_score = Column(Float)  # Based on recent review activity
    geographic_score = Column(Float)  # Based on location density

    # Composite Visibility Score (0-100)
    overall_visibility_score = Column(Float, index=True)

    # Ranking
    local_rank = Column(Integer)  # Rank within ZIP code
    city_rank = Column(Integer)  # Rank within city

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    clinic = relationship('Clinic', back_populates='visibility_scores')

    # Indexes
    __table_args__ = (
        Index('idx_clinic_date', 'clinic_id', 'calculation_date'),
    )

    def __repr__(self):
        return f"<VisibilityScore(clinic_id={self.clinic_id}, score={self.overall_visibility_score})>"


class DemandMetric(Base):
    """
    Demand metrics by service category and location.
    """
    __tablename__ = 'demand_metrics'

    id = Column(Integer, primary_key=True)

    # Dimensions
    service_category = Column(String(100), nullable=False, index=True)
    zip_code = Column(String(10), index=True)
    calculation_date = Column(Date, nullable=False, index=True)

    # Search Demand Metrics
    search_demand_index = Column(Float)  # Normalized demand score
    search_volume_trend = Column(String(20))  # increasing, stable, decreasing

    # Supply Metrics
    clinic_count = Column(Integer)  # Number of clinics in area
    avg_rating = Column(Float)
    total_review_count = Column(Integer)

    # Demand-Supply Ratio
    demand_to_competition_ratio = Column(Float, index=True)  # Higher = more opportunity

    # Opportunity Score (composite metric)
    opportunity_score = Column(Float, index=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index('idx_category_zip_date', 'service_category', 'zip_code', 'calculation_date'),
    )

    def __repr__(self):
        return f"<DemandMetric(category='{self.service_category}', zip='{self.zip_code}')>"


class CompetitorAnalysis(Base):
    """
    Competitor density and analysis by area.
    """
    __tablename__ = 'competitor_analysis'

    id = Column(Integer, primary_key=True)

    # Location
    zip_code = Column(String(10), nullable=False, index=True)
    calculation_date = Column(Date, nullable=False, index=True)

    # Competitor Metrics
    total_clinics = Column(Integer)
    by_type = Column(JSON)  # Breakdown by clinic type

    # Market Concentration
    avg_rating = Column(Float)
    avg_review_count = Column(Float)
    top_3_market_share = Column(Float)  # % of reviews from top 3 clinics

    # Market Maturity Indicators
    high_rated_count = Column(Integer)  # Clinics with 4+ rating
    low_review_count = Column(Integer)  # Clinics with <10 reviews

    # Geographic Coverage
    clinic_density_per_sqkm = Column(Float)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index('idx_zip_date', 'zip_code', 'calculation_date'),
    )

    def __repr__(self):
        return f"<CompetitorAnalysis(zip='{self.zip_code}', clinics={self.total_clinics})>"


class DataCollectionLog(Base):
    """
    Log of data collection runs for monitoring and debugging.
    """
    __tablename__ = 'data_collection_logs'

    id = Column(Integer, primary_key=True)

    # Collection Info
    collection_type = Column(String(50), nullable=False)  # google_places, yelp, trends
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    status = Column(String(20))  # success, failed, partial

    # Results
    records_collected = Column(Integer)
    records_updated = Column(Integer)
    records_failed = Column(Integer)

    # Error Info
    error_message = Column(Text)
    error_details = Column(JSON)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<DataCollectionLog(type='{self.collection_type}', status='{self.status}')>"
