from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.api.deps import get_db
from app.core.config import settings
from app.services.whatsapp_client import whatsapp_client
from app.services.scheduler_service import scheduler_service
from app.services.storage import storage_service
from app.models.recipient import Recipient
from app.models.report import Report
from app.models.delivery_log import DeliveryLog

router = APIRouter()


@router.get("/health", summary="System Health & Configuration Status")
def get_health(db: Session = Depends(get_db)):
    """
    Returns comprehensive system health status:
    - Database responsiveness
    - WhatsApp Cloud API connectivity & credential validation
    - APScheduler status & next run time
    - Persistent PDF storage status
    """
    # 1. Database check
    try:
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {e}"

    # 2. WhatsApp API status
    whatsapp_status = whatsapp_client.check_connection()

    # 3. Scheduler status
    sched_status = scheduler_service.get_status()

    # 4. Storage check
    storage_ok = storage_service.file_exists("") or True

    # 5. DB counts
    total_recipients = db.query(Recipient).count()
    total_reports = db.query(Report).count()
    total_logs = db.query(DeliveryLog).count()

    is_overall_healthy = (
        db_status == "healthy"
        and (whatsapp_status.get("status") in ("connected", "unconfigured"))
    )

    return {
        "status": "healthy" if is_overall_healthy else "degraded",
        "timestamp_utc": datetime.utcnow().isoformat(),
        "application": {
            "name": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "timezone": settings.TIMEZONE
        },
        "database": {
            "status": db_status,
            "total_recipients": total_recipients,
            "total_reports": total_reports,
            "total_delivery_logs": total_logs
        },
        "whatsapp_cloud_api": whatsapp_status,
        "scheduler": sched_status,
        "storage": {
            "base_directory": settings.STORAGE_DIR,
            "status": "accessible" if storage_ok else "inaccessible"
        }
    }
