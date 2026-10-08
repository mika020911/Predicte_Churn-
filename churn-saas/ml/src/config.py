from pathlib import Path

ML_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ML_DIR / "data"
MODELS_DIR = ML_DIR / "models"
REPORTS_DIR = ML_DIR / "reports"

RAW_DATA_PATH = DATA_DIR / "raw" / "churn_data.csv"
MODEL_PATH = MODELS_DIR / "random_forest_churn.pkl"
CALIBRATED_MODEL_PATH = MODELS_DIR / "random_forest_calibrated.pkl"
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