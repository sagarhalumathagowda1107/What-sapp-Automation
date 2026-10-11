from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.delivery_log import DeliveryLog
from app.schemas.delivery_log import DeliveryLogListResponse

router = APIRouter(prefix="/delivery-logs", tags=["Delivery Logs"])


@router.get(
    "",
    response_model=DeliveryLogListResponse,
    summary="List WhatsApp Delivery Logs & Statuses"
)
def list_delivery_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    report_id: Optional[int] = Query(None),
    recipient_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    phone_number: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Returns message delivery logs and breakdown across 'sent', 'delivered', 'read', and 'failed' states.
    Updated asynchronously via Meta WhatsApp Cloud API webhooks.
    """
    query = db.query(DeliveryLog)

    if report_id is not None:
        query = query.filter(DeliveryLog.report_id == report_id)
    if recipient_id is not None:
        query = query.filter(DeliveryLog.recipient_id == recipient_id)
    if status_filter is not None:
        query = query.filter(DeliveryLog.status == status_filter)
    if phone_number is not None:
        query = query.filter(DeliveryLog.phone_number == phone_number)

    total = query.count()

    # Aggregate status statistics
    sent_count = db.query(DeliveryLog).filter(DeliveryLog.status == "sent").count()
    delivered_count = db.query(DeliveryLog).filter(DeliveryLog.status == "delivered").count()
    read_count = db.query(DeliveryLog).filter(DeliveryLog.status == "read").count()
    failed_count = db.query(DeliveryLog).filter(DeliveryLog.status == "failed").count()

    items = query.order_by(DeliveryLog.created_at.desc()).offset(skip).limit(limit).all()

    return DeliveryLogListResponse(
        total=total,
        sent_count=sent_count,
        delivered_count=delivered_count,
        read_count=read_count,
        failed_count=failed_count,
        items=items
    )
