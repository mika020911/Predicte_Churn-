import sys
from pathlib import Path

# Permet aux tests d'importer config.py, predict.py, etc. depuis ml/src
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))