# ml/src/predict.py
"""
Service de prédiction : charge le modèle, prédit, explique avec SHAP.
Utilisé à la fois en standalone et par le backend FastAPI.
"""

import numpy as np
import pandas as pd
import joblib
import shap

from config import (
    CALIBRATED_MODEL_PATH,
    MODEL_PATH,
    PREPROCESSOR_PATH,
    FEATURE_COLUMNS,
    RISK_THRESHOLD_HIGH,
    RISK_THRESHOLD_MEDIUM,
)


# Dictionnaire de gabarits d'explication
EXPLANATION_TEMPLATES = {
    "tenure_months": {
        "positive": "Ancienneté faible ({value} mois), le client est encore en phase de découverte",
        "negative": "Client fidèle depuis {value} mois, signe de stabilité",
    },
    "contract_type": {
        "positive": "Contrat mensuel, plus facile à résilier",
        "negative": "Contrat annuel, engagement plus fort",
    },
    "mrr_change_pct": {
        "positive": "Baisse de la valeur d'abonnement de {value:.1f}%",
        "negative": "Augmentation de la valeur d'abonnement de {value:.1f}%",
    },
    "support_tickets_30d": {
        "positive": "{value} tickets support ouverts en 30 jours, signe de friction",
        "negative": "Peu de tickets support ({value}), expérience fluide",
    },
    "recency_days": {
        "positive": "Inactif depuis {value} jours, risque de désengagement",
        "negative": "Dernière activité il y a {value} jours, client actif",
    },
    "frequency_trend_30d": {
        "positive": "Baisse d'utilisation de {pct:.0f}% sur les 30 derniers jours",
        "negative": "Hausse d'utilisation de {pct:.0f}% sur les 30 derniers jours",
    },
    "engagement_breadth": {
        "positive": "Utilise seulement {pct:.0f}% des fonctionnalités disponibles",
        "negative": "Utilise {pct:.0f}% des fonctionnalités, bon niveau d'adoption",
    },
    "payment_failures_90d": {
        "positive": "{value} échec(s) de paiement sur 90 jours",
        "negative": "Aucun problème de paiement",
    },
}


class ChurnPredictor:
    """Encapsule le chargement du modèle, la prédiction et l'explication SHAP."""

    def __init__(self):
        self.calibrated_model = joblib.load(CALIBRATED_MODEL_PATH)
        self.raw_model = joblib.load(MODEL_PATH)
        self.preprocessor = joblib.load(PREPROCESSOR_PATH)
        self.explainer = shap.TreeExplainer(self.raw_model)

        # Reconstruire les noms des features après preprocessing
        numeric_features = [f for f in FEATURE_COLUMNS if f != "contract_type"]
        self.feature_names = numeric_features + ["contract_type"]

    def predict(self, data: dict) -> dict:
        """
        Prédit le risque de churn pour un client.

        Args:
            data: dict avec les clés correspondant à FEATURE_COLUMNS.

        Returns:
            dict avec score, risk_level, top_reasons.
        """
        # Préparer les données
        df = pd.DataFrame([data])[FEATURE_COLUMNS]
        X_processed = self.preprocessor.transform(df)

        # Prédiction calibrée
        proba = self.calibrated_model.predict_proba(X_processed)[0, 1]
        score = round(float(proba), 4)

        # Niveau de risque
        if score >= RISK_THRESHOLD_HIGH:
            risk_level = "high"
        elif score >= RISK_THRESHOLD_MEDIUM:
            risk_level = "medium"
        else:
            risk_level = "low"

        # Explications SHAP
        shap_values = self.explainer.shap_values(X_processed)
        if isinstance(shap_values, list):
            shap_vals = shap_values[1][0]  # classe churn
        else:
            shap_vals = shap_values[0]

        top_reasons = self._get_top_reasons(shap_vals, data, n=3)

        return {
            "score": score,
            "risk_level": risk_level,
            "top_reasons": top_reasons,
            "shap_values": {
                name: round(float(val), 4)
                for name, val in zip(self.feature_names, shap_vals)
            },
        }

    def predict_batch(self, records: list[dict]) -> list[dict]:
        """Prédit pour un lot de clients."""
        return [self.predict(record) for record in records]

    def _get_top_reasons(
        self, shap_vals: np.ndarray, original_data: dict, n: int = 3
    ) -> list[dict]:
        """Extrait les N raisons les plus influentes avec gabarits."""
        # Trier par valeur absolue de SHAP décroissante
        indices = np.argsort(np.abs(shap_vals))[::-1][:n]

        reasons = []
        for idx in indices:
            feature_name = self.feature_names[idx]
            shap_val = float(shap_vals[idx])
            raw_value = original_data.get(feature_name, 0)

            # Choisir le gabarit
            direction = "positive" if shap_val > 0 else "negative"
            template_dict = EXPLANATION_TEMPLATES.get(feature_name, {})
            template = template_dict.get(direction, f"{feature_name} a un impact {'positif' if shap_val > 0 else 'négatif'}")

            # Formater le message
            try:
                if feature_name == "frequency_trend_30d":
                    pct = abs(1 - raw_value) * 100
                    message = template.format(pct=pct, value=raw_value)
                elif feature_name == "engagement_breadth":
                    pct = raw_value * 100
                    message = template.format(pct=pct, value=raw_value)
                else:
                    message = template.format(value=raw_value)
            except (KeyError, ValueError):
                message = template

            reasons.append({
                "feature": feature_name,
                "shap_value": round(shap_val, 4),
                "direction": "risk" if shap_val > 0 else "protection",
                "message": message,
            })

        return reasons


# Singleton pour éviter les rechargements multiples
_predictor = None


def get_predictor() -> ChurnPredictor:
    """Retourne un singleton du prédicteur."""
    global _predictor
    if _predictor is None:
        _predictor = ChurnPredictor()
    return _predictor


if __name__ == "__main__":
    # Test rapide
    predictor = get_predictor()

    test_client = {
        "tenure_months": 3,
        "contract_type": 0,
        "mrr_change_pct": -5.2,
        "support_tickets_30d": 4,
        "recency_days": 25,
        "frequency_trend_30d": 0.6,
        "engagement_breadth": 0.3,
        "payment_failures_90d": 2,
    }

    result = predictor.predict(test_client)

    print("=" * 60)
    print("TEST DE PRÉDICTION")
    print("=" * 60)
    print(f"\nScore de risque : {result['score']:.2%}")
    print(f"Niveau de risque : {result['risk_level']}")
    print(f"\nRaisons principales :")
    for i, reason in enumerate(result["top_reasons"], 1):
        icon = "🔴" if reason["direction"] == "risk" else "🟢"
        print(f"  {i}. {icon} {reason['message']}")
        print(f"     (SHAP: {reason['shap_value']:+.4f})")
    print(f"\nValeurs SHAP complètes : {result['shap_values']}")