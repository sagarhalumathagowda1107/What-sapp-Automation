from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class ReportMetricsSummary(BaseModel):
    reporting_period: str
    total_revenue: float = 142500.00
    active_subscribers: int = 1240
    messages_sent: int = 4920
    delivery_success_rate: float = 98.6
    system_uptime: float = 99.95
    completed_tasks: int = 864
    growth_rate: float = 12.4


class ReportGenerateRequest(BaseModel):
    title: Optional[str] = Field(None, description="Custom title for the weekly PDF report")
    reporting_period_start: Optional[datetime] = Field(None, description="Start date of reporting window (defaults to 7 days ago)")
    reporting_period_end: Optional[datetime] = Field(None, description="End date of reporting window (defaults to today)")
    distribute_to_recipients: bool = Field(True, description="Whether to immediately distribute generated PDF to active opted-in recipients via WhatsApp")
    custom_metrics: Optional[Dict[str, Any]] = Field(None, description="Optional custom KPI data to embed in the PDF")


class ReportResponse(BaseModel):
    id: int
    title: str
    reporting_period_start: datetime
    reporting_period_end: datetime
    file_path: str
    file_name: str
    file_size_bytes: int
    media_id: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    generated_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReportDetailResponse(ReportResponse):
    metrics_data: Optional[Dict[str, Any]] = None
    total_recipients: Optional[int] = 0
    successful_deliveries: Optional[int] = 0
    failed_deliveries: Optional[int] = 0


class ReportListResponse(BaseModel):
    total: int
    items: List[ReportResponse]
