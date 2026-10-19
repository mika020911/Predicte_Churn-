
from sqlalchemy import Column, Integer, Float, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Observation(Base):
    __tablename__ = "observations"
    __table_args__ = (
        UniqueConstraint("customer_id", "snapshot_date", name="uq_customer_snapshot"),
    )

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    import_batch_id = Column(Integer, ForeignKey("import_batches.id", ondelete="SET NULL"), nullable=True, index=True)

    snapshot_date = Column(Date, nullable=False, index=True)
    tenure_months = Column(Integer, nullable=False)
    contract_type = Column(Integer, nullable=False)  # 0=mensuel, 1=annuel
    mrr_change_pct = Column(Float, nullable=False)
    support_tickets_30d = Column(Integer, nullable=False)
    recency_days = Column(Integer, nullable=False)
    frequency_trend_30d = Column(Float, nullable=False)
    engagement_breadth = Column(Float, nullable=False)
    payment_failures_90d = Column(Integer, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    customer = relationship("Customer", back_populates="observations")
    import_batch = relationship("ImportBatch", back_populates="observations")
    prediction = relationship("Prediction", back_populates="observation", uselist=False)