"""Paths and limits for the SVM web application backend. Everything is relative to the project root (override with env vars)."""
import os
from pathlib import Path

PROJECT_ROOT = Path(os.environ.get("SVM_PROJECT_ROOT", Path(__file__).resolve().parents[3])).resolve()
SVM_OUT = PROJECT_ROOT / "outputs" / "svm_variant"
MODEL_PATH = Path(os.environ.get("SVM_MODEL_PATH", SVM_OUT / "model" / "svm_model.joblib"))
TEST_EVAL = SVM_OUT / "test" / "test_evaluation.json"
SELECTION = SVM_OUT / "selection" / "selection.json"
MODEL_CONFIG = SVM_OUT / "model" / "model_config.json"
LEAKAGE = SVM_OUT / "leakage_evidence.json"
FIGURES = SVM_OUT / "figures"

CLASSES = ["glioma", "meningioma", "notumor", "pituitary"]
CLASS_LABELS = {"glioma": "Glioma", "meningioma": "Meningioma", "notumor": "No tumour", "pituitary": "Pituitary tumour"}

MAX_UPLOAD_BYTES = int(os.environ.get("SVM_MAX_UPLOAD_MB", "10")) * 1024 * 1024
MAX_IMAGE_SIDE = 8192
MIN_IMAGE_SIDE = 32
ALLOWED_ORIGINS = [o.strip() for o in os.environ.get("SVM_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if o.strip()]
