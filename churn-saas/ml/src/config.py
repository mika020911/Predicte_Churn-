from pathlib import Path

ML_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ML_DIR / "data"
MODELS_DIR = ML_DIR / "models"
REPORTS_DIR = ML_DIR / "reports"

RAW_DATA_PATH = DATA_DIR / "raw" / "churn_data.csv"
MODEL_PATH = MODELS_DIR / "random_forest_churn.pkl"

CALIBRATION_RESULTS_PATH = REPORTS_DIR / "calibration_results.json"
CALIBRATION_PLOT_PATH = REPORTS_DIR / "calibration_curve.png"

SHAP_PLOT_PATH = REPORTS_DIR / "shap_summary.png"
N_REASONS = 3  # nombre de raisons affichées par client

METADATA_PATH = MODELS_DIR / "metadata.json"

CALIBRATED_MODEL_PATH = MODELS_DIR / "calibrated_model.pkl"
#PROCESSOR_PATH = MODELS_DIR / "preprocessor.pkl"

FEATURE_COLUMNS = [
    "tenure_months",
    "contract_type",
    "mrr_change_pct",
    "support_tickets_30d",
    "recency_days",
    "frequency_trend_30d",
    "engagement_breadth",
    "payment_failures_90d",
]

TARGET_COLUMN = "churn"
DATE_COLUMN = "snapshot_date"

#seuil de risque metier
RISK_THRESHOLD_HIGH = 0.7
RISK_THRESHOLD_MEDIUM = 0.4

#Paramètres de génération de données
N_SAMPLES = 6000
CHURN_RATE = 0.18
RANDOM_STATE = 42

#Difficulté du jeu de données synthétique
SIGNAL_STRENGTH = 2.0
NOISE_STD = 1.5
NONLINEAR_STRENGTH = 3.0

# Découpage temporel des données (le reste = test)
TRAIN_RATIO = 0.70
VAL_RATIO = 0.15

# Benchmark (benchmark.py)
CV_FOLDS = 5                # nombre de parties pour la validation croisée
N_ITER_SEARCH = 20          # nombre de combinaisons d'hyperparamètres essayées par modèle
DECISION_THRESHOLD = 0.4    # seuil pour recall / précision / F1 (provisoire, juste pour comparer)
BENCHMARK_RESULTS_PATH = REPORTS_DIR / "benchmark_results.json"
BENCHMARK_PLOT_PATH = REPORTS_DIR / "benchmark_curves.png"
BEST_MODEL_PATH = MODELS_DIR / "best_model.pkl"

RF_PARAM_GRID = {
    "n_estimators": [200, 300, 500],
    "max_depth": [6, 8, 12, None],
    "min_samples_leaf": [3, 5, 10, 20],
    "min_samples_split": [2, 10, 20],
    "max_features": ["sqrt", 0.5],
}

XGB_PARAM_GRID = {
    "n_estimators": [100, 200, 400],
    "max_depth": [3, 4, 6],
    "learning_rate": [0.03, 0.05, 0.1],
    "subsample": [0.7, 0.85, 1.0],
    "colsample_bytree": [0.7, 0.85, 1.0],
    "min_child_weight": [1, 5, 10],
}

#Hyperparametre du modelsRF
ID_COLUMN = "customer_id"
RF_PARAMS = {
    "n_estimators": 200,
    "max_depth": 12,
    "min_samples_split": 10,
    "min_samples_leaf": 5,
#    "class_weight": "balanced",
    "random_state": RANDOM_STATE,
    "n_jobs": -1,
}
#Création automatique des dossiers
for d in [DATA_DIR, MODELS_DIR, REPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)