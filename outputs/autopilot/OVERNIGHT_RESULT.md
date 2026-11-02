# !! SUPERSEDING FINDING (final audit, 2026-10-12 ~12:10): archive/Testing is NOT independent of archive/Training
A near-duplicate audit (`scripts/audit_near_duplicates.py`, `outputs/final_audit/`) found that 1,076 of 1,600 Testing images (67%) have a near-identical,
mostly mirrored, copy in Training (exact SHA-256 hashing cannot see these). 56% of CNN-validation images likewise have a copy in CNN-training. Condition C test
accuracy is 0.925 on test images with a near-copy in Training (n=1,087) but 0.750 without (n=513). Therefore **every test accuracy below is optimistic, the
FID/KID reference overlaps the GAN training data, and the downstream conclusions are provisional** until repeated on a de-duplicated split. The statements below
that call the clean experiment "leakage-free" refer to file-level overlap only. Where this file says "comes from training-set size ... not from the synthetic images",
read: "was matched by a size-matched control on this (overlapping) test set; not attributable to the synthetic images".
Details and next steps: `outputs/FINAL_SUBMISSION_CHECKLIST.md`.

# IA3 overnight workflow - verified result (written manually from verified files, 2026-10-12 ~12:05)

The automated overnight chain was killed by a Mac restart (~01:50); this file replaces its result summary. Every statement below was
checked directly against saved files, not taken from a log summary.

## Completion status
| Item | Status | Evidence |
|---|---|---|
| Clean cWGAN-GP (4,480 CNN-train images only) | complete | 3,000 gen / 15,000 critic updates, finite, checkpoint counters read with weights_only=True, train-list sha256 `26f8ca06...`; verified by chain at 01:45 |
| Clean downstream CNN (A real-only, B real+synthetic) | complete (after one rerun) | `outputs/downstream_classification_clean/` 6 runs, all finite, each evaluated on 1,600 test images |
| Matched-size control (C) | complete | `outputs/downstream_classification_matched/` 3 runs, 10,080 examples (2,520/class), 267 s on MPS, exit 0 |
| Final report, slides outline, viva questions, comparison CSV/PNG | regenerated | `outputs/final_report.md` (+ `*.prev-*` earlier versions kept); numbers audited against saved metrics |
| Preliminary (leaky) results | preserved | `outputs/downstream_classification/` (summary.json unchanged), `PRELIMINARY_*_NOTICE.md` |

## Key verified results (TEST accuracy on archive/Testing, n=1,600; mean +/- sd over seeds 42-44)
- A real-only (4,480): 0.8112 +/- 0.0474 | B real + clean synthetic (10,080): 0.8517 +/- 0.0168 | **C real-only resampled to 10,080: 0.8690 +/- 0.0273**
- B-C per seed: -0.0225, -0.0288, -0.0006 -> no evidence synthetic images help beyond training-set size / optimizer steps.
- Validation accuracy (selection only): A 0.855-0.905, B 0.904-0.918, C 0.897-0.942.
- Preliminary leaky B: 0.8688 (clean B: 0.8517) -> the leakage inflated B by ~0.017, not used for conclusions.
- GAN FID/KID (unchanged): DCGAN 133.8/118.8 < cWGAN-GP 147.3/135.3 < WGAN-GP 160.8/149.0; real floor 14.1/0.7.

## Integrity checks performed
- Matched-control manifest: 10,080 examples, 2,520 per class, strict subset of the CNN-train list, 0 overlap with the CNN-val list; 3,998 of 4,480 distinct real images drawn (482 unused, max multiplicity 9); no synthetic images.
- Recomputed Condition C mean/sd and confusion-matrix accuracy from per-seed files: match the summary; saved predictions reproduce accuracy.
- SHA-256 duplicate check: 0 identical images Training<->Testing; **44 of 1,120 CNN-validation images (3.9%) have an exact copy in the CNN-training partition** (Kaggle Training folder duplicates). File-level leakage audit is clean, content-level is not: validation accuracy (epoch selection) is slightly optimistic for all conditions; test accuracies unaffected. Near-duplicates not checked; effect not quantified.
- Clean real-only and synthetic seeds 42-43 reproduced the first (interrupted) attempt bit-for-bit.

## Incident: non-finite loss (cause UNCONFIRMED)
In the first clean downstream attempt the real+synthetic seed-44 run raised a non-finite-loss error right after the log recorded an Apple Metal
"command buffer exited with error status / Internal Error" on the M4 GPU, and the Mac restarted around then. Sleep/restart is a hypothesis only.
Partial results were archived (`outputs/downstream_classification_clean.prev-*`, old log `*_run.prev-gpu-fault-*.log`); the full experiment was rerun from scratch
with identical code/data/seeds and finished with finite losses.

## ChatGPT handoff #1 (first real round trip)
Sent 01:46, reply read 01:48 (conversation title "GAN Healthcare Project Comparison"). The recommended task (matched-size control) was validated against the
project state and rules, then implemented and run; files in `outputs/autopilot/chatgpt_handoffs/`. The first attempt to type into ChatGPT was blocked by the
permission layer and was retried only after the user said to. A later message from the user quoted a further ChatGPT task; it matched the plan already being executed.
Not established: continuous unattended ChatGPT<->Claude looping (only one round trip was done).

## Remaining limitations
Three run seeds, one resampling seed, one training run per GAN; no significance tests; short GAN training (3,000 updates; DCGAN got 3,000 discriminator vs 15,000 critic updates for WGAN variants);
synthetic labels unverified; Inception features on 64x64 grayscale MRI; the clean GAN saw copies of 44 validation images; LLM-written report text only structurally validated plus the numeric audit above - read it before submitting;
the Mac was on battery during most of this work.

Controller: finished, 7/14 Claude calls ($0.77), 810/5,400 training-seconds. Inspect: `./scripts/run_ia3_autopilot.sh --status`.
