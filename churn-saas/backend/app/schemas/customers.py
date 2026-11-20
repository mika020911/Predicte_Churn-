from datetime import date
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

class RiskReason(BaseModel):
    feature:str
    impact:float
    message:str

class CustomerRiskRead(BaseModel):
    #un client avec sa prediction active
    customer_id:int
    external_id:str
    name:Optional[str]=None
    email:Optional[str]=None
    score:float
    risk_level:str
    snapshot_date:date
    top_reasons:List[RiskReason] = Field(default_factory=list)
    model_version:Optional[str]=None

class CustomerObservationRead(BaseModel):
    """Valeurs de l'observation la plus récente utilisée par le modèle."""
    snapshot_date:date
    tenure_months:int
    contract_type:int
    mrr_change_pct:float
    support_tickets_30d:int
    recency_days:int
    frequency_trend_30d:float
    engagement_breadth:float
    payment_failures_90d:int
    plan_tier_rank:float

    model_config = ConfigDict(from_attributes=True)


class CustomerDetailRead(CustomerRiskRead):
    phone_number:Optional[str]=None
    shap_values:Dict[str,float] = Field(default_factory=dict)
    observation:CustomerObservationRead


class CustomerListResponse(BaseModel):
    items:List[CustomerRiskRead]
    total:int
    page:int
    page_size:int
    total_pages:int
    zone_counts:Dict[str,int]


