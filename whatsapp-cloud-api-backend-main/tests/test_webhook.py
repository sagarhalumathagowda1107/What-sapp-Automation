import hmac
import hashlib
import json
from datetime import datetime

from app.core.config import settings
from app.models.delivery_log import DeliveryLog
from app.models.recipient import Recipient


def test_webhook_get_verification_success(client):
    """Test Meta webhook verification handshake succeeds with valid token."""
    res = client.get(
        "/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": settings.WEBHOOK_VERIFY_TOKEN,
            "hub.challenge": "11559988"
        }
    )
    assert res.status_code == 200
    assert res.text == "11559988"


def test_webhook_get_verification_failure(client):
    """Test Meta webhook verification handshake is rejected with invalid token."""
    res = client.get(
        "/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong_token",
            "hub.challenge": "11559988"
        }
    )
    assert res.status_code == 403


def test_webhook_post_signature_validation_and_status_update(client, db_session):
    """Test HMAC signature validation and status update delivery processing."""
    # 1. Create recipient and delivery log
    recipient = Recipient(
        name="Status Test User",
        phone_number="919999988888",
        opted_in=True,
        is_active=True
    )
    db_session.add(recipient)
    db_session.commit()

    delivery_log = DeliveryLog(
        recipient_id=recipient.id,
        phone_number="919999988888",
        message_id="wamid.HBgLStatusUpdateTest99",
        status="sent",
        sent_at=datetime.utcnow()
    )
    db_session.add(delivery_log)
    db_session.commit()

    # 2. Prepare Meta webhook status update payload
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "WABA_ID_123",
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "messaging_product": "whatsapp",
                            "statuses": [
                                {
                                    "id": "wamid.HBgLStatusUpdateTest99",
                                    "status": "delivered",
                                    "timestamp": "1710005000",
                                    "recipient_id": "919999988888"
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }
    payload_bytes = json.dumps(payload).encode("utf-8")

    # 3. Compute valid HMAC-SHA256 signature
    signature = hmac.new(
        key=settings.META_APP_SECRET.encode("utf-8"),
        msg=payload_bytes,
        digestmod=hashlib.sha256
    ).hexdigest()

    # 4. Post with valid signature
    post_res = client.post(
        "/webhook",
        content=payload_bytes,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": f"sha256={signature}"
        }
    )
    assert post_res.status_code == 200
    assert post_res.json()["status"] == "success"

    # 5. Verify database was updated to "delivered"
    updated_log = db_session.query(DeliveryLog).filter(
        DeliveryLog.message_id == "wamid.HBgLStatusUpdateTest99"
    ).first()
    assert updated_log.status == "delivered"
    assert updated_log.delivered_at is not None


def test_webhook_post_rejects_invalid_signature(client):
    """Test webhook rejects payload with invalid HMAC signature."""
    payload = {"object": "whatsapp_business_account", "entry": []}
    payload_bytes = json.dumps(payload).encode("utf-8")

    res = client.post(
        "/webhook",
        content=payload_bytes,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": "sha256=invalid_hash_value_here"
        }
    )
    assert res.status_code == 401
