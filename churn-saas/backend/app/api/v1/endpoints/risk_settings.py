from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.models import User
from app.schemas.risk_settings import RiskSettingsRead, RiskSettingsUpdate
from app.services import risk_settings_service

router = APIRouter(prefix="/risk-settings", tags=["Seuils de risque"])


@router.get("", response_model=RiskSettingsRead)
def read_risk_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Seuils de risque de l'organisation de l'utilisateur connecté."""
    return risk_settings_service.get_risk_settings(db, current_user.organization_id)


@router.put("", response_model=RiskSettingsRead)
def update_risk_settings(
    payload: RiskSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Modifie les seuils et met à jour la zone des prédictions existantes."""
    return risk_settings_service.update_risk_settings(
        db,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        threshold_medium=payload.threshold_medium,
        threshold_high=payload.threshold_high,
    )