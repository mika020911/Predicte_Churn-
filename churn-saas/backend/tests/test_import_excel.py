"""Tests de l'import Excel : lecture XLSX, fichier invalide, plafond de taille."""

import io

import pandas as pd

from app.config import settings
from app.models import Observation

from tests.helpers import login_headers, register_admin

HEADER = [
    "customer_id",
    "snapshot_date",
    "tenure_months",
    "contract_type",
    "mrr_change_pct",
    "support_tickets_30d",
    "recency_days",
    "frequency_trend_30d",
    "engagement_breadth",
    "payment_failures_90d",
]

ROWS = [
    ["C1", "2026-01-15", 12, "mensuel", 1.5, 0, 5, 1.0, 0.6, 0],
    ["C2", "2026-01-15", 36, "annuel", -1.2, 0, 2, 1.05, 0.9, 0],
]


def xlsx_bytes(rows=ROWS, columns=HEADER) -> bytes:
    buffer = io.BytesIO()
    pd.DataFrame(rows, columns=columns).to_excel(buffer, index=False, engine="openpyxl")
    return buffer.getvalue()


def xlsx_upload(content: bytes, filename: str = "import.xlsx") -> dict:
    return {
        "file": (
            filename,
            content,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }


def test_xlsx_preview_reads_the_first_sheet(client):
    admin = register_admin(client, email="xlsx-preview@example.com")
    headers = login_headers(client, admin["email"])

    response = client.post(
        "/api/v1/imports/preview", headers=headers, files=xlsx_upload(xlsx_bytes())
    )

    assert response.status_code == 200, response.text
    preview = response.json()
    assert preview["csv_columns"] == HEADER
    assert preview["problems"] == []


def test_xlsx_upload_imports_rows(client, db_session):
    admin = register_admin(client, email="xlsx-upload@example.com")
    headers = login_headers(client, admin["email"])

    response = client.post(
        "/api/v1/imports/upload", headers=headers, files=xlsx_upload(xlsx_bytes())
    )

    assert response.status_code == 201, response.text
    batch = response.json()
    assert batch["status"] == "completed"
    assert batch["imported_rows"] == 2
    assert db_session.query(Observation).count() == 2


def test_invalid_xlsx_preview_returns_400(client):
    admin = register_admin(client, email="xlsx-invalid@example.com")
    headers = login_headers(client, admin["email"])

    response = client.post(
        "/api/v1/imports/preview",
        headers=headers,
        files=xlsx_upload(b"ceci n'est pas un classeur"),
    )

    assert response.status_code == 400
    assert "illisible" in response.json()["detail"].lower()


def test_invalid_xlsx_upload_marks_the_batch_as_failed(client):
    admin = register_admin(client, email="xlsx-invalid-upload@example.com")
    headers = login_headers(client, admin["email"])

    response = client.post(
        "/api/v1/imports/upload",
        headers=headers,
        files=xlsx_upload(b"ceci n'est pas un classeur"),
    )

    assert response.status_code == 201
    assert response.json()["status"] == "failed"


def test_file_larger_than_the_configured_limit_is_rejected(client, monkeypatch):
    monkeypatch.setattr(settings, "max_upload_size_mb", 0)
    admin = register_admin(client, email="xlsx-too-big@example.com")
    headers = login_headers(client, admin["email"])

    response = client.post(
        "/api/v1/imports/preview", headers=headers, files=xlsx_upload(xlsx_bytes())
    )

    assert response.status_code == 413
    assert "volumineux" in response.json()["detail"].lower()


def test_unsupported_extension_is_rejected(client):
    admin = register_admin(client, email="xlsx-ext@example.com")
    headers = login_headers(client, admin["email"])

    response = client.post(
        "/api/v1/imports/preview",
        headers=headers,
        files={"file": ("import.txt", b"a,b\n1,2\n", "text/plain")},
    )

    assert response.status_code == 400
