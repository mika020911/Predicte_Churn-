"""Tests des actions de rétention (étape 7) et du playbook."""

from datetime import date
from types import SimpleNamespace

import pytest

from app.models import (
    Customer,
    CustomerAction,
    ImportBatch,
    Observation,
    Organization,
    Prediction,
)
from app.services.retention_service import DEFAULT_ACTION, suggest_actions
from tests.helpers import create_user, login_headers, register_admin

CUSTOMERS = "/api/v1/customers"
ACTIONS = "/api/v1/actions"

DEFAULT_FEATURES = dict(
    tenure_months=12,
    contract_type=0,
    mrr_change_pct=-10.0,
    support_tickets_30d=2,
    recency_days=25,
    frequency_trend_30d=0.6,
    engagement_breadth=0.3,
    payment_failures_90d=1,
    plan_tier_rank=0.2,
)


def make_customer(
    db,
    organization_id,
    external_id="C1",
    *,
    features=None,
    reasons=None,
    active=True,
    score=0.8,
):
    customer = Customer(
        organization_id=organization_id,
        external_id=external_id,
        name=f"Client {external_id}",
    )
    db.add(customer)
    db.flush()

    batch = ImportBatch(
        organization_id=organization_id,
        filename=f"{external_id}.csv",
        source="csv_upload",
        status="completed",
        total_rows=1,
        imported_rows=1,
        error_rows=0,
        anomaly_report=[],
    )
    db.add(batch)
    db.flush()

    values = {**DEFAULT_FEATURES, **(features or {})}
    observation = Observation(
        customer_id=customer.id,
        import_batch_id=batch.id,
        snapshot_date=date(2026, 11, 1),
        **values,
    )
    db.add(observation)
    db.flush()

    prediction = Prediction(
        customer_id=customer.id,
        observation_id=observation.id,
        score=score,
        risk_level="high",
        top_reasons=reasons if reasons is not None else [],
        shap_values={},
        is_active=active,
        model_version="test-v1",
    )
    db.add(prediction)
    db.commit()
    return customer


def setup_org(client, db_session, email="retention-admin@example.com"):
    admin = register_admin(client, email=email)
    headers = login_headers(client, admin["email"])
    return headers, admin["organization_id"]


def observation(**overrides):
    return SimpleNamespace(**{**DEFAULT_FEATURES, **overrides})


# ------------------------------------------------------------------ playbook
@pytest.mark.parametrize(
    "feature, values, expected_type, expected_text",
    [
        ("recency_days", {"recency_days": 25}, "call", "réactivation"),
        (
            "payment_failures_90d",
            {"payment_failures_90d": 2},
            "other",
            "moyen de paiement",
        ),
        (
            "frequency_trend_30d",
            {"frequency_trend_30d": 0.6},
            "onboarding",
            "onboarding",
        ),
        (
            "engagement_breadth",
            {"engagement_breadth": 0.2},
            "onboarding",
            "onboarding",
        ),
        (
            "support_tickets_30d",
            {"support_tickets_30d": 3},
            "other",
            "support",
        ),
        ("mrr_change_pct", {"mrr_change_pct": -12.0}, "discount", "forfait"),
        ("contract_type", {"contract_type": 0}, "email", "annuel"),
        ("plan_tier_rank", {"plan_tier_rank": 0.1}, "email", "montée en gamme"),
    ],
)
def test_playbook_maps_each_actionable_feature(
    feature, values, expected_type, expected_text
):
    result = suggest_actions(
        observation(**values),
        [{"feature": feature, "impact": 0.5, "message": "raison"}],
    )
    assert len(result) == 1
    assert result[0]["action_type"] == expected_type
    assert expected_text in result[0]["label"]
    assert result[0]["feature"] == feature
    assert result[0]["impact"] == 0.5


@pytest.mark.parametrize(
    "feature, values",
    [
        ("mrr_change_pct", {"mrr_change_pct": 12.0}),  # MRR positif ≠ revoir le forfait
        ("contract_type", {"contract_type": 1}),  # déjà annuel
        ("plan_tier_rank", {"plan_tier_rank": 0.5}),  # gamme inconnue / médiane
        ("recency_days", {"recency_days": 2}),
        ("payment_failures_90d", {"payment_failures_90d": 0}),
        ("frequency_trend_30d", {"frequency_trend_30d": 1.2}),
        ("engagement_breadth", {"engagement_breadth": 0.9}),
        ("support_tickets_30d", {"support_tickets_30d": 0}),
        ("tenure_months", {"tenure_months": 3}),
    ],
)
def test_playbook_ignores_non_actionable_values(feature, values):
    result = suggest_actions(
        observation(**values), [{"feature": feature, "impact": 0.9}]
    )
    assert result == [DEFAULT_ACTION]


def test_playbook_keeps_three_suggestions_ordered_by_impact():
    reasons = [
        {"feature": "tenure_months", "impact": 0.99},  # non actionnable
        {"feature": "contract_type", "impact": 0.2},
        {"feature": "mrr_change_pct", "impact": 0.8},
        {"feature": "recency_days", "impact": 0.5},
        {"feature": "support_tickets_30d", "impact": 0.1},
    ]
    result = suggest_actions(observation(), reasons)
    assert [item["feature"] for item in result] == [
        "mrr_change_pct",
        "recency_days",
        "contract_type",
    ]
    assert [item["impact"] for item in result] == [0.8, 0.5, 0.2]


def test_default_action_when_no_reason_is_actionable():
    result = suggest_actions(observation(mrr_change_pct=5.0), [])
    assert result == [DEFAULT_ACTION]


# ------------------------------------------------------------------ fiche client
def test_customer_detail_exposes_retention_and_suggested_actions(client, db_session):
    headers, organization_id = setup_org(client, db_session)
    customer = make_customer(
        db_session,
        organization_id,
        reasons=[
            {"feature": "mrr_change_pct", "impact": 0.9, "message": "MRR en baisse"},
            {"feature": "recency_days", "impact": 0.4, "message": "Inactif"},
        ],
    )

    response = client.get(f"{CUSTOMERS}/{customer.id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["retention_status"] == "none"
    assert data["owner_user_id"] is None
    assert [item["feature"] for item in data["suggested_actions"]] == [
        "mrr_change_pct",
        "recency_days",
    ]
    assert len(data["suggested_actions"]) <= 3


# ------------------------------------------------------------------ PATCH client
def test_patch_customer_retention_status_and_owner(client, db_session):
    headers, organization_id = setup_org(client, db_session)
    customer = make_customer(db_session, organization_id)
    owner = create_user(
        db_session,
        organization_id=organization_id,
        email="owner@example.com",
        role="analyst",
    )

    response = client.patch(
        f"{CUSTOMERS}/{customer.id}",
        json={"retention_status": "to_contact", "owner_user_id": owner.id},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["retention_status"] == "to_contact"
    assert response.json()["owner_user_id"] == owner.id

    detail = client.get(f"{CUSTOMERS}/{customer.id}", headers=headers).json()
    assert detail["retention_status"] == "to_contact"
    assert detail["owner_user_id"] == owner.id

    cleared = client.patch(
        f"{CUSTOMERS}/{customer.id}",
        json={"owner_user_id": None},
        headers=headers,
    )
    assert cleared.status_code == 200
    assert cleared.json()["owner_user_id"] is None


def test_patch_customer_rejects_invalid_status(client, db_session):
    headers, organization_id = setup_org(client, db_session)
    customer = make_customer(db_session, organization_id)

    response = client.patch(
        f"{CUSTOMERS}/{customer.id}",
        json={"retention_status": "perdu"},
        headers=headers,
    )
    assert response.status_code == 422


def test_patch_customer_rejects_owner_from_another_organization(client, db_session):
    headers, organization_id = setup_org(client, db_session)
    customer = make_customer(db_session, organization_id)

    other = Organization(name="Autre")
    db_session.add(other)
    db_session.commit()
    foreign = create_user(
        db_session,
        organization_id=other.id,
        email="foreign-owner@example.com",
        role="analyst",
    )

    response = client.patch(
        f"{CUSTOMERS}/{customer.id}",
        json={"owner_user_id": foreign.id},
        headers=headers,
    )
    assert response.status_code == 400


def test_patch_customer_rejects_inactive_owner(client, db_session):
    headers, organization_id = setup_org(client, db_session)
    customer = make_customer(db_session, organization_id)
    owner = create_user(
        db_session,
        organization_id=organization_id,
        email="inactive-owner@example.com",
        role="analyst",
        is_active=False,
    )

    response = client.patch(
        f"{CUSTOMERS}/{customer.id}",
        json={"owner_user_id": owner.id},
        headers=headers,
    )
    assert response.status_code == 400


def test_patch_customer_rejects_viewer_owner(client, db_session):
    headers, organization_id = setup_org(client, db_session)
    customer = make_customer(db_session, organization_id)
    owner = create_user(
        db_session,
        organization_id=organization_id,
        email="viewer-owner@example.com",
        role="viewer",
    )

    response = client.patch(
        f"{CUSTOMERS}/{customer.id}",
        json={"owner_user_id": owner.id},
        headers=headers,
    )
    assert response.status_code == 400


def test_deactivating_member_clears_owned_customers(client, db_session):
    headers, organization_id = setup_org(client, db_session)
    owner = create_user(
        db_session,
        organization_id=organization_id,
        email="owner-deactivated@example.com",
        role="analyst",
    )
    customer = make_customer(db_session, organization_id)
    assert client.patch(
        f"{CUSTOMERS}/{customer.id}",
        json={"owner_user_id": owner.id},
        headers=headers,
    ).status_code == 200

    response = client.patch(
        f"/api/v1/users/{owner.id}",
        json={"is_active": False},
        headers=headers,
    )
    assert response.status_code == 200
    db_session.expire_all()
    assert db_session.get(Customer, customer.id).owner_user_id is None


def test_deleting_member_clears_owned_customers(client, db_session):
    headers, organization_id = setup_org(client, db_session)
    owner = create_user(
        db_session,
        organization_id=organization_id,
        email="owner-deleted@example.com",
        role="analyst",
    )
    customer = make_customer(db_session, organization_id)
    assert client.patch(
        f"{CUSTOMERS}/{customer.id}",
        json={"owner_user_id": owner.id},
        headers=headers,
    ).status_code == 200

    response = client.delete(
        f"/api/v1/users/{owner.id}", headers=headers
    )
    assert response.status_code == 200
    db_session.expire_all()
    assert db_session.get(Customer, customer.id).owner_user_id is None


def test_patch_unknown_customer_returns_404(client):
    admin = register_admin(client, email="unknown-customer@example.com")
    headers = login_headers(client, admin["email"])
    assert client.patch(
        f"{CUSTOMERS}/9999", json={"retention_status": "contacted"}, headers=headers
    ).status_code == 404


# ------------------------------------------------------------------ CRUD actions
def test_actions_crud_and_status_transitions(client, db_session):
    headers, organization_id = setup_org(client, db_session)
    customer = make_customer(db_session, organization_id)

    created = client.post(
        f"{CUSTOMERS}/{customer.id}/actions",
        json={
            "action_type": "call",
            "note": "Appeler le client",
            "due_date": "2026-12-01",
        },
        headers=headers,
    )
    assert created.status_code == 201
    action = created.json()
    assert action["status"] == "todo"
    assert action["completed_at"] is None
    assert action["created_by_user_id"] is not None

    listing = client.get(
        f"{CUSTOMERS}/{customer.id}/actions", headers=headers
    )
    assert listing.status_code == 200
    assert [item["id"] for item in listing.json()] == [action["id"]]

    in_progress = client.patch(
        f"{ACTIONS}/{action['id']}",
        json={"status": "in_progress", "note": "Premier appel fait"},
        headers=headers,
    )
    assert in_progress.status_code == 200
    assert in_progress.json()["status"] == "in_progress"
    assert in_progress.json()["completed_at"] is None
    assert in_progress.json()["note"] == "Premier appel fait"

    done = client.patch(
        f"{ACTIONS}/{action['id']}", json={"status": "done"}, headers=headers
    )
    assert done.status_code == 200
    assert done.json()["completed_at"] is not None

    cancelled = client.patch(
        f"{ACTIONS}/{action['id']}", json={"status": "cancelled"}, headers=headers
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
    assert cancelled.json()["completed_at"] is None

    # Pas de suppression physique : l'endpoint DELETE n'existe pas.
    assert client.delete(f"{ACTIONS}/{action['id']}", headers=headers).status_code == 405
    assert db_session.get(CustomerAction, action["id"]) is not None


def test_action_creation_validates_payload(client, db_session):
    headers, organization_id = setup_org(client, db_session)
    customer = make_customer(db_session, organization_id)

    response = client.post(
        f"{CUSTOMERS}/{customer.id}/actions",
        json={"action_type": "sms"},
        headers=headers,
    )
    assert response.status_code == 422


def test_actions_filters_status_owner_and_overdue(client, db_session):
    headers, organization_id = setup_org(client, db_session)
    owner_a = create_user(
        db_session,
        organization_id=organization_id,
        email="owner-a@example.com",
        role="analyst",
    )
    owner_b = create_user(
        db_session,
        organization_id=organization_id,
        email="owner-b@example.com",
        role="analyst",
    )
    customer_a = make_customer(db_session, organization_id, "A")
    customer_b = make_customer(db_session, organization_id, "B")
    client.patch(
        f"{CUSTOMERS}/{customer_a.id}",
        json={"owner_user_id": owner_a.id},
        headers=headers,
    )
    client.patch(
        f"{CUSTOMERS}/{customer_b.id}",
        json={"owner_user_id": owner_b.id},
        headers=headers,
    )

    overdue_a = client.post(
        f"{CUSTOMERS}/{customer_a.id}/actions",
        json={"action_type": "call", "due_date": "2020-01-01"},
        headers=headers,
    ).json()
    future_a = client.post(
        f"{CUSTOMERS}/{customer_a.id}/actions",
        json={"action_type": "email", "due_date": "2099-01-01"},
        headers=headers,
    ).json()
    overdue_b = client.post(
        f"{CUSTOMERS}/{customer_b.id}/actions",
        json={"action_type": "call", "due_date": "2020-01-01"},
        headers=headers,
    ).json()
    done_overdue = client.post(
        f"{CUSTOMERS}/{customer_b.id}/actions",
        json={
            "action_type": "email",
            "status": "done",
            "due_date": "2020-01-01",
        },
        headers=headers,
    ).json()

    todo_ids = {
        item["id"]
        for item in client.get(
            ACTIONS, params={"status": "todo"}, headers=headers
        ).json()
    }
    assert todo_ids == {overdue_a["id"], future_a["id"], overdue_b["id"]}

    owned_ids = {
        item["id"]
        for item in client.get(
            ACTIONS, params={"owner": owner_a.id}, headers=headers
        ).json()
    }
    assert owned_ids == {overdue_a["id"], future_a["id"]}

    overdue_ids = {
        item["id"]
        for item in client.get(
            ACTIONS, params={"overdue": "true"}, headers=headers
        ).json()
    }
    assert overdue_ids == {overdue_a["id"], overdue_b["id"]}
    assert done_overdue["id"] not in overdue_ids


# ------------------------------------------------------------------ isolation
def test_actions_are_isolated_by_organization(client, db_session):
    headers_a, org_a = setup_org(client, db_session, "a-retention@example.com")
    headers_b, org_b = setup_org(client, db_session, "b-retention@example.com")

    customer_a = make_customer(db_session, org_a, "A")
    customer_b = make_customer(db_session, org_b, "B")
    action_a = client.post(
        f"{CUSTOMERS}/{customer_a.id}/actions",
        json={"action_type": "call"},
        headers=headers_a,
    ).json()
    action_b = client.post(
        f"{CUSTOMERS}/{customer_b.id}/actions",
        json={"action_type": "email"},
        headers=headers_b,
    ).json()

    assert client.get(
        f"{CUSTOMERS}/{customer_b.id}/actions", headers=headers_a
    ).status_code == 404
    assert client.post(
        f"{CUSTOMERS}/{customer_b.id}/actions",
        json={"action_type": "call"},
        headers=headers_a,
    ).status_code == 404
    assert client.patch(
        f"{ACTIONS}/{action_b['id']}",
        json={"status": "done"},
        headers=headers_a,
    ).status_code == 404
    assert client.patch(
        f"{CUSTOMERS}/{customer_b.id}",
        json={"retention_status": "contacted"},
        headers=headers_a,
    ).status_code == 404

    visible = client.get(ACTIONS, headers=headers_a).json()
    assert [item["id"] for item in visible] == [action_a["id"]]


# ------------------------------------------------------------------ permissions
def test_viewer_can_read_but_not_write_retention(client, db_session):
    headers, organization_id = setup_org(client, db_session)
    create_user(
        db_session,
        organization_id=organization_id,
        email="viewer-retention@example.com",
        role="viewer",
    )
    viewer_headers = login_headers(client, "viewer-retention@example.com")
    customer = make_customer(db_session, organization_id)
    action = client.post(
        f"{CUSTOMERS}/{customer.id}/actions",
        json={"action_type": "call"},
        headers=headers,
    ).json()

    assert client.get(f"{CUSTOMERS}/{customer.id}", headers=viewer_headers).status_code == 200
    assert client.get(
        f"{CUSTOMERS}/{customer.id}/actions", headers=viewer_headers
    ).status_code == 200
    assert client.get(ACTIONS, headers=viewer_headers).status_code == 200

    assert client.patch(
        f"{CUSTOMERS}/{customer.id}",
        json={"retention_status": "contacted"},
        headers=viewer_headers,
    ).status_code == 403
    assert client.post(
        f"{CUSTOMERS}/{customer.id}/actions",
        json={"action_type": "call"},
        headers=viewer_headers,
    ).status_code == 403
    assert client.patch(
        f"{ACTIONS}/{action['id']}",
        json={"status": "done"},
        headers=viewer_headers,
    ).status_code == 403


def test_analyst_can_write_retention(client, db_session):
    headers, organization_id = setup_org(client, db_session)
    create_user(
        db_session,
        organization_id=organization_id,
        email="analyst-retention@example.com",
        role="analyst",
    )
    analyst_headers = login_headers(client, "analyst-retention@example.com")
    customer = make_customer(db_session, organization_id)

    assert client.patch(
        f"{CUSTOMERS}/{customer.id}",
        json={"retention_status": "contacted"},
        headers=analyst_headers,
    ).status_code == 200
    created = client.post(
        f"{CUSTOMERS}/{customer.id}/actions",
        json={"action_type": "call"},
        headers=analyst_headers,
    )
    assert created.status_code == 201
    assert client.patch(
        f"{ACTIONS}/{created.json()['id']}",
        json={"status": "done"},
        headers=analyst_headers,
    ).status_code == 200
