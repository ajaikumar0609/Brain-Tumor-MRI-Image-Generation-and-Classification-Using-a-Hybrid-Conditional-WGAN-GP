# Brain Tumor MRI Classification Using Support Vector Machine (SVM)

An independent classical-ML variant of the brain-tumour MRI project, developed only in this folder (`~/Desktop/brain_svm`), a copy of the GAN project (`~/Desktop/brain`, left untouched).
Pipeline: grayscale + resize -> **HOG** features -> `StandardScaler` (fitted on training data only) -> **linear or RBF SVM** (scikit-learn). It is an academic prototype, not a medical device.

## Layout
```
svm_variant/               code: svm_lib.py (split mapping, preprocessing, HOG), train_select.py, evaluate_test.py, leakage_evidence.py, make_figures.py
svm_variant/webapp/        SVM-only FastAPI backend + React/TypeScript frontend (run_dev.sh, smoke_test.sh)
outputs/svm_variant/       selection/ (CV + validation), model/ (saved model + config), test/ (single test evaluation), figures/, leakage_evidence.json
outputs/svm_variant/report/        report (DOCX/PDF) and report assets      outputs/svm_variant/presentation/   PowerPoint
docs/svm_variant/PROJECT_AUDIT.md  what was copied/excluded, split mapping, leakage controls, QA record
```
Everything else in the folder (GAN code, outputs, app/) is the copied GAN project, kept as reference and **not** used for SVM results.

## Reproduce (Apple Silicon Mac, Python 3.14)
```bash
cd ~/Desktop/brain_svm
python3 -m venv .venv && .venv/bin/pip install -r svm_variant/requirements.txt
.venv/bin/python svm_variant/train_select.py      # CV grid search + validation selection (train/val only), saves the model  (~15 min)
.venv/bin/python svm_variant/evaluate_test.py     # single evaluation on the untouched test partition (refuses a second run)
.venv/bin/python svm_variant/leakage_evidence.py  # split / run-order audit
.venv/bin/python svm_variant/make_figures.py
```
Web app: `(cd svm_variant/webapp/frontend && npm install)` once, then `./svm_variant/webapp/run_dev.sh` and open http://localhost:5173
(same ports as the GAN app: do not run both at once). Tests: `.venv/bin/python -m pytest svm_variant/webapp/backend/tests -q`, `./svm_variant/webapp/smoke_test.sh` (stack running), `(cd svm_variant/webapp/frontend && npm run build)`.

## Data and split
The 7,200-image dataset (matches Kaggle *Brain Tumor MRI Dataset* v2 by M. Nickparvar, CC BY 4.0; local download record unverified) is in `archive/`. The cluster-disjoint split in
`outputs/deduplicated_experiment/split_manifest.csv` is reused unchanged (representatives only: 2,311 train / 492 validation / 492 test). Not redistributed.
