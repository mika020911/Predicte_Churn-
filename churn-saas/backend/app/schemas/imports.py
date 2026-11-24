from datetime import datetime
from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, ConfigDict, field_validator

from app.services.import_service import INTERNAL_FIELDS, normalize


class AnomalyReport(BaseModel):
    row_number: int
    external_id: Optional[str] = None
    error_type: str
    message: str


class ImportBatchRead(BaseModel):
    id: int
    organization_id: int
    uploaded_by_user_id: Optional[int] = None
    filename: str
    source: str
    status: str
    total_rows: int
    imported_rows: int
    error_rows: int
    anomaly_report: Optional[List[AnomalyReport]] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class ImportBatchSummary(BaseModel):
    import_batch_id: int
    filename: str
    status: str
    total_rows: int
    imported_rows: int
    error_rows: int
    created_at: datetime


class PlanOption(BaseModel):
    """Plan de l'organisation et son rang de gamme (0 = entrée, 1 = haut de gamme)."""

    name: str
    rank: float


class ImportMappingIn(BaseModel):
    column_mapping: Dict[str, Optional[str]] = {}
    contract_values: Dict[str, Literal[0, 1]] = {}
    # Plans classés du MOINS cher au PLUS cher. Liste complète : elle remplace le classement enregistré.
    plan_order: List[str] = []
 
    @field_validator("column_mapping")
    @classmethod
    def only_known_fields(cls, value):
        unknown = set(value) - set(INTERNAL_FIELDS)
        if unknown:
            raise ValueError(f"Champs inconnus : {sorted(unknown)}")
        return value

    @field_validator("plan_order")
    @classmethod
    def clean_plan_order(cls, value):
        plans = [p.strip() for p in value]
        if any(not p or len(p) > 100 for p in plans):
            raise ValueError("Chaque plan doit contenir entre 1 et 100 caractères.")
        if len(plans) > 50:
            raise ValueError("50 plans au maximum.")
        keys = [normalize(p) for p in plans]
        if len(set(keys)) != len(keys):
            raise ValueError("Un plan apparaît plusieurs fois dans le classement.")
        return plans
