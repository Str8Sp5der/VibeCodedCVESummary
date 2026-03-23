import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_admin
from models.user import User
from models.audit_log import AuditLog
from models.cve import CVE
from services.scheduler import scheduler
from services.nvd_sync import NVDSyncService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/audit-logs")
async def get_audit_logs(
    page: int = 1,
    limit: int = 100,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Get audit logs (admin only)
    """
    
    # Query audit logs
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc())
    
    total = logs.count()
    skip = (page - 1) * limit
    
    items = logs.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "items": [log.to_dict() for log in items],
        "page": page,
        "limit": limit,
    }


@router.get("/sync-status")
async def get_sync_status(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Get CVE database sync status (admin only)
    """
    
    cve_count = db.query(CVE).count()
    latest_cve = db.query(CVE).order_by(CVE.published_date.desc()).first()
    
    # Scheduler status
    scheduler_status = "running" if scheduler and scheduler.running else "stopped"
    
    jobs = []
    if scheduler and scheduler.running:
        for job in scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            })
    
    return {
        "cve_count": cve_count,
        "latest_cve_date": latest_cve.published_date.isoformat() if latest_cve else None,
        "scheduler_status": scheduler_status,
        "jobs": jobs,
    }


@router.post("/sync/trigger")
async def trigger_sync(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Manually trigger CVE database sync (admin only)
    """
    
    try:
        logger.info(f"Manual sync triggered by admin: {current_admin.email}")
        
        nvd_service = NVDSyncService(db)
        result = nvd_service.sync_recent_cves(hours=24)
        
        return {
            "status": "sync_started",
            "result": result,
            "message": f"Sync triggered. Updated {result['new'] + result['updated']} CVEs",
        }
        
    except Exception as e:
        logger.error(f"Manual sync failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}",
        )
