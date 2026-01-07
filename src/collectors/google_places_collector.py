"""
Google Places API data collector for clinic information.
"""

import googlemaps
import time
from datetime import datetime
from loguru import logger
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from config.settings import (
    GOOGLE_PLACES_API_KEY,
    TARGET_CITY,
    TARGET_STATE,
    CHICAGO_ZIP_CODES,
    SEARCH_RADIUS_METERS,
    API_RATE_LIMIT_DELAY,
    MAX_RETRIES
)
from src.database.models import Clinic, Review, DataCollectionLog
from src.database.init_db import get_session


class GooglePlacesCollector:
    """
    Collector for Google Places API data.
    """

    def __init__(self):
        self.client = googlemaps.Client(key=GOOGLE_PLACES_API_KEY)
        self.session = get_session()
        self.collected_count = 0
        self.updated_count = 0
        self.failed_count = 0

    def geocode_location(self, location_string):
        """
        Geocode a location string to lat/lng.
        """
        try:
            result = self.client.geocode(location_string)
            if result:
                location = result[0]['geometry']['location']
                return location['lat'], location['lng']
        except Exception as e:
            logger.error(f"Geocoding failed for {location_string}: {e}")
        return None, None

    def search_clinics_nearby(self, latitude, longitude, clinic_type='health'):
        """
        Search for clinics near a specific location.
        """
        try:
            results = self.client.places_nearby(
                location=(latitude, longitude),
                radius=SEARCH_RADIUS_METERS,
                type=clinic_type,
                keyword='clinic'
            )

            return results.get('results', [])

        except Exception as e:
            logger.error(f"Places search failed: {e}")
            return []

    def get_place_details(self, place_id):
        """
        Get detailed information about a place.
        """
        try:
            result = self.client.place(
                place_id=place_id,
                fields=[
                    'name', 'formatted_address', 'geometry', 'rating',
                    'user_ratings_total', 'formatted_phone_number', 'website',
                    'opening_hours', 'reviews', 'types', 'price_level',
                    'address_components'
                ]
            )

            return result.get('result', {})

        except Exception as e:
            logger.error(f"Place details failed for {place_id}: {e}")
            return {}

    def extract_address_components(self, address_components):
        """
        Extract structured address data from address components.
        """
        address_data = {
            'street': '',
            'city': '',
            'state': '',
            'zip_code': ''
        }

        for component in address_components:
            types = component.get('types', [])

            if 'postal_code' in types:
                address_data['zip_code'] = component['long_name']
            elif 'locality' in types:
                address_data['city'] = component['long_name']
            elif 'administrative_area_level_1' in types:
                address_data['state'] = component['short_name']

        return address_data

    def save_clinic(self, place_data):
        """
        Save or update clinic data in the database.
        """
        try:
            place_id = place_data.get('place_id')

            # Check if clinic already exists
            clinic = self.session.query(Clinic).filter_by(
                google_place_id=place_id
            ).first()

            # Extract address components
            address_components = place_data.get('address_components', [])
            addr_data = self.extract_address_components(address_components)

            location = place_data.get('geometry', {}).get('location', {})

            if clinic:
                # Update existing clinic
                clinic.name = place_data.get('name')
                clinic.address = place_data.get('formatted_address')
                clinic.city = addr_data['city']
                clinic.state = addr_data['state']
                clinic.zip_code = addr_data['zip_code']
                clinic.phone = place_data.get('formatted_phone_number')
                clinic.website = place_data.get('website')
                clinic.latitude = location.get('lat')
                clinic.longitude = location.get('lng')
                clinic.google_rating = place_data.get('rating')
                clinic.google_review_count = place_data.get('user_ratings_total')
                clinic.google_price_level = place_data.get('price_level')
                clinic.categories = place_data.get('types', [])
                clinic.hours_json = place_data.get('opening_hours', {})
                clinic.last_updated = datetime.utcnow()

                self.updated_count += 1
                action = "Updated"

            else:
                # Create new clinic
                clinic = Clinic(
                    google_place_id=place_id,
                    name=place_data.get('name'),
                    address=place_data.get('formatted_address'),
                    city=addr_data['city'],
                    state=addr_data['state'],
                    zip_code=addr_data['zip_code'],
                    phone=place_data.get('formatted_phone_number'),
                    website=place_data.get('website'),
                    latitude=location.get('lat'),
                    longitude=location.get('lng'),
                    google_rating=place_data.get('rating'),
                    google_review_count=place_data.get('user_ratings_total'),
                    google_price_level=place_data.get('price_level'),
                    categories=place_data.get('types', []),
                    hours_json=place_data.get('opening_hours', {}),
                    is_active=True
                )

                self.session.add(clinic)
                self.collected_count += 1
                action = "Added"

            self.session.commit()

            # Save reviews
            self.save_reviews(clinic.id, place_data.get('reviews', []))

            logger.info(f"{action} clinic: {clinic.name} ({addr_data['zip_code']})")

            return clinic

        except Exception as e:
            self.session.rollback()
            self.failed_count += 1
            logger.error(f"Failed to save clinic: {e}")
            return None

    def save_reviews(self, clinic_id, reviews_data):
        """
        Save reviews for a clinic.
        """
        for review_data in reviews_data:
            try:
                # Create unique review ID
                review_id = f"google_{clinic_id}_{review_data.get('time', 0)}"

                # Check if review exists
                existing = self.session.query(Review).filter_by(
                    review_id=review_id
                ).first()

                if not existing:
                    review = Review(
                        clinic_id=clinic_id,
                        source='google',
                        review_id=review_id,
                        author_name=review_data.get('author_name'),
                        rating=review_data.get('rating'),
                        text=review_data.get('text'),
                        review_date=datetime.fromtimestamp(review_data.get('time', 0))
                    )
                    self.session.add(review)

            except Exception as e:
                logger.error(f"Failed to save review: {e}")

        self.session.commit()

    def collect_by_zip_code(self, zip_code):
        """
        Collect clinic data for a specific ZIP code.
        """
        logger.info(f"Collecting data for ZIP code: {zip_code}")

        # Geocode ZIP code
        location_string = f"{zip_code}, {TARGET_CITY}, {TARGET_STATE}"
        lat, lng = self.geocode_location(location_string)

        if not lat or not lng:
            logger.warning(f"Could not geocode {zip_code}")
            return

        # Search for clinics
        places = self.search_clinics_nearby(lat, lng)
        logger.info(f"Found {len(places)} places in {zip_code}")

        for place in places:
            place_id = place.get('place_id')

            # Get detailed information
            details = self.get_place_details(place_id)

            if details:
                self.save_clinic(details)

            # Rate limiting
            time.sleep(API_RATE_LIMIT_DELAY)

    def collect_all_chicago(self):
        """
        Collect data for all Chicago ZIP codes.
        """
        log = DataCollectionLog(
            collection_type='google_places',
            start_time=datetime.utcnow(),
            status='running'
        )
        self.session.add(log)
        self.session.commit()

        try:
            logger.info(f"Starting Google Places collection for {len(CHICAGO_ZIP_CODES)} ZIP codes")

            for zip_code in CHICAGO_ZIP_CODES:
                try:
                    self.collect_by_zip_code(zip_code)
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
                f"✓ Collection complete: {self.collected_count} new, "
                f"{self.updated_count} updated, {self.failed_count} failed"
            )

        except Exception as e:
            log.end_time = datetime.utcnow()
            log.status = 'failed'
            log.error_message = str(e)
            self.session.commit()
            logger.error(f"Collection failed: {e}")
            raise

    def close(self):
        """Close database session."""
        self.session.close()


if __name__ == "__main__":
    from src.database.init_db import setup_logging

    setup_logging()

    collector = GooglePlacesCollector()
    try:
        collector.collect_all_chicago()
    finally:
        collector.close()
