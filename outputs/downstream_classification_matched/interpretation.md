# Matched-sample-count control: interpretation

Condition A trains on 4,480 real images; B on the same real images plus 5,600 cWGAN-GP images (10,080 examples); C on the same 4,480 real images resampled with replacement to 10,080 examples (2,520 per class) with no synthetic data, so B and C have identical size and optimizer-step counts.

| Condition | n_train | unique real images | test accuracy (mean +/- sd, 3 seeds) | macro-F1 |
|---|---|---|---|---|
| A_real_only | 4480 | 4480 | 0.8112 +/- 0.0474 | 0.8105 |
| B_real_plus_synthetic | 10080 | 4480 | 0.8517 +/- 0.0168 | 0.8475 |
| C_real_only_matched_size | 10080 | 3998 | 0.8690 +/- 0.0273 | 0.8677 |

Per-seed paired accuracy differences: B-A [0.1138, 0.0125, -0.005], C-A [0.1362, 0.0413, -0.0044], B-C [-0.0225, -0.0288, -0.0006] (means +0.0404, +0.0577, -0.0173).

**Reading (hedged, no significance test run):** B and C differ by less than the seed-to-seed standard deviation, so with 3 seeds this experiment cannot distinguish the effect of synthetic images from the effect of simply training on more (duplicated) examples.

## What this control can and cannot show
- It controls for training-set size and optimizer steps; it does not control for diversity: duplicated real images are exact copies, whereas generated images may add variation or label noise.
- Synthetic labels are the cWGAN-GP conditioning labels; the GAN evaluation gave no strong evidence that images match tumour classes.
- Condition C uses 3998 of 4480 unique real images (482 were not drawn); do not describe it as 10,080 unique images.
- Three run seeds, one resampling seed, one GAN training run: variability from resampling and GAN training is unmeasured.
- archive/Testing role: final evaluation of validation-selected weights for A, B and C only; it was also used earlier in the project as the FID/KID reference and for the pretrained-classifier sanity check, so it is not untouched across the whole project (no GAN or selection step used it).

## Post-hoc addendum (final audit)
`archive/Testing` overlaps `archive/Training`: 1,076 of 1,600 test images have a near-identical (often mirrored) copy in Training. Using this experiment's saved
predictions, Condition C's test accuracy was 0.925 (n=1,087) on test images with a near-copy in Training, 0.750 (n=513) without, and 0.618 (n=273) on clearly
different images (`outputs/final_audit/near_duplicate_followup.json`). The A/B/C comparison above shares this confound; predictions for A and B were not saved, so
the same split could not be computed for them. Treat the conclusions as provisional pending a de-duplicated rerun.
