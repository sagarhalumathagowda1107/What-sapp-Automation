from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class DeliveryLog(Base):
    """WhatsApp message delivery tracking and status log model."""
    __tablename__ = "message_delivery_logs"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id", ondelete="SET NULL"), nullable=True, index=True)
    recipient_id = Column(Integer, ForeignKey("recipients.id", ondelete="SET NULL"), nullable=True, index=True)
    phone_number = Column(String(30), nullable=False, index=True)
    message_id = Column(String(150), nullable=True, index=True)  # WhatsApp Cloud API wamid ID
    delivery_channel = Column(String(50), default="whatsapp_cloud_api", nullable=False)
    status = Column(String(50), default="pending", nullable=False, index=True)  # pending, sent, delivered, read, failed
    error_message = Column(Text, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)
    meta_response = Column(Text, nullable=True)  # Raw response or webhook status dump
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    report = relationship("Report", back_populates="delivery_logs")
    recipient = relationship("Recipient", back_populates="delivery_logs")

    def __repr__(self):
        return f"<DeliveryLog(id={self.id}, phone='{self.phone_number}', status='{self.status}', message_id='{self.message_id}')>"
