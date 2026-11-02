#!/usr/bin/env python3
"""Build SVM_Project_Presentation.pptx (14 slides, 16:9) from the SVM results. Numbers are read from outputs/svm_variant/. No training or evaluation here."""
import json, math
from pathlib import Path
from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor as C
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches as I, Pt

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SV = ROOT / "outputs/svm_variant"
FIG = SV / "figures"
SHOT = SV / "report/assets/screenshots"
ASSET = SV / "report/assets"
EXP = ROOT / "outputs/deduplicated_experiment"
OUT = SV / "presentation/SVM_Project_Presentation.pptx"

NAVY, TEAL, INK, MUTED = C(0x1F, 0x3A, 0x5F), C(0x2A, 0x9D, 0x8F), C(0x14, 0x21, 0x3D), C(0x55, 0x60, 0x70)
LIGHT, AMBERF, AMBERL, WHITE, BG = C(0xEE, 0xF2, 0xF6), C(0xFD, 0xF1, 0xDC), C(0xC9, 0x8A, 0x1A), C(255, 255, 255), C(0xF6, 0xF8, 0xFA)
MINT = C(0xE4, 0xF2, 0xF0)
FONT = "Calibri"
pm = "±"

t = json.load(open(SV / "test/test_evaluation.json"))
sel = json.load(open(SV / "selection/selection.json"))
cfg = json.load(open(SV / "model/model_config.json"))
leak = json.load(open(SV / "leakage_evidence.json"))
audit = json.load(open(EXP / "dedup_audit_summary.json"))
cand = sel["candidates"]
sc = sel["selected"]
ci = t["bootstrap_95ci_2000_resamples_of_test_predictions"]
cm = t["confusion_matrix"]["counts"]
CL = ["glioma", "meningioma", "notumor", "pituitary"]
CLN = {"glioma": "Glioma", "meningioma": "Meningioma", "notumor": "No tumour", "pituitary": "Pituitary"}
STU = "[Student name \u2013 to be filled in]"
REG = "[Register number \u2013 to be filled in]"

prs = Presentation()
prs.slide_width, prs.slide_height = I(13.333), I(7.5)
BLANK = prs.slide_layouts[6]
overflow = []
SL = []


def est_lines(text, w_in, size):
    cpl = max(1, int(w_in * 72 / (size * 0.50)))
    return sum(max(1, math.ceil(len(p) / cpl)) for p in text.split("\n"))


def bg(slide, color=BG):
    f = slide.background.fill
    f.solid(); f.fore_color.rgb = color


def text(slide, x, y, w, h, paras, size=16, color=INK, bold_first=False, bullet=False, fill=None, line=None, anchor=MSO_ANCHOR.TOP, align=PP_ALIGN.LEFT, shape=False, space=5):
    if fill is not None or line is not None or shape:
        s = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, I(x), I(y), I(w), I(h))
        s.adjustments[0] = 0.04
        if fill is not None:
            s.fill.solid(); s.fill.fore_color.rgb = fill
        else:
            s.fill.background()
        if line is not None:
            s.line.color.rgb = line; s.line.width = Pt(1.5)
        else:
            s.line.fill.background()
        s.shadow.inherit = False
    else:
        s = slide.shapes.add_textbox(I(x), I(y), I(w), I(h))
    tf = s.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = I(0.12)
    tf.margin_top = tf.margin_bottom = I(0.06)
    tot = 0.0
    for i, para in enumerate(paras):
        txt, sz, b, col = (para, size, False, color) if isinstance(para, str) else (para + (None,) * (4 - len(para)))[:4]
        sz = sz or size
        col = col or color
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(space)
        r = p.add_run()
        r.text = ("•  " if bullet and not (bold_first and i == 0) and not b else "") + txt
        r.font.size, r.font.name, r.font.color.rgb = Pt(sz), FONT, col
        r.font.bold = bool(b or (bold_first and i == 0))
        tot += est_lines(r.text, w - 0.3, sz) * sz * 1.2 / 72 + space / 72
    if tot > h + 0.05:
        overflow.append((len(SL), round(tot, 2), h, str(paras[0])[:40]))
    return s


def pic(slide, path, x, y, w, h):
    iw, ih = Image.open(path).size
    sc = min(w / iw, h / ih)
    pw, ph = iw * sc, ih * sc
    slide.shapes.add_picture(str(path), I(x + (w - pw) / 2), I(y + (h - ph) / 2), I(pw), I(ph))
    return pw, ph


def table(slide, rows, x, y, w, colw, size=12, rowh=0.36, bold_rows=(), align=None):
    t = slide.shapes.add_table(len(rows), len(rows[0]), I(x), I(y), I(w), I(rowh * len(rows))).table
    for j, cw in enumerate(colw):
        t.columns[j].width = I(cw)
    est = 0.0
    for i, row in enumerate(rows):
        t.rows[i].height = I(rowh)
        mx = 1
        for j, cell in enumerate(row):
            c = t.cell(i, j)
            c.text = str(cell)
            c.margin_left = c.margin_right = I(0.07); c.margin_top = c.margin_bottom = I(0.03)
            for p in c.text_frame.paragraphs:
                if align and align[j] == "c":
                    p.alignment = PP_ALIGN.CENTER
                for r in p.runs:
                    r.font.size, r.font.name = Pt(size), FONT
                    r.font.bold = (i == 0) or (i in bold_rows)
                    r.font.color.rgb = WHITE if i == 0 else INK
            c.fill.solid(); c.fill.fore_color.rgb = NAVY if i == 0 else (LIGHT if i % 2 else WHITE)
            mx = max(mx, est_lines(str(cell), colw[j] - 0.16, size))
        est += max(rowh, mx * size * 1.2 / 72 + 0.08)
    return est


def new_slide(title, notes_text=""):
    s = prs.slides.add_slide(BLANK)
    SL.append(s)
    bg(s)
    bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, I(0.95))
    bar.fill.solid(); bar.fill.fore_color.rgb = NAVY; bar.line.fill.background(); bar.shadow.inherit = False
    acc = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, I(0.95), prs.slide_width, I(0.05))
    acc.fill.solid(); acc.fill.fore_color.rgb = TEAL; acc.line.fill.background(); acc.shadow.inherit = False
    tb = s.shapes.add_textbox(I(0.5), I(0.1), I(12.3), I(0.78))
    tf = tb.text_frame; tf.word_wrap = True; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    r = tf.paragraphs[0].add_run(); r.text = title
    r.font.size, r.font.bold, r.font.name, r.font.color.rgb = Pt(28), True, FONT, WHITE
    ft = s.shapes.add_textbox(I(0.5), I(7.08), I(12.3), I(0.3))
    fr = ft.text_frame.paragraphs[0].add_run()
    fr.text = f"Brain Tumor MRI Classification Using SVM  |  {STU}  |  {len(SL)}"
    fr.font.size, fr.font.name, fr.font.color.rgb = Pt(10), FONT, MUTED
    if notes_text:
        s.notes_slide.notes_text_frame.text = notes_text
    return s


def callout(slide, x, y, w, h, title, lines, fill=AMBERF, line=AMBERL, size=13):
    return text(slide, x, y, w, h, [(title, size + 1, True, INK)] + [(l, size, False, INK) for l in lines], fill=fill, line=line, size=size, space=4)



# ============================================================ 1 title
s = prs.slides.add_slide(BLANK); SL.append(s)
full = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height); full.fill.solid(); full.fill.fore_color.rgb = NAVY; full.line.fill.background(); full.shadow.inherit = False
band = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, I(5.35), prs.slide_width, I(0.06)); band.fill.solid(); band.fill.fore_color.rgb = TEAL; band.line.fill.background()
text(s, 0.8, 0.9, 11.7, 2.0, [("BRAIN TUMOR MRI CLASSIFICATION USING SUPPORT VECTOR MACHINE (SVM)", 36, True, WHITE)], anchor=MSO_ANCHOR.MIDDLE)
text(s, 0.8, 3.0, 11.7, 0.6, [("HOG features + linear / RBF SVM, leakage-aware split, small web app", 20, False, C(0xCF, 0xDD, 0xEE))])
text(s, 0.8, 3.9, 11.7, 1.4, [(f"{STU}  ({REG})", 20, True, C(0xF2, 0xC9, 0x7A)),
                              ("B.Tech Computer Science and Engineering [ AIML/AI ] (as printed in the template)", 16, False, WHITE),
                              ("25AI2004 \u2013 Artificial Intelligence in Healthcare  |  Micro project presentation, 29/10/26 (scheduled)", 16, False, WHITE)], space=3)
text(s, 0.8, 5.6, 11.7, 1.2, [("Karunya Institute of Technology and Sciences (Deemed-to-be-University), Coimbatore", 16, True, WHITE),
                              ("Course faculty: Ms. Gethsia P (as named in the template), Division of Artificial Intelligence and Machine Learning", 14, False, C(0xCF, 0xDD, 0xEE)),
                              ("Academic research prototype \u2013 not a medical device or a clinically validated diagnostic system", 13, False, C(0xF2, 0xC9, 0x7A))], space=3)
s.notes_slide.notes_text_frame.text = "Student name and register number are placeholders to be filled in; the programme line, course and supervisor are as printed in the official template."

# ============================================================ 2 problem
s = new_slide("Problem statement and motivation", "Classical, light-weight classifiers are strong baselines on small medical datasets; the evaluation must be free of duplicate leakage.")
text(s, 0.5, 1.25, 7.4, 5.6, [
    "Task: classify a 2-D brain MRI slice as glioma, meningioma, pituitary tumour or no tumour.",
    "Deep networks need large data, GPUs and are hard to inspect; an SVM on hand-crafted HOG features is fast, transparent and needs no GPU.",
    "But scores are only trustworthy if training and test images are truly separate: copies, mirrored or re-encoded slices make results too optimistic.",
    "The public dataset used here showed exactly this problem, so a leakage-aware split is reused.",
], size=18, bullet=True, space=10)
callout(s, 8.2, 1.35, 4.65, 2.55, "What the audit found", ["1,076 of 1,600 original Testing images had a near-identical copy in Training.", f"Only {audit['representatives']:,} of 7,200 images are unique.", "No patient IDs: patient-level independence cannot be proven."], fill=MINT, line=TEAL, size=14)
callout(s, 8.2, 4.15, 4.65, 2.6, "Question", ["How well does a carefully tuned HOG + SVM pipeline classify whole MRI slices when training, validation and test data are separated by near-duplicate cluster?"], size=14)

# ============================================================ 3 aim
s = new_slide("Aim and objectives", "Six measurable objectives; the test set is used once.")
text(s, 0.5, 1.2, 7.4, 1.15, [("Aim: build and evaluate, without data leakage, a classical SVM pipeline for four-class brain tumour MRI classification, and deliver it as a documented, tested prototype.", 15, False, INK)], fill=MINT, line=TEAL, size=15)
text(s, 0.5, 2.5, 7.4, 4.4, [
    "O1  Reuse the audited, cluster-disjoint split (2,311 / 492 / 492) and verify it.",
    "O2  Preprocess reproducibly: grayscale, resize, HOG, scaler fitted on training data only.",
    "O3  Compare linear and RBF SVMs over three HOG settings (training CV + validation).",
    "O4  Evaluate the frozen model once on the test partition: accuracy, macro P/R/F1, per-class, confusion matrix.",
    "O5  Save and reload the model; check predictions are consistent.",
    "O6  Provide a web app with real SVM inference and tests.",
], size=15, space=8)
text(s, 8.1, 1.2, 4.75, 3.2, [("Relevance", 17, True, INK), ("Healthcare AI baselines and transparent models.", 14, False, INK), ("Leakage-aware evaluation habits for medical imaging.", 14, False, INK), ("Software delivery of research results.", 14, False, INK)], fill=WHITE, line=NAVY, size=14, space=8)
callout(s, 8.1, 4.6, 4.75, 2.25, "SDG links (research direction only)", ["SDG 3 Good Health and Well-being; SDG 9 Industry, Innovation and Infrastructure. Not approved for clinical use."], size=13)

# ============================================================ 4 literature
s = new_slide("Literature review and research gap", "Verified sources only; focused review, not a systematic survey.")
table(s, [["Work", "Contribution", "Role in this project", "Open issue"],
          ["Cortes & Vapnik [1]", "Support-vector network: max-margin classifier with kernels", "Linear and RBF SVM", "No calibrated confidence"],
          ["Dalal & Triggs [2]", "Histograms of oriented gradients", "Feature extractor", "Built for pedestrians; no tumour localisation"],
          ["Hsu, Chang & Lin [5]; LIBSVM [6]", "Scale features, RBF kernel, grid search of C, gamma", "Model-selection recipe", "Coarse grid"],
          ["Zacharaki et al. [7]", "Shape/texture + SVM for tumour type and grade (102 tumours)", "Precedent on brain MRI", "Needs expert regions"],
          ["Cheng et al. [8]", "3-class T1-CE tumour classification with region augmentation", "Same three tumour classes", "Needs tumour masks"]],
      0.5, 1.25, 12.3, [3.0, 4.0, 2.7, 2.6], size=13, rowh=0.62)
callout(s, 0.5, 5.2, 12.3, 1.65, "Research gap", ["Little guidance on whole-slice classification with a leakage-aware split: how good is a tuned HOG + SVM when partitions are separated by near-duplicate cluster, and what can be claimed given the remaining uncertainty (no patient IDs)?"], fill=MINT, line=TEAL, size=14)

# ============================================================ 5 dataset
s = new_slide("Dataset and class distribution", "Matches Kaggle Brain Tumor MRI Dataset v2 (M. Nickparvar, CC BY 4.0) on counts and size; download record unverified; not redistributed.")
pc = audit["partition_class_counts_representatives"]
text(s, 0.5, 1.2, 6.5, 3.3, [
    "Source: matches Kaggle \u2018Brain Tumor MRI Dataset\u2019 v2, CC BY 4.0, on counts and size (7,200 images). Download record UNVERIFIED; upstream terms may differ; not redistributed.",
    f"Audit (reused): 3,479 near-duplicate clusters, 207 images quarantined, {audit['representatives']:,} unique images.",
    "Split reused unchanged: 70/15/15, class-stratified, no cluster in two partitions.",
    "Used by the SVM: one representative per cluster.",
], size=14, bullet=True, space=6)
table(s, [["Partition", "Glioma", "Menin.", "No tumour", "Pituit.", "Total"]] + [[n.capitalize()] + [f"{pc[n][c]:,}" for c in CL] + [f"{sum(pc[n].values()):,}"] for n in ("train", "val", "test")],
      0.5, 4.6, 6.5, [1.2, 1.0, 1.0, 1.3, 1.0, 1.0], size=13, rowh=0.42, align=["l", "c", "c", "c", "c", "c"])
pic(s, FIG / "class_distribution.png", 7.2, 1.2, 5.7, 3.3)
callout(s, 7.2, 4.65, 5.7, 2.2, "Residual uncertainty", ["No patient identifiers: patient-level independence is NOT proven.", "Imbalanced: 227 no-tumour training images; 46 in validation and test."], size=13)

# ============================================================ 6 preprocessing / HOG
s = new_slide("Preprocessing and HOG features", "The same preprocessing function serves training, evaluation and the web app. HOG has no learned parameters, so computing it outside cross-validation does not leak.")
pic(s, FIG / "hog_illustration.png", 0.4, 1.2, 7.4, 4.1)
text(s, 8.0, 1.3, 4.9, 3.0, [
    "1. Grayscale, bilinear resize (128 or 64 px), scale to [0, 1].",
    "2. HOG: 9 orientation bins, 2\u00d72-cell blocks, L2-Hys normalisation.",
    "3. StandardScaler fitted on training data only (inside the pipeline).",
], size=15, space=8)
table(s, [["HOG variant", "Image", "Cell", "Features"], ["hog128_cell16", "128 px", "16 px", "1,764"], ["hog128_cell8", "128 px", "8 px", "8,100"], ["hog64_cell8", "64 px", "8 px", "1,764"]],
      8.0, 4.45, 4.9, [1.8, 1.0, 1.0, 1.1], size=13, rowh=0.42, align=["l", "c", "c", "r"])
text(s, 0.5, 5.5, 7.3, 1.3, [("Example training images (real dataset images, CC BY 4.0) and their HOG descriptors for the selected setting (128 px, 8-px cells, 8,100 features).", 12, False, MUTED)])

# ============================================================ 7 SVMs
s = new_slide("Linear SVM and RBF SVM", "scikit-learn SVC (LIBSVM-based); four classes via one-vs-one voting; the application reports one-vs-rest decision scores, not probabilities.")
callout(s, 0.5, 1.25, 6.0, 2.6, "Linear SVM", ["Linear boundary in HOG space; wide-margin classifier.", "Hyper-parameter C (larger C = fewer margin violations).", "Class weights: none or balanced."], fill=WHITE, line=NAVY, size=15)
callout(s, 6.8, 1.25, 6.0, 2.6, "RBF SVM", ["Kernel k(x, x\u2032) = exp(\u2212\u03b3\u2016x \u2212 x\u2032\u2016\u00b2): non-linear boundary.", "Hyper-parameters C and \u03b3 (reach of one example).", "Class weights: none or balanced."], fill=MINT, line=TEAL, size=15)
table(s, [["Kernel", "Grid searched (for every HOG variant)", "Fits"],
          ["Linear", "C in {1e-5, 1e-4, 1e-3, 1e-2, 1e-1, 1}; class weight in {none, balanced}", "12 \u00d7 5 folds = 60"],
          ["RBF", "C in {1, 10, 100}; \u03b3 in {0.1, 1, 3} / #features; class weight in {none, balanced}", "18 \u00d7 5 folds = 90"]],
      0.5, 4.1, 12.3, [1.3, 8.7, 2.3], size=14, rowh=0.6)
text(s, 0.5, 6.05, 12.3, 0.8, [("The first search was stopped because the linear optimum sat at the lower edge of its C grid; the grid was extended and the search repeated in full (training and validation data only).", 13, False, MUTED)])

# ============================================================ 8 architecture
s = new_slide("System architecture and implementation", "Real SVM inference only: the web app serves the saved SVM, verified by SHA-256 against the model that was evaluated on the test set.")
pic(s, FIG / "pipeline_diagram.png", 0.35, 1.15, 6.4, 3.0)
pic(s, ASSET / "svm_app_architecture.png", 6.9, 1.15, 6.0, 5.0)
text(s, 0.4, 4.3, 6.4, 2.5, [
    "svm_lib / train_select / evaluate_test / leakage_evidence / make_figures",
    "Saved: model, config, label mapping, seeds, package versions, predictions.",
    "Web app: FastAPI + React/TypeScript; endpoints health, status, classify, metrics, experiment, gallery.",
    "No generator, no other classifier.",
], size=13, bullet=True, space=4)
text(s, 6.9, 6.25, 6.0, 0.7, [("13 backend tests passed; 7/7 smoke checks; production build passed; no automated browser-level tests.", 11.5, False, MUTED)])

# ============================================================ 9 selection design
s = new_slide("Hyperparameter selection and evaluation design", "Test data never influence any choice; the evaluation script refuses to run twice.")
pic(s, FIG / "model_selection.png", 0.4, 1.2, 6.8, 3.3)
text(s, 7.4, 1.3, 5.5, 3.2, [
    "Per HOG variant and kernel: 5-fold stratified CV grid search on the TRAIN partition (macro-F1).",
    "Best setting refit on train, scored once on VALIDATION.",
    "Selected by validation macro-F1; fitted on train only; saved.",
    "Then: ONE evaluation on the TEST partition.",
], size=14, bullet=True, space=6)
callout(s, 0.5, 4.75, 6.7, 2.1, "Leakage controls", ["Scaler fitted on training folds only; HOG stateless.", "Selection script reads only train + validation.", "File lists hash-checked; model SHA-256 recorded before serving."], fill=MINT, line=TEAL, size=13)
callout(s, 7.4, 4.75, 5.5, 2.1, "Selected model", [f"{sc['kernel'].upper()} SVM, {sc['hog_variant']}, {sc['n_features']:,} features, C = {sc['best_params']['C']:g}, \u03b3 = 1/{sc['n_features']:,}.", f"Validation macro-F1 {sc['val_macro_f1']:.3f}; CV {sc['cv_macro_f1']:.3f}."], size=13)

# ============================================================ 10 results
s = new_slide("Actual SVM results and comparison", f"Test partition (n = 492), evaluated once. RBF beat linear for every HOG setting on training CV and validation.")
rows = [["Metric (test)", "Value", "95% interval"],
        ["Accuracy", f"{t['accuracy']:.3f}", f"{ci['accuracy'][0]:.3f} to {ci['accuracy'][1]:.3f}"],
        ["Macro precision", f"{t['macro_precision']:.3f}", "\u2013"],
        ["Macro recall", f"{t['macro_recall']:.3f}", "\u2013"],
        ["Macro-F1", f"{t['macro_f1']:.3f}", f"{ci['macro_f1'][0]:.3f} to {ci['macro_f1'][1]:.3f}"],
        ["Always-glioma baseline", f"{t['majority_class_baseline_accuracy']:.3f}", "\u2013"]]
table(s, rows, 0.5, 1.3, 6.2, [3.0, 1.4, 1.8], size=14, rowh=0.5, align=["l", "c", "c"], bold_rows=(1, 4))
crow = [["Candidate", "CV F1", "Val F1"]] + [[f"{c['hog_variant'].replace('hog', '')} {c['kernel']}", f"{c['cv_macro_f1']:.3f}", f"{c['val_macro_f1']:.3f}"] for c in cand]
table(s, crow, 0.5, 4.45, 6.2, [3.4, 1.4, 1.4], size=12, rowh=0.33, align=["l", "c", "c"], bold_rows=(4,))
pic(s, FIG / "per_class_metrics_test.png", 6.9, 1.2, 6.0, 3.4)
callout(s, 6.9, 4.75, 6.0, 2.1, "Reading the numbers", ["More than twice the always-predict-glioma baseline.", f"Validation accuracy {sc['val_accuracy']:.3f} > test {t['accuracy']:.3f}: the test figure is the one to quote.", f"Runtime: fit {t['runtime_seconds']['fit_final_model']:.1f} s; about {t['runtime_seconds']['per_image_total_ms']:.0f} ms per image (CPU)."], fill=MINT, line=TEAL, size=13)

# ============================================================ 11 confusion
s = new_slide("Confusion matrix and class-wise analysis", "Sensitivity/specificity are derived from the saved test predictions; no-tumour rests on only 46 images.")
pic(s, FIG / "confusion_matrix_test.png", 0.4, 1.2, 6.6, 3.2)
rows = [["Class (n)", "Prec.", "Recall", "F1", "Spec."]] + [[f"{CLN[c]} ({t['per_class'][c]['support']})", f"{t['per_class'][c]['precision']:.2f}", f"{t['per_class'][c]['recall']:.2f}", f"{t['per_class'][c]['f1']:.2f}", f"{t['per_class'][c]['specificity_ovr']:.2f}"] for c in CL]
table(s, rows, 7.2, 1.3, 5.7, [2.1, 0.9, 0.9, 0.9, 0.9], size=13, rowh=0.45, align=["l", "c", "c", "c", "c"])
off = sorted(((cm[i][j], CL[i], CL[j]) for i in range(4) for j in range(4) if i != j), reverse=True)
tv = t["tumour_vs_notumor"]
text(s, 0.5, 4.55, 12.3, 2.3, [
    f"Pituitary best (recall {t['per_class']['pituitary']['recall']:.2f}), glioma next ({t['per_class']['glioma']['recall']:.2f}); meningioma hardest ({t['per_class']['meningioma']['recall']:.2f}).",
    f"Largest confusions: {off[0][1]} \u2192 {off[0][2]} ({off[0][0]}), {off[1][1]} \u2192 {off[1][2]} ({off[1][0]}), {off[2][1]} \u2192 {off[2][2]} ({off[2][0]}).",
    f"No tumour has the lowest precision ({t['per_class']['notumor']['precision']:.2f}): {cm[0][2] + cm[1][2] + cm[3][2]} of the {sum(cm[i][2] for i in range(4))} images predicted no-tumour were tumours.",
    f"Tumour vs no-tumour (derived): sensitivity {tv['sensitivity']:.3f}, specificity {tv['specificity']:.3f} (46 no-tumour images).",
], size=14, bullet=True, space=6)

# ============================================================ 12 ethics
s = new_slide("Healthcare ethics, safety and limitations", "Leakage evidence is real but incomplete: patient-level independence is not proven.")
vs, ts = leak["max_similarity_of_val_and_test_images_to_train_images"]["val"], leak["max_similarity_of_val_and_test_images_to_train_images"]["test"]
pic(s, FIG / "leakage_similarity_hist.png", 0.4, 1.2, 6.2, 3.2)
text(s, 0.5, 4.5, 6.1, 2.4, [
    f"0 clusters in more than one partition; 0 identical files shared.",
    f"Max similarity of a held-out image to any training image: {vs['max_similarity_to_any_train_image']:.3f} (val) / {ts['max_similarity_to_any_train_image']:.3f} (test) < 0.98.",
    "But the median is about 0.94: neighbouring slices of one patient cannot be excluded.",
], size=13, bullet=True, space=5)
callout(s, 6.8, 1.25, 6.1, 5.6, "Limitations and safety", [
    "Not a medical device; never for diagnosis or treatment.",
    "Small, imbalanced test set (492; 46 no-tumour); intervals cover test sampling only.",
    "Patient-level independence unproven; heuristic de-duplication.",
    "Whole slices, no tumour masks; only three HOG settings and a coarse grid.",
    "SVM scores are not calibrated probabilities; no out-of-distribution detection.",
    "Data are public, without patient IDs or consent records; uploads processed locally, not stored.",
    "Dataset: matches Kaggle v2; download record unverified; CC BY 4.0, upstream terms may differ; not redistributed.",
], size=13)

# ============================================================ 13 conclusion
s = new_slide("Conclusion and future scope", "Honest conclusion: a good classical baseline on a leakage-aware split, not a clinical tool.")
text(s, 0.5, 1.25, 6.2, 5.6, [("Conclusion", 19, True, INK),
                              (f"Best of six candidates: RBF SVM on {sc['n_features']:,} HOG features (128 px, 8-px cells).", 15, False, INK),
                              (f"Test (evaluated once): accuracy {t['accuracy']:.3f} (95% {ci['accuracy'][0]:.3f}\u2013{ci['accuracy'][1]:.3f}), macro-F1 {t['macro_f1']:.3f}.", 15, False, INK),
                              ("RBF beat linear throughout; finer HOG cells and 128-px images helped.", 15, False, INK),
                              ("Pituitary and glioma best; meningioma and no-tumour weakest.", 15, False, INK),
                              ("A tested web app serves the saved results and real SVM predictions.", 15, False, INK),
                              ("Not clinically validated.", 15, True, INK)], fill=WHITE, line=NAVY, size=15, space=9)
text(s, 6.95, 1.25, 5.9, 5.6, [("Future scope", 19, True, INK),
                               "Larger, more diverse data with patient IDs; patient-level splits; external validation.",
                               "Richer features (texture, wavelets, learned) and a broader search; compare with other classical models and CNNs under the same split.",
                               "Calibrated scores and out-of-distribution detection.",
                               "Use tumour masks where available; expert review of class-wise errors.",
                               "Automated browser-level tests.",
                               "Clinical validation, regulatory review, privacy assessment before any healthcare use."], fill=MINT, line=TEAL, size=14, space=8, bold_first=True)

# ============================================================ 14 references
s = new_slide("References and questions", "Bibliographic details were checked against publisher / index records.")
refs = [
    "[1] Cortes & Vapnik, Support-vector networks, Machine Learning 20, 1995.",
    "[2] Dalal & Triggs, Histograms of oriented gradients for human detection, CVPR 2005.",
    "[3] United Nations, Transforming our world: the 2030 Agenda, 2015.",
    "[4] Karunya Institute of Technology and Sciences, official website.",
    "[5] Hsu, Chang & Lin, A practical guide to support vector classification.",
    "[6] Chang & Lin, LIBSVM, ACM TIST 2(3), 2011.",
]
refs2 = [
    "[7] Zacharaki et al., Classification of brain tumor type and grade \u2026, Magn Reson Med 62(6), 2009.",
    "[8] Cheng et al., Enhanced performance of brain tumor classification \u2026, PLoS ONE 10(10), 2015.",
    "[9] M. Nickparvar, Brain Tumor MRI Dataset, Kaggle v2, CC BY 4.0.",
    "[10] van der Walt et al., scikit-image, PeerJ 2:e453, 2014.",
    "[11] Pedregosa et al., Scikit-learn, JMLR 12, 2011.",
]
text(s, 0.5, 1.2, 6.3, 4.1, refs, size=12.5, space=6)
text(s, 6.9, 1.2, 6.0, 4.1, refs2, size=12.5, space=6)
text(s, 0.5, 5.45, 7.2, 1.45, [("Questions?", 28, True, NAVY), (f"{STU}  |  25AI2004 AI in Healthcare  |  Karunya Institute of Technology and Sciences", 13, False, MUTED)], space=4)
callout(s, 7.9, 5.4, 5.0, 1.5, "Reminder", ["Academic research prototype. Dataset matches Kaggle v2; download record unverified; not redistributed. Not a medical device."], size=12)

assert len(prs.slides) == 14
prs.core_properties.title = "Brain Tumor MRI Classification Using SVM (micro project presentation)"
prs.core_properties.author = ""
prs.save(OUT)
print("saved", OUT, "| slides:", len(prs.slides), "| possible text overflow:", overflow)
