"""Paramètres d'organisation : clé API (réservé aux administrateurs)."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.core.roles import ROLE_ADMIN
from app.models import Organization, User
from app.schemas.settings import ApiKeyRotateRead, ApiKeyStatus
from app.services.api_key_service import api_key_status, rotate_api_key

router = APIRouter(prefix="/settings", tags=["Paramètres"])

admin_only = require_roles(ROLE_ADMIN)


@router.get("/api-key", response_model=ApiKeyStatus)
def get_api_key_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only),
):
    """Indique si une clé existe, son préfixe et sa date de création.

    La clé complète n'est jamais renvoyée par cette route.
    """
    organization = db.get(Organization, current_user.organization_id)
    return api_key_status(organization)


@router.post("/api-key/rotate", response_model=ApiKeyRotateRead)
def rotate_organization_api_key(
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only),
):
    """Crée ou remplace la clé API. La nouvelle clé n'est affichée qu'ici.

    L'ancienne clé est invalidée immédiatement : seule la nouvelle empreinte
    est conservée.
    """
    organization = db.get(Organization, current_user.organization_id)
    raw_key = rotate_api_key(organization)
    db.commit()
    db.refresh(organization)

    return {**api_key_status(organization), "api_key": raw_key}
