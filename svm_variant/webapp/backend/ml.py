"""Loads the saved SVM bundle and runs REAL inference. The file must be exactly the model that was evaluated on the test partition (SHA-256 recorded by
evaluate_test.py); otherwise the classifier is reported as unavailable. Nothing is substituted or simulated."""
import hashlib
import json
import threading

from PIL import Image

from svm_variant import svm_lib as L
from . import config


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class SVMService:
    name = "HOG + StandardScaler + SVM (scikit-learn)"

    def __init__(self):
        self.lock = threading.Lock()
        self.loaded = False
        self.error = None
        self.bundle = None
        self.model_sha256 = None
        self.evaluated_sha256 = None

    def ensure(self) -> bool:
        with self.lock:
            if not self.loaded and self.error is None:
                try:
                    self._load()
                    self.loaded = True
                except Exception as e:  # reported verbatim; never replaced by another model
                    self.error = f"{type(e).__name__}: {e}"
            return self.loaded

    def _load(self):
        if not config.MODEL_PATH.exists():
            raise FileNotFoundError("SVM model file not found: run svm_variant/train_select.py and evaluate_test.py first")
        if not config.TEST_EVAL.exists():
            raise FileNotFoundError("the model has not been evaluated on the test partition yet (outputs/svm_variant/test/test_evaluation.json missing)")
        self.evaluated_sha256 = json.load(open(config.TEST_EVAL)).get("model_file_sha256")
        self.model_sha256 = sha256_file(config.MODEL_PATH)
        if self.model_sha256 != self.evaluated_sha256:
            raise ValueError("the model file differs from the model that was evaluated on the test partition (SHA-256 mismatch)")
        bundle = L.load_model(config.MODEL_PATH)          # local, trusted file: joblib pickle
        if bundle["classes"] != config.CLASSES:
            raise ValueError("class order in the model differs from the application's class order")
        self.bundle = bundle

    @property
    def cfg(self):
        return self.bundle["config"]

    def predict(self, img: Image.Image):
        with self.lock:
            idx, scores = L.predict_image(self.bundle, img)
        return idx, [float(s) for s in scores]


svm = SVMService()
