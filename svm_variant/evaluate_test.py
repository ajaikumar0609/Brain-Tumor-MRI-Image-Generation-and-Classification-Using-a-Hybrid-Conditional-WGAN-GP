#!/usr/bin/env python3
"""Evaluate the SELECTED SVM exactly once on the untouched TEST partition.

* Refuses to run again if outputs/svm_variant/test/test_evaluation.json already exists (the test set is looked at once); use --force only for a documented re-run.
* Reloads the saved model from disk (this is also the save/reload test), checks the test file list against the recorded split, predicts, and saves predictions and metrics.
* Verifies that the single-image path used by the web application (svm_lib.predict_image) gives the same labels as batch prediction.

    .venv/bin/python svm_variant/evaluate_test.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix, f1_score, precision_recall_fscore_support

sys.path.insert(0, str(Path(__file__).resolve().parent))
import svm_lib as L  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    out = L.OUT / "test"
    out.mkdir(parents=True, exist_ok=True)
    result_file = out / "test_evaluation.json"
    if result_file.exists() and not args.force:
        raise SystemExit("The test partition was already evaluated (test_evaluation.json exists). Refusing to evaluate again.")
    sel = json.load(open(L.OUT / "selection" / "selection.json"))          # selection must be finished before the test set is touched
    bundle = L.load_model()
    cfg = bundle["config"]
    assert cfg["test_partition_read"] is False and cfg["partitions_read_by_this_script"] == ["train", "val"]
    assert cfg["hog_variant"] == sel["selected"]["hog_variant"] and cfg["kernel"] == sel["selected"]["kernel"]
    te_p, yte = L.load_partition("test")
    split_cfg = json.load(open(L.SPLIT_CONFIG))
    assert len(te_p) == 492 and L.file_list_sha256(te_p) == split_cfg["partition_file_list_sha256"]["test"], "test list differs from the recorded split"
    tr_p, _ = L.load_partition("train"); va_p, _ = L.load_partition("val")
    assert not (set(te_p) & (set(tr_p) | set(va_p))), "test files overlap train/validation files"

    t0 = time.time()
    X = L.load_images(te_p, cfg["image_size"])
    t_load = time.time() - t0
    hog = L.hog_from_variant(cfg["hog_variant"])
    t0 = time.time(); F = hog.transform(X); t_hog = time.time() - t0
    pipe = bundle["pipeline"]
    t0 = time.time(); pred = pipe.predict(F); scores = pipe.decision_function(F); t_pred = time.time() - t0

    # consistency of the single-image (web application) path with batch prediction
    n_chk = 60
    single = [L.predict_image(bundle, Image.open(L.ARCHIVE / p))[0] for p in te_p[:n_chk]]
    assert single == pred[:n_chk].tolist(), "single-image prediction path disagrees with batch prediction"

    acc = accuracy_score(yte, pred)
    p, r, f1, sup = precision_recall_fscore_support(yte, pred, labels=range(4), zero_division=0)
    cm = confusion_matrix(yte, pred, labels=range(4))
    rng = np.random.default_rng(L.SEED)
    boot = [(accuracy_score(yte[i], pred[i]), f1_score(yte[i], pred[i], average="macro")) for i in (rng.integers(0, len(yte), len(yte)) for _ in range(2000))]
    boot = np.array(boot)
    # derived one-vs-rest sensitivity / specificity and tumour-vs-no-tumour
    sens, spec = [], []
    for i in range(4):
        tp, fn = ((yte == i) & (pred == i)).sum(), ((yte == i) & (pred != i)).sum()
        fp, tn = ((yte != i) & (pred == i)).sum(), ((yte != i) & (pred != i)).sum()
        sens.append(float(tp / (tp + fn))); spec.append(float(tn / (tn + fp)))
    tum_t, tum_p = yte != 2, pred != 2
    res = {
        "partition": "test (untouched until this run)", "n_test": int(len(yte)), "test_file_list_sha256": L.file_list_sha256(te_p), "class_counts": np.bincount(yte, minlength=4).tolist(),
        "model_file": "outputs/svm_variant/model/svm_model.joblib", "model_file_sha256": hashlib.sha256((L.OUT / "model" / "svm_model.joblib").read_bytes()).hexdigest(),
        "model": {"hog_variant": cfg["hog_variant"], "kernel": cfg["kernel"], "svc_params": cfg["svc_params"], "n_features": cfg["n_features"], "image_size": cfg["image_size"]},
        "accuracy": float(acc), "balanced_accuracy": float(balanced_accuracy_score(yte, pred)),
        "macro_precision": float(p.mean()), "macro_recall": float(r.mean()), "macro_f1": float(f1.mean()), "weighted_f1": float(f1_score(yte, pred, average="weighted")),
        "per_class": {c: {"precision": float(p[i]), "recall": float(r[i]), "f1": float(f1[i]), "support": int(sup[i]), "sensitivity_ovr": sens[i], "specificity_ovr": spec[i]} for i, c in enumerate(L.CLASSES)},
        "confusion_matrix": {"labels": L.CLASSES, "rows": "true class", "cols": "predicted class", "counts": cm.tolist()},
        "tumour_vs_notumor": {"sensitivity": float((tum_t & tum_p).sum() / tum_t.sum()), "specificity": float((~tum_t & ~tum_p).sum() / (~tum_t).sum()), "n_tumour": int(tum_t.sum()), "n_notumor": int((~tum_t).sum())},
        "bootstrap_95ci_2000_resamples_of_test_predictions": {"accuracy": [float(np.percentile(boot[:, 0], 2.5)), float(np.percentile(boot[:, 0], 97.5))], "macro_f1": [float(np.percentile(boot[:, 1], 2.5)), float(np.percentile(boot[:, 1], 97.5))], "seed": L.SEED},
        "majority_class_baseline_accuracy": float(np.bincount(yte).max() / len(yte)),
        "runtime_seconds": {"image_loading_test": round(t_load, 2), "hog_extraction_test": round(t_hog, 2), "scaler_plus_svm_prediction_test": round(t_pred, 2), "per_image_total_ms": round(1000 * (t_load + t_hog + t_pred) / len(yte), 2), "fit_final_model": cfg["fit_seconds_final_model"]},
        "decision_score_argmax_agrees_with_predicted_label_fraction": float((scores.argmax(1) == pred).mean()),
        "checks": {"saved_model_reloaded_from_disk": True, "single_image_path_matches_batch_first_n": n_chk, "test_files_disjoint_from_train_and_val": True, "model_selected_before_test_was_read": True},
    }
    json.dump(res, open(result_file, "w"), indent=2)
    json.dump({"files": te_p, "y_true": yte.tolist(), "y_pred": pred.tolist(), "decision_scores": np.round(scores, 5).tolist(), "classes": L.CLASSES}, open(out / "test_predictions.json", "w"))
    np.savetxt(out / "confusion_matrix.csv", cm, fmt="%d", delimiter=",", header=",".join(L.CLASSES), comments="")
    print(f"TEST: accuracy {acc:.4f} | macro-P {p.mean():.4f} macro-R {r.mean():.4f} macro-F1 {f1.mean():.4f} | 95% CI acc {res['bootstrap_95ci_2000_resamples_of_test_predictions']['accuracy']}")
    print("confusion matrix (rows = true):\n", cm)


if __name__ == "__main__":
    main()
