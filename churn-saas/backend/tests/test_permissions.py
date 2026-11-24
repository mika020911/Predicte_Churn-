"""Matrice des permissions : viewer (lecture), analyst (écriture), admin (administration)."""

from app.models import User

from tests.helpers import create_user, login_headers, register_admin

RISK_PAYLOAD = {"threshold_medium": 0.4, "threshold_high": 0.7}


def _member_headers(client, db_session, *, role: str, email: str) -> dict:
    admin = register_admin(client, email=f"admin-{role}@example.com")
    create_user(
        db_session,
        organization_id=admin["organization_id"],
        email=email,
        role=role,
    )
    return login_headers(client, email)


def test_admin_can_update_risk_settings(client):
    admin = register_admin(client, email="admin-settings@example.com")
    response = client.put(
        "/api/v1/risk-settings",
        json=RISK_PAYLOAD,
        headers=login_headers(client, admin["email"]),
    )
    assert response.status_code == 200


def test_analyst_cannot_update_risk_settings(client, db_session):
    headers = _member_headers(
        client, db_session, role="analyst", email="analyst-settings@example.com"
    )
    response = client.put("/api/v1/risk-settings", json=RISK_PAYLOAD, headers=headers)
    assert response.status_code == 403


def test_viewer_cannot_update_risk_settings(client, db_session):
    headers = _member_headers(
        client, db_session, role="viewer", email="viewer-settings@example.com"
    )
    response = client.put("/api/v1/risk-settings", json=RISK_PAYLOAD, headers=headers)
    assert response.status_code == 403


def test_viewer_can_read_risk_settings_and_customers(client, db_session):
    headers = _member_headers(
        client, db_session, role="viewer", email="viewer-read@example.com"
    )
    assert client.get("/api/v1/risk-settings", headers=headers).status_code == 200
    assert client.get("/api/v1/customers", headers=headers).status_code == 200


def test_viewer_cannot_save_import_mapping(client, db_session):
    headers = _member_headers(
        client, db_session, role="viewer", email="viewer-import@example.com"
    )
    response = client.put("/api/v1/imports/mapping", json={}, headers=headers)
    assert response.status_code == 403


def test_analyst_can_save_import_mapping(client, db_session):
    headers = _member_headers(
        client, db_session, role="analyst", email="analyst-import@example.com"
    )
    response = client.put("/api/v1/imports/mapping", json={}, headers=headers)
    assert response.status_code == 200


def test_disabled_admin_is_rejected(client, db_session):
    """Un admin désactivé doit être refusé par require_roles (via get_current_active_user)."""
    admin = register_admin(client, email="disabled-admin@example.com")
    headers = login_headers(client, admin["email"])

    user = db_session.query(User).filter(User.email == admin["email"]).first()
    user.is_active = False
    db_session.commit()

    response = client.put("/api/v1/risk-settings", json=RISK_PAYLOAD, headers=headers)
    assert response.status_code == 403
