# Preliminary artifacts (written 2026-10-12 01:15, before the leakage issue was addressed)

`final_report.md`, `ia3_slides_outline.md`, `ia3_viva_questions.md`, `gan_comparison/final_comparison.csv/.png` and
`downstream_classification/` were produced from a downstream experiment whose synthetic-image GAN had seen the CNN validation images
(see `downstream_classification/PRELIMINARY_LEAKAGE_NOTICE.md`). The GAN FID/KID results (`gan_comparison/metrics.json`) are NOT affected
(reference set = `archive/Testing`, never seen by any GAN). The downstream sections of those documents must be treated as preliminary
until they are regenerated from the clean experiment. Old versions are kept (renamed `*.prev-<timestamp>`) when regenerated.
