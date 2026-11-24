"""Journal des actions de rétention, toutes organisations confondues."""

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db, require_roles
from app.core.roles import ROLE_ADMIN, ROLE_ANALYST
from app.models import Customer, CustomerAction, User
from app.schemas.retention import (
    ActionStatus,
    CustomerActionRead,
    CustomerActionUpdate,
)

router = APIRouter(prefix="/actions", tags=["Actions de rétention"])


def _org_actions_query(db: Session, organization_id: int):
    """Actions dont le client appartient à l'organisation (pas de colonne org)."""
    return (
        db.query(CustomerAction)
        .join(Customer, Customer.id == CustomerAction.customer_id)
        .filter(Customer.organization_id == organization_id)
    )


@router.get("", response_model=List[CustomerActionRead])
def list_actions(
    status_filter: Optional[ActionStatus] = Query(None, alias="status"),
    owner: Optional[int] = Query(None, ge=1),
    overdue: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Actions de l'organisation, filtrables par statut, propriétaire et retard.

    `owner` cible le propriétaire du client (`customers.owner_user_id`).
    Une action est en retard si son échéance est passée et qu'elle n'est ni
    terminée ni annulée.
    """
    query = _org_actions_query(db, current_user.organization_id)

    if status_filter is not None:
        query = query.filter(CustomerAction.status == status_filter)
    if owner is not None:
        query = query.filter(Customer.owner_user_id == owner)
    if overdue:
        today = datetime.now(timezone.utc).date()
        query = query.filter(
            CustomerAction.due_date.is_not(None),
            CustomerAction.due_date < today,
            CustomerAction.status.in_(("todo", "in_progress")),
        )

    return (
        query.order_by(
            CustomerAction.due_date.is_(None),
            CustomerAction.due_date.asc(),
            CustomerAction.id.desc(),
        )
        .all()
    )


@router.patch("/{action_id}", response_model=CustomerActionRead)
def update_action(
    action_id: int,
    payload: CustomerActionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(ROLE_ADMIN, ROLE_ANALYST)),
):
    """Met à jour une action. L'annulation passe par `status=cancelled`.

    Aucune suppression physique : le journal reste complet.
    """
    action = (
        _org_actions_query(db, current_user.organization_id)
        .filter(CustomerAction.id == action_id)
        .first()
    )
    if action is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Action introuvable.",
        )

    fields = payload.model_fields_set
    if "action_type" in fields and payload.action_type is not None:
        action.action_type = payload.action_type
    if "status" in fields and payload.status is not None:
        action.status = payload.status
        if payload.status == "done":
            if action.completed_at is None:
                action.completed_at = datetime.now(timezone.utc)
        else:
            action.completed_at = None
    if "note" in fields:
        action.note = payload.note
    if "due_date" in fields:
        action.due_date = payload.due_date

    db.commit()
    db.refresh(action)
    return action
