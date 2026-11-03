from datetime import datetime
from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, ConfigDict, field_validator

from app.services.import_service import INTERNAL_FIELDS


class AnomalyReport(BaseModel):
    row_number: int
    external_id: Optional[str] = None
    error_type: str
    message: str


class ImportBatchRead(BaseModel):
    id: int
    organization_id: int
    uploaded_by_user_id: int
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

class ImportMappingIn(BaseModel):
    column_mapping: Dict[str, Optional[str]] = {}
    contract_values: Dict[str, Literal[0, 1]] = {}
 
    @field_validator("column_mapping")
    @classmethod
    def only_known_fields(cls, value):
        unknown = set(value) - set(INTERNAL_FIELDS)
        if unknown:
            raise ValueError(f"Champs inconnus : {sorted(unknown)}")
        return value
