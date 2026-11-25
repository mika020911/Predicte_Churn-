from sqlalchemy import JSON, Column, String, Integer, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Organization(Base):
    __tablename__ = "organizations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    # Clé API : seule l'empreinte SHA-256 est stockée, jamais la clé en clair.
    api_key_hash = Column(String(64), unique=True, index=True, nullable=True)
    api_key_prefix = Column(String(16), nullable=True)
    api_key_created_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    column_mapping = Column(JSON, nullable=True, default=dict)    # champ interne -> colonne du CSV
    contract_mapping = Column(JSON, nullable=True, default=dict)  # valeur du CSV -> 0 ou 1
    plan_mapping = Column(JSON, nullable=True, default=dict)      # plan (normalisé) -> rang de gamme entre 0 et 1

    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    customers = relationship("Customer", back_populates="organization", cascade="all, delete-orphan")
    import_batches = relationship("ImportBatch", back_populates="organization", cascade="all, delete-orphan")
    risk_settings = relationship("RiskSettings", back_populates="organization", uselist=False, cascade="all, delete-orphan")
