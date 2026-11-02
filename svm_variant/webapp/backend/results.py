"""Reads the saved SVM result files (outputs/svm_variant/). Values are passed through unchanged; nothing is recomputed or modified."""
import json
from . import config


def _load(path):
    return json.loads(path.read_text())


def metrics() -> dict:
    t = _load(config.TEST_EVAL)
    s = _load(config.SELECTION)
    return {
        "n_test": t["n_test"], "classes": config.CLASSES, "model": t["model"], "accuracy": t["accuracy"], "balanced_accuracy": t["balanced_accuracy"],
        "macro_precision": t["macro_precision"], "macro_recall": t["macro_recall"], "macro_f1": t["macro_f1"], "weighted_f1": t["weighted_f1"],
        "per_class": t["per_class"], "confusion_matrix": t["confusion_matrix"], "tumour_vs_notumor": t["tumour_vs_notumor"],
        "bootstrap_95ci": t["bootstrap_95ci_2000_resamples_of_test_predictions"], "majority_class_baseline_accuracy": t["majority_class_baseline_accuracy"],
        "runtime_seconds": t["runtime_seconds"], "model_file_sha256": t["model_file_sha256"],
        "candidates": s["candidates"], "selected": s["selected"], "selection_rule": s["selection_rule"], "validation_baseline": s["baselines"],
        "sources": ["outputs/svm_variant/test/test_evaluation.json", "outputs/svm_variant/selection/selection.json"],
        "notes": "Model selected on training cross-validation and the validation partition; the test partition was evaluated once with the frozen model.",
    }


def experiment() -> dict:
    leak = _load(config.LEAKAGE) if config.LEAKAGE.exists() else None
    cfg = _load(config.MODEL_CONFIG)
    return {
        "title": "Brain Tumor MRI Classification Using Support Vector Machine (SVM)",
        "status": "Academic research prototype. Not a clinically validated medical diagnostic system.",
        "method": ["Grayscale conversion and bilinear resize", f"Histogram of Oriented Gradients ({cfg['n_features']} features, variant {cfg['hog_variant']})",
                   "StandardScaler fitted on the training partition only", f"{cfg['kernel'].upper()} SVM (scikit-learn SVC)"],
        "model_config": {k: cfg[k] for k in ("image_size", "hog_variant", "hog_params", "n_features", "kernel", "svc_params", "n_support_vectors", "seed", "fitted_on", "selected_by", "packages")},
        "dataset": {
            "description": "4-class brain-tumour MRI images (glioma, meningioma, no tumour, pituitary).",
            "provenance": "Matches Kaggle 'Brain Tumor MRI Dataset' v2 (Masoud Nickparvar, CC BY 4.0) by file count, per-class split and size; the original download record is unverified. The dataset is not redistributed.",
            "split": "Cluster-disjoint, class-stratified 70/15/15 split of 3,295 unique images (2,311 train / 492 validation / 492 test) built after near-duplicate clustering (heuristic).",
        },
        "leakage_evidence": leak,
        "limitations": [
            "Small, imbalanced test set (492 images, only 46 no-tumour); results are single measurements with bootstrap intervals, not clinical estimates.",
            "Patient-level independence is NOT proven: the dataset has no patient identifiers, and near-duplicate detection is a heuristic.",
            "HOG + SVM is a classical baseline on 2-D slices; it is not a diagnostic system and has not been validated on other scanners, sites or populations.",
            "The SVM returns decision scores, not calibrated probabilities. Any uploaded image, even one that is not a brain MRI, receives one of the four labels (no out-of-distribution detection).",
            "The model was selected on the training cross-validation and the validation partition; the test partition was used once.",
            "Dataset provenance: matches Kaggle v2 but the download record is unverified; upstream datasets may carry separate terms.",
        ],
        "source_files": ["outputs/svm_variant/test/test_evaluation.json", "outputs/svm_variant/selection/selection.json", "outputs/svm_variant/model/model_config.json"],
    }


_FIG = [
    ("pipeline", "Pipeline and data usage", "diagram", "pipeline_diagram.png", "Image to class; training, validation and test usage."),
    ("confusion", "Test confusion matrix", "result", "confusion_matrix_test.png", "Counts and row-normalised; produced from the saved test predictions."),
    ("per-class", "Per-class precision, recall and F1", "result", "per_class_metrics_test.png", "From the saved test predictions."),
    ("selection", "Model selection (CV vs validation)", "result", "model_selection.png", "Six candidates: three HOG variants x two kernels."),
    ("heatmap", "RBF hyper-parameter grid (CV)", "result", "rbf_cv_heatmap.png", "Training-only 5-fold cross-validation."),
    ("distribution", "Class distribution of the split", "data", "class_distribution.png", "Representatives of each cluster-disjoint partition."),
    ("hog", "HOG illustration", "data", "hog_illustration.png", "Training images and their HOG descriptors."),
    ("errors", "Misclassified test images", "result", "misclassified_examples.png", "First 12 errors in manifest order (real dataset images)."),
    ("leakage", "Leakage check: nearest-training similarity", "audit", "leakage_similarity_hist.png", "Re-measured maximum similarity of held-out images to training images."),
]


def gallery():
    return [{"id": i, "title": t, "kind": k, "note": n, "url": f"/api/gallery/image/{i}"} for i, t, k, f, n in _FIG if (config.FIGURES / f).exists()]


def gallery_path(item_id):
    for i, _t, _k, f, _n in _FIG:
        if i == item_id and (config.FIGURES / f).exists():
            return config.FIGURES / f
    return None
