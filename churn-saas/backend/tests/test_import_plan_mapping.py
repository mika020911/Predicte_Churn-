"""Tests du classement des plans (plan_tier_rank) : calcul des rangs, endpoint de mapping, import CSV."""
import io

from app.models import Observation
from app.services.import_service import (
    NEUTRAL_PLAN_TIER_RANK,
    compute_plan_ranks,
    distinct_plan_labels,
    plan_order_from_ranks,
    suggest_column_mapping,
)

import pandas as pd

HEADER = ("customer_id,snapshot_date,tenure_months,contract_type,mrr_change_pct,support_tickets_30d,"
          "recency_days,frequency_trend_30d,engagement_breadth,payment_failures_90d")


def register_and_login(client, email="a@company.com", organization="Org A"):
    client.post("/api/v1/auth/register", json={
        "email": email, "password": "Password123!", "full_name": "Test", "organization_name": organization,
    })
    token = client.post("/api/v1/auth/login/json",
                        json={"email": email, "password": "Password123!"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def csv_file(rows, with_plan=True):
    """rows : liste de (customer_id, plan). Les autres colonnes ont des valeurs valides fixes."""
    header = HEADER + (",plan" if with_plan else "")
    lines = [header]
    for customer_id, plan in rows:
        line = f"{customer_id},2026-01-15,12,mensuel,1.5,0,5,1.0,0.6,0"
        lines.append(line + (f",{plan}" if with_plan else ""))
    return ("import.csv", io.BytesIO("\n".join(lines).encode()), "text/csv")


# ------------------------------------------------------------------ fonctions pures
def test_ranks_are_spread_between_0_and_1():
    assert compute_plan_ranks(["Standard", "Pro", "Max Ultra"]) == {
        "standard": 0.0, "pro": 0.5, "max ultra": 1.0,
    }
    assert compute_plan_ranks(["Access", "Évasion", "Access+", "Tout Canal+"])["access+"] == 0.667


def test_single_plan_gets_the_neutral_rank():
    assert compute_plan_ranks(["Unique"]) == {"unique": NEUTRAL_PLAN_TIER_RANK}


def test_ranks_ignore_case_accents_and_duplicates():
    ranks = compute_plan_ranks(["Évasion", "evasion ", "PREMIUM"])
    assert ranks == {"evasion": 0.0, "premium": 1.0}


def test_no_plan_gives_no_rank():
    assert compute_plan_ranks([]) == {}


def test_order_is_rebuilt_from_ranks():
    ranks = compute_plan_ranks(["basic", "plus", "business"])
    assert plan_order_from_ranks(ranks) == ["basic", "plus", "business"]


def test_distinct_labels_keep_first_spelling_and_skip_blanks():
    series = pd.Series(["Pro", "pro", None, " ", "Premium"])
    assert distinct_plan_labels(series) == ["Pro", "Premium"]


def test_explicit_none_mapping_is_not_redetected_by_name():
    columns = ["customer_id", "plan"]
    assert suggest_column_mapping(columns, {"plan": None})["plan"] is None
    assert suggest_column_mapping(columns, {})["plan"] == "plan"  # sans consigne : détection par nom


def test_neutral_rank_matches_the_ml_module():
    from app.services.ml_client import feature_columns

    columns = feature_columns()  # cet appel ajoute ml/src au chemin Python
    from config import NEUTRAL_PLAN_TIER_RANK as ml_neutral

    assert ml_neutral == NEUTRAL_PLAN_TIER_RANK
    assert "plan_tier_rank" in columns


# ------------------------------------------------------------------ endpoint /imports/mapping
def test_plan_order_is_saved_as_ranks(client):
    headers = register_and_login(client)
    response = client.put("/api/v1/imports/mapping", headers=headers,
                          json={"plan_order": ["Standard", "Pro", "Max Ultra"]})
    assert response.status_code == 200
    assert response.json()["plan_mapping"] == {"standard": 0.0, "pro": 0.5, "max ultra": 1.0}


def test_plan_listed_twice_is_rejected(client):
    headers = register_and_login(client)
    response = client.put("/api/v1/imports/mapping", headers=headers,
                          json={"plan_order": ["Pro", "pro"]})
    assert response.status_code == 422


def test_preview_proposes_unknown_plans_after_the_saved_ones(client):
    headers = register_and_login(client)
    client.put("/api/v1/imports/mapping", headers=headers, json={"plan_order": ["standard", "pro"]})
    preview = client.post("/api/v1/imports/preview", headers=headers,
                          files={"file": csv_file([("C1", "Pro"), ("C2", "Max Ultra")])}).json()
    assert preview["unknown_plan_values"] == ["Max Ultra"]
    assert preview["proposed_plan_order"] == ["standard", "pro", "Max Ultra"]


# ------------------------------------------------------------------ import
def test_import_is_refused_while_plans_are_unranked(client, db_session):
    headers = register_and_login(client)
    batch = client.post("/api/v1/imports/upload", headers=headers,
                        files={"file": csv_file([("C1", "Standard"), ("C2", "Pro")])}).json()
    assert batch["status"] == "failed"
    assert "Plans non classés" in batch["error_message"]
    assert db_session.query(Observation).count() == 0


def test_import_stores_the_rank_of_each_plan(client, db_session):
    headers = register_and_login(client)
    client.put("/api/v1/imports/mapping", headers=headers, json={"plan_order": ["Standard", "Pro", "Max Ultra"]})
    batch = client.post("/api/v1/imports/upload", headers=headers, files={
        "file": csv_file([("C1", "standard"), ("C2", "PRO"), ("C3", "Max Ultra")])}).json()
    assert batch["status"] == "completed" and batch["imported_rows"] == 3
    ranks = {o.customer.external_id: o.plan_tier_rank for o in db_session.query(Observation).all()}
    assert ranks == {"C1": 0.0, "C2": 0.5, "C3": 1.0}


def test_row_with_missing_plan_is_reported_not_imported(client, db_session):
    headers = register_and_login(client)
    client.put("/api/v1/imports/mapping", headers=headers, json={"plan_order": ["Standard", "Pro"]})
    batch = client.post("/api/v1/imports/upload", headers=headers, files={
        "file": csv_file([("C1", "Standard"), ("C2", "")])}).json()
    assert batch["imported_rows"] == 1 and batch["error_rows"] == 1
    assert "plan manquant" in batch["anomaly_report"][0]["message"]


def test_csv_without_plan_column_uses_the_neutral_rank(client, db_session):
    headers = register_and_login(client)
    batch = client.post("/api/v1/imports/upload", headers=headers,
                        files={"file": csv_file([("C1", None)], with_plan=False)}).json()
    assert batch["status"] == "completed"
    assert db_session.query(Observation).one().plan_tier_rank == NEUTRAL_PLAN_TIER_RANK
