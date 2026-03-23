import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from sqlalchemy.orm import Session
from database import SessionLocal
from services.nvd_sync import NVDSyncService
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Global scheduler instance
scheduler = None


def init_scheduler():
    """Initialize background scheduler for CVE sync jobs"""
    global scheduler
    
    if scheduler is not None:
        return scheduler
    
    scheduler = BackgroundScheduler(daemon=True)
    
    # Delta sync job - every 10 minutes for recent CVEs
    def delta_sync_job():
        logger.info("Starting scheduled delta sync...")
        try:
            db = SessionLocal()
            nvd_service = NVDSyncService(db)
            result = nvd_service.sync_recent_cves(hours=1)
            logger.info(f"Delta sync result: {result}")
            db.close()
        except Exception as e:
            logger.error(f"Delta sync job failed: {e}")
    
    # Full sync job - every 60 minutes (runs in background)
    def full_sync_job():
        logger.info("Starting scheduled full sync (paginated)...")
        try:
            db = SessionLocal()
            nvd_service = NVDSyncService(db)
            
            start_index = 0
            batch_size = 2000
            total_updated = 0
            
            while True:
                result = nvd_service.sync_recent_cves_paginated(start_index, batch_size)
                total_updated += result['new'] + result['updated']
                
                if not result.get('has_more'):
                    break
                
                start_index = result['next_index']
            
            logger.info(f"Full sync complete: {total_updated} total updates")
            db.close()
            
        except Exception as e:
            logger.error(f"Full sync job failed: {e}")
    
    # Add jobs to scheduler
    scheduler.add_job(
        delta_sync_job,
        trigger=IntervalTrigger(minutes=settings.DELTA_SYNC_INTERVAL),
        id='delta_sync',
        name='Delta CVE sync (recent CVEs)',
        replace_existing=True,
    )
    
    scheduler.add_job(
        full_sync_job,
        trigger=IntervalTrigger(minutes=settings.FULL_SYNC_INTERVAL),
        id='full_sync',
        name='Full CVE sync (paginated)',
        replace_existing=True,
    )
    
    scheduler.start()
    logger.info(f"✓ Scheduler initialized with delta sync interval ({settings.DELTA_SYNC_INTERVAL}min) and full sync interval ({settings.FULL_SYNC_INTERVAL}min)")
    
    return scheduler


def shutdown_scheduler():
    """Shutdown the scheduler"""
    global scheduler
    
    if scheduler and scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler shutdown")
