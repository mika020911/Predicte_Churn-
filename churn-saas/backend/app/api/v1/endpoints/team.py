"""Équipe : membres de l'organisation et invitations (réservé aux administrateurs)."""

from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.core.roles import ROLE_ADMIN, ROLE_ANALYST
from app.models import Customer, Organization, User, UserInvitation
from app.schemas.team import (
    InvitationCreate,
    InvitationRead,
    UserUpdate,
)
from app.schemas.user import UserRead
from app.services import invitation_service

router = APIRouter(prefix="/users", tags=["Équipe"])

admin_only = require_roles(ROLE_ADMIN)


def _get_member(db: Session, organization_id: int, user_id: int) -> User:
    member = (
        db.query(User)
        .filter(User.id == user_id, User.organization_id == organization_id)
        .first()
    )
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membre introuvable.",
        )
    return member


def _get_invitation(
    db: Session, organization_id: int, invitation_id: int
) -> UserInvitation:
    invitation = (
        db.query(UserInvitation)
        .filter(
            UserInvitation.id == invitation_id,
            UserInvitation.organization_id == organization_id,
        )
        .first()
    )
    if invitation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation introuvable.",
        )
    return invitation


def _clear_owned_customers(db: Session, user_id: int) -> None:
    """Détache les clients suivis par un membre qui n'est plus actif."""
    (
        db.query(Customer)
        .filter(Customer.owner_user_id == user_id)
        .update({Customer.owner_user_id: None}, synchronize_session=False)
    )


def _ensure_admin_remains(
    db: Session,
    organization_id: int,
    target: User,
    *,
    new_role: str | None = None,
    new_is_active: bool | None = None,
) -> None:
    """Refuse une modification qui laisserait l'organisation sans admin actif."""
    if target.role != ROLE_ADMIN or not target.is_active:
        return

    role_after = new_role if new_role is not None else target.role
    active_after = (
        new_is_active if new_is_active is not None else target.is_active
    )
    if role_after == ROLE_ADMIN and active_after:
        return

    other_admins = (
        db.query(User)
        .filter(
            User.organization_id == organization_id,
            User.role == ROLE_ADMIN,
            User.is_active.is_(True),
            User.id != target.id,
        )
        .count()
    )
    if other_admins == 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Impossible de retirer le dernier administrateur actif.",
        )


@router.get("", response_model=List[UserRead])
def list_members(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(ROLE_ADMIN, ROLE_ANALYST)),
):
    """Membres de l'organisation, actifs et désactivés.

    Lecture ouverte aux analystes (nécessaire à l'attribution des actions de
    rétention) ; les écritures et les invitations restent réservées aux admins.
    """
    return (
        db.query(User)
        .filter(User.organization_id == current_user.organization_id)
        .order_by(User.id)
        .all()
    )


@router.get("/invitations", response_model=List[InvitationRead])
def list_invitations(
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only),
):
    """Invitations de l'organisation, les plus récentes d'abord."""
    invitations = (
        db.query(UserInvitation)
        .filter(UserInvitation.organization_id == current_user.organization_id)
        .order_by(UserInvitation.created_at.desc(), UserInvitation.id.desc())
        .all()
    )
    now = datetime.now(timezone.utc)
    return [
        invitation_service.serialize_invitation(invitation, now)
        for invitation in invitations
    ]


@router.post(
    "/invitations",
    response_model=InvitationRead,
    status_code=status.HTTP_201_CREATED,
)
def create_invitation(
    payload: InvitationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only),
):
    """Crée une invitation. Le lien n'est renvoyé qu'ici (jamais dans la liste)."""
    organization = db.get(Organization, current_user.organization_id)
    invitation, raw_token, email_sent = invitation_service.create_invitation(
        db,
        organization,
        current_user,
        str(payload.email),
        payload.role,
    )
    return invitation_service.serialize_invitation(
        invitation,
        datetime.now(timezone.utc),
        raw_token=raw_token,
        email_sent=email_sent,
    )


@router.post(
    "/invitations/{invitation_id}/resend",
    response_model=InvitationRead,
)
def resend_invitation(
    invitation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only),
):
    invitation = _get_invitation(
        db, current_user.organization_id, invitation_id
    )
    invitation, raw_token, email_sent = invitation_service.resend_invitation(
        db, invitation
    )
    return invitation_service.serialize_invitation(
        invitation,
        datetime.now(timezone.utc),
        raw_token=raw_token,
        email_sent=email_sent,
    )


@router.delete(
    "/invitations/{invitation_id}",
    response_model=InvitationRead,
)
def revoke_invitation(
    invitation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only),
):
    invitation = _get_invitation(
        db, current_user.organization_id, invitation_id
    )
    invitation = invitation_service.revoke_invitation(db, invitation)
    return invitation_service.serialize_invitation(
        invitation, datetime.now(timezone.utc)
    )


@router.patch("/{user_id}", response_model=UserRead)
def update_member(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only),
):
    """Modifie le nom, le rôle ou l'activation d'un membre."""
    member = _get_member(db, current_user.organization_id, user_id)

    if member.id == current_user.id:
        if payload.role is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous ne pouvez pas modifier votre propre rôle.",
            )
        if payload.is_active is False:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous ne pouvez pas désactiver votre propre compte.",
            )

    _ensure_admin_remains(
        db,
        current_user.organization_id,
        member,
        new_role=payload.role,
        new_is_active=payload.is_active,
    )

    if payload.full_name is not None:
        member.full_name = payload.full_name.strip()
    if payload.role is not None:
        member.role = payload.role
    if payload.is_active is not None:
        member.is_active = payload.is_active
        if payload.is_active is False:
            _clear_owned_customers(db, member.id)

    db.commit()
    db.refresh(member)
    return member


@router.delete("/{user_id}", response_model=UserRead)
def deactivate_member(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only),
):
    """Désactivation logique : aucune suppression physique n'est faite."""
    member = _get_member(db, current_user.organization_id, user_id)

    if member.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous ne pouvez pas désactiver votre propre compte.",
        )

    _ensure_admin_remains(
        db, current_user.organization_id, member, new_is_active=False
    )

    if member.is_active:
        member.is_active = False
    _clear_owned_customers(db, member.id)
    db.commit()
    db.refresh(member)
    return member
