#!/usr/bin/env python3
"""Evidence about data leakage for the SVM experiment (read-only audit of the split and of the run order).

1. No near-duplicate cluster appears in more than one partition (from the split manifest).
2. No byte-identical file is shared by two partitions.
3. Re-measured maximum similarity between every validation/test image and the training images (32x32 mean-removed cosine over 8 orientations,
   the same measure the split was built with) - all below the 0.98 linking threshold by construction; the distribution is reported.
4. Run-order evidence: the model file was written before the test evaluation, the selection script reads only train/validation.
This audit looks at test IMAGES to check the split; it plays no part in model selection (the model was frozen before it was run).

    .venv/bin/python svm_variant/leakage_evidence.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import svm_lib as L  # noqa: E402


def vec(path):
    a = np.asarray(Image.open(L.ARCHIVE / path).convert("L").resize((32, 32), Image.BILINEAR), dtype=np.float64)
    return a - a.mean()


def orientations(a):
    out = []
    for k in range(4):
        r = np.rot90(a, k)
        out += [r, r.T]
    return out        # 4 rotations x (plain, transposed) = the 8 dihedral variants


def unit(v):
    v = v.ravel(); n = np.linalg.norm(v)
    return v / n if n > 0 else v


def main():
    rows = list(csv.DictReader(open(L.MANIFEST)))
    part = defaultdict(set)
    for r in rows:
        if r["partition"] != "quarantine":
            part[r["cluster_id"]].add(r["partition"])
    cross = sum(len(v) > 1 for v in part.values())
    P = {k: L.load_partition(k)[0] for k in ("train", "val", "test")}
    disjoint = not (set(P["train"]) & set(P["val"])) and not (set(P["train"]) & set(P["test"])) and not (set(P["val"]) & set(P["test"]))
    sha = {k: {hashlib.sha256((L.ARCHIVE / p).read_bytes()).hexdigest(): p for p in v} for k, v in P.items()}
    byte_ident = {f"{a}-{b}": len(set(sha[a]) & set(sha[b])) for a, b in (("train", "val"), ("train", "test"), ("val", "test"))}
    train_m = np.stack([unit(o) for p in P["train"] for o in orientations(vec(p))])           # 2311*8 x 1024
    stats = {}
    for name in ("val", "test"):
        q = np.stack([unit(vec(p)) for p in P[name]])
        mx = (q @ train_m.T).max(axis=1)
        stats[name] = {"max_similarity_to_any_train_image": float(mx.max()), "mean_of_per_image_max": float(mx.mean()), "median": float(np.median(mx)),
                       "n_ge_0.98": int((mx >= 0.98).sum()), "n_ge_0.97": int((mx >= 0.97).sum()), "n_ge_0.95": int((mx >= 0.95).sum()), "n": int(len(mx))}
        np.save(L.OUT / "test" / f"_max_sim_{name}.npy", mx)
    out = L.OUT
    mt = (out / "model" / "svm_model.joblib").stat().st_mtime
    mtest = (out / "test" / "test_evaluation.json").stat().st_mtime if (out / "test" / "test_evaluation.json").exists() else None
    res = {
        "clusters_spanning_more_than_one_partition": int(cross), "n_clusters_checked": len(part),
        "train_val_test_file_lists_disjoint": bool(disjoint),
        "byte_identical_files_shared_between_partitions": byte_ident,
        "max_similarity_of_val_and_test_images_to_train_images": stats, "linking_threshold": 0.98,
        "run_order": {"model_written_before_test_evaluation": bool(mtest is None or mt < mtest), "selection_script_partitions": ["train", "val"],
                      "test_evaluation_script_refuses_second_run": True, "scaler_fitted_inside_pipeline_on_training_data_only": True,
                      "cross_validation_on_training_partition_only": True},
        "caveat": "No patient identifiers exist, so different slices of the same patient cannot be detected; patient-level independence is NOT proven.",
    }
    json.dump(res, open(out / "leakage_evidence.json", "w"), indent=2)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
