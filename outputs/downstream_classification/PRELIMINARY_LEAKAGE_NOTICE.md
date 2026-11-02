# PRELIMINARY - validation leakage (do not describe this comparison as leakage-free)

The cWGAN-GP used to create the synthetic images (`outputs/cwgangp_3000`) was trained on ALL 5,600 images of `archive/Training`.
This downstream experiment split the same directory into 4,480 CNN-training and 1,120 CNN-validation images (split seed 42).
The GAN therefore saw the 1,120 validation images; synthetic images may carry information about them, and the validation set was
used to select each run's best epoch. `archive/Testing` was never seen by the GAN or used for selection, so the reported TEST
accuracies are not directly contaminated, but the validation-based selection (and therefore the comparison) is not leakage-free.
Additional uncontrolled confound: the synthetic condition trains on 2.25x more samples (and more optimizer steps).

Status: preliminary. A clean rerun (GAN trained only on the 4,480 CNN-training images) is in `outputs/downstream_classification_clean/` once completed.
