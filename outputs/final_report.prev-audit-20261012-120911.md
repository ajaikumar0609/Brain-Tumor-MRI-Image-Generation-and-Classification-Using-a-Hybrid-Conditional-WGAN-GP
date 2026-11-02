# Brain Tumor MRI Image Generation and Classification Using a Hybrid Conditional WGAN-GP

## Abstract
We compare three GANs trained for 3,000 generator updates on the Kaggle Brain Tumor MRI Dataset (4 classes, 64×64 grayscale): DCGAN, an unconditional WGAN-GP, and a conditional WGAN-GP (cWGAN-GP, the proposed model, with a projection critic). Quality was measured with FID and KID (torch-fidelity, 1,600 generated vs 1,600 real Testing images, 3 generation seeds). **The proposed model was not the best.** DCGAN scored best on both metrics (FID 133.8 ± 1.1, KID 0.119); cWGAN-GP was second (FID 147.3 ± 1.3, KID 0.135) and beat the unconditional WGAN-GP (FID 160.8 ± 2.0, KID 0.149). All GAN scores are far from the real-vs-real reference (FID 14.1). Per-class KID gave no strong evidence that generated images match their intended tumour class. In a downstream test, a small CNN was trained on (A) real images only, (B) real plus 5,600 cWGAN-GP images, and (C) a matched-size real-only control (real images resampled to 10,080). The GAN for B/C was trained only on the CNN-training split (leakage-free). Test accuracy was A 0.811 ± 0.047, B 0.852 ± 0.017, C 0.869 ± 0.027. B did not exceed C (mean B−C = −0.017), so the gain of B over A is explained by training-set size and optimizer steps, and **we find no evidence that the synthetic images add benefit.** No clinical claims are made.

## Problem statement
Medical image datasets are limited, and GANs are often proposed to generate extra training data. We ask: (1) can a conditional WGAN-GP with a projection critic generate MRI-like images of better distributional quality than DCGAN and WGAN-GP, and (2) does adding its images to the training set improve a tumour classifier, once training-set size is controlled for? The work is an academic comparison, not a clinical tool.

## Dataset and preprocessing
- Source: Kaggle "Brain Tumor MRI Dataset" (masoudnickparvar/brain-tumor-mri-dataset). Classes: glioma, meningioma, notumor, pituitary.
- `archive/Training`: 5,600 images (1,400/class), used for GAN training and a stratified 80/20 train/validation split (4,480 train / 1,120 validation, split seed 42).
- `archive/Testing`: 1,600 images (400/class), used only as the FID/KID real reference and for final classifier evaluation. No GAN was trained on it and nothing was selected with it.
- Images were converted to grayscale and resized to 64×64. For FID/KID, real and generated images were treated identically (grayscale → Resize 64 → uint8 → repeated to 3 channels).
- Side check: an independent pretrained EfficientNet-B3 scored 95.94% on Testing, but it may overlap its original training data and is not an independent benchmark.

## Methodology
**Models**
- **DCGAN**: conv/transposed-conv generator (z=100 → 64×64×1, BatchNorm, Tanh), BatchNorm discriminator, non-saturating BCE loss, Adam 2e-4 (β 0.5, 0.999).
- **WGAN-GP**: same generator, BatchNorm-free critic, Wasserstein loss with gradient penalty (λ=10), 5 critic steps per generator step, Adam 1e-4 (β 0.5, 0.9).
- **cWGAN-GP (proposed)**: WGAN-GP with a 50-d label embedding concatenated to z in the generator and a projection critic D(x,y)=ψ(h(x))+⟨E(y),h(x)⟩; no classifier guidance. Conditioning follows Mirza & Osindero; the projection critic follows Miyato & Koyama.
- **Downstream CNN**: 4 conv blocks (32-64-128-256), global average pooling, dropout 0.3; Adam 1e-3, batch 64, 15 epochs, no augmentation.

**Objectives.** DCGAN uses the standard non-saturating GAN loss. WGAN-GP minimises the Wasserstein critic loss plus λ·E[(‖∇D(x̂)‖₂−1)²] on interpolates. cWGAN-GP uses the same loss with the critic conditioned on the label.

**Metrics.** FID (Heusel et al.) from Inception-v3 pool3 (2048-d) features; KID (Binkowski et al.) with a cubic polynomial kernel and unbiased MMD² (100 subsets; size 1,000 overall, 200 per class).

## Experimental setup
- GAN training: 3,000 generator updates each on MPS. DCGAN: 3,000 discriminator updates (204 s); WGAN-GP and cWGAN-GP: 15,000 critic updates (≈1,200 s each). All runs finite. GAN comparison models used the 5,600 Training images and not the Testing directory.
- Evaluation: 1,600 generated images per seed (cWGAN-GP: 400 per label), seeds 1001–1003, vs the 1,600 real Testing images. Uncertainty is the std across the 3 generation seeds (ddof=1). The single real reference set has no uncertainty estimate; GAN training itself was run once per model, so training-run variability is unmeasured.
- Downstream: three conditions, run seeds 42–44.
  - **A** real only (4,480).
  - **B** real + 5,600 synthetic (1,400/class) from a *clean* cWGAN-GP trained only on the 4,480 CNN-training images (10,080 examples).
  - **C** matched-size control: the same real images resampled with replacement to 10,080 (2,520/class); 3,998 of 4,480 distinct images were drawn (max multiplicity 9), no synthetic images.
- Validation (real-only, n=1,120) selected the best epoch. Every accuracy reported below is **test** accuracy (n=1,600) of that selected epoch. Validation metrics are kept separate and are not tabulated here.
- Synthetic labels are the labels the images were generated for; that they depict the class is unverified.

## Results

### GAN quality (lower is better; mean ± std over 3 generation seeds)
| Model | FID | KID |
|---|---|---|
| Real train (class-balanced, reference) | 14.13 ± 0.11 | 0.0007 ± 0.0002 |
| DCGAN | **133.76 ± 1.06** | **0.1188 ± 0.0016** |
| cWGAN-GP (proposed) | 147.26 ± 1.34 | 0.1353 ± 0.0025 |
| WGAN-GP | 160.84 ± 1.99 | 0.1490 ± 0.0026 |

Ranking (best first), identical for FID and KID: DCGAN, cWGAN-GP, WGAN-GP. Differences between models are many times the across-seed std, but this reflects generation-seed variability only. The real-reference row is a real-vs-real floor, not a GAN. Visual samples: `sample_grids_real_vs_generated.png`, and `samples_step_3000.png` for each model.

### Per-class findings (cWGAN-GP, 400 images/class, KID subset 200)
| Class | FID | KID | KID lowest to own real class? |
|---|---|---|---|
| glioma | 171.1 ± 1.5 | 0.1498 | no |
| meningioma | 176.7 ± 3.6 | 0.1484 | yes |
| notumor | 170.5 ± 2.6 | 0.1540 | no |
| pituitary | 198.3 ± 2.2 | 0.1836 | no |

Pituitary is the worst class on both metrics.

### Class-confusion KID (rows = generated label, columns = real class)
| gen \ real | glioma | meningioma | notumor | pituitary |
|---|---|---|---|---|
| glioma | 0.150 | 0.146 | 0.203 | 0.201 |
| meningioma | 0.157 | 0.148 | 0.218 | 0.199 |
| notumor | 0.157 | 0.147 | 0.154 | 0.199 |
| pituitary | 0.175 | 0.162 | 0.245 | 0.184 |

Only meningioma-labelled images are closest to their own real class. Glioma-, notumor- and pituitary-labelled images are all numerically closest to *real meningioma*. Many entries differ by only a few thousandths, so this is weak evidence of class conditioning at best. The class-conditional signal in this 3,000-update model is weak and the images should not be assumed to carry class-specific features.

### Downstream classification (clean, leakage-free; test set, mean ± sd over 3 seeds)
| Condition | n_train | unique real | Accuracy | Macro-F1 | Per-seed accuracy |
|---|---|---|---|---|---|
| A real only | 4,480 | 4,480 | 0.8112 ± 0.0474 | 0.8105 | 0.757, 0.833, 0.844 |
| B real + cWGAN-GP synthetic | 10,080 | 4,480 | 0.8517 ± 0.0168 | 0.8475 | 0.871, 0.846, 0.839 |
| C real only, matched size | 10,080 | 3,998 | 0.8690 ± 0.0273 | 0.8677 | 0.893, 0.874, 0.839 |

Paired accuracy differences per seed (42, 43, 44): B−A = +0.114, +0.0125, −0.005 (mean +0.040); C−A = +0.136, +0.041, −0.004 (mean +0.058); **B−C = −0.0225, −0.029, −0.0006 (mean −0.017)**.

Per-class F1 (mean over seeds):
| Class | A | B | C |
|---|---|---|---|
| glioma | 0.772 | 0.749 | 0.810 |
| meningioma | 0.745 | 0.797 | 0.818 |
| notumor | 0.901 | 0.916 | 0.936 |
| pituitary | 0.824 | 0.928 | 0.907 |

Glioma recall was lowest in all conditions (A 0.665, B 0.628, C 0.767); glioma was often confused with meningioma (mean confusion counts: A 79.7, B 96.7, C 48.3 of 400). B's glioma F1 is below A's.

**Interpretation (hedged, no significance test run).** B beats A, but C beats A by even more, and B is at or below C in every seed. B and C differ by less than the seed-to-seed standard deviation (0.017 and 0.027), so with 3 seeds the experiment cannot distinguish a synthetic-image effect from the effect of training on more examples and optimizer steps. We therefore do **not** credit the synthetic images with a benefit; the experiment gives no evidence they add anything beyond size/step count. Duplicated real images are not new data: C controls for size and optimizer steps but not for diversity, so a diversity benefit of synthetic images (or a label-noise cost) is neither shown nor excluded.

### Preliminary leaky experiment (not used for conclusions)
An earlier pass generated synthetic images from a cWGAN-GP trained on all 5,600 Training images, which included the 1,120 CNN-validation images later used to select epochs. Information from validation images could thus reach the training set through the generator, making validation-based epoch selection optimistic. This run is labelled **preliminary** and no conclusion rests on it. (The GAN never saw `archive/Testing`.) Its real+synthetic accuracy was 0.8688 ± 0.0092 (mean paired gain over A +0.0575), versus 0.8517 ± 0.0168 (gain +0.0404) in the clean run, i.e. about 0.017 higher accuracy and 0.017 larger gain. This comparison only shows how much the leakage mattered; the clean run is the primary result. The clean audit reports GAN training on 4,480 images, zero file overlap with CNN validation, and no access to Testing. Real-only A is identical in both runs.

## Discussion
- The proposed cWGAN-GP improved on the unconditional WGAN-GP (FID 147.3 vs 160.8; KID 0.135 vs 0.149) but did not beat DCGAN. Under a short 3,000-update budget we cannot say whether this ordering would hold with longer training or tuning; WGAN-GP variants also took ≈6× more wall-clock time and 5× the critic updates than DCGAN.
- FID/KID values of ~130–160 indicate the generated distribution remains far from real; the sample grids should be inspected visually. Inception features are ImageNet-based and a 64×64 grayscale domain may limit metric reliability for MRI, so the numbers are best used for relative comparison.
- Class-confusion KID suggests conditioning is weak, which also means synthetic labels may be noisy.
- Downstream, the apparent benefit of synthetic data (B>A) is matched or exceeded by simply resampling real data (C), showing why a matched-size control is necessary. Without it, the result would likely be reported as a synthetic-augmentation win.

## Limitations
- Three run seeds, one resampling seed, one training run per GAN; variability from GAN training and resampling is unmeasured. No significance test was run.
- Short training (3,000 generator updates); no hyperparameter tuning reported; 64×64 grayscale only.
- FID/KID use a single 1,600-image reference set (no uncertainty) and Inception features not specific to MRI.
- Synthetic labels are generation labels with unverified correctness; generated images are not shown to contain anatomically accurate tumours. No clinical claims are made.
- **Operational and reproducibility notes**
  1. *Non-finite-loss incident (cause unconfirmed):* during the first run of the clean downstream experiment (01:45–01:50, 2026-10-12) the real+synthetic run for seed 44 raised a non-finite-loss error right after the log recorded an Apple Metal "command buffer exited with error status / Internal Error" on the M4 GPU, and the Mac restarted around then. Sleep/restart is only a hypothesis; the root cause was not established. Partial results were archived (`outputs/downstream_classification_clean.prev-*`) and the experiment was rerun from scratch with identical code, data and seeds; all 6 runs finished with finite losses and every comparable run (real-only seeds 42–44, real+synthetic seeds 42–43) reproduced the earlier numbers exactly.
  2. *Content-level duplicates:* the file-level audit shows zero overlap between GAN training files and CNN validation files, but a SHA-256 byte-identity check found 44 of the 1,120 CNN-validation images (3.9%) have an exact copy in the CNN-training partition (the Kaggle Training folder contains duplicates; 39 of them are among the 3,998 distinct images in C's training set). Validation accuracy, used only for best-epoch selection, is therefore slightly optimistic for all three conditions, and the clean GAN also saw copies of those images. The same check found 0 byte-identical images between Training and Testing, so test accuracies are not affected by this; near-duplicates were not checked and the effect on epoch selection was not quantified.
  3. *Validation vs test:* every headline accuracy is test accuracy on `archive/Testing` (n=1,600) of the validation-selected epoch; validation accuracy (real-only, n=1,120) only chose the epoch and is reported separately. Testing was also used earlier as the FID/KID reference and for a pretrained-classifier sanity check, so it is not untouched across the whole project, though no GAN training or selection step used it.
  4. *Origin of Condition C:* C was recommended by an external reviewer model (ChatGPT) via an automated handoff and validated against project rules by Claude before it was run. In the saved results C scored at least as high as B in all three seeds (B−C ≤ 0 in each), so B's improvement over A is explained by training-set size and optimizer steps.
  5. *Process:* the first complete autopilot pass (stages A–D) ran before the validation-leakage issue was noticed; its downstream results and documents are preserved as preliminary (`outputs/downstream_classification/` and `*.prev-*` report files). The overnight automation chain was terminated by a Mac restart; resumption and final verification were done manually, and `outputs/autopilot/OVERNIGHT_RESULT.md` was written from verified files.

## Conclusion
On this dataset and budget, DCGAN produced the best FID/KID, with cWGAN-GP second and unconditional WGAN-GP last; the proposed model is therefore not the best generator. Per-class analysis shows weak evidence of class-specific generation. In leakage-free downstream tests, real+synthetic (0.852) beat real-only (0.811) but not the matched-size real-only control (0.869), so we find no evidence that cWGAN-GP images improve classification beyond added training volume. Stronger claims would need more seeds, longer GAN training, label-correctness checks and significance testing.

## References
Please verify each reference before citing.
1. Mirza & Osindero, Conditional Generative Adversarial Nets, arXiv:1411.1784.
2. Radford, Metz & Chintala, Unsupervised Representation Learning with Deep Convolutional GANs (DCGAN), arXiv:1511.06434.
3. Gulrajani et al., Improved Training of Wasserstein GANs (WGAN-GP), arXiv:1704.00028.
4. Heusel et al., GANs Trained by a Two Time-Scale Update Rule Converge to a Local Nash Equilibrium (FID), arXiv:1706.08500.
5. Binkowski et al., Demystifying MMD GANs (KID), arXiv:1801.01401.
6. Miyato & Koyama, cGANs with Projection Discriminator, arXiv:1802.05637.
7. Kaggle "Brain Tumor MRI Dataset" (masoudnickparvar/brain-tumor-mri-dataset).
