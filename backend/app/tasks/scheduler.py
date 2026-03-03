import asyncio
import logging
from datetime import timezone, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.db.database import SessionLocal
from app.services.scraper import scrape_all_tracked_products

logger = logging.getLogger(__name__)

BRT = timezone(timedelta(hours=-3))
scheduler = AsyncIOScheduler(timezone=BRT)


async def run_scrape_job():
    """Job that re-scrapes all tracked products."""
    logger.info("Scheduled scrape job starting")
    db = SessionLocal()
    try:
        await scrape_all_tracked_products(db)
        logger.info("Scheduled scrape job completed")
    except Exception as e:
        logger.error("Scheduled scrape job failed: %s", e)
    finally:
        db.close()


def start_scheduler():
    """Start the APScheduler with the scraping job."""
    scheduler.add_job(
        run_scrape_job,
        "interval",
        hours=1,
        id="scrape_tracked_products",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.start()
    logger.info("Scheduler started — scraping every 1 hour")


def stop_scheduler():
    """Shutdown the scheduler."""
    logger.info("Stopping scheduler")
    scheduler.shutdown()
