from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class WebhookStatusError(BaseModel):
    code: int
    title: Optional[str] = None
    message: Optional[str] = None
    error_data: Optional[Dict[str, Any]] = None


class WebhookStatus(BaseModel):
    id: str = Field(..., description="Message ID (wamid) corresponding to the sent message")
    status: str = Field(..., description="Status: sent, delivered, read, failed")
    timestamp: str = Field(..., description="Unix timestamp of the status update")
    recipient_id: str = Field(..., description="Recipient phone number / WhatsApp ID")
    conversation: Optional[Dict[str, Any]] = None
    pricing: Optional[Dict[str, Any]] = None
    errors: Optional[List[WebhookStatusError]] = None


class WebhookMessage(BaseModel):
    from_phone: Optional[str] = Field(None, alias="from")
    id: str
    timestamp: str
    type: str
    text: Optional[Dict[str, Any]] = None
    document: Optional[Dict[str, Any]] = None
    interactive: Optional[Dict[str, Any]] = None


class WebhookChangeValue(BaseModel):
    messaging_product: str = "whatsapp"
    metadata: Optional[Dict[str, Any]] = None
    contacts: Optional[List[Dict[str, Any]]] = None
    messages: Optional[List[Dict[str, Any]]] = None
    statuses: Optional[List[Dict[str, Any]]] = None


class WebhookChange(BaseModel):
    field: str
    value: Dict[str, Any]


class WebhookEntry(BaseModel):
    id: str
    changes: List[WebhookChange]


class WebhookPayload(BaseModel):
    object: str
    entry: List[WebhookEntry]


class WebhookVerificationQuery(BaseModel):
    hub_mode: Optional[str] = Field(None, alias="hub.mode")
    hub_challenge: Optional[str] = Field(None, alias="hub.challenge")
    hub_verify_token: Optional[str] = Field(None, alias="hub.verify_token")
