#!/usr/bin/env python3
"""Find the page on which each TOC heading is printed in a rendered PDF and write assets/toc_pages.json (arabic numbers; the front matter is 4 pages: i-iv).
usage: compute_toc.py report.pdf"""
import json, re, subprocess, sys
from pathlib import Path
pdf = Path(sys.argv[1]); out = Path(__file__).resolve().parents[1] / "assets/toc_pages.json"
n = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout).group(1))
pages = [subprocess.run(["pdftotext", "-f", str(i), "-l", str(i), "-layout", str(pdf), "-"], capture_output=True, text=True).stdout for i in range(1, n + 1)]
FRONT = 4
heads = {"INTRODUCTION": "1. INTRODUCTION", "LITERATURE REVIEW": "2. LITERATURE REVIEW", "METHODOLOGY": "3. METHODOLOGY",
         "FABRICATION/SIMULATION/PROGRAM OR CODE/DESIGN": "4. FABRICATION / SIMULATION / PROGRAM OR CODE / DESIGN",
         "RESULTS AND INTERPRETATION": "5. RESULTS AND INTERPRETATION", "CONCLUSION AND FUTURE SCOPE": "6. CONCLUSION AND FUTURE SCOPE", "REFERENCES": "REFERENCES",
         "1.1": "1.1 Background of the selected problem", "1.2": "1.2 Industry Relevance", "1.3": "1.3 Aim and Objective of the Micro Project", "1.4": "1.4 Link to SDG / KITS Technology Mission"}
res = {}
for key, text in heads.items():
    for i in range(FRONT, n):   # 0-based index FRONT == pdf page FRONT+1
        if any(line.strip().startswith(text) for line in pages[i].splitlines()):
            res[key] = i + 1 - FRONT; break
    else:
        raise SystemExit(f"heading not found: {text}")
out.write_text(json.dumps(res, indent=1)); print(res, "| total pdf pages", n, "| last page is the evaluation form:", "EVALUATION REPORT" in pages[-1])
