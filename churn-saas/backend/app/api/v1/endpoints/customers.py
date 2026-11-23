from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db, require_roles
from app.core.roles import ROLE_ADMIN, ROLE_ANALYST
from app.models import User
from app.schemas.customers import (
    CustomerDetailRead,
    CustomerHistoryRead,
    CustomerListResponse,
    SimulationIn,
    SimulationRead,
)
from app.services import customer_service, export_service, simulation_service

router = APIRouter(prefix="/customers", tags=["Clients"])


@router.get("", response_model=CustomerListResponse)
def list_customers(
    zone: Optional[Literal["low", "medium", "high"]] = Query(
        None, description="Filtre par zone de risque",
        ),
        search: Optional[str] = Query(
            None, 
            max_length=100,
            description="Recherche par nom ou identifiant externe du client ",
        ),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Clients de l'organisation avec leur score actif, du plus risqué au moins risqué."""
    return customer_service.list_customers(db, current_user.organization_id, zone, page, page_size, search,)


EXPORT_HEADERS = [
    "customer_id",
    "external_id",
    "name",
    "email",
    "phone_number",
    "score",
    "risk_level",
    "snapshot_date",
    "model_version",
    "top_reasons",
]


@router.get("/export")
def export_customers(
    format: Literal["csv", "xlsx"] = Query("csv"),
    zone: Optional[Literal["low", "medium", "high"]] = Query(None),
    search: Optional[str] = Query(None, max_length=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Export des clients filtrés (mêmes filtres que la liste), plafonné à 50 000 lignes.

    Déclaré avant /{customer_id} pour ne pas être capturé comme un identifiant.
    """
    rows = customer_service.export_customers(
        db,
        current_user.organization_id,
        zone,
        search,
        export_service.MAX_EXPORT_ROWS,
    )
    content, media_type, extension = export_service.render_export(
        format, EXPORT_HEADERS, rows
    )
    filename = export_service.export_filename("clients", extension)
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{customer_id}", response_model=CustomerDetailRead)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Fiche d'un client : prédiction active, raisons, valeurs SHAP et observation."""
    detail = customer_service.get_customer_detail(
        db, current_user.organization_id, customer_id
    )
    if detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client introuvable ou sans prédiction active.",
        )
    return detail


@router.get("/{customer_id}/history", response_model=CustomerHistoryRead)
def get_customer_history(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Toutes les prédictions du client, de la plus ancienne à la plus récente."""
    history = customer_service.get_customer_history(
        db, current_user.organization_id, customer_id
    )
    if history is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client introuvable.",
        )
    return history


@router.post("/{customer_id}/simulate", response_model=SimulationRead)
async def simulate_customer(
    customer_id: int,
    payload: SimulationIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(ROLE_ADMIN, ROLE_ANALYST)),
):
    """Score what-if : mêmes features que la prédiction active, avec les valeurs fournies.

    Aucune prédiction ni observation n'est créée ou modifiée.
    """
    result = await run_in_threadpool(
        simulation_service.simulate_customer,
        db,
        current_user.organization_id,
        customer_id,
        payload.model_dump(exclude_none=True),
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client introuvable ou sans prédiction active.",
        )
    return result
