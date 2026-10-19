import secrets
from sqlalchemy import Column, String, Integer, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

def generate_api_key():
    return f"cs_{secrets.token_urlsafe(32)}"


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    api_key = Column(String(64), unique=True, index=True, default=generate_api_key)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    customers = relationship("Customer", back_populates="organization", cascade="all, delete-orphan")
    import_batches = relationship("ImportBatch", back_populates="organization", cascade="all, delete-orphan")
    risk_settings = relationship("RiskSettings", back_populates="organization", uselist=False, cascade="all, delete-orphan")
