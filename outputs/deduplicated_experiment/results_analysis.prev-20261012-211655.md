# Results analysis (de-duplicated experiment)
Source files: `gan_comparison/metrics.json`, `downstream/summary.json`, `dedup_audit_summary.json`, `verification.json` (23/23 verification checks passed).

**1. Split.** 7,200 pooled images → 3,479 near-duplicate clusters (threshold 0.98; second-stage refinement at 0.97) → 3,295 unique representatives: train 2,311, validation 492, test 492; 207 images quarantined; no cluster crosses partitions. Same-patient neighbouring slices cannot be detected, so patient-level leakage may remain.

**2. GAN quality (vs 492 test images).** FID: DCGAN 154.7, cWGAN-GP 177.8, WGAN-GP 182.1 (floor 34.2); KID x1000: DCGAN 129.4, cWGAN-GP 157.6, WGAN-GP 163.5. DCGAN is best by a wide margin; cWGAN-GP beats WGAN-GP by 4.3 FID, a few seed standard deviations, with one training run each and unequal compute (DCGAN: 3,000 discriminator updates vs 15,000 critic updates). Images are head-shaped with soft interiors and no identifiable tumours.

**3. Conditioning.** Row-wise only meningioma is closest to its own class; column-wise the generated label is closest for glioma and notumor. No-tumour estimates use 46 real images. Class-dependent, not shown tumour-specific.

**4. Downstream (test n=492).** A 0.817 ± 0.027 (macro-F1 0.786); B 0.839 ± 0.020 (0.821); C 0.869 ± 0.021 (0.853). B>A in 3/3 seeds; C≥B in 2/3 seeds (mean B−C accuracy -0.030). Differences between B and C are within seed spread and test-sampling error (about ±3.2 points), so **no evidence of a benefit of synthetic images beyond training volume**.

**5. Caveats.** Small test set; class imbalance (no-tumour test n=46); 3 seeds; one GAN training run each; cWGAN-GP resumed after an interrupted attempt (cause unconfirmed); unverified synthetic labels; results not comparable with the earlier experiment; dataset provenance unverified.
