from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict
import re


def normalize_phone_number(v: str) -> str:
    """Validate and normalize phone number into standard international format without leading plus or spaces."""
    cleaned = re.sub(r"[^\d]", "", v)
    if not (10 <= len(cleaned) <= 15):
        raise ValueError("Phone number must contain between 10 and 15 digits (E.164 international standard).")
    return cleaned


class RecipientBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Full name or team identifier")
    phone_number: str = Field(..., description="Phone number with country code (e.g. +919876543210 or 919876543210)")
    email: Optional[str] = Field(None, max_length=255, description="Optional email contact")
    department: Optional[str] = Field(None, max_length=100, description="Department or business unit")
    is_active: bool = Field(True, description="Whether recipient is actively receiving messages")
    opted_in: bool = Field(True, description="WhatsApp communication opt-in status")
    timezone: str = Field("Asia/Kolkata", max_length=50, description="Recipient local timezone")

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        return normalize_phone_number(v)


class RecipientCreate(RecipientBase):
    pass


class RecipientUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone_number: Optional[str] = None
    email: Optional[str] = None
    department: Optional[str] = None
    is_active: Optional[bool] = None
    opted_in: Optional[bool] = None
    timezone: Optional[str] = None

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return normalize_phone_number(v)
        return v


class RecipientResponse(RecipientBase):
    id: int
    opted_in_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RecipientListResponse(BaseModel):
    total: int
    items: List[RecipientResponse]
