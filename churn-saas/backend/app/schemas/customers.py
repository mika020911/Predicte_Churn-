from datetime import date
from typing import Dict, List, Literal, Optional

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


class SimulationIn(BaseModel):
    """Valeurs à simuler. Un champ absent reprend la valeur de l'observation active.

    Aucune valeur n'est écrite en base : c'est un calcul à la volée.
    """

    model_config = ConfigDict(allow_inf_nan=False)

    tenure_months: Optional[int] = Field(None, ge=0)
    contract_type: Optional[Literal[0, 1]] = None
    mrr_change_pct: Optional[float] = None
    support_tickets_30d: Optional[int] = Field(None, ge=0)
    recency_days: Optional[int] = Field(None, ge=0)
    frequency_trend_30d: Optional[float] = None
    engagement_breadth: Optional[float] = Field(None, ge=0, le=1)
    payment_failures_90d: Optional[int] = Field(None, ge=0)
    plan_tier_rank: Optional[float] = Field(None, ge=0, le=1)


class SimulationRead(BaseModel):
    baseline_score: float
    simulated_score: float
    delta: float
    risk_level: str
    top_reasons: List[RiskReason] = Field(default_factory=list)
    shap_values: Dict[str, float] = Field(default_factory=dict)


