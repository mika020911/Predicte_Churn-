import pytest


def test_register_user_success(client):
    """Test de création réussie d'une organisation et d'un utilisateur admin."""
    payload = {
        "email": "test@company.com",
        "password": "Password123!",
        "full_name": "Test User",
        "organization_name": "Test Company",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@company.com"
    assert data["full_name"] == "Test User"
    assert data["role"] == "admin"
    assert "id" in data
    assert "organization_id" in data


def test_register_duplicate_email(client):
    """Test qu'une inscription avec un email déjà existant échoue avec une 409."""
    payload = {
        "email": "duplicate@company.com",
        "password": "Password123!",
        "full_name": "User One",
        "organization_name": "Company One",
    }
    # Première inscription
    client.post("/api/v1/auth/register", json=payload)

    # Seconde inscription avec le même email
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409
    assert response.json()["detail"] == "Un compte existe déjà avec cet email"


def test_login_success(client):
    """Test de la connexion JSON et récupération d'un access token JWT valide."""
    # Création du compte
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "login@company.com",
            "password": "Password123!",
            "full_name": "Login User",
            "organization_name": "Login Org",
        },
    )

    # Connexion
    login_response = client.post(
        "/api/v1/auth/login/json",
        json={"email": "login@company.com", "password": "Password123!"},
    )
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"


def test_login_wrong_password(client):
    """Test qu'un mot de passe incorrect retourne une erreur 401."""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "wrongpwd@company.com",
            "password": "CorrectPassword123!",
            "full_name": "User",
            "organization_name": "Org",
        },
    )

    response = client.post(
        "/api/v1/auth/login/json",
        json={"email": "wrongpwd@company.com", "password": "BadPassword!"},
    )
    assert response.status_code == 401


def test_read_me_authenticated(client):
    """Test de la récupération du profil utilisateur via endpoint /me avec token."""
    # Inscription & Connexion
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "me@company.com",
            "password": "Password123!",
            "full_name": "Me User",
            "organization_name": "Me Org",
        },
    )
    login_res = client.post(
        "/api/v1/auth/login/json",
        json={"email": "me@company.com", "password": "Password123!"},
    )
    token = login_res.json()["access_token"]

    # Appel /me avec le token Bearer
    me_res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "me@company.com"


def test_read_me_unauthorized(client):
    """Test qu'un appel /me sans token ou avec un token invalide retourne une 401."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401