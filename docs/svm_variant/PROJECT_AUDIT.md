# SVM variant: project audit

Created 2026-10-27. The original project `~/Desktop/brain` was treated as read-only: a size/mtime fingerprint of its 23,930 files taken before the copy was identical afterwards.

## 1. Copy
- Source `~/Desktop/brain` (6.2 GB incl. environments) -> destination `~/Desktop/brain_svm` (did not exist; created fresh; 110 GB free). Method: `rsync -a` (times preserved).
- **Copied (everything else):** `archive/` (7,200-image dataset), `outputs/` (all GAN results, checkpoints, reports, the cluster-disjoint split manifest, submission package), `external_models/`, `src/`, `scripts/`, `app/` (GAN web app source), `docs/`, `templates/E-report template.docx`, `README.md`, `requirements.txt`, and the two top-level GAN deliverables (`NEUROVISION_AI_Micro_Project_Report.pdf`, `NEUROVISION_AI_Project_Presentation.pptx`). Verified: 23,929 files present, 0 missing, 0 size mismatches; split manifest, the cWGAN-GP checkpoint, the third-party classifier weights and the template are byte-identical (SHA-256).
- **Excluded:** `.venv/` (research environment), `app/backend/.venv/`, `app/frontend/node_modules/`, `__pycache__/`, `.pytest_cache/`, `.playwright-mcp/`, `.DS_Store` (all re-creatable; dependency manifests `requirements.txt`, `app/backend/requirements.txt`, `app/frontend/package*.json` are copied). `.claude/settings.local.json` (one permission rule for an old autopilot script) was not copied.
- **New in the copy:** `.venv/` (own environment, `svm_variant/requirements.txt`), `svm_variant/`, `outputs/svm_variant/`, `docs/svm_variant/`. `svm_variant/webapp/frontend/node_modules` was copied from the original app's `node_modules` (read-only copy) to avoid a slow re-download.
- The GAN code, checkpoints, results and reports in the copy are **reference only**; no GAN metric appears in any SVM result.

## 2. Split mapping (no new split was generated)
`outputs/deduplicated_experiment/split_manifest.csv` (7,200 rows) maps each image path (relative to `archive/`) to a partition and a near-duplicate cluster. All 3,295 representative files exist in `archive/`; 0 clusters span two partitions; the train/validation/test file lists hash to the values recorded in `split_config.json` (asserted in code). The SVM uses the representatives only: **2,311 train / 492 validation / 492 test** (glioma/meningioma/no tumour/pituitary: 918/566/227/600 train; 196/122/46/128 validation and test). The 207 quarantined images and the non-representative cluster members are not used.

## 3. Leakage controls (details in `outputs/svm_variant/leakage_evidence.json`)
- Cross-validation and hyper-parameter search use the **training partition only**; `StandardScaler` is inside the pipeline (fitted on training folds only); HOG is stateless.
- `train_select.py` reads only train and validation (asserted; it records `test_partition_read: false`); the model is selected on validation macro-F1 and frozen **before** the test partition is read.
- `evaluate_test.py` evaluates the test partition **once** and refuses to run again; it records the SHA-256 of the evaluated model, and the web app serves only a model file with that hash.
- Re-measured: 0 clusters in more than one partition; 0 byte-identical files shared between partitions; the maximum 32x32-cosine similarity (8 orientations) of any validation/test image to a training image is 0.980/0.980, below the 0.98 linking threshold, with a median of about 0.94 (so many held-out images have similar-looking training slices).
- **Not excluded:** different slices of the same patient (no patient identifiers exist) - patient-level independence is NOT proven.

## 4. Choices and deviations
- Representatives only (as in the GAN project's downstream classifier) for a clean comparison; the extra near-duplicate members of training clusters are unused.
- Final model fitted on the training partition only (validation used for selection, not for fitting).
- The first run of `train_select.py` was stopped because the linear-SVM optimum sat at the lower edge of its C grid; the grid was extended (C from 1e-5) and the whole search re-run from scratch (the stopped attempt's log is `outputs/svm_variant/_train_select_first_attempt_stopped.log`). Only train/validation data were involved.
- numpy 2.5.4 was installed (pulled in by scikit-image) instead of the research project's 2.4.0.
- The SVM web app returns SVM decision scores (not probabilities); the GAN app's generator and EfficientNet are not part of it.
- A temporary browser-automation folder was created in the original project by the screenshot tool and removed immediately (the original is unchanged).
