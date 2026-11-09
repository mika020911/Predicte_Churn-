import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from config import FEATURE_COLUMNS, RANDOM_STATE, RAW_DATA_PATH, TARGET_COLUMN


def main():
    df = pd.read_csv(RAW_DATA_PATH)
    X, y = df[FEATURE_COLUMNS], df[TARGET_COLUMN]
    print(f"Lignes : {len(df)} | taux de churn : {y.mean():.2%}")

    models = {
        "Régression logistique": make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000)),
        "Random Forest": RandomForestClassifier(
            n_estimators=200, min_samples_leaf=5, random_state=RANDOM_STATE, n_jobs=-1
        ),
    }
    scores = {}
    for name, model in models.items():
        scores[name] = cross_val_score(model, X, y, cv=5, scoring="roc_auc").mean()
        print(f"  {name:<22} AUC-ROC (CV 5 plis) : {scores[name]:.3f}")

    lr = scores["Régression logistique"]
    print("OK : difficulté réaliste" if 0.80 <= lr <= 0.88 else "À ajuster : AUC LR hors de 0,80-0,88")

if __name__ == "__main__":
    main()