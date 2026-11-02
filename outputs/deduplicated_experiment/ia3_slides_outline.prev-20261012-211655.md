1. **Title** — Brain Tumor MRI Generation and Classification Using a Hybrid Conditional WGAN-GP (de-duplicated evaluation).
2. **Problem and questions** — Can a conditional WGAN-GP generate better MRI-like images than DCGAN/WGAN-GP, and do its images help a tumour classifier once training size is controlled? Academic study, no clinical claims.
3. **Why the data had to be re-split** — Original Testing folder shares near-identical (often mirrored) images with Training (1,076 of 1,600 test images; 56% of validation images); exact hashing misses them. Earlier numbers were optimistic. Figure: `outputs/final_audit/closest_testing_training_pairs.png`.
4. **Cluster-aware split** — 32×32 cosine similarity over 8 orientations, threshold 0.98, connected components, second-stage 96×96 re-scoring; 7,200 images → 3,479 clusters → 3,295 unique images; 207 quarantined (label conflicts, augmented files). Table: split counts (2,311/492/492; no-tumour test n=46).
5. **Residual uncertainty** — Heuristic; no patient IDs, so same-patient slices not detected; cross-partition candidate pairs inspected (`cross_partition_top_pairs.png`).
6. **Models** — DCGAN, WGAN-GP, cWGAN-GP (50-d label embedding; projection critic). 3,000 generator updates each, same seed/data. Table: architectures/optimisers.
7. **Training outcomes** — counters and runtimes; all finite; cWGAN-GP interrupted at step 2861 (cause unconfirmed) and resumed from step 2,500. Table: training runs.
8. **Evaluation protocol** — torch-fidelity FID/KID vs test partition (n=492); 3 generation seeds; floor row; downstream A/B/C with matched-composition control; test used only for final evaluation.
9. **Sample grids** — `gan_comparison/sample_grids.png`: head-shaped, soft, no identifiable tumours.
10. **GAN results** — FID: DCGAN 154.7 < cWGAN-GP 177.8 < WGAN-GP 182.1; floor 34.2. Figure: `gan_comparison/fid_kid_bar_chart.png`. Hybrid not best; margin over WGAN-GP small.
11. **Class conditioning** — per-class KID and confusion; column-wise own label closest for glioma and notumor; small n; class-dependent, not tumour-specific.
12. **Downstream design** — A real; B real + 2,888 synthetic; C real resampled to B's size and class mix.
13. **Downstream results** — test accuracy A 0.817, B 0.839, C 0.869; macro-F1 0.786/0.821/0.853. Figure: `downstream/accuracy_A_B_C.png`.
14. **Interpretation** — B>A in 3/3 seeds, but C ≥ B in 2/3 seeds (mean B−C -0.030); no evidence of benefit beyond training volume; differences within noise.
15. **Limitations** — small test set, imbalance, residual patient-level leakage, 3 seeds, single GAN runs, unverified labels/dataset source, Inception features on small grayscale MRI.
16. **Conclusion and future work** — implemented and evaluated honestly; DCGAN best FID/KID; no downstream benefit shown. Future: patient-level split, more data and seeds, longer training, label verification, significance tests. References (arXiv 1411.1784, 1511.06434, 1704.00028, 1706.08500, 1801.01401, 1802.05637 verified; dataset source unverified).
