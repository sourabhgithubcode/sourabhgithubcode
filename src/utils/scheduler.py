"""
Automated scheduler for daily data refresh pipeline.
"""

import schedule
import time
from datetime import datetime
from loguru import logger
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from config.settings import DAILY_REFRESH_TIME
from src.collectors.google_places_collector import GooglePlacesCollector
from src.collectors.yelp_collector import YelpCollector
from src.collectors.trends_collector import GoogleTrendsCollector
from src.analysis.scoring_engine import ScoringEngine
from src.database.init_db import setup_logging


class DataRefreshPipeline:
    """
    Orchestrates the complete data collection and analysis pipeline.
    """

    def __init__(self):
        setup_logging()
        logger.info("Data Refresh Pipeline initialized")

    def collect_google_places(self):
        """
        Collect Google Places data.
        """
        logger.info("=== Starting Google Places Collection ===")
        collector = GooglePlacesCollector()
        try:
            collector.collect_all_chicago()
            logger.success("✓ Google Places collection completed")
            return True
        except Exception as e:
            logger.error(f"✗ Google Places collection failed: {e}")
            return False
        finally:
            collector.close()

    def collect_yelp(self):
        """
        Collect Yelp data.
        """
        logger.info("=== Starting Yelp Collection ===")
        collector = YelpCollector()
        try:
            collector.collect_all_chicago()
            logger.success("✓ Yelp collection completed")
            return True
        except Exception as e:
            logger.error(f"✗ Yelp collection failed: {e}")
            return False
        finally:
            collector.close()

    def collect_trends(self):
        """
        Collect Google Trends data.
        """
        logger.info("=== Starting Google Trends Collection ===")
        collector = GoogleTrendsCollector()
        try:
            collector.collect_all_keywords(timeframe='today 3-m')
            logger.success("✓ Google Trends collection completed")
            return True
        except Exception as e:
            logger.error(f"✗ Google Trends collection failed: {e}")
            return False
        finally:
            collector.close()

    def run_analysis(self):
        """
        Run scoring and analysis.
        """
        logger.info("=== Starting Analysis Engine ===")
        engine = ScoringEngine()
        try:
            engine.run_all_calculations()
            logger.success("✓ Analysis completed")
            return True
        except Exception as e:
            logger.error(f"✗ Analysis failed: {e}")
            return False
        finally:
            engine.close()

    def run_full_refresh(self):
        """
        Run complete data refresh pipeline.
        """
        start_time = datetime.now()
        logger.info("=" * 60)
        logger.info(f"STARTING DAILY DATA REFRESH - {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)

        results = {
            'google_places': False,
            'yelp': False,
            'trends': False,
            'analysis': False
        }

        # Step 1: Collect Google Places data
        results['google_places'] = self.collect_google_places()
        time.sleep(5)  # Brief pause between collections

        # Step 2: Collect Yelp data
        results['yelp'] = self.collect_yelp()
        time.sleep(5)

        # Step 3: Collect Google Trends data
        results['trends'] = self.collect_trends()
        time.sleep(5)

        # Step 4: Run analysis
        results['analysis'] = self.run_analysis()

        # Summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds() / 60

        logger.info("=" * 60)
        logger.info("DAILY REFRESH SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Google Places: {'✓ Success' if results['google_places'] else '✗ Failed'}")
        logger.info(f"Yelp:          {'✓ Success' if results['yelp'] else '✗ Failed'}")
        logger.info(f"Google Trends: {'✓ Success' if results['trends'] else '✗ Failed'}")
        logger.info(f"Analysis:      {'✓ Success' if results['analysis'] else '✗ Failed'}")
        logger.info(f"Duration:      {duration:.2f} minutes")
        logger.info("=" * 60)

        success_rate = sum(results.values()) / len(results) * 100
        if success_rate == 100:
            logger.success(f"✓ Daily refresh completed successfully in {duration:.2f} minutes")
        elif success_rate >= 75:
            logger.warning(f"⚠ Daily refresh completed with some failures ({success_rate:.0f}% success)")
        else:
            logger.error(f"✗ Daily refresh failed ({success_rate:.0f}% success)")

        return results

    def start_scheduler(self):
        """
        Start the scheduled daily refresh.
        """
        logger.info(f"Scheduler started. Daily refresh scheduled for {DAILY_REFRESH_TIME}")

        # Schedule daily refresh
        schedule.every().day.at(DAILY_REFRESH_TIME).do(self.run_full_refresh)

        # Run immediately on startup (optional)
        run_on_startup = input("Run data refresh now? (y/n): ").lower() == 'y'
        if run_on_startup:
            self.run_full_refresh()

        # Keep running
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")


def run_once():
    """
    Run the pipeline once (for manual execution or testing).
    """
    pipeline = DataRefreshPipeline()
    pipeline.run_full_refresh()


def run_scheduled():
    """
    Run the pipeline on a schedule.
    """
    pipeline = DataRefreshPipeline()
    pipeline.start_scheduler()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Chicago Clinic Data Refresh Pipeline')
    parser.add_argument(
        '--mode',
        choices=['once', 'scheduled'],
        default='once',
        help='Run once or on a schedule'
    )
    parser.add_argument(
        '--component',
        choices=['google', 'yelp', 'trends', 'analysis', 'all'],
        default='all',
        help='Run specific component only'
    )

    args = parser.parse_args()

    pipeline = DataRefreshPipeline()

    if args.component == 'google':
        pipeline.collect_google_places()
    elif args.component == 'yelp':
        pipeline.collect_yelp()
    elif args.component == 'trends':
        pipeline.collect_trends()
    elif args.component == 'analysis':
        pipeline.run_analysis()
    else:
        if args.mode == 'once':
            run_once()
        else:
            run_scheduled()
