from datetime import date
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

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

class CustomerRiskResponse(BaseModel):
    items:List[CustomerRiskRead]
    total:int
    page:int
    page_size:int
    total_pages:int
    zone_counts:Dict[str,int]


