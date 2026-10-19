
from sqlalchemy import Column, Integer, Float, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    observation_id = Column(Integer, ForeignKey("observations.id", ondelete="CASCADE"), nullable=False, index=True, unique=True)

    score = Column(Float, nullable=False)
    risk_level = Column(String(20), nullable=False)  # low | medium | high
    top_reasons = Column(JSON, nullable=True)
    shap_values = Column(JSON, nullable=True)

    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    model_version = Column(String(50), nullable=True)

    customer = relationship("Customer", back_populates="predictions")
    observation = relationship("Observation", back_populates="prediction")
    alert = relationship("Alert", back_populates="prediction", uselist=False)