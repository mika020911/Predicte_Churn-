"""Tests du simulateur what-if : permissions, bornes, isolation, absence d'écriture."""

from datetime import date

import pytest

from app.config import settings
from app.models import Customer, Observation, Organization, Prediction

from tests.helpers import create_user, login_headers, register_admin

MODEL_FILE = settings.ml_src_dir.parent / "models" / "best_model.pkl"
needs_model = pytest.mark.skipif(
    not MODEL_FILE.exists(), reason="Modèle ML absent : lance d'abord ml/src/benchmark.py"
)

BASE = dict(
    tenure_months=24,
    contract_type=0,
    mrr_change_pct=0.0,
    support_tickets_30d=1,
    recency_days=10,
    frequency_trend_30d=1.0,
    engagement_breadth=0.5,
    payment_failures_90d=0,
    plan_tier_rank=0.5,
)

SAFE = dict(
    tenure_months=60,
    contract_type=1,
    mrr_change_pct=10.0,
    support_tickets_30d=0,
    recency_days=0,
    frequency_trend_30d=1.2,
    engagement_breadth=1.0,
    payment_failures_90d=0,
    plan_tier_rank=1.0,
)

RISKY = dict(
    tenure_months=1,
    contract_type=0,
    mrr_change_pct=-30.0,
    support_tickets_30d=10,
    recency_days=60,
    frequency_trend_30d=0.1,
    engagement_breadth=0.0,
    payment_failures_90d=5,
    plan_tier_rank=0.0,
)


def add_customer_with_prediction(
    db,
    organization_id: int,
    *,
    external_id: str = "C1",
    score: float = 0.5,
    is_active: bool = True,
    features: dict | None = None,
) -> Customer:
    customer = Customer(
        organization_id=organization_id,
        external_id=external_id,
        name=external_id,
    )
    db.add(customer)
    db.flush()

    observation = Observation(
        customer_id=customer.id,
        import_batch_id=None,
        snapshot_date=date(2026, 11, 1),
        **(features or BASE),
    )
    db.add(observation)
    db.flush()

    db.add(
        Prediction(
            customer_id=customer.id,
            observation_id=observation.id,
            score=score,
            risk_level="medium",
            top_reasons=[],
            shap_values={},
            is_active=is_active,
            model_version="test-v1",
        )
    )
    db.commit()
    return customer


@pytest.fixture
def admin_headers(client):
    admin = register_admin(client, email="simulate-admin@example.com")
    return login_headers(client, admin["email"]), admin["organization_id"]


def test_viewer_cannot_simulate(client, db_session, admin_headers):
    _, organization_id = admin_headers
    customer = add_customer_with_prediction(db_session, organization_id)
    create_user(
        db_session,
        organization_id=organization_id,
        email="simulate-viewer@example.com",
        role="viewer",
    )

    response = client.post(
        f"/api/v1/customers/{customer.id}/simulate",
        json={},
        headers=login_headers(client, "simulate-viewer@example.com"),
    )

    assert response.status_code == 403


@pytest.mark.parametrize(
    "payload",
    [
        {"contract_type": 2},
        {"engagement_breadth": 1.5},
        {"engagement_breadth": -0.1},
        {"plan_tier_rank": 1.1},
        {"plan_tier_rank": -0.1},
        {"tenure_months": -1},
        {"support_tickets_30d": -2},
        {"recency_days": -1},
        {"payment_failures_90d": -3},
    ],
)
def test_out_of_bounds_values_are_rejected(client, admin_headers, payload):
    headers, _ = admin_headers
    response = client.post(
        "/api/v1/customers/1/simulate", json=payload, headers=headers
    )
    assert response.status_code == 422


@pytest.mark.parametrize(
    "body",
    [
        '{"engagement_breadth": NaN}',
        '{"plan_tier_rank": Infinity}',
        '{"mrr_change_pct": -Infinity}',
    ],
)
def test_non_finite_values_are_rejected(client, admin_headers, body):
    headers, _ = admin_headers
    response = client.post(
        "/api/v1/customers/1/simulate",
        content=body,
        headers={**headers, "Content-Type": "application/json"},
    )
    assert response.status_code == 422, response.text


def test_unknown_customer_returns_404(client, admin_headers):
    headers, _ = admin_headers
    response = client.post(
        "/api/v1/customers/9999/simulate", json={}, headers=headers
    )
    assert response.status_code == 404


def test_customer_from_another_organization_returns_404(client, db_session, admin_headers):
    headers, _ = admin_headers
    other_org = Organization(name="Autre organisation")
    db_session.add(other_org)
    db_session.commit()
    foreign_customer = add_customer_with_prediction(db_session, other_org.id)

    response = client.post(
        f"/api/v1/customers/{foreign_customer.id}/simulate",
        json={},
        headers=headers,
    )

    assert response.status_code == 404


def test_customer_without_active_prediction_returns_404(client, db_session, admin_headers):
    headers, organization_id = admin_headers
    inactive = add_customer_with_prediction(
        db_session, organization_id, external_id="INACTIVE", is_active=False
    )

    response = client.post(
        f"/api/v1/customers/{inactive.id}/simulate", json={}, headers=headers
    )

    assert response.status_code == 404


@needs_model
def test_simulated_score_is_in_range_and_uses_the_stored_baseline(
    client, db_session, admin_headers
):
    headers, organization_id = admin_headers
    customer = add_customer_with_prediction(db_session, organization_id, score=0.5)

    response = client.post(
        f"/api/v1/customers/{customer.id}/simulate", json={}, headers=headers
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["baseline_score"] == 0.5
    assert 0.0 <= data["simulated_score"] <= 1.0
    assert data["delta"] == round(data["simulated_score"] - 0.5, 4)
    assert data["risk_level"] in {"low", "medium", "high"}
    assert set(data["shap_values"]) >= {"tenure_months", "payment_failures_90d"}
    assert data["top_reasons"]


@needs_model
def test_overrides_change_the_simulated_score(client, db_session, admin_headers):
    headers, organization_id = admin_headers
    customer = add_customer_with_prediction(db_session, organization_id)
    url = f"/api/v1/customers/{customer.id}/simulate"

    safe = client.post(url, json=SAFE, headers=headers)
    risky = client.post(url, json=RISKY, headers=headers)

    assert safe.status_code == 200, safe.text
    assert risky.status_code == 200, risky.text
    assert risky.json()["simulated_score"] > safe.json()["simulated_score"] + 0.3


@needs_model
def test_simulation_writes_nothing(client, db_session, admin_headers):
    headers, organization_id = admin_headers
    customer = add_customer_with_prediction(db_session, organization_id)
    predictions_before = db_session.query(Prediction).count()
    observations_before = db_session.query(Observation).count()

    response = client.post(
        f"/api/v1/customers/{customer.id}/simulate", json=RISKY, headers=headers
    )

    assert response.status_code == 200, response.text
    db_session.expire_all()
    assert db_session.query(Prediction).count() == predictions_before
    assert db_session.query(Observation).count() == observations_before
