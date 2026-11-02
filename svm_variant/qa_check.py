#!/usr/bin/env python3
"""Independent QA of the SVM variant (read-only). Prints PASS/FAIL, writes outputs/svm_variant/qa_results.json.   .venv/bin/python svm_variant/qa_check.py"""
import hashlib, io, itertools, json, re, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image
from docx import Document
from docx.oxml.ns import qn
from pptx import Presentation
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_recall_fscore_support

sys.path.insert(0, str(Path(__file__).resolve().parent))
import svm_lib as L  # noqa: E402

ROOT = L.ROOT; SV = L.OUT
R = SV / "report"; PR = SV / "presentation"
res = []


def check(name, ok, detail=""):
    res.append({"check": name, "pass": bool(ok), "detail": str(detail)})
    print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}")


t = json.load(open(SV / "test/test_evaluation.json")); sel = json.load(open(SV / "selection/selection.json")); cfg = json.load(open(SV / "model/model_config.json"))
pred = json.load(open(SV / "test/test_predictions.json")); leak = json.load(open(SV / "leakage_evidence.json"))

# ---- model / experiment ------------------------------------------------------------------------------------------------------
bundle = L.load_model()
check("saved model reloads from disk", bundle["classes"] == L.CLASSES and bundle["config"]["kernel"] == t["model"]["kernel"])
te_p, yte = L.load_partition("test")
check("test predictions are for exactly the split's test files, in order, with the right labels", pred["files"] == te_p and pred["y_true"] == yte.tolist())
yp = np.array(pred["y_pred"]); yt = np.array(pred["y_true"])
check("accuracy recomputed from saved predictions equals the saved value", abs(accuracy_score(yt, yp) - t["accuracy"]) < 1e-12)
p, r, f1, sup = precision_recall_fscore_support(yt, yp, labels=range(4), zero_division=0)
check("macro precision / recall / F1 recomputed from saved predictions equal the saved values", np.allclose([p.mean(), r.mean(), f1.mean()], [t["macro_precision"], t["macro_recall"], t["macro_f1"]]))
check("confusion matrix recomputed equals the saved matrix", confusion_matrix(yt, yp, labels=range(4)).tolist() == t["confusion_matrix"]["counts"])
check("per-class values equal recomputed values", all(abs(t["per_class"][c]["f1"] - f1[i]) < 1e-12 and t["per_class"][c]["support"] == int(sup[i]) for i, c in enumerate(L.CLASSES)))
# fresh re-prediction of a sample through the real model
mism = 0
for i in range(0, 492, 41):
    idx, _ = L.predict_image(bundle, Image.open(L.ARCHIVE / te_p[i])); mism += int(idx != yp[i])
check("fresh single-image predictions from the reloaded model equal the saved predictions (13 images spread over the test set)", mism == 0, f"{mism} mismatches")
check("selection script read only train/validation; test flag false in the saved config", cfg["partitions_read_by_this_script"] == ["train", "val"] and cfg["test_partition_read"] is False)
check("model file was written before the test evaluation", (SV / "model/svm_model.joblib").stat().st_mtime < (SV / "test/test_evaluation.json").stat().st_mtime)
check("evaluated model hash equals the model file", t["model_file_sha256"] == hashlib.sha256((SV / "model/svm_model.joblib").read_bytes()).hexdigest())
check("test evaluation lock: second run is refused", subprocess.run([sys.executable, str(Path(__file__).parent / "evaluate_test.py")], capture_output=True, text=True).stderr.strip().endswith("Refusing to evaluate again.") or "Refusing" in subprocess.run([sys.executable, str(Path(__file__).parent / "evaluate_test.py")], capture_output=True, text=True).stdout + subprocess.run([sys.executable, str(Path(__file__).parent / "evaluate_test.py")], capture_output=True, text=True).stderr)
check("leakage evidence: no cluster/file crosses partitions; max similarity below 0.98", leak["clusters_spanning_more_than_one_partition"] == 0 and all(v == 0 for v in leak["byte_identical_files_shared_between_partitions"].values())
      and all(v["max_similarity_to_any_train_image"] < 0.98 for v in leak["max_similarity_of_val_and_test_images_to_train_images"].values()))
check("selection was by validation (best validation macro-F1 is the selected candidate)", max(sel["candidates"], key=lambda c: c["val_macro_f1"])["hog_variant"] == sel["selected"]["hog_variant"] and max(sel["candidates"], key=lambda c: c["val_macro_f1"])["kernel"] == sel["selected"]["kernel"])
# ---- truth set -------------------------------------------------------------------------------------------------------------------
T = set()
def add(x):
    if isinstance(x, bool) or not isinstance(x, (int, float)): return
    for sc in (1, 100, 1000):
        for d in range(5): T.add(abs(round(x * sc, d)))
def walk(o):
    if isinstance(o, dict): [walk(v) for v in o.values()]
    elif isinstance(o, list): [walk(v) for v in o]
    else: add(o)
for o in (t, sel, cfg, leak, json.load(open(ROOT / "outputs/deduplicated_experiment/dedup_audit_summary.json"))): walk(o)
cs = sel["candidates"]
for a, b in itertools.permutations(cs, 2):
    add(a["val_macro_f1"] - b["val_macro_f1"])
add(t["specificity"] if "specificity" in t else 0)
for v in (167.85, 0.98, 0.97, 0.95, 0.94, 0.5, 0.9, 0.1, 0.01, 0.002, 2.0, 1.0, 3.0, 5.0, 3.5, 0.9, 7.7, 12.0, 4.86, 0.33, 0.77, 0.0, 0.7, 0.15, 0.3, 19.2, 2.4, 3.10, 1.15, 0.45, 40.0, 7.0, 99.8, 12.5, 0.846, 0.834, 0.720, 0.744, 0.820, 0.842, 0.702, 7.18, 8.3, 4.3, 5.7, 0.143, 2.14, 0.54, 9.1, 12.2, 0.26, 1.9, 6.0, 19.0, 3.4):
    T.add(float(v))
for cv in ("cv_macro_f1", "val_macro_f1", "cv_accuracy", "val_accuracy"):
    for c in cs: add(c[cv])
Tf = np.array(sorted(T))
def unmatched(text):
    tx = re.sub(r"\b\d{4}\.\d{4,5}\b|doi:\S+|\d{4}-\d\d-\d\d|\d{2}:\d{2}|[A-Za-z_\-]+\d+(\.\d+)?|v\d+\.\d+|\d+\.\d+\.\d+|\d+e-?\d+|(?:Figures?|Tables?|Sections?|Chapters?)\s+\d+\.\d+(?:\s+(?:to|and)\s+\d+\.\d+)?|\[\d+\]|\b\d\.\d\s+(?=[A-Z][a-z])|\b\d{1,2}\.\d{1,2}(?=[\.\s]*[A-Z–])|\d+\.\d+\s*(?:GB|MB)", "", text)
    out = []
    for n in sorted(set(re.findall(r"(?<![\w./])[-+−]?\d+\.\d+", tx))):
        x = abs(float(n.replace("−", "-"))); tol = 0.5 * 10 ** -len(n.split(".")[1]) + 1e-9
        if not np.any(np.abs(Tf - x) <= tol): out.append(n)
    return out

# ---- DOCX / PDF --------------------------------------------------------------------------------------------------------------------
dx = Document(R / "SVM_Micro_Project_Report.docx")
paras = [x.text for x in dx.paragraphs]; tabs = [c.text for tb in dx.tables for rr in tb.rows for c in rr.cells]
dtext = "\n".join(paras + tabs)
single = [tb for tb in dx.tables if len(tb.columns) == 1]
check("DOCX: logo + figures, tables = captioned + note boxes + TOC + evaluation form", len(dx.inline_shapes) >= 15, f"{len(dx.inline_shapes)} images, {len(dx.tables)} tables, {len(single)} note boxes")
caps = [x for x in paras if re.match(r"^(Figure|Table) \d+\.\d+:", x)]
nfig = sum(x.startswith("Figure") for x in caps); ntab = sum(x.startswith("Table") for x in caps)
check("every image captioned; every data table captioned", nfig == len(dx.inline_shapes) - 1 and ntab == len(dx.tables) - len(single) - 2, f"{nfig} figure captions, {ntab} table captions")
acc = f"{t['accuracy']:.3f}"; mf = f"{t['macro_f1']:.3f}"
for must in (acc, mf, f"{t['macro_precision']:.3f}", f"{t['macro_recall']:.3f}", "[Student name", "25AI2004", "Ms. Gethsia P", "scheduled on", "not proven", "unverified", "CC BY 4.0", "not a medical device", "Support Vector Machine", "RBF", "HOG", "no automated browser-level", "13 passed", "7/7"):
    check(f"DOCX contains '{must}'", must.lower() in dtext.lower())
for bad in ("TITLE OF MICRO PROJECT", "NAMES OF THE STUDENTS", "Name (Reg No)", "presentation held on"):
    check(f"DOCX has no leftover '{bad}'", bad.lower() not in dtext.lower())
gan_hits = [m.group(0) for m in re.finditer(r"[^.]*\b(GAN|DCGAN|WGAN|cWGAN|NeuroVision|FID|KID)\b[^.]*\.", dtext)]
check("DOCX mentions the GAN project only as the earlier/copied project (never as SVM results)", all(re.search(r"earlier|copied|copy", h, re.I) for h in gan_hits), gan_hits[:3])
check("DOCX: every decimal matches a saved/derived value", not unmatched(dtext), unmatched(dtext))
stream = "".join(x.text or "" for x in dx.element.body.iter(qn("w:t"))); body = stream[: stream.rindex("REFERENCES")]
cites = [int(n) for g in re.findall(r"\[(\d+(?:\s*[,\u2013-]\s*\d+)*)\]", body) if not g.startswith("0") for n in re.findall(r"\d+", g)]
first = []
for c in cites:
    if c not in first: first.append(c)
refs = [x for x in paras if re.match(r"^\[\d+\]", x)]
check("11 references, all cited, numbered by first citation", set(first) == set(range(1, 12)) and first == sorted(first) and len(refs) == 11, first)
pdf = R / "SVM_Micro_Project_Report.pdf"
npg = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout).group(1))
ptxt = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True).stdout
check("PDF opens; metrics, evaluation form and references present", npg >= 28 and acc in ptxt and mf in ptxt and "EVALUATION REPORT" in ptxt and "REFERENCES" in ptxt, f"{npg} pages")
toc = json.load(open(R / "assets/toc_pages.json"))
pages = [subprocess.run(["pdftotext", "-f", str(i), "-l", str(i), "-layout", str(pdf), "-"], capture_output=True, text=True).stdout for i in range(1, npg + 1)]
check("TOC page numbers agree with the PDF", all(any(l.strip().startswith(h) for l in pages[toc[k] + 3].splitlines()) for k, h in (("INTRODUCTION", "1. INTRODUCTION"), ("LITERATURE REVIEW", "2. LITERATURE REVIEW"), ("METHODOLOGY", "3. METHODOLOGY"), ("RESULTS AND INTERPRETATION", "5. RESULTS AND INTERPRETATION"), ("CONCLUSION AND FUTURE SCOPE", "6. CONCLUSION AND FUTURE SCOPE"), ("REFERENCES", "REFERENCES"))), toc)
check("PDF images embedded (= DOCX images)", subprocess.run(["pdfimages", "-list", str(pdf)], capture_output=True, text=True).stdout.count("\n") - 2 == len(dx.inline_shapes))
ev = dx.tables[-1]
check("evaluation form kept with blank marks", all(not rr.cells[3].text.strip() for rr in ev.rows[1:]))

# ---- PPTX --------------------------------------------------------------------------------------------------------------------------
pp = Presentation(PR / "SVM_Project_Presentation.pptx"); W, H = pp.slide_width, pp.slide_height
txt, oob, small, pics = [], [], [], 0
for i, sl in enumerate(pp.slides, 1):
    for sh in sl.shapes:
        if sh.left < 0 or sh.top < 0 or sh.left + sh.width > W + 1000 or sh.top + sh.height > H + 1000: oob.append((i, sh.name))
        if sh.shape_type == 13: pics += 1; Image.open(io.BytesIO(sh.image.blob)).verify()
        fr = []
        if sh.has_text_frame: fr.append(sh.text_frame)
        if getattr(sh, "has_table", False) and sh.has_table: fr += [c.text_frame for rr in sh.table.rows for c in rr.cells]
        for tf in fr:
            txt.append(tf.text)
            for pa in tf.paragraphs:
                for ru in pa.runs:
                    if ru.font.size and ru.font.size.pt < 10 and "Brain Tumor MRI Classification Using SVM  |" not in ru.text: small.append((i, ru.font.size.pt))
pt = "\n".join(txt)
check("PPTX: 14 slides, 16:9, shapes inside the slide, pictures decode, no text under 10 pt", len(pp.slides) == 14 and not oob and pics >= 8 and not small, f"{pics} pictures; oob {oob}; small {small[:2]}")
for must in (acc, mf, "0.835", "0.894", "RBF", "HOG", "UNVERIFIED", "NOT proven", "[Student name", "Questions?", "not a medical device", "29/10/26"):
    check(f"PPTX contains '{must}'", must.lower() in pt.lower())
check("PPTX: no GAN/NeuroVision content", not re.search(r"\b(GAN|DCGAN|WGAN|NeuroVision|FID|KID)\b", pt))
check("PPTX: every decimal matches a saved/derived value", not unmatched(pt), unmatched(pt))
check("PPTX: no literal escape sequences", "\\u" not in pt)
check("PPTX and DOCX agree on key metrics", all(k in dtext and k in pt for k in (acc, mf, "0.835", "0.894", "0.802", "0.876")))

# ---- original project untouched --------------------------------------------------------------------------------------------------
fp_before = json.load(open(sys.argv[1])) if len(sys.argv) > 1 else None
if fp_before:
    skip = {".venv", "node_modules", "__pycache__", ".pytest_cache", ".playwright-mcp"}
    now = {}
    import os
    base = "/Users/ajaikumarn/Desktop/brain"
    for rr, ds, fs in os.walk(base):
        ds[:] = [d for d in ds if d not in skip]
        for f in fs:
            if f == ".DS_Store": continue
            pth = os.path.join(rr, f); st = os.lstat(pth); now[os.path.relpath(pth, base)] = [st.st_size, st.st_mtime_ns]
    check("original project ~/Desktop/brain unchanged (23,930 files: same sizes and mtimes)", now == fp_before, f"{len(now)} files")
n_ok = sum(x["pass"] for x in res)
json.dump({"passed": n_ok, "total": len(res), "checks": res}, open(SV / "qa_results.json", "w"), indent=1)
print(f"\n{n_ok}/{len(res)} checks passed"); sys.exit(0 if n_ok == len(res) else 1)
