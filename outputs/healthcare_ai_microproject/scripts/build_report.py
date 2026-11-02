#!/usr/bin/env python3
"""Build NEUROVISION_AI_Micro_Project_Report.docx from the official e-report template (templates/E-report template.docx).
All numbers come from the saved result files under outputs/deduplicated_experiment/ (and the derived-metrics file computed from the saved
predictions); nothing is trained or evaluated here.   python outputs/healthcare_ai_microproject/scripts/build_report.py"""
import copy, json, sys
from pathlib import Path
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH as AL
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, Inches

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from report_lib import Builder, rich, _run, TEXT_W  # noqa: E402

ROOT = HERE.parents[2]
OUTD = ROOT / "outputs/healthcare_ai_microproject"
EXP = ROOT / "outputs/deduplicated_experiment"
FIGS = ROOT / "outputs/submission/figures"        # existing project figures (generated from saved results earlier)
NEW = OUTD / "assets/figures"
SHOT = OUTD / "assets/screenshots"
TEMPLATE = ROOT / "templates/E-report template.docx"
OUT = OUTD / "NEUROVISION_AI_Micro_Project_Report.docx"
TOC_JSON = OUTD / "assets/toc_pages.json"

TITLE = "Brain Tumor MRI Image Generation and Classification Using a Hybrid Conditional WGAN-GP"
STUDENT = "Ajai Kumar N (URK23CS5064)"

# ---------------------------------------------------------------- saved results -------------------------------------------------------
gm = json.load(open(EXP / "gan_comparison/metrics.json"))
gagg = gm["aggregate"]
ds = json.load(open(EXP / "downstream/summary.json"))
cond = ds["conditions"]
audit = json.load(open(EXP / "dedup_audit_summary.json"))
ver = json.load(open(EXP / "gan/gan_verification.json"))["models"]
der = json.load(open(OUTD / "assets/derived_class_metrics.json"))
CL = ["glioma", "meningioma", "notumor", "pituitary"]
CLN = {"glioma": "Glioma", "meningioma": "Meningioma", "notumor": "No tumour", "pituitary": "Pituitary"}
M = "−"  # minus sign
pm = "±"


def f(x, d=1):
    s = f"{x:.{d}f}"
    return s.replace("-", M)


def gan_row(key, label):
    a = gagg[key]
    return [label, f"{f(a['fid_mean'])} {pm} {f(a['fid_std_across_seeds'])}", f"{f(a['kid_mean'] * 1000)} {pm} {f(a['kid_std_across_seeds'] * 1000)}"]


FLOOR_KEY = "Real train reps (class-matched, reference)"
assert round(gagg["DCGAN"]["fid_mean"], 1) == 154.7 and round(gagg["cWGAN-GP"]["fid_mean"], 1) == 177.8 and round(gagg["WGAN-GP"]["fid_mean"], 1) == 182.1
assert round(cond["A_real_only"]["accuracy"]["mean"], 3) == 0.817 and round(cond["C_real_only_matched_composition"]["accuracy"]["mean"], 3) == 0.869
assert audit["representatives"] == 3295 and audit["quarantined_images"] == 207 and audit["partition_totals"] == {"train": 2311, "val": 492, "test": 492}, audit["partition_totals"]

# ---------------------------------------------------------------- open template ---------------------------------------------------------
doc = Document(TEMPLATE)
body = doc.element.body
P = doc.paragraphs
assert P[0].text.startswith("TITLE OF MICRO PROJECT") and P[26].text.startswith("BONAFIDE") and P[56].text.startswith("TABLE OF CONTENTS")


def set_text(par, text, keep_run=0):
    """Replace a paragraph's text but keep the formatting of one existing run."""
    runs = par.runs
    runs[keep_run].text = text
    for i, r in enumerate(runs):
        if i != keep_run:
            r._element.getparent().remove(r._element)


# ---- cover page ---------------------------------------------------------------------------------------------------------------------
set_text(P[0], TITLE.upper() + " ")
P[0].runs[0].font.size = Pt(15)
r = P[1].add_run("NeuroVision AI: a research prototype web application")
r.font.size, r.bold, r.italic = Pt(13), True, True
set_text(P[4], STUDENT)
for i in (5, 6, 7):                                  # the template has four "Name (Reg No)" lines; this is a single-student project
    P[i]._p.getparent().remove(P[i]._p)
set_text(P[13], "B. TECH COMPUTER SCIENCE AND ENGINEERING [ AI ]")
# 25AI2004 line already reads "25AI2004 - Artificial Intelligence in Healthcare"; supervisor and October 2026 are kept as printed in the template.

# ---- bonafide certificate -----------------------------------------------------------------------------------------------------------
cp = P[28]
runs = cp.runs
runs[1].text = f"“{TITLE}” "                      # bold title run
runs[5].text = STUDENT                                       # bold names run
runs[6].text = ""                                            # tab
P[26].paragraph_format.page_break_before = True
sub = P[42]
sub.runs[0].text = "Submitted for the micro project presentation scheduled on "
P[56].paragraph_format.page_break_before = True

# ---- remove the template's empty spacer paragraphs that only existed to push content onto the next page ---------------------------------
children = list(body.iterchildren())
toc_head = P[56]._p
idx_toc = children.index(toc_head)
idx_sub = children.index(sub._p)
for el in children[idx_sub + 1: idx_toc]:           # spacers between the submission line and "TABLE OF CONTENTS"
    if el.tag == qn("w:p") and not "".join(el.itertext()).strip():
        body.remove(el)
children = list(body.iterchildren())
toc_tbl = doc.tables[0]._tbl
idx_tbl = children.index(toc_tbl)
frame = [el for el in children if el.tag == qn("w:p") and el.find(qn("w:pPr")) is not None and el.find(qn("w:pPr")).find(qn("w:pStyle")) is not None
         and el.find(qn("w:pPr")).find(qn("w:pStyle")).get(qn("w:val")) == "FrameContents"]
idx_eval = children.index(frame[0])
eval_block = children[idx_eval:-1]                   # evaluation report heading ... faculty signature (everything before the final sectPr)
spacers = [el for el in children[idx_tbl + 1: idx_eval] if el.tag == qn("w:p") and not "".join(el.itertext()).strip()]
for el in eval_block:
    body.remove(el)
for el in spacers[1:]:
    body.remove(el)
section_break_par = spacers[0]                       # the empty paragraph after the TOC table: will carry the prelim-section properties

# ---------------------------------------------------------------- content ----------------------------------------------------------------
B = Builder(doc)

# ---- ABSTRACT (inserted before the TOC) -----------------------------------------------------------------------------------------------
mark = len(list(body.iterchildren())) - 1        # index of the (current) final sectPr: new elements are inserted before it
B.para("ABSTRACT", AL.CENTER, 14, True, before=0, after=12, page_break=True)
abstract = (
    "Brain tumour MRI classification needs many labelled images, but medical data are scarce, imbalanced and hard to share, and generative adversarial "
    "networks (GANs) are often proposed to create extra training images. This micro project compares three GANs on 64×64 grayscale brain MRI slices from a "
    "four-class public dataset (glioma, meningioma, pituitary tumour, no tumour): a DCGAN, an unconditional WGAN-GP and a proposed conditional WGAN-GP "
    "(cWGAN-GP) with a projection critic. An audit showed that 1,076 of the 1,600 images in the dataset’s original Testing folder had a near-identical copy in the "
    "Training folder, so the 7,200 images were grouped into 3,479 near-duplicate clusters, 207 images were quarantined, and a cluster-disjoint split of 3,295 unique "
    "images into 2,311 training, 492 validation and 492 test images was built. Generation quality was measured with the Fréchet and Kernel Inception Distances "
    "(FID, KID) against the test images, and usefulness with a small CNN trained on (A) real images only, (B) real plus cWGAN-GP images and (C) a real-only control "
    "resampled to B’s size and class mix. DCGAN gave the best generation scores (FID 154.7; KID×1000 129.4), ahead of cWGAN-GP (177.8; 157.6) and WGAN-GP "
    "(182.1; 163.5). Mean test accuracy was 0.817 for A, 0.839 for B and 0.869 for C: the matched real-only control scored highest, so the study shows no benefit of "
    "synthetic augmentation beyond added training volume. The work is packaged as NeuroVision AI, a React and FastAPI web application that displays the saved results, "
    "generates synthetic samples with the saved cWGAN-GP checkpoint and demonstrates a third-party pretrained classifier. It is an academic prototype, not a clinically "
    "validated system: the test set is small (492 images, 46 no-tumour), patient-level independence could not be established, and the generator did not demonstrate "
    "reliable tumour-specific anatomy.")
B.para(abstract, AL.JUSTIFY, 12, line=1.3, after=10)
B.para("**Keywords:** brain tumour MRI, generative adversarial network, conditional WGAN-GP, data leakage, near-duplicate detection, FID, KID, medical image synthesis, "
       "healthcare AI, web application", AL.JUSTIFY, 12, after=6)
abs_elems = list(body.iterchildren())[mark:-1]       # new elements (excluding final sectPr)
for el in abs_elems:
    toc_head.addprevious(el)

# ---- CHAPTER 1 --------------------------------------------------------------------------------------------------------------------------
B.chapter_heading(1, "INTRODUCTION")
B.h2("1.1", "Background of the selected problem")
B.para("A brain tumour is an abnormal growth of cells in or around the brain. Magnetic resonance imaging (MRI) is one of the main tools used to examine the brain, and "
       "computer-aided analysis of MRI slices is an active research area. This project works with four image classes: **glioma** and **meningioma** (two common tumour "
       "types), **pituitary tumour** (a tumour of the pituitary gland) and **no tumour**. Deep learning classifiers can learn to separate such classes, but they need many "
       "correctly labelled images. In medicine, labelled images are expensive because they need expert review, they are protected by privacy rules, rare conditions give "
       "few examples, and the classes are usually imbalanced.")
B.para("One proposed remedy is **synthetic data generation**: a generative model learns the appearance of the real images and produces new ones that can be added to the "
       "training set (“data augmentation”). A **generative adversarial network (GAN)** [1] trains two neural networks against each other: a *generator* turns random "
       "noise into an image and a *discriminator* tries to tell generated images from real ones. A *conditional* GAN [2] also receives a label, so that the class of the "
       "generated image can be requested. Popular variants include the deep convolutional GAN (DCGAN) [3], the Wasserstein GAN [4] and its gradient-penalty form, "
       "WGAN-GP [5]. Generated images are compared with real ones using distribution distances such as the Fréchet Inception Distance (FID) [6] and the Kernel Inception "
       "Distance (KID) [7], and class information can be injected into the critic with a projection layer [8].")
B.para("Synthetic medical images must be treated with care. A generator can produce images that merely *look* like MRI without carrying real pathology, and the requested "
       "label is not a diagnosis. A second problem concerns evaluation: if the same slice (or a mirrored or re-encoded copy of it) appears in both the training and the test "
       "data, every reported score is optimistic. This project found exactly that problem in the public dataset it started from, and therefore rebuilt its experiments on a "
       "leakage-controlled split. The project is titled *Brain Tumor MRI Image Generation and Classification Using a Hybrid Conditional WGAN-GP*; the web application built "
       "around it is called **NeuroVision AI**.")
B.h2("1.2", "Industry Relevance")
B.para("Healthcare AI, medical-image computing and medical-software engineering all face the same questions that this micro project works through on a small scale:")
B.bullets([
    "**Healthcare AI and data augmentation research.** Whether synthetic images help a classifier is an open question; a fair test needs a control that gives the "
    "classifier the same amount of *real* data (condition C in this project).",
    "**Medical-image computing.** Duplicate and near-duplicate slices are a known risk when many slices come from the same scans. A reproducible audit and a "
    "cluster-disjoint split are practical tools for any imaging team.",
    "**Responsible evaluation.** The project reports uncertainty (seed spread, small test set), keeps validation and test data separate, states what cannot be concluded, "
    "and distinguishes research results from application demonstrations.",
    "**Software delivery.** NeuroVision AI shows how saved research results and model checkpoints can be exposed through a validated API and a browser interface for "
    "exploration by non-programmers.",
])
B.para("These are research and engineering benefits only. The models and the application are **not approved or validated for clinical use** and must not be used to "
       "diagnose or treat patients.")
B.h2("1.3", "Aim and Objective of the Micro Project")
B.para("**Aim.** To compare three GANs (DCGAN, WGAN-GP and the proposed conditional WGAN-GP) for generating 64×64 brain MRI slices on a leakage-controlled dataset, to "
       "test honestly whether their synthetic images improve a downstream tumour classifier, and to deliver the completed work as a documented web application.")
B.para("The measurable objectives were:")
B.numbered([
    "Audit the dataset for exact and near-duplicate images and build a cluster-disjoint train/validation/test split (measured by the number of clusters, quarantined images, "
    "partition sizes and the number of clusters crossing partitions, which must be zero).",
    "Implement and train DCGAN, WGAN-GP and cWGAN-GP on the training partition only, with identical data, seed, batch size and 3,000 generator updates each.",
    "Evaluate generation quality with FID and KID against the 492 test images, using three generation seeds and a real-versus-real reference floor.",
    "Implement label-conditional generation and examine whether the requested class changes and matches the generated images (per-class KID).",
    "Compare a small CNN trained on real data only (A), real plus synthetic data (B) and a size-matched real-only control (C) over three training seeds, reporting accuracy, "
    "macro-F1 and, from the saved predictions, per-class sensitivity and specificity.",
    "Build and test NeuroVision AI, a React + TypeScript frontend with a FastAPI + PyTorch backend, for viewing the saved results, generating samples and demonstrating "
    "classification, with visible research-prototype warnings.",
])
B.h2("1.4", "Link to SDG / KITS Technology Mission")
B.para("**UN Sustainable Development Goals.** The project relates most directly to **SDG 3, Good Health and Well-being** (“Ensure healthy lives and promote well-being for all "
       "at all ages”) [9]. Methods that make diagnostic-support research less dependent on large private image collections, and that expose data leakage, contribute to "
       "the research base of that goal; the project itself makes no claim of health impact. It relates secondarily to **SDG 9, Industry, Innovation and Infrastructure** "
       "(“Build resilient infrastructure, promote inclusive and sustainable industrialization and foster innovation”) [9], through a reproducible pipeline and a "
       "working software prototype. These links are about research direction, not about delivered outcomes.")
B.para("**Karunya Institute of Technology and Sciences.** The university’s official site states its mission as raising scientists and entrepreneurs to find solutions, and "
       "names food, water, health care and energy as its product-development focus areas [10]; this project falls under the health care area. The sources consulted "
       "(karunya.edu and kcode.karunya.edu) did not contain a description of a specific “Technology Mission”, so this report does not describe one and does not claim "
       "any institutional endorsement. *If the course requires a particular Technology Mission statement, it should be taken from the official document and added here.*")

# ---- CHAPTER 2 --------------------------------------------------------------------------------------------------------------------------
B.chapter_heading(2, "LITERATURE REVIEW")
B.para("This chapter reviews the original papers on which the project’s methods and metrics rest. It is a review of foundational methods, not a systematic survey of "
       "medical GAN applications. For each work the text states what it contributes, how it is used here, and what remains unresolved for low-resolution grayscale MRI.")
lit = [
    ("2.1", "Generative Adversarial Networks (Goodfellow et al., 2014) [1]",
     "Goodfellow and colleagues introduced a framework in which a generator and a discriminator are trained simultaneously in a two-player game: the generator tries to "
     "produce samples the discriminator accepts as real, and the discriminator tries to reject them. The approach can be trained with back-propagation, without Markov "
     "chains or approximate-inference networks. **Relevance:** it is the basis of all three models here; the DCGAN baseline uses the standard binary cross-entropy (BCE) adversarial objective. "
     "**Unresolved:** adversarial training can be unstable, and the framework offers no built-in measure of sample quality or of medical correctness."),
    ("2.2", "Conditional GANs (Mirza and Osindero, 2014) [2]",
     "Mirza and Osindero extended the GAN by giving both networks extra information, such as a class label, so that generation can be directed. **Relevance:** the proposed "
     "cWGAN-GP feeds a label embedding to the generator together with the noise vector. **Unresolved:** conditioning does not guarantee that the model learns "
     "class-specific features; with noisy labels or few examples per class it may only change global appearance. In this dataset, one cluster family carried conflicting class "
     "labels, which makes the question sharper."),
    ("2.3", "DCGAN (Radford, Metz and Chintala, 2015) [3]",
     "Radford and colleagues proposed architectural guidelines that made convolutional GANs train more reliably: strided convolutions in place of pooling, batch normalisation, "
     "no fully connected hidden layers, ReLU in the generator and LeakyReLU in the discriminator. **Relevance:** the project’s generator and discriminator at 64×64 follow these "
     "guidelines. **Unresolved:** the guidelines were demonstrated on large natural-image collections; behaviour on a few thousand grayscale MRI slices is not guaranteed."),
    ("2.4", "Wasserstein GAN and WGAN-GP (Arjovsky et al., 2017; Gulrajani et al., 2017) [4], [5]",
     "Arjovsky, Chintala and Bottou replaced the original divergence by the Wasserstein distance and used a *critic* (a discriminator without a sigmoid) constrained to be "
     "Lipschitz by weight clipping [4]. Gulrajani and colleagues showed that clipping can cause problems and proposed a **gradient penalty** that pushes the norm of the critic’s "
     "gradient towards one on interpolated samples; they also recommend not using batch normalisation in the critic [5]. **Relevance:** the WGAN-GP and cWGAN-GP here use "
     "a penalty weight of 10 and five critic updates per generator update. **Unresolved:** the extra critic updates cost compute, the critic loss does not directly give an image-quality "
     "number, and in this project WGAN-GP did not beat the simpler DCGAN within 3,000 generator updates."),
    ("2.5", "Fréchet Inception Distance (Heusel et al., 2017) [6]",
     "Heusel and colleagues introduced the FID, which fits Gaussians to Inception-network features of real and generated images and measures the Fréchet distance between them; "
     "lower is better. **Relevance:** FID is the main generation-quality score here. **Unresolved:** the Inception network was trained on colour photographs of everyday objects, FID "
     "is biased upward for small samples, and a low FID is not evidence of anatomical correctness. This project computes it on 492 grayscale 64×64 images."),
    ("2.6", "Kernel Inception Distance (Bińkowski et al., 2018) [7]",
     "Bińkowski, Sutherland, Arbel and Gretton analysed MMD-based GANs and proposed the KID, a squared maximum-mean-discrepancy on Inception features with a polynomial kernel and an "
     "*unbiased* estimator, which suits smaller sample sizes. **Relevance:** KID complements FID and is computed over 100 subsets of 300 images. **Unresolved:** it shares FID’s "
     "domain gap for medical images, and its unbiased estimate can be slightly negative (as it is for the real-versus-real reference here)."),
    ("2.7", "Projection discriminators (Miyato and Koyama, 2018) [8]",
     "Miyato and Koyama proposed a conditional discriminator whose output is an unconditional score plus the inner product of a learned class embedding with the image features. "
     "**Relevance:** the project’s critic uses exactly this projection form, D(x, y) = ψ(h(x)) + E(y)·h(x), without batch normalisation. **Unresolved:** the method was evaluated on "
     "large natural-image datasets; whether a projection critic yields class-faithful synthetic MRI from only 227 no-tumour and a few hundred other images per class is the question "
     "this project examines, with a cautious answer in Chapter 5."),
]
for num, title, text in lit:
    B.h2(num, title)
    B.para(text)
B.h2("2.8", "Summary and research gap")
B.table("Summary of the reviewed work and its role in this project.", [
    ["Work", "Key contribution", "Used here as", "Open issue for MRI"],
    ["GAN [1]", "Adversarial generator–discriminator training", "DCGAN baseline objective", "Instability; no quality or clinical check"],
    ["cGAN [2]", "Conditioning on a label", "Label embedding in the generator", "Labels may not be learned as class features"],
    ["DCGAN [3]", "Stable convolutional architecture", "64×64 generator/discriminator", "Designed for large natural-image sets"],
    ["WGAN [4], WGAN-GP [5]", "Wasserstein critic; gradient penalty", "WGAN-GP and cWGAN-GP training", "More compute; no better than DCGAN here"],
    ["FID [6]", "Inception-feature Fréchet distance", "Main quality score", "ImageNet features; small-sample bias"],
    ["KID [7]", "Unbiased MMD on Inception features", "Second quality score", "Same domain gap; can be negative"],
    ["Projection critic [8]", "Class embedding projected on features", "cWGAN-GP critic", "Needs reliable labels and enough data"],
], [1.15, 1.9, 1.7, 1.75], size=9.5)
B.para("**Gap addressed.** The reviewed methods supply the building blocks, but they do not answer three practical questions for small grayscale medical datasets: (i) whether "
       "label-conditional WGAN-GP images are class-faithful at 64×64; (ii) whether synthetic augmentation still helps once the *amount* of real training data is controlled; and "
       "(iii) whether reported gains survive removal of near-duplicate images between training and test data. The experiments in Chapters 3 and 5 are designed around these three questions.")

# ---- CHAPTER 3 --------------------------------------------------------------------------------------------------------------------------
B.chapter_heading(3, "METHODOLOGY")
B.figure(NEW / "fig_research_workflow.png", "Experimental workflow of the project, from the original dataset to the results and the NeuroVision AI application.", width=5.1)
B.h2("3.1", "Dataset source and initial structure")
B.para("The data are a four-class brain MRI collection obtained from Kaggle. Its folder structure (Training and Testing, each with glioma, meningioma, notumor and pituitary "
       "folders), its 7,200 image files (1,400 training and 400 testing images per class) and its size (167.85 MB) match the Kaggle page *Brain Tumor MRI Dataset* by Masoud "
       "Nickparvar, Version 2 [11]. The page lists the licence as **CC BY 4.0** and names three upstream sources: the figshare brain MRI dataset, the SARTAJ dataset and the Br35H "
       "dataset (the no-tumour images come from Br35H). File names carry the prefixes Tr- and Te-, and 203 files carry an *aug* marker (100 in Training and 103 in Testing), which the Kaggle "
       "page does not mention.")
B.note("Provenance caveats", [
    "The match with the Kaggle page is on checkable counts and size only. **The local download record is unverified** (no URL was saved), so it cannot be proved that the files "
    "are identical to that version.",
    "The CC BY 4.0 licence is the one shown on the dataset page; the upstream datasets may carry separate terms. **The dataset is not redistributed** with this report or the "
    "software package; attribution: M. Nickparvar, *Brain Tumor MRI Dataset*, Kaggle.",
    "The page states that Version 2 removed duplicates and eliminated train/test overlap. The project’s own near-duplicate audit (a heuristic, described next) nevertheless found "
    "near-identical images across the two folders.",
])
B.h2("3.2", "Data auditing, duplicates and image preprocessing")
B.para("All 7,200 files were pooled and checked for byte-identical files (153 groups of identical files were found, which exact SHA-256 hashing detects). Exact hashing, however, "
       "cannot find *mirrored*, rotated or re-encoded copies of the same slice, which are common in this dataset. Images used by the GANs and the classifier were converted to "
       "one-channel grayscale, resized to **64×64** pixels, and scaled to the range [−1, 1] (the range of the generator’s Tanh output). For FID/KID, real and generated "
       "images were converted identically (grayscale, 64×64, 8-bit, replicated to three channels) so that the Inception network sees both in the same way.")
B.h2("3.3", "Near-duplicate detection and cluster-disjoint partitioning")
B.para("Each image was reduced to 32×32 grayscale, mean-removed and length-normalised; the similarity of two images is the cosine similarity, evaluated against the second image "
       "in all eight orientations (identity, horizontal and vertical flips, three rotations and two transposes). Two images were linked when the similarity was at least 0.98 "
       "or the files were byte-identical, and linked images were merged into **clusters** (connected components). A second stage re-scored the closest held-out pairs at 96×96 "
       "pixels with shifts of ±4 pixels; pairs that looked alike at 32×32 scored about 0.94 at higher resolution, i.e. similar but distinct scans.")
B.figure(FIGS / "original_near_duplicate_pairs.png", "Examples from the audit of the original folders: Testing images (top row) and their near-identical, often mirrored, copies in Training (bottom row). These are real dataset images shown for audit purposes (dataset licence: CC BY 4.0 [11]).", width=6.2)
B.table("Result of the duplicate audit and cluster construction.", [
    ["Quantity", "Value"],
    ["Candidate images pooled (Training + Testing)", "7,200"],
    ["Original Testing images with a near-identical Training copy", "1,076 of 1,600"],
    ["Near-duplicate clusters at threshold 0.98 (largest cluster: 83 images)", f"{audit['n_clusters']:,}"],
    ["Clusters containing images from both original folders", f"{audit['clusters_spanning_original_train_and_test']:,}"],
    ["Quarantined images: 8 clusters with conflicting class labels (30 images), 172 clusters made only of *aug* files, 4 images removed by the second stage", f"{audit['quarantined_images']}"],
    ["Final usable unique images (one representative per cluster)", f"{audit['representatives']:,}"],
    ["Clusters that appear in more than one partition", "0"],
], [5.0, 1.5], size=10, align=["l", "r"])
B.para("One representative per cluster (preferring a non-augmented, originally-Training file) was assigned to train, validation or test by a class-stratified 70/15/15 split "
       "with seed 42, so that no cluster crosses a partition. The split manifest and the three file lists are hash-recorded and were re-verified by automated checks.")
pc = audit["partition_class_counts_representatives"]
B.table("Final cluster-disjoint partitions (unique images per class).", [["Partition"] + [CLN[c] for c in CL] + ["Total"]] + [
    [n.capitalize()] + [f"{pc[n][c]:,}" for c in CL] + [f"{sum(pc[n][c] for c in CL):,}"] for n in ("train", "val", "test")],
    [1.3, 1.0, 1.1, 1.1, 1.0, 1.0], size=10, align=["l", "r", "r", "r", "r", "r"])
B.figure(FIGS / "split_counts.png", "Unique images per partition and class after de-duplication.", width=4.6)
B.note("Residual uncertainty", [
    "The similarity measure is a heuristic with no ground truth. The dataset has **no patient identifiers**, so different slices of the *same patient* cannot be detected and may lie in "
    "different partitions: patient-level independence is **not proven**. Files marked *aug* were removed by name only, and heavily rescaled or re-cropped copies below the "
    "similarity threshold would be missed. The split is therefore better protected against copy-level leakage than the original folders, not proven leak-free.",
    "The cost of the audit is data: only 3,295 of the 7,200 images are unique and usable, and the classes became imbalanced (227 no-tumour training images, 46 in each of "
    "validation and test).",
], size=10.5)
B.h2("3.4", "DCGAN, WGAN-GP and conditional WGAN-GP architectures")
B.para("All three models generate 64×64×1 images from a 100-dimensional noise vector with the same transposed-convolution generator (channel widths 512, 256, 128, 64, 1; "
       "batch normalisation and ReLU in the hidden layers; Tanh output). They differ in the discriminator or critic, the objective and the conditioning (Table 3.3).")
B.table("Comparison of the three GANs.", [
    ["", "DCGAN [3]", "WGAN-GP [4], [5]", "cWGAN-GP (proposed) [2], [5], [8]"],
    ["Generator", "Noise z (100-d) → transposed convolutions", "Same", "Label embedding (50-d) concatenated to z; same convolution stack"],
    ["Discriminator / critic", "Convolutions with batch normalisation; outputs a logit", "Convolutions without batch normalisation; scalar score", "Projection critic: D(x, y) = ψ(h(x)) + E(y)·h(x); no batch normalisation"],
    ["Objective", "Non-saturating BCE", "Wasserstein loss + gradient penalty (λ = 10)", "Same loss; real and fake samples share the label"],
    ["Optimiser [12]", "Adam 2×10⁻⁴, β = (0.5, 0.999)", "Adam 1×10⁻⁴, β = (0.5, 0.9)", "Adam 1×10⁻⁴, β = (0.5, 0.9)"],
    ["Updates for 3,000 generator steps", f"{ver['DCGAN']['critic_or_discriminator_updates']:,} discriminator", f"{ver['WGAN-GP']['critic_or_discriminator_updates']:,} critic (5 per generator step)", f"{ver['cWGAN-GP']['critic_or_discriminator_updates']:,} critic (5 per generator step)"],
    ["Conditioning", "None", "None", "Requested class label; no classifier guidance"],
], [1.1, 1.65, 1.75, 2.0], size=9)
B.figure(NEW / "fig_cwgangp_architecture.png", "Architecture of the proposed cWGAN-GP: label-conditioned generator and projection critic.", width=5.9)
B.h2("3.5", "Training configuration and hardware")
B.table("Training configuration and hardware.", [
    ["Item", "Setting"],
    ["Training data", "The 2,311-image training partition only (hash-verified for each model); validation and test images are never used for GAN training"],
    ["Common GAN settings", "64×64 grayscale, noise dimension 100, batch size 16, seed 42, 3,000 generator updates, no data augmentation"],
    ["Runtime on the Apple GPU (MPS)", f"DCGAN {ver['DCGAN']['runtime_seconds']:.0f} s; WGAN-GP {ver['WGAN-GP']['runtime_seconds']:.0f} s; cWGAN-GP {ver['cWGAN-GP']['runtime_seconds']:.0f} s (cumulative; Low Power Mode was on when checked)"],
    ["Hardware", "Apple MacBook Air, M4 chip, 16 GB unified memory, macOS"],
    ["Software", "Python 3.14.3, PyTorch 2.14.0 (MPS backend, no CPU fallback), torchvision 0.29.1, torch-fidelity 0.4.0 [13]"],
    ["Interrupted run", "The first cWGAN-GP attempt stopped at generator step 2,861 with a non-finite loss; **the cause is unconfirmed**. It was resumed from the verified step-2,500 checkpoint and completed, so the final model is not bit-identical to an uninterrupted run. The abandoned attempt’s logs are preserved."],
], [1.7, 4.8], size=9.5)
B.h2("3.6", "FID/KID generation-quality evaluation")
B.para("Generated images were compared with the 492 real **test** images using torch-fidelity 0.4.0 [13] with its Inception-v3 “pool3” (2,048-dimensional) features and identical preprocessing "
       "for real and generated images. Each model generated 492 images per seed over three generation seeds (1001–1003); the conditional model generated the test partition’s class "
       "counts (196, 122, 46, 128). KID used 100 subsets of 300 images. A **real-versus-real floor** (class-matched random training images against the test images) shows the "
       "score of images that really are from the same distribution. The standard deviations reported later describe *generation-seed* variability only, because each GAN was trained once.")
B.h2("3.7", "Three-condition downstream classifier experiment (A, B and C)")
B.para("A small convolutional network (four convolution blocks of 32, 64, 128 and 256 filters, global average pooling, dropout 0.3, Adam with learning rate 10⁻³, batch size 64, "
       "15 epochs, no augmentation) was trained with three seeds (42–44). The validation partition selects the best epoch; the test partition is read only afterwards. "
       "The three conditions differ only in the training set:")
B.table("Training sets of the three downstream conditions.", [
    ["Condition", "Training images", "Per-class counts (glioma, meningioma, no tumour, pituitary)", "Total"],
    ["A: real only", "Real training images", "918, 566, 227, 600", "2,311"],
    ["B: real + synthetic", "A + 722 cWGAN-GP images per class (labels = requested conditions, unverified)", "1,640, 1,288, 949, 1,322", "5,199"],
    ["C: matched-size real only", "Real training images resampled with replacement to B’s exact counts (2,029 distinct images drawn; at most 12 repeats); no synthetic images", "1,640, 1,288, 949, 1,322", "5,199"],
], [1.35, 2.55, 1.9, 0.7], size=9.5, align=["l", "l", "l", "r"])
B.para("**Why condition C is essential.** B has more images than A, so any gain of B over A could come from the larger and better-balanced training set rather than from the synthetic "
       "images. C gives a classifier the same number of images and the same class mix as B using only real images. Only a gain of B *over C* would indicate a benefit specific to "
       "synthetic data.")
B.h2("3.8", "Ethical considerations and evaluation limitations")
B.bullets([
    "**Not a medical device.** No component was tested clinically or reviewed by clinicians. Predictions and generated images must not guide diagnosis or treatment; healthcare use would "
    "require clinical validation, regulatory review and oversight that are outside this project.",
    "**Synthetic images and labels.** Generated images are synthetic and are not patient scans; the class attached to a generated image is the label that was *requested*, not an "
    "expert-verified diagnosis. Synthetic images can be mistaken for real ones, so the application labels them clearly.",
    "**Data and privacy.** The dataset is public and comes without patient identifiers or consent records that this project could inspect; patient-level "
    "grouping was therefore impossible. The images are used under the CC BY 4.0 licence shown on the Kaggle page (upstream terms may differ) and are not redistributed.",
    "**Label noise and bias.** Eight near-duplicate clusters (30 images) carried conflicting class labels, which indicates label noise in the source data. The classes are imbalanced "
    "and the data come from a limited set of sources, so performance on other scanners or populations is unknown.",
    "**Metric limits.** FID and KID use ImageNet-trained Inception features on small grayscale MRI images and do not measure anatomical or clinical validity. The test set is small "
    "(492 images, 46 no-tumour), and results are from three classifier seeds and one training run per GAN, with no significance tests.",
    "**Honest reporting.** Results are reported as measured, including those that do not favour the proposed model.",
])

# ---- CHAPTER 4 --------------------------------------------------------------------------------------------------------------------------
B.chapter_heading(4, "FABRICATION / SIMULATION / PROGRAM OR CODE / DESIGN")
B.para("This chapter describes the solution that was implemented. It has two parts that are deliberately kept apart: the **research experiments** (Chapters 3 and 5), whose results "
       "are saved files, and the **NeuroVision AI web application**, which presents those results and runs two models on request.")
B.h2("4.1", "GAN model implementation")
B.para("The models are written in PyTorch. The research code is organised as follows (all under the project’s *src/* and *scripts/* folders):")
B.table("Main research code components.", [
    ["File", "Responsibility"],
    ["data_pipeline.py", "Image loading, grayscale/resize/normalise transforms, manifest-based partition dataset"],
    ["dedup_split.py, dedup_refine.py", "Near-duplicate similarity, clustering, quarantine, cluster-disjoint split and the second-stage refinement"],
    ["dcgan_train.py, wgangp_train.py, cwgangp_train.py", "Model definitions, training loops, checkpointing (every 500 updates), sample grids and loss logs; the conditional script also supports resuming"],
    ["dedup_eval_fid_kid.py", "FID/KID evaluation of the three checkpoints against the test partition"],
    ["dedup_downstream.py", "Conditions A, B and C: training, epoch selection on validation, one-time test evaluation, saved predictions"],
    ["run_dedup_gans.py, run_dedup_stage2.py", "Resumable, hash-checked runners that train the GANs and then the downstream and FID/KID stages"],
    ["verify_dedup_experiment.py", "23 automated checks (split integrity, training data, counters, evaluation partitions, preserved earlier results)"],
], [2.35, 4.15], size=9.5)
B.h2("4.2", "Conditional generation and label conditioning")
B.para("The conditional generator (class *CondGenerator*) holds an embedding table of four 50-dimensional vectors, one per class in the dataset order glioma = 0, meningioma = 1, no "
       "tumour = 2, pituitary = 3. The 100-dimensional noise vector and the selected class embedding are concatenated into a 150-dimensional vector, reshaped to 150×1×1 and "
       "passed through five transposed-convolution stages to a 64×64 image (Figure 3.4). The projection critic (*ProjectionCritic*) extracts 512-channel 4×4 features, sums them over "
       "space into a 512-dimensional vector h(x), and outputs ψ(h(x)) + E(y)·h(x). During training the gradient penalty is computed with the label held fixed, and "
       "no classifier guides the generator. A saved checkpoint stores the generator and critic weights, optimiser states, counters and the class-to-index mapping, which the web "
       "application reads to make sure its class order matches.")
B.h2("4.3", "Experiment and result-processing pipeline")
B.para("Each stage writes its outputs, configuration and hashes to *outputs/deduplicated_experiment/*: the split manifest and configuration, per-model checkpoints, metrics, losses and "
       "sample grids, FID/KID metrics, the per-run downstream histories and test predictions, and the summary tables. The verification script checks, among other things, that every "
       "GAN checkpoint was trained on exactly the manifest’s training partition, that every classifier run was evaluated on exactly the test partition, and that earlier experiments "
       "were preserved. The report tables in this document are generated from these saved files by script, and sensitivity and specificity were derived from the saved per-run "
       "test predictions (Section 5.5) without running any model.")
B.h2("4.4", "NeuroVision AI web-application architecture")
B.para("NeuroVision AI is a two-tier local application (Figure 4.1). The browser interface calls a JSON API; the API validates requests, loads the models on first use, runs inference "
       "on the Apple GPU (MPS) or the CPU, and reads the saved result files. The backend never writes to the experiment outputs or the checkpoints.")
B.figure(NEW / "fig_app_architecture.png", "Software architecture of NeuroVision AI.", width=5.5)
B.table("Technology stack, as recorded in the application’s package and requirement files.", [
    ["Layer", "Technology (version)"],
    ["Frontend framework", "React 19.2, TypeScript 6.0, Vite 8.3, React Router 7.18"],
    ["Styling and components", "Tailwind CSS 4.3 with the shadcn/ui component set (Radix primitives, lucide icons)"],
    ["Charts", "Recharts 3.10"],
    ["Backend API", "Python, FastAPI 0.143 with Uvicorn 0.54, Pydantic 2.14"],
    ["AI inference", "PyTorch 2.14.0 and torchvision 0.29.1 (MPS or CPU), Pillow 12.2, NumPy 2.4"],
    ["Testing", "pytest 9.1 with the FastAPI test client; a shell integration smoke test; the TypeScript/Vite production build"],
], [1.7, 4.8], size=9.5)
B.h2("4.5", "FastAPI backend and PyTorch inference")
B.para("The backend (folder *app/backend/*) has four modules: *main.py* (routes, validation, CORS and error handling), *ml.py* (model wrappers), *results.py* (reads the saved result "
       "files) and *config.py* (paths relative to the project root and limits). The endpoints are:")
B.table("API endpoints and their responsibilities.", [
    ["Endpoint", "Responsibility"],
    ["GET /api/health", "Liveness and the research-prototype disclaimer"],
    ["GET /api/models/status", "Device (MPS/CPU), whether the generator and classifier loaded, checkpoint details; states that the project’s own A/B/C classifiers are not available"],
    ["POST /api/classify", "Accepts a PNG or JPEG upload; returns the predicted class, softmax probabilities, timing and caveats"],
    ["POST /api/generate", "Body {class, count 1–16, optional seed}; returns synthetic 64×64 PNG images generated by the cWGAN-GP"],
    ["GET /api/metrics", "FID/KID and A/B/C results read from the saved files"],
    ["GET /api/experiment", "Dataset description, methodology, key findings and the documented limitations"],
    ["GET /api/gallery (+ /image/{id})", "A fixed registry of saved figure sheets labelled real, synthetic or mixed; no arbitrary file access"],
], [2.0, 4.5], size=9.5)
B.para("**Model and checkpoint loading.** Each model is loaded once, on first use, behind a lock, and kept in memory. The generator checkpoint is loaded with *weights_only* and strict "
       "key matching, and its stored class mapping is compared with the application’s. The classifier weights file must match a recorded SHA-256 digest. If a checkpoint is missing, "
       "mismatched or fails to load, the feature is reported as unavailable with an error message; **no substitute model is used and no result is invented**. Seeded generation draws "
       "the noise on the CPU so that the same seed and class give the same images on any device.")
B.table("Input validation and error handling.", [
    ["Case", "Behaviour"],
    ["Upload not an image / unsupported format (e.g. GIF, text)", "JSON error: not_an_image (415) or unsupported_type (415)"],
    ["Empty file; file larger than 10 MB", "empty_file (400); file_too_large (413)"],
    ["Image sides below 32 or above 8,192 pixels", "bad_dimensions (422)"],
    ["Unknown class, count outside 1–16, negative seed", "Request validation error (422) with the offending field"],
    ["Model or checkpoint unavailable", "classifier_unavailable / generator_unavailable (503) with the reason"],
    ["Saved result file missing", "metrics_unavailable / experiment_unavailable (503)"],
    ["Cross-origin request from another site", "Not allowed: CORS is limited to the local Vite origin (port 5173)"],
], [3.0, 3.5], size=9.5)
B.h2("4.6", "React + TypeScript + Vite frontend")
B.para("The frontend (folder *app/frontend/*) is a single-page application with five pages: the **Dashboard** (key results, GAN and classifier charts, model readiness), **Classify MRI** "
       "(drag-and-drop or file-picker upload, preview, prediction with class probabilities), **Generate** (class selector, 4–16 images, optional seed, individual and grid PNG download), "
       "**Gallery** (saved image sheets labelled real, synthetic or mixed) and **Experiment results** (FID/KID and A/B/C tables and charts, class-wise results, dataset notes and limitations). "
       "A navy, teal and off-white theme is defined with Tailwind and shadcn/ui variables; charts use Recharts with error bars; every page shows a research-prototype notice, and "
       "the classification and generation pages show the caveats returned by the API. Figures 4.2 to 4.5 are screenshots of the running application captured for this report.")
B.figure(SHOT / "app_dashboard.png", "NeuroVision AI dashboard (screenshot, top of page): saved FID results, A/B/C chart and key figures.", width=5.3)
B.figure(SHOT / "app_generate.png", "Generate page: eight synthetic images for the requested class “Meningioma” (seed shown on screen), marked SYNTHETIC. The class is a requested label, not a diagnosis.", width=5.3)
B.figure(SHOT / "app_classify.png", "Classify page with a dataset test image. The output comes from a third-party pretrained model (Section 4.7), is a demonstration of the application, and is not an evaluation result.", width=5.3)
B.figure(SHOT / "app_results.png", "Experiment results page (screenshot, top of page): FID and KID charts and table from the saved results.", width=5.3)
B.h2("4.7", "Research classifiers versus the application’s classifier")
B.note("Critical distinction", [
    "The A, B and C classifiers of the research experiment **did not save model checkpoints**: only their metrics and per-image test predictions were kept, and they were not "
    "retrained for the application. They therefore cannot classify a new uploaded image.",
    "The application’s *Classify MRI* page uses a **third-party pretrained EfficientNet-B3** [14] from the open-source repository *brain-tumor-classifier* [15] (Apache-2.0 licence; one-channel "
    "input resized to 224×224; four output classes in the order glioma, meningioma, no tumour, pituitary). **Its predictions are not results of condition A, B or C.**",
    "That model was trained on an earlier version of the Kaggle dataset. Because this project found near-duplicates across that dataset’s train and test folders, its published accuracy "
    "may be inflated, and its accuracy on this project’s cluster-disjoint test set is **unknown**. The application performs **no out-of-distribution detection**: any image, even one that is not "
    "a brain MRI, receives one of the four labels, and the confidence is a softmax probability, not a calibrated clinical certainty.",
], fill="FDF1DC", size=10.5)
B.h2("4.8", "Local startup procedure")
B.para("After the one-time setup (a Python virtual environment for the backend with the pinned requirements, and *npm install* for the frontend), both servers are started from the "
       "project root with one command:")
B.para("./app/run_dev.sh", AL.CENTER, 11, italic=False, bold=True, after=4)
B.para("The backend then listens on http://127.0.0.1:8000 (interactive API documentation at /docs) and the frontend on http://localhost:5173, which is the address opened in the browser. "
       "The launcher refuses to start if either port is already in use, and Ctrl+C stops both servers. Configuration (allowed origin, upload limit, optional checkpoint paths) uses "
       "environment variables documented in an example file that contains no secrets.")
B.h2("4.9", "Tests performed")
B.table("Application tests and their recorded outcomes.", [
    ["Test", "What it checks", "Recorded outcome"],
    ["Backend pytest suite (16 tests)", "Health and status; both models load with the real checkpoints; metrics endpoint values equal the saved files (including FID 154.7/177.8/182.1 and A/B/C accuracy 0.817/0.839/0.869); generation shape, class dependence and seed reproducibility; invalid input; classification of PNG/JPEG and of local dataset images; error cases; an unavailable model is reported, not substituted; gallery path-traversal blocked; CORS restricted; no hard-coded user paths", "16 passed"],
    ["Integration smoke test (6 checks)", "Through the Vite proxy: page served, health, models available, DCGAN FID value, generation of 4 images, rejection of a non-image upload", "6/6 passed"],
    ["Frontend production build", "TypeScript type-check and Vite build", "Completed without errors"],
    ["Manual browser checks", "Dashboard, classification (upload and result), generation, gallery and results pages in a real browser; the screenshots in this chapter were taken during these checks", "Pages rendered and worked as expected"],
    ["PNG grid download", "Download of the generated grid image from the Generate page", "Reported as confirmed in the browser by the author; not covered by an automated test"],
], [1.55, 3.55, 1.4], size=9)
B.para("There is **no automated browser-level (end-to-end) test suite**; frontend behaviour was checked manually. Outputs produced during these tests are plumbing checks of the application and are "
       "not scientific results.")

# ---- CHAPTER 5 --------------------------------------------------------------------------------------------------------------------------
B.chapter_heading(5, "RESULTS AND INTERPRETATION")
B.para("All numbers in this chapter come from the saved result files of the final de-duplicated experiment (*outputs/deduplicated_experiment/*); sensitivity and specificity were "
       "derived from the saved predictions of that experiment. Results of the earlier experiment on the original folders (which contained near-duplicates between training and test "
       "data) are superseded and are **not** used or compared here.")
B.h2("5.1", "Dataset audit")
B.table("Dataset audit and final split.", [
    ["Quantity", "Value"],
    ["Initial candidate images", "7,200"],
    ["Original Testing images with a near-identical Training copy (audit of the original folders)", "1,076 of 1,600"],
    ["Quarantined images", "207"],
    ["Final usable unique images", "3,295"],
    ["Training / validation / test images", "2,311 / 492 / 492"],
    ["Test images per class (glioma, meningioma, no tumour, pituitary)", "196, 122, 46, 128"],
    ["Patient-level independence", "Not proven (no patient identifiers)"],
], [4.7, 1.8], size=10, align=["l", "r"])
B.para("The audit shows why the original split could not be trusted: roughly two thirds of its test images had a near-copy in training. The corrected split is much smaller, and the class "
       "imbalance is stronger, but its scores are not inflated by copies. Patient-level leakage through different slices of the same patient cannot be excluded.")
B.h2("5.2", "GAN generation quality (FID and KID)")
B.table("FID and KID (×1000) against the 492 test images; mean ± standard deviation over 3 generation seeds; lower is better.", [
    ["Model", "FID", "KID × 1000"],
    gan_row(FLOOR_KEY, "Real-vs-real reference floor"),
    gan_row("DCGAN", "DCGAN"),
    gan_row("cWGAN-GP", "cWGAN-GP"),
    gan_row("WGAN-GP", "WGAN-GP"),
], [3.0, 1.75, 1.75], size=10.5, align=["l", "c", "c"], bold_rows=(2,))
B.figure(FIGS / "fid_kid_bar_chart.png", "FID and KID (×1000) of the three GANs and the real-versus-real floor; error bars show the standard deviation over 3 generation seeds.", width=6.0)
B.para("**DCGAN achieved the best FID and KID** of the three generators (154.7 and 129.4), with a wide margin over the other two relative to the seed spread. The proposed cWGAN-GP was "
       "second (177.8 and 157.6) and WGAN-GP last (182.1 and 163.5); the 4.3-point FID difference between these two is only a few seed standard deviations and could change across "
       "training runs. All three are far above the reference floor of 34.2, i.e. none of the generators matches the real distribution. The comparison is not compute-matched (DCGAN "
       "used 3,000 discriminator updates, the WGAN variants 15,000 critic updates), each GAN was trained once, and FID is biased for small samples; the metrics also rely on "
       "Inception features learned from colour photographs, so they **do not establish anatomical or clinical validity**.")
B.h2("5.3", "Generation findings and class conditioning")
B.figure(FIGS / "sample_grids_real_vs_generated.png", "Real test images (top left) and samples from DCGAN, WGAN-GP and cWGAN-GP; the rows of the conditional model are glioma, meningioma, no tumour and pituitary.", width=5.6)
B.para("All three GANs produce head-shaped, MRI-like images with soft internal structure. None shows an identifiable tumour, whereas the real images show clear lesions and fine detail. "
       "For the cWGAN-GP the requested class changes the output distribution (the no-tumour images are visibly brighter), but the evidence for *tumour-specific* anatomy is weak, as the "
       "per-class analysis shows.")
cls_rows = [["Requested class", "n generated = n real", "FID", "KID × 1000", "Reliability"]]
for r in gm["per_class_cwgangp"]:
    cls_rows.append([CLN[r["class"]], str(r["n_generated_per_seed"]), f"{f(r['fid_mean'])} {pm} {f(r['fid_std'])}", f"{f(r['kid_mean'] * 1000)} {pm} {f(r['kid_std'] * 1000)}",
                     "indicative only (n < 100)" if r["n_real"] < 100 else "small for 2,048-d FID"])
B.table("Per-class FID/KID of the cWGAN-GP (each requested class against the real test images of that class).", cls_rows, [1.4, 1.35, 1.2, 1.2, 1.35], size=9.5, align=["l", "c", "c", "c", "l"])
B.para("Matching each generated class against each real class (KID × 1000), only the meningioma row is closest to its own real class, the glioma and no-tumour labels are the closest "
       "generated label for their own real class, and pituitary is not separated. With 46 to 196 images per class, per-class FID is strongly biased and should not be compared across classes. "
       "**The generator therefore did not demonstrate reliable tumour-specific anatomy**, and the requested labels are conditioning inputs, not expert-verified diagnoses.")
B.figure(FIGS / "cwgangp_samples_by_class.png", "cWGAN-GP samples at step 3,000: rows are the requested classes, columns share the same eight noise vectors.", width=5.2)
B.h2("5.4", "Downstream classifier comparison (A, B, C)")
rows = [["Condition", "Training examples", "Test accuracy", "Macro-F1", "Validation accuracy"]]
for key, name in (("A_real_only", "A: real only"), ("B_real_plus_cwgangp_synthetic", "B: real + synthetic"), ("C_real_only_matched_composition", "C: matched-size real only")):
    c = cond[key]
    rows.append([name, f"{c['n_train']:,}", f"{c['accuracy']['mean']:.3f} {pm} {c['accuracy']['std']:.3f}", f"{c['macro_f1']['mean']:.3f} {pm} {c['macro_f1']['std']:.3f}", f"{c['val_accuracy']['mean']:.3f}"])
B.table("Downstream classification on the 492 test images (mean ± standard deviation over 3 seeds).", rows, [1.9, 1.2, 1.2, 1.2, 1.0], size=10.5, align=["l", "r", "c", "c", "c"], bold_rows=(3,))
B.figure(FIGS / "accuracy_A_B_C.png", "Test accuracy, test macro-F1 and validation accuracy of conditions A, B and C (dots are individual seeds).", width=6.0)
pdiff = ds["paired_differences"]
B.table("Paired per-seed differences (seeds 42, 43, 44).", [
    ["Difference", "Accuracy per seed", "Mean", "Macro-F1 per seed", "Mean"],
    ["B − A", ", ".join(f"{v:+.3f}".replace("-", M) for v in pdiff["accuracy"]["B_minus_A"]), f"{pdiff['accuracy']['mean_B_minus_A']:+.3f}",
     ", ".join(f"{v:+.3f}".replace("-", M) for v in pdiff["macro_f1"]["B_minus_A"]), f"{pdiff['macro_f1']['mean_B_minus_A']:+.3f}"],
    ["C − A", ", ".join(f"{v:+.3f}".replace("-", M) for v in pdiff["accuracy"]["C_minus_A"]), f"{pdiff['accuracy']['mean_C_minus_A']:+.3f}",
     ", ".join(f"{v:+.3f}".replace("-", M) for v in pdiff["macro_f1"]["C_minus_A"]), f"{pdiff['macro_f1']['mean_C_minus_A']:+.3f}"],
    ["B − C", ", ".join(f"{v:+.3f}".replace("-", M) for v in pdiff["accuracy"]["B_minus_C"]), f"{pdiff['accuracy']['mean_B_minus_C']:+.3f}".replace("-", M),
     ", ".join(f"{v:+.3f}".replace("-", M) for v in pdiff["macro_f1"]["B_minus_C"]), f"{pdiff['macro_f1']['mean_B_minus_C']:+.3f}".replace("-", M)],
], [0.9, 2.0, 0.7, 2.2, 0.7], size=9.5, align=["l", "c", "c", "c", "c"])
B.para("Adding the cWGAN-GP images to the real data (B) beat real-only training (A) in all three seeds (mean accuracy +0.022, macro-F1 +0.035). **However, the matched-size real-only control (C) "
       "achieved the highest mean accuracy (0.869) and macro-F1 (0.853)**, scoring above B on average (+0.030 accuracy) and in two of the three seeds. With a 492-image test set (a single run has "
       "a 95% sampling interval of about ±3 accuracy points), three seeds and seed standard deviations near 0.02, B and C cannot be separated statistically, and no significance test was run. "
       "**The experiment therefore does not demonstrate an advantage of synthetic augmentation beyond the added training volume, and the point estimates favour the control.**")
B.h2("5.5", "Class-wise findings, confusion matrices and sensitivity/specificity")
B.figure(FIGS / "confusion_matrices_A_B_C.png", "Mean confusion matrices over three seeds for conditions A, B and C (counts on the 492 test images).", width=6.2)
pcf = [["Class (test n)"] + [f"{k}: F1 / recall" for k in "ABC"]]
for c in CL:
    n = {"glioma": 196, "meningioma": 122, "notumor": 46, "pituitary": 128}[c]
    pcf.append([f"{CLN[c]} ({n})"] + [f"{cond[key]['per_class_f1_mean'][c]:.2f} / {cond[key]['per_class_recall_mean'][c]:.2f}"
                                    for key in ("A_real_only", "B_real_plus_cwgangp_synthetic", "C_real_only_matched_composition")])
B.table("Per-class F1 and recall (mean over seeds).", pcf, [1.6, 1.6, 1.6, 1.7], size=10, align=["l", "c", "c", "c"])
B.para("The largest confusion in every condition is glioma predicted as meningioma (on average 26, 31 and 16 of 196 glioma images for A, B and C). The no-tumour class, with only 46 test "
       "images, is the least reliable: its F1 rises from 0.66 (A) to 0.74 (B) and 0.80 (C), but each value rests on a handful of images.")
sr = [["Condition", "Tumour vs no-tumour: sensitivity", "Tumour vs no-tumour: specificity"]]
for k in "ABC":
    tv = der["conditions"][k]["tumour_vs_notumor"]
    sr.append([{"A": "A: real only", "B": "B: real + synthetic", "C": "C: matched-size real only"}[k], f"{tv['sensitivity']['mean']:.3f} {pm} {tv['sensitivity']['sd']:.3f}", f"{tv['specificity']['mean']:.3f} {pm} {tv['specificity']['sd']:.3f}"])
B.table("Derived sensitivity and specificity for detecting “any tumour” (glioma, meningioma or pituitary; 446 images) versus “no tumour” (46 images), mean ± sd over 3 seeds.", sr, [2.3, 2.1, 2.1], size=10, align=["l", "c", "c"])
B.para("These values were computed from the saved test predictions (positive class = any tumour class) and they reproduce the saved accuracies exactly; they are *derived* figures, not "
       "separately recorded results. All three conditions detect tumour-bearing images with high sensitivity (about 0.96–0.97), but specificity, i.e. the ability to keep no-tumour images "
       "out of the tumour classes, differs: 0.67 for A, 0.75 for B and 0.91 for C. The specificity rests on only 46 no-tumour images, so these numbers are very uncertain and are not "
       "clinical performance estimates.")
B.figure(NEW / "fig_sens_spec.png", "Derived sensitivity and specificity (left) and per-class sensitivity (right) for conditions A, B and C, from the saved test predictions.", width=6.2)
B.h2("5.6", "Application implementation and testing results")
B.para("NeuroVision AI was implemented as described in Chapter 4 and tested as listed in Table 4.5: 16 backend tests passed, the 6-check integration smoke test passed, the TypeScript/Vite "
       "production build completed, and the dashboard, classification, generation, gallery and results pages were checked manually in a browser (the generated-grid PNG download is "
       "reported by the author as confirmed in the browser). No automated browser-level test suite exists. The tests establish that the application runs the real models, serves the "
       "saved results unchanged and rejects invalid input; they do not measure the scientific quality of the generator or of the third-party classifier. In particular, a confident prediction "
       "on a test image in the Classify page is a plumbing check and **not evidence of clinical accuracy**.")
B.h2("5.7", "What the results support and do not support")
B.table("Summary of supported and unsupported statements.", [
    ["Supported by the results", "Not supported"],
    ["DCGAN gave the lowest FID and KID on this split; cWGAN-GP was second and WGAN-GP last", "That the proposed hybrid is the best generator"],
    ["Adding cWGAN-GP images improved mean accuracy and macro-F1 over real-only training (B over A) in all three seeds", "That synthetic images improve classification beyond added training volume"],
    ["A size- and class-mix-matched real-only control scored at least as well on average", "That the generated labels correspond to real tumour classes"],
    ["The requested label changes the generated distribution (clearest for no tumour)", "That the images are anatomically or clinically meaningful"],
    ["The split is protected against copy-level leakage (0 clusters cross partitions)", "That the result is free of patient-level leakage"],
    ["The application runs the real models and shows the saved results", "That any ranking persists across other training seeds, longer training or other hyperparameters; or any estimate of performance on new patients"],
], [3.3, 3.2], size=9.5)

# ---- CHAPTER 6 --------------------------------------------------------------------------------------------------------------------------
B.chapter_heading(6, "CONCLUSION AND FUTURE SCOPE")
B.h2("6.1", "Conclusion")
B.para("This micro project audited a public brain-tumour MRI dataset, found that its original test images were not independent of the training images, and rebuilt a cluster-disjoint "
       "split of 3,295 unique images. On that split three GANs were compared. **DCGAN achieved the best generation metrics** (FID 154.7, KID×1000 129.4), the proposed conditional WGAN-GP "
       "was second (177.8, 157.6) and WGAN-GP third (182.1, 163.5). In the downstream experiment, adding synthetic images raised the mean test accuracy over real-only training (0.817 to 0.839), "
       "but **the matched-size real-only control achieved the best mean accuracy (0.869) and macro-F1 (0.853)**, so the study does not demonstrate a benefit of synthetic augmentation beyond "
       "added training volume. The generator produced MRI-like images but did not demonstrate reliable tumour-specific anatomy.")
B.para("The work was packaged as NeuroVision AI, a tested React + TypeScript and FastAPI + PyTorch application that presents the saved results, generates synthetic samples with the saved "
       "cWGAN-GP checkpoint and demonstrates a third-party pretrained classifier, with the research limits displayed in the interface. The project demonstrates careful implementation, "
       "fair comparison and honest reporting; it does not show that the proposed model outperforms the baselines, and it is not a clinically validated system.")
B.h2("6.2", "Limitations")
B.bullets([
    "Small, imbalanced test set (492 images; 46 no-tumour); no significance tests; three classifier seeds and a single training run per GAN.",
    "Patient-level independence is unproven; near-duplicate detection is heuristic and may miss rescaled or re-cropped copies. The dataset download record is unverified and its upstream "
    "sources may have separate terms.",
    "FID/KID use ImageNet Inception features on 64×64 grayscale MRI; short GAN training (3,000 updates) that is not compute-matched between DCGAN and the WGAN variants; the "
    "cWGAN-GP run was interrupted at step 2,861 and resumed (cause unconfirmed).",
    "Synthetic labels are requested conditions, not verified diagnoses; weak evidence for tumour-specific generation.",
    "The application’s classifier is third-party, may have inflated published accuracy, has unknown accuracy on this project’s test set, and has no out-of-distribution detection; the "
    "application has no automated browser-level tests.",
])
B.h2("6.3", "Future scope")
B.bullets([
    "Use larger and more diverse datasets, ideally with patient identifiers so that splits can be made at patient level.",
    "Run more independent GAN training runs and classifier seeds, with significance testing and compute-matched baselines and longer training.",
    "Improve conditional generation (for example stronger conditioning, larger resolution, or expert-reviewed labels) and evaluate class consistency of the generated images.",
    "Evaluate medical-image structure directly, for example with expert review or domain-trained feature extractors instead of ImageNet features alone.",
    "Save a research classifier checkpoint (for example from condition C) if new-image inference with the research classifier is needed, and evaluate it on the cluster-disjoint test set.",
    "Add automated browser-level tests and out-of-distribution handling to NeuroVision AI.",
    "Before any healthcare deployment: clinical validation, regulatory review, privacy assessment and continuous clinical oversight.",
])

# ---- REFERENCES -------------------------------------------------------------------------------------------------------------------------
B.para("REFERENCES", AL.CENTER, 14, True, before=0, after=10, page_break=True, outline=0)
refs = [
    "I. J. Goodfellow, J. Pouget-Abadie, M. Mirza, B. Xu, D. Warde-Farley, S. Ozair, A. Courville and Y. Bengio, “Generative Adversarial Networks,” arXiv:1406.2661, 2014.",
    "M. Mirza and S. Osindero, “Conditional Generative Adversarial Nets,” arXiv:1411.1784, 2014.",
    "A. Radford, L. Metz and S. Chintala, “Unsupervised Representation Learning with Deep Convolutional Generative Adversarial Networks,” arXiv:1511.06434, 2015 (submitted to ICLR 2016).",
    "M. Arjovsky, S. Chintala and L. Bottou, “Wasserstein GAN,” arXiv:1701.07875, 2017.",
    "I. Gulrajani, F. Ahmed, M. Arjovsky, V. Dumoulin and A. Courville, “Improved Training of Wasserstein GANs,” arXiv:1704.00028, 2017.",
    "M. Heusel, H. Ramsauer, T. Unterthiner, B. Nessler and S. Hochreiter, “GANs Trained by a Two Time-Scale Update Rule Converge to a Local Nash Equilibrium,” in *Advances in Neural Information Processing Systems 30 (NIPS 2017)*; arXiv:1706.08500.",
    "M. Bińkowski, D. J. Sutherland, M. Arbel and A. Gretton, “Demystifying MMD GANs,” in *International Conference on Learning Representations (ICLR)*, 2018; arXiv:1801.01401.",
    "T. Miyato and M. Koyama, “cGANs with Projection Discriminator,” in *International Conference on Learning Representations (ICLR)*, 2018; arXiv:1802.05637.",
    "United Nations, “Transforming our world: the 2030 Agenda for Sustainable Development,” 2015. https://sdgs.un.org/2030agenda",
    "Karunya Institute of Technology and Sciences, official website (mission statement and focus areas). https://www.karunya.edu/ and https://kcode.karunya.edu/about-us (accessed 27 October 2026).",
    "M. Nickparvar, “Brain Tumor MRI Dataset,” Kaggle, Version 2, licence CC BY 4.0. https://www.kaggle.com/datasets/masoudnickparvar/brain-tumor-mri-dataset (accessed October 2026). Compiled from the figshare, SARTAJ and Br35H datasets.",
    "D. P. Kingma and J. Ba, “Adam: A Method for Stochastic Optimization,” in *International Conference on Learning Representations (ICLR)*, 2015; arXiv:1412.6980.",
    "torch-fidelity (version 0.4.0), open-source package for FID, KID and Inception score. https://github.com/toshas/torch-fidelity",
    "M. Tan and Q. V. Le, “EfficientNet: Rethinking Model Scaling for Convolutional Neural Networks,” in *International Conference on Machine Learning (ICML)*, 2019; arXiv:1905.11946.",
    "Phi-007, “brain-tumor-classifier,” open-source repository (Apache-2.0), EfficientNet-B3 brain MRI classifier. https://github.com/Phi-007/brain-tumor-classifier",
]
for i, r_ in enumerate(refs, 1):
    p = B.para("", AL.JUSTIFY, 11, after=4, left=0.45, first=-0.45, line=1.1)
    rich(p, f"[{i}] " + r_, 11)

# ---------------------------------------------------------------- page numbers in the TOC -----------------------------------------------------------
toc_pages = json.load(open(TOC_JSON)) if TOC_JSON.exists() else {}
from docx.table import _Cell
tbl = doc.tables[0]
last = tbl.rows[-1]._tr
new_tr = copy.deepcopy(last)
last.addnext(new_tr)                                  # extra row for REFERENCES (copy of the last chapter row)
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
    label = (tcs[-2].text.strip() if len(tcs) == 3 else tcs[-2].text.strip())
    if len(tcs) == 4:                                  # sub-section rows: key = "1.1 Title"
        label = tcs[1].text.strip()
    pg = toc_pages.get(label)
    if pg:
        set_text(page_cell.paragraphs[0], str(pg))

# ---------------------------------------------------------------- sections, footer page numbers ---------------------------------------------------------
final_sect = body.find(qn("w:sectPr"))
sect1 = copy.deepcopy(final_sect)
pg_num = sect1.find(qn("w:pgNumType"))
pg_num.set(qn("w:fmt"), "lowerRoman"); pg_num.set(qn("w:start"), "1")
tp = OxmlElement("w:titlePg")
sect1.append(tp)
ppr = section_break_par.find(qn("w:pPr"))
if ppr is None:
    ppr = OxmlElement("w:pPr"); section_break_par.insert(0, ppr)
ppr.append(sect1)

# the template's footer holds an empty text box; add a centred PAGE field beneath it
footer = doc.sections[-1].footer
fp = footer.add_paragraph()
fp.alignment = AL.CENTER
run = fp.add_run()
for kind, txt in (("begin", None), ("instr", " PAGE "), ("end", None)):
    if kind == "instr":
        el = OxmlElement("w:instrText"); el.set(qn("xml:space"), "preserve"); el.text = txt
    else:
        el = OxmlElement("w:fldChar"); el.set(qn("w:fldCharType"), kind)
    run._r.append(el)
run.font.name, run.font.size = "Times New Roman", Pt(11)

# ---------------------------------------------------------------- evaluation page (template, unchanged) ------------------------------------------------
final_sect_el = body.find(qn("w:sectPr"))
first_eval = eval_block[0]
pb = OxmlElement("w:pageBreakBefore")
epPr = first_eval.find(qn("w:pPr"))
if epPr is None:
    epPr = OxmlElement("w:pPr"); first_eval.insert(0, epPr)
epPr.append(pb)
for el in eval_block:
    final_sect_el.addprevious(el)

doc.core_properties.title = TITLE
doc.core_properties.author = "Ajai Kumar N"
doc.core_properties.subject = "25AI2004 Artificial Intelligence in Healthcare: micro project e-report"
doc.save(OUT)
print("saved", OUT)
