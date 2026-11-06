import json

import matplotlib
import joblib
from sklearn.linear_model import LogisticRegression

matplotlib.use("Agg")  #save image dans un fichier plutot que de l'afficher
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (average_precision_score, brier_score_loss, confusion_matrix, f1_score,
    precision_recall_curve, precision_score, recall_score, roc_auc_score, roc_curve,
)
from sklearn.model_selection import RandomizedSearchCV, StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

from config import (
    BENCHMARK_PLOT_PATH, BENCHMARK_RESULTS_PATH, BEST_MODEL_PATH, CV_FOLDS,
    DECISION_THRESHOLD, N_ITER_SEARCH, RANDOM_STATE, RF_PARAM_GRID, XGB_PARAM_GRID,
)
from preprocess import load_splits

def search_best(name, estimator, param_grid, X_train, y_train):
    #Essaie N combinaisons de N HP et renvoie le meilleur modele entrainer
    print(f"\n[{name}] recherche des meilleurs réglages ({N_ITER_SEARCH} essais)...")
    search = RandomizedSearchCV(
        estimator,
        param_distributions=param_grid,
        n_iter=N_ITER_SEARCH,
        scoring="average_precision",
        cv=StratifiedKFold(CV_FOLDS, shuffle=True, random_state=RANDOM_STATE),
        random_state=RANDOM_STATE,
        n_jobs=-1,
        refit=True,
    )
    search.fit(X_train, y_train)
    print(f"  meilleur score (validation croisée) : {search.best_score_:.3f}")
    print(f"  réglages retenus : {search.best_params_}")
    return search.best_estimator_, search.best_params_

def evaluate(model, X, y):
    #calcule les metrique d'un model sur un jeu de données
    proba = model.predict_proba(X)[:, 1]
    pred = (proba >= DECISION_THRESHOLD).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred).ravel()
    return {
        "auc_pr": average_precision_score(y, proba),
        "auc_roc": roc_auc_score(y, proba),
        "brier": brier_score_loss(y, proba),
        "recall": recall_score(y, pred),
        "precision": precision_score(y, pred, zero_division=0),
        "f1": f1_score(y, pred),
        "confusion": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
    }

def plot_curves(models, X_val, y_val):
    #Trace les courbes précision-rappel et ROC des modèles sur la validation

    fig, (ax_pr, ax_roc) = plt.subplots(1, 2, figsize=(11, 4.5))
    for name, model in models.items():
        proba = model.predict_proba(X_val)[:, 1]
        prec, rec, _ = precision_recall_curve(y_val, proba)
        fpr, tpr, _ = roc_curve(y_val, proba)
        ax_pr.plot(rec, prec, label=name)
        ax_roc.plot(fpr, tpr, label=name)
    ax_pr.set(title="Précision-rappel (validation)", xlabel="Rappel", ylabel="Précision")
    ax_roc.plot([0, 1], [0, 1], "--", color="grey")
    ax_roc.set(title="ROC (validation)", xlabel="Faux positifs", ylabel="Vrais positifs")
    ax_pr.legend()
    ax_roc.legend()
    fig.tight_layout()
    fig.savefig(BENCHMARK_PLOT_PATH, dpi=150)
    plt.close(fig)

def main():
    splits = load_splits()
    X_train, y_train = splits["train"]
    X_val, y_val = splits["val"]
    print(f"Entraînement : {len(X_train)} lignes | Validation : {len(X_val)} lignes")

    # Référence : un modèle simple, pour savoir si les modèles complexes apportent vraiment quelque chose
    baseline = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
    baseline.fit(X_train, y_train)

    rf, rf_params = search_best(
        "Random Forest",
        RandomForestClassifier(random_state=RANDOM_STATE, n_jobs=1),
        RF_PARAM_GRID, X_train, y_train,
    )
    xgb, xgb_params = search_best(
        "XGBoost",
        XGBClassifier(eval_metric="logloss", random_state=RANDOM_STATE, n_jobs=1),
        XGB_PARAM_GRID, X_train, y_train,
    )

    models = {"Régression logistique (référence)": baseline, "Random Forest": rf, "XGBoost": xgb}
    results = {name: evaluate(model, X_val, y_val) for name, model in models.items()}

    print(f"\n=== Résultats sur la VALIDATION (seuil {DECISION_THRESHOLD}) ===")
    print(f"{'modèle':<34}{'AUC-PR':>8}{'AUC-ROC':>9}{'Brier':>8}{'rappel':>8}{'précis.':>9}{'F1':>7}")
    for name, m in results.items():
        print(
            f"{name:<34}{m['auc_pr']:>8.3f}{m['auc_roc']:>9.3f}{m['brier']:>8.3f}"
            f"{m['recall']:>8.2f}{m['precision']:>9.2f}{m['f1']:>7.2f}"
        )

    # Le gagnant est choisi entre RF et XGBoost sur l'AUC-PR de validation
    winner = max(("Random Forest", "XGBoost"), key=lambda n: results[n]["auc_pr"])
    print(f"\nGagnant : {winner}")

    joblib.dump(models[winner], BEST_MODEL_PATH)
    report = {
        "winner": winner,
        "selection_metric": "auc_pr (validation)",
        "decision_threshold": DECISION_THRESHOLD,
        "best_params": {"Random Forest": rf_params, "XGBoost": xgb_params},
        "validation_metrics": results,
    }
    BENCHMARK_RESULTS_PATH.write_text(json.dumps(report, indent=2, default=str, ensure_ascii=False))
    plot_curves(models, X_val, y_val)
    print(f"Modèle sauvegardé : {BEST_MODEL_PATH}")
    print(f"Résultats : {BENCHMARK_RESULTS_PATH}")
    print(f"Courbes : {BENCHMARK_PLOT_PATH}")


if __name__ == "__main__":
    main()

    