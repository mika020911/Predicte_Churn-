from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class AnomalyReport(BaseModel):
    row_number: int
    external_id: Optional[str] = None
    error_type: str
    message: str


class ImportBatchRead(BaseModel):
    id: str
    organization_id: str
    uploaded_by_user_id: str
    filename: str
    source: str
    status: str
    total_rows: int
    imported_rows: int
    error_rows: int
    anomaly_report: Optional[List[Dict[str, Any]]] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ImportBatchSummary(BaseModel):
    import_batch_id: str
    filename: str
    status: str
    total_rows: int
    imported_rows: int
    error_rows: int
    created_at: datetime