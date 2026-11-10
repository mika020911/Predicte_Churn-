"""Pont entre le backend et le module ML (dossier ml/src).

Le module ML a ses propres fichiers (config.py, predict.py...). On ajoute son dossier au
chemin Python, puis on importe le prédicteur seulement quand on en a besoin.
"""
import sys

from app.config import settings


def _ensure_ml_on_path() -> None:
    ml_src = str(settings.ml_src_dir)
    if ml_src not in sys.path:
        sys.path.insert(0, ml_src)


def get_predictor():
    """Renvoie le prédicteur unique (le modèle n'est chargé qu'une seule fois)."""
    _ensure_ml_on_path()
    from predict import get_predictor as _get_predictor
    return _get_predictor()


def feature_columns() -> list[str]:
    """Les 8 colonnes attendues par le modèle, dans le bon ordre."""
    _ensure_ml_on_path()
    from config import FEATURE_COLUMNS
    return list(FEATURE_COLUMNS)