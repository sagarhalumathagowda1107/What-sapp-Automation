import json
import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Request, HTTPException, Depends, Query, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings
from app.core.security import verify_webhook_signature
from app.models.delivery_log import DeliveryLog
from app.models.recipient import Recipient

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Webhooks"])


@router.get(
    "/webhook",
    summary="Meta WhatsApp Cloud API Webhook Verification Challenge"
)
def verify_webhook(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token")
):
    """
    Handles Meta WhatsApp Cloud API initial webhook verification challenge.
    Validates hub.mode == 'subscribe' and matches hub.verify_token with WEBHOOK_VERIFY_TOKEN.
    Returns hub.challenge as plain text.
    """
    logger.info(f"Webhook verification request received. Mode: {hub_mode}")

    if hub_mode == "subscribe" and hub_verify_token == settings.WEBHOOK_VERIFY_TOKEN:
        logger.info("Meta webhook verification challenge succeeded.")
        return PlainTextResponse(content=str(hub_challenge), status_code=status.HTTP_200_OK)

    logger.warning("Meta webhook verification challenge failed: token mismatch or invalid mode.")
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Webhook verification failed: Invalid verify token or mode."
    )


@router.post(
    "/webhook",
    summary="Receive WhatsApp Cloud API Webhook Notifications & Delivery Statuses"
)
async def process_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Processes real-time WhatsApp Cloud API events:
    - Enforces HMAC-SHA256 signature verification via X-Hub-Signature-256 header.
    - Updates message delivery statuses (sent -> delivered -> read / failed).
    - Handles recipient opt-in/opt-out keywords (e.g. STOP, START).
    """
    # 1. Read raw body for HMAC signature verification
    raw_body = await request.body()
    signature_header = request.headers.get("X-Hub-Signature-256")

    # Enforce signature validation if META_APP_SECRET is set
    if settings.META_APP_SECRET and not verify_webhook_signature(raw_body, signature_header, settings.META_APP_SECRET):
        logger.warning("Rejected webhook request due to invalid HMAC signature.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook HMAC signature."
        )

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except Exception as parse_err:
        logger.error(f"Failed to parse webhook JSON payload: {parse_err}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON body.")

    # 2. Process payload entries
    entries = payload.get("entry", [])
    for entry in entries:
        changes = entry.get("changes", [])
        for change in changes:
            value = change.get("value", {})

            # A. Process message delivery statuses
            statuses = value.get("statuses", [])
            for status_update in statuses:
                message_id = status_update.get("id")
                new_status = status_update.get("status")  # sent, delivered, read, failed
                ts_raw = status_update.get("timestamp")

                status_time = None
                if ts_raw:
                    try:
                        status_time = datetime.utcfromtimestamp(int(ts_raw))
                    except Exception:
                        status_time = datetime.utcnow()

                logger.info(f"Received delivery status update: message_id={message_id}, status={new_status}")

                if message_id:
                    delivery_log = db.query(DeliveryLog).filter(
                        DeliveryLog.message_id == message_id
                    ).first()

                    if delivery_log:
                        delivery_log.status = new_status
                        if new_status == "delivered":
                            delivery_log.delivered_at = status_time or datetime.utcnow()
                        elif new_status == "read":
                            delivery_log.read_at = status_time or datetime.utcnow()
                        elif new_status == "failed":
                            errors = status_update.get("errors", [])
                            delivery_log.error_message = json.dumps(errors)

                        # Append metadata
                        existing_meta = json.loads(delivery_log.meta_response) if delivery_log.meta_response else {}
                        existing_meta.setdefault("status_history", []).append({
                            "status": new_status,
                            "timestamp": ts_raw
                        })
                        delivery_log.meta_response = json.dumps(existing_meta)
                        db.commit()

            # B. Process inbound messages (Opt-out / Opt-in commands)
            messages = value.get("messages", [])
            for message in messages:
                from_phone = message.get("from")
                msg_type = message.get("type")
                if msg_type == "text":
                    body_text = message.get("text", {}).get("body", "").strip().upper()
                    if body_text in ("STOP", "UNSUBSCRIBE", "OPTOUT"):
                        logger.info(f"Recipient {from_phone} requested OPT-OUT.")
                        recipient = db.query(Recipient).filter(Recipient.phone_number == from_phone).first()
                        if recipient:
                            recipient.opted_in = False
                            db.commit()
                    elif body_text in ("START", "SUBSCRIBE", "OPTIN"):
                        logger.info(f"Recipient {from_phone} requested OPT-IN.")
                        recipient = db.query(Recipient).filter(Recipient.phone_number == from_phone).first()
                        if recipient:
                            recipient.opted_in = True
                            recipient.opted_in_at = datetime.utcnow()
                            db.commit()

    return {"status": "success", "processed": True}
