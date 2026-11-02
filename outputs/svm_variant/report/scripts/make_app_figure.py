#!/usr/bin/env python3
"""Software-architecture diagram of the SVM web application (project-authored)."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT = Path(__file__).resolve().parents[1] / "assets"
NAVY, TEAL, AMBER, INK, MUTED = "#1f3a5f", "#2a9d8f", "#c98a1a", "#14213d", "#556070"
plt.rcParams.update({"font.family": "DejaVu Sans"})
fig, ax = plt.subplots(figsize=(7.0, 5.8)); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")


def box(x, y, w, h, t, fc="#ffffff", ec=NAVY, fs=7.6, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.008,rounding_size=0.015", fc=fc, ec=ec, lw=1.3)); ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=fs, fontweight="bold" if bold else "normal", linespacing=1.25)


def arr(p, q):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=10, color=MUTED, lw=1.2))


ax.add_patch(FancyBboxPatch((.005, .68), .99, .3, boxstyle="round,pad=0.008,rounding_size=0.02", fc="#f6f8fa", ec="#d5dde6"))
ax.text(.02, .945, "Browser: http://localhost:5173   (React + TypeScript + Vite)", fontsize=9, fontweight="bold", color=NAVY)
for i, t in enumerate(["Dashboard", "Classify MRI", "SVM results", "Figures"]):
    box(.02 + i * .245, .80, .22, .1, t)
box(.02, .70, .465, .07, "Tailwind CSS + shadcn/ui components", fc="#e4f2f0", ec=TEAL)
box(.515, .70, .465, .07, "Recharts charts + typed API client", fc="#e4f2f0", ec=TEAL)
arr((.5, .68), (.5, .62)); ax.text(.52, .645, "fetch /api/*  (Vite dev proxy to port 8000)", fontsize=7.6, color=MUTED, va="center")
ax.add_patch(FancyBboxPatch((.005, .17), .99, .44, boxstyle="round,pad=0.008,rounding_size=0.02", fc="#f6f8fa", ec="#d5dde6"))
ax.text(.02, .575, "FastAPI backend: http://127.0.0.1:8000   (svm_variant/webapp/backend/)", fontsize=9, fontweight="bold", color=NAVY)
for i, t in enumerate(["GET\n/api/health", "GET\n/api/models/status", "POST\n/api/classify", "GET /api/metrics\n/api/experiment", "GET\n/api/gallery"]):
    box(.02 + i * .195, .43, .17, .11, t, fs=6.6)
for i, t in enumerate(["main.py\nvalidation, CORS,\nJSON errors", "ml.py\nloads the SVM once;\nSHA-256 must match\nthe evaluated model", "results.py\nreads saved results\n(read-only)", "config.py\nrelative paths,\nlimits"]):
    box(.02 + i * .245, .21, .22, .17, t, fs=6.8)
box(.02, .015, .30, .11, "svm_lib.py\ngrayscale, resize, HOG,\nStandardScaler + SVC", fc="#e4f2f0", ec=TEAL, fs=6.9)
box(.35, .015, .30, .11, "outputs/svm_variant/model/\nsvm_model.joblib + config", fc="#fdf1dc", ec=AMBER, fs=6.9)
box(.68, .015, .30, .11, "outputs/svm_variant/\ntest, selection, figures", fc="#eef2f6", fs=6.9)
arr((.37, .21), (.17, .13)); arr((.37, .21), (.50, .13)); arr((.62, .21), (.83, .13))
fig.savefig(OUT / "svm_app_architecture.png", dpi=220, bbox_inches="tight", facecolor="white"); print("ok")
