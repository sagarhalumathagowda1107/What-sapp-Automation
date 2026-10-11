from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class DeliveryLogResponse(BaseModel):
    id: int
    report_id: Optional[int] = None
    recipient_id: Optional[int] = None
    phone_number: str
    message_id: Optional[str] = None
    delivery_channel: str
    status: str
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DeliveryLogListResponse(BaseModel):
    total: int
    sent_count: int
    delivered_count: int
    read_count: int
    failed_count: int
    items: List[DeliveryLogResponse]
