## Viva questions and answers

**1. What is the goal of the project?**
To compare DCGAN, WGAN-GP and a proposed conditional WGAN-GP (cWGAN-GP) for generating 64×64 brain MRI, using FID and KID. Then to test whether adding cWGAN-GP samples changes a small CNN's four-class accuracy on real test images.

**2. Which dataset did you use and how was it split?**
The Kaggle Brain Tumor MRI Dataset (masoudnickparvar). `Training` has 5,600 images (1,400 per class) and was used for GAN training and a stratified 80/20 train/val split (4,480/1,120). `Testing` has 1,600 images (400 per class) and was used only as the FID/KID reference and for final classifier evaluation.

**3. Was the test set used for training or model selection?**
No. The facts record that no GAN was trained on the Testing folder, and the classifier evaluation read it only after training and never used it for selection.

**4. What is the proposed model?**
cWGAN-GP: WGAN-GP (gradient penalty λ=10, 5 critic steps per generator step) with a 50-d label embedding concatenated to the noise vector in the generator and a projection critic D(x,y)=ψ(h(x))+⟨E(y),h(x)⟩. It has no classifier guidance.

**5. Why use a Wasserstein loss with gradient penalty?**
The Wasserstein objective gives a smoother training signal than the original GAN loss. The gradient penalty softly enforces the critic's Lipschitz constraint without weight clipping (Gulrajani et al.). That is why the critic has no BatchNorm.

**6. What is a projection discriminator?**
It conditions the critic on the label by adding an inner product between a label embedding and the image features to an unconditional score (Miyato & Koyama).

**7. How do FID and KID work?**
Both compare real and generated images in Inception-v3 pool3 feature space. FID fits a Gaussian to each set and computes the Fréchet distance. KID is an unbiased MMD² estimate with a cubic polynomial kernel, averaged over subsets (here 100 subsets of 1000). Lower is better for both.

**8. What are the main GAN results?**
FID/KID: DCGAN 133.8/0.119, cWGAN-GP 147.3/0.135, WGAN-GP 160.8/0.149, with a real-vs-real floor of 14.1/0.0007. FID and KID agree on the ranking.

**9. Did your proposed model win?**
No. DCGAN had the best FID and KID. cWGAN-GP was second and better than the unconditional WGAN-GP.

**10. Why might DCGAN have beaten the WGAN variants?**
We did not test the cause. Possible factors: only 3,000 generator updates, a single training run per model, hyperparameters not tuned, and unmatched compute (the WGAN variants got 15,000 critic updates vs 3,000 for DCGAN). These are hypotheses, not findings.

**11. How reliable is the ranking?**
The gaps (about 13.5 FID points) are much larger than the std across 3 generation seeds (1.1–2.0), so the order is stable under sampling. Each model was trained only once, so training-seed variability is unmeasured and the ranking might change on retraining.

**12. Why is the real-vs-real FID not zero?**
FID is biased upward at finite sample size (n=1,600), and the train and test sets differ somewhat. The value 14.1 serves as the practical floor for this setup.

**13. Do the generated images look like real MRI?**
No. They are blurry head-shaped outlines with noisy or soft interiors. No convincing tumour appears in any generated image, while real glioma and meningioma images show distinct bright masses.

**14. Does class conditioning work?**
Only weakly. In the fixed-latent grid, images within a column are near-identical across labels, so the latent dominates. KID confusion shows generated outputs are generically near real meningioma. Column-wise, each real class (except meningioma, which is unresolved) is closest to its own generated label, clearest for notumor. This indicates class-dependent output but not tumour-specific appearance.

**15. Which class is generated worst?**
Pituitary, with FID 198.3 and KID 0.184 versus about 170–177 FID and about 0.15 KID for the other classes. Per-class numbers use n=400, so they are noisier and more biased than the pooled values.

**16. What were the downstream classification results?**
Real only: accuracy 0.811 ± 0.047, macro-F1 0.810. Real + 5,600 cWGAN-GP images: accuracy 0.869 ± 0.009, macro-F1 0.866. The mean paired accuracy gain is +0.0575 (per seed +0.117, +0.041, +0.014).

**17. Does this prove the GAN images help?**
No. The gain is an association. The synthetic condition has 10,080 vs 4,480 training samples and more optimizer steps over the same 15 epochs, with no matched-size control. The synthetic labels are unverified, the images do not look like real tumours, and there are only 3 seeds with a high-variance baseline.

**18. Why is this not contradictory with poor FID?**
FID/KID measure feature-space similarity to real images. Downstream accuracy measures whether extra labelled samples change the classifier's decision boundary on real test data. Samples can help as regularisation or extra variation even if they are not realistic. We did not test that mechanism.

**19. Which classes changed most in the downstream test?**
Pituitary F1 rose most (0.824→0.944), then meningioma (0.745→0.807). Glioma recall rose from 0.665 to 0.724 and glioma→meningioma confusions fell. Meningioma→glioma confusions rose, and glioma precision fell from 0.921 to 0.873.

**20. How were the synthetic labels assigned?**
They are the labels the images were generated for. We did not verify that each image depicts its class.

**21. What does the 95.94% EfficientNet-B3 number mean?**
An independent pretrained classifier scored 95.94% on `archive/Testing`, but it may overlap its original training data. It is only a sanity check, not an independent benchmark, and it is not part of the comparisons.

**22. What are the main limitations?**
One training run per GAN, short training, unmatched critic/discriminator updates, FID/KID on ImageNet features with upsampled grayscale 64×64 images, biased FID at small n, a single reference set with no uncertainty, a small 3-seed downstream study with no matched-size control or verified labels.

**23. Can this be used clinically?**
No. Generated images are not shown to contain anatomically accurate tumours, and FID/KID do not measure medical validity.

**24. What would you do next?**
Train multiple seeds per GAN, match compute, train longer, verify synthetic labels (for example with an independent classifier), add a matched-size control (oversampled or augmented real data), run more downstream seeds with a significance test, and evaluate with domain-appropriate metrics or expert review.

**25. Which references support the methods?**
Mirza & Osindero (arXiv:1411.1784, conditional GANs), Radford et al. (arXiv:1511.06434, DCGAN), Gulrajani et al. (arXiv:1704.00028, WGAN-GP), Heusel et al. (arXiv:1706.08500, FID), Binkowski et al. (arXiv:1801.01401, KID), Miyato & Koyama (arXiv:1802.05637, projection discriminator), and the Kaggle dataset. Verify them before citing.
