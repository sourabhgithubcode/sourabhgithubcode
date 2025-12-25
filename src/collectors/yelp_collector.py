"""
Yelp API data collector for clinic information and reviews.
"""

import requests
import time
from datetime import datetime
from loguru import logger
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from config.settings import (
    YELP_API_KEY,
    TARGET_CITY,
    TARGET_STATE,
    CHICAGO_ZIP_CODES,
    API_RATE_LIMIT_DELAY,
    MAX_RETRIES
)
from src.database.models import Clinic, Review, DataCollectionLog
from src.database.init_db import get_session


class YelpCollector:
    """
    Collector for Yelp Fusion API data.
    """

    def __init__(self):
        self.api_key = YELP_API_KEY
        self.base_url = "https://api.yelp.com/v3"
        self.headers = {
            'Authorization': f'Bearer {self.api_key}'
        }
        self.session = get_session()
        self.collected_count = 0
        self.updated_count = 0
        self.failed_count = 0

    def search_businesses(self, location, categories='health', limit=50):
        """
        Search for businesses using Yelp API.
        """
        url = f"{self.base_url}/businesses/search"

        params = {
            'location': location,
            'categories': categories,
            'term': 'clinic',
            'limit': limit
        }

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()

            data = response.json()
            return data.get('businesses', [])

        except Exception as e:
            logger.error(f"Yelp search failed for {location}: {e}")
            return []

    def get_business_details(self, business_id):
        """
        Get detailed business information.
        """
        url = f"{self.base_url}/businesses/{business_id}"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()

            return response.json()

        except Exception as e:
            logger.error(f"Failed to get details for {business_id}: {e}")
            return {}

    def get_reviews(self, business_id):
        """
        Get reviews for a business.
        """
        url = f"{self.base_url}/businesses/{business_id}/reviews"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()

            data = response.json()
            return data.get('reviews', [])

        except Exception as e:
            logger.error(f"Failed to get reviews for {business_id}: {e}")
            return []

    def match_or_create_clinic(self, business_data):
        """
        Match Yelp business to existing clinic or create new one.
        """
        try:
            business_id = business_data.get('id')
            name = business_data.get('name')
            location = business_data.get('location', {})

            # Try to find existing clinic by Yelp ID
            clinic = self.session.query(Clinic).filter_by(
                yelp_business_id=business_id
            ).first()

            # If not found, try to match by name and address
            if not clinic:
                zip_code = location.get('zip_code')
                clinic = self.session.query(Clinic).filter(
                    Clinic.name.ilike(f"%{name}%"),
                    Clinic.zip_code == zip_code
                ).first()

            coordinates = business_data.get('coordinates', {})
            categories = [cat['title'] for cat in business_data.get('categories', [])]

            if clinic:
                # Update existing clinic with Yelp data
                clinic.yelp_business_id = business_id
                clinic.yelp_rating = business_data.get('rating')
                clinic.yelp_review_count = business_data.get('review_count')
                clinic.yelp_price_level = business_data.get('price')

                # Update if Google data doesn't exist
                if not clinic.latitude:
                    clinic.latitude = coordinates.get('latitude')
                if not clinic.longitude:
                    clinic.longitude = coordinates.get('longitude')
                if not clinic.phone:
                    clinic.phone = business_data.get('phone')
                if not clinic.website:
                    clinic.website = business_data.get('url')

                clinic.last_updated = datetime.utcnow()
                self.updated_count += 1
                action = "Updated"

            else:
                # Create new clinic
                clinic = Clinic(
                    yelp_business_id=business_id,
                    name=name,
                    address=location.get('address1'),
                    city=location.get('city'),
                    state=location.get('state'),
                    zip_code=location.get('zip_code'),
                    phone=business_data.get('phone'),
                    website=business_data.get('url'),
                    latitude=coordinates.get('latitude'),
                    longitude=coordinates.get('longitude'),
                    yelp_rating=business_data.get('rating'),
                    yelp_review_count=business_data.get('review_count'),
                    yelp_price_level=business_data.get('price'),
                    categories=categories,
                    is_active=True
                )

                self.session.add(clinic)
                self.collected_count += 1
                action = "Added"

            self.session.commit()

            logger.info(f"{action} clinic from Yelp: {name} ({location.get('zip_code')})")

            return clinic

        except Exception as e:
            self.session.rollback()
            self.failed_count += 1
            logger.error(f"Failed to save Yelp clinic: {e}")
            return None

    def save_reviews(self, clinic_id, business_id):
        """
        Fetch and save reviews for a business.
        """
        reviews_data = self.get_reviews(business_id)

        for review_data in reviews_data:
            try:
                review_id = f"yelp_{review_data.get('id')}"

                # Check if review exists
                existing = self.session.query(Review).filter_by(
                    review_id=review_id
                ).first()

                if not existing:
                    # Parse date
                    time_created = review_data.get('time_created')
                    review_date = datetime.fromisoformat(time_created.replace('Z', '+00:00'))

                    review = Review(
                        clinic_id=clinic_id,
                        source='yelp',
                        review_id=review_id,
                        author_name=review_data.get('user', {}).get('name'),
                        rating=review_data.get('rating'),
                        text=review_data.get('text'),
                        review_date=review_date
                    )

                    self.session.add(review)

            except Exception as e:
                logger.error(f"Failed to save Yelp review: {e}")

        self.session.commit()

    def collect_by_location(self, location):
        """
        Collect Yelp data for a specific location.
        """
        logger.info(f"Collecting Yelp data for: {location}")

        # Search for businesses
        businesses = self.search_businesses(location)
        logger.info(f"Found {len(businesses)} businesses")

        for business in businesses:
            business_id = business.get('id')

            # Get detailed information
            details = self.get_business_details(business_id)

            if details:
                clinic = self.match_or_create_clinic(details)

                if clinic:
                    # Get and save reviews
                    self.save_reviews(clinic.id, business_id)

            # Rate limiting
            time.sleep(API_RATE_LIMIT_DELAY)

    def collect_all_chicago(self):
        """
        Collect Yelp data for all Chicago ZIP codes.
        """
        log = DataCollectionLog(
            collection_type='yelp',
            start_time=datetime.utcnow(),
            status='running'
        )
        self.session.add(log)
        self.session.commit()

        try:
            logger.info(f"Starting Yelp collection for {len(CHICAGO_ZIP_CODES)} ZIP codes")

            for zip_code in CHICAGO_ZIP_CODES:
                try:
                    location = f"{zip_code}, {TARGET_CITY}, {TARGET_STATE}"
                    self.collect_by_location(location)
                except Exception as e:
                    logger.error(f"Failed to collect {zip_code}: {e}")
                    self.failed_count += 1

            # Update log
            log.end_time = datetime.utcnow()
            log.status = 'success'
            log.records_collected = self.collected_count
            log.records_updated = self.updated_count
            log.records_failed = self.failed_count
            self.session.commit()

            logger.success(
                f"✓ Yelp collection complete: {self.collected_count} new, "
                f"{self.updated_count} updated, {self.failed_count} failed"
            )

        except Exception as e:
            log.end_time = datetime.utcnow()
            log.status = 'failed'
            log.error_message = str(e)
            self.session.commit()
            logger.error(f"Yelp collection failed: {e}")
            raise

    def close(self):
        """Close database session."""
        self.session.close()


if __name__ == "__main__":
    from src.database.init_db import setup_logging

    setup_logging()

    collector = YelpCollector()
    try:
        collector.collect_all_chicago()
    finally:
        collector.close()
