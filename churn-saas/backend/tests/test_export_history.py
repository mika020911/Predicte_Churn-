"""Tests des exports clients/imports et de l'historique des prédictions."""

import csv
import io
from datetime import date

from openpyxl import load_workbook

from app.models import Customer, ImportBatch, Observation, Organization, Prediction
from app.services import export_service

from tests.helpers import create_user, login_headers, register_admin

FEATURES = dict(
    tenure_months=12,
    contract_type=0,
    mrr_change_pct=0.0,
    support_tickets_30d=0,
    recency_days=5,
    frequency_trend_30d=1.0,
    engagement_breadth=0.5,
    payment_failures_90d=0,
    plan_tier_rank=0.5,
)

EXPORT_HEADER = [
    "customer_id",
    "external_id",
    "name",
    "email",
    "phone_number",
    "score",
    "risk_level",
    "snapshot_date",
    "model_version",
    "top_reasons",
]


def add_prediction(
    db,
    organization_id: int,
    external_id: str,
    *,
    snapshot: date = date(2026, 11, 1),
    score: float = 0.5,
    level: str = "medium",
    name: str | None = None,
    reasons: list | None = None,
    model_version: str = "test-v1",
    is_active: bool = True,
    phone_number: str | None = None,
) -> Prediction:
    customer = (
        db.query(Customer)
        .filter(
            Customer.organization_id == organization_id,
            Customer.external_id == external_id,
        )
        .first()
    )
    if customer is None:
        customer = Customer(
            organization_id=organization_id,
            external_id=external_id,
            name=name or external_id,
            phone_number=phone_number,
        )
        db.add(customer)
        db.flush()

    observation = Observation(
        customer_id=customer.id,
        import_batch_id=None,
        snapshot_date=snapshot,
        **FEATURES,
    )
    db.add(observation)
    db.flush()

    prediction = Prediction(
        customer_id=customer.id,
        observation_id=observation.id,
        score=score,
        risk_level=level,
        top_reasons=reasons or [],
        shap_values={},
        model_version=model_version,
        is_active=is_active,
    )
    db.add(prediction)
    db.commit()
    return prediction


def read_csv(content: bytes) -> list[list[str]]:
    return list(csv.reader(io.StringIO(content.decode("utf-8-sig"))))


def test_customer_export_columns_filename_and_zone_filter(client, db_session):
    admin = register_admin(client, email="export-admin@example.com")
    headers = login_headers(client, admin["email"])
    add_prediction(db_session, admin["organization_id"], "LOW", score=0.1, level="low")
    add_prediction(db_session, admin["organization_id"], "HIGH", score=0.9, level="high")

    response = client.get("/api/v1/customers/export?format=csv", headers=headers)

    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("text/csv")
    assert "clients_" in response.headers["content-disposition"]
    assert response.headers["content-disposition"].endswith('.csv"')

    rows = read_csv(response.content)
    assert rows[0] == EXPORT_HEADER
    assert [row[1] for row in rows[1:]] == ["HIGH", "LOW"]

    filtered = client.get(
        "/api/v1/customers/export?format=csv&zone=high", headers=headers
    )
    assert [row[1] for row in read_csv(filtered.content)[1:]] == ["HIGH"]


def test_customer_export_xlsx(client, db_session):
    admin = register_admin(client, email="export-xlsx@example.com")
    headers = login_headers(client, admin["email"])
    add_prediction(db_session, admin["organization_id"], "C1", score=0.3)

    response = client.get("/api/v1/customers/export?format=xlsx", headers=headers)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    workbook = load_workbook(io.BytesIO(response.content))
    sheet = workbook.active
    values = list(sheet.values)
    assert list(values[0]) == EXPORT_HEADER
    assert values[1][1] == "C1"


def test_customer_export_is_isolated_by_organization(client, db_session):
    admin = register_admin(client, email="export-org-a@example.com")
    headers = login_headers(client, admin["email"])
    other = Organization(name="Autre organisation")
    db_session.add(other)
    db_session.commit()
    add_prediction(db_session, admin["organization_id"], "MINE")
    add_prediction(db_session, other.id, "FOREIGN")

    response = client.get("/api/v1/customers/export?format=csv", headers=headers)

    exported = [row[1] for row in read_csv(response.content)[1:]]
    assert exported == ["MINE"]


def test_customer_export_neutralises_formulas(client, db_session):
    admin = register_admin(client, email="export-formula@example.com")
    headers = login_headers(client, admin["email"])
    add_prediction(
        db_session,
        admin["organization_id"],
        "C1",
        name="=1+1",
        reasons=[
            {"feature": "recency_days", "impact": 0.5, "message": "+SUM(A1:A2)"}
        ],
    )

    csv_row = read_csv(
        client.get("/api/v1/customers/export?format=csv", headers=headers).content
    )[1]
    assert csv_row[2].startswith("'=")
    assert csv_row[9].startswith("'+SUM")

    xlsx = client.get("/api/v1/customers/export?format=xlsx", headers=headers)
    sheet = load_workbook(io.BytesIO(xlsx.content)).active
    values = list(sheet.values)
    assert values[1][2].startswith("'=")
    # En XLSX, seul « = » est préfixé : « +SUM » reste intact.
    assert values[1][9] == "+SUM(A1:A2)"


def test_viewer_can_export_customers(client, db_session):
    admin = register_admin(client, email="export-viewer-admin@example.com")
    add_prediction(db_session, admin["organization_id"], "C1")
    create_user(
        db_session,
        organization_id=admin["organization_id"],
        email="export-viewer@example.com",
        role="viewer",
    )

    response = client.get(
        "/api/v1/customers/export?format=csv",
        headers=login_headers(client, "export-viewer@example.com"),
    )

    assert response.status_code == 200


def test_export_requires_a_token(client):
    assert client.get("/api/v1/customers/export").status_code == 401


def test_import_export_anomalies_and_isolation(client, db_session):
    admin = register_admin(client, email="export-import@example.com")
    headers = login_headers(client, admin["email"])
    batch = ImportBatch(
        organization_id=admin["organization_id"],
        filename="t.csv",
        source="csv_upload",
        status="failed",
        total_rows=1,
        imported_rows=0,
        error_rows=1,
        anomaly_report=[
            {
                "row_number": 2,
                "external_id": "C1",
                "error_type": "INVALID_DATE",
                "message": "Format de date invalide",
            }
        ],
    )
    db_session.add(batch)
    db_session.commit()

    response = client.get(
        f"/api/v1/imports/{batch.id}/export?format=csv", headers=headers
    )

    assert response.status_code == 200
    assert f"import_{batch.id}_anomalies" in response.headers["content-disposition"]
    rows = read_csv(response.content)
    assert rows[0] == ["row_number", "external_id", "error_type", "message"]
    assert rows[1] == ["2", "C1", "INVALID_DATE", "Format de date invalide"]

    other_org = Organization(name="Autre organisation")
    db_session.add(other_org)
    db_session.commit()
    foreign = ImportBatch(
        organization_id=other_org.id,
        filename="x.csv",
        source="csv_upload",
        status="completed",
        anomaly_report=[],
    )
    db_session.add(foreign)
    db_session.commit()
    assert client.get(
        f"/api/v1/imports/{foreign.id}/export", headers=headers
    ).status_code == 404


def test_history_is_ordered_with_delta_and_model_version(client, db_session):
    admin = register_admin(client, email="history@example.com")
    headers = login_headers(client, admin["email"])
    add_prediction(
        db_session, admin["organization_id"], "C1",
        snapshot=date(2026, 1, 1), score=0.2, level="low", model_version="v1",
    )
    add_prediction(
        db_session, admin["organization_id"], "C1",
        snapshot=date(2026, 2, 1), score=0.5, level="medium", model_version="v2",
    )
    add_prediction(
        db_session, admin["organization_id"], "C1",
        snapshot=date(2026, 3, 1), score=0.4, level="medium", model_version="v3",
    )
    customer = db_session.query(Customer).filter(Customer.external_id == "C1").one()

    response = client.get(
        f"/api/v1/customers/{customer.id}/history", headers=headers
    )

    assert response.status_code == 200, response.text
    items = response.json()["items"]
    assert [item["snapshot_date"] for item in items] == [
        "2026-01-01", "2026-02-01", "2026-03-01",
    ]
    assert [item["score"] for item in items] == [0.2, 0.5, 0.4]
    assert [item["delta"] for item in items] == [None, 0.3, -0.1]
    assert [item["model_version"] for item in items] == ["v1", "v2", "v3"]


def test_history_is_isolated_by_organization(client, db_session):
    admin = register_admin(client, email="history-org@example.com")
    headers = login_headers(client, admin["email"])
    other = Organization(name="Autre organisation")
    db_session.add(other)
    db_session.commit()
    add_prediction(db_session, other.id, "FOREIGN")
    foreign = db_session.query(Customer).filter(Customer.external_id == "FOREIGN").one()

    response = client.get(
        f"/api/v1/customers/{foreign.id}/history", headers=headers
    )

    assert response.status_code == 404


def test_history_requires_a_token(client):
    assert client.get("/api/v1/customers/1/history").status_code == 401


def test_phone_numbers_are_not_prefixed_in_csv(client, db_session):
    admin = register_admin(client, email="export-phone@example.com")
    headers = login_headers(client, admin["email"])
    add_prediction(
        db_session,
        admin["organization_id"],
        "C1",
        phone_number="+33 6 12 34 56 78",
    )

    row = read_csv(
        client.get("/api/v1/customers/export?format=csv", headers=headers).content
    )[1]

    assert row[4] == "+33 6 12 34 56 78"


def test_export_marks_truncation_when_the_cap_is_reached(
    client, db_session, monkeypatch
):
    monkeypatch.setattr(export_service, "MAX_EXPORT_ROWS", 1)
    admin = register_admin(client, email="export-truncated@example.com")
    headers = login_headers(client, admin["email"])
    add_prediction(db_session, admin["organization_id"], "C1", score=0.9)
    add_prediction(db_session, admin["organization_id"], "C2", score=0.8)

    response = client.get("/api/v1/customers/export?format=csv", headers=headers)

    assert response.headers["x-export-truncated"] == "true"
    assert len(read_csv(response.content)) == 2  # en-tête + 1 ligne
