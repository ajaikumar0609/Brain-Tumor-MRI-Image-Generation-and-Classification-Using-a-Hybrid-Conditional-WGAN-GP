#!/usr/bin/env python3
"""Project-authored diagrams and the derived sensitivity/specificity chart for the micro-project report.
Reads only saved files; nothing is trained or evaluated.   python outputs/healthcare_ai_microproject/scripts/make_figures.py"""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "outputs/healthcare_ai_microproject/assets/figures"
OUT.mkdir(parents=True, exist_ok=True)
NAVY, TEAL, AMBER, INK, MUTED = "#1f3a5f", "#2a9d8f", "#c98a1a", "#14213d", "#556070"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})


def box(ax, x, y, w, h, text, fc="#ffffff", ec=NAVY, tc=INK, fs=8.5, bold=False, lw=1.4):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.012,rounding_size=0.015", fc=fc, ec=ec, lw=lw))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=tc, fontweight="bold" if bold else "normal", linespacing=1.25)


def arrow(ax, p, q, color=MUTED, style="-|>", ls="-", rad=0.0):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=11, color=color, lw=1.3, linestyle=ls, connectionstyle=f"arc3,rad={rad}"))


def canvas(w, h):
    fig, ax = plt.subplots(figsize=(w, h)); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off"); return fig, ax


# ---- 1. research workflow -------------------------------------------------------------------------------------------------
fig, ax = canvas(7.0, 7.4)
box(ax, .12, .915, .76, .07, "Kaggle brain-tumour MRI data: 7,200 images\n(Training 1,400 + Testing 400 per class)", fc="#eef2f6", fs=8.5)
box(ax, .12, .79, .76, .092, "Audit: near-duplicate clustering (threshold 0.98)\n32x32 cosine similarity over 8 orientations -> 3,479 clusters\n1,076 of 1,600 original test images had a training copy", fc="#fdf1dc", ec=AMBER, fs=8)
box(ax, .12, .683, .76, .068, "Quarantine 207 images (label conflicts, augmented-only\nclusters, refinement removals) -> 3,295 unique images", fc="#fdf1dc", ec=AMBER, fs=8)
box(ax, .12, .575, .76, .068, "Cluster-disjoint, class-stratified split (70/15/15)\nTrain 2,311  |  Validation 492  |  Test 492", fc="#e4f2f0", ec=TEAL, bold=True, fs=8.5)
for a_, b_ in ((.915, .884), (.79, .753), (.683, .645)):
    arrow(ax, (.5, a_), (.5, b_))
box(ax, .02, .35, .29, .15, "1. Train 3 GANs\n(training partition only)\nDCGAN, WGAN-GP,\ncWGAN-GP: 3,000 updates", fs=7.4)
box(ax, .355, .35, .29, .15, "2. Generation quality\nFID / KID of generated\nimages vs the 492 test\nimages; 3 seeds + floor", fs=7.4)
box(ax, .69, .35, .29, .15, "3. Downstream CNN, 3 seeds\nA real only: 2,311\nB + 2,888 cWGAN-GP: 5,199\nC real, matched: 5,199", fs=7.4)
arrow(ax, (.30, .575), (.17, .503)); arrow(ax, (.5, .575), (.5, .503)); arrow(ax, (.70, .575), (.83, .503))
box(ax, .06, .17, .40, .1, "Results (Chapter 5)\nDCGAN: best FID/KID\nC: highest mean accuracy", fc="#e4f2f0", ec=TEAL, bold=True, fs=8)
box(ax, .54, .17, .40, .1, "Validation selects the CNN epoch;\ntest set read afterwards\n(n = 492, only 46 no-tumour)", fc="#eef2f6", fs=7.8)
arrow(ax, (.17, .35), (.23, .272)); arrow(ax, (.5, .35), (.34, .272)); arrow(ax, (.83, .35), (.74, .272))
box(ax, .04, .02, .92, .115, "NeuroVision AI web application (Chapter 4)\nreads the saved results; generates images with the saved cWGAN-GP checkpoint;\nclassifies uploads with a THIRD-PARTY EfficientNet-B3, not the A/B/C research classifiers", fc="#ffffff", ec=NAVY, fs=7.8)
arrow(ax, (.25, .17), (.25, .137), ls="--")
fig.savefig(OUT / "fig_research_workflow.png", dpi=220, bbox_inches="tight", facecolor="white"); plt.close(fig)

# ---- 2. cWGAN-GP architecture ----------------------------------------------------------------------------------------------
fig, ax = canvas(7.0, 6.2)
ax.text(.01, .975, "Generator G(z, y)", fontsize=10, fontweight="bold", color=NAVY)
box(ax, .01, .85, .17, .075, "noise z\n100-d, N(0, I)", fc="#eef2f6", fs=7.8)
box(ax, .01, .74, .17, .075, "class label y\n0..3", fc="#eef2f6", fs=7.8)
box(ax, .25, .74, .19, .075, "Embedding\n4 x 50", fc="#e4f2f0", ec=TEAL, fs=7.8)
box(ax, .52, .79, .17, .075, "concatenate\n150-d vector", fs=7.8)
arrow(ax, (.18, .887), (.52, .84)); arrow(ax, (.18, .777), (.25, .777)); arrow(ax, (.44, .777), (.52, .82))
ax.text(.72, .83, "reshape to\n150 x 1 x 1", fontsize=7.5, color=MUTED, va="center")
ax.plot([.605, .605, .09], [.79, .70, .70], color=MUTED, lw=1.3); arrow(ax, (.09, .70), (.09, .655))
chain = ["ConvT 512\n4 x 4\nBN, ReLU", "ConvT 256\n8 x 8\nBN, ReLU", "ConvT 128\n16 x 16\nBN, ReLU", "ConvT 64\n32 x 32\nBN, ReLU", "ConvT 1\n64 x 64\nTanh"]
for i, t in enumerate(chain):
    x = .01 + i * .2
    box(ax, x, .53, .165, .12, t, fs=7.6)
    if i: arrow(ax, (x - .035, .59), (x, .59))
ax.text(.01, .485, "Output: 64 x 64 grayscale image in [-1, 1]. The label is a requested condition; there is no classifier guidance.", fontsize=7.6, color=MUTED)
ax.text(.01, .415, "Projection critic  D(x, y) = psi(h(x)) + E(y) . h(x)", fontsize=10, fontweight="bold", color=NAVY)
box(ax, .01, .27, .15, .11, "image x\n64x64x1\nreal or fake", fc="#eef2f6", fs=7.4)
crit = ["Conv 64\ns2\nLeakyReLU", "Conv 128\ns2\nLeakyReLU", "Conv 256\ns2\nLeakyReLU", "Conv 512\ns2\nLeakyReLU"]
for i, t in enumerate(crit):
    x = .205 + i * .135
    box(ax, x, .27, .105, .11, t, fs=6.8)
    arrow(ax, (x - .045, .325), (x, .325))
box(ax, .745, .27, .12, .11, "sum-pool\n4x4 -> h(x)\n512-d", fc="#ffffff", fs=7)
arrow(ax, (.71, .325), (.745, .325))
box(ax, .60, .115, .15, .08, "psi: Linear\n512 -> 1", fc="#e4f2f0", ec=TEAL, fs=7.4)
box(ax, .78, .115, .20, .08, "E(y): Embedding\n4 x 512, dot h(x)", fc="#e4f2f0", ec=TEAL, fs=7.2)
arrow(ax, (.80, .27), (.69, .197)); arrow(ax, (.83, .27), (.87, .197))
box(ax, .35, .115, .17, .08, "D(x, y)\n= sum of both", fs=7.6)
arrow(ax, (.60, .155), (.52, .155)); arrow(ax, (.78, .13), (.52, .13), rad=-0.25)
ax.text(.01, .04, "No BatchNorm in the critic.  L_D = E[D(G(z,y),y)] - E[D(x,y)] + 10 GP;  L_G = -E[D(G(z,y),y)];  5 critic updates per generator update.", fontsize=7.2, color=MUTED)
fig.savefig(OUT / "fig_cwgangp_architecture.png", dpi=220, bbox_inches="tight", facecolor="white"); plt.close(fig)

# ---- 3. software architecture ----------------------------------------------------------------------------------------------
fig, ax = canvas(7.0, 6.6)
ax.add_patch(FancyBboxPatch((.005, .665), .99, .32, boxstyle="round,pad=0.008,rounding_size=0.02", fc="#f6f8fa", ec="#d5dde6"))
ax.text(.02, .945, "Browser: http://localhost:5173   (React + TypeScript + Vite)", fontsize=9, fontweight="bold", color=NAVY)
pages = ["Dashboard", "Classify\nMRI", "Generate", "Gallery", "Experiment\nresults"]
for i, t in enumerate(pages): box(ax, .02 + i * .195, .80, .17, .105, t, fs=7.8)
box(ax, .02, .69, .465, .075, "Tailwind CSS v4 + shadcn/ui (Radix) components", fc="#e4f2f0", ec=TEAL, fs=7.6)
box(ax, .515, .69, .465, .075, "Recharts charts + typed API client (lib/api.ts)", fc="#e4f2f0", ec=TEAL, fs=7.6)
arrow(ax, (.5, .665), (.5, .60)); ax.text(.52, .625, "fetch /api/*   (Vite dev proxy to port 8000)", fontsize=7.6, color=MUTED, va="center")
ax.add_patch(FancyBboxPatch((.005, .15), .99, .44, boxstyle="round,pad=0.008,rounding_size=0.02", fc="#f6f8fa", ec="#d5dde6"))
ax.text(.02, .555, "FastAPI backend: http://127.0.0.1:8000   (app/backend/)", fontsize=9, fontweight="bold", color=NAVY)
eps = ["GET\n/api/health", "GET\n/api/models/status", "POST\n/api/classify", "POST\n/api/generate", "GET /api/metrics\n/api/experiment\n/api/gallery"]
for i, t in enumerate(eps): box(ax, .02 + i * .195, .415, .17, .105, t, fs=6.6)
mods = ["main.py\nvalidation, CORS,\nJSON errors", "ml.py\nmodel wrappers,\nload once, MPS/CPU", "results.py\nreads saved result\nfiles (read-only)", "config.py\nrelative paths\nand limits"]
for i, t in enumerate(mods): box(ax, .02 + i * .245, .20, .22, .13, t, fs=7)
for x in (.13, .375, .62, .865): pass
box(ax, .02, .025, .30, .105, "cWGAN-GP checkpoint\n(step 3000), strict load,\neval mode", fc="#fdf1dc", ec=AMBER, fs=6.8)
box(ax, .35, .025, .30, .105, "Third-party EfficientNet-B3\nweights, SHA-256 checked;\n224x224 grayscale input", fc="#fdf1dc", ec=AMBER, fs=6.8)
box(ax, .68, .025, .30, .105, "outputs/deduplicated_\nexperiment/ metrics,\nsummary, split files", fc="#eef2f6", fs=6.8)
arrow(ax, (.37, .20), (.17, .118)); arrow(ax, (.37, .20), (.50, .118)); arrow(ax, (.62, .20), (.83, .118))
fig.savefig(OUT / "fig_app_architecture.png", dpi=220, bbox_inches="tight", facecolor="white"); plt.close(fig)

# ---- 4. derived sensitivity / specificity -----------------------------------------------------------------------------------
d = json.load(open(ROOT / "outputs/healthcare_ai_microproject/assets/derived_class_metrics.json"))
C = {"A": "#3d73b8", "B": "#1f9e8f", "C": "#c2651a"}
NAMES = {"A": "A  real only", "B": "B  real + synthetic", "C": "C  matched real-only"}
fig, axs = plt.subplots(1, 2, figsize=(7.2, 3.3), gridspec_kw={"width_ratios": [1, 1.7]})
ax = axs[0]
labs = ["Sensitivity\n(tumour found)", "Specificity\n(no-tumour kept)"]
w = 0.26
for i, cid in enumerate("ABC"):
    tv = d["conditions"][cid]["tumour_vs_notumor"]
    for j, k in enumerate(("sensitivity", "specificity")):
        v = tv[k]["mean"]; ax.bar(j + (i - 1) * (w + 0.02), v, w, color=C[cid], label=NAMES[cid] if j == 0 else None)
        ax.text(j + (i - 1) * (w + 0.02), v + 0.012, f"{v:.2f}", ha="center", fontsize=7.5, color=INK)
ax.set_xticks([0, 1]); ax.set_xticklabels(labs); ax.set_ylim(0, 1.1); ax.set_ylabel("mean over 3 seeds"); ax.set_title("Tumour vs no-tumour\n(446 tumour / 46 no-tumour test images)", fontsize=8.5, color=INK)
ax = axs[1]
cls = ["glioma", "meningioma", "notumor", "pituitary"]
for i, cid in enumerate("ABC"):
    for j, c in enumerate(cls):
        v = d["conditions"][cid]["per_class"][c]["sensitivity"]["mean"]
        ax.bar(j + (i - 1) * (w + 0.02), v, w, color=C[cid]); ax.text(j + (i - 1) * (w + 0.02), v + 0.012, f"{v:.2f}", ha="center", fontsize=7, color=INK)
ax.set_xticks(range(4)); ax.set_xticklabels(["glioma\n(196)", "meningioma\n(122)", "no tumour\n(46)", "pituitary\n(128)"]); ax.set_ylim(0, 1.1)
ax.set_title("Per-class sensitivity (recall), one-vs-rest", fontsize=8.5, color=INK)
for a in axs:
    for s in ("top", "right"): a.spines[s].set_visible(False)
    a.grid(axis="y", color="#e3e8ee", lw=0.6); a.set_axisbelow(True)
h, l = axs[0].get_legend_handles_labels()
fig.legend(h, l, loc="lower center", ncol=3, frameon=False, fontsize=8, bbox_to_anchor=(0.5, -0.04))
fig.tight_layout(rect=(0, 0.04, 1, 1))
fig.savefig(OUT / "fig_sens_spec.png", dpi=220, bbox_inches="tight", facecolor="white"); plt.close(fig)
print("figures written:", sorted(p.name for p in OUT.glob("*.png")))
