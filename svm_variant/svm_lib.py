"""Shared code for the SVM variant: split mapping, preprocessing, HOG feature transformer and the single-image prediction helper.

Everything is relative to the project root (the folder that contains `archive/` and `outputs/`), so the project can be moved.
The split is the cluster-disjoint partition produced earlier for this dataset (outputs/deduplicated_experiment/split_manifest.csv); only the
one-representative-per-cluster images are used, exactly like the research project's downstream classifier.
"""
from __future__ import annotations

import csv
import hashlib
from pathlib import Path

import numpy as np
from PIL import Image
from sklearn.base import BaseEstimator, TransformerMixin
from skimage.feature import hog

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "archive"
MANIFEST = ROOT / "outputs" / "deduplicated_experiment" / "split_manifest.csv"
SPLIT_CONFIG = ROOT / "outputs" / "deduplicated_experiment" / "split_config.json"
OUT = ROOT / "outputs" / "svm_variant"
CLASSES = ["glioma", "meningioma", "notumor", "pituitary"]          # same order as the manifest's class_idx
CLASS_LABELS = {"glioma": "Glioma", "meningioma": "Meningioma", "notumor": "No tumour", "pituitary": "Pituitary tumour"}
SEED = 42

# HOG variants compared during model selection (all on grayscale images resized to size x size)
HOG_VARIANTS = {
    "hog128_cell16": dict(size=128, orientations=9, pixels_per_cell=(16, 16), cells_per_block=(2, 2), block_norm="L2-Hys"),
    "hog128_cell8": dict(size=128, orientations=9, pixels_per_cell=(8, 8), cells_per_block=(2, 2), block_norm="L2-Hys"),
    "hog64_cell8": dict(size=64, orientations=9, pixels_per_cell=(8, 8), cells_per_block=(2, 2), block_norm="L2-Hys"),
}


def load_partition(partition: str):
    """Return (relative paths, labels) of the representative images of one partition: 'train', 'val' or 'test'."""
    assert partition in ("train", "val", "test")
    paths, labels = [], []
    with open(MANIFEST) as f:
        for r in csv.DictReader(f):
            if r["partition"] == partition and r["is_representative"] == "True":
                paths.append(r["source_path"])
                labels.append(int(r["class_idx"]))
                assert CLASSES[int(r["class_idx"])] == r["class_name"]
    return paths, np.array(labels)


def file_list_sha256(paths) -> str:
    return hashlib.sha256("\n".join(sorted(paths)).encode()).hexdigest()


def preprocess(img: Image.Image, size: int) -> np.ndarray:
    """Grayscale, bilinear resize to size x size, scale to [0, 1]. Identical for training, evaluation and the web application."""
    g = img.convert("L").resize((size, size), Image.BILINEAR)
    return np.asarray(g, dtype=np.float32) / 255.0


def load_images(paths, size: int) -> np.ndarray:
    return np.stack([preprocess(Image.open(ARCHIVE / p), size) for p in paths])


class HOGTransformer(BaseEstimator, TransformerMixin):
    """Histogram of Oriented Gradients of each (already preprocessed) grayscale image. Stateless: nothing is learned from the data."""

    def __init__(self, orientations=9, pixels_per_cell=(16, 16), cells_per_block=(2, 2), block_norm="L2-Hys"):
        self.orientations = orientations
        self.pixels_per_cell = pixels_per_cell
        self.cells_per_block = cells_per_block
        self.block_norm = block_norm

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return np.stack([hog(im, orientations=self.orientations, pixels_per_cell=self.pixels_per_cell, cells_per_block=self.cells_per_block,
                             block_norm=self.block_norm, feature_vector=True) for im in X]).astype(np.float32)


def hog_from_variant(name: str) -> HOGTransformer:
    v = {k: val for k, val in HOG_VARIANTS[name].items() if k != "size"}
    return HOGTransformer(**v)


def load_model(path: Path | None = None):
    """Load the saved bundle: {'pipeline': sklearn Pipeline(StandardScaler, SVC) on HOG features, 'config': {...}, 'classes': [...]}."""
    import joblib
    return joblib.load(path or OUT / "model" / "svm_model.joblib")


def predict_image(bundle, img: Image.Image):
    """Real SVM inference for one PIL image. Returns (class_index, decision_scores[4])."""
    cfg = bundle["config"]
    x = preprocess(img, cfg["image_size"])[None]
    feats = hog_from_variant(cfg["hog_variant"]).transform(x)
    pipe = bundle["pipeline"]
    scores = pipe.decision_function(feats)[0]
    return int(pipe.predict(feats)[0]), scores
