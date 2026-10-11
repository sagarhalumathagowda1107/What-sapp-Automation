from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class Report(Base):
    """Generated PDF Report metadata model."""
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    reporting_period_start = Column(DateTime, nullable=False)
    reporting_period_end = Column(DateTime, nullable=False)
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size_bytes = Column(Integer, default=0, nullable=False)
    media_id = Column(String(100), nullable=True, index=True)  # WhatsApp Media ID upon upload
    metrics_data = Column(Text, nullable=True)  # JSON-serialized KPI metrics snapshot
    status = Column(String(50), default="generated", nullable=False, index=True)  # generated, uploaded, sent, failed
    error_message = Column(Text, nullable=True)
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    delivery_logs = relationship("DeliveryLog", back_populates="report", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Report(id={self.id}, title='{self.title}', status='{self.status}', file='{self.file_name}')>"
