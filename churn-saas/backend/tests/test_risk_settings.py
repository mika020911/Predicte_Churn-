"""Tests des seuils de risque : lecture, modification, validation, isolation, recalcul des zones."""
from datetime import date

import pytest

from app.models import Customer, ImportBatch, Observation, Prediction

URL = "/api/v1/risk-settings"


def register_and_login(client, email="a@company.com", organization="Org A"):
    """Crée un compte et renvoie (en-têtes d'authentification, id de l'organisation)."""
    user = client.post("/api/v1/auth/register", json={
        "email": email, "password": "Password123!", "full_name": "Test", "organization_name": organization,
    }).json()
    token = client.post("/api/v1/auth/login/json",
                        json={"email": email, "password": "Password123!"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, user["organization_id"]


def add_prediction(db, organization_id, external_id, score, risk_level):
    customer = Customer(organization_id=organization_id, external_id=external_id, name=external_id)
    db.add(customer)
    db.flush()
    batch = ImportBatch(organization_id=organization_id, filename="t.csv", source="csv_upload",
                        status="COMPLETED", total_rows=1, imported_rows=1, error_rows=0, anomaly_report=[])
    db.add(batch)
    db.flush()
    obs = Observation(customer_id=customer.id, import_batch_id=batch.id, snapshot_date=date(2026, 11, 1),
                      tenure_months=12, contract_type=0, mrr_change_pct=0.0, support_tickets_30d=0,
                      recency_days=5, frequency_trend_30d=1.0, engagement_breadth=0.5,
                      payment_failures_90d=0)
    db.add(obs)
    db.flush()
    prediction = Prediction(customer_id=customer.id, observation_id=obs.id, score=score,
                            risk_level=risk_level, is_active=True, model_version="test")
    db.add(prediction)
    db.commit()
    return prediction


# ------------------------------------------------------------------ accès
def test_requires_authentication(client):
    assert client.get(URL).status_code == 401
    assert client.put(URL, json={"threshold_medium": 0.3, "threshold_high": 0.6}).status_code == 401


def test_new_organization_has_default_thresholds(client):
    headers, _ = register_and_login(client)
    response = client.get(URL, headers=headers)
    assert response.status_code == 200
    assert response.json()["threshold_medium"] == 0.4
    assert response.json()["threshold_high"] == 0.7


# ------------------------------------------------------------ modification
def test_update_then_read_returns_new_thresholds(client):
    headers, _ = register_and_login(client)
    response = client.put(URL, json={"threshold_medium": 0.3, "threshold_high": 0.6}, headers=headers)
    assert response.status_code == 200
    assert response.json()["threshold_medium"] == 0.3
    assert client.get(URL, headers=headers).json()["threshold_high"] == 0.6


def test_updating_twice_keeps_a_single_row(client, db_session):
    from app.models import RiskSettings
    headers, org_id = register_and_login(client)
    client.put(URL, json={"threshold_medium": 0.3, "threshold_high": 0.6}, headers=headers)
    client.put(URL, json={"threshold_medium": 0.2, "threshold_high": 0.5}, headers=headers)
    assert db_session.query(RiskSettings).filter(RiskSettings.organization_id == org_id).count() == 1


@pytest.mark.parametrize("medium, high", [
    (0.7, 0.4),    # moyen au-dessus de haut
    (0.5, 0.5),    # égaux
    (0.0, 0.5),    # hors de ]0, 1[
    (0.3, 1.0),
    (-0.1, 0.5),
    (0.3, 1.5),
])
def test_invalid_thresholds_are_rejected(client, medium, high):
    headers, _ = register_and_login(client)
    response = client.put(URL, json={"threshold_medium": medium, "threshold_high": high}, headers=headers)
    assert response.status_code == 422
    # les anciennes valeurs restent en place
    assert client.get(URL, headers=headers).json()["threshold_high"] == 0.7


def test_missing_field_is_rejected(client):
    headers, _ = register_and_login(client)
    assert client.put(URL, json={"threshold_high": 0.6}, headers=headers).status_code == 422


# --------------------------------------------------------------- isolation
def test_each_organization_has_its_own_thresholds(client):
    headers_a, _ = register_and_login(client, "a@company.com", "Org A")
    headers_b, _ = register_and_login(client, "b@company.com", "Org B")
    client.put(URL, json={"threshold_medium": 0.1, "threshold_high": 0.2}, headers=headers_a)
    assert client.get(URL, headers=headers_b).json()["threshold_high"] == 0.7


# ------------------------------------------------ recalcul des prédictions
def test_changing_thresholds_updates_existing_risk_levels(client, db_session):
    headers, org_id = register_and_login(client)
    low = add_prediction(db_session, org_id, "C1", score=0.10, risk_level="low")
    mid = add_prediction(db_session, org_id, "C2", score=0.55, risk_level="medium")
    high = add_prediction(db_session, org_id, "C3", score=0.90, risk_level="high")

    client.put(URL, json={"threshold_medium": 0.05, "threshold_high": 0.5}, headers=headers)
    db_session.expire_all()
    assert [low.risk_level, mid.risk_level, high.risk_level] == ["medium", "high", "high"]

    client.put(URL, json={"threshold_medium": 0.6, "threshold_high": 0.95}, headers=headers)
    db_session.expire_all()
    assert [low.risk_level, mid.risk_level, high.risk_level] == ["low", "low", "medium"]


def test_changing_thresholds_does_not_touch_other_organizations(client, db_session):
    headers_a, org_a = register_and_login(client, "a@company.com", "Org A")
    _, org_b = register_and_login(client, "b@company.com", "Org B")
    other = add_prediction(db_session, org_b, "X1", score=0.55, risk_level="medium")

    client.put(URL, json={"threshold_medium": 0.05, "threshold_high": 0.2}, headers=headers_a)
    db_session.expire_all()
    assert other.risk_level == "medium"