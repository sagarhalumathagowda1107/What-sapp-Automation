from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base


class Recipient(Base):
    """WhatsApp message recipient model with opt-in status."""
    __tablename__ = "recipients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phone_number = Column(String(30), unique=True, index=True, nullable=False)
    email = Column(String(255), nullable=True)
    department = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    opted_in = Column(Boolean, default=True, nullable=False)
    opted_in_at = Column(DateTime, default=datetime.utcnow, nullable=True)
    timezone = Column(String(50), default="Asia/Kolkata", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    delivery_logs = relationship("DeliveryLog", back_populates="recipient", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Recipient(id={self.id}, name='{self.name}', phone='{self.phone_number}', active={self.is_active})>"
