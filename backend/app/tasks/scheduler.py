import asyncio
import logging
from datetime import timezone, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.db.database import SessionLocal
from app.services.scraper import scrape_all_tracked_products, scrape_untracked_products

logger = logging.getLogger(__name__)

BRT = timezone(timedelta(hours=-3))
scheduler = AsyncIOScheduler(timezone=BRT)


async def run_tracked_scrape_job():
    """Job that re-scrapes products with at least one user tracking them."""
    logger.info("Scheduled tracked scrape job starting")
    db = SessionLocal()
    try:
        await scrape_all_tracked_products(db)
        logger.info("Scheduled tracked scrape job completed")
    except Exception as e:
        logger.error("Scheduled tracked scrape job failed: %s", e)
    finally:
        db.close()


async def run_untracked_scrape_job():
    """Job that re-scrapes products with no users tracking them."""
    logger.info("Scheduled untracked scrape job starting")
    db = SessionLocal()
    try:
        await scrape_untracked_products(db)
        logger.info("Scheduled untracked scrape job completed")
    except Exception as e:
        logger.error("Scheduled untracked scrape job failed: %s", e)
    finally:
        db.close()


def start_scheduler():
    """Start the APScheduler with the scraping jobs."""
    scheduler.add_job(
        run_tracked_scrape_job,
        "interval",
        hours=1,
        id="scrape_tracked_products",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.add_job(
        run_untracked_scrape_job,
        "interval",
        hours=24,
        id="scrape_untracked_products",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.start()
    logger.info("Scheduler started — tracked: every 1h, untracked: every 24h")


def stop_scheduler():
    """Shutdown the scheduler."""
    logger.info("Stopping scheduler")
    scheduler.shutdown()
