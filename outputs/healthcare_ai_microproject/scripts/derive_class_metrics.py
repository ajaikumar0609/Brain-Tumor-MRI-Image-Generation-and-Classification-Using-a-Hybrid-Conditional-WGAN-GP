#!/usr/bin/env python3
"""Derive per-class sensitivity/specificity (one-vs-rest) and tumour-vs-no-tumour sensitivity/specificity from the SAVED per-run test
predictions (outputs/deduplicated_experiment/downstream/runs/*_test_predictions.json). No model is run; nothing is retrained.
Writes outputs/healthcare_ai_microproject/assets/derived_class_metrics.json"""
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
RUNS = ROOT / "outputs/deduplicated_experiment/downstream/runs"
OUT = ROOT / "outputs/healthcare_ai_microproject/assets/derived_class_metrics.json"
CLASSES = ["glioma", "meningioma", "notumor", "pituitary"]
CONDS = {"A": "A_real_only", "B": "B_real_plus_cwgangp_synthetic", "C": "C_real_only_matched_composition"}
res = {"source": "outputs/deduplicated_experiment/downstream/runs/*_test_predictions.json (y_true, y_pred; 492 test images; seeds 42-44)",
       "method": "one-vs-rest sensitivity = TP/(TP+FN), specificity = TN/(TN+FP) per class; tumour-vs-no-tumour: positive = any of glioma/meningioma/pituitary; mean and sample sd over 3 seeds",
       "classes": CLASSES, "conditions": {}}
for cid, stem in CONDS.items():
    per = {c: {"sens": [], "spec": []} for c in CLASSES}; tv = {"sens": [], "spec": []}; acc = []
    for seed in (42, 43, 44):
        p = json.load(open(RUNS / f"{stem}_seed{seed}_test_predictions.json"))
        t, y = np.array(p["y_true"]), np.array(p["y_pred"]); assert len(t) == 492
        acc.append(float((t == y).mean()))
        for i, c in enumerate(CLASSES):
            tp = ((t == i) & (y == i)).sum(); fn = ((t == i) & (y != i)).sum(); fp = ((t != i) & (y == i)).sum(); tn = ((t != i) & (y != i)).sum()
            per[c]["sens"].append(tp / (tp + fn)); per[c]["spec"].append(tn / (tn + fp))
        tt, yy = t != 2, y != 2
        tv["sens"].append(float((tt & yy).sum() / tt.sum())); tv["spec"].append(float((~tt & ~yy).sum() / (~tt).sum()))
    ms = lambda v: {"mean": float(np.mean(v)), "sd": float(np.std(v, ddof=1)), "values": [float(x) for x in v]}
    res["conditions"][cid] = {"accuracy_check": ms(acc), "per_class": {c: {"sensitivity": ms(per[c]["sens"]), "specificity": ms(per[c]["spec"])} for c in CLASSES},
                              "tumour_vs_notumor": {"sensitivity": ms(tv["sens"]), "specificity": ms(tv["spec"]), "n_tumour": 446, "n_notumor": 46}}
OUT.write_text(json.dumps(res, indent=2))
s = json.load(open(ROOT / "outputs/deduplicated_experiment/downstream/summary.json"))
for cid, stem in CONDS.items():
    assert abs(res["conditions"][cid]["accuracy_check"]["mean"] - s["conditions"][stem]["accuracy"]["mean"]) < 1e-9, cid   # reproduces the saved accuracy
    c = res["conditions"][cid]
    print(cid, "acc", round(c["accuracy_check"]["mean"], 3), "| tumour-vs-no-tumour sens %.3f spec %.3f" % (c["tumour_vs_notumor"]["sensitivity"]["mean"], c["tumour_vs_notumor"]["specificity"]["mean"]),
          "| per-class sens", [round(c["per_class"][k]["sensitivity"]["mean"], 2) for k in CLASSES], "spec", [round(c["per_class"][k]["specificity"]["mean"], 2) for k in CLASSES])
