# Brain Tumor MRI Image Generation and Classification Using a Hybrid Conditional WGAN-GP

## Abstract

We compare three GANs on 64×64 grayscale brain MRI from the Kaggle Brain Tumor MRI Dataset (four classes: glioma, meningioma, notumor, pituitary). The three are a DCGAN, an unconditional WGAN-GP, and a proposed hybrid conditional WGAN-GP (cWGAN-GP). The cWGAN-GP combines a label-embedded generator with a projection critic. Each model was trained once for 3,000 generator updates on 5,600 training images. We scored each with FID and KID against the 1,600-image test folder, using 3 generation seeds.

**The proposed model was not the best generator.** DCGAN had the lowest FID (133.8) and KID (0.119). cWGAN-GP came second (FID 147.3, KID 0.135) and improved on unconditional WGAN-GP (FID 160.8, KID 0.149). All three are far from the real-vs-real floor (FID 14.1, KID 0.0007). Visual inspection shows blurry head-shaped outlines with no convincing tumours. Class conditioning is weak.

In a downstream test, a small CNN trained on real data only reached 81.1% ± 4.7% test accuracy (3 seeds). The same CNN trained on real data plus 5,600 cWGAN-GP images (1,400 per class) reached 86.9% ± 0.9%, a mean paired gain of +5.75 points. This gain is not shown to come from the realism or class correctness of the synthetic images. The comparison has no matched-size control, the synthetic labels are unverified, and there are only 3 seeds. We make no clinical claims.

## Problem statement

Brain MRI datasets are limited and class-imbalanced in many settings. Generative models are sometimes proposed to supply extra training images. We ask two questions:

1. Does a hybrid conditional WGAN-GP (conditional generator, projection critic, Wasserstein-GP objective) produce samples closer to real MRI than a DCGAN or an unconditional WGAN-GP, as measured by FID and KID?
2. Does adding its class-labelled samples to the training set of a small CNN change four-class classification performance on a held-out real test set?

## Dataset and preprocessing

- **Source:** Kaggle "Brain Tumor MRI Dataset" (masoudnickparvar/brain-tumor-mri-dataset). Readers should verify the dataset's provenance and licence on Kaggle.
- **Training folder (`archive/Training`):** 5,600 images, 1,400 per class. It was used for GAN training and for a stratified 80/20 train/validation split (4,480 train / 1,120 val; split seed 42).
- **Testing folder (`archive/Testing`):** 1,600 images, 400 per class. It was used only as the FID/KID real reference and for final classifier evaluation. It was not used for model selection and no GAN was trained on it.
- **Preprocessing for GANs:** 64×64 single-channel images, Tanh output range for the generators.
- **Preprocessing for FID/KID:** grayscale → Resize(64,64) → uint8 → repeated to 3 channels. This was identical for real and generated images.
- An independent pretrained EfficientNet-B3 scored 95.94% on `archive/Testing`. It may overlap its original training data, so this is a sanity check and not an independent benchmark. It is not used in the comparisons below.

## Methodology

### Models

| Model | Architecture and objective |
|---|---|
| DCGAN | Conv/transposed-conv generator (z=100 → 64×64×1, BatchNorm, Tanh) and a BatchNorm discriminator. Non-saturating BCE loss. Adam 2e-4 (β=0.5, 0.999). |
| WGAN-GP | Same generator. BatchNorm-free critic. Wasserstein loss with gradient penalty (λ=10). 5 critic steps per generator step. Adam 1e-4 (β=0.5, 0.9). |
| cWGAN-GP (proposed) | WGAN-GP with a 50-d label embedding concatenated to z in the generator. Projection critic D(x,y) = ψ(h(x)) + ⟨E(y), h(x)⟩. No classifier guidance. |
| Downstream CNN | SmallCNN: 4 conv blocks (32-64-128-256), global average pooling, dropout 0.3. Adam 1e-3, batch 64, 15 epochs, no augmentation. |

### Objectives and background

- DCGAN follows Radford, Metz & Chintala (arXiv:1511.06434).
- WGAN-GP follows Gulrajani et al. (arXiv:1704.00028).
- Label conditioning follows the idea in Mirza & Osindero (arXiv:1411.1784).
- The projection critic follows Miyato & Koyama (arXiv:1802.05637).
- The "hybrid" designation refers to combining these components.

### Metrics

- **FID** follows Heusel et al. (arXiv:1706.08500).
- **KID** follows Binkowski et al. (arXiv:1801.01401). We used 100 subsets with a polynomial kernel (degree 3, gamma=1/d, coef0=1) and the unbiased MMD² estimator.
- Both use torch-fidelity 0.4.0 with Inception-v3 (compat) pool3 2048-d features. Lower is better.

## Experimental setup

- **GAN training:** one run per model, 3,000 generator updates, on MPS (Apple GPU). All runs finished with finite values. The training images were the 5,600 images in `archive/Training`.
  - DCGAN: 3,000 discriminator updates, 204 s.
  - WGAN-GP: 15,000 critic updates, 1,200 s.
  - cWGAN-GP: 15,000 critic updates, 1,213 s.
  - **Compute is not matched:** the WGAN variants received 5× more critic updates than the discriminator updates DCGAN received.
- **GAN evaluation:** 1,600 generated images per model per seed, using generation seeds 1001, 1002 and 1003. The real reference is the 1,600 test images. cWGAN-GP samples were 400 per label. Reported uncertainty is the std across the 3 generation seeds (ddof=1) plus the within-seed KID subset std. It does **not** capture training-seed variability, which was not measured. The single real reference set has no uncertainty estimate.
- **Per-class evaluation:** cWGAN-GP only, 400 generated vs 400 real per class. KID subset size 200.
- **Downstream classification:**
  - Run seeds 42, 43, 44; split seed 42.
  - Two conditions: (a) real only, 4,480 training images; (b) real + 5,600 cWGAN-GP images (1,400 per class), 10,080 training images.
  - Synthetic images came from `outputs/cwgangp_3000/checkpoint_step_3000.pth` (synthetic seed 3001).
  - Synthetic labels are the labels used for generation. Whether the images depict the class is **unverified**.
  - Evaluation is on `archive/Testing`, read only after training.

## Results

### GAN FID/KID (mean ± std across 3 generation seeds)

| Model | FID | KID | KID within-seed subset std |
|---|---|---|---|
| Real train (class-balanced, reference) | 14.13 ± 0.11 | 0.00070 ± 0.00022 | 0.00022 |
| DCGAN | **133.76 ± 1.06** | **0.1188 ± 0.0016** | 0.0012 |
| cWGAN-GP (proposed) | 147.26 ± 1.34 | 0.1353 ± 0.0025 | 0.0013 |
| WGAN-GP | 160.84 ± 1.99 | 0.1490 ± 0.0026 | 0.0015 |

- FID and KID give the same ranking: DCGAN < cWGAN-GP < WGAN-GP.
- The gaps (about 13.5 FID points between adjacent models) are much larger than the generation-seed std. This only says the ordering is stable across sampling seeds. Training-seed effects are unmeasured, so the ranking cannot be called robust to retraining.
- The real-vs-real reference is not zero (FID 14.1) because of finite samples and train/test differences. All GANs are roughly 120–147 FID points above this floor.
- **Visual inspection** of the sample grids shows head-shaped outlines with noisy or blurry interiors. WGAN-GP samples are flatter and greyer. cWGAN-GP samples have soft interiors, and the notumor row looks different from the other three, with brighter, more symmetric axial-looking interiors. No clearly identifiable, convincing tumour appears in any generated image, whereas the real glioma and meningioma rows show distinct bright masses.

### Per-class cWGAN-GP (n=400 per class)

| Class | FID | KID |
|---|---|---|
| glioma | 171.1 ± 1.5 | 0.1498 |
| meningioma | 176.7 ± 3.6 | 0.1484 |
| notumor | 170.5 ± 2.6 | 0.1540 |
| pituitary | 198.3 ± 2.2 | 0.1836 |

- All per-class FIDs exceed the pooled 147.3. Part of this is FID's upward bias at smaller n.
- Pituitary is clearly the worst class. Glioma, meningioma and notumor are within a few FID points of each other and should not be ranked.

### Class-confusion KID (rows = generated label, columns = real class; lower = closer)

| Generated \ Real | glioma | meningioma | notumor | pituitary |
|---|---|---|---|---|
| glioma | 0.1498 | 0.1458 | 0.2027 | 0.2012 |
| meningioma | 0.1567 | 0.1477 | 0.2180 | 0.1992 |
| notumor | 0.1566 | 0.1470 | 0.1539 | 0.1994 |
| pituitary | 0.1751 | 0.1616 | 0.2451 | 0.1837 |

- **Row-wise reading (which real class is each generated label nearest to):** only meningioma is nearest to its own class. Glioma, notumor and pituitary are all nearest to real meningioma. Real meningioma acts as a hub. Several of the margins (for example glioma→glioma 0.150 vs glioma→meningioma 0.146) are comparable to the seed std and are not clearly resolved.
- **Column-wise reading (which generated label is nearest to each real class):**
  - Real glioma: generated glioma is closest.
  - Real notumor: generated notumor is closest by a large margin (0.154 vs 0.203–0.245).
  - Real pituitary: generated pituitary is closest.
  - Real meningioma: unresolved. Generated glioma, notumor and meningioma differ by less than the per-class seed std.
- For generated pituitary, real glioma (0.175) is closer than real pituitary (0.184).
- **Reading:** the label changes the output distribution somewhat, most clearly for notumor. It does not give reliably class-specific outputs, and this is not evidence of tumour-specific appearance. In the fixed-latent grid, images within a column are near-identical in shape and pose across labels, so the latent controls most of the structure.

### Downstream classification (SmallCNN, 3 run seeds, `archive/Testing`, n=1,600)

| Training data | Train n | Accuracy | Macro-F1 |
|---|---|---|---|
| Real only | 4,480 | 0.811 ± 0.047 (0.757, 0.833, 0.844) | 0.810 ± 0.049 |
| Real + cWGAN-GP synthetic | 10,080 | 0.869 ± 0.009 (0.874, 0.874, 0.858) | 0.866 ± 0.010 |

Paired accuracy difference (synthetic − real only) per seed: +0.117, +0.041, +0.014. The mean is **+0.0575**.

| Class | F1 real-only | F1 real+synthetic | Recall real-only | Recall real+synthetic |
|---|---|---|---|---|
| glioma | 0.772 | 0.791 | 0.665 | 0.724 |
| meningioma | 0.745 | 0.807 | 0.824 | 0.821 |
| notumor | 0.901 | 0.923 | 0.910 | 0.974 |
| pituitary | 0.824 | 0.944 | 0.846 | 0.956 |

Mean confusion matrices (rows are assumed to be true labels and columns predicted labels; this orientation is not stated in the facts, so verify it in the outputs):
- Real only: 79.7 of 400 glioma were predicted as meningioma, and 55.7 pituitary as meningioma.
- Real + synthetic: glioma→meningioma fell to 64.0 and pituitary→meningioma fell to 15.7. Meningioma→glioma rose from 10.7 to 36.3, and glioma precision fell from 0.921 to 0.873.

## Discussion

1. **The hybrid model did not win on generation quality.** DCGAN beat cWGAN-GP on both FID and KID. cWGAN-GP did beat unconditional WGAN-GP, which is consistent with conditioning helping a little in this single run. The comparison is confounded: the WGAN variants got 5× more critic updates, each model was trained once, and the training was short (3,000 generator updates).
2. **All GANs are low fidelity.** FID and KID are far above the real-vs-real floor and the samples lack coherent anatomy and visible tumours. The FID/KID values use ImageNet features on upsampled grayscale MRI and are not comparable to natural-image benchmarks.
3. **Synthetic augmentation was associated with higher test accuracy, but the cause is not established.**
   - The mean accuracy increase is 5.75 points and all three paired differences are positive. The real-only runs varied a lot (std 4.7 points, lowest run 0.757), so much of the gain on seed 42 (+11.7) may reflect an unlucky baseline run.
   - The synthetic condition has 2.25× more training samples and, with the same 15 epochs, more optimizer steps. There is no control with matched sample count (e.g. repeated or augmented real images), so the gain cannot be attributed to the synthetic images' realism.
   - Because the generated images do not look like real tumours and their labels are unverified, the gain may reflect regularisation or other effects. We did not test this.
   - With 3 seeds we did not run a significance test and do not claim statistical significance.
   - The gain is uneven across classes. Pituitary F1 rose most (0.824→0.944), and glioma→meningioma errors fell. Meningioma→glioma errors rose.
4. **Poor FID/KID and a downstream gain can coexist.** The two measure different things. FID/KID measure feature-space similarity to real images, while the downstream test measures whether the classifier's decision boundary improves on real test data. Neither shows clinical validity.

## Limitations

- One training run per GAN, so training-seed variability is unmeasured. The model ranking might change on retraining.
- Short training (3,000 generator updates) and unmatched critic/discriminator updates between DCGAN and the WGAN variants.
- FID/KID use ImageNet Inception features on 64×64 grayscale images upsampled for the extractor. FID is biased upward at n=1,600 and more so at n=400 per class. Per-class KID uses subsets of 200, so per-class and confusion results are indicative only.
- The real reference is a single set with no uncertainty estimate.
- The downstream study has 3 seeds, a small CNN, no augmentation, and no matched-size or oversampling control. Synthetic labels were not verified (a label-correctness check, such as a separate classifier, was not performed). Hyperparameters were not tuned.
- Generated images are not shown to contain anatomically accurate tumours. Nothing here supports clinical use or diagnostic claims.
- The EfficientNet-B3 score (95.94%) may overlap its original training data and is only a sanity check.

## Conclusion

In this experiment DCGAN was the best generator by FID and KID. The proposed cWGAN-GP ranked second, ahead of unconditional WGAN-GP, but all models remain far from real data and show weak class conditioning. Adding cWGAN-GP samples to the training set was associated with a higher CNN test accuracy (86.9% vs 81.1%, mean paired +5.75 points over 3 seeds). Without a matched-size control and label verification, this cannot be attributed to the quality of the generated images. Future work should include multiple training seeds, matched compute, longer training, a label-correctness check on synthetic data, and a matched-size augmentation control. No clinical claim is made.

## References

Please verify each reference against its original source before citing. These are given by author, title and arXiv id as supplied:

1. Mirza & Osindero, *Conditional Generative Adversarial Nets*, arXiv:1411.1784.
2. Radford, Metz & Chintala, *Unsupervised Representation Learning with Deep Convolutional GANs (DCGAN)*, arXiv:1511.06434.
3. Gulrajani et al., *Improved Training of Wasserstein GANs (WGAN-GP)*, arXiv:1704.00028.
4. Heusel et al., *GANs Trained by a Two Time-Scale Update Rule Converge to a Local Nash Equilibrium (FID)*, arXiv:1706.08500.
5. Binkowski et al., *Demystifying MMD GANs (KID)*, arXiv:1801.01401.
6. Miyato & Koyama, *cGANs with Projection Discriminator*, arXiv:1802.05637.
7. Kaggle "Brain Tumor MRI Dataset" (masoudnickparvar/brain-tumor-mri-dataset).
