# Report and slides: QA record

Project: *Brain Tumor MRI Image Generation and Classification Using a Hybrid Conditional WGAN-GP* (application: NeuroVision AI)
Student: Ajai Kumar N (URK23CS5064), B.Tech CSE (AI), Karunya Institute of Technology and Sciences, course 25AI2004 Artificial Intelligence in Healthcare.
Produced 2026-10-27. **No GAN or classifier was trained, and no scientific evaluation was re-run.**

## Deliverables (all in `outputs/healthcare_ai_microproject/`)
| File | What it is |
|---|---|
| `NEUROVISION_AI_Micro_Project_Report.docx` | Report built **from the official template** (`templates/E-report template.docx`, copied from `~/Downloads/`; original left in place). 36 pages in the Pages render: cover, bonafide certificate, abstract, TOC, Chapters 1-6, references, evaluation form. |
| `NEUROVISION_AI_Micro_Project_Report.pdf` | PDF exported from that DOCX by Apple **Pages** (installed; no software was installed). 36 pages. |
| `NEUROVISION_AI_Project_Presentation.pptx` | 14 slides, 16:9, with speaker notes. |
| `REPORT_AND_SLIDES_QA.md` | This file. |
| `assets/` | Project-authored diagrams (`figures/`), genuine NeuroVision AI screenshots (`screenshots/`), `derived_class_metrics.json`, `toc_pages.json`, `qa_results.json`. |
| `scripts/` | Everything needed to rebuild: `build_report.py`, `build_presentation.py`, `make_figures.py`, `derive_class_metrics.py`, `compute_toc.py`, `qa_check.py`, `render_slide_preview.py`, `report_lib.py`. |
| `qa_renders/` | Page contact sheet of the final PDF; approximate slide previews. |

## Sources used (nothing was taken from an older report without checking)
Template; `outputs/deduplicated_experiment/` result files (`gan_comparison/metrics.json`, `downstream/summary.json`, `dedup_audit_summary.json`, `split_config.json`, `gan/gan_verification.json`, per-run test predictions); `outputs/submission/FINAL_REPORT_source.md` and figures; `docs/WEB_APP_AUDIT.md`; `app/` source, `app/README.md`, package files and test file; `src/cwgangp_train.py`, `src/dcgan_train.py`, `src/data_pipeline.py`. All tables in the report are generated from the saved files by script; headline values were asserted in code (DCGAN FID 154.7 etc.).

## Checks run (`scripts/qa_check.py`): 99 / 99 passed
- Numbers: every decimal in the DOCX and PPTX matches a saved or derived value; DCGAN/cWGAN-GP/WGAN-GP FID and KID, A/B/C accuracy, 3,295 / 2,311 / 492, 1,076 of 1,600 and 207 appear identically in DOCX, PDF and PPTX.
- Template: no leftover placeholders; evaluation table kept with blank mark fields; signature block kept blank.
- Citations: 15 references, all cited, numbered in order of first citation; Figure and Table numbering consecutive; every image and data table captioned (15 figures + logo; 19 captioned tables + 3 note boxes + TOC + evaluation form).
- TOC page numbers agree with the final PDF (roman for the front matter, arabic from Chapter 1); stable across a rebuild.
- PPTX: 14 slides, all shapes inside the slide, pictures decode, no text under 10 pt, notes on every slide, no overclaiming phrases.
- Untouched: the old submission package matches its manifest hashes; no file under `outputs/deduplicated_experiment/`, `outputs/submission/`, `external_models/`, `src/` or `archive/` was modified after the task began.

## Rendering and visual QA
- **Report (DOCX/PDF): genuinely rendered with Apple Pages** and every page inspected (contact sheets and full-size pages). Fixed during QA: cover spilling to a second page; abstract text landing before the certificate (off-by-one); empty chart bars in two screenshots (see below). Pages is not Microsoft Word: **Word may paginate slightly differently**. The TOC is a static table (as in the template); if the DOCX is edited, re-check its page numbers.
- **Slides: not natively rendered.** Keynote could not be driven (it fails to open the PPTX under scripting: "Can't make missing value into type document", as in the earlier session) and LibreOffice is not installed, so I stopped after one bounded attempt and quit Keynote. The slides were checked with a **shape-based approximation** (`qa_renders/slide_preview_approximate/`, PIL + Arial in place of Calibri). It found and I fixed: slide 1 background not a real shape, an unreadably small diagram on slide 7, tiny screenshots on slide 8, two text-fit warnings. **This is not a PowerPoint/Keynote render. Open the PPTX in PowerPoint or Keynote and check every slide; slide 5's table is the one element the approximation says grows slightly.**

## Items to know about or confirm
1. **Template location.** It was not in `templates/`; found in `~/Downloads/` and copied (byte-identical, SHA-256 matched). Used as the official template.
2. **Changes to the template wording (minimal).** Single-student project: the three spare "Name (Reg No)" lines were removed; "[ AIML/AI ]" became "[ AI ]"; title and a NeuroVision AI line added on the cover; "presentation **held** on 29/10/26" became "presentation **scheduled** on 29/10/26" because 29/10/26 is after today (27/10/26); a REFERENCES row was added to the TOC. Supervisor (Ms. Gethsia P) and "October 2026" are as printed in the template. Signature spaces and mark fields are blank; no marks, seals or certification-course completion were entered.
3. **KITS Technology Mission: not verified.** The official sites (karunya.edu, kcode.karunya.edu) state the mission and the food/water/health care/energy focus areas, but contain no description of a "Technology Mission". Section 1.4 says so and makes no claim; add the official wording if the course needs it.
4. **PNG-grid download.** The task states it was confirmed in the browser; I did not test it (I said so earlier). The report words it as "reported as confirmed by the author" and notes it is not covered by an automated test.
5. **Screenshots** are genuine, captured from the running app during this task (the app was started and stopped by the launcher). The first dashboard/results captures were mid-animation (empty bars) and were retaken; the final ones match the results tables. The classify screenshot uses a dataset test image (CC BY 4.0 dataset, attributed) and its caption states it is a plumbing demonstration, not a result.
6. **Derived metrics.** Sensitivity/specificity (tumour vs no-tumour and per class) were computed from the saved per-run test predictions (`scripts/derive_class_metrics.py`); they reproduce the saved accuracies exactly and are labelled "derived" with the 46-image caveat.
7. **References.** All 10 papers were checked against their arXiv pages. Venues are given only where arXiv states them (Heusel: NIPS 2017; Bińkowski, Miyato: ICLR 2018; Kingma: ICLR 2015; Tan & Le: ICML 2019; Radford: submitted to ICLR 2016); Goodfellow, Mirza, Arjovsky and Gulrajani are cited as arXiv preprints because the arXiv pages give no venue. The UN 2030 Agenda title and goal wording were checked on sdgs.un.org (no resolution number is shown there, so none is cited). The Kaggle dataset page was viewed in a browser (licence CC BY 4.0). torch-fidelity and the third-party classifier are cited as software repositories ("Phi-007" is the GitHub account name; no real name is claimed). The three upstream datasets (figshare, SARTAJ, Br35H) are named, not cited, because their bibliographic details were not verified.
8. **Length.** The report is 36 pages (about 32 numbered pages incl. the evaluation form), longer than the roughly 15 body pages implied by the template's sample TOC numbers. Trim figures or tables if the course sets a page limit.
9. **Preserved caveats.** Dataset provenance (matches Kaggle v2; download record unverified; CC BY 4.0 with possibly different upstream terms; not redistributed), heuristic de-duplication and unproven patient-level independence, the third-party classifier's unknown accuracy and lack of out-of-distribution detection, the unconfirmed cause of the cWGAN-GP interruption at step 2,861, and "research prototype, not a medical device" appear in the report and the slides.
10. Hardware note: the report says Low Power Mode was on "when checked" for the training runs, as in the earlier verified report.
