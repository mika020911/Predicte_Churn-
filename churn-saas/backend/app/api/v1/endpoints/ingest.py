"""API d'ingestion machine-à-machine, authentifiée par clé API uniquement."""

import json
import logging

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.concurrency import run_in_threadpool
from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_organization_from_api_key
from app.config import settings
from app.models import ImportBatch, Organization
from app.schemas.ingest import IngestRequest, IngestResult
from app.services.import_service import ingest_dataframe
from app.services.prediction_service import generate_predictions_for_batch

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ingest", tags=["Ingestion"])


async def _read_ingest_payload(request: Request) -> IngestRequest:
    """Lit le corps avec un plafond configurable, puis valide le JSON."""
    max_bytes = settings.max_ingest_body_size_mb * 1024 * 1024
    content_length = request.headers.get("content-length")
    if content_length is not None:
        try:
            if int(content_length) > max_bytes:
                raise HTTPException(
                    status.HTTP_413_CONTENT_TOO_LARGE,
                    f"Corps trop volumineux : {settings.max_ingest_body_size_mb} Mo maximum.",
                )
        except ValueError:
            pass  # en-tête invalide : on contrôle la taille réelle ci-dessous

    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > max_bytes:
            raise HTTPException(
                status.HTTP_413_CONTENT_TOO_LARGE,
                f"Corps trop volumineux : {settings.max_ingest_body_size_mb} Mo maximum.",
            )

    if not body:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "Corps JSON manquant."
        )

    try:
        data = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "Corps JSON invalide."
        )

    try:
        return IngestRequest.model_validate(data)
    except ValidationError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=jsonable_encoder(exc.errors()),
        )


def _to_dataframe(payload: IngestRequest) -> pd.DataFrame:
    """Convertit les observations en DataFrame aux noms internes d'import."""
    records = []
    for observation in payload.observations:
        row = observation.model_dump()
        row["customer_name"] = row.pop("name")
        row["customer_email"] = row.pop("email")
        records.append(row)
    return pd.DataFrame(records)


@router.post(
    "/observations",
    response_model=IngestResult,
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "schema": IngestRequest.model_json_schema(),
                    "example": {
                        "observations": [
                            {
                                "customer_id": "CLI-1042",
                                "snapshot_date": "2026-11-01",
                                "name": "Camille Martin",
                                "email": "camille.martin@example.com",
                                "phone_number": "+33612345678",
                                "tenure_months": 18,
                                "contract_type": 1,
                                "mrr_change_pct": -12.5,
                                "support_tickets_30d": 4,
                                "recency_days": 9,
                                "frequency_trend_30d": -0.18,
                                "engagement_breadth": 0.42,
                                "payment_failures_90d": 1,
                                "plan": "Business",
                                "plan_tier_rank": 0.6,
                            }
                        ]
                    },
                }
            },
        }
    },
)
async def ingest_observations(
    request: Request,
    db: Session = Depends(get_db),
    organization: Organization = Depends(get_organization_from_api_key),
):
    """Ingère jusqu'à 5 000 observations pour l'organisation de la clé API.

    Aucun JWT n'est accepté ici : l'organisation vient exclusivement de la clé.
    Les plans non classés et les doublons deviennent des anomalies de ligne ;
    les lignes valides du lot sont importées.
    """
    payload = await _read_ingest_payload(request)
    df = _to_dataframe(payload)

    batch = ImportBatch(
        organization_id=organization.id,
        uploaded_by_user_id=None,
        filename="api_observations",
        source="api",
        status="processing",
        total_rows=len(df),
        imported_rows=0,
        error_rows=0,
        anomaly_report=[],
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)

    batch = await run_in_threadpool(
        ingest_dataframe,
        df,
        batch,
        organization,
        None,
        db,
        extra_columns=("phone_number", "plan_tier_rank"),
        lenient_plans=True,
    )

    # Côté API, des lignes toutes en anomalie (doublons, plans non classés) ne
    # sont pas un échec global : le lot a bien été traité.
    if batch.status == "failed" and not batch.error_message:
        batch.status = "completed"
        db.commit()

    if batch.status == "completed":
        try:
            await run_in_threadpool(
                generate_predictions_for_batch,
                db,
                batch.id,
                organization.id,
            )
        except Exception:
            logger.exception(
                "Échec du calcul des prédictions pour le lot d'ingestion %s",
                batch.id,
            )
            db.rollback()
            batch = db.get(ImportBatch, batch.id)
            batch.error_message = (
                "Ingestion réussie, mais le calcul des prédictions a échoué."
            )
            db.commit()

    return {
        "batch_id": batch.id,
        "status": batch.status,
        "total_rows": batch.total_rows,
        "imported_rows": batch.imported_rows,
        "error_rows": batch.error_rows,
        "anomalies": (batch.anomaly_report or [])[:50],
    }
