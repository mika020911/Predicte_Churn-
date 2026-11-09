"""Calibre le modèle gagnant, puis passe l'examen final sur le jeu de TEST (une seule fois).

Calibrer = faire en sorte que « 70 % » veuille vraiment dire « 70 clients sur 100 partent ».
  - la calibration s'apprend sur le jeu de VALIDATION ;
  - le jeu de TEST sert uniquement à mesurer le résultat final.
"""
import json

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.frozen import FrozenEstimator
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score

from config import (
    BEST_MODEL_PATH, CALIBRATED_MODEL_PATH, CALIBRATION_PLOT_PATH, CALIBRATION_RESULTS_PATH,
)
from preprocess import load_splits


def expected_calibration_error(y_true, proba, n_bins=10):
    """Écart moyen entre la probabilité annoncée et la fréquence réelle de départ."""
    bins = np.quantile(proba, np.linspace(0, 1, n_bins + 1))
    ids = np.clip(np.digitize(proba, bins[1:-1]), 0, n_bins - 1)
    ece = 0.0
    for b in range(n_bins):
        mask = ids == b
        if mask.any():
            ece += mask.mean() * abs(proba[mask].mean() - y_true[mask].mean())
    return float(ece)


def metrics(y, proba):
    y = np.asarray(y)
    return {
        "auc_pr": float(average_precision_score(y, proba)),
        "auc_roc": float(roc_auc_score(y, proba)),
        "brier": float(brier_score_loss(y, proba)),
        "ece": expected_calibration_error(y, proba),
    }


def plot_calibration(y, probas):
    fig, ax = plt.subplots(figsize=(5.5, 5))
    ax.plot([0, 1], [0, 1], "--", color="grey", label="Calibration parfaite")
    for name, proba in probas.items():
        frac_pos, mean_pred = calibration_curve(y, proba, n_bins=10, strategy="quantile")
        ax.plot(mean_pred, frac_pos, marker="o", label=name)
    ax.set(
        title="Courbe de calibration (test)",
        xlabel="Probabilité annoncée par le modèle",
        ylabel="Part réelle de clients partis",
    )
    ax.legend()
    fig.tight_layout()
    fig.savefig(CALIBRATION_PLOT_PATH, dpi=150)
    plt.close(fig)


def main():
    splits = load_splits()
    X_val, y_val = splits["val"]
    X_test, y_test = splits["test"]

    model = joblib.load(BEST_MODEL_PATH)  # modèle gagnant, déjà entraîné
    calibrated = CalibratedClassifierCV(FrozenEstimator(model), method="isotonic")
    calibrated.fit(X_val, y_val)

    proba_raw = model.predict_proba(X_test)[:, 1]
    proba_cal = calibrated.predict_proba(X_test)[:, 1]
    results = {"avant calibration": metrics(y_test, proba_raw), "après calibration": metrics(y_test, proba_cal)}

    print(f"=== Examen final sur le TEST ({len(X_test)} lignes) ===")
    print(f"{'':<20}{'AUC-PR':>8}{'AUC-ROC':>9}{'Brier':>8}{'ECE':>8}")
    for name, m in results.items():
        print(f"{name:<20}{m['auc_pr']:>8.3f}{m['auc_roc']:>9.3f}{m['brier']:>8.3f}{m['ece']:>8.3f}")
    print(f"\nProbabilité moyenne annoncée : {proba_cal.mean():.3f} | part réelle de partants : {np.mean(y_test):.3f}")

    joblib.dump(calibrated, CALIBRATED_MODEL_PATH)
    CALIBRATION_RESULTS_PATH.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    plot_calibration(y_test, {"Avant calibration": proba_raw, "Après calibration": proba_cal})
    print(f"Modèle calibré sauvegardé : {CALIBRATED_MODEL_PATH}")
    print(f"Résultats : {CALIBRATION_RESULTS_PATH}")
    print(f"Courbe : {CALIBRATION_PLOT_PATH}")


if __name__ == "__main__":
    main()