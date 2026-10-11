from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.recipient import Recipient
from app.schemas.recipient import (
    RecipientCreate,
    RecipientUpdate,
    RecipientResponse,
    RecipientListResponse
)

router = APIRouter(prefix="/recipients", tags=["Recipients"])


@router.post(
    "",
    response_model=RecipientResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register & Subscribe WhatsApp Recipient"
)
def create_recipient(payload: RecipientCreate, db: Session = Depends(get_db)):
    """
    Subscribes a recipient to weekly PDF reports.
    Validates E.164 phone number format and tracks opt-in timestamp.
    """
    existing = db.query(Recipient).filter(Recipient.phone_number == payload.phone_number).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Recipient with phone number '{payload.phone_number}' is already registered."
        )

    recipient = Recipient(
        **payload.model_dump(),
        opted_in_at=datetime.utcnow() if payload.opted_in else None
    )
    db.add(recipient)
    db.commit()
    db.refresh(recipient)
    return recipient


@router.get(
    "",
    response_model=RecipientListResponse,
    summary="List Registered Recipients"
)
def list_recipients(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    is_active: Optional[bool] = Query(None),
    opted_in: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """Lists registered WhatsApp recipients with optional active and opt-in filters."""
    query = db.query(Recipient)
    if is_active is not None:
        query = query.filter(Recipient.is_active == is_active)
    if opted_in is not None:
        query = query.filter(Recipient.opted_in == opted_in)

    total = query.count()
    items = query.order_by(Recipient.id.asc()).offset(skip).limit(limit).all()
    return RecipientListResponse(total=total, items=items)


@router.get(
    "/{recipient_id}",
    response_model=RecipientResponse,
    summary="Get Recipient Details"
)
def get_recipient(recipient_id: int, db: Session = Depends(get_db)):
    recipient = db.query(Recipient).filter(Recipient.id == recipient_id).first()
    if not recipient:
        raise HTTPException(status_code=404, detail=f"Recipient with ID {recipient_id} not found.")
    return recipient


@router.put(
    "/{recipient_id}",
    response_model=RecipientResponse,
    summary="Update Recipient Information"
)
def update_recipient(
    recipient_id: int,
    payload: RecipientUpdate,
    db: Session = Depends(get_db)
):
    recipient = db.query(Recipient).filter(Recipient.id == recipient_id).first()
    if not recipient:
        raise HTTPException(status_code=404, detail=f"Recipient with ID {recipient_id} not found.")

    update_data = payload.model_dump(exclude_unset=True)

    # If opt-in changed to True, refresh opted_in_at
    if update_data.get("opted_in") is True and not recipient.opted_in:
        recipient.opted_in_at = datetime.utcnow()

    for key, value in update_data.items():
        setattr(recipient, key, value)

    db.commit()
    db.refresh(recipient)
    return recipient


@router.delete(
    "/{recipient_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Recipient"
)
def delete_recipient(recipient_id: int, db: Session = Depends(get_db)):
    recipient = db.query(Recipient).filter(Recipient.id == recipient_id).first()
    if not recipient:
        raise HTTPException(status_code=404, detail=f"Recipient with ID {recipient_id} not found.")

    db.delete(recipient)
    db.commit()
    return None
