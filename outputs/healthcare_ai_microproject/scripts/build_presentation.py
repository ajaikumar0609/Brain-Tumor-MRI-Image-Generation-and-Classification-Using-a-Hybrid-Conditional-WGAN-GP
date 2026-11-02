#!/usr/bin/env python3
"""Build NEUROVISION_AI_Project_Presentation.pptx (14 slides, 16:9) from the finalized micro-project report content.
Numbers are read from the saved result files; figures are the project's own (saved results, diagrams, genuine app screenshots)."""
import json, math
from pathlib import Path
from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor as C
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches as I, Pt

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUTD = ROOT / "outputs/healthcare_ai_microproject"
EXP = ROOT / "outputs/deduplicated_experiment"
FIGS = ROOT / "outputs/submission/figures"
NEW = OUTD / "assets/figures"
SHOT = OUTD / "assets/screenshots"
OUT = OUTD / "NEUROVISION_AI_Project_Presentation.pptx"

NAVY, TEAL, INK, MUTED = C(0x1F, 0x3A, 0x5F), C(0x2A, 0x9D, 0x8F), C(0x14, 0x21, 0x3D), C(0x55, 0x60, 0x70)
LIGHT, AMBERF, AMBERL, WHITE, BG = C(0xEE, 0xF2, 0xF6), C(0xFD, 0xF1, 0xDC), C(0xC9, 0x8A, 0x1A), C(255, 255, 255), C(0xF6, 0xF8, 0xFA)
MINT = C(0xE4, 0xF2, 0xF0)
FONT = "Calibri"
pm = "±"

gm = json.load(open(EXP / "gan_comparison/metrics.json"))["aggregate"]
ds = json.load(open(EXP / "downstream/summary.json"))
cond = ds["conditions"]
der = json.load(open(OUTD / "assets/derived_class_metrics.json"))["conditions"]
audit = json.load(open(EXP / "dedup_audit_summary.json"))

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
    fr.text = f"NeuroVision AI  |  Brain Tumor MRI Generation and Classification  |  Ajai Kumar N (URK23CS5064)  |  {len(SL)}"
    fr.font.size, fr.font.name, fr.font.color.rgb = Pt(10), FONT, MUTED
    if notes_text:
        s.notes_slide.notes_text_frame.text = notes_text
    return s


def callout(slide, x, y, w, h, title, lines, fill=AMBERF, line=AMBERL, size=13):
    return text(slide, x, y, w, h, [(title, size + 1, True, INK)] + [(l, size, False, INK) for l in lines], fill=fill, line=line, size=size, space=4)


# ============================================================ 1 title
s = prs.slides.add_slide(BLANK); SL.append(s)
bg(s, NAVY)
full = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height); full.fill.solid(); full.fill.fore_color.rgb = NAVY; full.line.fill.background(); full.shadow.inherit = False
band = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, I(5.35), prs.slide_width, I(0.06)); band.fill.solid(); band.fill.fore_color.rgb = TEAL; band.line.fill.background()
text(s, 0.8, 0.9, 11.7, 2.0, [("BRAIN TUMOR MRI IMAGE GENERATION AND CLASSIFICATION USING A HYBRID CONDITIONAL WGAN-GP", 34, True, WHITE)], anchor=MSO_ANCHOR.MIDDLE)
text(s, 0.8, 3.0, 11.7, 0.6, [("NeuroVision AI: a research prototype web application (React + FastAPI)", 20, False, C(0xCF, 0xDD, 0xEE))])
text(s, 0.8, 3.9, 11.7, 1.4, [("Ajai Kumar N  (URK23CS5064)", 20, True, C(0xF2, 0xC9, 0x7A)),
                              ("B.Tech Computer Science and Engineering, specialization in Artificial Intelligence", 16, False, WHITE),
                              ("25AI2004 – Artificial Intelligence in Healthcare  |  Micro project presentation, 29/10/26 (scheduled)", 16, False, WHITE)], space=3)
text(s, 0.8, 5.6, 11.7, 1.2, [("Karunya Institute of Technology and Sciences (Deemed-to-be-University), Coimbatore", 16, True, WHITE),
                              ("Course faculty: Ms. Gethsia P, Division of Artificial Intelligence and Machine Learning", 14, False, C(0xCF, 0xDD, 0xEE)),
                              ("Academic research prototype – not a medical device or a clinically validated diagnostic system", 13, False, C(0xF2, 0xC9, 0x7A))], space=3)
s.notes_slide.notes_text_frame.text = "Title slide. The presentation is scheduled for 29/10/26 per the e-report template; it has not taken place yet."

# ============================================================ 2 problem
s = new_slide("Healthcare problem and motivation",
              "Why synthetic MRI generation is attractive, and why it must be evaluated with care: duplicates between training and test data inflate scores.")
text(s, 0.5, 1.25, 7.4, 5.6, [
    "Brain tumour MRI classification (glioma, meningioma, pituitary tumour, no tumour) needs many correctly labelled images.",
    "Medical data are scarce, imbalanced, expensive to label and protected by privacy rules.",
    "GANs can synthesise extra training images (data augmentation), but generated images may only look like MRI without real pathology, and the requested label is not a diagnosis.",
    "Evaluation is fragile: copies, mirrored or re-encoded slices shared by training and test data inflate every score.",
    "This project found exactly that in its starting dataset and rebuilt the experiments on a leakage-controlled split.",
], size=18, bullet=True, space=9)
callout(s, 8.2, 1.35, 4.65, 2.55, "What we found in the data", [f"{1076:,} of 1,600 original Testing images had a near-identical copy in Training.", "Exact file hashing missed them (mirrored / re-encoded copies).", f"Only {audit['representatives']:,} of 7,200 images are unique."], fill=MINT, line=TEAL, size=14)
callout(s, 8.2, 4.15, 4.65, 2.6, "Research questions", ["Q1: Does the proposed conditional WGAN-GP generate better images than DCGAN / WGAN-GP (FID, KID)?", "Q2: Does adding its images help a CNN once training size is controlled?"], size=14)

# ============================================================ 3 aim
s = new_slide("Aim, objectives and industry relevance", "Aim, six measurable objectives, and relevance without any clinical claim.")
text(s, 0.5, 1.2, 7.3, 1.15, [("Aim: compare DCGAN, WGAN-GP and a conditional WGAN-GP on a leakage-controlled MRI dataset, test honestly whether synthetic images help a classifier, and deliver the work as a documented web application.", 15, False, INK)], fill=MINT, line=TEAL, size=15)
text(s, 0.5, 2.5, 7.3, 4.4, [
    "O1  Audit duplicates; build a cluster-disjoint split (0 clusters crossing partitions).",
    "O2  Train DCGAN, WGAN-GP, cWGAN-GP on the training partition only (3,000 generator updates).",
    "O3  Evaluate FID / KID on the 492 test images, 3 generation seeds, real-vs-real floor.",
    "O4  Implement label-conditional generation; test whether the label changes the output.",
    "O5  Compare classifiers A / B / C (3 seeds): accuracy, macro-F1, derived sensitivity / specificity.",
    "O6  Build and test NeuroVision AI with visible research-prototype warnings.",
], size=15, space=8)
text(s, 8.1, 1.2, 4.75, 4.2, [("Industry relevance", 17, True, INK),
                              ("Healthcare AI and augmentation research: fair tests need a size-matched real-only control.", 14, False, INK),
                              ("Medical-image computing: reproducible duplicate audits and cluster-disjoint splits.", 14, False, INK),
                              ("Responsible evaluation: uncertainty, limits and honest reporting.", 14, False, INK),
                              ("Software delivery: saved results and models exposed through a validated API.", 14, False, INK)], fill=WHITE, line=NAVY, size=14, space=8)
callout(s, 8.1, 5.55, 4.75, 1.3, "SDG links (research direction only)", ["SDG 3 Good Health and Well-being; SDG 9 Industry, Innovation and Infrastructure. Not approved for clinical use."], size=12)

# ============================================================ 4 literature
s = new_slide("Literature review and research gap", "Seven original works, what each contributes, how it is used here and what stays open for low-resolution grayscale MRI.")
table(s, [["Work", "Contribution", "Used in this project", "Open for MRI"],
          ["GAN – Goodfellow et al. [1]", "Adversarial generator vs discriminator", "DCGAN objective (BCE)", "Instability; no clinical check"],
          ["cGAN – Mirza & Osindero [2]", "Condition on a label", "Label embedding in generator", "Labels may not be learned"],
          ["DCGAN – Radford et al. [3]", "Stable conv architecture", "64×64 generator / discriminator", "Large natural-image data"],
          ["WGAN-GP – Arjovsky [4], Gulrajani [5]", "Wasserstein critic + gradient penalty", "WGAN-GP and cWGAN-GP", "More compute; not better here"],
          ["FID – Heusel et al. [6]", "Inception-feature Fréchet distance", "Main quality score", "ImageNet features; small-n bias"],
          ["KID – Bińkowski et al. [7]", "Unbiased MMD on Inception features", "Second quality score", "Same domain gap"],
          ["Projection critic – Miyato & Koyama [8]", "Class embedding projected on features", "cWGAN-GP critic", "Needs reliable labels"]],
      0.5, 1.25, 12.3, [3.7, 3.2, 2.9, 2.5], size=13, rowh=0.5)
callout(s, 0.5, 5.55, 12.3, 1.3, "Research gap", ["Are label-conditional WGAN-GP images class-faithful at 64×64?  Does augmentation still help once training size is controlled?  Do gains survive removal of near-duplicates?  (Foundational methods only; not a survey of medical GAN applications.)"], fill=MINT, line=TEAL, size=13)

# ============================================================ 5 dataset
s = new_slide("Dataset, de-duplication and final split", "Provenance: matches Kaggle Brain Tumor MRI Dataset v2 by Masoud Nickparvar (CC BY 4.0) on counts and size; the local download record is unverified. Not redistributed.")
text(s, 0.5, 1.2, 6.6, 3.55, [
    "Source: matches Kaggle ‘Brain Tumor MRI Dataset’ v2 (M. Nickparvar, CC BY 4.0) on counts and size: 7,200 images, 1,400 / 400 per class. Local download record UNVERIFIED; upstream sources may carry separate terms; not redistributed.",
    "Audit: 1,076 of 1,600 original test images had a near-identical training copy.",
    f"Method: 32×32 cosine similarity over 8 orientations (≥ 0.98) → {audit['n_clusters']:,} clusters.",
    f"Quarantined {audit['quarantined_images']} images (label conflicts, augmented-only clusters, 4 refinement removals) → {audit['representatives']:,} unique images; 0 clusters cross partitions.",
], size=14, bullet=True, space=6)
pc = audit["partition_class_counts_representatives"]
table(s, [["Partition", "Glioma", "Menin.", "No tumour", "Pituit.", "Total"]] + [[n.capitalize()] + [f"{pc[n][c]:,}" for c in ("glioma", "meningioma", "notumor", "pituitary")] + [f"{sum(pc[n].values()):,}"] for n in ("train", "val", "test")],
      7.4, 1.3, 5.4, [1.1, 0.85, 0.85, 1.0, 0.8, 0.8], size=13, rowh=0.42, align=["l", "c", "c", "c", "c", "c"])
pic(s, FIGS / "original_near_duplicate_pairs.png", 7.4, 3.3, 5.4, 1.45)
text(s, 7.4, 4.75, 5.4, 0.4, [("Testing images (top) vs their Training copies (bottom); CC BY 4.0.", 10, False, MUTED)])
callout(s, 0.5, 5.2, 12.3, 1.65, "Residual uncertainty", ["No patient identifiers: different slices of the same patient cannot be detected, so patient-level independence is NOT proven. Near-duplicate detection is a heuristic and may miss rescaled copies.", "Cost: only 3,295 of 7,200 images usable; no-tumour has 227 training and 46 test images."], size=13)

# ============================================================ 6 pipeline
s = new_slide("Proposed methodology and experiment pipeline", "Workflow from the dataset audit to the three evaluations. Validation selects the CNN epoch; the test partition is read afterwards.")
pic(s, NEW / "fig_research_workflow.png", 0.4, 1.15, 5.9, 5.85)
text(s, 6.6, 1.3, 6.3, 5.6, [
    "All three GANs train on the 2,311-image training partition only (hash-verified): 64×64 grayscale, batch 16, seed 42, 3,000 generator updates.",
    "FID / KID: torch-fidelity Inception-v3 pool3, 492 generated vs 492 real test images per seed, 3 generation seeds, KID = 100 subsets of 300, plus a real-vs-real floor.",
    "Downstream CNN (4 conv blocks, 15 epochs, 3 seeds): A real only; B real + 2,888 cWGAN-GP images; C real resampled to B’s size and class mix.",
    "Why C matters: it controls training-set size, so only B > C would indicate a benefit specific to synthetic images.",
    "Hardware: Apple M4 MacBook Air, PyTorch on MPS.",
], size=16, bullet=True, space=9)

# ============================================================ 7 architectures
s = new_slide("DCGAN vs WGAN-GP vs conditional WGAN-GP", "Same generator stack; the models differ in discriminator/critic, loss and conditioning. Not compute-matched: DCGAN used 5x fewer discriminator updates.")
table(s, [["", "DCGAN [3]", "WGAN-GP [4, 5]", "cWGAN-GP (proposed) [2, 5, 8]"],
          ["Generator", "z (100-d) → transposed convs, BatchNorm, Tanh", "Same", "Label embedding (50-d) concatenated to z"],
          ["Discriminator / critic", "Conv + BatchNorm, logit", "Conv, no BatchNorm, scalar score", "Projection critic: ψ(h(x)) + E(y)·h(x), no BatchNorm"],
          ["Objective", "Non-saturating BCE", "Wasserstein + gradient penalty (λ = 10)", "Same loss; real and fake share the label"],
          ["Optimiser (Adam)", "2e-4, β (0.5, 0.999)", "1e-4, β (0.5, 0.9)", "1e-4, β (0.5, 0.9)"],
          ["Updates for 3,000 steps", "3,000 discriminator", "15,000 critic (5 per step)", "15,000 critic (5 per step)"],
          ["Conditioning", "None", "None", "Requested class; no classifier guidance"]],
      0.5, 1.25, 12.3, [2.3, 3.2, 3.2, 3.6], size=13, rowh=0.55)
callout(s, 0.5, 5.35, 12.3, 1.5, "Reading the comparison", ["Only the cWGAN-GP receives the class label; all three share the generator stack and the same data, seed and batch size.", "The WGAN variants use 5x more critic updates than DCGAN's discriminator updates, so the comparison is not compute-matched; the architecture diagram is in the report (Figure 3.4)."], fill=MINT, line=TEAL, size=14)

# ============================================================ 8 app
s = new_slide("NeuroVision AI: architecture and interface", "React + TypeScript + Vite frontend (Tailwind, shadcn/ui, Recharts) and FastAPI + PyTorch backend. The upload classifier is a third-party EfficientNet-B3, not the A/B/C research classifiers.")
pic(s, NEW / "fig_app_architecture.png", 0.35, 1.15, 5.7, 5.4)
pic(s, SHOT / "app_dashboard.png", 6.2, 1.2, 3.3, 2.6)
pic(s, SHOT / "app_generate.png", 9.6, 1.2, 3.3, 2.6)
text(s, 6.2, 3.8, 6.7, 0.35, [("Genuine screenshots of the running application: dashboard (left) and generator (right).", 10.5, False, MUTED)])
text(s, 6.2, 4.15, 6.7, 0.95, [("Endpoints: /api/health, /models/status, /classify, /generate, /metrics, /experiment, /gallery. Models load once with strict checkpoint loading; an unavailable model gives an honest error, never a substitute.", 12.5, False, INK)])
callout(s, 6.2, 5.15, 6.7, 1.2, "Critical distinction", ["Classify MRI uses a third-party pretrained EfficientNet-B3 [14, 15]. A/B/C did not save checkpoints. Its accuracy on our test set is unknown; no out-of-distribution check."], size=12)
text(s, 6.2, 6.4, 6.7, 0.6, [("Tests: 16 backend pytest, 6/6 smoke checks, production build; manual browser checks; no automated browser-level suite.", 11, False, MUTED)])

# ============================================================ 9 samples
s = new_slide("Generated samples and conditioning findings", "MRI-like head shapes, no identifiable tumours; the requested label changes brightness more than anatomy. Labels are requested conditions, not diagnoses.")
pic(s, FIGS / "sample_grids_real_vs_generated.png", 0.4, 1.2, 6.2, 4.15)
pic(s, FIGS / "cwgangp_samples_by_class.png", 6.8, 1.2, 6.1, 2.4)
text(s, 6.8, 3.65, 6.1, 1.75, [
    "All three GANs make head-shaped, MRI-like images with soft interiors; none shows an identifiable tumour.",
    "cWGAN-GP: the no-tumour row is visibly brighter; other labels look alike.",
    "Per-class KID: only meningioma is closest to its own class; pituitary is not separated.",
], size=14, bullet=True, space=4)
callout(s, 0.5, 5.55, 12.3, 1.3, "Conclusion on conditioning", ["The generator did NOT demonstrate reliable tumour-specific anatomy. Synthetic labels are requested conditions, not expert-verified diagnoses. Per-class FID/KID rest on only 46–196 images (indicative)."], size=14)

# ============================================================ 10 FID/KID
s = new_slide("FID / KID comparison (lower is better)", "DCGAN has the best FID and KID. The 4.3-point FID gap between cWGAN-GP and WGAN-GP is small. All far above the 34.2 reference floor.")


def gr(key, label):
    a = gm[key]
    return [label, f"{a['fid_mean']:.1f} {pm} {a['fid_std_across_seeds']:.1f}", f"{a['kid_mean'] * 1000:.1f} {pm} {a['kid_std_across_seeds'] * 1000:.1f}".replace("-", "−")]


table(s, [["Model", "FID", "KID × 1000"], gr("Real train reps (class-matched, reference)", "Real-vs-real floor"), gr("DCGAN", "DCGAN (best)"), gr("cWGAN-GP", "cWGAN-GP"), gr("WGAN-GP", "WGAN-GP")],
      0.5, 1.3, 5.9, [2.5, 1.7, 1.7], size=15, rowh=0.5, bold_rows=(2,), align=["l", "c", "c"])
pic(s, FIGS / "fid_kid_bar_chart.png", 6.6, 1.2, 6.3, 3.2)
text(s, 0.5, 4.0, 5.9, 2.85, [
    "n = 492 test images; mean ± sd over 3 generation seeds.",
    "Each GAN trained once, so training-run variance is unmeasured.",
    "Not compute-matched: 3,000 discriminator vs 15,000 critic updates.",
], size=14, bullet=True, space=6)
callout(s, 6.6, 4.55, 6.3, 2.3, "How to read these metrics", ["Inception-v3 features were learned on colour photographs; FID is biased for small samples.", "They do not establish anatomical or clinical validity."], size=14)

# ============================================================ 11 A/B/C
s = new_slide("Downstream classification: conditions A, B and C", "C, the matched-size real-only control, had the highest mean accuracy and macro-F1. B beat A in 3/3 seeds, C was above B in 2/3 seeds. B and C cannot be separated statistically.")
rows = [["Condition", "Train n", "Test accuracy", "Macro-F1", "Val. acc."]]
for key, name in (("A_real_only", "A: real only"), ("B_real_plus_cwgangp_synthetic", "B: real + synthetic"), ("C_real_only_matched_composition", "C: matched real only")):
    c = cond[key]
    rows.append([name, f"{c['n_train']:,}", f"{c['accuracy']['mean']:.3f} {pm} {c['accuracy']['std']:.3f}", f"{c['macro_f1']['mean']:.3f} {pm} {c['macro_f1']['std']:.3f}", f"{c['val_accuracy']['mean']:.3f}"])
table(s, rows, 0.5, 1.3, 7.2, [2.3, 0.9, 1.6, 1.5, 0.9], size=14, rowh=0.5, bold_rows=(3,), align=["l", "c", "c", "c", "c"])
pic(s, FIGS / "accuracy_A_B_C.png", 0.4, 3.45, 7.4, 3.4)
text(s, 8.0, 1.3, 4.9, 3.1, [
    "Test set: 492 images, 3 training seeds.",
    "Adding cWGAN-GP images (B) beat real-only (A) in all 3 seeds (+0.022 accuracy).",
    "But the size-matched real-only control (C) scored highest: 0.869 accuracy, 0.853 macro-F1.",
    "Mean B − C accuracy: −0.030.",
], size=15, bullet=True, space=7)
callout(s, 8.0, 4.55, 4.9, 2.3, "Conclusion", ["No benefit of synthetic augmentation beyond added training volume is demonstrated; the point estimates favour the control. A single run has ±3 accuracy points of sampling error; no significance test was run."], fill=MINT, line=TEAL, size=14)

# ============================================================ 12 class-wise / ethics
s = new_slide("Class-wise findings, ethics and patient-safety limits", "Sensitivity/specificity were derived from the saved test predictions; they reproduce the saved accuracies and are not clinical performance estimates.")
pic(s, NEW / "fig_sens_spec.png", 0.4, 1.2, 6.5, 3.1)
tv = {k: der[k]["tumour_vs_notumor"] for k in "ABC"}
text(s, 0.5, 4.35, 6.4, 2.5, [
    "Largest confusion in every condition: glioma predicted as meningioma (26 / 31 / 16 of 196 for A / B / C).",
    f"Tumour vs no-tumour sensitivity ≈ 0.96–0.97 for all; specificity {tv['A']['specificity']['mean']:.2f} (A), {tv['B']['specificity']['mean']:.2f} (B), {tv['C']['specificity']['mean']:.2f} (C).",
    "No-tumour rests on only 46 test images: very uncertain.",
], size=14, bullet=True, space=6)
callout(s, 7.1, 1.25, 5.8, 5.6, "Ethics, safety and limitations", [
    "Not a medical device; never for diagnosis or treatment.",
    "Synthetic images are not patient scans; labels are requested, not verified.",
    "Small test set (492; 46 no-tumour); patient-level independence unproven; heuristic de-duplication.",
    "3 seeds, one GAN run each; no significance tests.",
    "cWGAN-GP interrupted at step 2,861 (non-finite loss); cause unconfirmed; resumed from step 2,500.",
    "Third-party classifier may have inflated accuracy; unknown here; no OOD detection.",
    "Dataset: matches Kaggle v2, download record unverified; CC BY 4.0, upstream terms may differ; not redistributed.",
], size=13)

# ============================================================ 13 conclusion
s = new_slide("Conclusion and future scope", "Honest conclusion: DCGAN best on generation metrics; matched-size real-only control best on classification; the proposed hybrid is evaluated, not shown to win.")
text(s, 0.5, 1.25, 6.2, 5.6, [("Conclusion", 19, True, INK),
                              ("DCGAN gave the best generation metrics: FID 154.7, KID×1000 129.4 (cWGAN-GP 177.8 / 157.6; WGAN-GP 182.1 / 163.5).", 15, False, INK),
                              ("Mean test accuracy: A 0.817, B 0.839, C 0.869. The matched-size real-only control was best, so no benefit beyond added training volume was shown.", 15, False, INK),
                              ("The generator produced MRI-like images but no reliable tumour-specific anatomy.", 15, False, INK),
                              ("NeuroVision AI delivers the saved results, sample generation and a third-party classifier demo with visible limits.", 15, False, INK),
                              ("Not clinically validated.", 15, True, INK)], fill=WHITE, line=NAVY, size=15, space=9)
text(s, 6.95, 1.25, 5.9, 5.6, [("Future scope", 19, True, INK),
                               "Larger, more diverse data; patient-level splits where identifiers exist.",
                               "More GAN runs and seeds, significance tests, compute-matched baselines, longer training.",
                               "Improved conditional generation and class-consistency evaluation.",
                               "Medical-structure evaluation beyond ImageNet-feature FID/KID.",
                               "Save a research classifier checkpoint (e.g. condition C) for new-image inference.",
                               "Automated browser-level tests and out-of-distribution handling.",
                               "Clinical validation, regulatory review and oversight before any healthcare use."], fill=MINT, line=TEAL, size=14, space=7, bold_first=True)

# ============================================================ 14 references
s = new_slide("References and questions", "Reference list as in the report; all arXiv-based references were checked against arXiv.")
refs = [
    "[1] Goodfellow et al., Generative Adversarial Networks, arXiv:1406.2661, 2014.",
    "[2] Mirza & Osindero, Conditional Generative Adversarial Nets, arXiv:1411.1784, 2014.",
    "[3] Radford, Metz & Chintala, DCGAN, arXiv:1511.06434, 2015.",
    "[4] Arjovsky, Chintala & Bottou, Wasserstein GAN, arXiv:1701.07875, 2017.",
    "[5] Gulrajani et al., Improved Training of Wasserstein GANs, arXiv:1704.00028, 2017.",
    "[6] Heusel et al., TTUR / FID, NIPS 2017; arXiv:1706.08500.",
    "[7] Bińkowski et al., Demystifying MMD GANs, ICLR 2018; arXiv:1801.01401.",
    "[8] Miyato & Koyama, cGANs with Projection Discriminator, ICLR 2018; arXiv:1802.05637.",
]
refs2 = [
    "[9] United Nations, Transforming our world: the 2030 Agenda, 2015.",
    "[10] Karunya Institute of Technology and Sciences, official website.",
    "[11] M. Nickparvar, Brain Tumor MRI Dataset, Kaggle v2, CC BY 4.0.",
    "[12] Kingma & Ba, Adam, ICLR 2015; arXiv:1412.6980.",
    "[13] torch-fidelity 0.4.0 (software).",
    "[14] Tan & Le, EfficientNet, ICML 2019; arXiv:1905.11946.",
    "[15] Phi-007, brain-tumor-classifier (Apache-2.0) (software).",
]
text(s, 0.5, 1.2, 6.3, 4.1, refs, size=12.5, space=5)
text(s, 6.9, 1.2, 6.0, 4.1, refs2, size=12.5, space=5)
text(s, 0.5, 5.45, 7.2, 1.45, [("Questions?", 28, True, NAVY), ("Ajai Kumar N (URK23CS5064)  |  25AI2004 AI in Healthcare  |  Karunya Institute of Technology and Sciences", 13, False, MUTED)], space=4)
callout(s, 7.9, 5.4, 5.0, 1.5, "Reminder", ["Academic research prototype. Dataset matches Kaggle v2; download record unverified; not redistributed. Not a medical device."], size=12)

assert len(prs.slides) == 14
prs.core_properties.title = "NeuroVision AI – Brain Tumor MRI Generation and Classification (micro project)"
prs.core_properties.author = "Ajai Kumar N"
prs.save(OUT)
print("saved", OUT, "| slides:", len(prs.slides), "| possible text overflow:", overflow)
