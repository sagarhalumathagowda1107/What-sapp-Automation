import os
import pytest
from unittest.mock import patch, MagicMock
from app.services.whatsapp_client import (
    WhatsAppCloudAPIClient,
    WhatsAppAPIError,
    WhatsAppConfigurationError
)


@pytest.fixture
def temp_pdf_file():
    path = "storage/test_reports/mock_sample.pdf"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(b"%PDF-1.4 Mock PDF Document Content For Testing")
    yield path
    if os.path.exists(path):
        os.remove(path)


def test_upload_media_success(temp_pdf_file):
    """Test successful WhatsApp Cloud API media upload with mocked Meta Graph response."""
    client = WhatsAppCloudAPIClient()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"id": "meta_media_id_998877"}

    with patch("requests.post", return_value=mock_resp) as mock_post:
        media_id = client.upload_media(temp_pdf_file)
        assert media_id == "meta_media_id_998877"
        mock_post.assert_called_once()


def test_send_document_message_success():
    """Test sending document message with mocked Meta Graph response."""
    client = WhatsAppCloudAPIClient()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "messaging_product": "whatsapp",
        "contacts": [{"input": "919876543210", "wa_id": "919876543210"}],
        "messages": [{"id": "wamid.HBgLMjE5OTg4"}]
    }

    with patch("requests.post", return_value=mock_resp):
        res = client.send_document_message(
            recipient_phone="919876543210",
            media_id="meta_media_id_998877",
            filename="Weekly_Report.pdf",
            caption="Here is your weekly report"
        )
        assert "messages" in res
        assert res["messages"][0]["id"] == "wamid.HBgLMjE5OTg4"


def test_send_document_template_success():
    """Test sending template document message."""
    client = WhatsAppCloudAPIClient()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "messaging_product": "whatsapp",
        "messages": [{"id": "wamid.HBgLTemplateMsg"}]
    }

    with patch("requests.post", return_value=mock_resp):
        res = client.send_document_template(
            recipient_phone="919876543210",
            template_name="weekly_report_document",
            language_code="en_US",
            media_id="meta_media_id_998877",
            filename="Weekly_Report.pdf",
            body_parameters=["Jane Doe", "Oct 05 - Oct 11, 2026"]
        )
        assert res["messages"][0]["id"] == "wamid.HBgLTemplateMsg"


def test_whatsapp_api_error_raised():
    """Test WhatsAppAPIError is raised on 400 Bad Request."""
    client = WhatsAppCloudAPIClient()
    mock_resp = MagicMock()
    mock_resp.status_code = 400
    mock_resp.content = b'{"error": {"message": "Invalid Parameter"}}'
    mock_resp.json.return_value = {"error": {"message": "Invalid Parameter"}}

    with patch("requests.post", return_value=mock_resp):
        with pytest.raises(WhatsAppAPIError):
            client.send_document_message("919876543210", "invalid_id", "test.pdf")
