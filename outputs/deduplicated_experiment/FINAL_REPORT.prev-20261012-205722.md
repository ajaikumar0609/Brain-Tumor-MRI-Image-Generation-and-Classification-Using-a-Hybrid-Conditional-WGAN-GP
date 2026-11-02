# Brain Tumor MRI Image Generation and Classification Using a Hybrid Conditional WGAN-GP: de-duplicated experiment (final)

> This report supersedes the earlier reports in `outputs/` (`final_report.md` and related files), which were produced on the original `archive/Training` / `archive/Testing`
> folders. A later audit showed those folders share many near-identical images, so their test numbers were optimistic. All results below were recomputed on a new
> cluster-disjoint split. **The old and new numbers are not comparable** (different data, sample sizes and reference sets).

## Abstract
The original train/test folders of the Kaggle brain-tumour MRI data used here contain many near-copies (mostly mirrored) across the split, so a near-duplicate audit was used to
build a new split: 7,200 images were grouped into 3,479 near-duplicate clusters, 207 images were quarantined, and one representative per cluster was assigned to a class-stratified,
cluster-disjoint train / validation / test split of 2,311 / 492 / 492 images (only 3,295 of 7,200 images are unique). A DCGAN, an unconditional WGAN-GP and the proposed conditional WGAN-GP (cWGAN-GP,
projection critic) were retrained for 3,000 generator updates on the new training partition and evaluated with FID/KID against the new test partition (n=492). **DCGAN had the best FID and KID**
(FID 154.7), followed by cWGAN-GP (FID 177.8) and WGAN-GP (FID 182.1); the proposed hybrid was not the best generator, and its margin over WGAN-GP (4.3 FID) is small. In a downstream test
a small CNN trained on (A) real images only, (B) real plus cWGAN-GP images, or (C) a real-only control resampled to B's size and class mix reached test accuracies of
0.817 ± 0.027, 0.839 ± 0.020 and 0.869 ± 0.021 (3 seeds). B beat A in all 3 seeds, but C scored higher than B on average and in 2 of 3 seeds, so these experiments
**provide no evidence that the synthetic images help beyond added training volume**. The test set is small (492 images, 46 no-tumour), copies were removed but same-patient neighbouring slices could not be, and each GAN was trained once; no clinical claim is made.

## 1. Why a new split was needed
An audit of the original data found that about two thirds of the original Testing images (1,076 of 1,600) had a near-identical, often mirrored, copy in Training (exact file hashing misses these), and that
56% of the CNN-validation images had a copy in the CNN-training images. Test accuracies, validation-based epoch selection and the FID/KID reference were therefore not independent of training (details in
`outputs/final_audit/`). This experiment repeats the GAN training, the downstream comparison and the FID/KID evaluation on data split by near-duplicate cluster.

## 2. Dataset and the cluster-disjoint split
**Source.** A four-class brain tumour MRI dataset obtained from Kaggle (the exact dataset page and licence were *not verified*; file names such as `Tr-gl_*`, `Te-gl_*`, `Tr-aug-me_*`, `Te-aug-me_*` and the balanced 1,400/400-per-class folders suggest a re-balanced variant of the public Brain Tumor MRI Dataset). Both original folders were pooled (7,200 images); the old Testing folder is **not** used as the test set.

**Near-duplicate detection** (`src/dedup_split.py`, `src/dedup_refine.py`): every image is reduced to 32×32 grayscale, mean-removed and L2-normalised; similarity is the cosine similarity, evaluated against each other image in 8 orientations (identity, horizontal/vertical flip, three rotations, two transposes). Two images are linked if their similarity is ≥ 0.98 or their files are byte-identical (153 byte-identical groups); transitive links form clusters (connected components).
- Result: 3,479 clusters (largest 83 images); 756 clusters contain images from both original folders.
- Threshold sensitivity (clusters / largest cluster): 0.999: 3,927 / 43, 0.995: 3,857 / 58, 0.99: 3,782 / 63, 0.98: 3,479 / 83. The 0.98 cut was chosen after inspecting the strongest cross-partition pairs of a 0.99 attempt (kept in `_exploratory_attempt_threshold_0.99/`), some of which were near-copies.
- Quarantine (207 images excluded from every partition): 8 clusters whose members carry **conflicting class labels** (a label-noise finding about the dataset), 172 clusters made only of files whose names mark them as augmented (`aug`; they may be transformed copies this method cannot link), and 4 held-out images removed in a second stage.
- Second stage: each validation/test representative's best match in a higher-priority partition was re-scored at 96×96 with ±4 px shifts. No pair reached 0.99; 4 pairs reached ≥ 0.97 (maximum 0.982) and the 4 held-out images involved were quarantined. Higher-resolution scores for pairs that look alike at 32×32 (0.97-0.98) were about 0.94, i.e. similar but distinct scans, not copies.
- One representative per cluster was kept (preferring a non-augmented file, then an original Training file) and clusters were split 70/15/15 per class with seed 42. **Final real-image dataset** (3,295 unique images):

| Partition | glioma | meningioma | notumor | pituitary | Total |
|---|---|---|---|---|---|
| train | 918 | 566 | 227 | 600 | 2311 |
| val | 196 | 122 | 46 | 128 | 492 |
| test | 196 | 122 | 46 | 128 | 492 |

**Verification.** No cluster occurs in more than one partition (0 violations); the manifest and the three partition file lists are hash-recorded (`split_manifest.csv`, `split_config.json`). The strongest remaining cross-partition candidates were inspected visually (`cross_partition_top_pairs.png`): they were the same anatomy/sequence but different slices or scans.

**Residual uncertainty (important).** (i) This is a similarity heuristic with no ground truth. (ii) There are no patient identifiers, so **different slices of the same patient are not detected** and may sit in different partitions; this leakage route cannot be excluded. (iii) Files marked augmented were removed by name only. (iv) Rescaled or heavily re-cropped copies below the similarity cut would be missed. Consequently the results are better protected against copy-level leakage than the earlier ones, not proven leak-free.
**Cost:** only 3,295 of 7,200 images are unique and usable, and the classes became imbalanced (no-tumour has only 227 training and 46 test images).

## 3. Methods
- **GANs** (64×64 grayscale, z=100, batch 16, seed 42, 3,000 generator updates, identical architectures/objectives/optimisers to the earlier experiment): DCGAN (BCE, Adam 2e-4, β 0.5/0.999, 1 discriminator update per generator update); unconditional WGAN-GP (gradient penalty λ=10, 5 critic updates per generator update, Adam 1e-4, β 0.5/0.9, no BatchNorm in the critic); cWGAN-GP (50-d label embedding concatenated to z; projection critic D(x,y)=ψ(h(x))+⟨E(y),h(x)⟩; same loss; no classifier guidance). All three were trained on the 2,311-image training partition only (`--manifest`); the training-file hash recorded in each checkpoint equals the manifest's training partition. The unconditional models receive no labels; the conditional model's labels are *requested* conditions, not proof of tumour-specific content.
- **Downstream CNN** (`src/dedup_downstream.py`): 4 conv blocks (32-64-128-256), global average pooling, dropout 0.3, Adam 1e-3, batch 64, 15 epochs, no augmentation, seeds 42, 43, 44. The validation partition (492 real images) selects the best epoch; the test partition (492) is read only afterwards. A = real training representatives; B = A + 722 cWGAN-GP images per class (2,888 images, labels = requested conditions, correctness unverified); C = real training representatives resampled with replacement to B's exact per-class counts (1640, 1288, 949, 1322; 2029 of 2311 distinct images drawn, maximum repetition 12; no synthetic images).
- **FID/KID** (`src/dedup_eval_fid_kid.py`): torch-fidelity 0.4.0, `inception-v3-compat` pool3 features, identical preprocessing for real and generated images (grayscale → 64×64 uint8 → 3 channels), reference = the 492 test representatives; 492 generated images per model and seed (cWGAN-GP: the test class counts [196, 122, 46, 128]), generation seeds 1001, 1002, 1003; KID = 100 subsets of 300. The floor row compares class-matched random training representatives with the test set. The test partition is not used for checkpoint selection or tuning.

## 4. Training outcomes
| Model | Generator updates | Discriminator / critic updates | Runtime (s, MPS) | Finite | Training-file hash = manifest train partition |
|---|---|---|---|---|---|
| DCGAN | 3000 | 3000 | 293 | True | True |
| WGAN-GP | 3000 | 15000 | 1759 | True | True |
| cWGAN-GP | 3000 | 15000 | 2149 | True | True |

- All three GANs reached the intended update counts with finite losses and gradients; checkpoints reload with `weights_only=True`.
- **Interruption of the cWGAN-GP (cause unconfirmed).** The first cWGAN-GP attempt stopped at generator step 2861 with `FloatingPointError: non-finite critic loss/grad at gen step 2861` after healthy losses; its log contains no Metal/GPU error message. The Mac was then found rebooted (probably after battery exhaustion, which is a hypothesis only). The run was resumed from the verified step-2,500 checkpoint (all weights and optimizer states finite) and completed; the model therefore consists of steps 1-2,500 of the first attempt and 2,501-3,000 of the resumed run (data order restarts at an epoch boundary, so it is not bit-identical to an uninterrupted run). The abandoned attempt's logs and CSVs are preserved in `gan/cwgangp.failed-attempt-*`.
- Runtimes are longer than in the earlier experiment (e.g. DCGAN 293 s versus 204 s); the Mac reported Low Power Mode as enabled when checked. The runtimes are not comparable across the two experiments.

## 5. Results
### 5.1 GAN quality (new test partition, n=492; mean ± std over 3 generation seeds; lower is better)
| Model | FID | KID x1000 | generated / reference (x3 seeds) |
|---|---|---|---|
| Real train representatives (class-matched; floor) | 34.20 ± 0.29 | -0.31 ± 0.13 | 492/492 |
| **DCGAN** | 154.69 ± 1.90 | 129.44 ± 2.45 | 492/492 |
| cWGAN-GP | 177.84 ± 1.80 | 157.63 ± 2.37 | 492/492 |
| WGAN-GP | 182.11 ± 1.49 | 163.54 ± 2.02 | 492/492 |

Ranking by FID and by KID (identical): DCGAN, cWGAN-GP, WGAN-GP. The seed standard deviations cover generation-seed variability only; each GAN was trained once, so training-run variability is unmeasured. DCGAN's lead is large relative to the seed spread; the cWGAN-GP-over-WGAN-GP margin (4.3 FID, 5.9 KID x1000) is only a few seed standard deviations and could easily change across training runs. DCGAN also used 5× fewer discriminator updates than the WGAN variants' critic updates, so the comparison is not compute-matched. FID is biased upward for small samples, which together with the smaller reference explains the higher floor (34.2) than in the earlier experiment. Sample grids: `gan_comparison/sample_grids.png`: all three models produce head-shaped, MRI-like images with soft internal structure and no identifiable tumours.

### 5.2 Class conditioning of the cWGAN-GP (per class; small samples)
| Class | n (generated = real per seed) | FID | KID x1000 | KID subset | reliability |
|---|---|---|---|---|---|
| glioma | 196 | 190.9 ± 4.1 | 157.2 ± 4.2 | 100 | n>=100 (still small for 2048-d FID) |
| meningioma | 122 | 213.6 ± 1.1 | 154.9 ± 0.4 | 97 | n>=100 (still small for 2048-d FID) |
| notumor | 46 | 242.1 ± 3.1 | 166.0 ± 2.0 | 36 | n<100: FID/KID indicative only |
| pituitary | 128 | 239.0 ± 3.0 | 208.7 ± 4.4 | 100 | n>=100 (still small for 2048-d FID) |

Class-confusion KID x1000 (rows = generated label, columns = real test class):

| generated label \ real test class | glioma | meningioma | notumor | pituitary |
|---|---|---|---|---|
| glioma | 157.2 | 149.7 | 178.6 | 208.8 |
| meningioma | 168.1 | 154.9 | 187.4 | 209.9 |
| notumor | 174.6 | 157.2 | 166.1 | 210.0 |
| pituitary | 202.7 | 183.6 | 219.5 | 208.8 |

Row-wise, only meningioma is closest to its own real class (meningioma acts as a hub that most labels are near). Column-wise, the generated label is the closest for glioma, notumor; pituitary is not separated (its row and column values are essentially tied) and the no-tumour estimates rest on only 46 real images (KID subset 36), so they are indicative only. Per-class FID with 46-196 images in 2,048 dimensions is strongly biased and should not be compared across classes. The labels change the output distribution (no-tumour images are visibly brighter), which is not evidence of tumour-specific or medically correct features.

### 5.3 Downstream classification (test n=492; mean ± sd over 3 seeds)
| Condition | n_train | Test accuracy | Macro-F1 | Balanced acc. | Weighted-F1 | Validation acc. | Test accuracy per seed (42, 43, 44) |
|---|---|---|---|---|---|---|---|
| A real only | 2311 | 0.817 ± 0.027 | 0.786 ± 0.010 | 0.796 | 0.817 | 0.812 | 0.795, 0.809, 0.848 |
| B real + cWGAN-GP synthetic | 5199 | 0.839 ± 0.020 | 0.821 ± 0.025 | 0.828 | 0.841 | 0.827 | 0.841, 0.817, 0.858 |
| C real only, matched composition | 5199 | 0.869 ± 0.021 | 0.853 ± 0.024 | 0.871 | 0.869 | 0.877 | 0.890, 0.868, 0.848 |

| Paired difference (per seed) | Accuracy | mean | Macro-F1 | mean |
|---|---|---|---|---|
| B − A | +0.047, +0.008, +0.010 | +0.022 | +0.046, +0.012, +0.046 | +0.035 |
| C − A | +0.096, +0.059, +0.000 | +0.051 | +0.097, +0.071, +0.031 | +0.066 |
| B − C | -0.049, -0.051, +0.010 | -0.030 | -0.051, -0.059, +0.015 | -0.032 |

B beat A in 3 of 3 seeds (mean accuracy +0.022, macro-F1 +0.035). The matched-composition real-only control C was +0.051 (accuracy) above A on average and scored higher than B on average (+0.030 accuracy, +0.032 macro-F1) and in 2 of 3 seeds. With 3 seeds, a test set of 492 images (a 95% interval of about ±3.2 accuracy points for a single run) and seed standard deviations of about 0.02, B and C cannot be separated statistically; no significance test was run. **The measurements give no evidence that the synthetic images add benefit beyond training-set size and class balance, and the point estimates favour the control.**

Per-class F1 / recall (mean over seeds; test counts in brackets; the no-tumour estimates rest on 46 images):

| Class (test n) | A real only | B real + cWGAN-GP synthetic | C real only, matched composition |
|---|---|---|---|
| glioma (196) | F1 0.853 / recall 0.801 | F1 0.861 / recall 0.804 | F1 0.908 / recall 0.886 |
| meningioma (122) | F1 0.740 / recall 0.770 | F1 0.760 / recall 0.828 | F1 0.784 / recall 0.762 |
| notumor (46) | F1 0.659 / recall 0.674 | F1 0.739 / recall 0.746 | F1 0.804 / recall 0.906 |
| pituitary (128) | F1 0.893 / recall 0.938 | F1 0.923 / recall 0.935 | F1 0.915 / recall 0.930 |

Mean confusion matrices are in `downstream/classification_report.txt`; glioma→meningioma and meningioma→glioma are the main confusions in all conditions. Per-seed results, predictions and training histories are in `downstream/runs/`. Figure: `downstream/accuracy_A_B_C.png`.

## 6. What the results support and do not support
**Supported:** DCGAN gave the lowest FID/KID on this split, with the proposed cWGAN-GP second and WGAN-GP last (ranking identical to the earlier, contaminated experiment, though by small margins for the last two); adding cWGAN-GP images to the real data improved the mean test accuracy and macro-F1 over real-only training in all three seeds; a size- and class-mix-matched real-only control scored at least as well on average; generated labels change the output distribution (clearest for no-tumour).
**Not supported:** that the hybrid is the best generator; that the synthetic images improve classification beyond added training volume; that the synthetic labels correspond to real tumour classes; that the images are anatomically or clinically meaningful; that the result is free of patient-level leakage; that any ranking would persist across training seeds, longer training or other hyperparameters; absolute performance estimates for new patients (small test set, residual leakage).

## 7. Limitations
Small data after de-duplication (3,295 unique images; 492 test images, 46 no-tumour) and class imbalance; heuristic near-duplicate detection with residual same-patient and rescaled-copy leakage; 3 seeds, one training run per GAN and no significance tests; short GAN training (3,000 updates; not compute-matched between DCGAN and the WGAN variants); the cWGAN-GP was resumed after an interrupted attempt (cause unconfirmed); unverified synthetic labels; Inception features on 64×64 grayscale MRI and FID bias at small n; dataset source/licence unverified; 8 clusters (30 images) carried conflicting class labels, indicating label noise in the source data; the two experiments (old and new split) are not comparable; no clinical claims.

## 8. Conclusion
On a split in which copies and mirrored duplicates cannot cross partitions, DCGAN again produced the best-scoring images, the proposed conditional WGAN-GP was second by a small margin over unconditional WGAN-GP, and augmenting real data with the hybrid's synthetic images did not outperform simply resampling the real data to the same size and class mix. The project demonstrates the implementation and careful evaluation of the hybrid model, but not a benefit of it; stronger claims would need patient-level splits, more seeds and training runs, longer training, label-correctness checks and significance testing.

## References
1-6 checked against arXiv (titles, authors and years match):
1. Mirza & Osindero, *Conditional Generative Adversarial Nets*, arXiv:1411.1784.
2. Radford, Metz & Chintala, *Unsupervised Representation Learning with Deep Convolutional Generative Adversarial Networks*, arXiv:1511.06434.
3. Gulrajani et al., *Improved Training of Wasserstein GANs*, arXiv:1704.00028.
4. Heusel et al., *GANs Trained by a Two Time-Scale Update Rule Converge to a Local Nash Equilibrium*, arXiv:1706.08500.
5. Binkowski, Sutherland, Arbel & Gretton, *Demystifying MMD GANs*, arXiv:1801.01401.
6. Miyato & Koyama, *cGANs with Projection Discriminator*, arXiv:1802.05637.
7. Dataset: obtained from Kaggle; exact page and licence not verified.
