from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict


class ScheduleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Name of the reporting schedule")
    description: Optional[str] = Field(None, description="Optional schedule details")
    cron_expression: Optional[str] = Field(None, description="Standard 5-part cron expression (e.g., '0 9 * * 1')")
    day_of_week: str = Field("mon", description="Day of week: mon, tue, wed, thu, fri, sat, sun")
    hour: int = Field(9, ge=0, le=23, description="Hour of the day in 24h format (0-23)")
    minute: int = Field(0, ge=0, le=59, description="Minute of the hour (0-59)")
    timezone: str = Field("Asia/Kolkata", description="Timezone (default: Asia/Kolkata)")
    is_active: bool = Field(True, description="Whether this schedule is currently enabled")

    @field_validator("day_of_week")
    @classmethod
    def validate_day(cls, v: str) -> str:
        v_clean = v.strip().lower()
        valid_days = {"mon", "tue", "wed", "thu", "fri", "sat", "sun"}
        if v_clean not in valid_days:
            raise ValueError(f"day_of_week must be one of: {', '.join(sorted(valid_days))}")
        return v_clean


class ScheduleCreate(ScheduleBase):
    pass


class ScheduleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    cron_expression: Optional[str] = None
    day_of_week: Optional[str] = None
    hour: Optional[int] = Field(None, ge=0, le=23)
    minute: Optional[int] = Field(None, ge=0, le=59)
    timezone: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator("day_of_week")
    @classmethod
    def validate_day(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_clean = v.strip().lower()
            valid_days = {"mon", "tue", "wed", "thu", "fri", "sat", "sun"}
            if v_clean not in valid_days:
                raise ValueError(f"day_of_week must be one of: {', '.join(sorted(valid_days))}")
            return v_clean
        return v


class ScheduleResponse(ScheduleBase):
    id: int
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScheduleListResponse(BaseModel):
    total: int
    items: List[ScheduleResponse]
