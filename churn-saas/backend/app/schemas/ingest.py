"""Schémas de l'API d'ingestion par clé API."""

from datetime import date
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

MAX_INGEST_ROWS = 5000


class ObservationIn(BaseModel):
    """Une observation au format interne de l'API (pas de mapping CSV)."""

    model_config = ConfigDict(extra="forbid")

    customer_id: str = Field(min_length=1, max_length=100)
    snapshot_date: date
    name: Optional[str] = Field(None, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone_number: Optional[str] = Field(None, max_length=20)

    tenure_months: int = Field(ge=0)
    contract_type: Literal[0, 1]
    mrr_change_pct: float
    support_tickets_30d: int = Field(ge=0)
    recency_days: int = Field(ge=0)
    frequency_trend_30d: float
    engagement_breadth: float = Field(ge=0, le=1)
    payment_failures_90d: int = Field(ge=0)

    plan: Optional[str] = Field(None, max_length=100)
    plan_tier_rank: Optional[float] = Field(None, ge=0, le=1)

    @field_validator("customer_id", mode="before")
    @classmethod
    def coerce_customer_id(cls, value):
        return str(value).strip() if value is not None else value


class IngestRequest(BaseModel):
    observations: List[ObservationIn] = Field(
        ..., min_length=1, max_length=MAX_INGEST_ROWS
    )


class IngestAnomaly(BaseModel):
    row_number: int
    external_id: Optional[str] = None
    error_type: str
    message: str


class IngestResult(BaseModel):
    batch_id: int
    status: str
    total_rows: int
    imported_rows: int
    error_rows: int
    anomalies: List[IngestAnomaly] = Field(default_factory=list)
