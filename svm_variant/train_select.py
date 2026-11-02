#!/usr/bin/env python3
"""Train and SELECT the SVM. Uses only the TRAIN and VALIDATION partitions (the test partition is never loaded here: see TEST_NEVER_LOADED).

For each HOG variant and each kernel (linear, RBF):
  1. grid search with 5-fold stratified cross-validation on the TRAIN partition only (StandardScaler is inside the pipeline, so it is fitted on the training
     folds only; HOG is a fixed, stateless transform),
  2. the best setting by CV macro-F1 is refit on the whole train partition and scored once on the VALIDATION partition.
The candidate with the best validation macro-F1 (ties within 0.002 broken by CV macro-F1) is saved as the final model. The final model is fitted on the
training partition only (the validation partition is used for selection, not for fitting).

    .venv/bin/python svm_variant/train_select.py
"""
from __future__ import annotations

import json
import platform
import sys
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import scipy
import skimage
import sklearn
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

sys.path.insert(0, str(Path(__file__).resolve().parent))
import svm_lib as L  # noqa: E402

PARTITIONS_USED = ("train", "val")
TEST_NEVER_LOADED = True          # this script has no code path that reads the test partition


def main():
    np.random.seed(L.SEED)
    out = L.OUT
    (out / "selection").mkdir(parents=True, exist_ok=True)
    (out / "model").mkdir(parents=True, exist_ok=True)
    tr_p, ytr = L.load_partition("train")
    va_p, yva = L.load_partition("val")
    assert len(tr_p) == 2311 and len(va_p) == 492
    assert not (set(tr_p) & set(va_p))
    split_cfg = json.load(open(L.SPLIT_CONFIG))
    assert L.file_list_sha256(tr_p) == split_cfg["partition_file_list_sha256"]["train"], "train list differs from the recorded split"
    assert L.file_list_sha256(va_p) == split_cfg["partition_file_list_sha256"]["val"], "validation list differs from the recorded split"
    print(f"train {len(tr_p)} (class counts {np.bincount(ytr).tolist()})  |  validation {len(va_p)} ({np.bincount(yva).tolist()})", flush=True)
    base = {"majority_class_validation_accuracy": float(np.bincount(yva).max() / len(yva))}

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=L.SEED)
    candidates, best_by_key = [], {}
    for vname, vcfg in L.HOG_VARIANTS.items():
        t0 = time.time()
        Xtr_img, Xva_img = L.load_images(tr_p, vcfg["size"]), L.load_images(va_p, vcfg["size"])
        hog = L.hog_from_variant(vname)
        Ftr, Fva = hog.transform(Xtr_img), hog.transform(Xva_img)
        nf = Ftr.shape[1]
        print(f"\n[{vname}] images {vcfg['size']}px, {nf} HOG features; extracted in {time.time() - t0:.1f}s", flush=True)
        grids = {
            "linear": {"svc__kernel": ["linear"], "svc__C": [1e-5, 1e-4, 1e-3, 1e-2, 1e-1, 1.0], "svc__class_weight": [None, "balanced"]},
            "rbf": {"svc__kernel": ["rbf"], "svc__C": [1.0, 10.0, 100.0], "svc__gamma": [0.1 / nf, 1.0 / nf, 3.0 / nf], "svc__class_weight": [None, "balanced"]},
        }
        for kname, grid in grids.items():
            pipe = Pipeline([("scaler", StandardScaler()), ("svc", SVC(random_state=L.SEED, cache_size=1000))])
            gs = GridSearchCV(pipe, grid, scoring={"f1_macro": "f1_macro", "accuracy": "accuracy"}, refit="f1_macro", cv=cv, n_jobs=-1, return_train_score=False)
            t1 = time.time()
            gs.fit(Ftr, ytr)
            grid_s = time.time() - t1
            res = pd.DataFrame(gs.cv_results_)
            res = res.drop(columns=[c for c in res.columns if c.startswith("split")])
            res.to_csv(out / "selection" / f"cv_results_{vname}_{kname}.csv", index=False)
            best = gs.best_estimator_
            pva = best.predict(Fva)
            cand = {"hog_variant": vname, "kernel": kname, "n_features": int(nf), "best_params": {k.replace("svc__", ""): (None if v is None else (float(v) if isinstance(v, (int, float, np.floating)) else v)) for k, v in gs.best_params_.items()},
                    "cv_macro_f1": float(gs.best_score_), "cv_accuracy": float(res.loc[gs.best_index_, "mean_test_accuracy"]), "cv_macro_f1_std": float(res.loc[gs.best_index_, "std_test_f1_macro"]),
                    "val_macro_f1": float(f1_score(yva, pva, average="macro")), "val_accuracy": float(accuracy_score(yva, pva)),
                    "grid_search_seconds": round(grid_s, 1), "n_fits": int(len(res) * cv.get_n_splits())}
            candidates.append(cand)
            best_by_key[(vname, kname)] = best
            print(f"  {kname:6s} best {cand['best_params']}  CV macro-F1 {cand['cv_macro_f1']:.3f} | validation macro-F1 {cand['val_macro_f1']:.3f} acc {cand['val_accuracy']:.3f}  ({grid_s:.0f}s)", flush=True)

    # ---- selection: validation macro-F1, ties (within 0.002) broken by CV macro-F1
    top = max(c["val_macro_f1"] for c in candidates)
    tied = [c for c in candidates if top - c["val_macro_f1"] <= 0.002]
    final = max(tied, key=lambda c: c["cv_macro_f1"])
    key = (final["hog_variant"], final["kernel"])
    best = best_by_key[key]
    vcfg = L.HOG_VARIANTS[final["hog_variant"]]
    hog = L.hog_from_variant(final["hog_variant"])
    Fva = hog.transform(L.load_images(va_p, vcfg["size"]))
    pva = best.predict(Fva)
    # fit time / prediction time of the final configuration measured on a clean refit of the training partition
    Ftr = hog.transform(L.load_images(tr_p, vcfg["size"]))
    t0 = time.time()
    refit = Pipeline([("scaler", StandardScaler()), ("svc", SVC(random_state=L.SEED, cache_size=1000, **final["best_params"]))]).fit(Ftr, ytr)
    fit_s = time.time() - t0
    assert np.array_equal(refit.predict(Fva), pva), "clean refit does not reproduce the grid-search estimator"
    n_sv = int(refit.named_steps["svc"].n_support_.sum())

    config = {
        "task": "4-class brain tumour MRI classification (glioma, meningioma, notumor, pituitary)",
        "classes": L.CLASSES, "label_mapping": {c: i for i, c in enumerate(L.CLASSES)},
        "image_size": vcfg["size"], "hog_variant": final["hog_variant"], "hog_params": {k: (list(v) if isinstance(v, tuple) else v) for k, v in vcfg.items() if k != "size"},
        "n_features": final["n_features"], "kernel": final["kernel"], "svc_params": final["best_params"],
        "scaler": "StandardScaler fitted on the training partition only", "fitted_on": "train partition only (2,311 representative images)",
        "selected_by": "validation macro-F1 (ties within 0.002 broken by 5-fold CV macro-F1 on the training partition)",
        "seed": L.SEED, "cv": "StratifiedKFold(n_splits=5, shuffle=True, random_state=42) on the training partition only",
        "train_file_list_sha256": L.file_list_sha256(tr_p), "validation_file_list_sha256": L.file_list_sha256(va_p),
        "n_support_vectors": n_sv, "fit_seconds_final_model": round(fit_s, 2),
        "packages": {"python": platform.python_version(), "scikit-learn": sklearn.__version__, "scikit-image": skimage.__version__, "numpy": np.__version__, "scipy": scipy.__version__, "joblib": joblib.__version__, "pandas": pd.__version__},
        "partitions_read_by_this_script": list(PARTITIONS_USED), "test_partition_read": not TEST_NEVER_LOADED,
    }
    joblib.dump({"pipeline": refit, "config": config, "classes": L.CLASSES}, out / "model" / "svm_model.joblib")
    json.dump(config, open(out / "model" / "model_config.json", "w"), indent=2)
    json.dump({"candidates": candidates, "selected": final, "baselines": base, "selection_rule": config["selected_by"]}, open(out / "selection" / "selection.json", "w"), indent=2)
    pd.DataFrame(candidates).to_csv(out / "selection" / "candidates.csv", index=False)
    json.dump({"y_true": yva.tolist(), "y_pred": pva.tolist(), "files": va_p}, open(out / "selection" / "validation_predictions.json", "w"))
    print(f"\nSELECTED: {final['hog_variant']} + {final['kernel']} {final['best_params']}  (validation macro-F1 {final['val_macro_f1']:.3f}, CV {final['cv_macro_f1']:.3f})")
    print(f"final model saved; {n_sv} support vectors; fit {fit_s:.1f}s; test partition NOT read.")


if __name__ == "__main__":
    main()
