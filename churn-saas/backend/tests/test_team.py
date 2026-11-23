"""Tests du lot Équipe : membres, invitations, verrouillages et isolation."""

from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi import HTTPException

from app.models import Organization, User, UserInvitation


PASSWORD = "Password123!"


def token_from_url(url: str) -> str:
    return parse_qs(urlparse(url).query)["token"][0]


def invite(client, headers, email: str, role: str = "analyst"):
    response = client.post(
        "/api/v1/users/invitations",
        json={"email": email, "role": role},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    data = response.json()
    return data, token_from_url(data["invite_url"])


def accept(client, token: str, full_name: str = "Nouveau Membre", password: str = PASSWORD):
    return client.post(
        "/api/v1/auth/invitations/accept",
        json={"token": token, "full_name": full_name, "password": password},
    )


def admin_of(client, email="team-admin@example.com"):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": PASSWORD,
            "full_name": "Admin",
            "organization_name": "Org Équipe",
        },
    )
    assert response.status_code == 201, response.text
    token = client.post(
        "/api/v1/auth/login/json",
        json={"email": email, "password": PASSWORD},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, response.json()["organization_id"]


# ------------------------------------------------------------------ invitations
def test_admin_can_invite_a_member(client):
    headers, _ = admin_of(client)

    data, token = invite(client, headers, "analyst@example.com", "analyst")

    assert data["status"] == "pending"
    assert data["role"] == "analyst"
    assert token
    assert data["email_sent"] is True  # dry-run en test


def test_analyst_cannot_invite(client, db_session):
    headers, organization_id = admin_of(client)
    from tests.helpers import create_user, login_headers

    create_user(
        db_session,
        organization_id=organization_id,
        email="analyst@example.com",
        role="analyst",
    )
    response = client.post(
        "/api/v1/users/invitations",
        json={"email": "other@example.com", "role": "viewer"},
        headers=login_headers(client, "analyst@example.com"),
    )
    assert response.status_code == 403


def test_viewer_cannot_list_members(client, db_session):
    from tests.helpers import create_user, login_headers

    headers, organization_id = admin_of(client)
    create_user(
        db_session,
        organization_id=organization_id,
        email="viewer@example.com",
        role="viewer",
    )
    response = client.get(
        "/api/v1/users", headers=login_headers(client, "viewer@example.com")
    )
    assert response.status_code == 403


def test_existing_member_email_is_rejected(client, db_session):
    headers, organization_id = admin_of(client)

    response = client.post(
        "/api/v1/users/invitations",
        json={"email": "team-admin@example.com", "role": "analyst"},
        headers=headers,
    )

    assert response.status_code == 409


def test_email_of_another_organization_is_rejected(client, db_session):
    headers, _ = admin_of(client)
    other = Organization(name="Autre")
    db_session.add(other)
    db_session.commit()
    from tests.helpers import create_user

    create_user(
        db_session,
        organization_id=other.id,
        email="foreign@example.com",
        role="analyst",
    )

    response = client.post(
        "/api/v1/users/invitations",
        json={"email": "foreign@example.com", "role": "analyst"},
        headers=headers,
    )

    assert response.status_code == 409


def test_disabled_user_email_requires_reactivation(client, db_session):
    headers, organization_id = admin_of(client)
    from tests.helpers import create_user

    disabled = create_user(
        db_session,
        organization_id=organization_id,
        email="disabled@example.com",
        role="analyst",
        is_active=False,
    )

    response = client.post(
        "/api/v1/users/invitations",
        json={"email": "disabled@example.com", "role": "analyst"},
        headers=headers,
    )
    assert response.status_code == 409
    assert "désactivé" in response.json()["detail"]

    reactivated = client.patch(
        f"/api/v1/users/{disabled.id}",
        json={"is_active": True},
        headers=headers,
    )
    assert reactivated.status_code == 200
    assert reactivated.json()["is_active"] is True


def test_preview_accept_and_auto_login(client, db_session):
    headers, organization_id = admin_of(client)
    _, token = invite(client, headers, "new@example.com", "viewer")

    preview = client.get(
        "/api/v1/auth/invitations/preview", params={"token": token}
    )
    assert preview.status_code == 200
    assert preview.json()["email"] == "new@example.com"
    assert preview.json()["organization_name"] == "Org Équipe"
    assert preview.json()["role"] == "viewer"

    response = accept(client, token, full_name="Nouvelle Personne")
    assert response.status_code == 200, response.text
    access_token = response.json()["access_token"]

    me = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me.status_code == 200
    assert me.json()["email"] == "new@example.com"
    assert me.json()["role"] == "viewer"
    assert me.json()["organization_id"] == organization_id


def test_expired_token_is_refused(client, db_session):
    headers, _ = admin_of(client)
    invitation, token = invite(client, headers, "expired@example.com")

    model = db_session.get(UserInvitation, invitation["id"])
    model.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
    db_session.commit()

    assert client.get(
        "/api/v1/auth/invitations/preview", params={"token": token}
    ).status_code == 400
    assert accept(client, token).status_code == 400


def test_used_token_is_refused(client):
    headers, _ = admin_of(client)
    _, token = invite(client, headers, "once@example.com")

    assert accept(client, token).status_code == 200
    assert accept(client, token).status_code == 400


def test_revoked_invitation_is_refused(client):
    headers, _ = admin_of(client)
    invitation, token = invite(client, headers, "revoked@example.com")

    revoked = client.delete(
        f"/api/v1/users/invitations/{invitation['id']}", headers=headers
    )
    assert revoked.status_code == 200
    assert revoked.json()["status"] == "revoked"

    assert accept(client, token).status_code == 400


def test_resend_invalidates_the_previous_token(client):
    headers, _ = admin_of(client)
    invitation, old_token = invite(client, headers, "resend@example.com")

    response = client.post(
        f"/api/v1/users/invitations/{invitation['id']}/resend", headers=headers
    )
    assert response.status_code == 200
    new_token = token_from_url(response.json()["invite_url"])
    assert new_token != old_token

    assert accept(client, old_token).status_code == 400
    assert accept(client, new_token).status_code == 200


# ------------------------------------------------------------------ membres
def test_admin_can_change_a_member_role(client, db_session):
    headers, organization_id = admin_of(client)
    from tests.helpers import create_user

    member = create_user(
        db_session,
        organization_id=organization_id,
        email="member@example.com",
        role="analyst",
    )

    response = client.patch(
        f"/api/v1/users/{member.id}",
        json={"role": "viewer"},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["role"] == "viewer"


def test_admin_cannot_change_own_role(client, db_session):
    headers, organization_id = admin_of(client)
    admin = (
        db_session.query(User)
        .filter(User.organization_id == organization_id, User.role == "admin")
        .one()
    )

    response = client.patch(
        f"/api/v1/users/{admin.id}", json={"role": "analyst"}, headers=headers
    )

    assert response.status_code == 403


def test_admin_cannot_deactivate_self(client, db_session):
    headers, organization_id = admin_of(client)
    admin = (
        db_session.query(User)
        .filter(User.organization_id == organization_id, User.role == "admin")
        .one()
    )

    assert client.patch(
        f"/api/v1/users/{admin.id}", json={"is_active": False}, headers=headers
    ).status_code == 403
    assert client.delete(
        f"/api/v1/users/{admin.id}", headers=headers
    ).status_code == 403


def test_last_active_admin_is_protected(db_session):
    from app.api.v1.endpoints.team import _ensure_admin_remains

    organization = Organization(name="Solo")
    db_session.add(organization)
    db_session.flush()
    admin = User(
        organization_id=organization.id,
        email="solo@example.com",
        full_name="Solo",
        hashed_password="x",
        role="admin",
        is_active=True,
    )
    db_session.add(admin)
    db_session.commit()

    with pytest.raises(HTTPException) as exc:
        _ensure_admin_remains(
            db_session, organization.id, admin, new_is_active=False
        )
    assert exc.value.status_code == 403


def test_deactivated_member_cannot_log_in(client, db_session):
    headers, organization_id = admin_of(client)
    from tests.helpers import create_user

    member = create_user(
        db_session,
        organization_id=organization_id,
        email="deactivate@example.com",
        role="analyst",
    )
    assert client.delete(
        f"/api/v1/users/{member.id}", headers=headers
    ).status_code == 200

    response = client.post(
        "/api/v1/auth/login/json",
        json={"email": "deactivate@example.com", "password": PASSWORD},
    )
    assert response.status_code == 403


def test_members_are_isolated_by_organization(client, db_session):
    headers, _ = admin_of(client)
    other = Organization(name="Autre")
    db_session.add(other)
    db_session.commit()
    from tests.helpers import create_user

    foreign = create_user(
        db_session, organization_id=other.id, email="foreign2@example.com", role="analyst"
    )

    assert client.patch(
        f"/api/v1/users/{foreign.id}", json={"role": "viewer"}, headers=headers
    ).status_code == 404
    assert client.delete(
        f"/api/v1/users/{foreign.id}", headers=headers
    ).status_code == 404

    members = client.get("/api/v1/users", headers=headers).json()
    assert [member["email"] for member in members] == ["team-admin@example.com"]


def test_shared_password_rule_applies_to_register_and_accept(client):
    short = "court"
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "short@example.com",
            "password": short,
            "full_name": "Court",
            "organization_name": "Court Org",
        },
    )
    assert response.status_code == 422

    headers, _ = admin_of(client)
    _, token = invite(client, headers, "short-accept@example.com")
    assert accept(client, token, password=short).status_code == 422
