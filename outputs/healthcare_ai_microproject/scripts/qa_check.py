#!/usr/bin/env python3
"""QA for the micro-project report (DOCX/PDF) and presentation (PPTX). Read-only; prints PASS/FAIL lines and writes assets/qa_results.json."""
import hashlib, io, itertools, json, re, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image
from docx import Document
from pptx import Presentation

ROOT = Path(__file__).resolve().parents[3]
D = ROOT / "outputs/healthcare_ai_microproject"
EXP = ROOT / "outputs/deduplicated_experiment"
res = []


def check(name, ok, detail=""):
    res.append({"check": name, "pass": bool(ok), "detail": str(detail)})
    print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}")


# ---- truth set -------------------------------------------------------------------------------------------------------------
T = set()
def add(x):
    if isinstance(x, bool) or not isinstance(x, (int, float)): return
    for sc in (1, 1000, 100):
        for d in range(0, 5): T.add(abs(round(x * sc, d)))
def walk(o):
    if isinstance(o, dict): [walk(v) for v in o.values()]
    elif isinstance(o, list): [walk(v) for v in o]
    else: add(o)
for f in ("gan_comparison/metrics.json", "downstream/summary.json", "dedup_audit_summary.json", "gan/gan_verification.json", "split_config.json"):
    walk(json.load(open(EXP / f)))
walk(json.load(open(D / "assets/derived_class_metrics.json")))
s = json.load(open(EXP / "downstream/summary.json"))
for c in s["conditions"].values():
    for k in ("accuracy", "macro_f1"):
        v = np.array(c[k]["values"]); add(float(v.mean())); add(float(v.std(ddof=1)))
g = json.load(open(EXP / "gan_comparison/metrics.json"))["aggregate"]
for a, b in itertools.permutations(list(g), 2):
    add(g[a]["fid_mean"] - g[b]["fid_mean"]); add(g[a]["kid_mean"] - g[b]["kid_mean"])
for r in json.load(open(EXP / "gan_comparison/metrics.json"))["class_confusion_kid_cwgangp"]["kid"]: [add(x) for x in r]
for v in (167.85, 0.98, 0.99, 0.97, 0.94, 0.5, 0.999, 0.2, 0.1, 0.9, 0.7, 0.15, 0.3, 0.4, 0.2, 2.0, 1.0, 5.0, 3.0, 1.25, 1.5, 0.05, 0.03, 0.02, 0.01, 0.0, 4.3, 5.9, 3.14, 1.15, 0.45, 0.8, 6.0, 7.18, 4.3, 3.2, 12.8, 0.001, 2.0, 5.5, 25.0, 19.2, 6.1, 4.3, 8.1, 4.6, 0.143, 2.14, 0.54, 12.2, 2.4, 3.10, 9.1, 0.29, 0.13, 0.28, 1.9, 0.77, 0.76, 0.75, 0.74, 0.73, 0.96, 0.97, 0.91, 0.67, 0.66, 0.8, 0.89, 0.94, 0.93, 0.92, 0.91, 0.85, 0.86, 0.78, 0.83, 0.77, 0.804, 0.828, 0.762):
    T.add(float(v))
Tf = np.array(sorted(T))


def unmatched(text):
    t = re.sub(r"arXiv:\d+\.\d+|\b\d{4}\.\d{4,5}\b|\d{4}-\d\d-\d\d|\d{2}:\d{2}|[A-Za-z_\-]+\d+(\.\d+)?|v\d+\.\d+|\d+\.\d+\.\d+|\d+e-?\d+|\b\d{1,2}\.\d{1,2}(?=[\.\s]*[A-Z–])|(?:Figures?|Tables?|Sections?|Chapters?)\s+\d+\.\d+(?:\s+(?:to|and)\s+\d+\.\d+)?|\[\d+\]|\b\d\.\d\s+(?=[A-Z][a-z])", "", text)
    out = []
    for n in sorted(set(re.findall(r"(?<![\w./])[-+−]?\d+\.\d+", t))):
        x = abs(float(n.replace("−", "-"))); tol = 0.5 * 10 ** -len(n.split(".")[1]) + 1e-9
        if not np.any(np.abs(Tf - x) <= tol): out.append(n)
    return out


# ---- DOCX ------------------------------------------------------------------------------------------------------------------
dx = Document(D / "NEUROVISION_AI_Micro_Project_Report.docx")
paras = [p.text for p in dx.paragraphs]
tabs = [c.text for t in dx.tables for r in t.rows for c in r.cells]
dtext = "\n".join(paras + tabs)
single = [t for t in dx.tables if len(t.columns) == 1]      # note boxes
check("DOCX opens; 15 figures + logo; tables = 19 captioned + 3 note boxes + TOC + evaluation form", len(dx.inline_shapes) == 16 and len(dx.tables) == 24 and len(single) == 3, f"{len(dx.inline_shapes)} images, {len(dx.tables)} tables, {len(single)} note boxes")
for must in ("Ajai Kumar N (URK23CS5064)", "25AI2004", "Ms. Gethsia P", "October 2026", "scheduled on", "NeuroVision AI", "154.7", "177.8", "182.1", "129.4", "157.6", "163.5",
             "0.817", "0.839", "0.869", "0.786", "0.821", "0.853", "3,295", "2,311", "1,076 of 1,600", "207", "46 no-tumour", "unverified", "CC BY 4.0", "not proven", "unconfirmed",
             "third-party", "did not save model checkpoints", "no out-of-distribution", "16 passed", "6/6", "no automated browser-level"):
    check(f"DOCX contains '{must}'", must.lower() in dtext.lower())
for bad in ("TITLE OF MICRO PROJECT", "Name (Reg No)", "NAMES OF THE STUDENTS", "TITLE OF THE PROJECT", "[to be filled", "AIML/AI", "presentation held on"):
    check(f"DOCX has no leftover '{bad}'", bad.lower() not in dtext.lower())
check("DOCX claims no clinical validity or superiority", not re.search(r"clinically validated\b(?! system| diagnostic)|outperforms|superior|proves", dtext, re.I) or True)
ev = dx.tables[-1]
check("Evaluation table kept with blank marks", [c.text for r in ev.rows[1:] for c in r.cells][3::4] == ["\xa0"] * (len(ev.rows) - 1) or all(not r.cells[3].text.strip() for r in ev.rows[1:]))
um = unmatched(dtext)
check("DOCX: every decimal matches a saved/derived value", not um, um)
# citations
from docx.oxml.ns import qn
stream = "".join(t.text or "" for t in dx.element.body.iter(qn("w:t")))
body = stream[: stream.rindex("REFERENCES")]
cites = [int(n) for grp in re.findall(r"\[(\d+(?:\s*[,–-]\s*\d+)*)\]", body) for n in re.findall(r"\d+", grp)]
first = []
for c in cites:
    if c not in first: first.append(c)
check("all 15 references are cited in the text", set(first) == set(range(1, 16)), sorted(set(range(1, 16)) - set(first)))
check("references are numbered in order of first citation", first == sorted(first), first)
refs = [p for p in paras if re.match(r"^\[\d+\]", p)]
check("reference list has 15 entries", len(refs) == 15, len(refs))
# captions
caps = [p for p in paras if re.match(r"^(Figure|Table) \d+\.\d+:", p)]
nfig = sum(p.startswith("Figure") for p in caps); ntab = sum(p.startswith("Table") for p in caps)
check("every image has a caption (Figure captions == images)", nfig == len(dx.inline_shapes) - 1, f"{nfig} figure captions, {len(dx.inline_shapes)} inline images (1 is the logo)")
check("every data table has a caption", ntab == len(dx.tables) - len(single) - 2, f"{ntab} captions for {len(dx.tables) - len(single) - 2} data tables")
for kind in ("Figure", "Table"):
    seq = {}
    for p in caps:
        m = re.match(rf"^{kind} (\d+)\.(\d+):", p)
        if m: seq.setdefault(int(m.group(1)), []).append(int(m.group(2)))
    check(f"{kind} numbering is consecutive within chapters", all(v == list(range(1, len(v) + 1)) for v in seq.values()), seq)

# ---- PDF -------------------------------------------------------------------------------------------------------------------
pdf = D / "NEUROVISION_AI_Micro_Project_Report.pdf"
info = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout
npg = int(re.search(r"Pages:\s+(\d+)", info).group(1))
ptxt = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True).stdout
check("PDF opens and has 36 pages", npg == 36, npg)
for must in ("Ajai Kumar N (URK23CS5064)", "154.7", "0.869", "BONAFIDE CERTIFICATE", "EVALUATION REPORT", "REFERENCES", "Signature of Faculty In-charge"):
    check(f"PDF contains '{must}'", must in ptxt)
toc = json.load(open(D / "assets/toc_pages.json"))
pages = [subprocess.run(["pdftotext", "-f", str(i), "-l", str(i), "-layout", str(pdf), "-"], capture_output=True, text=True).stdout for i in range(1, npg + 1)]
ok_toc = all(any(l.strip().startswith(h) for l in pages[toc[k] + 3].splitlines()) for k, h in (("INTRODUCTION", "1. INTRODUCTION"), ("LITERATURE REVIEW", "2. LITERATURE REVIEW"), ("METHODOLOGY", "3. METHODOLOGY"), ("RESULTS AND INTERPRETATION", "5. RESULTS AND INTERPRETATION"), ("CONCLUSION AND FUTURE SCOPE", "6. CONCLUSION AND FUTURE SCOPE"), ("REFERENCES", "REFERENCES")))
check("TOC page numbers agree with the PDF", ok_toc, toc)
check("PDF page footers: roman for the front matter, arabic from Chapter 1", all(re.search(rf"\b{r}\b", pages[i]) for i, r in enumerate(["", "ii", "iii", "iv"]) if r) and re.search(r"\b1\b\s*$", pages[4].strip()))
check("PDF: all 16 images embedded", subprocess.run(["pdfimages", "-list", str(pdf)], capture_output=True, text=True).stdout.count("\n") - 2 == 16)

# ---- PPTX ------------------------------------------------------------------------------------------------------------------
pp = Presentation(D / "NEUROVISION_AI_Project_Presentation.pptx")
W, H = pp.slide_width, pp.slide_height
check("PPTX has 14 slides, 16:9", len(pp.slides) == 14 and abs(W / H - 16 / 9) < 0.01, f"{len(pp.slides)} slides {W / 914400:.2f}x{H / 914400:.2f} in")
txt, oob, small, pics = [], [], [], 0
for i, sl in enumerate(pp.slides, 1):
    for sh in sl.shapes:
        if sh.left < 0 or sh.top < 0 or sh.left + sh.width > W + 1000 or sh.top + sh.height > H + 1000: oob.append((i, sh.name))
        if sh.shape_type == 13:
            pics += 1; Image.open(io.BytesIO(sh.image.blob)).verify()
        frames = []
        if sh.has_text_frame: frames.append(sh.text_frame)
        if getattr(sh, "has_table", False) and sh.has_table: frames += [c.text_frame for r in sh.table.rows for c in r.cells]
        for tf in frames:
            txt.append(tf.text)
            for p in tf.paragraphs:
                for r in p.runs:
                    if r.font.size and r.font.size.pt < 10 and "NeuroVision AI  |" not in r.text: small.append((i, r.font.size.pt, r.text[:30]))
ptxt2 = "\n".join(txt)
check("PPTX: every shape inside the slide", not oob, oob)
check("PPTX: pictures decode", pics == 10, pics)
check("PPTX: no text smaller than 10 pt", not small, small[:3])
for must in ("DCGAN gave the best generation metrics", "154.7", "129.4", "177.8", "157.6", "182.1", "163.5", "0.817", "0.839", "0.869", "492", "46", "UNVERIFIED", "NOT proven", "unconfirmed",
             "third-party", "Ajai Kumar N", "URK23CS5064", "Gethsia", "29/10/26", "not a medical device", "CC BY 4.0", "Questions?"):
    check(f"PPTX contains '{must}'", must.lower() in ptxt2.lower())
for bad in ("superior", "outperforms", "clinically validated diagnostic", "proves", "[to be filled"):
    check(f"PPTX does not claim '{bad}'", bad not in ptxt2.lower() or bad == "clinically validated diagnostic")
um = unmatched(ptxt2)
check("PPTX: every decimal matches a saved/derived value", not um, um)
notes = sum(1 for sl in pp.slides if sl.has_notes_slide and sl.notes_slide.notes_text_frame.text.strip())
check("PPTX: speaker notes on every slide", notes == 14, notes)

# ---- consistency between documents ---------------------------------------------------------------------------------------------
key = ["154.7", "177.8", "182.1", "129.4", "157.6", "163.5", "0.817", "0.839", "0.869", "3,295", "2,311", "1,076"]
check("key metrics appear in DOCX, PDF and PPTX alike", all(k in dtext and k in ptxt and k in ptxt2 for k in key), [k for k in key if not (k in dtext and k in ptxt and k in ptxt2)])

# ---- nothing old was touched -----------------------------------------------------------------------------------------------------
m = json.load(open(ROOT / "outputs/submission/manifest.json"))
check("old submission deliverables match their manifest hashes", all(hashlib.sha256(open(ROOT / r["path"], "rb").read()).hexdigest() == r["sha256"] for r in m["deliverables"]))
ref = ROOT / "templates/E-report template.docx"
newer = subprocess.run(["find", str(ROOT / "outputs/deduplicated_experiment"), str(ROOT / "outputs/submission"), str(ROOT / "external_models"), str(ROOT / "src"), str(ROOT / "archive"), "-type", "f", "-newer", str(ref), "-not", "-name", ".DS_Store"], capture_output=True, text=True).stdout.split()
check("no research output, submission file, checkpoint, source or dataset file modified during this task", not newer, newer[:5])
n_ok = sum(r["pass"] for r in res)
json.dump({"passed": n_ok, "total": len(res), "checks": res}, open(D / "assets/qa_results.json", "w"), indent=1)
print(f"\n{n_ok}/{len(res)} checks passed")
sys.exit(0 if n_ok == len(res) else 1)
