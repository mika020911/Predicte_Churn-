import joblib
import pandas as pd
import shap

from config import FEATURE_COLUMNS, MODEL_PATH, RAW_DATA_PATH

model = joblib.load(MODEL_PATH)
X = pd.read_csv(RAW_DATA_PATH)[FEATURE_COLUMNS].head(5)

sv = shap.TreeExplainer(model).shap_values(X)
# La forme de sortie dépend de la version de shap : on isole la classe « départ »
sv1 = sv[1] if isinstance(sv, list) else (sv[:, :, 1] if sv.ndim == 3 else sv)

for i in range(len(X)):
    top = sorted(zip(FEATURE_COLUMNS, sv1[i]), key=lambda t: abs(t[1]), reverse=True)[:3]
    print(f"Client {i} : {[(n, round(float(v), 3)) for n, v in top]}")