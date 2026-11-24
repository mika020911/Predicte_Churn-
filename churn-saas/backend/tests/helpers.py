"""Helpers partagés pour les tests (comptes et en-têtes d'authentification)."""

from app.core.security import get_password_hash
from app.models import User

DEFAULT_PASSWORD = "Password123!"


def register_admin(
    client,
    *,
    email: str = "admin@example.com",
    organization_name: str = "Organisation test",
    full_name: str = "Admin Test",
) -> dict:
    """Crée une organisation avec son administrateur via l'inscription publique."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": DEFAULT_PASSWORD,
            "full_name": full_name,
            "organization_name": organization_name,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_user(
    db_session,
    *,
    organization_id: int,
    email: str,
    role: str,
    password: str = DEFAULT_PASSWORD,
    full_name: str | None = None,
    is_active: bool = True,
) -> User:
    """Ajoute un utilisateur d'un rôle donné dans une organisation existante."""
    user = User(
        organization_id=organization_id,
        email=email.lower(),
        full_name=full_name or email.split("@")[0],
        hashed_password=get_password_hash(password),
        role=role,
        is_active=is_active,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def login_headers(client, email: str, password: str = DEFAULT_PASSWORD) -> dict:
    """Connecte un utilisateur et renvoie l'en-tête Authorization prêt à l'emploi."""
    response = client.post(
        "/api/v1/auth/login/json",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}
