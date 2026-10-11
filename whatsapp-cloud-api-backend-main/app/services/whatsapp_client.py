import os
import time
import logging
from typing import Optional, Dict, Any, List
import requests

from app.core.config import settings

logger = logging.getLogger(__name__)


class WhatsAppConfigurationError(Exception):
    """Raised when WhatsApp Cloud API credentials are unset or invalid."""
    pass


class WhatsAppAPIError(Exception):
    """Raised when Meta WhatsApp Cloud API returns an error."""
    def __init__(self, status_code: int, error_data: Dict[str, Any]):
        self.status_code = status_code
        self.error_data = error_data
        message = error_data.get("error", {}).get("message", f"WhatsApp API HTTP {status_code}")
        super().__init__(message)


class WhatsAppCloudAPIClient:
    """
    Official Meta WhatsApp Cloud API Client.
    
    Handles:
    - PDF document media uploads (POST /{phone_number_id}/media)
    - Document message delivery via media ID (POST /{phone_number_id}/messages)
    - Document template delivery outside the 24-hour conversation window
    - Safe retries with exponential backoff
    """

    def __init__(self):
        self.base_url = f"{settings.WHATSAPP_API_URL.rstrip('/')}/{settings.WHATSAPP_API_VERSION}"

    @property
    def headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
            "User-Agent": f"WhatsAppReportAutomation/{settings.VERSION}"
        }

    def _ensure_configured(self):
        if not settings.is_whatsapp_configured:
            raise WhatsAppConfigurationError(
                "Meta WhatsApp Cloud API is not configured. Please supply valid WHATSAPP_ACCESS_TOKEN "
                "and WHATSAPP_PHONE_NUMBER_ID in your environment or .env file before making API calls."
            )

    def upload_media(self, file_path: str, mime_type: str = "application/pdf") -> str:
        """
        Uploads a local PDF document to Meta WhatsApp Cloud API.
        Returns the Meta media ID string.
        """
        self._ensure_configured()

        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found for media upload: {file_path}")

        file_name = os.path.basename(file_path)
        url = f"{self.base_url}/{settings.WHATSAPP_PHONE_NUMBER_ID}/media"

        max_retries = max(1, settings.MAX_RETRIES)
        backoff = settings.RETRY_BACKOFF_SECONDS

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Uploading media '{file_name}' to Meta Cloud API (Attempt {attempt}/{max_retries})...")
                
                with open(file_path, "rb") as f:
                    files = {
                        "file": (file_name, f, mime_type)
                    }
                    data = {
                        "messaging_product": "whatsapp",
                        "type": mime_type
                    }
                    response = requests.post(
                        url,
                        headers=self.headers,
                        files=files,
                        data=data,
                        timeout=settings.API_TIMEOUT
                    )

                if response.status_code in (200, 201):
                    res_json = response.json()
                    media_id = res_json.get("id")
                    if not media_id:
                        raise WhatsAppAPIError(response.status_code, {"error": {"message": "No media ID in response"}})
                    logger.info(f"Successfully uploaded media. Media ID: {media_id}")
                    return media_id

                error_data = response.json() if response.content else {"error": {"message": response.text}}
                logger.warning(f"Meta media upload failed (HTTP {response.status_code}): {error_data}")

                if attempt == max_retries or response.status_code in (400, 401, 403):
                    raise WhatsAppAPIError(response.status_code, error_data)

            except (requests.ConnectionError, requests.Timeout) as net_err:
                logger.warning(f"Network error on media upload attempt {attempt}: {net_err}")
                if attempt == max_retries:
                    raise

            time.sleep(backoff * (2 ** (attempt - 1)))

        raise WhatsAppAPIError(500, {"error": {"message": "Failed to upload media after maximum retries"}})

    def send_document_message(
        self,
        recipient_phone: str,
        media_id: str,
        filename: str,
        caption: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Sends an uploaded PDF document directly to a recipient phone number.
        """
        self._ensure_configured()

        url = f"{self.base_url}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
        
        doc_payload = {
            "id": media_id,
            "filename": filename
        }
        if caption:
            doc_payload["caption"] = caption

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient_phone,
            "type": "document",
            "document": doc_payload
        }

        return self._send_request(url, payload)

    def send_document_template(
        self,
        recipient_phone: str,
        template_name: str,
        language_code: str,
        media_id: str,
        filename: str,
        body_parameters: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Sends a template message containing the PDF report in the header.
        Complies with Meta policies for business-initiated notifications outside 24h window.
        """
        self._ensure_configured()

        url = f"{self.base_url}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"

        components = [
            {
                "type": "header",
                "parameters": [
                    {
                        "type": "document",
                        "document": {
                            "id": media_id,
                            "filename": filename
                        }
                    }
                ]
            }
        ]

        if body_parameters:
            components.append({
                "type": "body",
                "parameters": [{"type": "text", "text": str(param)} for param in body_parameters]
            })

        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_phone,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code},
                "components": components
            }
        }

        return self._send_request(url, payload)

    def send_text_message(self, recipient_phone: str, text: str) -> Dict[str, Any]:
        """Sends a standard text message."""
        self._ensure_configured()

        url = f"{self.base_url}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient_phone,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": text
            }
        }

        return self._send_request(url, payload)

    def _send_request(self, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Executes POST request to Meta Graph API with retries and backoff."""
        max_retries = max(1, settings.MAX_RETRIES)
        backoff = settings.RETRY_BACKOFF_SECONDS
        json_headers = {**self.headers, "Content-Type": "application/json"}

        for attempt in range(1, max_retries + 1):
            try:
                response = requests.post(
                    url,
                    json=payload,
                    headers=json_headers,
                    timeout=settings.API_TIMEOUT
                )

                if response.status_code in (200, 201):
                    res_json = response.json()
                    logger.info(f"Message delivered to WhatsApp Cloud API: {res_json}")
                    return res_json

                error_data = response.json() if response.content else {"error": {"message": response.text}}
                logger.warning(f"Meta API error (HTTP {response.status_code}) on attempt {attempt}: {error_data}")

                # Do not retry client auth or validation errors
                if response.status_code in (400, 401, 403, 404):
                    raise WhatsAppAPIError(response.status_code, error_data)

                if attempt == max_retries:
                    raise WhatsAppAPIError(response.status_code, error_data)

            except (requests.ConnectionError, requests.Timeout) as net_err:
                logger.warning(f"Connection timeout/error on attempt {attempt}: {net_err}")
                if attempt == max_retries:
                    raise

            time.sleep(backoff * (2 ** (attempt - 1)))

        raise WhatsAppAPIError(500, {"error": {"message": "Failed to send message after maximum retries"}})

    def check_connection(self) -> Dict[str, Any]:
        """Check Meta Cloud API connectivity."""
        if not settings.is_whatsapp_configured:
            return {
                "configured": False,
                "status": "unconfigured",
                "message": "Valid WHATSAPP_ACCESS_TOKEN and WHATSAPP_PHONE_NUMBER_ID required."
            }

        url = f"{self.base_url}/{settings.WHATSAPP_PHONE_NUMBER_ID}"
        try:
            res = requests.get(url, headers=self.headers, timeout=5)
            if res.status_code == 200:
                data = res.json()
                return {
                    "configured": True,
                    "status": "connected",
                    "display_phone_number": data.get("display_phone_number"),
                    "verified_name": data.get("verified_name"),
                    "quality_rating": data.get("quality_rating")
                }
            return {
                "configured": True,
                "status": "error",
                "http_status": res.status_code,
                "error": res.json() if res.content else res.text
            }
        except Exception as e:
            return {
                "configured": True,
                "status": "unreachable",
                "error": str(e)
            }


whatsapp_client = WhatsAppCloudAPIClient()
