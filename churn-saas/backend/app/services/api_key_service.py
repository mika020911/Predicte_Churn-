"""Génération et empreinte des clés API d'organisation.

La clé complète n'est jamais stockée : seule son empreinte SHA-256 est conservée.
Les 8 premiers caractères servent de préfixe visible dans l'interface.
"""

import hashlib
import secrets
from datetime import datetime, timezone

API_KEY_PREFIX = "cs_"
API_KEY_VISIBLE_LENGTH = 8


def generate_api_key() -> str:
    """Nouvelle clé en clair : ``cs_`` suivi de 32 octets aléatoires encodés."""
    return f"{API_KEY_PREFIX}{secrets.token_urlsafe(32)}"


def hash_api_key(raw_key: str) -> str:
    """Empreinte SHA-256 hexadécimale d'une clé en clair."""
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def rotate_api_key(organization) -> str:
    """Remplace la clé de l'organisation et renvoie la nouvelle clé en clair.

    L'ancienne clé devient immédiatement invalide puisque son empreinte est
    écrasée. L'appelant doit committer la session.
    """
    raw_key = generate_api_key()
    organization.api_key_hash = hash_api_key(raw_key)
    organization.api_key_prefix = raw_key[:API_KEY_VISIBLE_LENGTH]
    organization.api_key_created_at = datetime.now(timezone.utc)
    return raw_key


def api_key_status(organization) -> dict:
    """Résumé sans secret : existence, préfixe visible et date de création."""
    return {
        "exists": bool(organization.api_key_hash),
        "prefix": organization.api_key_prefix,
        "created_at": organization.api_key_created_at,
    }
