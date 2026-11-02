# Approximate slide preview review

**This is an approximation, not a PowerPoint or Keynote render.** `scripts/render_slide_preview.py` draws each slide from the PPTX shape geometry with PIL (rectangles, word-wrapped text with per-run size/bold/colour, tables, pictures). Calibri is not installed, so Arial (about 10% wider) is used and wrapping is slightly pessimistic. Known limits of the approximation: arrows are drawn as plain rectangles, text is always left-aligned (centred text in the slide-4 boxes is not reproduced), shadows/themes/line spacing details are not reproduced, and chart images are shown as stored. It cannot tell you how PowerPoint or Keynote will lay out the deck. **Open the PPTX in PowerPoint or Keynote and check every slide yourself.**

Preview files: `index.html` (self-contained, slide navigation), `contact_sheet.png`, `slide_01.png` ... `slide_14.png` (1920x1080), `approx_flags.json` (automatic overflow flags; none were raised).

## Defects found and fixed (PPTX edited; previous file kept in `_build_history/`)
1. **Slide 4, flow boxes:** four boxes stored a literal newline inside one text run (e.g. "Cluster-disjoint split\n2,311 / 492 / 492"). PowerPoint/Keynote may collapse or mis-render that. Each was split into two real paragraphs. Text and numbers unchanged.
2. **Slide 5, projection-critic cell:** the characters U+27E8/U+27E9 (angle brackets) are not in Calibri and could show as empty boxes. Replaced `⟨E(y), h(x)⟩` with `E(y)·h(x)` (the same inner product). No other non-Calibri-risk glyphs were found (checked: ± × β λ ψ • → − ≥ are standard).

## Per-slide result
| Slide | Result | Notes |
|---|---|---|
| 1 | no obvious issue in approximation | Programme line "B.Tech ... (specialization: Artificial Intelligence)" fits on one line at 16 pt in the 11.7 in box (about 2 in of slack in Arial), so no wrapping is expected; guide/date placeholders visible. Contrast gold-on-navy is good. |
| 2 | no obvious issue in approximation | Framing box has spare space. |
| 3 | no obvious issue in approximation | Text, table (header "no tumour" wraps to two lines) and amber box fit; the amber box is about half empty (cosmetic). UNVERIFIED wording for the download record is present. Table font is small-ish (12 pt) but legible. |
| 4 | fixed, then no obvious issue in approximation | See defect 1. Arrows and centring are not reproduced by the approximation. |
| 5 | fixed, then no obvious issue in approximation | See defect 2. Dense table at about 12 pt; legible. |
| 6 | no obvious issue in approximation | Two text columns, no overflow. |
| 7 | refined, then no obvious issue in approximation | Picture enlarged from 8.6 to 9.2 in wide (aspect ratio kept); text column narrowed to 3.4 in and still fits. Labels baked into the PNG remain small: real legibility not assessable. |
| 8 | refined, then no obvious issue in approximation | Table narrowed to 5.1 in, chart enlarged from 6.3 to 7.4 in wide, notes box widened; no overlap. Chart's internal text still small. |
| 9 | refined, then possible issue | Picture enlarged from 6.9 to 7.4 in; table/text moved right. The mostly empty amber note box is still unbalanced (cosmetic, left unchanged). |
| 10 | refined, then no obvious issue in approximation | Chart enlarged from 7.7 to 8.6 in (aspect ratio kept) and moved up 0.45 in; right text column narrowed to 3.9 in and fits. Chart text is the figure's own and remains small; the size gain is limited by the slide width. Values match the table. |
| 11 | refined, then no obvious issue in approximation | Table row height 0.46 -> 0.42 in and moved to 4.55 in: the table now ends about 6.65 in, i.e. roughly 0.4 in above the footer (was about 0.15 in). Table text size unchanged. Confusion-matrix image unchanged. |
| 12 | no obvious issue in approximation | Large amber box with about a third unused. |
| 13 | no obvious issue in approximation | Future-work box mostly empty (cosmetic). |
| 14 | refined, then no obvious issue in approximation | Picture enlarged from 8.4 to 12.6 in wide (full width, aspect ratio kept); bullet and reference boxes moved below it. Label legibility inside the image not assessable. |

"Not assessable" for all slides: real font rendering (Calibri), exact line spacing, how PowerPoint grows table rows, text autofit, animations, speaker notes display.

## Layout refinements (second pass)
Only positions, sizes and column widths were changed (picture aspect ratios preserved, nothing cropped, no text or values altered). Slides changed: 7, 8, 9, 10, 11, 14. Slides 1-6, 12 and 13 unchanged in this pass. Previous PPTX saved in `_build_history/`. After the edit the approximation raised no automatic flags and the contact sheet was inspected again. **The native PowerPoint/Keynote check is still open.**

## Independent LibreOffice render (supplied by the user's ChatGPT session)
A genuine LibreOffice Impress 25.2.3.2 render of the current deck (14 pages; `E(y)·h(x)` and the full-width slide-14 image present) was reviewed. It reported no must-fix layout defects; small labels inside chart and sample-grid images remain the main readability limit. Viewing the render also showed one real defect that the approximation could not: in the filled note boxes on slides 3, 8 and 12 the first paragraph had an explicit centre alignment while the others were left-aligned. The first paragraph on those three slides was set to left alignment (slide 13's bold "Future work" heading and the single-paragraph boxes on slides 2 and 9 stay centred on purpose). LibreOffice is not PowerPoint or Keynote: the native check remains open.
