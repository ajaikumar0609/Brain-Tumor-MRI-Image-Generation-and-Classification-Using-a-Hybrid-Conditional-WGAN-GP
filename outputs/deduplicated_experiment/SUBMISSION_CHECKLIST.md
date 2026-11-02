# Submission checklist (de-duplicated experiment)
Verification: `scripts/verify_dedup_experiment.py` → **23/23 checks passed** (`verification.json`, `verification.log`). Every decimal in the generated documents is read from the saved result files (`scripts/build_dedup_report.py`).

## Submission readiness
**Ready to submit as the primary results, with the disclosures below.** It is *not* proven leak-free: copies were removed but same-patient slices could not be, the test set is small, and the conclusions are modest. Do not describe the results as clinically meaningful or as showing a benefit of the hybrid GAN.

## Files to submit
- `outputs/deduplicated_experiment/FINAL_REPORT.md` (primary report), `ia3_slides_outline.md`, `ia3_viva_questions.md`, `results_analysis.md`.
- Figures/tables: `gan_comparison/fid_kid_bar_chart.png`, `gan_comparison/sample_grids.png`, `gan_comparison/fid_kid_results.csv`, `downstream/accuracy_A_B_C.png`, `downstream/comparison_A_B_C.csv`, `cross_partition_top_pairs.png`, GAN sample grids `gan/*/samples_step_3000.png`.
- Evidence: `split_manifest.csv`, `split_config.json`, `dedup_audit_summary.json`, `gan/gan_verification.json`.

## Key measured results
| Item | Result |
|---|---|
| Split | 2,311 / 492 / 492 unique images (train/val/test) from 7,200; 3,479 clusters; 207 quarantined |
| FID / KID x1000 (n=492) | DCGAN 154.7 / 129.4; cWGAN-GP 177.8 / 157.6; WGAN-GP 182.1 / 163.5; floor 34.2 |
| Test accuracy A / B / C | 0.817 / 0.839 / 0.869 (macro-F1 0.786 / 0.821 / 0.853) |
| GAN training | 3,000 generator updates each; critic/discriminator updates DCGAN 3,000, WGAN-GP 15,000, cWGAN-GP 15,000; all finite; cWGAN-GP resumed from step 2,500 |

## Required disclosures (all in FINAL_REPORT.md)
New split replaces the original folders; reduced and imbalanced data (test n=492, no-tumour n=46); heuristic duplicate detection with residual same-patient leakage; hybrid not best; no downstream benefit beyond sample size; 3 seeds / single GAN runs / no significance tests; cWGAN-GP interruption at step 2861 (cause unconfirmed) and resume; unverified synthetic labels; 8 label-conflict clusters (30 images) in the source data; old and new results not comparable; no clinical claims.

## Open items for you
1. Cite the dataset (Nickparvar, Kaggle, CC BY 4.0); confirm against your own download record if you have one.
2. Read the report text yourself (numbers are generated from saved files; wording was written and hedged by hand).
3. Decide whether to keep the earlier documents in `outputs/` in the submission: they are superseded (banner added) and contain optimistic numbers; submit the files in this folder instead.

## Do not submit (internal)
`*.prev-*`, `_exploratory_attempt_threshold_0.99/`, `gan/cwgangp.failed-attempt-*`, `outputs/autopilot/`, earlier experiment folders, checkpoints (large), `external_models/`.
