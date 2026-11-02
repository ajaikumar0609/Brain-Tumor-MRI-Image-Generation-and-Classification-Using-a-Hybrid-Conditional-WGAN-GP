# Submission checklist (final package)
Verification of the experiment: `scripts/verify_dedup_experiment.py` passed **23/23** checks. Package files were opened or parsed and cross-checked against the saved results (`MANIFEST.md`).

## Readiness
**Ready to submit once the placeholders are filled in and the open items below are decided.** The results are modest and honestly reported: DCGAN had the best FID/KID; the matched-size real-only control had the highest mean downstream accuracy; no benefit of the hybrid GAN or of synthetic augmentation is shown. The experiment is **not** proven free of patient-level leakage.

## Files to submit
`FINAL_REPORT.pdf` (and `.docx` if an editable copy is wanted), `IA3_Presentation.pptx`, `VIVA_QUESTIONS.md` (for your own preparation), `IA3_SOURCE_CODE.zip` if source code is requested, this checklist and `README.md` if helpful. Keep `MANIFEST.md` for your records.

## Key measured results (test set n=492; mean ± sd over 3 seeds)
| Item | Result |
|---|---|
| FID (lower is better) | DCGAN 154.7; cWGAN-GP 177.8; WGAN-GP 182.1; real-vs-real floor 34.2 |
| KID x1000 | DCGAN 129.4; cWGAN-GP 157.6; WGAN-GP 163.5 |
| Test accuracy A / B / C | 0.817 ± 0.027 / 0.839 ± 0.020 / 0.869 ± 0.021 |
| Macro-F1 A / B / C | 0.786 / 0.821 / 0.853 |
| Validation accuracy (epoch selection only) A / B / C | 0.812 / 0.827 / 0.877 |

## Disclosures that must stay in anything you submit
Cluster-aware split method and residual patient-level uncertainty; small test set and no-tumour imbalance; earlier leakage-affected experiment is preliminary and superseded; conditional GAN's limited, not tumour-specific, conditioning; 3 seeds and one training run per GAN; unconfirmed cause of the non-finite loss at cWGAN-GP step 2,861 (resumed from step 2,500); dataset matched to Kaggle v2 (CC BY 4.0) but download record unverified; no clinical claims.

## Open items for you
1. Fill in the two remaining placeholders, **guide / faculty** and **submission date**, in the report (DOCX, then regenerate or edit the PDF), the presentation title slide and the README. Student name, register number, programme and institution are already filled in.
2. **Dataset provenance: identified, not proven.** The data match Kaggle's Brain Tumor MRI Dataset v2 (Nickparvar, CC BY 4.0) on count, per-class split and size, but no local download record exists. Check your own Kaggle/browser download history if you want to confirm, and cite the dataset in your report.
3. Read the report and slides yourself. The figures and numbers are generated from saved files; the wording is hand-written and hedged.
4. **Open `IA3_Presentation.pptx` in PowerPoint or Keynote and check every slide.** Keynote is installed here but could not be driven from the command line, so there is no genuine render. An approximate shape-based preview (`slide_preview/`, with `PREVIEW_REVIEW.md`) was produced and led to two small fixes (slide 4 line breaks, slide 5 symbol); the preview is not a PowerPoint/Keynote render and is not a visual verification. Slides flagged as possible issues in the review: 7, 8, 9, 10, 11, 14 (small chart text, tight spacing on slide 11).
5. The package contains no dataset, weights or checkpoints. If your institution requires them, check the licences first.

## Not for submission (internal)
Everything under `outputs/` outside `submission/` and `deduplicated_experiment/` (earlier, superseded experiments), all `*.prev-*` versions, `_exploratory_attempt_threshold_0.99/`, `gan/cwgangp.failed-attempt-*`, `_build_history/`, checkpoints and `external_models/`.
