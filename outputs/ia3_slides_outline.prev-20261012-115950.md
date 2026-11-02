## Slide outline (about 14 slides)

Figure paths below are the ones available under `outputs/`. For downstream-classification slides, I have no file names, so build those from the tables in the report or take the plots from your downstream output folder.

**1. Title**
- Brain Tumor MRI Image Generation and Classification Using a Hybrid Conditional WGAN-GP (IA3)
- Name, course, date
- Note: research exercise, no clinical claims

**2. Problem and questions**
- MRI data is limited and imbalanced, so synthetic data is sometimes proposed
- Q1: does a hybrid cWGAN-GP generate better MRI than DCGAN or WGAN-GP (FID/KID)?
- Q2: does adding its samples change CNN classification on real test data?

**3. Dataset and splits**
- Kaggle Brain Tumor MRI (masoudnickparvar): 4 classes
- Training: 5,600 images (1,400 per class), used for GAN training and an 80/20 train/val split
- Testing: 1,600 images (400 per class), used only as the FID/KID reference and the final evaluation
- 64×64 grayscale
- Figure: `outputs/gan_comparison/sample_grids_real_vs_generated.png` (real rows)

**4. Models compared**
- DCGAN: BCE, BatchNorm D, Adam 2e-4
- WGAN-GP: BatchNorm-free critic, λ=10, 5 critic steps, Adam 1e-4
- cWGAN-GP (proposed): 50-d label embedding in G, projection critic, no classifier guidance
- Table: architecture summary (text only)

**5. Objectives and metrics**
- Hinge-free formulas: BCE vs Wasserstein + gradient penalty; projection D(x,y)=ψ(h(x))+⟨E(y),h(x)⟩
- FID (Heusel et al.) and KID (Binkowski et al.), Inception pool3, torch-fidelity 0.4.0
- KID: 100 subsets of 1000, polynomial kernel, unbiased MMD²
- Lower is better for both

**6. Experimental setup**
- 3,000 generator updates per model, one training run each, MPS device
- DCGAN: 3,000 D updates; WGAN variants: 15,000 critic updates (compute is not matched)
- 3 generation seeds (1001–1003), 1,600 images per seed
- Uncertainty is generation-seed std only
- Table: runtimes (204 s / 1,200 s / 1,213 s)

**7. Sample grids**
- Real vs DCGAN vs WGAN-GP vs cWGAN-GP
- Generated images look like blurry head outlines, with no convincing tumours
- cWGAN-GP notumor row looks distinct (brighter, symmetric)
- Figures: `outputs/gan_comparison/sample_grids_real_vs_generated.png`, `outputs/dcgan_3000/samples_step_3000.png`, `outputs/wgangp_3000/samples_step_3000.png`, `outputs/cwgangp_3000/samples_step_3000.png`

**8. FID/KID results (headline)**
- DCGAN 133.8 / 0.119, cWGAN-GP 147.3 / 0.135, WGAN-GP 160.8 / 0.149, real floor 14.1 / 0.0007
- The proposed model is NOT the best; it is second and beats unconditional WGAN-GP
- Gaps are much larger than the generation-seed std, but training-seed variability is unmeasured
- Figure: `outputs/gan_comparison/fid_kid_bar_chart.png`; table: FID/KID table

**9. Per-class cWGAN-GP**
- FID: glioma 171.1, meningioma 176.7, notumor 170.5, pituitary 198.3
- Pituitary is the worst; the other three should not be ranked
- Per-class n=400 is small, so FID is biased upward
- Table: per-class FID/KID

**10. Does the label matter? Class-confusion KID**
- Row-wise: only meningioma is nearest to its own class; meningioma acts as a hub
- Column-wise: notumor is clearly closest to its own label; glioma and pituitary are mildly so
- Conclusion: class-dependent but weak, clearest for notumor; not tumour-specific
- Table: 4×4 KID confusion matrix (heatmap)

**11. Downstream protocol**
- SmallCNN (4 conv blocks, GAP, dropout 0.3), Adam 1e-3, 15 epochs, no augmentation
- Real only (4,480) vs real + 5,600 cWGAN-GP images (10,080 total)
- Seeds 42/43/44; test set read after training
- Synthetic labels are generation labels and are unverified

**12. Downstream results**
- Accuracy 0.811 ± 0.047 → 0.869 ± 0.009; macro-F1 0.810 → 0.866
- Paired gains per seed: +0.117, +0.041, +0.014 (mean +0.0575)
- Per-class F1: pituitary 0.824→0.944, meningioma 0.745→0.807, glioma 0.772→0.791, notumor 0.901→0.923
- Table: real-only vs real+synthetic; confusion matrices

**13. Interpretation and caveats**
- Gain does not prove the synthetic images are realistic or correctly labelled
- Confounds: 2.25× more training data and steps, no matched-size control, only 3 seeds, high baseline variance
- Error shifts: glioma→meningioma errors fell, meningioma→glioma errors rose
- FID/KID and downstream measure different things

**14. Limitations**
- One training run per GAN, short training, unmatched compute
- ImageNet features on upsampled grayscale MRI; biased FID at small n
- No anatomical or clinical validation

**15. Conclusion and future work**
- DCGAN best on FID/KID; cWGAN-GP second; all far from real
- Synthetic augmentation was associated with +5.75 points accuracy, cause not established
- Next: multiple training seeds, matched critic updates, longer training, label verification, matched-size control
- References slide or backup: the 7 approved references (verify before citing)
