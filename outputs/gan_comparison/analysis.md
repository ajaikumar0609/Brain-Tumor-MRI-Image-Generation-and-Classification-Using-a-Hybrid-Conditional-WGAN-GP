## Summary

Three GANs were trained for 3,000 generator updates each on 5,600 images, with one training run per model. They were DCGAN, unconditional WGAN-GP and the proposed hybrid conditional WGAN-GP (cWGAN-GP). All three are far from the real data on FID and KID, and the generated images look like blurry head-shaped outlines rather than convincing MRI.

- **Best model:** **DCGAN has the best FID (133.8) and the best KID (0.119).** The proposed cWGAN-GP is second on both metrics, and unconditional WGAN-GP is worst.
- **Where the hybrid sits:** cWGAN-GP improves on unconditional WGAN-GP but does not beat the plain DCGAN. The proposed model is therefore not the best model in this experiment.
- **Scope:** Nothing here is a clinical claim. The metrics measure distributional similarity in an ImageNet feature space, not medical validity.

## Quantitative results

Each generated set has n = 1600 per seed, evaluated over 3 generation seeds against 1600 real test images. FID and KID are both lower-is-better.

| Model | FID mean ± std across seeds | KID mean ± std across seeds | KID within-seed subset std |
|---|---|---|---|
| Real train (reference) | 14.13 ± 0.11 | 0.00070 ± 0.00022 | 0.00022 |
| DCGAN | 133.76 ± 1.06 | 0.1188 ± 0.0016 | 0.0012 |
| cWGAN-GP | 147.26 ± 1.34 | 0.1353 ± 0.0025 | 0.0013 |
| WGAN-GP | 160.84 ± 1.99 | 0.1490 ± 0.0026 | 0.0015 |

**Rankings.** FID and KID give the same order: DCGAN, then cWGAN-GP, then WGAN-GP. `best_fid_model` and `best_kid_model` are both DCGAN.

**Gaps against the across-seed std.**
- The FID gaps are about 13.5 (DCGAN to cWGAN-GP) and about 13.6 (cWGAN-GP to WGAN-GP). Both are many times larger than the across-seed stds of 1.1 to 2.0.
- The KID gaps are about 0.0165 and about 0.0137. Both are many times larger than the across-seed stds of 0.0016 to 0.0026.
- The ordering is therefore stable across generation seeds.
- The across-seed std measures only the variability of sampling from a fixed trained generator. Each model has a single training run, so training-seed variability is **unmeasured**. The gaps cannot be called robust to retraining, and a different training seed could plausibly change the ranking.

**Real-vs-real floor.** Real train images scored against the real test reference give FID 14.1 and KID 0.0007. This is not zero, which is expected from finite-sample bias at n = 1600 and from any train/test differences. It sets the practical floor for this setup. All three GANs sit roughly 120 to 147 FID points above it, and about 170 to 210 times the floor in KID. All models are therefore far from the real distribution as seen by this metric. The reference set has no uncertainty estimate of its own.

**Per-class cWGAN-GP** (n = 400 per class, KID subset size 200):

| Class | FID | KID |
|---|---|---|
| glioma | 171.1 ± 1.5 | 0.150 |
| meningioma | 176.7 ± 3.6 | 0.148 |
| notumor | 170.5 ± 2.6 | 0.154 |
| pituitary | 198.3 ± 2.2 | 0.184 |

- Every per-class FID is higher than the pooled cWGAN-GP FID of 147.3. Part of this is the known upward bias of FID at smaller n.
- Pituitary is clearly the worst class. Its FID and KID are well above the others, by more than the across-seed stds.
- Glioma, meningioma and notumor are close to one another. Their FID differences are only a few points, comparable to the stds for meningioma and notumor, so these three should not be ranked.

## What the image grids show

- **Real test images** (rows: glioma, meningioma, notumor, pituitary). These are varied. They include coronal, axial and sagittal views, different contrast weightings, and sharp skull and brain detail. Several glioma and meningioma images show bright focal lesions. The notumor row contains many T2-style axial slices with clearly visible ventricles.
- **DCGAN.** Samples are head-shaped outlines with textured, often noisy interiors. Some are very bright and high-contrast, and some are patchy or distorted. The skull rim is usually recognisable, but internal anatomy is not coherent. There is visible diversity in brightness and orientation.
- **WGAN-GP.** Samples are similar in style but generally flatter and greyer, with smoother, blotchy interiors. Some have dark holes or voids, and a few are very bright. Anatomical detail is weak. This matches its worst FID and KID.
- **cWGAN-GP.** Samples are also head outlines with soft, low-detail interiors. The notumor row looks different from the others, with brighter, more symmetric axial-looking interiors that loosely resemble the real T2-like notumor slices. The other three rows look much alike.
- **Fixed-latent grid.** In the cWGAN-GP step-3000 grid, each column uses the same latent across the four labels. Within a column the images are nearly identical in shape and pose, and the label changes mainly texture and brightness. The latent controls most of the structure, and the class label has a weak effect. Notumor shows the most visible change.
- **Lesions.** I see no clearly identifiable, convincing tumour in any generated image. The real glioma and meningioma rows show distinct bright masses, and the generated images do not reproduce them.
- **Bar chart.** The chart agrees with the table. DCGAN has the lowest bars among the GANs, and the real reference is very close to zero. The error bars are small relative to the gaps between models.

## Class conditioning

`class_confusion_kid_cwgangp` gives KID from each generated label (rows) to each real class (columns). Lower is closer.

| Generated label | glioma | meningioma | notumor | pituitary | Closest real class |
|---|---|---|---|---|---|
| glioma | 0.150 | **0.146** | 0.203 | 0.201 | meningioma |
| meningioma | 0.157 | **0.148** | 0.218 | 0.199 | meningioma (own) |
| notumor | 0.157 | **0.147** | 0.154 | 0.199 | meningioma |
| pituitary | 0.175 | **0.162** | 0.245 | 0.184 | meningioma |

- **Only one label sits closest to its own class.** Generated meningioma is nearest to real meningioma. Generated glioma, notumor and pituitary are all nearest to real meningioma instead, which matches the per-class flags (own class lowest only for meningioma).
- **Real meningioma is a default nearest neighbour.** Its column is the lowest or near-lowest in every row. The generator's output is generically closest to that class in this feature space.
- **Margins are small.** Glioma to glioma (0.150) versus glioma to meningioma (0.146) differs by about 0.004. Notumor to notumor (0.154) versus notumor to meningioma (0.147) differs by about 0.007. These differences are comparable to or smaller than the per-class KID across-seed std (0.0007 to 0.006), so they are not clearly resolved.
- **Notumor and pituitary are partly separated.** Generated labels are noticeably further from real notumor (0.20 to 0.25) except for the generated notumor row itself (0.154). Generated pituitary is also closest to its own class (0.184) among the non-meningioma columns. This is weak evidence of some conditioning signal.
- **Overall reading.** Conditioning is weak and not reliably class-specific. The model does not produce outputs that are closest to the correct real class for most labels. This agrees with the near-identical rows in the fixed-latent grid.

## Limitations

- **Feature extractor mismatch.** FID and KID use ImageNet-trained Inception-v3 pool3 features. The inputs are 64×64 grayscale MRI, replicated to 3 channels and upsampled to 299. Those features may not capture medically relevant structure, and the upsampling adds interpolation artefacts. Absolute values are not comparable to FID on natural-image benchmarks.
- **FID bias at n = 1600.** FID is biased upward at small n, and the bias depends on sample size. Values here are best used for relative comparison within this setup.
- **Per-class n = 400 is small.** Per-class FID is even more biased and noisier than the pooled FID. KID per class uses subsets of 200. The per-class and confusion results should be treated as indicative only.
- **Single training seed.** Each model was trained once. Across-seed std reflects only generation sampling, so differences between models may partly reflect training luck.
- **Short training.** Each model had only 3,000 generator updates, so the ranking may not hold at longer training. WGAN-GP and cWGAN-GP also received 15,000 critic updates against 3,000 for DCGAN, and that difference was not controlled for.
- **No evidence of anatomical correctness.** FID and KID measure distribution similarity in feature space. They do not show that generated tumours are anatomically correct or realistic.
- **Pretrained classifier overlap.** A pretrained classifier used for downstream evaluation may overlap with its original training data, which could inflate or distort any classification results.
- **Reference set.** The real reference is a single set with no uncertainty estimate.

## What the results support and do not support

**Supported:**
- DCGAN gave the lowest FID and KID in this experiment, followed by cWGAN-GP and then WGAN-GP. The gaps are much larger than the generation-seed std.
- Conditioning improved on the unconditional WGAN-GP baseline on both metrics, in this single run.
- All three GANs remain far from the real-vs-real floor, and the samples are visibly low-fidelity.
- There is weak evidence of class-dependent output, with notumor the most distinct. Pituitary is the hardest class by FID and KID.

**Not supported:**
- That the proposed hybrid cWGAN-GP is the best generator. DCGAN beat it on both metrics.
- That the ranking would hold across training seeds, longer training or other hyperparameters.
- That class conditioning works reliably. Three of four generated labels sit closest to real meningioma rather than their own class.
- That generated images contain anatomically correct or diagnostically meaningful tumours, or any clinical usefulness.
- That the absolute FID and KID values are comparable to values in other studies.

## Reviewer corrections (added after checking this analysis against the raw metrics)

These corrections supersede the statements above where they conflict. Numbers are KID x 1000 from `class_confusion_kid_cwgangp.csv` (rows = generated label, columns = real test class).

1. **Pituitary sentence is incorrect.** The "Class conditioning" section says generated pituitary is "closest to its own class among the non-meningioma columns". It is not: generated pituitary is 175.1 from real glioma and 183.7 from real pituitary, so glioma is closer than its own class.
2. **The row-wise reading understates the evidence.** Real meningioma acts as a hub that almost every generated label is near (column values 145.8-161.6), so asking "which real class is each generated label closest to" gives only 1 of 4 correct. Reading column-wise ("for each real class, which generated label is closest") gives a different picture:
   - real glioma: generated glioma is closest (149.8 vs 156.6-175.1);
   - real notumor: generated notumor is closest by a large margin (153.9 vs 202.7-245.1);
   - real pituitary: generated pituitary is closest (183.7 vs 199.2-201.2);
   - real meningioma: unresolved - generated glioma (145.8), notumor (147.0) and meningioma (147.7) differ by less than the per-class across-seed std (about 3-6).
   So there is moderate evidence that the label changes the output's distribution (clearest for notumor, which matches the visibly brighter, T2-like notumor row), but it is still not evidence of tumour-specific appearance, and the generator output is generically near real meningioma. The conclusion "conditioning is weak and not reliably class-specific" stands; "weak evidence of some conditioning signal" is better stated as "class-dependent, clearest for notumor".
3. **The "Pretrained classifier overlap" limitation does not apply to the downstream experiment.** The downstream CNN is trained from scratch on this dataset; the overlap caveat applies only to the earlier 95.94% accuracy of the pretrained EfficientNet-B3 classifier, which is a sanity check, not a benchmark.
4. **Additional context for the ranking.** DCGAN received 3,000 discriminator updates whereas the two WGAN variants received 15,000 critic updates (stated above); the ranking is therefore not a like-for-like compute comparison.
