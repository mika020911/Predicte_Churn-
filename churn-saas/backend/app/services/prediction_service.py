"""Calcule les prédictions de risque pour les observations d'un lot d'import."""
import logging

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Observation, Prediction
from app.services.ml_client import feature_columns, get_predictor
from app.services.risk_settings_service import get_thresholds, risk_level_for  # noqa: F401

logger = logging.getLogger(__name__)

def generate_predictions_for_batch(db: Session, batch_id: int, organization_id: int) -> int:
    """Prédit toutes les observations du lot qui n'ont pas encore de prédiction.

    Renvoie le nombre de prédictions créées.
    """
    observations = (
        db.query(Observation)
        .outerjoin(Prediction, Prediction.observation_id == Observation.id)
        .filter(Observation.import_batch_id == batch_id, Prediction.id.is_(None))
        .all()
    )
    if not observations:
        return 0

    # Seuils propres à l'organisation (valeurs par défaut si elle n'a rien réglé)
    t_high, t_medium = get_thresholds(db, organization_id)

    # Un seul appel au modèle pour tout le lot
    columns = feature_columns()
    records = [{c: getattr(obs, c) for c in columns} for obs in observations]
    results = get_predictor().predict_batch(records)

    for obs, result in zip(observations, results):
        db.add(Prediction(
            customer_id=obs.customer_id,
            observation_id=obs.id,
            score=result["score"],
            risk_level=risk_level_for(result["score"], t_high, t_medium),
            top_reasons=result["top_reasons"],
            shap_values=result["shap_values"],
            model_version=result["model_version"],
            is_active=False,  # l'activation est décidée juste après
        ))
    db.flush()

    _refresh_active_flags(db, {obs.customer_id for obs in observations})
    db.commit()
    return len(results)


def _refresh_active_flags(db: Session, customer_ids: set[int]) -> None:
    """Pour chaque client, seule la prédiction de l'observation la PLUS RÉCENTE reste active."""
    latest = dict(
        db.query(Observation.customer_id, func.max(Observation.snapshot_date))
        .filter(Observation.customer_id.in_(customer_ids))
        .group_by(Observation.customer_id)
        .all()
    )
    rows = (
        db.query(Prediction, Observation.snapshot_date)
        .join(Observation, Observation.id == Prediction.observation_id)
        .filter(Prediction.customer_id.in_(customer_ids))
        .all()
    )
    for prediction, snapshot_date in rows:
        prediction.is_active = snapshot_date == latest[prediction.customer_id]