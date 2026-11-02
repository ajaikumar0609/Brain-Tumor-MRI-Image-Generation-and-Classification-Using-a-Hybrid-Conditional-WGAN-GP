#!/usr/bin/env python3
"""Build SVM_Micro_Project_Report.docx from the official e-report template (templates/E-report template.docx).
Every number comes from the saved SVM result files under outputs/svm_variant/; nothing is trained or evaluated here.
    .venv/bin/python outputs/svm_variant/report/scripts/build_svm_report.py"""
import copy, csv, json, sys
from pathlib import Path
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH as AL
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from report_lib import Builder  # noqa: E402

ROOT = HERE.parents[3]
RPT = ROOT / "outputs/svm_variant/report"
SV = ROOT / "outputs/svm_variant"
FIG = SV / "figures"
SHOT = RPT / "assets/screenshots"
ASSET = RPT / "assets"
TEMPLATE = ROOT / "templates/E-report template.docx"
OUT = RPT / "SVM_Micro_Project_Report.docx"
TOC_JSON = RPT / "assets/toc_pages.json"
EXP = ROOT / "outputs/deduplicated_experiment"

TITLE = "Brain Tumor MRI Classification Using Support Vector Machine (SVM)"
STUDENT = "[Student name – to be filled in] ([Register number – to be filled in])"
M, pm = "−", "±"

t = json.load(open(SV / "test/test_evaluation.json"))
sel = json.load(open(SV / "selection/selection.json"))
cfg = json.load(open(SV / "model/model_config.json"))
leak = json.load(open(SV / "leakage_evidence.json"))
audit = json.load(open(EXP / "dedup_audit_summary.json"))
pred = json.load(open(SV / "test/test_predictions.json"))
cand = sel["candidates"]
CL = ["glioma", "meningioma", "notumor", "pituitary"]
CLN = {"glioma": "Glioma", "meningioma": "Meningioma", "notumor": "No tumour", "pituitary": "Pituitary tumour"}
cm = t["confusion_matrix"]["counts"]
ci = t["bootstrap_95ci_2000_resamples_of_test_predictions"]
sc = sel["selected"]
f3 = lambda x: f"{x:.3f}"
assert t["n_test"] == 492 and sum(map(sum, cm)) == 492 and cfg["test_partition_read"] is False
assert audit["representatives"] == 3295 and audit["partition_totals"] == {"train": 2311, "val": 492, "test": 492}
ACC, MF1 = t["accuracy"], t["macro_f1"]
errors = 492 - sum(cm[i][i] for i in range(4))
off = sorted(((cm[i][j], CL[i], CL[j]) for i in range(4) for j in range(4) if i != j), reverse=True)
by = {(c["hog_variant"], c["kernel"]): c for c in cand}
rbf_gain = {v: by[(v, "rbf")]["val_macro_f1"] - by[(v, "linear")]["val_macro_f1"] for v in ("hog128_cell16", "hog128_cell8", "hog64_cell8")}

doc = Document(TEMPLATE)
body = doc.element.body
P = doc.paragraphs
assert P[0].text.startswith("TITLE OF MICRO PROJECT") and P[26].text.startswith("BONAFIDE") and P[56].text.startswith("TABLE OF CONTENTS")


def set_text(par, text, keep_run=0):
    runs = par.runs
    runs[keep_run].text = text
    for i, r in enumerate(runs):
        if i != keep_run:
            r._element.getparent().remove(r._element)


# ---- cover ----------------------------------------------------------------------------------------------------------------------
set_text(P[0], TITLE.upper() + " ")
P[0].runs[0].font.size = Pt(15)
set_text(P[4], STUDENT)
for i in (5, 6, 7):
    P[i]._p.getparent().remove(P[i]._p)
# course line, programme line ("[ AIML/AI ]" as printed), supervisor and October 2026 are left exactly as in the template (not confirmed for this student)

# ---- certificate ----------------------------------------------------------------------------------------------------------------------
runs = P[28].runs
runs[1].text = f"“{TITLE}” "
runs[5].text = STUDENT
runs[6].text = ""
P[26].paragraph_format.page_break_before = True
P[42].runs[0].text = "Submitted for the micro project presentation scheduled on "
P[56].paragraph_format.page_break_before = True

children = list(body.iterchildren())
toc_head = P[56]._p
idx_sub = children.index(P[42]._p)
for el in children[idx_sub + 1: children.index(toc_head)]:
    if el.tag == qn("w:p") and not "".join(el.itertext()).strip():
        body.remove(el)
children = list(body.iterchildren())
toc_tbl = doc.tables[0]._tbl
idx_tbl = children.index(toc_tbl)
frame = [el for el in children if el.tag == qn("w:p") and el.find(qn("w:pPr")) is not None and el.find(qn("w:pPr")).find(qn("w:pStyle")) is not None
         and el.find(qn("w:pPr")).find(qn("w:pStyle")).get(qn("w:val")) == "FrameContents"]
idx_eval = children.index(frame[0])
eval_block = children[idx_eval:-1]
spacers = [el for el in children[idx_tbl + 1: idx_eval] if el.tag == qn("w:p") and not "".join(el.itertext()).strip()]
for el in eval_block:
    body.remove(el)
for el in spacers[1:]:
    body.remove(el)
section_break_par = spacers[0]

B = Builder(doc)

# ---- abstract -------------------------------------------------------------------------------------------------------------------
mark = len(list(body.iterchildren())) - 1
B.para("ABSTRACT", AL.CENTER, 14, True, before=0, after=12, page_break=True)
B.para(
    "Brain tumour classification from MRI is a standard test of medical image analysis, and Support Vector Machines (SVMs) on hand-crafted features remain a strong, light-weight "
    "baseline that needs no GPU and is easy to inspect. This micro project classifies 2-D brain MRI slices into four classes (glioma, meningioma, pituitary tumour and no tumour) with a "
    "classical pipeline: grayscale conversion and resizing, Histogram of Oriented Gradients (HOG) features, feature scaling fitted on training data only, and a linear or RBF-kernel SVM. "
    "The data are a public four-class Kaggle collection whose original train/test folders were found to share near-identical images, so a cluster-disjoint split of 3,295 unique images "
    f"into 2,311 training, 492 validation and 492 test images was used. Three HOG settings and two kernels were compared by 5-fold cross-validation on the training partition and on the "
    f"validation partition; the selected model, an RBF SVM on 8,100 HOG features (128-pixel images, 8-pixel cells), was frozen and evaluated once on the untouched test partition. "
    f"It reached an accuracy of {ACC:.3f} (95% bootstrap interval {ci['accuracy'][0]:.3f}–{ci['accuracy'][1]:.3f}), macro-precision {t['macro_precision']:.3f}, macro-recall {t['macro_recall']:.3f} and "
    f"macro-F1 {MF1:.3f}, against 0.398 for always predicting the most frequent class. Pituitary tumours and gliomas were recognised best, meningioma and no-tumour least well. "
    "Leakage checks found no shared clusters, no identical files and no held-out image above the 0.98 similarity linking threshold, but patient-level independence could not be proven. "
    "The model is also served by a small FastAPI and React web application that performs real SVM inference. This is an academic prototype, not a clinically validated system.", AL.JUSTIFY, 12, line=1.3, after=10)
B.para("**Keywords:** brain tumour MRI, support vector machine, histogram of oriented gradients, RBF kernel, data leakage, near-duplicate detection, healthcare AI, web application", AL.JUSTIFY, 12, after=6)
for el in list(body.iterchildren())[mark:-1]:
    toc_head.addprevious(el)

# ---- CHAPTER 1 ------------------------------------------------------------------------------------------------------------------
B.chapter_heading(1, "INTRODUCTION")
B.h2("1.1", "Background of the selected problem")
B.para("A brain tumour is an abnormal growth of cells in or around the brain. Magnetic resonance imaging (MRI) is one of the main tools used to look at the brain, and automatic "
       "analysis of MRI slices is an active research area. This project works with four image classes: **glioma** and **meningioma** (two common tumour types), **pituitary tumour** (a tumour of "
       "the pituitary gland) and **no tumour**. Assigning one of these labels to a slice is a *multi-class classification* problem.")
B.para("Deep neural networks dominate recent work, but they need large datasets, specialised hardware and careful tuning, and their decisions are hard to inspect. A **Support Vector Machine (SVM)** [1] "
       "is a classical learning method that finds the decision boundary with the widest margin between classes; with a *kernel* it can also draw non-linear boundaries. Applied to hand-crafted "
       "image descriptors, it often forms a strong, fast and transparent baseline on small datasets. Here the descriptor is the **Histogram of Oriented Gradients (HOG)** [2], which summarises "
       "local edge directions in small image cells and is a well-known feature for shape and texture.")
B.para("A second problem concerns evaluation. If the same slice, or a mirrored or re-encoded copy of it, appears in both the training and the test data, any reported score is too optimistic. The "
       "public dataset used here showed exactly this problem, so the project builds on a leakage-aware split and reports what it can and cannot guarantee.")
B.h2("1.2", "Industry Relevance")
B.bullets([
    "**Healthcare AI baselines.** Classical, light-weight classifiers are used as baselines and as fall-back components when GPUs, large datasets or model transparency are limited; a trustworthy baseline is the starting point for judging more complex models.",
    "**Medical-image computing practice.** Duplicate and near-duplicate slices are a known risk when many images come from the same scans; auditing the split before training is a practical, reusable skill.",
    "**Responsible evaluation.** Selecting a model on validation data, evaluating on the test data once, and reporting uncertainty (bootstrap intervals, small classes) are habits expected of healthcare AI work.",
    "**Software delivery.** A trained model, its saved results and a validated API and browser interface show how research output can be exposed for exploration.",
])
B.para("These are research and engineering benefits only. The model and the application are **not approved or validated for clinical use** and must not be used to diagnose or treat patients.")
B.h2("1.3", "Aim and Objective of the Micro Project")
B.para("**Aim.** To build and evaluate, without data leakage, a classical Support Vector Machine pipeline for four-class brain tumour MRI classification, and to deliver it as a documented and tested prototype.")
B.para("The measurable objectives were:")
B.numbered([
    "Reuse the dataset audit and cluster-disjoint split (2,311 / 492 / 492 unique images) and show by checks that clusters, files and near-duplicates do not cross partitions.",
    "Implement a reproducible preprocessing pipeline (grayscale conversion, resizing, HOG features, scaling fitted on training data only).",
    "Train and compare a linear SVM and an RBF-kernel SVM over three HOG settings, tuning by 5-fold cross-validation on the training partition and selecting by validation performance.",
    "Evaluate the frozen selected model once on the untouched test partition and report accuracy, macro precision, macro recall, macro-F1, per-class scores, the confusion matrix and a bootstrap interval.",
    "Save the model, configuration, label mapping, seeds, package versions and predictions, and show that the saved model reloads and predicts consistently.",
    "Provide a small web application with genuine SVM inference, backend tests, a frontend build and an integration smoke test.",
])
B.h2("1.4", "Link to SDG / KITS Technology Mission")
B.para("**UN Sustainable Development Goals.** The project relates most directly to **SDG 3, Good Health and Well-being** (“Ensure healthy lives and promote well-being for all at all ages”) [3]. "
       "Transparent, inexpensive classifiers and careful evaluation methods contribute to the research base of that goal; the project itself makes no claim of health impact. It relates secondarily "
       "to **SDG 9, Industry, Innovation and Infrastructure** (“Build resilient infrastructure, promote inclusive and sustainable industrialization and foster innovation”) [3], through a "
       "reproducible pipeline and a working software prototype. These links concern research direction, not delivered outcomes.")
B.para("**Karunya Institute of Technology and Sciences.** The university’s official site states its mission as raising scientists and entrepreneurs to find solutions, and names food, water, "
       "health care and energy as its product-development focus areas [4]; this project falls under the health care area. The sources consulted (karunya.edu and kcode.karunya.edu) contained no "
       "description of a specific “Technology Mission”, so this report does not describe one and claims no institutional endorsement. *If the course requires a particular Technology Mission "
       "statement, it should be taken from the official document and added here.*")

# ---- CHAPTER 2 ------------------------------------------------------------------------------------------------------------------
B.chapter_heading(2, "LITERATURE REVIEW")
B.para("This chapter reviews the original works on which the project’s methods rest and two studies of classical machine learning on brain MRI. It is a focused review of the verified sources "
       "listed in the reference list, not a systematic survey of the brain-MRI literature.")
B.h2("2.1", "Support Vector Machines")
B.para("Cortes and Vapnik presented the support-vector network as a learning machine for two-group classification: inputs are mapped into a high-dimensional feature space, where a linear decision "
       "surface with a large margin is constructed [1]. The *soft-margin* formulation allows some training errors, controlled by a penalty parameter **C**; a *kernel function* lets the machine work "
       "in the feature space without computing it explicitly. The **linear kernel** gives a linear boundary; the **radial basis function (RBF) kernel** adds a width parameter **gamma** that "
       "sets how far the influence of a single training example reaches. Multi-class problems are handled by combining binary classifiers.")
B.para("The practical guide by Hsu, Chang and Lin [5] recommends scaling the features, trying the RBF kernel and choosing C and gamma by cross-validated grid search, and the library LIBSVM [6] is a "
       "widely used implementation of these methods. **Relevance:** the project follows exactly that recipe: scaled features, linear and RBF kernels and a cross-validated grid. **Unresolved:** a "
       "kernel SVM has no built-in probability or uncertainty estimate and no concept of an input that is not a brain image at all, so its confidence must be interpreted carefully.")
B.h2("2.2", "Histogram of Oriented Gradients")
B.para("Dalal and Triggs introduced the Histogram of Oriented Gradients descriptor for human detection [2]: the image is divided into small cells, each cell collects a histogram of gradient "
       "directions, and groups of cells (blocks) are contrast-normalised before the histograms are concatenated into one feature vector. **Relevance:** HOG captures edge and texture structure "
       "that differs between brain slices, with tolerance to small changes in illumination; the cell size controls the level of detail. **Unresolved:** the descriptor was designed for pedestrian "
       "detection, not for medical images; it encodes no explicit tumour localisation, and its fixed grid is sensitive to slice orientation and position.")
B.h2("2.3", "Classical machine learning on brain MRI")
B.para("Zacharaki and colleagues classified brain tumour type and grade from MRI using tumour shape, intensity and texture features with an SVM and recursive feature elimination, on 102 tumours "
       "evaluated by leave-one-out cross-validation [7]. Cheng and colleagues studied three-class classification (meningioma, glioma, pituitary tumour) of T1-weighted contrast-enhanced MRI with "
       "intensity-histogram, gray-level co-occurrence and bag-of-words features, showing that enlarging the tumour region and splitting it into rings improved accuracy [8]. **Relevance:** both "
       "show that classical features and SVM-type classifiers are credible for this task. **Unresolved:** both rely on tumour regions defined by experts, whereas this project uses whole slices "
       "without a tumour mask; and neither addresses near-duplicate slices between training and test data, which is the evaluation risk examined here.")
B.h2("2.4", "Summary and research gap")
B.table("Summary of the reviewed work and its role in this project.", [
    ["Work", "Key contribution", "Used here as", "Open issue"],
    ["Support-vector network [1]", "Maximum-margin classifier with kernels", "Linear and RBF SVM", "No calibrated confidence or out-of-distribution check"],
    ["Practical SVM guide [5]; LIBSVM [6]", "Scaling, RBF kernel, grid search of C and gamma", "Model-selection recipe", "Grid is coarse; cost grows with features"],
    ["HOG [2]", "Cell-wise gradient-orientation histograms", "Feature extractor", "Designed for pedestrians; no tumour localisation"],
    ["Zacharaki et al. [7]", "Shape/texture features + SVM for tumour type and grade", "Precedent for SVM on brain MRI", "Expert regions; 102 tumours"],
    ["Cheng et al. [8]", "Three-class T1-CE classification with region augmentation", "Precedent for the same three tumour classes", "Needs tumour masks"],
], [1.5, 2.0, 1.55, 1.45], size=9.5)
B.para("**Gap addressed.** The reviewed work supplies the method, but little guidance on whole-slice classification with a *leakage-aware* split. This project therefore asks how well a carefully "
       "tuned HOG + SVM pipeline performs on whole slices when training, validation and test images are separated by near-duplicate cluster, and how much can be said given the remaining uncertainty.")

# ---- CHAPTER 3 ------------------------------------------------------------------------------------------------------------------
B.chapter_heading(3, "METHODOLOGY")
B.figure(FIG / "pipeline_diagram.png", "Classical pipeline and use of the three data partitions.", width=6.2)
B.h2("3.1", "Dataset source and initial structure")
B.para("The data are a four-class brain MRI collection obtained from Kaggle. Its folder structure (Training and Testing, each with glioma, meningioma, notumor and pituitary folders), its 7,200 image files "
       "(1,400 training and 400 testing images per class) and its size (167.85 MB) match the Kaggle page *Brain Tumor MRI Dataset* by Masoud Nickparvar, Version 2 [9], which lists the licence as "
       "**CC BY 4.0** and names three upstream sources: the figshare brain MRI dataset, the SARTAJ dataset and the Br35H dataset. File names carry the prefixes Tr- and Te-, and 203 files carry an *aug* marker, "
       "which the Kaggle page does not mention.")
B.note("Provenance caveats", [
    "The match with the Kaggle page is on checkable counts and size only. **The local download record is unverified**, so it cannot be proved that the files are identical to that version.",
    "The CC BY 4.0 licence is the one shown on the dataset page; the upstream datasets may carry separate terms. **The dataset is not redistributed** with this report or the software; attribution: M. Nickparvar, *Brain Tumor MRI Dataset*, Kaggle.",
    "The page states that Version 2 removed duplicates and eliminated train/test overlap; the near-duplicate audit described next nevertheless found near-identical images across the two folders.",
])
B.h2("3.2", "Data auditing and the leakage-aware split")
B.para("An audit performed earlier on this dataset (and reused here without change) pooled all 7,200 images, compared every image with every other one using a 32×32 mean-removed cosine similarity "
       "over eight orientations (flips, rotations, transposes), and linked images with similarity of at least 0.98 or identical bytes into **clusters**. It found that 1,076 of the 1,600 images of the "
       "original Testing folder had a near-identical copy in the Training folder. After quarantining 207 images (clusters with conflicting class labels, clusters made only of *aug* files and four "
       f"borderline cases) {audit['representatives']:,} unique images remained, one representative per cluster, assigned to train, validation or test by a class-stratified 70/15/15 split with no cluster in two partitions. "
       "This SVM project **reuses that split exactly** (the split manifest in the project, hash-checked in code) and generated no new one.")
pc = audit["partition_class_counts_representatives"]
B.table("Final cluster-disjoint partitions used for the SVM (unique images per class).", [["Partition"] + [CLN[c] for c in CL] + ["Total"]] + [
    [n.capitalize()] + [f"{pc[n][c]:,}" for c in CL] + [f"{sum(pc[n][c] for c in CL):,}"] for n in ("train", "val", "test")],
    [1.3, 1.0, 1.1, 1.1, 1.0, 1.0], size=10, align=["l", "r", "r", "r", "r", "r"])
B.figure(FIG / "class_distribution.png", "Class distribution of the training, validation and test partitions.", width=5.0)
B.note("Residual uncertainty", [
    "The similarity measure is a heuristic with no ground truth. The dataset has **no patient identifiers**, so different slices of the *same patient* cannot be detected and may lie in different "
    "partitions: patient-level independence is **not proven**. Files marked *aug* were removed by name only, and heavily rescaled copies below the threshold would be missed.",
    "Only 3,295 of the 7,200 images are unique and the classes are imbalanced (227 no-tumour training images; 46 each in validation and test).",
], size=10.5)
B.h2("3.3", "Preprocessing and HOG feature extraction")
B.para("Every image is converted to one-channel grayscale, resized with bilinear interpolation to a square (128 or 64 pixels) and scaled to [0, 1]; the same function is used for training, evaluation "
       "and the web application. HOG features are then computed with 9 orientation bins, 2×2-cell blocks and L2-Hys block normalisation (scikit-image [10]). Three settings were compared "
       "(Table 3.2). HOG has no learned parameters, so computing it before cross-validation causes no leakage; the **StandardScaler**, which does learn (means and variances), is placed inside the "
       "pipeline and is fitted on training data only (on the training folds only during cross-validation).")
B.table("HOG settings compared.", [
    ["Variant", "Image size", "Cell size", "Features"],
    ["hog128_cell16", "128×128", "16×16", "1,764"],
    ["hog128_cell8", "128×128", "8×8", "8,100"],
    ["hog64_cell8", "64×64", "8×8", "1,764"],
], [1.8, 1.5, 1.5, 1.2], size=10, align=["l", "c", "c", "r"])
B.figure(FIG / "hog_illustration.png", "Example training images (one per class) as seen by the model, with their HOG descriptors (selected setting). These are real dataset images, shown under the dataset licence (CC BY 4.0 [9]).", width=5.8)
B.h2("3.4", "Linear and RBF support vector machines")
B.para("Both models are scikit-learn *SVC* classifiers [11] (an implementation based on LIBSVM [6]) applied to the scaled HOG vector; four classes are handled internally by one-vs-one voting, and the "
       "decision scores reported by the application are the one-vs-rest aggregation of those votes. The **linear SVM** has one hyper-parameter, C (larger C = fewer margin violations allowed). "
       "The **RBF SVM** uses the kernel k(x, x′) = exp(−γ ‖x − x′‖²) and has C and γ. Both can use class weights inversely proportional to class frequency (‘balanced’) "
       "to counter the class imbalance, or no weights.")
B.h2("3.5", "Hyper-parameter search and model selection")
B.table("Hyper-parameter grids searched for every HOG variant.", [
    ["Kernel", "Grid", "Settings"],
    ["Linear", "C ∈ {10⁻⁵, 10⁻⁴, 10⁻³, 10⁻², 10⁻¹, 1}; class weight ∈ {none, balanced}", "12 × 5 folds = 60 fits"],
    ["RBF", "C ∈ {1, 10, 100}; γ ∈ {0.1, 1, 3} / (number of features); class weight ∈ {none, balanced}", "18 × 5 folds = 90 fits"],
], [0.9, 4.2, 1.4], size=9.5)
B.para("For each HOG variant and kernel, a grid search with **5-fold stratified cross-validation on the training partition** (seed 42, scoring by macro-F1) picked the best setting; that setting was "
       "refit on the whole training partition and scored once on the **validation partition**. The candidate with the highest validation macro-F1 (a tie within 0.002 would have been resolved by the "
       "cross-validation score) became the final model, fitted on the training partition only. The first search was stopped when the linear optimum sat at the lower edge of its C grid; the grid was "
       "extended and the search repeated in full, using training and validation data only. **The test partition is not read by the selection program.**")
B.h2("3.6", "Evaluation protocol and metrics")
B.para("The selected model was evaluated **once** on the 492 test images (the evaluation program refuses a second run). Reported: accuracy, macro-averaged precision, recall and F1 (every class counts "
       "equally, which matters for the small no-tumour class), per-class precision, recall and F1, the confusion matrix, and a 95% interval obtained by resampling the test predictions 2,000 times "
       "(seed 42). One-vs-rest sensitivity and specificity, and tumour-versus-no-tumour sensitivity and specificity, were *derived* from the saved predictions. A trivial baseline, always predicting the most "
       "frequent class, is given for reference. Runtimes were measured on the evaluation machine.")
B.h2("3.7", "Software and hardware")
pk = cfg["packages"]
B.table("Software and hardware.", [
    ["Item", "Setting"],
    ["Hardware", "Apple MacBook Air, M4 chip, 16 GB unified memory, macOS (CPU only; no GPU was used)"],
    ["Software", f"Python {pk['python']}, scikit-learn {pk['scikit-learn']} [11], scikit-image {pk['scikit-image']} [10], NumPy {pk['numpy']}, SciPy {pk['scipy']}, joblib {pk['joblib']}, pandas {pk['pandas']}"],
    ["Randomness", "Seed 42 for cross-validation folds and bootstrap; SVC training is deterministic"],
], [1.5, 5.0], size=9.5)
B.h2("3.8", "Ethical considerations and evaluation limitations")
B.bullets([
    "**Not a medical device.** No component was tested clinically or reviewed by clinicians. Predictions must not guide diagnosis or treatment.",
    "**Data and privacy.** The dataset is public and comes without patient identifiers or consent records that this project could inspect; patient-level grouping was therefore impossible. The images are used under the CC BY 4.0 licence shown on the Kaggle page (upstream terms may differ) and are not redistributed. The web application processes uploads locally and does not store them.",
    "**Label noise and bias.** Eight near-duplicate clusters (30 images) carried conflicting class labels, which indicates label noise in the source data. The classes are imbalanced and the data come from limited sources, so performance on other scanners or populations is unknown.",
    "**Metric limits.** The test set is small (492 images; 46 no-tumour), the result is a single training run per configuration, and the intervals describe test-sampling variability only.",
    "**Honest reporting.** Choices that were changed during the work (the extended grid) are stated; no test result was used to choose anything.",
])

# ---- CHAPTER 4 ------------------------------------------------------------------------------------------------------------------
B.chapter_heading(4, "FABRICATION / SIMULATION / PROGRAM OR CODE / DESIGN")
B.para("This chapter describes what was implemented. The SVM experiment and the web application live in a separate working copy of an earlier GAN-based project; the copied GAN code and results "
       "are kept only as reference and none of them is used for the SVM results.")
B.h2("4.1", "Code components")
B.table("SVM code components (folder svm_variant/).", [
    ["File", "Responsibility"],
    ["svm_lib.py", "Maps the saved split to image paths (representatives only, hash-checked); grayscale/resize function; HOG transformer; saved-model loader and single-image prediction"],
    ["train_select.py", "Grid search with training-only cross-validation for each HOG variant and kernel; validation scoring; selection rule; saves the model, configuration and selection tables. Reads only train and validation data"],
    ["evaluate_test.py", "Single evaluation on the test partition; metrics, confusion matrix, bootstrap interval; reload and consistency checks; refuses a second run; records the model’s SHA-256"],
    ["leakage_evidence.py", "Cluster, byte-identity and nearest-similarity audit of the split and run-order evidence"],
    ["make_figures.py", "All result figures, generated only from saved outputs"],
    ["webapp/", "SVM-only FastAPI backend, React/TypeScript frontend, tests, launcher and smoke test"],
], [1.7, 4.8], size=9.5)
B.h2("4.2", "Training, saving and reloading the model")
cfgrows = [["Item", "Value"],
           ["Selected model", f"{cfg['kernel'].upper()} SVM on {cfg['hog_variant']}: {cfg['image_size']}×{cfg['image_size']} images, {cfg['n_features']:,} HOG features"],
           ["Parameters", f"C = {cfg['svc_params']['C']:g}, gamma = 1 / {cfg['n_features']:,} (= {cfg['svc_params']['gamma']:.3e}), class weight = {cfg['svc_params']['class_weight'] or 'none'}"],
           ["Support vectors", f"{cfg['n_support_vectors']:,} of 2,311 training images"],
           ["Fitted on", "training partition only; StandardScaler fitted on training data only"],
           ["Label mapping", "glioma = 0, meningioma = 1, no tumour = 2, pituitary = 3"],
           ["Saved files", "outputs/svm_variant/model/svm_model.joblib and model_config.json; selection tables; test predictions"]]
B.table("The final saved model.", cfgrows, [1.5, 5.0], size=9.5)
B.para("The saved bundle contains the fitted scaler-and-SVC pipeline, the configuration, the class order and the package versions. The evaluation program reloads it from disk, checks that the test file list "
       "matches the recorded split and does not overlap training or validation files, and verifies that the single-image path used by the web application gives the same label as batch prediction for the "
       "first 60 test images (it did). It also records that the argmax of the decision scores agrees with the predicted label for 99.8% of test images; the application reports the label returned by the SVM.")
B.h2("4.3", "Leakage guards built into the code")
B.bullets([
    "Cross-validation, scaling and grid search use training data only; the selection program loads only the training and validation partitions and records that it did not read the test partition.",
    "The selected model is written to disk before the test partition is read; the test evaluation lock prevents a second evaluation, and the SHA-256 of the evaluated model is stored.",
    "File lists of the three partitions are hashed and compared with the recorded split; disjointness is asserted.",
    "The web application refuses to load any model file whose SHA-256 differs from the evaluated model.",
])
B.h2("4.4", "SVM web application: architecture")
B.para("The application (folder svm_variant/webapp/) is a two-tier local application. It was adapted from the layout of the earlier project’s application, but its backend contains **only the SVM**: the "
       "image generator and the third-party classifier of the earlier application are not part of it, and there is no generation endpoint.")
B.figure(ASSET / "svm_app_architecture.png", "Software architecture of the SVM web application.", width=5.4)
B.table("Technology stack, as recorded in the requirement and package files.", [
    ["Layer", "Technology (version)"],
    ["Frontend", "React 19.2, TypeScript 6.0, Vite 8.3, React Router 7.18, Tailwind CSS 4.3 with shadcn/ui (Radix), Recharts 3.10"],
    ["Backend API", "Python, FastAPI 0.143 with Uvicorn 0.54, Pydantic 2.14"],
    ["Inference", "scikit-learn 1.9.1, scikit-image 0.26.0, NumPy, Pillow 12.2, joblib (CPU)"],
    ["Testing", "pytest 9.1 with the FastAPI test client; a shell integration smoke test; the TypeScript/Vite production build"],
], [1.5, 5.0], size=9.5)
B.h2("4.5", "FastAPI backend")
B.table("API endpoints.", [
    ["Endpoint", "Responsibility"],
    ["GET /api/health", "Liveness and the research-prototype disclaimer"],
    ["GET /api/models/status", "Whether the SVM loaded; kernel, parameters, support vectors, model SHA-256 and whether it equals the evaluated model"],
    ["POST /api/classify", "Accepts a PNG or JPEG; returns the predicted class, the four SVM decision scores, the margin over the runner-up, timing and caveats"],
    ["GET /api/metrics", "Test metrics, confusion matrix, selection table, read from the saved result files"],
    ["GET /api/experiment", "Method, dataset and provenance notes, leakage evidence, limitations"],
    ["GET /api/gallery (+ /image/{id})", "A fixed registry of figures generated from the saved outputs; no arbitrary file access"],
], [2.0, 4.5], size=9.5)
B.para("**Model loading.** The SVM is loaded once, on first use, behind a lock. If the file is missing, if the model has not been evaluated, or if its SHA-256 differs from the evaluated model, the "
       "classifier is reported as unavailable with the reason; **no substitute is used and nothing is simulated**. The decision scores are not probabilities and are labelled as such.")
B.table("Input validation and error handling.", [
    ["Case", "Behaviour"],
    ["Not an image / unsupported format (e.g. GIF, text)", "not_an_image (415) / unsupported_type (415)"],
    ["Empty file; file larger than 10 MB", "empty_file (400); file_too_large (413)"],
    ["Image sides below 32 or above 8,192 pixels", "bad_dimensions (422)"],
    ["Model unavailable or mismatched", "classifier_unavailable (503) with the reason"],
    ["Saved result file missing", "metrics_unavailable / experiment_unavailable (503)"],
    ["Request from another origin", "Blocked by CORS (only the local Vite origin is allowed)"],
], [3.0, 3.5], size=9.5)
B.h2("4.6", "React + TypeScript frontend")
B.para("Four pages: **Dashboard** (key test metrics with intervals, model-selection and per-class charts, model readiness), **Classify MRI** (drag-and-drop or file-picker upload, preview, predicted class with "
       "decision scores, and the model’s measured test performance beside every prediction), **SVM results** (metric table, confusion matrix, per-class table, selection chart, method, leakage checks, limitations) "
       "and **Figures**. Every page carries the research-prototype notice. Figures 4.2 to 4.5 are screenshots of the running application captured for this report.")
B.figure(SHOT / "svm_app_dashboard.png", "SVM dashboard (screenshot).", width=5.3)
B.figure(SHOT / "svm_app_classify.png", "Classify page with a dataset test image: real SVM output with decision scores and caveats. A demonstration of the application, not an evaluation result.", width=5.3)
B.figure(SHOT / "svm_app_results.png", "SVM results page (screenshot): test metrics, confusion matrix and per-class table.", width=5.3)
B.figure(SHOT / "svm_app_gallery.png", "Figures page (screenshot).", width=5.3)
B.h2("4.7", "Local startup procedure")
B.para("After the one-time setup (a Python virtual environment with the pinned requirements and *npm install* for the frontend) and after the model has been trained and evaluated, the application is started "
       "from the project root with one command:")
B.para("./svm_variant/webapp/run_dev.sh", AL.CENTER, 11, bold=True, after=4)
B.para("The backend listens on http://127.0.0.1:8000 (API documentation at /docs) and the frontend on http://localhost:5173. The launcher stops with a clear message if the model or an environment is missing "
       "or if a port is in use (the earlier project’s application uses the same ports, so both must not run together).")
B.h2("4.8", "Tests performed")
B.table("Tests and recorded outcomes.", [
    ["Test", "What it checks", "Outcome"],
    ["Backend pytest (13 tests)", "Health; the real model loads and equals the evaluated file; metrics endpoint equals the saved files and the saved predictions; classification equals the library prediction for one image of every class; PNG/JPEG uploads; error cases; no generation endpoint; missing or tampered model reported, not substituted; gallery path traversal blocked; CORS; limitations and leakage evidence present; no hard-coded user paths", "13 passed"],
    ["Integration smoke test (7 checks)", "Through the Vite proxy: page served, health, SVM available and matching, metrics equal the saved file, real classification, rejection of a text file, no generator endpoint", "7/7 passed"],
    ["Frontend production build", "TypeScript type-check and Vite build", "Completed without errors"],
    ["Experiment checks", "Model saved and reloaded; test list matches the recorded split; single-image path equals batch prediction; second test evaluation refused", "All passed"],
], [1.55, 3.55, 1.4], size=9)
B.para("There is **no automated browser-level test suite**; the screenshots in this chapter come from manual use of the running application. Outputs produced during these tests are plumbing checks and are not scientific results.")

# ---- CHAPTER 5 ------------------------------------------------------------------------------------------------------------------
B.chapter_heading(5, "RESULTS AND INTERPRETATION")
B.para("All numbers in this chapter are read from the saved SVM outputs (outputs/svm_variant/). Sensitivity and specificity are derived from the saved test predictions.")
B.h2("5.1", "Leakage checks")
vs, ts = leak["max_similarity_of_val_and_test_images_to_train_images"]["val"], leak["max_similarity_of_val_and_test_images_to_train_images"]["test"]
B.table("Evidence about leakage between the partitions.", [
    ["Check", "Result"],
    ["Clusters with images in more than one partition", f"0 of {leak['n_clusters_checked']:,}"],
    ["Train, validation and test file lists disjoint", "Yes"],
    ["Byte-identical files shared (train–val / train–test / val–test)", ", ".join(str(v) for v in leak["byte_identical_files_shared_between_partitions"].values())],
    ["Maximum similarity of a validation / test image to any training image", f"{vs['max_similarity_to_any_train_image']:.3f} / {ts['max_similarity_to_any_train_image']:.3f} (linking threshold 0.98)"],
    ["Images with similarity ≥ 0.98 / ≥ 0.97 / ≥ 0.95 (validation)", f"{vs['n_ge_0.98']} / {vs['n_ge_0.97']} / {vs['n_ge_0.95']} of {vs['n']}"],
    ["Images with similarity ≥ 0.98 / ≥ 0.97 / ≥ 0.95 (test)", f"{ts['n_ge_0.98']} / {ts['n_ge_0.97']} / {ts['n_ge_0.95']} of {ts['n']}"],
    ["Median nearest-training similarity (validation / test)", f"{vs['median']:.3f} / {ts['median']:.3f}"],
    ["Model written before the test evaluation; test run refuses a repeat; scaler fitted on training data only", "Yes"],
], [4.1, 2.4], size=9.5)
B.figure(FIG / "leakage_similarity_hist.png", "Re-measured similarity of each validation and test image to its closest training image.", width=5.0)
B.para("No cluster, file or near-duplicate (at the 0.98 threshold) crosses a partition. The histogram also shows that many held-out images have a *similar-looking* training slice (a median of about 0.94 at "
       "32×32 pixels); in the earlier audit\u2019s higher-resolution re-check, pairs of this kind scored about 0.94, i.e. similar but distinct scans. This is the part of the leakage risk that the method cannot rule out: "
       "neighbouring slices of the same patient. **Patient-level independence is not proven**, so the test scores may be somewhat optimistic.")
B.h2("5.2", "Model selection: linear versus RBF kernel")
rows = [["HOG variant", "Kernel", "Best C", "Best gamma × features", "CV macro-F1", "Val. macro-F1", "Val. accuracy"]]
for c in cand:
    bp = c["best_params"]
    rows.append([c["hog_variant"], c["kernel"].upper(), f"{bp['C']:g}", (f"{bp['gamma'] * c['n_features']:.1f}" if c["kernel"] == "rbf" else "–"), f3(c["cv_macro_f1"]), f3(c["val_macro_f1"]), f3(c["val_accuracy"])])
B.table("The six candidate models: best grid setting of each (training cross-validation and validation).", rows, [1.35, 0.7, 0.6, 1.25, 0.9, 0.95, 0.95], size=9, align=["l", "c", "c", "c", "c", "c", "c"],
        bold_rows=(next(i for i, c in enumerate(cand, 1) if (c["hog_variant"], c["kernel"]) == (sc["hog_variant"], sc["kernel"])),))
B.figure(FIG / "model_selection.png", "Cross-validation and validation macro-F1 of the six candidates.", width=5.6)
B.para(f"The **RBF kernel beat the linear kernel for every HOG setting** on validation macro-F1 (by {rbf_gain['hog128_cell16']:.3f}, {rbf_gain['hog128_cell8']:.3f} and {rbf_gain['hog64_cell8']:.3f} for the 128/16, 128/8 and 64/8 settings) and on "
       f"cross-validation. Finer HOG cells helped (8,100 features beat 1,764 for both kernels at 128 pixels), and 128-pixel images beat 64-pixel images. The best candidate, the RBF SVM on "
       f"{sc['hog_variant']}, has a validation macro-F1 of {sc['val_macro_f1']:.3f} and a cross-validation macro-F1 of {sc['cv_macro_f1']:.3f}; it was selected and frozen. In the RBF grid the best setting (C = 10, "
       "gamma = 1/number of features) has an interior gamma; C = 10 and C = 100 give the same cross-validation macro-F1 (0.846), a smaller gamma scores 0.834 and a larger gamma drops to 0.720 (Figure 5.3).")
B.figure(FIG / "rbf_cv_heatmap.png", "Cross-validation macro-F1 over the RBF grid for the selected HOG setting.", width=3.9)
B.h2("5.3", "Test results of the selected model")
rows = [["Metric", "Value", "95% bootstrap interval"],
        ["Accuracy", f3(ACC), f"{ci['accuracy'][0]:.3f} to {ci['accuracy'][1]:.3f}"],
        ["Balanced accuracy", f3(t["balanced_accuracy"]), "–"],
        ["Macro precision", f3(t["macro_precision"]), "–"],
        ["Macro recall", f3(t["macro_recall"]), "–"],
        ["Macro-F1", f3(MF1), f"{ci['macro_f1'][0]:.3f} to {ci['macro_f1'][1]:.3f}"],
        ["Weighted F1", f3(t["weighted_f1"]), "–"],
        ["Always-predict-glioma baseline accuracy", f3(t["majority_class_baseline_accuracy"]), "–"]]
B.table(f"Test-set metrics (n = {t['n_test']}; evaluated once).", rows, [3.0, 1.4, 2.1], size=10.5, align=["l", "c", "c"])
B.figure(FIG / "confusion_matrix_test.png", "Test confusion matrix of the selected model (counts and row-normalised).", width=5.8)
pcr = [["Class (test n)", "Precision", "Recall (sensitivity)", "F1", "Specificity"]]
for c in CL:
    v = t["per_class"][c]
    pcr.append([f"{CLN[c]} ({v['support']})", f"{v['precision']:.3f}", f"{v['recall']:.3f}", f"{v['f1']:.3f}", f"{v['specificity_ovr']:.3f}"])
B.table("Per-class results on the test partition (sensitivity and specificity are one-vs-rest values derived from the saved predictions).", pcr, [1.8, 1.1, 1.5, 1.0, 1.1], size=10, align=["l", "c", "c", "c", "c"])
B.figure(FIG / "per_class_metrics_test.png", "Per-class precision, recall and F1 on the test partition.", width=5.4)
B.h2("5.4", "Interpretation")
B.para(f"The model classified {492 - errors} of 492 test images correctly ({ACC:.1%}; {errors} errors), more than twice the accuracy of always predicting the most frequent class ({t['majority_class_baseline_accuracy']:.1%}), with a 95% interval "
       f"of {ci['accuracy'][0]:.3f}–{ci['accuracy'][1]:.3f}. **Pituitary tumours** were recognised best (recall {t['per_class']['pituitary']['recall']:.2f}, F1 {t['per_class']['pituitary']['f1']:.2f}) and "
       f"**gliomas** next (recall {t['per_class']['glioma']['recall']:.2f}, F1 {t['per_class']['glioma']['f1']:.2f}). **Meningioma** was the hardest tumour class (recall {t['per_class']['meningioma']['recall']:.2f}): the largest "
       f"confusions were {off[0][1]} predicted as {off[0][2]} ({off[0][0]} images), and {off[1][1]} predicted as {off[1][2]} ({off[1][0]}), with {off[2][1]} predicted as {off[2][2]} ({off[2][0]}) close behind. "
       f"**No tumour** has the lowest precision ({t['per_class']['notumor']['precision']:.2f}): of the {cm[0][2] + cm[1][2] + cm[2][2] + cm[3][2]} images predicted as no-tumour, {cm[0][2] + cm[1][2] + cm[3][2]} were tumours "
       f"(glioma {cm[0][2]}, meningioma {cm[1][2]}, pituitary {cm[3][2]}); its recall is {t['per_class']['notumor']['recall']:.2f} on only 46 images, so these estimates are very uncertain.")
tv = t["tumour_vs_notumor"]
B.para(f"Treating the three tumour classes as one “tumour” class, the model found {tv['sensitivity']:.3f} of the {tv['n_tumour']} tumour-bearing images (sensitivity) and kept {tv['specificity']:.3f} of the "
       f"{tv['n_notumor']} no-tumour images out of the tumour classes (specificity). These derived values rest on 46 no-tumour images and are not clinical performance estimates.")
B.para(f"Validation accuracy of the selected model was {sc['val_accuracy']:.3f}, higher than the test accuracy {ACC:.3f}; a difference of this size (about {100 * (sc['val_accuracy'] - ACC):.1f} points) is within the sampling "
       "interval of a 492-image set, and the validation score is also expected to be slightly optimistic because the validation set was used to choose among six candidates. The test figure is the one to quote.")
B.figure(FIG / "misclassified_examples.png", "The first 12 of the misclassified test images, in split-manifest order (real dataset images, CC BY 4.0 [9]).", width=5.8)
B.h2("5.5", "Runtime")
rt = t["runtime_seconds"]
B.para(f"Training the final model on 2,311 images took {rt['fit_final_model']:.1f} s on the CPU, and the full grid searches took between about 40 s and 7 min per HOG variant and kernel (Table 3.3 lists the grids). On the test set, "
       f"loading and resizing took {rt['image_loading_test']:.2f} s, HOG extraction {rt['hog_extraction_test']:.2f} s and scaling plus SVM prediction {rt['scaler_plus_svm_prediction_test']:.2f} s: about {rt['per_image_total_ms']:.0f} ms per image in total.")
B.h2("5.6", "Application implementation and testing results")
B.para("The web application was implemented as described in Chapter 4 and tested as listed in Table 4.6: 13 backend tests passed, the 7-check smoke test passed and the frontend production build completed. The tests show that the "
       "application serves the saved metrics unchanged, runs the real saved SVM (the one that was evaluated) and rejects invalid input; they do not measure the scientific quality of the model. A confident output on "
       "a single image in the Classify page is a plumbing check and **not evidence of clinical accuracy**. There is no automated browser-level test suite.")
B.h2("5.7", "What the results support and do not support")
B.table("Summary of supported and unsupported statements.", [
    ["Supported by the results", "Not supported"],
    ["An RBF SVM on HOG features separates the four classes well above chance on this split (test accuracy 0.866, macro-F1 0.841)", "That the model is clinically useful or diagnostic"],
    ["RBF beat linear, and finer HOG cells beat coarser ones, on training CV and validation", "That the same ranking holds on other data, scanners or HOG parameters"],
    ["The split has no shared clusters or files and no held-out image above the 0.98 similarity threshold", "That the result is free of patient-level leakage"],
    ["Pituitary and glioma are recognised best; meningioma and no-tumour are the weakest", "Precise per-class estimates for no-tumour (46 test images)"],
    ["The web application runs the real evaluated SVM and shows its saved results", "That an uploaded image outside the dataset (or a non-MRI) is handled safely"],
], [3.3, 3.2], size=9.5)

# ---- CHAPTER 6 ------------------------------------------------------------------------------------------------------------------
B.chapter_heading(6, "CONCLUSION AND FUTURE SCOPE")
B.h2("6.1", "Conclusion")
B.para(f"This micro project built a classical pipeline for four-class brain tumour MRI classification: grayscale conversion, HOG features, scaling fitted on training data only and a Support Vector Machine. On a "
       f"cluster-disjoint split of 3,295 unique images, the best of six candidates by validation performance was an **RBF SVM on 8,100 HOG features** (128-pixel images, 8-pixel cells; C = 10). Evaluated once on the untouched "
       f"test partition it reached an accuracy of **{ACC:.3f}** (95% interval {ci['accuracy'][0]:.3f}–{ci['accuracy'][1]:.3f}) and a macro-F1 of **{MF1:.3f}**, with pituitary tumours and gliomas recognised best "
       "and meningioma and no-tumour least well. The RBF kernel outperformed the linear kernel throughout. Checks showed no shared clusters, identical files or above-threshold near-duplicates between partitions, "
       "but patient-level independence could not be established. A small web application serves the saved results and real SVM predictions. The work is an academic prototype and is not clinically validated.")
B.h2("6.2", "Ethics, privacy and patient-safety considerations")
B.bullets([
    "Predictions are not diagnoses; any clinical use would need validation on independent, patient-level-separated data, regulatory review and clinician oversight.",
    "The data carry no patient identifiers here; the application processes uploads locally and stores nothing, but any real deployment would need a privacy and consent assessment.",
    "An SVM returns scores, not calibrated probabilities, and has no out-of-distribution detection, so non-MRI or unusual images still receive a tumour label; this is displayed in the interface.",
    "Class imbalance and label noise in the source data could bias results against rarer groups.",
])
B.h2("6.3", "Limitations")
B.bullets([
    "Small, imbalanced test set (492 images; 46 no-tumour); one training run per configuration; intervals describe test-sampling variability only.",
    "Patient-level independence unproven; near-duplicate detection is heuristic. The dataset download record is unverified and its upstream sources may have separate terms.",
    "Whole 2-D slices without tumour masks; HOG is not designed for medical images; only three HOG settings and a coarse grid were searched.",
    "No external validation; no out-of-distribution handling; no automated browser-level tests.",
])
B.h2("6.4", "Future scope")
B.bullets([
    "Use larger, more diverse data with patient identifiers so that splits can be made at patient level, and validate on an independent site.",
    "Add richer features (texture, wavelets, learned features) and a broader search, and compare with other classical models and with neural networks under the same split.",
    "Calibrate the scores, add out-of-distribution detection and report uncertainty per prediction.",
    "Use tumour-region information where masks exist, and evaluate class-wise clinical metrics with expert review.",
    "Add automated browser-level tests; before any healthcare use, conduct clinical validation, regulatory review and privacy assessment.",
])

# ---- REFERENCES -----------------------------------------------------------------------------------------------------------------
B.para("REFERENCES", AL.CENTER, 14, True, before=0, after=10, page_break=True, outline=0)
refs = [
    "C. Cortes and V. Vapnik, “Support-vector networks,” *Machine Learning*, vol. 20, pp. 273–297, 1995. doi:10.1007/BF00994018.",
    "N. Dalal and B. Triggs, “Histograms of oriented gradients for human detection,” in *Proc. IEEE Conference on Computer Vision and Pattern Recognition (CVPR)*, 2005. doi:10.1109/CVPR.2005.177.",
    "United Nations, “Transforming our world: the 2030 Agenda for Sustainable Development,” 2015. https://sdgs.un.org/2030agenda",
    "Karunya Institute of Technology and Sciences, official website (mission statement and focus areas). https://www.karunya.edu/ and https://kcode.karunya.edu/about-us (accessed 27 October 2026).",
    "C.-W. Hsu, C.-C. Chang and C.-J. Lin, “A practical guide to support vector classification,” technical guide, National Taiwan University (first version 2003; later revised). https://www.csie.ntu.edu.tw/~cjlin/",
    "C.-C. Chang and C.-J. Lin, “LIBSVM: a library for support vector machines,” *ACM Transactions on Intelligent Systems and Technology*, vol. 2, no. 3, article 27, 2011. doi:10.1145/1961189.1961199.",
    "E. I. Zacharaki *et al.*, “Classification of brain tumor type and grade using MRI texture and shape in a machine learning scheme,” *Magnetic Resonance in Medicine*, vol. 62, no. 6, pp. 1609–1618, 2009. doi:10.1002/mrm.22147.",
    "J. Cheng *et al.*, “Enhanced performance of brain tumor classification via tumor region augmentation and partition,” *PLoS ONE*, vol. 10, no. 10, e0140381, 2015. doi:10.1371/journal.pone.0140381.",
    "M. Nickparvar, “Brain Tumor MRI Dataset,” Kaggle, Version 2, licence CC BY 4.0. https://www.kaggle.com/datasets/masoudnickparvar/brain-tumor-mri-dataset (accessed October 2026). Compiled from the figshare, SARTAJ and Br35H datasets.",
    "S. van der Walt *et al.*, “scikit-image: image processing in Python,” *PeerJ*, vol. 2, e453, 2014. doi:10.7717/peerj.453.",
    "F. Pedregosa *et al.*, “Scikit-learn: machine learning in Python,” *Journal of Machine Learning Research*, vol. 12, pp. 2825–2830, 2011.",
]
for i, r_ in enumerate(refs, 1):
    p = B.para("", AL.JUSTIFY, 11, after=4, left=0.45, first=-0.45, line=1.1)
    from report_lib import rich
    rich(p, f"[{i}] " + r_, 11)

# ---- TOC numbers, sections, footer, evaluation page ------------------------------------------------------------------------------
toc_pages = json.load(open(TOC_JSON)) if TOC_JSON.exists() else {}
from docx.table import _Cell
tbl = doc.tables[0]
last = tbl.rows[-1]._tr
new_tr = copy.deepcopy(last)
last.addnext(new_tr)
TC = qn("w:tc")
for ri, tr in enumerate(tbl.rows):
    tcs = [_Cell(tc, tbl) for tc in tr._tr.findall(TC)]
    title_cell, page_cell = tcs[-2], tcs[-1]
    if tr._tr is new_tr:
        set_text(title_cell.paragraphs[0], "REFERENCES")
        if tcs[0].paragraphs[0].runs:
            set_text(tcs[0].paragraphs[0], "")
    if ri == 0:
        continue
    label = tcs[1].text.strip() if len(tcs) == 4 else tcs[-2].text.strip()
    pg = toc_pages.get(label)
    if pg:
        set_text(page_cell.paragraphs[0], str(pg))

final_sect = body.find(qn("w:sectPr"))
sect1 = copy.deepcopy(final_sect)
pg_num = sect1.find(qn("w:pgNumType")); pg_num.set(qn("w:fmt"), "lowerRoman"); pg_num.set(qn("w:start"), "1")
sect1.append(OxmlElement("w:titlePg"))
ppr = section_break_par.find(qn("w:pPr"))
if ppr is None:
    ppr = OxmlElement("w:pPr"); section_break_par.insert(0, ppr)
ppr.append(sect1)
footer = doc.sections[-1].footer
fp = footer.add_paragraph(); fp.alignment = AL.CENTER
run = fp.add_run()
for kind, txt in (("begin", None), ("instr", " PAGE "), ("end", None)):
    if kind == "instr":
        el = OxmlElement("w:instrText"); el.set(qn("xml:space"), "preserve"); el.text = txt
    else:
        el = OxmlElement("w:fldChar"); el.set(qn("w:fldCharType"), kind)
    run._r.append(el)
run.font.name, run.font.size = "Times New Roman", Pt(11)

final_el = body.find(qn("w:sectPr"))
epPr = eval_block[0].find(qn("w:pPr"))
if epPr is None:
    epPr = OxmlElement("w:pPr"); eval_block[0].insert(0, epPr)
epPr.append(OxmlElement("w:pageBreakBefore"))
for el in eval_block:
    final_el.addprevious(el)

doc.core_properties.title = TITLE
doc.core_properties.author = ""
doc.core_properties.subject = "25AI2004 Artificial Intelligence in Healthcare: micro project e-report"
doc.save(OUT)
print("saved", OUT)
