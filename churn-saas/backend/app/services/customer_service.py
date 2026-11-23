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


def _apply_filters(query, zone: Optional[str], search: Optional[str]):
    """Filtres communs à la liste et à l'export (zone + nom/identifiant externe)."""
    if zone:
        query = query.filter(Prediction.risk_level == zone)

    search_term = (search or "").strip()
    if search_term:
        pattern = f"%{search_term}%"
        query = query.filter(
            (Customer.name.ilike(pattern)) | (Customer.external_id.ilike(pattern))
        )
    return query


def list_customers(db: Session, organization_id: int, zone: Optional[str], page: int, page_size: int, search: Optional[str]=None) -> dict:
    """Liste paginée, triée par score décroissant, filtrable par zone de risque."""
    query = _apply_filters(
        _active_predictions_query(db, organization_id), zone, search
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


def get_customer_detail(db: Session, organization_id: int, customer_id: int) -> Optional[dict]:
    """Fiche d'un client de l'organisation, avec sa prédiction active et son observation.

    Renvoie None si le client n'existe pas dans cette organisation ou s'il n'a
    aucune prédiction active (même règle que la liste).
    """
    row = (
        db.query(Customer, Prediction, Observation)
        .join(Prediction, Prediction.customer_id == Customer.id)
        .join(Observation, Observation.id == Prediction.observation_id)
        .filter(
            Customer.id == customer_id,
            Customer.organization_id == organization_id,
            Prediction.is_active.is_(True),
        )
        .first()
    )
    if row is None:
        return None

    customer, prediction, observation = row
    return {
        "customer_id": customer.id,
        "external_id": customer.external_id,
        "name": customer.name,
        "email": customer.email,
        "phone_number": customer.phone_number,
        "score": prediction.score,
        "risk_level": prediction.risk_level,
        "snapshot_date": observation.snapshot_date,
        "top_reasons": prediction.top_reasons or [],
        "shap_values": prediction.shap_values or {},
        "model_version": prediction.model_version,
        "observation": observation,
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

def _reasons_text(prediction: Prediction) -> str:
    """Raisons lisibles dans une seule cellule d'export."""
    parts = []
    for reason in prediction.top_reasons or []:
        message = reason.get("message")
        if message:
            parts.append(str(message))
        else:
            parts.append(f"{reason.get('feature', '?')} ({reason.get('impact', 0):+.2f})")
    return " | ".join(parts)


def export_customers(
    db: Session,
    organization_id: int,
    zone: Optional[str],
    search: Optional[str],
    limit: int,
) -> tuple[list[list], bool]:
    """Lignes d'export (mêmes filtres que la liste) et indicateur de troncature."""
    query = _apply_filters(
        _active_predictions_query(db, organization_id), zone, search
    )

    # +1 ligne : permet de savoir si le plafond a été atteint.
    rows = (
        query.order_by(Prediction.score.desc(), Customer.id)
        .limit(limit + 1)
        .all()
    )
    truncated = len(rows) > limit
    rows = rows[:limit]

    export_rows = [
        [
            customer.id,
            customer.external_id,
            customer.name or "",
            customer.email or "",
            customer.phone_number or "",
            prediction.score,
            prediction.risk_level,
            snapshot_date.isoformat(),
            prediction.model_version or "",
            _reasons_text(prediction),
        ]
        for customer, prediction, snapshot_date in rows
    ]
    return export_rows, truncated


def get_customer_history(
    db: Session, organization_id: int, customer_id: int
) -> Optional[dict]:
    """Historique des prédictions d'un client, de la plus ancienne à la plus récente.

    Renvoie None si le client n'appartient pas à l'organisation. `delta` est
    l'écart de score avec la prédiction précédente (None pour la première).
    """
    customer = (
        db.query(Customer)
        .filter(
            Customer.id == customer_id,
            Customer.organization_id == organization_id,
        )
        .first()
    )
    if customer is None:
        return None

    rows = (
        db.query(Prediction, Observation.snapshot_date)
        .join(Observation, Observation.id == Prediction.observation_id)
        .filter(Prediction.customer_id == customer_id)
        .order_by(Observation.snapshot_date.asc(), Prediction.id.asc())
        .all()
    )

    items = []
    previous_score = None
    for prediction, snapshot_date in rows:
        delta = (
            None
            if previous_score is None
            else round(prediction.score - previous_score, 4)
        )
        items.append(
            {
                "prediction_id": prediction.id,
                "snapshot_date": snapshot_date,
                "score": prediction.score,
                "risk_level": prediction.risk_level,
                "top_reasons": prediction.top_reasons or [],
                "model_version": prediction.model_version,
                "delta": delta,
            }
        )
        previous_score = prediction.score

    return {"customer_id": customer.id, "items": items}
