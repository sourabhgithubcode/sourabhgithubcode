"""
Configuration management for Chicago Clinic Demand Intelligence system.
Loads settings from environment variables with sensible defaults.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data'
LOG_DIR = BASE_DIR / 'logs'

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)
(DATA_DIR / 'raw').mkdir(exist_ok=True)
(DATA_DIR / 'processed').mkdir(exist_ok=True)

# API Configuration
GOOGLE_PLACES_API_KEY = os.getenv('GOOGLE_PLACES_API_KEY', '')
YELP_API_KEY = os.getenv('YELP_API_KEY', '')

# Database Configuration
DB_TYPE = os.getenv('DB_TYPE', 'sqlite')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', 5432))
DB_NAME = os.getenv('DB_NAME', 'clinic_intelligence')
DB_USER = os.getenv('DB_USER', '')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
SQLITE_DB_PATH = os.getenv('SQLITE_DB_PATH', 'data/clinic_intelligence.db')

# Geographic Configuration
TARGET_CITY = os.getenv('TARGET_CITY', 'Chicago')
TARGET_STATE = os.getenv('TARGET_STATE', 'IL')
TARGET_COUNTRY = os.getenv('TARGET_COUNTRY', 'US')

# Chicago ZIP codes for targeted analysis
CHICAGO_ZIP_CODES = [
    '60601', '60602', '60603', '60604', '60605', '60606', '60607', '60608',
    '60609', '60610', '60611', '60612', '60613', '60614', '60615', '60616',
    '60617', '60618', '60619', '60620', '60621', '60622', '60623', '60624',
    '60625', '60626', '60628', '60629', '60630', '60631', '60632', '60633',
    '60634', '60636', '60637', '60638', '60639', '60640', '60641', '60642',
    '60643', '60644', '60645', '60646', '60647', '60649', '60651', '60652',
    '60653', '60654', '60655', '60656', '60657', '60659', '60660', '60661'
]

# Search Parameters
SEARCH_RADIUS_METERS = int(os.getenv('SEARCH_RADIUS_METERS', 5000))
MAX_RESULTS_PER_QUERY = int(os.getenv('MAX_RESULTS_PER_QUERY', 60))

# Clinic Types
CLINIC_TYPES = os.getenv(
    'CLINIC_TYPES',
    'urgent_care,primary_care,specialty_clinic,dental_clinic,physical_therapy'
).split(',')

# Service Keywords for Trends Analysis
SERVICE_KEYWORDS = os.getenv(
    'SERVICE_KEYWORDS',
    'urgent care,walk-in clinic,family doctor,pediatric clinic,dental emergency,physical therapy,medical clinic'
).split(',')

# Additional service categories for demand analysis
SERVICE_CATEGORIES = {
    'urgent_care': ['urgent care', 'walk-in clinic', 'emergency clinic'],
    'primary_care': ['family doctor', 'primary care physician', 'general practitioner'],
    'pediatric': ['pediatric clinic', 'children doctor', 'pediatrician'],
    'dental': ['dental clinic', 'dentist', 'dental emergency'],
    'specialty': ['physical therapy', 'dermatology', 'cardiology', 'orthopedic']
}

# Scheduling
DAILY_REFRESH_TIME = os.getenv('DAILY_REFRESH_TIME', '02:00')
DATA_RETENTION_DAYS = int(os.getenv('DATA_RETENTION_DAYS', 365))

# Logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = LOG_DIR / os.getenv('LOG_FILE', 'clinic_intelligence.log').split('/')[-1]

# Rate Limiting
API_RATE_LIMIT_DELAY = float(os.getenv('API_RATE_LIMIT_DELAY', 1.0))
MAX_RETRIES = int(os.getenv('MAX_RETRIES', 3))

# Database connection string
def get_database_url():
    """Generate database connection URL based on configuration."""
    if DB_TYPE == 'postgresql':
        return f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    elif DB_TYPE == 'sqlite':
        return f"sqlite:///{SQLITE_DB_PATH}"
    else:
        raise ValueError(f"Unsupported database type: {DB_TYPE}")

# Validation
def validate_config():
    """Validate critical configuration settings."""
    errors = []

    if not GOOGLE_PLACES_API_KEY:
        errors.append("GOOGLE_PLACES_API_KEY is not set")

    if not YELP_API_KEY:
        errors.append("YELP_API_KEY is not set")

    if DB_TYPE == 'postgresql' and (not DB_USER or not DB_PASSWORD):
        errors.append("Database credentials not set for PostgreSQL")

    if errors:
        return False, errors

    return True, []

if __name__ == "__main__":
    # Test configuration
    is_valid, errors = validate_config()
    if is_valid:
        print("✓ Configuration is valid")
        print(f"Database URL: {get_database_url()}")
        print(f"Target City: {TARGET_CITY}, {TARGET_STATE}")
        print(f"Clinic Types: {', '.join(CLINIC_TYPES)}")
    else:
        print("✗ Configuration errors:")
        for error in errors:
            print(f"  - {error}")
