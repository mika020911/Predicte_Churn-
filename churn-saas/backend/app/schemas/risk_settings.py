from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RiskSettingsRead(BaseModel):
    threshold_medium: float
    threshold_high: float
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class RiskSettingsUpdate(BaseModel):
    """Seuils entre 0 et 1 : score < moyen = vert, moyen <= score < haut = orange, score >= haut = rouge."""
    threshold_medium: float = Field(gt=0, lt=1)
    threshold_high: float = Field(gt=0, lt=1)

    @model_validator(mode="after")
    def medium_must_be_below_high(self):
        if self.threshold_medium >= self.threshold_high:
            raise ValueError("Le seuil moyen doit être strictement inférieur au seuil haut")
        return self