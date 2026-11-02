> **SUPERSEDED (2026-10-12).** This document describes the earlier experiment on the original `archive/Training` / `archive/Testing` folders, which a later audit showed share many near-identical images (about two thirds of the original test images have a near-copy in training), so its test numbers are optimistic. The final, cluster-disjoint re-evaluation is in `outputs/deduplicated_experiment/` (start with `FINAL_REPORT.md` and `SUBMISSION_CHECKLIST.md`). Old and new numbers are not comparable.

# Final submission checklist - Brain Tumor MRI Generation and Classification Using a Hybrid Conditional WGAN-GP
Audit date: 2026-10-12 (final editorial and evidence audit; no training was run, no dependencies added).

## Verdict: NOT an unqualified "ready to submit"
The numbers in the documents match the saved results, the documents agree with each other, and the references are checked. But the audit found a **material
limitation in the data itself** (below). The documents now disclose it prominently, so they can be submitted **honestly as provisional**; they must not be presented
as held-out generalisation results. The proper fix is a de-duplicated rerun (not done: outside this audit's no-training scope).

## 1. Critical finding (new in this audit): train/test near-duplicates
- Exact SHA-256 hashing finds 0 identical Training/Testing files, but a near-duplicate audit (`scripts/audit_near_duplicates.py`; 32x32 correlation over 8 orientations) finds
  **1,076 of 1,600 Testing images (67%) with a near-identical, mostly mirrored, copy in Training** (bimodal: 1,076 at >=0.999 vs 11 at 0.99-0.999; 99.8% same label;
  250 sampled pairs confirmed at 128x128; 12 closest pairs inspected visually: `outputs/final_audit/closest_testing_training_pairs.png`).
- **627 of 1,120 CNN-validation images (56%)** have a copy in the CNN-training partition (the 44 exact duplicates were only the tip).
- Condition C test accuracy: **0.925** with a near-copy in Training (n=1,087), **0.750** without (n=513), **0.618** clearly different (n=273).
- Consequences: test accuracies are optimistic; validation epoch selection is optimistic; the FID/KID reference overlaps GAN training data (not held-out); the 95.94%
  pretrained-classifier score is uninformative; whether A, B, C rank the same on a de-duplicated split is unknown. Predictions for A and B were not saved, so only C could be split.
- Heuristic, not ground truth. Evidence files: `outputs/final_audit/near_duplicate_audit.json`, `near_duplicate_followup.json`.
- **Recommended fix (needs your go-ahead; about 45-60 min compute):** cluster-aware de-duplicated split -> retrain the cWGAN-GP on the de-duplicated training set -> rerun A/B/C saving predictions -> FID/KID vs a de-duplicated reference.

## 2. Verified artifacts (all exist and open)
- Report: `outputs/final_report.md` | Slides outline (16 slides): `outputs/ia3_slides_outline.md` | Viva Q&A (30): `outputs/ia3_viva_questions.md`
- Tables/figures: `outputs/gan_comparison/final_comparison.csv/.png`, `fid_kid_bar_chart.png`, `sample_grids_real_vs_generated.png`, `outputs/downstream_classification_matched/accuracy_A_B_C.png`, `comparison_A_B_C.csv`, `confusion_matrices_A_B_C.png`
- Experiment outputs: `outputs/downstream_classification_clean/` (A, B), `outputs/downstream_classification_matched/` (C), `outputs/gan_comparison/` (FID/KID), GAN checkpoints/logs in `outputs/{dcgan_3000,wgangp_3000,cwgangp_3000,cwgangp_clean_3000}/`
- Audit/process: `outputs/autopilot/OVERNIGHT_RESULT.md`, `outputs/final_audit/`, `scripts/IA3_AUTOPILOT.md`
- Earlier versions kept (not deleted): `*.prev-*` files, including `outputs/*.prev-audit-20261012-120911.md` (pre-audit report/slides/viva).

## 3. Key measured results (verified against saved files; every decimal in the three documents matched a saved value)
| Item | Result |
|---|---|
| FID / KID x1000 (vs Testing, n=1,600, 3 gen seeds) | DCGAN 133.8 / 118.8 < cWGAN-GP 147.3 / 135.3 < WGAN-GP 160.8 / 149.0; real-vs-real floor 14.1 / 0.7 |
| Downstream TEST accuracy (mean +/- sd, seeds 42-44) | A real-only 0.811 +/- 0.047; B real+clean synthetic 0.852 +/- 0.017; C matched-size real 0.869 +/- 0.027 |
| B-C per seed | -0.0225, -0.0288, -0.0006 (C >= B every seed; no evidence of benefit beyond training-set size; no significance test) |
| Validation accuracy (selection only) | A 0.855-0.905; B 0.904-0.918; C 0.897-0.942 |
| Training | 3,000 generator updates each; DCGAN 3,000 D updates (204 s), WGAN variants 15,000 critic updates (~1,200 s); MPS; all finite; cWGAN-GP run resumed from step 500 |
| Conditioning | class-dependent output (clearest for notumor) but not shown tumour-specific; none of the GANs shows identifiable tumours |
| References | 1-6 verified on arXiv (titles/authors/years); reference 7 (dataset) unverifiable - replaced by a neutral statement |

## 4. Required disclosures (all now in the report, slides and viva)
Near-duplicate finding; proposed hybrid is not the best generator; no downstream benefit shown beyond sample count; 3 seeds / 1 GAN run each / no significance tests;
short training; unverified synthetic labels; Inception features on 64x64 grayscale MRI; first (leaky) run preserved as preliminary; non-finite-loss incident with
Metal command-buffer error, cause **unconfirmed**; Testing reused for FID/KID and a pretrained-classifier check; Condition C proposed by an external reviewer model and validated by Claude; no clinical claims.

## 5. Unresolved issues (need your decision)
1. De-duplicated rerun (section 1): do it, or submit as provisional with the disclosure.
2. **Dataset provenance/licence:** the data looks like a re-balanced variant (file names `Tr-gl_*`, plus 100 `Tr-aug-me_*` / 103 `Te-aug-me_*` augmented files; 1,400/400 per class vs the public 5,712/1,311 split). Confirm the Kaggle page you downloaded and cite it.
3. Metal command-buffer error / non-finite loss: cause unknown (reran cleanly; reproduced numbers).
4. Report prose is LLM-written: numbers and structure were audited, but read every sentence yourself before submitting.
5. Mac was on battery for most of the work (power-loss risk only affects further runs).

## 6. What to submit / what not to
- **Submit:** `outputs/final_report.md`, `outputs/ia3_slides_outline.md` (build slides from it), `outputs/ia3_viva_questions.md`, and the figures/tables in section 2.
- **Keep internal (do not submit unless asked):** all `*.prev-*` files, `outputs/downstream_classification/` (preliminary leaky run), `outputs/autopilot/`, smoke-test directories (`*_smoke`), `outputs/cwgangp_500/`, checkpoints (large), `external_models/`.
