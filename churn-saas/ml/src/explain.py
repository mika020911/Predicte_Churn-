"""Explication des prédictions avec SHAP : pourquoi ce client est à risque ?

SHAP donne, pour chaque client, la contribution de chacune des 8 colonnes au score.
  - contribution positive  -> la colonne AUGMENTE le risque de départ ;
  - contribution négative  -> la colonne DIMINUE le risque.
On garde les N colonnes qui augmentent le plus le risque et on les traduit en phrases.
"""
import joblib
import numpy as np
import pandas as pd
import shap

from config import BEST_MODEL_PATH, FEATURE_COLUMNS, N_REASONS

# Une phrase par colonne, choisie d'après la VALEUR réelle du client (pas seulement le signe SHAP).
REASON_MESSAGES = {
    "tenure_months": lambda v: (
        f"Client récent ({v:.0f} mois), encore en phase de découverte"
        if v <= 12 else f"Ancienneté de {v:.0f} mois, mais moins ancré que les clients les plus fidèles"
    ),
    "contract_type": lambda v: (
        "Contrat mensuel, plus facile à résilier" if v == 0 else "Contrat annuel"
    ),
    "mrr_change_pct": lambda v: (
        f"Baisse de {abs(v):.1f}% de la valeur d'abonnement" if v < 0
        else f"Valeur d'abonnement en hausse de {v:.1f}%, mais profil à surveiller"
    ),
    "support_tickets_30d": lambda v: f"{v:.0f} ticket(s) support ouvert(s) en 30 jours, signe de friction",
    "recency_days": lambda v: f"Inactif depuis {v:.0f} jours, risque de désengagement",
    "frequency_trend_30d": lambda v: (
        f"Baisse d'utilisation de {(1 - v) * 100:.0f}% sur les 30 derniers jours" if v < 1
        else "Utilisation stable ou en hausse, mais profil à surveiller"
    ),
    "engagement_breadth": lambda v: f"Utilise seulement {v * 100:.0f}% des fonctionnalités disponibles",
    "payment_failures_90d": lambda v: f"{v:.0f} échec(s) de paiement sur 90 jours",
}


class ChurnExplainer:
    """Charge le modèle une seule fois et explique les prédictions."""

    def __init__(self, model_path=BEST_MODEL_PATH):
        self.model = joblib.load(model_path)
        self.explainer = shap.TreeExplainer(self.model)

    def shap_values(self, X: pd.DataFrame) -> np.ndarray:
        """Contributions SHAP, un tableau (nb_clients, 8) pour la classe « part »."""
        values = self.explainer.shap_values(X[FEATURE_COLUMNS])
        if isinstance(values, list):      # anciens formats : une liste par classe
            values = values[1]
        values = np.asarray(values)
        if values.ndim == 3:              # format (clients, colonnes, classes)
            values = values[:, :, 1]
        return values

    def top_reasons(self, row: dict, shap_row: np.ndarray, n: int = N_REASONS) -> list[dict]:
        """Les n colonnes qui augmentent le plus le risque (contribution > 0 uniquement)."""
        order = np.argsort(shap_row)[::-1]
        reasons = []
        for idx in order:
            if shap_row[idx] <= 0 or len(reasons) == n:
                break
            feature = FEATURE_COLUMNS[idx]
            reasons.append({
                "feature": feature,
                "impact": round(float(shap_row[idx]), 3),
                "message": REASON_MESSAGES[feature](float(row[feature])),
            })
        return reasons

    def explain(self, X: pd.DataFrame) -> list[list[dict]]:
        """Pour chaque client de X, renvoie sa liste de raisons."""
        values = self.shap_values(X)
        rows = X[FEATURE_COLUMNS].to_dict("records")
        return [self.top_reasons(row, vals) for row, vals in zip(rows, values)]


def main():
    from config import SHAP_PLOT_PATH
    from preprocess import load_splits

    explainer = ChurnExplainer()
    X_val, _ = load_splits()["val"]

    # 1) Démo sur 5 clients types
    demo = pd.DataFrame([
        [36, 1, 2.5, 0, 2, 1.05, 0.85, 0],     # client sûr
        [3, 0, -15.0, 4, 25, 0.60, 0.30, 2],   # client très à risque
        [14, 0, 0.0, 1, 8, 0.95, 0.55, 0],     # intermédiaire
        [8, 0, -5.2, 3, 18, 0.70, 0.40, 1],    # en dégradation
        [60, 1, 8.0, 0, 1, 1.20, 0.92, 0],     # très fidèle
    ], columns=FEATURE_COLUMNS)
    probas = explainer.model.predict_proba(demo)[:, 1]
    for i, reasons in enumerate(explainer.explain(demo)):
        print(f"\nClient {i + 1} : risque {probas[i]:.0%}")
        for r in reasons or [{"message": "(aucun facteur ne fait monter le risque)", "impact": 0}]:
            print(f"   - {r['message']}  [impact {r['impact']:+.2f}]")

    # 2) Contrôle : SHAP + valeur de base doit retrouver le score du modèle (en log-odds)
    values = explainer.shap_values(X_val)
    base = float(np.ravel(explainer.explainer.expected_value)[0])
    reconstructed = 1 / (1 + np.exp(-(base + values.sum(axis=1))))
    gap = np.abs(reconstructed - explainer.model.predict_proba(X_val)[:, 1]).max()
    print(f"\nContrôle d'additivité : écart maximal {gap:.6f} (doit être proche de 0)")

    # 3) Importance globale des colonnes
    importance = pd.Series(np.abs(values).mean(axis=0), index=FEATURE_COLUMNS).sort_values(ascending=False)
    print("\nColonnes les plus influentes (moyenne des |SHAP|) :")
    print(importance.round(3).to_string())

    # 4) Graphique pour le rapport
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    shap.summary_plot(values, X_val[FEATURE_COLUMNS], show=False)
    plt.tight_layout()
    plt.savefig(SHAP_PLOT_PATH, dpi=150)
    plt.close()
    print(f"\nGraphique : {SHAP_PLOT_PATH}")


if __name__ == "__main__":
    main()