"""Backend tests for the SVM web app. Run from the project root:  .venv/bin/python -m pytest svm_variant/webapp/backend/tests -q
These use the real saved model; their outputs are plumbing checks, not scientific results."""
import io
import json
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from svm_variant import svm_lib as L
from svm_variant.webapp.backend import config
from svm_variant.webapp.backend.main import app

client = TestClient(app)
TEST = json.load(open(config.TEST_EVAL))


def _png(size=(128, 128), mode="L", fmt="PNG"):
    buf = io.BytesIO(); Image.new(mode, size, 90).save(buf, fmt); return buf.getvalue()


def test_health():
    r = client.get("/api/health"); assert r.status_code == 200 and r.json()["status"] == "ok"


def test_status_real_model_matches_evaluated_file():
    d = client.get("/api/models/status").json()
    c = d["classifier"]
    assert c["available"] and c["matches_evaluated_model"] and c["model_sha256"] == TEST["model_file_sha256"]
    assert c["kernel"] == TEST["model"]["kernel"] and d["generator"]["available"] is False


def test_metrics_equal_saved_files():
    d = client.get("/api/metrics").json()
    assert d["accuracy"] == TEST["accuracy"] and d["macro_f1"] == TEST["macro_f1"] and d["n_test"] == 492
    assert d["confusion_matrix"]["counts"] == TEST["confusion_matrix"]["counts"]
    pred = json.load(open(config.SVM_OUT / "test" / "test_predictions.json"))
    yt, yp = np.array(pred["y_true"]), np.array(pred["y_pred"])
    assert abs((yt == yp).mean() - d["accuracy"]) < 1e-12                    # metrics recomputed from the saved predictions
    cm = np.zeros((4, 4), int)
    for a, b in zip(yt, yp): cm[a, b] += 1
    assert cm.tolist() == d["confusion_matrix"]["counts"]


def test_classify_matches_the_library_prediction():
    bundle = L.load_model(config.MODEL_PATH)
    for cls in config.CLASSES:
        f = sorted((config.PROJECT_ROOT / "archive" / "Testing" / cls).glob("*.jpg"))[0]
        r = client.post("/api/classify", files={"file": (f.name, f.read_bytes(), "image/jpeg")})
        assert r.status_code == 200, r.text
        d = r.json()
        idx, scores = L.predict_image(bundle, Image.open(f))
        assert d["predicted_class"] == config.CLASSES[idx]
        assert np.allclose([s["score"] for s in d["decision_scores"]], scores)
        assert "not a medical diagnosis" in d["disclaimer"].lower() and d["caveats"]


def test_classify_png_and_jpeg_uploads():
    for fmt, mime in (("PNG", "image/png"), ("JPEG", "image/jpeg")):
        r = client.post("/api/classify", files={"file": (f"x.{fmt.lower()}", _png(fmt=fmt), mime)})
        assert r.status_code == 200 and r.json()["predicted_class"] in config.CLASSES


def test_test_partition_predictions_cover_every_class_label_consistently():
    pred = json.load(open(config.SVM_OUT / "test" / "test_predictions.json"))
    paths, y = L.load_partition("test")
    assert pred["files"] == paths and pred["y_true"] == y.tolist() and set(pred["y_pred"]) <= {0, 1, 2, 3}


def test_classify_error_handling():
    assert client.post("/api/classify", files={"file": ("a.txt", b"hello", "text/plain")}).json()["error"]["code"] == "not_an_image"
    assert client.post("/api/classify", files={"file": ("a.png", b"", "image/png")}).json()["error"]["code"] == "empty_file"
    gif = io.BytesIO(); Image.new("L", (64, 64)).save(gif, "GIF")
    assert client.post("/api/classify", files={"file": ("a.gif", gif.getvalue(), "image/gif")}).json()["error"]["code"] == "unsupported_type"
    assert client.post("/api/classify", files={"file": ("tiny.png", _png((8, 8)), "image/png")}).json()["error"]["code"] == "bad_dimensions"
    big = b"\x89PNG" + b"0" * (config.MAX_UPLOAD_BYTES + 10)
    assert client.post("/api/classify", files={"file": ("big.png", big, "image/png")}).status_code == 413
    assert client.post("/api/classify").status_code == 422


def test_no_generator_or_other_classifier_endpoints():
    assert client.post("/api/generate", json={"class": "glioma", "count": 4}).status_code in (404, 405)
    assert not any("generat" in r.path for r in app.routes)


def test_unavailable_or_mismatched_model_is_reported_not_substituted(monkeypatch, tmp_path):
    from svm_variant.webapp.backend import ml
    real = config.MODEL_PATH.read_bytes()
    svc = ml.SVMService(); monkeypatch.setattr(config, "MODEL_PATH", tmp_path / "missing.joblib")
    assert svc.ensure() is False and "not found" in svc.error
    other = tmp_path / "other.joblib"; other.write_bytes(real + b"tampered"); monkeypatch.setattr(config, "MODEL_PATH", other)
    svc2 = ml.SVMService(); assert svc2.ensure() is False and "SHA-256 mismatch" in svc2.error


def test_gallery_registry_only():
    d = client.get("/api/gallery").json()["items"]
    assert d and client.get(d[0]["url"]).headers["content-type"] == "image/png"
    for bad in ("../../etc/passwd", "..%2f..%2fetc%2fpasswd", "nonexistent"):
        assert client.get(f"/api/gallery/image/{bad}").status_code == 404


def test_cors_restricted_to_vite_origin():
    assert client.get("/api/health", headers={"Origin": "http://localhost:5173"}).headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert "access-control-allow-origin" not in client.get("/api/health", headers={"Origin": "http://evil.example"}).headers


def test_experiment_lists_limitations_and_leakage_evidence():
    d = client.get("/api/experiment").json()
    text = " ".join(d["limitations"]).lower()
    for must in ("patient-level", "492", "out-of-distribution", "not calibrated"):
        assert must in text
    assert d["leakage_evidence"]["clusters_spanning_more_than_one_partition"] == 0


def test_no_hardcoded_user_paths():
    for p in Path(__file__).parents[1].glob("*.py"):
        assert "/Users/" not in p.read_text(), p
