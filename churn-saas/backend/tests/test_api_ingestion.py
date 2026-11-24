"""Tests de l'API d'ingestion par clé API et de la gestion des clés (étape 8)."""

from app.config import settings
from app.models import Customer, ImportBatch, Observation, Organization, Prediction
from tests.helpers import create_user, login_headers, register_admin

INGEST_URL = "/api/v1/ingest/observations"
API_KEY_URL = "/api/v1/settings/api-key"
ROTATE_URL = "/api/v1/settings/api-key/rotate"


def setup_admin(client, email="ingest-admin@example.com", organization="Org Ingest"):
    admin = register_admin(client, email=email, organization_name=organization)
    return admin, login_headers(client, admin["email"])


def rotate_key(client, headers) -> str:
    response = client.post(ROTATE_URL, headers=headers)
    assert response.status_code == 200, response.text
    return response.json()["api_key"]


def observation(customer_id="C1", snapshot_date="2026-11-01", **overrides):
    data = {
        "customer_id": customer_id,
        "snapshot_date": snapshot_date,
        "name": f"Client {customer_id}",
        "email": f"{customer_id.lower()}@example.com",
        "phone_number": "+33 6 12 34 56 78",
        "tenure_months": 12,
        "contract_type": 0,
        "mrr_change_pct": -5.0,
        "support_tickets_30d": 1,
        "recency_days": 10,
        "frequency_trend_30d": 0.9,
        "engagement_breadth": 0.5,
        "payment_failures_90d": 0,
    }
    data.update(overrides)
    return data


def post_ingest(client, api_key, observations):
    return client.post(
        INGEST_URL,
        headers={"X-API-Key": api_key},
        json={"observations": observations},
    )


# ------------------------------------------------------------------ clé API
def test_settings_api_key_never_returns_the_key(client):
    _, headers = setup_admin(client)

    before = client.get(API_KEY_URL, headers=headers)
    assert before.status_code == 200
    assert before.json() == {"exists": False, "prefix": None, "created_at": None}

    rotated = client.post(ROTATE_URL, headers=headers)
    assert rotated.status_code == 200
    raw_key = rotated.json()["api_key"]
    assert raw_key.startswith("cs_")

    after = client.get(API_KEY_URL, headers=headers)
    assert after.status_code == 200
    body = after.json()
    assert body["exists"] is True
    assert body["prefix"] == raw_key[:8]
    assert body["created_at"] is not None
    assert "api_key" not in body
    assert raw_key not in after.text


def test_analyst_and_viewer_cannot_manage_api_key(client, db_session):
    admin, _ = setup_admin(client)
    create_user(
        db_session,
        organization_id=admin["organization_id"],
        email="ingest-analyst@example.com",
        role="analyst",
    )
    create_user(
        db_session,
        organization_id=admin["organization_id"],
        email="ingest-viewer@example.com",
        role="viewer",
    )

    for email in ("ingest-analyst@example.com", "ingest-viewer@example.com"):
        headers = login_headers(client, email)
        assert client.get(API_KEY_URL, headers=headers).status_code == 403
        assert client.post(ROTATE_URL, headers=headers).status_code == 403


def test_ingest_rejects_missing_invalid_and_rotated_keys(client):
    _, headers = setup_admin(client)

    assert client.post(
        INGEST_URL, json={"observations": [observation()]}
    ).status_code == 401
    assert post_ingest(client, "cs_inconnue", [observation()]).status_code == 401

    old_key = rotate_key(client, headers)
    new_key = rotate_key(client, headers)
    assert old_key != new_key
    assert post_ingest(client, old_key, [observation()]).status_code == 401
    assert post_ingest(client, new_key, [observation()]).status_code == 200


def test_inactive_organization_key_is_rejected(client, db_session):
    admin, headers = setup_admin(client)
    api_key = rotate_key(client, headers)

    organization = db_session.get(Organization, admin["organization_id"])
    organization.is_active = False
    db_session.commit()

    assert post_ingest(client, api_key, [observation()]).status_code == 401


# ------------------------------------------------------------------ ingestion
def test_key_only_writes_to_its_own_organization(client, db_session):
    admin_a, headers_a = setup_admin(
        client, email="ingest-a@example.com", organization="Org A"
    )
    admin_b, headers_b = setup_admin(
        client, email="ingest-b@example.com", organization="Org B"
    )
    key_a = rotate_key(client, headers_a)
    rotate_key(client, headers_b)

    response = post_ingest(client, key_a, [observation("ONLY-A")])
    assert response.status_code == 200
    assert response.json()["imported_rows"] == 1

    assert (
        db_session.query(Customer)
        .filter(Customer.organization_id == admin_a["organization_id"])
        .count()
        == 1
    )
    assert (
        db_session.query(Customer)
        .filter(Customer.organization_id == admin_b["organization_id"])
        .count()
        == 0
    )


def test_more_than_5000_rows_is_rejected(client):
    _, headers = setup_admin(client)
    api_key = rotate_key(client, headers)
    observations = [
        observation(customer_id=f"C{i}") for i in range(5001)
    ]

    response = post_ingest(client, api_key, observations)
    assert response.status_code == 422


def test_body_larger_than_configured_limit_is_rejected(client, monkeypatch):
    _, headers = setup_admin(client)
    api_key = rotate_key(client, headers)
    monkeypatch.setattr(settings, "max_ingest_body_size_mb", 0)

    response = post_ingest(client, api_key, [observation()])
    assert response.status_code == 413


def test_repeated_payload_reports_duplicates_without_http_error(client):
    _, headers = setup_admin(client)
    api_key = rotate_key(client, headers)
    payload = [observation()]

    first = post_ingest(client, api_key, payload)
    assert first.status_code == 200
    assert first.json()["imported_rows"] == 1

    second = post_ingest(client, api_key, payload)
    assert second.status_code == 200
    body = second.json()
    assert body["status"] == "completed"
    assert body["imported_rows"] == 0
    assert body["error_rows"] == 1
    assert body["anomalies"][0]["error_type"] == "DUPLICATE_SNAPSHOT"


def test_unranked_plan_is_an_anomaly_without_failing_the_batch(client, db_session):
    _, headers = setup_admin(client)
    api_key = rotate_key(client, headers)
    client.put(
        "/api/v1/imports/mapping",
        json={"plan_order": ["Standard", "Pro"]},
        headers=headers,
    )

    response = post_ingest(
        client,
        api_key,
        [
            observation("RANKED", plan="Pro"),
            observation("UNRANKED", plan="Gold"),
        ],
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["imported_rows"] == 1
    assert body["error_rows"] == 1
    assert body["anomalies"][0]["error_type"] == "UNKNOWN_PLAN"
    assert body["anomalies"][0]["external_id"] == "UNRANKED"
    assert db_session.query(Observation).count() == 1


def test_only_unranked_plans_do_not_fail_the_batch(client):
    _, headers = setup_admin(client)
    api_key = rotate_key(client, headers)
    client.put(
        "/api/v1/imports/mapping",
        json={"plan_order": ["Standard", "Pro"]},
        headers=headers,
    )

    response = post_ingest(
        client, api_key, [observation("GOLD", plan="Gold")]
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["imported_rows"] == 0
    assert body["error_rows"] == 1


def test_direct_plan_tier_rank_is_accepted(client, db_session):
    _, headers = setup_admin(client)
    api_key = rotate_key(client, headers)

    response = post_ingest(
        client,
        api_key,
        [observation("DIRECT", plan_tier_rank=0.75)],
    )

    assert response.status_code == 200
    assert response.json()["imported_rows"] == 1
    stored = db_session.query(Observation).one()
    assert stored.plan_tier_rank == 0.75


def test_api_batch_is_visible_in_import_history(client):
    _, headers = setup_admin(client)
    api_key = rotate_key(client, headers)
    batch_id = post_ingest(client, api_key, [observation()]).json()["batch_id"]

    history = client.get("/api/v1/imports/", headers=headers)
    assert history.status_code == 200
    item = next(
        row for row in history.json() if row["import_batch_id"] == batch_id
    )
    assert item["source"] == "api"

    detail = client.get(f"/api/v1/imports/{batch_id}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["source"] == "api"
    assert detail.json()["uploaded_by_user_id"] is None


def test_predictions_are_generated_for_ingested_rows(client, db_session):
    _, headers = setup_admin(client)
    api_key = rotate_key(client, headers)
    batch_id = post_ingest(
        client, api_key, [observation("PRED", plan_tier_rank=0.2)]
    ).json()["batch_id"]

    predictions = (
        db_session.query(Prediction)
        .join(Observation, Observation.id == Prediction.observation_id)
        .filter(Observation.import_batch_id == batch_id)
        .all()
    )
    assert len(predictions) == 1
    assert 0.0 <= predictions[0].score <= 1.0
    assert predictions[0].is_active is True
    assert db_session.get(ImportBatch, batch_id).source == "api"
