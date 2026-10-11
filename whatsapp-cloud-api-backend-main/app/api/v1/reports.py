import json
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.report import Report
from app.models.delivery_log import DeliveryLog
from app.schemas.report import (
    ReportGenerateRequest,
    ReportResponse,
    ReportDetailResponse,
    ReportListResponse
)
from app.services.report_service import report_service
from app.services.storage import storage_service

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post(
    "/generate",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate On-Demand Weekly PDF Report"
)
def generate_report(
    payload: ReportGenerateRequest,
    db: Session = Depends(get_db)
):
    """
    Triggers immediate PDF report compilation and optional WhatsApp Cloud API distribution.
    - Generates vector-formatted PDF report via ReportLab.
    - Uploads media to Meta Cloud API if configured.
    - Sends document message to all active opted-in recipients.
    - Logs status for every recipient.
    """
    report = report_service.generate_and_distribute_report(
        db=db,
        title=payload.title,
        period_start=payload.reporting_period_start,
        period_end=payload.reporting_period_end,
        distribute=payload.distribute_to_recipients,
        custom_metrics=payload.custom_metrics
    )
    return report


@router.get(
    "",
    response_model=ReportListResponse,
    summary="List Generated PDF Reports"
)
def list_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db)
):
    """Retrieves paginated list of generated reports."""
    query = db.query(Report)
    if status_filter:
        query = query.filter(Report.status == status_filter)

    total = query.count()
    items = query.order_by(Report.created_at.desc()).offset(skip).limit(limit).all()
    return ReportListResponse(total=total, items=items)


@router.get(
    "/{report_id}",
    response_model=ReportDetailResponse,
    summary="Get Report Details by ID"
)
def get_report(report_id: int, db: Session = Depends(get_db)):
    """Fetches single report details along with distribution delivery aggregates."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail=f"Report with ID {report_id} not found.")

    # Calculate delivery aggregates
    total_logs = db.query(DeliveryLog).filter(DeliveryLog.report_id == report_id).count()
    success_logs = db.query(DeliveryLog).filter(
        DeliveryLog.report_id == report_id,
        DeliveryLog.status.in_(["sent", "delivered", "read"])
    ).count()
    failed_logs = db.query(DeliveryLog).filter(
        DeliveryLog.report_id == report_id,
        DeliveryLog.status == "failed"
    ).count()

    metrics = json.loads(report.metrics_data) if report.metrics_data else None

    return ReportDetailResponse(
        id=report.id,
        title=report.title,
        reporting_period_start=report.reporting_period_start,
        reporting_period_end=report.reporting_period_end,
        file_path=report.file_path,
        file_name=report.file_name,
        file_size_bytes=report.file_size_bytes,
        media_id=report.media_id,
        status=report.status,
        error_message=report.error_message,
        generated_at=report.generated_at,
        created_at=report.created_at,
        metrics_data=metrics,
        total_recipients=total_logs,
        successful_deliveries=success_logs,
        failed_deliveries=failed_logs
    )


@router.get(
    "/{report_id}/download",
    summary="Download Generated PDF Report"
)
def download_report(report_id: int, db: Session = Depends(get_db)):
    """
    Streams the physical PDF file to the client for secure download.
    Validates file existence and returns proper application/pdf content type.
    """
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail=f"Report with ID {report_id} not found.")

    if not storage_service.file_exists(report.file_name):
        raise HTTPException(
            status_code=404,
            detail=f"Report PDF file '{report.file_name}' does not exist on storage disk."
        )

    file_path = storage_service.get_file_path(report.file_name)
    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=report.file_name,
        headers={
            "Content-Disposition": f'attachment; filename="{report.file_name}"'
        }
    )
