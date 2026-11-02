#!/usr/bin/env python3
"""Figures for the SVM report and slides, generated ONLY from the saved SVM outputs (selection CSV/JSON, test predictions, split manifest, dataset images).
Run after evaluate_test.py.   .venv/bin/python svm_variant/make_figures.py"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from PIL import Image
from skimage.feature import hog

sys.path.insert(0, str(Path(__file__).resolve().parent))
import svm_lib as L  # noqa: E402

FIG = L.OUT / "figures"
FIG.mkdir(parents=True, exist_ok=True)
C4 = ["#3d73b8", "#1f9e8f", "#c2651a", "#8a5fb8"]
NAVY, TEAL, AMBER, INK, MUTED = "#1f3a5f", "#2a9d8f", "#c98a1a", "#14213d", "#556070"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})
LAB = [L.CLASS_LABELS[c] for c in L.CLASSES]
sel = json.load(open(L.OUT / "selection" / "selection.json"))
test = json.load(open(L.OUT / "test" / "test_evaluation.json"))
pred = json.load(open(L.OUT / "test" / "test_predictions.json"))
cm = np.array(test["confusion_matrix"]["counts"])


def clean(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="y", color="#e3e8ee", lw=0.6); ax.set_axisbelow(True)


# 1. confusion matrices (counts and row-normalised)
fig, axs = plt.subplots(1, 2, figsize=(7.2, 3.4))
for ax, mat, title, fmt in ((axs[0], cm, "Counts", "{:d}"), (axs[1], cm / cm.sum(1, keepdims=True), "Row-normalised (recall)", "{:.2f}")):
    im = ax.imshow(mat, cmap="Blues", vmin=0, vmax=mat.max())
    ax.set_xticks(range(4)); ax.set_yticks(range(4)); ax.set_xticklabels(LAB, rotation=30, ha="right", fontsize=8); ax.set_yticklabels(LAB, fontsize=8)
    ax.set_xlabel("predicted"); ax.set_ylabel("true"); ax.set_title(title, fontsize=9.5)
    for i in range(4):
        for j in range(4):
            v = mat[i, j]; ax.text(j, i, fmt.format(int(v) if fmt == "{:d}" else v), ha="center", va="center", fontsize=9, color="white" if v > mat.max() * 0.55 else INK)
fig.suptitle(f"Test confusion matrix (n = {test['n_test']}): {test['model']['kernel'].upper()} SVM + {test['model']['hog_variant']}", fontsize=10)
fig.tight_layout(rect=(0, 0, 1, 0.94)); fig.savefig(FIG / "confusion_matrix_test.png", dpi=220, facecolor="white"); plt.close(fig)

# 2. per-class precision / recall / F1
fig, ax = plt.subplots(figsize=(6.6, 3.5))
w = 0.26
for k, (name, col) in enumerate((("precision", C4[0]), ("recall", C4[1]), ("f1", C4[2]))):
    vals = [test["per_class"][c][name] for c in L.CLASSES]
    ax.bar(np.arange(4) + (k - 1) * (w + 0.02), vals, w, color=col, label=name.upper() if name == "f1" else name.capitalize())
    for i, v in enumerate(vals): ax.text(i + (k - 1) * (w + 0.02), v + 0.012, f"{v:.2f}", ha="center", fontsize=7.5)
ax.set_xticks(range(4)); ax.set_xticklabels([f"{L.CLASS_LABELS[c]}\n(n={test['per_class'][c]['support']})" for c in L.CLASSES]); ax.set_ylim(0, 1.12); ax.set_ylabel("score")
ax.set_title("Per-class precision, recall and F1 on the test partition", fontsize=9.5); ax.legend(frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.2)); clean(ax)
fig.tight_layout(); fig.savefig(FIG / "per_class_metrics_test.png", dpi=220, facecolor="white"); plt.close(fig)

# 3. model selection: CV vs validation macro-F1 for the 6 candidates
cand = pd.DataFrame(sel["candidates"])
cand["label"] = cand["hog_variant"].str.replace("hog", "HOG ").str.replace("_cell", "\ncell ") + "\n" + cand["kernel"]
fig, ax = plt.subplots(figsize=(7.0, 3.4))
x = np.arange(len(cand)); w = 0.36
ax.bar(x - w / 2 - 0.01, cand["cv_macro_f1"], w, color=C4[0], label="5-fold CV macro-F1 (train)")
ax.bar(x + w / 2 + 0.01, cand["val_macro_f1"], w, color=C4[2], label="Validation macro-F1")
for i, r in cand.iterrows():
    ax.text(i - w / 2 - 0.01, r["cv_macro_f1"] + 0.008, f"{r['cv_macro_f1']:.3f}", ha="center", fontsize=7); ax.text(i + w / 2 + 0.01, r["val_macro_f1"] + 0.008, f"{r['val_macro_f1']:.3f}", ha="center", fontsize=7)
ax.set_xticks(x); ax.set_xticklabels(cand["label"], fontsize=7.5); ax.set_ylim(0.5, 1.0); ax.set_ylabel("macro-F1")
ax.set_title("Model selection: HOG variant x kernel (best grid setting of each)", fontsize=9.5); ax.legend(frameon=False, fontsize=8, loc="upper left"); clean(ax)
fig.tight_layout(); fig.savefig(FIG / "model_selection.png", dpi=220, facecolor="white"); plt.close(fig)

# 4. RBF hyper-parameter heatmap (CV macro-F1) for the selected HOG variant, best class_weight
v = sel["selected"]["hog_variant"]
r = pd.read_csv(L.OUT / "selection" / f"cv_results_{v}_rbf.csv")
cw = sel["selected"]["best_params"].get("class_weight") if sel["selected"]["kernel"] == "rbf" else None
r = r[r["param_svc__class_weight"].isna()] if cw is None else r[r["param_svc__class_weight"] == cw]
piv = r.pivot_table(index="param_svc__C", columns="param_svc__gamma", values="mean_test_f1_macro")
nf = sel["selected"]["n_features"] if sel["selected"]["hog_variant"] == v else None
fig, ax = plt.subplots(figsize=(4.6, 3.1))
im = ax.imshow(piv.values, cmap="Blues", vmin=piv.values.min() - 0.02, vmax=piv.values.max())
ax.set_xticks(range(piv.shape[1])); ax.set_yticks(range(piv.shape[0]))
ax.set_xticklabels([f"{float(g) * (r['param_svc__gamma'].astype(float).max() and 1):.2e}" for g in piv.columns], fontsize=7.5); ax.set_yticklabels([f"{float(c):g}" for c in piv.index])
ax.set_xlabel("RBF gamma"); ax.set_ylabel("C"); ax.set_title(f"RBF 5-fold CV macro-F1 ({v})", fontsize=9)
for i in range(piv.shape[0]):
    for j in range(piv.shape[1]):
        ax.text(j, i, f"{piv.values[i, j]:.3f}", ha="center", va="center", fontsize=8, color="white" if (piv.values[i, j] - (piv.values.min() - 0.02)) / (piv.values.max() - piv.values.min() + 0.02) > 0.45 else INK)
fig.tight_layout(); fig.savefig(FIG / "rbf_cv_heatmap.png", dpi=220, facecolor="white"); plt.close(fig)

# 5. class distribution by partition
import csv
cnt = {p: np.zeros(4, int) for p in ("train", "val", "test")}
for row in csv.DictReader(open(L.MANIFEST)):
    if row["is_representative"] == "True" and row["partition"] in cnt: cnt[row["partition"]][int(row["class_idx"])] += 1
fig, ax = plt.subplots(figsize=(6.0, 3.2))
w = 0.26
for k, (part, col) in enumerate((("train", C4[0]), ("val", C4[2]), ("test", C4[1]))):
    vals = [cnt[part][i] for i in range(4)]
    ax.bar(np.arange(4) + (k - 1) * (w + 0.02), vals, w, color=col, label={"train": "train (2,311)", "val": "validation (492)", "test": "test (492)"}[part])
    for i, vv in enumerate(vals): ax.text(i + (k - 1) * (w + 0.02), vv + 12, str(vv), ha="center", fontsize=7.5)
ax.set_xticks(range(4)); ax.set_xticklabels(LAB); ax.set_ylabel("unique images"); ax.set_ylim(0, 1020)
ax.set_title("Class distribution of the cluster-disjoint split", fontsize=9.5); ax.legend(frameon=False, fontsize=8, loc="upper right"); clean(ax)
fig.tight_layout(); fig.savefig(FIG / "class_distribution.png", dpi=220, facecolor="white"); plt.close(fig)

# 6. HOG illustration: one training image per class, resized as in the pipeline, with its HOG visualisation
tr_p, ytr = L.load_partition("train")
cfg = json.load(open(L.OUT / "model" / "model_config.json"))
hp = {k: (tuple(v) if isinstance(v, list) else v) for k, v in cfg["hog_params"].items()}
fig, axs = plt.subplots(2, 4, figsize=(7.2, 3.9))
for k, c in enumerate(L.CLASSES):
    p = [q for q, y in zip(tr_p, ytr) if y == k][3]
    im = L.preprocess(Image.open(L.ARCHIVE / p), cfg["image_size"])
    _, vis = hog(im, visualize=True, feature_vector=True, **hp)
    axs[0, k].imshow(im, cmap="gray"); axs[0, k].set_title(L.CLASS_LABELS[c], fontsize=8.5); axs[1, k].imshow(vis / max(vis.max(), 1e-9), cmap="gray")
    for a in axs[:, k]: a.axis("off")
axs[0, 0].text(-0.08, 0.5, "grayscale\nresized", transform=axs[0, 0].transAxes, ha="right", va="center", fontsize=7.5, color=MUTED)
axs[1, 0].text(-0.08, 0.5, "HOG\nvisualisation", transform=axs[1, 0].transAxes, ha="right", va="center", fontsize=7.5, color=MUTED)
fig.suptitle(f"Training images and their HOG descriptors ({cfg['image_size']} px, {cfg['hog_params']['pixels_per_cell'][0]}-px cells, {cfg['n_features']} features)", fontsize=9.5)
fig.tight_layout(rect=(0.04, 0, 1, 0.94)); fig.savefig(FIG / "hog_illustration.png", dpi=220, facecolor="white"); plt.close(fig)

# 7. misclassified test examples (the 12 with the lowest top-score margin are not chosen: just the first 12 errors in manifest order)
te_p = pred["files"]; yt = np.array(pred["y_true"]); yp = np.array(pred["y_pred"])
wrong = np.where(yt != yp)[0][:12]
fig, axs = plt.subplots(2, 6, figsize=(7.2, 3.9))
for a in axs.ravel(): a.axis("off")
for a, i in zip(axs.ravel(), wrong):
    a.imshow(Image.open(L.ARCHIVE / te_p[i]).convert("L").resize((128, 128)), cmap="gray"); a.set_title(f"true: {L.CLASSES[yt[i]]}\npred: {L.CLASSES[yp[i]]}", fontsize=6.5, color="#b3261e")
fig.suptitle(f"First 12 misclassified test images (of {int((yt != yp).sum())} errors), in split-manifest order", fontsize=9)
fig.subplots_adjust(hspace=0.55, top=0.86, bottom=0.02, left=0.02, right=0.98); fig.savefig(FIG / "misclassified_examples.png", dpi=220, facecolor="white"); plt.close(fig)

# 8. pipeline diagram
fig, ax = plt.subplots(figsize=(7.6, 3.6)); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
def box(x, y, w, h, t, fc="#ffffff", ec=NAVY, fs=8, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.01,rounding_size=0.015", fc=fc, ec=ec, lw=1.3)); ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=fs, fontweight="bold" if bold else "normal", linespacing=1.25)
def arr(p, q): ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=10, color=MUTED, lw=1.2))
steps = ["MRI image\n(JPEG)", f"Grayscale,\nresize\n{cfg['image_size']}x{cfg['image_size']}", f"HOG\n{cfg['n_features']} features", "Standard-\nScaler\n(train fit only)", f"{cfg['kernel'].upper()} SVM\n(C={cfg['svc_params']['C']:g})", "Class +\ndecision\nscores"]
for i, t in enumerate(steps):
    x = 0.01 + i * 0.165; box(x, 0.58, 0.135, 0.26, t, fs=7, fc="#e4f2f0" if i in (2, 3, 4) else "#ffffff", ec=TEAL if i in (2, 3, 4) else NAVY)
    if i: arr((x - 0.028, 0.71), (x - 0.003, 0.71))
box(0.01, 0.12, 0.30, 0.28, "Training partition (2,311)\n5-fold CV grid search\n(training folds only)", fc="#eef2f6", fs=7.5)
box(0.345, 0.12, 0.30, 0.28, "Validation partition (492)\nselects HOG variant\nand kernel", fc="#fdf1dc", ec=AMBER, fs=7.5)
box(0.68, 0.12, 0.30, 0.28, "Test partition (492)\nevaluated ONCE with the\nfrozen final model", fc="#e4f2f0", ec=TEAL, fs=7.5, bold=True)
arr((0.16, 0.40), (0.16, 0.57)); arr((0.495, 0.40), (0.495, 0.57)); arr((0.83, 0.40), (0.83, 0.57))
ax.text(0.5, 0.95, "Classical pipeline and data usage", ha="center", fontsize=10, fontweight="bold", color=NAVY)
fig.savefig(FIG / "pipeline_diagram.png", dpi=220, facecolor="white", bbox_inches="tight"); plt.close(fig)

# 9. leakage evidence histogram (re-measured max similarity of val/test images to the training images)
fig, ax = plt.subplots(figsize=(5.8, 3.0))
for name, col in (("val", C4[2]), ("test", C4[1])):
    f = L.OUT / "test" / f"_max_sim_{name}.npy"
    if f.exists(): ax.hist(np.load(f), bins=40, alpha=0.65, color=col, label="validation" if name == "val" else "test")
ax.axvline(0.98, color="#b3261e", ls="--", lw=1.2); ax.text(0.62, ax.get_ylim()[1] * 0.55, "red dashed line: linking\nthreshold 0.98 (no held-out\nimage reaches it)", ha="left", fontsize=7.5, color="#b3261e")
ax.set_xlabel("maximum similarity to any training image (32x32 cosine, 8 orientations)"); ax.set_ylabel("images"); ax.legend(frameon=False, fontsize=8); clean(ax)
ax.set_title("Nearest-training-image similarity of held-out images", fontsize=9.5)
fig.tight_layout(); fig.savefig(FIG / "leakage_similarity_hist.png", dpi=220, facecolor="white"); plt.close(fig)
print(sorted(p.name for p in FIG.glob("*.png")))
