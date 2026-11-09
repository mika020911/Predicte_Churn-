"""Tests du module ML : prédiction, explications SHAP et découpage des données.

Prérequis : avoir lancé generate_data.py, benchmark.py et make_metadata.py.
"""
import pytest

from config import BEST_MODEL_PATH, FEATURE_COLUMNS, RAW_DATA_PATH

SAFE_CLIENT = {
    "tenure_months": 60, "contract_type": 1, "mrr_change_pct": 8.0,
    "support_tickets_30d": 0, "recency_days": 1, "frequency_trend_30d": 1.2,
    "engagement_breadth": 0.92, "payment_failures_90d": 0,
}
RISKY_CLIENT = {
    "tenure_months": 3, "contract_type": 0, "mrr_change_pct": -15.0,
    "support_tickets_30d": 4, "recency_days": 25, "frequency_trend_30d": 0.60,
    "engagement_breadth": 0.30, "payment_failures_90d": 2,
}

needs_model = pytest.mark.skipif(
    not BEST_MODEL_PATH.exists(), reason="Modèle absent : lance d'abord benchmark.py"
)
needs_data = pytest.mark.skipif(
    not RAW_DATA_PATH.exists(), reason="Données absentes : lance d'abord generate_data.py"
)


@pytest.fixture(scope="module")
def predictor():
    from predict import get_predictor
    return get_predictor()


@needs_model
def test_score_is_a_probability(predictor):
    for client in (SAFE_CLIENT, RISKY_CLIENT):
        assert 0.0 <= predictor.predict(client)["score"] <= 1.0


@needs_model
def test_risky_client_scores_higher_than_safe_client(predictor):
    assert predictor.predict(RISKY_CLIENT)["score"] > predictor.predict(SAFE_CLIENT)["score"] + 0.3


@needs_model
def test_at_most_three_reasons_and_all_increase_risk(predictor):
    reasons = predictor.predict(RISKY_CLIENT)["top_reasons"]
    assert 1 <= len(reasons) <= 3
    assert all(r["impact"] > 0 for r in reasons)
    assert all(r["feature"] in FEATURE_COLUMNS and r["message"] for r in reasons)


@needs_model
def test_safe_client_has_few_or_no_risk_reasons(predictor):
    assert len(predictor.predict(SAFE_CLIENT)["top_reasons"]) <= 3


@needs_model
def test_result_contains_expected_keys(predictor):
    result = predictor.predict(RISKY_CLIENT)
    assert {"score", "top_reasons", "shap_values", "model_version"} <= result.keys()
    assert set(result["shap_values"]) == set(FEATURE_COLUMNS)


@needs_model
def test_batch_gives_same_result_as_single_predictions(predictor):
    batch = predictor.predict_batch([SAFE_CLIENT, RISKY_CLIENT])
    assert [b["score"] for b in batch] == [
        predictor.predict(SAFE_CLIENT)["score"], predictor.predict(RISKY_CLIENT)["score"]
    ]


@needs_model
def test_empty_batch_returns_empty_list(predictor):
    assert predictor.predict_batch([]) == []


@needs_model
def test_missing_column_raises_clear_error(predictor):
    with pytest.raises(ValueError, match="Colonnes manquantes"):
        predictor.predict({"tenure_months": 3})


@needs_model
def test_missing_value_is_accepted(predictor):
    client = {**RISKY_CLIENT, "mrr_change_pct": None}
    assert 0.0 <= predictor.predict(client)["score"] <= 1.0


@needs_model
def test_negative_revenue_change_is_worded_without_double_negative(predictor):
    from explain import REASON_MESSAGES
    message = REASON_MESSAGES["mrr_change_pct"](-5.2)
    assert "5.2%" in message and "-" not in message


@needs_model
def test_model_is_loaded_only_once():
    from predict import get_predictor
    assert get_predictor() is get_predictor()


@needs_data
def test_temporal_split_has_no_overlap_and_loses_no_row():
    from config import DATE_COLUMN
    from preprocess import load_data, temporal_split

    df = load_data()
    train, val, test = temporal_split(df)
    assert train[DATE_COLUMN].max() < val[DATE_COLUMN].min()
    assert val[DATE_COLUMN].max() < test[DATE_COLUMN].min()
    assert len(train) + len(val) + len(test) == len(df)