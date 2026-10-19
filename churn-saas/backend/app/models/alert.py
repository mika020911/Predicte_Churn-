# backend/app/models/alert.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    prediction_id = Column(Integer, ForeignKey("predictions.id", ondelete="CASCADE"), nullable=False, unique=True)

    alert_type = Column(String(50), nullable=False, default="high_risk")
    message = Column(Text, nullable=False)

    is_read = Column(Boolean, default=False)
    is_processed = Column(Boolean, default=False)
    is_sent_email = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)

    customer = relationship("Customer", back_populates="alerts")
    prediction = relationship("Prediction", back_populates="alert")