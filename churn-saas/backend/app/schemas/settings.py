"""Schémas des paramètres d'organisation (clé API)."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ApiKeyStatus(BaseModel):
    """État de la clé API : jamais la clé elle-même."""

    exists: bool
    prefix: Optional[str] = None
    created_at: Optional[datetime] = None


class ApiKeyRotateRead(ApiKeyStatus):
    """Réponse de rotation : la clé en clair n'apparaît qu'ici, une seule fois."""

    api_key: str
