# SVM variant: results and QA record

Test partition (492 images) evaluated once with the frozen model. Source files: `outputs/svm_variant/test/test_evaluation.json`, `test_predictions.json`, `selection/selection.json`.

**Selected model:** RBF SVM, hog128_cell8 (8,100 HOG features, 128 px), C = 10, gamma = 1/8,100, class weight none; 1,996 support vectors; fitted on the 2,311 training images only.

| Test metric | Value |
|---|---|
| Accuracy | 0.866 (95% bootstrap interval 0.835 to 0.894) |
| Macro precision / recall / F1 | 0.836 / 0.850 / 0.841 (F1 interval 0.802 to 0.876) |
| Balanced accuracy / weighted F1 | 0.850 / 0.864 |
| Always-predict-glioma baseline accuracy | 0.398 |

| Class (test n) | Precision | Recall | F1 |
|---|---|---|---|
| glioma (196) | 0.917 | 0.898 | 0.907 |
| meningioma (122) | 0.824 | 0.730 | 0.774 |
| notumor (46) | 0.725 | 0.804 | 0.763 |
| pituitary (128) | 0.879 | 0.969 | 0.922 |

Confusion matrix (rows = true, columns = predicted; glioma, meningioma, notumor, pituitary): [176, 13, 4, 3]; [12, 89, 9, 12]; [3, 4, 37, 2]; [1, 2, 1, 124]

| Candidate (HOG variant, kernel) | CV macro-F1 (train) | Validation macro-F1 |
|---|---|---|
| hog128_cell16, linear | 0.793 | 0.823 |
| hog128_cell16, rbf | 0.839 | 0.880 |
| hog128_cell8, linear | 0.834 | 0.866 |
| hog128_cell8, rbf | 0.846 | 0.886 |
| hog64_cell8, linear | 0.770 | 0.800 |
| hog64_cell8, rbf | 0.825 | 0.853 |

## Tests run (all inside `brain_svm`)
- `svm_variant/qa_check.py` (62 checks): model reload; test predictions map to the split's files and labels; metrics and confusion matrix recomputed from the saved predictions; fresh predictions equal the saved ones; selection read only train/validation; model written before the test evaluation; second test evaluation refused; leakage evidence; report/slide numbers, citations, captions and TOC against the saved results; no GAN content in the SVM documents; the original `~/Desktop/brain` unchanged.
- Backend pytest: 13 passed. Integration smoke test: 7/7 passed. Frontend production build: passed. No automated browser-level tests.
- Report: Pages render inspected page by page (31 pages). Slides: approximate shape-based preview only (no native PowerPoint/Keynote render).

## Known limitations
Small imbalanced test set (46 no-tumour); patient-level independence unproven (no patient identifiers; many held-out images have similar-looking training slices, median similarity about 0.94); single training run per configuration; dataset download record unverified.
