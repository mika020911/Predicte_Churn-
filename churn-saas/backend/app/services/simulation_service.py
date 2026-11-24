"""Simulation what-if : recalcule un score avec des valeurs modifiées, sans rien écrire."""

from sqlalchemy.orm import Session

from app.services.customer_service import get_customer_detail
from app.services.ml_client import feature_columns, get_predictor
from app.services.risk_settings_service import get_thresholds, risk_level_for


def simulate_customer(
    db: Session,
    organization_id: int,
    customer_id: int,
    overrides: dict,
) -> dict | None:
    """Score simulé à partir de l'observation de la prédiction active.

    Renvoie None si le client est hors organisation ou sans prédiction active.
    Aucune écriture en base : seul `get_predictor().predict` est appelé.
    """
    detail = get_customer_detail(db, organization_id, customer_id)
    if detail is None:
        return None

    observation = detail["observation"]
    record = {column: getattr(observation, column) for column in feature_columns()}
    record.update(overrides)

    result = get_predictor().predict(record)
    threshold_high, threshold_medium = get_thresholds(db, organization_id)
    baseline_score = float(detail["score"])
    simulated_score = float(result["score"])

    return {
        "baseline_score": baseline_score,
        "simulated_score": simulated_score,
        "delta": round(simulated_score - baseline_score, 4),
        "risk_level": risk_level_for(simulated_score, threshold_high, threshold_medium),
        "top_reasons": result["top_reasons"],
        "shap_values": result["shap_values"],
    }
