"""Invitations d'équipe : création, aperçu, acceptation, renvoi, révocation."""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.core.security import get_password_hash
from app.models import Organization, User, UserInvitation
from app.services.email_service import send_invitation_email


def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def _aware(value: datetime) -> datetime:
    """SQLite renvoie des datetimes naïfs ; on les considère en UTC."""
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def invitation_status(invitation: UserInvitation, now: datetime) -> str:
    if invitation.accepted_at is not None:
        return "accepted"
    if invitation.revoked_at is not None:
        return "revoked"
    if _aware(invitation.expires_at) < now:
        return "expired"
    return "pending"


def build_invite_url(raw_token: str) -> str:
    return (
        f"{settings.frontend_url.rstrip('/')}"
        f"/auth/accept-invitation?token={raw_token}"
    )


def serialize_invitation(
    invitation: UserInvitation,
    now: datetime,
    *,
    raw_token: str | None = None,
    email_sent: bool | None = None,
) -> dict:
    return {
        "id": invitation.id,
        "email": invitation.email,
        "role": invitation.role,
        "status": invitation_status(invitation, now),
        "invited_by_user_id": invitation.invited_by_user_id,
        "expires_at": invitation.expires_at,
        "created_at": invitation.created_at,
        "invite_url": build_invite_url(raw_token) if raw_token else None,
        "email_sent": email_sent,
    }


def create_invitation(
    db: Session,
    organization: Organization,
    invited_by: User,
    email: str,
    role: str,
) -> tuple[UserInvitation, str, bool]:
    """Crée l'invitation, renvoie (invitation, jeton brut, email envoyé)."""
    normalized_email = email.strip().lower()
    existing = db.query(User).filter(User.email == normalized_email).first()
    if existing is not None:
        if not existing.is_active:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Un compte désactivé utilise déjà cette adresse email. "
                    "Un administrateur peut le réactiver depuis la page Équipe."
                ),
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cette adresse email est déjà utilisée.",
        )

    now = datetime.now(timezone.utc)

    # Une seule invitation active par couple organisation / email.
    (
        db.query(UserInvitation)
        .filter(
            UserInvitation.organization_id == organization.id,
            UserInvitation.email == normalized_email,
            UserInvitation.accepted_at.is_(None),
            UserInvitation.revoked_at.is_(None),
        )
        .update(
            {UserInvitation.revoked_at: now},
            synchronize_session=False,
        )
    )

    raw_token = secrets.token_urlsafe(32)
    invitation = UserInvitation(
        organization_id=organization.id,
        email=normalized_email,
        role=role,
        token_hash=hash_token(raw_token),
        invited_by_user_id=invited_by.id,
        expires_at=now + timedelta(hours=settings.invitation_expire_hours),
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)

    email_sent = send_invitation_email(
        invitation.email,
        organization.name,
        invitation.role,
        build_invite_url(raw_token),
    )
    return invitation, raw_token, email_sent


def get_valid_invitation(
    db: Session, raw_token: str
) -> UserInvitation | None:
    now = datetime.now(timezone.utc)
    return (
        db.query(UserInvitation)
        .filter(
            UserInvitation.token_hash == hash_token(raw_token),
            UserInvitation.accepted_at.is_(None),
            UserInvitation.revoked_at.is_(None),
            UserInvitation.expires_at > now,
        )
        .first()
    )


def preview_invitation(db: Session, raw_token: str) -> dict:
    invitation = get_valid_invitation(db, raw_token)
    if invitation is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'invitation est invalide, expirée ou déjà utilisée.",
        )
    organization = db.get(Organization, invitation.organization_id)
    return {
        "email": invitation.email,
        "organization_name": organization.name,
        "role": invitation.role,
        "expires_at": invitation.expires_at,
    }


def accept_invitation(
    db: Session,
    raw_token: str,
    full_name: str,
    password: str,
) -> User:
    invitation = get_valid_invitation(db, raw_token)
    if invitation is None:
        # Un jeton déjà accepté est un conflit (double acceptation), pas une
        # simple invitation invalide. Les jetons expirés/révoqués restent 400.
        already_used = (
            db.query(UserInvitation)
            .filter(
                UserInvitation.token_hash == hash_token(raw_token),
                UserInvitation.accepted_at.is_not(None),
            )
            .first()
        )
        if already_used is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cette invitation a déjà été acceptée.",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'invitation est invalide, expirée ou déjà utilisée.",
        )

    existing = (
        db.query(User).filter(User.email == invitation.email).first()
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un compte existe déjà avec cette adresse email.",
        )

    now = datetime.now(timezone.utc)
    user = User(
        organization_id=invitation.organization_id,
        email=invitation.email,
        full_name=full_name.strip(),
        hashed_password=get_password_hash(password),
        role=invitation.role,
        is_active=True,
    )
    try:
        db.add(user)
        invitation.accepted_at = now

        # Les autres invitations en attente pour cet email deviennent inutiles.
        (
            db.query(UserInvitation)
            .filter(
                UserInvitation.email == invitation.email,
                UserInvitation.id != invitation.id,
                UserInvitation.accepted_at.is_(None),
                UserInvitation.revoked_at.is_(None),
            )
            .update(
                {UserInvitation.revoked_at: now},
                synchronize_session=False,
            )
        )

        db.commit()
    except IntegrityError:
        # Double acceptation simultanée du même jeton : la contrainte d'unicité
        # sur l'email (ou la mise à jour concurrente) a échoué.
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cette invitation a déjà été acceptée.",
        )
    db.refresh(user)
    return user


def resend_invitation(
    db: Session, invitation: UserInvitation
) -> tuple[UserInvitation, str, bool]:
    now = datetime.now(timezone.utc)
    if invitation.accepted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cette invitation a déjà été acceptée.",
        )
    if invitation.revoked_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cette invitation a été révoquée. Crées-en une nouvelle.",
        )

    raw_token = secrets.token_urlsafe(32)
    invitation.token_hash = hash_token(raw_token)
    invitation.expires_at = now + timedelta(
        hours=settings.invitation_expire_hours
    )
    db.commit()
    db.refresh(invitation)

    organization = db.get(Organization, invitation.organization_id)
    email_sent = send_invitation_email(
        invitation.email,
        organization.name,
        invitation.role,
        build_invite_url(raw_token),
    )
    return invitation, raw_token, email_sent


def revoke_invitation(db: Session, invitation: UserInvitation) -> UserInvitation:
    if invitation.accepted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cette invitation a déjà été acceptée.",
        )
    if invitation.revoked_at is None:
        invitation.revoked_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(invitation)
    return invitation
