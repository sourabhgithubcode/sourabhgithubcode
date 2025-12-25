"""
Database initialization and management utilities.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from loguru import logger
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.database.models import Base
from config.settings import get_database_url, LOG_FILE, LOG_LEVEL


def setup_logging():
    """Configure logging."""
    logger.remove()
    logger.add(
        sys.stderr,
        level=LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
    )
    logger.add(
        LOG_FILE,
        rotation="10 MB",
        retention="30 days",
        level=LOG_LEVEL,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}"
    )


def create_database():
    """
    Create all database tables.
    """
    setup_logging()

    try:
        database_url = get_database_url()
        logger.info(f"Creating database with URL: {database_url.split('@')[-1]}")  # Hide credentials

        engine = create_engine(database_url, echo=False)

        # Create all tables
        Base.metadata.create_all(engine)

        logger.success("✓ Database tables created successfully")

        # Print table summary
        tables = Base.metadata.tables.keys()
        logger.info(f"Created {len(tables)} tables:")
        for table in tables:
            logger.info(f"  - {table}")

        return engine

    except Exception as e:
        logger.error(f"Failed to create database: {e}")
        raise


def drop_database():
    """
    Drop all database tables. Use with caution!
    """
    setup_logging()

    try:
        database_url = get_database_url()
        logger.warning(f"Dropping all tables from: {database_url.split('@')[-1]}")

        engine = create_engine(database_url, echo=False)
        Base.metadata.drop_all(engine)

        logger.success("✓ All tables dropped successfully")

        return engine

    except Exception as e:
        logger.error(f"Failed to drop database: {e}")
        raise


def get_session():
    """
    Get a database session.
    """
    database_url = get_database_url()
    engine = create_engine(database_url, echo=False)
    Session = sessionmaker(bind=engine)
    return Session()


def reset_database():
    """
    Drop and recreate all tables. Use with caution!
    """
    logger.warning("Resetting database - all data will be lost!")
    drop_database()
    create_database()
    logger.success("✓ Database reset complete")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Database management utilities')
    parser.add_argument(
        'action',
        choices=['create', 'drop', 'reset'],
        help='Action to perform'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force action without confirmation'
    )

    args = parser.parse_args()

    if args.action == 'create':
        create_database()

    elif args.action == 'drop':
        if not args.force:
            confirm = input("Are you sure you want to drop all tables? (yes/no): ")
            if confirm.lower() != 'yes':
                print("Aborted.")
                sys.exit(0)
        drop_database()

    elif args.action == 'reset':
        if not args.force:
            confirm = input("Are you sure you want to reset the database? All data will be lost. (yes/no): ")
            if confirm.lower() != 'yes':
                print("Aborted.")
                sys.exit(0)
        reset_database()
