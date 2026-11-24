from datetime import datetime, timezone
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db, require_roles
from app.core.roles import ROLE_ADMIN, ROLE_ANALYST
from app.models import Customer, CustomerAction, User
from app.schemas.customers import (
    CustomerDetailRead,
    CustomerHistoryRead,
    CustomerListResponse,
    SimulationIn,
    SimulationRead,
)
from app.schemas.retention import (
    CustomerActionCreate,
    CustomerActionRead,
    CustomerRetentionRead,
    CustomerRetentionUpdate,
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
    rows, truncated = customer_service.export_customers(
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
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    if truncated:
        headers["X-Export-Truncated"] = "true"
    return Response(content=content, media_type=media_type, headers=headers)


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


def _get_customer(db: Session, organization_id: int, customer_id: int) -> Customer:
    customer = (
        db.query(Customer)
        .filter(
            Customer.id == customer_id,
            Customer.organization_id == organization_id,
        )
        .first()
    )
    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client introuvable.",
        )
    return customer


@router.patch("/{customer_id}", response_model=CustomerRetentionRead)
def update_customer_retention(
    customer_id: int,
    payload: CustomerRetentionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(ROLE_ADMIN, ROLE_ANALYST)),
):
    """Met à jour le statut de rétention et le propriétaire du suivi.

    Le statut se change à la main ; les actions, elles, alimentent un journal.
    """
    customer = _get_customer(db, current_user.organization_id, customer_id)

    if "owner_user_id" in payload.model_fields_set:
        owner_id = payload.owner_user_id
        if owner_id is not None:
            owner = (
                db.query(User)
                .filter(
                    User.id == owner_id,
                    User.organization_id == current_user.organization_id,
                    User.is_active.is_(True),
                    User.role.in_([ROLE_ADMIN, ROLE_ANALYST]),
                )
                .first()
            )
            if owner is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "Le propriétaire doit être un utilisateur actif "
                        "(administrateur ou analyste) de la même organisation."
                    ),
                )
        customer.owner_user_id = owner_id

    if payload.retention_status is not None:
        customer.retention_status = payload.retention_status

    db.commit()
    db.refresh(customer)
    return {
        "customer_id": customer.id,
        "external_id": customer.external_id,
        "name": customer.name,
        "retention_status": customer.retention_status,
        "owner_user_id": customer.owner_user_id,
    }


@router.get(
    "/{customer_id}/actions", response_model=List[CustomerActionRead]
)
def list_customer_actions(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Journal des actions de rétention d'un client de l'organisation."""
    _get_customer(db, current_user.organization_id, customer_id)
    return (
        db.query(CustomerAction)
        .filter(CustomerAction.customer_id == customer_id)
        .order_by(CustomerAction.created_at.desc(), CustomerAction.id.desc())
        .all()
    )


@router.post(
    "/{customer_id}/actions",
    response_model=CustomerActionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_customer_action(
    customer_id: int,
    payload: CustomerActionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(ROLE_ADMIN, ROLE_ANALYST)),
):
    """Ajoute une action au journal du client."""
    _get_customer(db, current_user.organization_id, customer_id)

    action = CustomerAction(
        customer_id=customer_id,
        created_by_user_id=current_user.id,
        action_type=payload.action_type,
        status=payload.status,
        note=payload.note,
        due_date=payload.due_date,
        completed_at=(
            datetime.now(timezone.utc) if payload.status == "done" else None
        ),
    )
    db.add(action)
    db.commit()
    db.refresh(action)
    return action
