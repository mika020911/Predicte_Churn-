"""Tests de GET /customers : pagination, filtre par zone, tri, isolation, prédiction active."""
from datetime import date

import pytest
from sqlalchemy import event

from app.models import Customer, ImportBatch, Observation, Prediction

URL = "/api/v1/customers"
REASONS = [{"feature": "recency_days", "impact": 0.8, "message": "Inactif depuis 25 jours"}]


def register_and_login(client, email="a@company.com", organization="Org A"):
    user = client.post("/api/v1/auth/register", json={
        "email": email, "password": "Password123!", "full_name": "Test", "organization_name": organization,
    }).json()
    token = client.post("/api/v1/auth/login/json",
                        json={"email": email, "password": "Password123!"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, user["organization_id"]


def add_customer(db, organization_id, external_id, name=None):
    customer = Customer(organization_id=organization_id, external_id=external_id, name=name or external_id)
    db.add(customer)
    db.flush()
    return customer


def add_prediction(db, customer, score, level, snapshot=date(2026, 11, 1), active=True, reasons=None):
    batch = ImportBatch(organization_id=customer.organization_id, filename="t.csv", source="csv_upload",
                        status="COMPLETED", total_rows=1, imported_rows=1, error_rows=0, anomaly_report=[])
    db.add(batch)
    db.flush()
    obs = Observation(customer_id=customer.id, import_batch_id=batch.id, snapshot_date=snapshot,
                      tenure_months=12, contract_type=0, mrr_change_pct=0.0, support_tickets_30d=0,
                      recency_days=5, frequency_trend_30d=1.0, engagement_breadth=0.5,
                      payment_failures_90d=0)
    db.add(obs)
    db.flush()
    prediction = Prediction(customer_id=customer.id, observation_id=obs.id, score=score, risk_level=level,
                            top_reasons=reasons if reasons is not None else [], is_active=active,
                            model_version="test-v1")
    db.add(prediction)
    db.commit()
    return prediction


def seed(db, org_id, scores_levels, prefix="C"):
    for i, (score, level) in enumerate(scores_levels):
        add_prediction(db, add_customer(db, org_id, f"{prefix}{i:03d}"), score, level)


# ------------------------------------------------------------------ accès
def test_requires_authentication(client):
    assert client.get(URL).status_code == 401


def test_empty_organization_returns_empty_page(client):
    headers, _ = register_and_login(client)
    data = client.get(URL, headers=headers).json()
    assert data["items"] == [] and data["total"] == 0 and data["total_pages"] == 0
    assert data["zone_counts"] == {"low": 0, "medium": 0, "high": 0}


# --------------------------------------------------------------- contenu et tri
def test_items_are_sorted_by_descending_score_and_complete(client, db_session):
    headers, org = register_and_login(client)
    add_prediction(db_session, add_customer(db_session, org, "LOW", "Alice"), 0.10, "low")
    add_prediction(db_session, add_customer(db_session, org, "HIGH", "Bob"), 0.90, "high", reasons=REASONS)
    add_prediction(db_session, add_customer(db_session, org, "MID", "Chloé"), 0.50, "medium")

    items = client.get(URL, headers=headers).json()["items"]
    assert [i["external_id"] for i in items] == ["HIGH", "MID", "LOW"]
    top = items[0]
    assert top["name"] == "Bob" and top["score"] == 0.9 and top["risk_level"] == "high"
    assert top["snapshot_date"] == "2026-11-01" and top["model_version"] == "test-v1"
    assert top["top_reasons"] == REASONS


# ------------------------------------------------------------------ pagination
def test_pagination_covers_all_customers_without_overlap(client, db_session):
    headers, org = register_and_login(client)
    seed(db_session, org, [(round(0.99 - i * 0.03, 2), "high") for i in range(25)])

    pages = [client.get(URL, params={"page": p, "page_size": 10}, headers=headers).json() for p in (1, 2, 3)]
    assert [len(p["items"]) for p in pages] == [10, 10, 5]
    assert all(p["total"] == 25 and p["total_pages"] == 3 for p in pages)
    ids = [i["customer_id"] for p in pages for i in p["items"]]
    assert len(ids) == len(set(ids)) == 25
    scores = [i["score"] for p in pages for i in p["items"]]
    assert scores == sorted(scores, reverse=True)


def test_page_beyond_the_end_is_empty(client, db_session):
    headers, org = register_and_login(client)
    seed(db_session, org, [(0.5, "medium")] * 3)
    data = client.get(URL, params={"page": 5, "page_size": 10}, headers=headers).json()
    assert data["items"] == [] and data["total"] == 3


def test_equal_scores_do_not_duplicate_or_skip_customers_across_pages(client, db_session):
    headers, org = register_and_login(client)
    seed(db_session, org, [(0.5, "medium")] * 25)
    ids = []
    for page in (1, 2, 3):
        ids += [i["customer_id"] for i in
                client.get(URL, params={"page": page, "page_size": 10}, headers=headers).json()["items"]]
    assert len(ids) == len(set(ids)) == 25


@pytest.mark.parametrize("params", [{"page": 0}, {"page_size": 0}, {"page_size": 101}, {"zone": "rouge"}])
def test_invalid_parameters_are_rejected(client, params):
    headers, _ = register_and_login(client)
    assert client.get(URL, params=params, headers=headers).status_code == 422


# ------------------------------------------------------------------ filtre de zone
def test_zone_filter_and_zone_counts(client, db_session):
    headers, org = register_and_login(client)
    seed(db_session, org, [(0.9, "high")] * 2 + [(0.5, "medium")] * 3 + [(0.1, "low")] * 5)

    data = client.get(URL, params={"zone": "medium"}, headers=headers).json()
    assert data["total"] == 3
    assert {i["risk_level"] for i in data["items"]} == {"medium"}
    # la répartition porte sur tous les clients, pas seulement sur le filtre
    assert data["zone_counts"] == {"low": 5, "medium": 3, "high": 2}


# --------------------------------------------------------------- isolation et actif
def test_other_organizations_customers_are_never_returned(client, db_session):
    headers_a, org_a = register_and_login(client, "a@company.com", "Org A")
    _, org_b = register_and_login(client, "b@company.com", "Org B")
    seed(db_session, org_a, [(0.8, "high")], prefix="A")
    seed(db_session, org_b, [(0.9, "high")] * 4, prefix="B")

    data = client.get(URL, headers=headers_a).json()
    assert data["total"] == 1 and data["items"][0]["external_id"] == "A000"
    assert data["zone_counts"]["high"] == 1


def test_only_the_active_prediction_is_listed(client, db_session):
    headers, org = register_and_login(client)
    customer = add_customer(db_session, org, "C1")
    add_prediction(db_session, customer, 0.95, "high", snapshot=date(2026, 10, 1), active=False)
    add_prediction(db_session, customer, 0.20, "low", snapshot=date(2026, 11, 1), active=True)

    data = client.get(URL, headers=headers).json()
    assert data["total"] == 1
    assert data["items"][0]["score"] == 0.2 and data["items"][0]["snapshot_date"] == "2026-11-01"


def test_customer_without_prediction_is_not_listed(client, db_session):
    headers, org = register_and_login(client)
    add_customer(db_session, org, "NOPRED")
    db_session.commit()
    assert client.get(URL, headers=headers).json()["total"] == 0


# -------------------------------------------------------------------- performance
def test_listing_uses_a_constant_number_of_queries(client, db_session):
    headers, org = register_and_login(client)
    seed(db_session, org, [(0.9 - i * 0.01, "high") for i in range(30)])

    statements = []
    engine = db_session.get_bind()
    capture = lambda conn, cursor, statement, *a: statements.append(statement)  # noqa: E731
    event.listen(engine, "before_cursor_execute", capture)
    try:
        client.get(URL, params={"page_size": 30}, headers=headers)
    finally:
        event.remove(engine, "before_cursor_execute", capture)

    prediction_queries = [s for s in statements if "predictions" in s]
    assert len(prediction_queries) <= 3  # liste, total, répartition : jamais une requête par client