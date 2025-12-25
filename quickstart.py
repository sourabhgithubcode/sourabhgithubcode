#!/usr/bin/env python
"""
Quick Start Script for Chicago Clinic Demand Intelligence

This script helps you get started quickly by:
1. Validating your configuration
2. Initializing the database
3. Running a test collection
4. Generating sample insights
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config.settings import validate_config, get_database_url
from src.database.init_db import create_database, setup_logging
from loguru import logger


def welcome_message():
    """Display welcome message."""
    print("=" * 70)
    print("  CHICAGO CLINIC DEMAND INTELLIGENCE - QUICK START")
    print("=" * 70)
    print()
    print("This script will guide you through setting up the system.")
    print()


def check_configuration():
    """Validate configuration."""
    print("Step 1: Checking configuration...")
    print("-" * 70)

    is_valid, errors = validate_config()

    if is_valid:
        print("✓ Configuration is valid")
        print(f"  Database: {get_database_url().split('@')[-1]}")
        return True
    else:
        print("✗ Configuration errors found:")
        for error in errors:
            print(f"  - {error}")
        print()
        print("Please fix the errors in your .env file and try again.")
        print("See .env.example for reference.")
        return False


def setup_database():
    """Initialize database."""
    print()
    print("Step 2: Setting up database...")
    print("-" * 70)

    try:
        create_database()
        print("✓ Database setup complete")
        return True
    except Exception as e:
        print(f"✗ Database setup failed: {e}")
        return False


def test_collectors():
    """Test data collectors with a small sample."""
    print()
    print("Step 3: Testing data collectors...")
    print("-" * 70)
    print()
    print("We'll collect data for just one ZIP code to verify everything works.")
    print()

    # Import here to avoid errors if config is invalid
    from src.collectors.google_places_collector import GooglePlacesCollector
    from src.collectors.yelp_collector import YelpCollector

    # Test Google Places
    print("Testing Google Places API...")
    try:
        collector = GooglePlacesCollector()
        collector.collect_by_zip_code('60601')  # Downtown Chicago
        collector.close()
        print("✓ Google Places API working")
    except Exception as e:
        print(f"✗ Google Places API error: {e}")
        return False

    # Test Yelp
    print("Testing Yelp API...")
    try:
        collector = YelpCollector()
        collector.collect_by_location('60601, Chicago, IL')
        collector.close()
        print("✓ Yelp API working")
    except Exception as e:
        print(f"✗ Yelp API error: {e}")
        return False

    return True


def show_sample_data():
    """Show sample data from database."""
    print()
    print("Step 4: Viewing sample data...")
    print("-" * 70)

    from src.database.init_db import get_session
    from src.database.models import Clinic

    session = get_session()

    try:
        # Get sample clinics
        clinics = session.query(Clinic).limit(5).all()

        if clinics:
            print(f"\n✓ Found {len(clinics)} clinics in database:")
            print()
            for clinic in clinics:
                print(f"  • {clinic.name}")
                print(f"    {clinic.address}")
                print(f"    Rating: {clinic.google_rating or clinic.yelp_rating or 'N/A'}")
                print()
        else:
            print("  No clinics found yet. Run full collection to populate data.")

    except Exception as e:
        print(f"✗ Error reading data: {e}")
    finally:
        session.close()


def next_steps():
    """Display next steps."""
    print()
    print("=" * 70)
    print("  NEXT STEPS")
    print("=" * 70)
    print()
    print("1. Run full data collection:")
    print("   python src/utils/scheduler.py --mode once")
    print()
    print("2. View data in database:")
    print("   psql -U clinic_user -d clinic_intelligence")
    print("   or")
    print("   sqlite3 data/clinic_intelligence.db")
    print()
    print("3. Set up Power BI dashboard:")
    print("   See dashboards/POWERBI_SETUP.md")
    print()
    print("4. Schedule daily refresh:")
    print("   python src/utils/scheduler.py --mode scheduled")
    print()
    print("For detailed documentation, see:")
    print("  - docs/SETUP_GUIDE.md")
    print("  - PROJECT_README.md")
    print()
    print("=" * 70)
    print()


def main():
    """Main quickstart flow."""
    setup_logging()
    welcome_message()

    # Step 1: Configuration
    if not check_configuration():
        sys.exit(1)

    # Step 2: Database
    if not setup_database():
        sys.exit(1)

    # Step 3: Test collectors
    print()
    run_test = input("Run test data collection? (y/n): ").lower()
    if run_test == 'y':
        if not test_collectors():
            print()
            print("⚠ Some tests failed. Check your API keys and try again.")
        else:
            # Step 4: Show sample data
            show_sample_data()

    # Next steps
    next_steps()

    print("✓ Quick start complete!")
    print()


if __name__ == "__main__":
    main()
