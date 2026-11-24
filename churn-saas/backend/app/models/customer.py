from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
from sqlalchemy import UniqueConstraint

class Customer(Base):
    __tablename__ = "customers"
    __table_args__ = (
        UniqueConstraint("organization_id", "external_id", name="uq_org_external_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    external_id = Column(String(100), index=True, nullable=False)
    name = Column(String(255), nullable=True)
    email = Column(String(255), index=True, nullable=True)
    phone_number = Column(String(20), nullable=True)

    # Rétention : statut décidé à la main et propriétaire du suivi.
    retention_status = Column(
        String(20), nullable=False, default="none", server_default="none"
    )
    owner_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    organization = relationship("Organization", back_populates="customers")
    owner = relationship("User", foreign_keys=[owner_user_id])
    observations = relationship("Observation", back_populates="customer", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="customer", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="customer", cascade="all, delete-orphan")
    actions = relationship(
        "CustomerAction",
        back_populates="customer",
        cascade="all, delete-orphan",
        order_by="CustomerAction.id",
    )