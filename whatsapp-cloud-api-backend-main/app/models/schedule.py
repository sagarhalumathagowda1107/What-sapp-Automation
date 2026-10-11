from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from app.core.database import Base


class Schedule(Base):
    """Automated reporting schedule configuration model."""
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    cron_expression = Column(String(100), nullable=True)  # e.g., "0 9 * * 1" (Every Mon at 9:00 AM)
    day_of_week = Column(String(20), default="mon", nullable=False)  # mon, tue, wed, thu, fri, sat, sun
    hour = Column(Integer, default=9, nullable=False)  # 0-23
    minute = Column(Integer, default=0, nullable=False)  # 0-59
    timezone = Column(String(50), default="Asia/Kolkata", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_run_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Schedule(id={self.id}, name='{self.name}', day='{self.day_of_week}', time='{self.hour}:{self.minute}', active={self.is_active})>"
