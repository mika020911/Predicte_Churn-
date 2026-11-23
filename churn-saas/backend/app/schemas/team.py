"""Schémas de l'équipe : membres et invitations."""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field

from app.core.passwords import Password

Role = Literal["admin", "analyst", "viewer"]
InvitationStatus = Literal["pending", "accepted", "expired", "revoked"]


class InvitationCreate(BaseModel):
    email: EmailStr
    role: Role = "analyst"


class InvitationRead(BaseModel):
    id: int
    email: EmailStr
    role: Role
    status: InvitationStatus
    invited_by_user_id: Optional[int] = None
    expires_at: datetime
    created_at: datetime
    # Renseigné uniquement à la création / au renvoi (le lien n'est jamais re-listed).
    invite_url: Optional[str] = None
    email_sent: Optional[bool] = None


class InvitationPreview(BaseModel):
    email: EmailStr
    organization_name: str
    role: Role
    expires_at: datetime


class InvitationAccept(BaseModel):
    token: str = Field(min_length=20, max_length=200)
    full_name: str = Field(min_length=1, max_length=255)
    password: Password


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    role: Optional[Role] = None
    is_active: Optional[bool] = None
