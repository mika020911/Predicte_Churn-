import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score

from config import (DATE_COLUMN, FEATURE_COLUMNS, MODEL_PATH, RAW_DATA_PATH,
                    RF_PARAMS, TARGET_COLUMN)

df = pd.read_csv(RAW_DATA_PATH, parse_dates=[DATE_COLUMN]).sort_values(DATE_COLUMN)

# Split temporel : entraînement sur le passé, test sur les dernières dates
cut = int(len(df) * 0.8)
train, test = df.iloc[:cut], df.iloc[cut:]

model = RandomForestClassifier(**RF_PARAMS)
model.fit(train[FEATURE_COLUMNS], train[TARGET_COLUMN])

proba = model.predict_proba(test[FEATURE_COLUMNS])[:, 1]
y_test = test[TARGET_COLUMN]
print("AUC :", round(roc_auc_score(y_test, proba), 3))
print("Proba moyenne prédite :", round(proba.mean(), 3),
      "| taux de départ réel :", round(y_test.mean(), 3))
print(classification_report(y_test, (proba >= 0.4).astype(int)))

joblib.dump(model, MODEL_PATH)
print("Modèle sauvegardé :", MODEL_PATH)