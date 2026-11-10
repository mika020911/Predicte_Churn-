"""Seuils de risque (zones vert / orange / rouge) propres à chaque organisation."""
from sqlalchemy import case, select, update
from sqlalchemy.orm import Session

from app.models import Customer, Prediction, RiskSettings

DEFAULT_THRESHOLD_HIGH = 0.70
DEFAULT_THRESHOLD_MEDIUM = 0.40

def risk_level_for(score:float, threshold_high:float, threshold_medium:float)-> str:
    """Zone de risque d'un score HLM"""
    if score >= threshold_high:
        return "high"
    if score >= threshold_medium:
        return "medium"
    return "low"

def get_thresholds(db:Session, organization_id:int)-> tuple[float, float]:
    """Renvoie (seuil haut, seuil moyen) de l'organisation, ou les valeurs par défaut."""
    row = db.query(RiskSettings).filter(RiskSettings.organization_id == organization_id).first()
    if row is None:
        return (DEFAULT_THRESHOLD_HIGH, DEFAULT_THRESHOLD_MEDIUM)
    return row.threshold_high, row.threshold_medium



def get_risk_settings(db: Session, organization_id: int) -> dict:
    """Seuils de l'organisation, sous une forme prête pour l'API."""
    row = db.query(RiskSettings).filter(RiskSettings.organization_id == organization_id).first()
    if row is None:
        return {"threshold_medium": DEFAULT_THRESHOLD_MEDIUM, "threshold_high": DEFAULT_THRESHOLD_HIGH,
                "updated_at": None}
    return {"threshold_medium": row.threshold_medium, "threshold_high": row.threshold_high,
            "updated_at": row.updated_at}

def update_risk_settings(db: Session, organization_id: int, user_id: int,
                         threshold_medium: float, threshold_high: float) -> dict:
    """Enregistre les nouveaux seuils et met à jour la zone des prédictions déjà calculées."""
    row = db.query(RiskSettings).filter(RiskSettings.organization_id == organization_id).first()
    if row is None:
        row = RiskSettings(organization_id=organization_id)
        db.add(row)
    row.threshold_medium = threshold_medium
    row.threshold_high = threshold_high
    row.updated_by_user_id = user_id
    db.flush()
 
    recompute_risk_levels(db, organization_id, threshold_high, threshold_medium)
    db.commit()
    db.refresh(row)
    return get_risk_settings(db, organization_id)
 
 

def recompute_risk_levels(db: Session, organization_id: int,
                          threshold_high: float, threshold_medium: float) -> int:
    """Recalcule la zone de toutes les prédictions de l'organisation (le score ne change pas).
 
    Sans cela, un changement de seuils ne s'appliquerait qu'aux futurs imports.
    """
    organization_customers = select(Customer.id).where(Customer.organization_id == organization_id)
    new_level = case(
        (Prediction.score >= threshold_high, "high"),
        (Prediction.score >= threshold_medium, "medium"),
        else_="low",
    )
    result = db.execute(
        update(Prediction)
        .where(Prediction.customer_id.in_(organization_customers))
        .values(risk_level=new_level)
        .execution_options(synchronize_session=False)
    )
    return result.rowcount
 
