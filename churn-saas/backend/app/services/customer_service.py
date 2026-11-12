"""Consultation des clients avec leur prédiction de risque active."""
import math
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Customer, Observation, Prediction

ZONES = ("low", "medium", "high")


def _active_predictions_query(db: Session, organization_id: int):
    """Base commune : clients de l'organisation ayant une prédiction active."""
    return (
        db.query(Customer, Prediction, Observation.snapshot_date)
        .join(Prediction, Prediction.customer_id == Customer.id)
        .join(Observation, Observation.id == Prediction.observation_id)
        .filter(Customer.organization_id == organization_id, Prediction.is_active.is_(True))
    )


def list_customers(db: Session, organization_id: int, zone: Optional[str], page: int, page_size: int, search: Optional[str]=None) -> dict:
    """Liste paginée, triée par score décroissant, filtrable par zone de risque."""
    query = _active_predictions_query(db, organization_id)
    if zone:
        query = query.filter(Prediction.risk_level == zone)

    search_term = (search or "").strip()
    if search_term:
        pattern = f"%{search_term}%"
        query = query.filter(
            (Customer.name.ilike(pattern)) | (Customer.external_id.ilike(pattern))
        )

    total = query.count()
    rows = (
        query
        # l'identifiant départage les scores égaux : la pagination reste stable
        .order_by(Prediction.score.desc(), Customer.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = [
        {
            "customer_id": customer.id,
            "external_id": customer.external_id,
            "name": customer.name,
            "email": customer.email,
            "score": prediction.score,
            "risk_level": prediction.risk_level,
            "snapshot_date": snapshot_date,
            "top_reasons": prediction.top_reasons or [],
            "model_version": prediction.model_version,
        }
        for customer, prediction, snapshot_date in rows
    ]

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": math.ceil(total / page_size),
        "zone_counts": zone_counts(db, organization_id),
    }


def zone_counts(db: Session, organization_id: int) -> dict:
    """Nombre de clients par zone de risque (prédictions actives de l'organisation)."""
    rows = (
        db.query(Prediction.risk_level, func.count(Prediction.id))
        .join(Customer, Customer.id == Prediction.customer_id)
        .filter(Customer.organization_id == organization_id, Prediction.is_active.is_(True))
        .group_by(Prediction.risk_level)
        .all()
    )
    counts = {zone: 0 for zone in ZONES}
    counts.update({level: n for level, n in rows})
    return counts