import hmac
import hashlib
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def verify_webhook_signature(payload_bytes: bytes, signature_header: Optional[str], app_secret: str) -> bool:
    """
    Verify the X-Hub-Signature-256 header sent by Meta WhatsApp Cloud API.
    
    Header format: "sha256=<hash>"
    Validation algorithm: HMAC-SHA256 with Meta App Secret as the key.
    """
    if not app_secret:
        logger.warning("META_APP_SECRET is not configured. Webhook signature validation bypassed.")
        return True

    if not signature_header:
        logger.warning("Missing X-Hub-Signature-256 header on webhook request.")
        return False

    prefix = "sha256="
    if signature_header.startswith(prefix):
        provided_hash = signature_header[len(prefix):]
    else:
        provided_hash = signature_header

    try:
        expected_hash = hmac.new(
            key=app_secret.encode("utf-8"),
            msg=payload_bytes,
            digestmod=hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(provided_hash, expected_hash)
    except Exception as e:
        logger.error(f"Error validating webhook signature: {e}")
        return False
