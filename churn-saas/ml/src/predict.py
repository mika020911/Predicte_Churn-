"""Service de prédiction utilisé par le backend : score de risque + 3 raisons.

Le modèle n'est chargé qu'une seule fois (get_predictor).
predict() renvoie le SCORE et les RAISONS ; la zone vert / orange / rouge se calcule
dans le backend, avec les seuils propres à chaque organisation.
"""
import json
from functools import lru_cache

import pandas as pd

from config import FEATURE_COLUMNS, METADATA_PATH
from explain import ChurnExplainer

class ChurnPredictor:
    def __init__(self):
        self.metadata = json.loads(METADATA_PATH.read_text()) if METADATA_PATH.exists() else {}
        saved_columns = self.metadata.get("feature_columns")
        if saved_columns and saved_columns != FEATURE_COLUMNS:
            raise RuntimeError(
                "Les colonnes du modèle ne correspondent plus à FEATURE_COLUMNS : "
                "relance benchmark.py puis make_metadata.py."
            )
        self.explainer = ChurnExplainer()
        self.model_version = self.metadata.get("model_version", "inconnu")

    def predict_batch(self, records: list[dict]) -> list[dict]:
        """Prédit pour plusieurs clients à la fois (beaucoup plus rapide qu'un par un)."""
        if not records:
            return []
        df = pd.DataFrame(records)
        missing = [c for c in FEATURE_COLUMNS if c not in df.columns]
        if missing:
            raise ValueError(f"Colonnes manquantes : {missing}")
        X = df[FEATURE_COLUMNS].astype(float)  # une valeur absente (None) devient NaN

        probas = self.explainer.model.predict_proba(X)[:, 1]
        shap_matrix = self.explainer.shap_values(X)
        rows = X.to_dict("records")

        return [
            {
                "score": round(float(p), 4),
                "top_reasons": self.explainer.top_reasons(row, shap_row),
                "shap_values": {f: round(float(v), 4) for f, v in zip(FEATURE_COLUMNS, shap_row)},
                "model_version": self.model_version,
            }
            for p, row, shap_row in zip(probas, rows, shap_matrix)
        ]

    def predict(self, record: dict) -> dict:
        """Prédit pour un seul client."""
        return self.predict_batch([record])[0]


@lru_cache(maxsize=1)
def get_predictor() -> ChurnPredictor:
    """Charge le modèle une seule fois pour toute la durée de vie de l'application."""
    return ChurnPredictor()


def main():
    import time

    from preprocess import load_splits

    predictor = get_predictor()
    print(f"Modèle chargé : {predictor.model_version}")

    client = {
        "tenure_months": 3, "contract_type": 0, "mrr_change_pct": -15.0,
        "support_tickets_30d": 4, "recency_days": 25, "frequency_trend_30d": 0.60,
        "engagement_breadth": 0.30, "payment_failures_90d": 2,
    }
    result = predictor.predict(client)
    print(f"\nScore : {result['score']:.0%}")
    for r in result["top_reasons"]:
        print(f"   - {r['message']}")

    X_test, _ = load_splits()["test"]
    start = time.perf_counter()
    predictor.predict_batch(X_test.to_dict("records"))
    print(f"\n{len(X_test)} clients prédits en {time.perf_counter() - start:.2f} s")


if __name__ == "__main__":
    main()