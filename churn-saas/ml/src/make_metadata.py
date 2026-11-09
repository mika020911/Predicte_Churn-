"""Écrit models/metadata.json : la « carte d'identité » du modèle gagnant.

À lancer après benchmark.py et calibrate.py. predict.py s'en sert pour vérifier
qu'il charge le bon modèle avec les bonnes colonnes.
"""
import json
from datetime import datetime, timezone

import sklearn
import xgboost

from config import (
    BENCHMARK_RESULTS_PATH, CALIBRATION_RESULTS_PATH, DECISION_THRESHOLD,
    FEATURE_COLUMNS, METADATA_PATH,
)


def main():
    benchmark = json.loads(BENCHMARK_RESULTS_PATH.read_text())
    calibration = json.loads(CALIBRATION_RESULTS_PATH.read_text())
    winner = benchmark["winner"]
    trained_at = datetime.now(timezone.utc)

    metadata = {
        "model_name": winner,
        "model_version": f"{winner.lower().replace(' ', '-')}-{trained_at:%Y%m%d}",
        "trained_at": trained_at.isoformat(timespec="seconds"),
        "feature_columns": FEATURE_COLUMNS,
        "best_params": benchmark["best_params"][winner],
        "validation_metrics": benchmark["validation_metrics"][winner],
        "test_metrics": calibration["avant calibration"],
        "calibration_applied": False,
        "calibration_note": "Le modèle brut est déjà bien calibré (voir calibration_results.json).",
        "decision_threshold_for_metrics": DECISION_THRESHOLD,
        "library_versions": {"scikit-learn": sklearn.__version__, "xgboost": xgboost.__version__},
    }
    METADATA_PATH.write_text(json.dumps(metadata, indent=2, ensure_ascii=False))
    print(f"Modèle : {metadata['model_version']}")
    print(f"Écrit : {METADATA_PATH}")


if __name__ == "__main__":
    main()