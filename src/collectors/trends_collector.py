"""
Google Trends data collector for search demand analysis.
"""

from pytrends.request import TrendReq
import pandas as pd
from datetime import datetime, timedelta
from loguru import logger
import sys
from pathlib import Path
import time

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from config.settings import (
    TARGET_CITY,
    TARGET_STATE,
    SERVICE_KEYWORDS,
    SERVICE_CATEGORIES,
    API_RATE_LIMIT_DELAY
)
from src.database.models import SearchTrend, DataCollectionLog
from src.database.init_db import get_session


class GoogleTrendsCollector:
    """
    Collector for Google Trends search demand data.
    """

    def __init__(self):
        self.pytrends = TrendReq(
            hl='en-US',
            tz=360,
            timeout=(10, 25),
            retries=2,
            backoff_factor=0.1
        )
        self.session = get_session()
        self.collected_count = 0
        self.failed_count = 0

        # Geographic code for Chicago
        self.geo_code = 'US-IL-674'  # Chicago DMA

    def get_interest_over_time(self, keyword, timeframe='today 3-m', category=None):
        """
        Get interest over time for a keyword.
        """
        try:
            # Build payload
            self.pytrends.build_payload(
                [keyword],
                cat=0,
                timeframe=timeframe,
                geo=self.geo_code,
                gprop=''
            )

            # Get data
            interest_df = self.pytrends.interest_over_time()

            if interest_df.empty:
                logger.warning(f"No data for keyword: {keyword}")
                return None

            # Remove 'isPartial' column if present
            if 'isPartial' in interest_df.columns:
                interest_df = interest_df.drop(columns=['isPartial'])

            # Rename column to 'interest'
            interest_df = interest_df.rename(columns={keyword: 'interest'})

            # Add metadata
            interest_df['keyword'] = keyword
            interest_df['category'] = category or 'general'

            return interest_df

        except Exception as e:
            logger.error(f"Failed to get trends for '{keyword}': {e}")
            return None

    def calculate_rolling_averages(self, df):
        """
        Calculate 7-day and 30-day rolling averages.
        """
        df['interest_7day_avg'] = df['interest'].rolling(window=7, min_periods=1).mean()
        df['interest_30day_avg'] = df['interest'].rolling(window=30, min_periods=1).mean()
        return df

    def save_trends_data(self, trends_df):
        """
        Save trends data to database.
        """
        try:
            for index, row in trends_df.iterrows():
                # Check if record exists
                existing = self.session.query(SearchTrend).filter_by(
                    keyword=row['keyword'],
                    date=index.date()
                ).first()

                if existing:
                    # Update
                    existing.interest_score = row['interest']
                    existing.interest_7day_avg = row.get('interest_7day_avg')
                    existing.interest_30day_avg = row.get('interest_30day_avg')
                else:
                    # Create new
                    trend = SearchTrend(
                        keyword=row['keyword'],
                        service_category=row['category'],
                        location=f"{TARGET_CITY}, {TARGET_STATE}",
                        date=index.date(),
                        interest_score=row['interest'],
                        interest_7day_avg=row.get('interest_7day_avg'),
                        interest_30day_avg=row.get('interest_30day_avg')
                    )
                    self.session.add(trend)
                    self.collected_count += 1

            self.session.commit()

        except Exception as e:
            self.session.rollback()
            self.failed_count += 1
            logger.error(f"Failed to save trends data: {e}")

    def collect_keyword(self, keyword, category=None, timeframe='today 3-m'):
        """
        Collect trend data for a single keyword.
        """
        logger.info(f"Collecting trends for: {keyword} ({category})")

        trends_df = self.get_interest_over_time(keyword, timeframe, category)

        if trends_df is not None:
            # Calculate rolling averages
            trends_df = self.calculate_rolling_averages(trends_df)

            # Save to database
            self.save_trends_data(trends_df)

            logger.info(f"Saved {len(trends_df)} records for '{keyword}'")

        # Rate limiting
        time.sleep(API_RATE_LIMIT_DELAY * 2)  # Google Trends has stricter limits

    def collect_all_keywords(self, timeframe='today 3-m'):
        """
        Collect trend data for all configured keywords.
        """
        log = DataCollectionLog(
            collection_type='google_trends',
            start_time=datetime.utcnow(),
            status='running'
        )
        self.session.add(log)
        self.session.commit()

        try:
            logger.info("Starting Google Trends collection")

            # Collect for flat keyword list
            for keyword in SERVICE_KEYWORDS:
                try:
                    self.collect_keyword(keyword, category='general', timeframe=timeframe)
                except Exception as e:
                    logger.error(f"Failed to collect '{keyword}': {e}")
                    self.failed_count += 1

            # Collect for categorized keywords
            for category, keywords in SERVICE_CATEGORIES.items():
                for keyword in keywords:
                    try:
                        self.collect_keyword(keyword, category=category, timeframe=timeframe)
                    except Exception as e:
                        logger.error(f"Failed to collect '{keyword}' ({category}): {e}")
                        self.failed_count += 1

            # Update log
            log.end_time = datetime.utcnow()
            log.status = 'success'
            log.records_collected = self.collected_count
            log.records_failed = self.failed_count
            self.session.commit()

            logger.success(
                f"✓ Trends collection complete: {self.collected_count} records, "
                f"{self.failed_count} failed"
            )

        except Exception as e:
            log.end_time = datetime.utcnow()
            log.status = 'failed'
            log.error_message = str(e)
            self.session.commit()
            logger.error(f"Trends collection failed: {e}")
            raise

    def get_trending_keywords(self, pn='united_states'):
        """
        Get currently trending health-related searches.
        """
        try:
            trending_searches_df = self.pytrends.trending_searches(pn=pn)
            logger.info(f"Current trending searches: {trending_searches_df.head(10).values.flatten().tolist()}")
            return trending_searches_df
        except Exception as e:
            logger.error(f"Failed to get trending searches: {e}")
            return None

    def close(self):
        """Close database session."""
        self.session.close()


if __name__ == "__main__":
    from src.database.init_db import setup_logging

    setup_logging()

    collector = GoogleTrendsCollector()
    try:
        # Collect data for the last 3 months
        collector.collect_all_keywords(timeframe='today 3-m')

        # Show trending searches
        collector.get_trending_keywords()
    finally:
        collector.close()
