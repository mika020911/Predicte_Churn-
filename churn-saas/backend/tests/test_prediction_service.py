"""Tests du service de prédiction (base SQLite de test, fixture `db_session` de conftest.py).

Prérequis : le modèle ML doit exister (`cd ml/src && python benchmark.py && python make_metadata.py`).
"""
from datetime import date

import pytest

from app.config import settings
from app.models import (
    Customer, ImportBatch, Observation, Organization, Prediction, RiskSettings,
)
from app.services.prediction_service import generate_predictions_for_batch, risk_level_for

MODEL_FILE = settings.ml_src_dir.parent / "models" / "best_model.pkl"
needs_model = pytest.mark.skipif(
    not MODEL_FILE.exists(), reason="Modèle ML absent : lance d'abord ml/src/benchmark.py"
)

SAFE = dict(tenure_months=60, contract_type=1, mrr_change_pct=8.0, support_tickets_30d=0,
            recency_days=1, frequency_trend_30d=1.2, engagement_breadth=0.92, payment_failures_90d=0)
RISKY = dict(tenure_months=3, contract_type=0, mrr_change_pct=-15.0, support_tickets_30d=4,
             recency_days=25, frequency_trend_30d=0.6, engagement_breadth=0.3, payment_failures_90d=2)


# ------------------------------------------------------------------ outils
@pytest.fixture
def org(db_session):
    organization = Organization(name="Acme")
    db_session.add(organization)
    db_session.commit()
    return organization


def make_customer(db, org, external_id):
    customer = Customer(organization_id=org.id, external_id=external_id, name=external_id)
    db.add(customer)
    db.commit()
    return customer


def make_batch(db, org, filename="test.csv"):
    batch = ImportBatch(organization_id=org.id, filename=filename, source="csv_upload",
                        status="COMPLETED", total_rows=0, imported_rows=0, error_rows=0,
                        anomaly_report=[])
    db.add(batch)
    db.commit()
    return batch


def add_observation(db, customer, batch, snapshot, features):
    obs = Observation(customer_id=customer.id, import_batch_id=batch.id, snapshot_date=snapshot, **features)
    db.add(obs)
    db.commit()
    return obs


def predictions_of(db, customer):
    return (db.query(Prediction, Observation.snapshot_date)
            .join(Observation, Observation.id == Prediction.observation_id)
            .filter(Prediction.customer_id == customer.id)
            .order_by(Observation.snapshot_date).all())


# ------------------------------------------------------------ zone de risque
@pytest.mark.parametrize("score, expected", [
    (0.10, "low"), (0.39, "low"), (0.40, "medium"), (0.69, "medium"), (0.70, "high"), (0.99, "high"),
])
def test_risk_level_with_default_thresholds(score, expected):
    assert risk_level_for(score, 0.70, 0.40) == expected


def test_risk_level_follows_custom_thresholds():
    assert risk_level_for(0.60, threshold_high=0.50, threshold_medium=0.20) == "high"
    assert risk_level_for(0.60, threshold_high=0.90, threshold_medium=0.80) == "low"


# --------------------------------------------------------------- prédictions
@needs_model
def test_one_prediction_per_observation(db_session, org):
    batch = make_batch(db_session, org)
    c1, c2 = make_customer(db_session, org, "C1"), make_customer(db_session, org, "C2")
    add_observation(db_session, c1, batch, date(2026, 11, 1), SAFE)
    add_observation(db_session, c2, batch, date(2026, 11, 1), RISKY)

    assert generate_predictions_for_batch(db_session, batch.id, org.id) == 2
    assert db_session.query(Prediction).count() == 2


@needs_model
def test_prediction_contains_score_reasons_and_model_version(db_session, org):
    batch = make_batch(db_session, org)
    customer = make_customer(db_session, org, "C1")
    add_observation(db_session, customer, batch, date(2026, 11, 1), RISKY)
    generate_predictions_for_batch(db_session, batch.id, org.id)

    prediction = predictions_of(db_session, customer)[0][0]
    assert 0.0 <= prediction.score <= 1.0
    assert 1 <= len(prediction.top_reasons) <= 3
    assert set(prediction.shap_values) >= {"tenure_months", "payment_failures_90d"}
    assert prediction.model_version


@needs_model
def test_risky_client_scores_higher_than_safe_client(db_session, org):
    batch = make_batch(db_session, org)
    safe, risky = make_customer(db_session, org, "S"), make_customer(db_session, org, "R")
    add_observation(db_session, safe, batch, date(2026, 11, 1), SAFE)
    add_observation(db_session, risky, batch, date(2026, 11, 1), RISKY)
    generate_predictions_for_batch(db_session, batch.id, org.id)

    assert predictions_of(db_session, risky)[0][0].score > predictions_of(db_session, safe)[0][0].score + 0.3


@needs_model
def test_default_thresholds_used_when_organization_has_no_settings(db_session, org):
    batch = make_batch(db_session, org)
    customer = make_customer(db_session, org, "R")
    add_observation(db_session, customer, batch, date(2026, 11, 1), RISKY)
    generate_predictions_for_batch(db_session, batch.id, org.id)
    assert predictions_of(db_session, customer)[0][0].risk_level == "high"


@needs_model
def test_risk_level_uses_organization_thresholds(db_session, org):
    db_session.add(RiskSettings(organization_id=org.id, threshold_high=0.9999, threshold_medium=0.9998))
    db_session.commit()
    batch = make_batch(db_session, org)
    customer = make_customer(db_session, org, "R")
    add_observation(db_session, customer, batch, date(2026, 11, 1), RISKY)
    generate_predictions_for_batch(db_session, batch.id, org.id)
    assert predictions_of(db_session, customer)[0][0].risk_level == "low"


# ------------------------------------------------------------ prédiction active
@needs_model
def test_only_latest_snapshot_is_active(db_session, org):
    customer = make_customer(db_session, org, "C1")
    first, second = make_batch(db_session, org, "a.csv"), make_batch(db_session, org, "b.csv")
    add_observation(db_session, customer, first, date(2026, 11, 1), RISKY)
    generate_predictions_for_batch(db_session, first.id, org.id)
    add_observation(db_session, customer, second, date(2026, 11, 8), SAFE)
    generate_predictions_for_batch(db_session, second.id, org.id)

    rows = predictions_of(db_session, customer)
    assert [p.is_active for p, _ in rows] == [False, True]


@needs_model
def test_older_snapshot_imported_later_does_not_replace_active_prediction(db_session, org):
    customer = make_customer(db_session, org, "C1")
    recent, late_old = make_batch(db_session, org, "recent.csv"), make_batch(db_session, org, "old.csv")
    add_observation(db_session, customer, recent, date(2026, 11, 8), SAFE)
    generate_predictions_for_batch(db_session, recent.id, org.id)
    add_observation(db_session, customer, late_old, date(2026, 10, 1), RISKY)  # importé après coup
    generate_predictions_for_batch(db_session, late_old.id, org.id)

    rows = predictions_of(db_session, customer)
    assert [(s, p.is_active) for p, s in rows] == [(date(2026, 10, 1), False), (date(2026, 11, 8), True)]


@needs_model
def test_rerunning_on_same_batch_creates_no_duplicate(db_session, org):
    batch = make_batch(db_session, org)
    customer = make_customer(db_session, org, "C1")
    add_observation(db_session, customer, batch, date(2026, 11, 1), RISKY)

    assert generate_predictions_for_batch(db_session, batch.id, org.id) == 1
    assert generate_predictions_for_batch(db_session, batch.id, org.id) == 0
    assert db_session.query(Prediction).count() == 1


@needs_model
def test_empty_batch_returns_zero(db_session, org):
    batch = make_batch(db_session, org)
    assert generate_predictions_for_batch(db_session, batch.id, org.id) == 0