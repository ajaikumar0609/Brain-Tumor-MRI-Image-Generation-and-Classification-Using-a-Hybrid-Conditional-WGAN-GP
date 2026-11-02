"""Helpers that append template-styled content to a python-docx Document opened from the official e-report template.
Body font Times New Roman (the template's default); tables copy the template's black borders and DBEEF3 header shading."""
import re
from pathlib import Path
from docx.enum.text import WD_ALIGN_PARAGRAPH as AL
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

FONT = "Times New Roman"
BODY_PT = 12
TEXT_W = 6.5  # inches available between the template's margins (8.5 - 2 x 0.985)


def _run(p, text, size=BODY_PT, bold=False, italic=False, color=None, font=FONT):
    r = p.add_run(text)
    r.font.name = font
    r._element.rPr.rFonts.set(qn("w:eastAsia"), font)
    r.font.size = Pt(size)
    r.bold = bold or None
    r.italic = italic or None
    if color:
        r.font.color.rgb = RGBColor.from_string(color)
    return r


_TOK = re.compile(r"(\*\*[^*]+\*\*|\*[^*]+\*)")


def rich(p, text, size=BODY_PT, bold=False, italic=False, color=None):
    """**bold** and *italic* inline markup."""
    for part in _TOK.split(text):
        if not part:
            continue
        if part.startswith("**"):
            _run(p, part[2:-2], size, True, italic, color)
        elif part.startswith("*"):
            _run(p, part[1:-1], size, bold, True, color)
        else:
            _run(p, part, size, bold, italic, color)


class Builder:
    def __init__(self, doc):
        self.doc = doc
        self.fig = {}
        self.tab = {}
        self.chapter = 0

    # ---- paragraphs -------------------------------------------------------------------------------------------
    def para(self, text="", align=AL.JUSTIFY, size=BODY_PT, bold=False, italic=False, before=0, after=6, line=1.15, keep_next=False,
             left=None, first=None, color=None, page_break=False, outline=None):
        p = self.doc.add_paragraph()
        pf = p.paragraph_format
        pf.alignment = align
        pf.space_before, pf.space_after, pf.line_spacing = Pt(before), Pt(after), line
        pf.keep_with_next = keep_next or None
        pf.page_break_before = page_break or None
        pf.widow_control = True
        if left is not None:
            pf.left_indent = Inches(left)
        if first is not None:
            pf.first_line_indent = Inches(first)
        if outline is not None:
            ppr = p._p.get_or_add_pPr()
            o = OxmlElement("w:outlineLvl")
            o.set(qn("w:val"), str(outline))
            ppr.append(o)
        if text:
            rich(p, text, size, bold, italic, color)
        return p

    def chapter_heading(self, number, title):
        self.chapter = number
        self.fig[number] = 0
        self.tab[number] = 0
        self.para(f"{number}. {title}", AL.LEFT, 14, True, before=0, after=10, keep_next=True, page_break=True, outline=0)

    def h2(self, num, title):
        self.para(f"{num} {title}", AL.LEFT, 12, True, before=8, after=4, keep_next=True, outline=1)

    def h3(self, title):
        self.para(title, AL.LEFT, 12, True, italic=True, before=4, after=3, keep_next=True)

    def bullets(self, items, left=0.3, size=BODY_PT, after=3):
        for it in items:
            p = self.para("", AL.JUSTIFY, size, after=after, left=left, first=-0.2)
            rich(p, "•  " + it, size)

    def numbered(self, items, left=0.35, size=BODY_PT, after=3, prefix="O"):
        for i, it in enumerate(items, 1):
            p = self.para("", AL.JUSTIFY, size, after=after, left=left, first=-0.35)
            rich(p, f"{prefix}{i}.  " + it, size)

    def equation(self, text):
        self.para(text, AL.CENTER, 12, italic=True, before=2, after=6)

    # ---- captions ---------------------------------------------------------------------------------------------
    def caption(self, kind, text, keep_next=False):
        n = self.chapter
        counter = self.fig if kind == "Figure" else self.tab
        counter[n] += 1
        label = f"{kind} {n}.{counter[n]}"
        p = self.para("", AL.CENTER, 10, before=2, after=8 if kind == "Figure" else 3, line=1.0, keep_next=keep_next)
        _run(p, label + ": ", 10, True)
        rich(p, text, 10)
        return label

    # ---- figures ----------------------------------------------------------------------------------------------
    def figure(self, path, caption, width=6.0, crop=None):
        p = self.doc.add_paragraph()
        p.paragraph_format.alignment = AL.CENTER
        p.paragraph_format.space_before, p.paragraph_format.space_after = Pt(4), Pt(0)
        p.paragraph_format.keep_with_next = True
        src = str(path)
        if crop:
            from PIL import Image
            im = Image.open(path)
            im = im.crop(crop)
            cp = Path(__file__).resolve().parents[1] / "assets" / "_cropped"
            cp.mkdir(exist_ok=True)
            out = cp / (Path(path).stem + f"_{crop[1]}_{crop[3]}.png")
            im.save(out)
            src = str(out)
        p.add_run().add_picture(src, width=Inches(width))
        return self.caption("Figure", caption)

    # ---- tables -----------------------------------------------------------------------------------------------
    @staticmethod
    def _cell_borders(cell, sz=4):
        tcPr = cell._tc.get_or_add_tcPr()
        b = OxmlElement("w:tcBorders")
        for edge in ("top", "left", "bottom", "right"):
            e = OxmlElement(f"w:{edge}")
            e.set(qn("w:val"), "single"); e.set(qn("w:sz"), str(sz)); e.set(qn("w:space"), "0"); e.set(qn("w:color"), "000000")
            b.append(e)
        tcPr.append(b)

    @staticmethod
    def shade(cell, fill):
        tcPr = cell._tc.get_or_add_tcPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), fill)
        tcPr.append(shd)

    def table(self, caption, rows, widths, size=10, align=None, header=True, bold_rows=(), shade_rows=None, caption_keep=True):
        """rows: list of lists of strings (inline markup allowed). widths: inches per column. align: per-column 'l'|'c'|'r'."""
        if caption:
            self.caption("Table", caption, keep_next=caption_keep)
        t = self.doc.add_table(rows=len(rows), cols=len(rows[0]))
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        t.autofit = False
        tblPr = t._tbl.tblPr
        lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "fixed"); tblPr.append(lay)
        mar = OxmlElement("w:tblCellMar")
        for edge, w in (("top", 25), ("left", 70), ("bottom", 25), ("right", 70)):
            e = OxmlElement(f"w:{edge}"); e.set(qn("w:w"), str(w)); e.set(qn("w:type"), "dxa"); mar.append(e)
        tblPr.append(mar)
        align = align or ["l"] * len(widths)
        amap = {"l": AL.LEFT, "c": AL.CENTER, "r": AL.RIGHT}
        for i, row in enumerate(rows):
            tr = t.rows[i]
            trPr = tr._tr.get_or_add_trPr()
            cs = OxmlElement("w:cantSplit"); trPr.append(cs)
            if header and i == 0:
                th = OxmlElement("w:tblHeader"); trPr.append(th)
            for j, txt in enumerate(row):
                c = tr.cells[j]
                c.width = Inches(widths[j])
                self._cell_borders(c)
                if header and i == 0:
                    self.shade(c, "DBEEF3")
                elif shade_rows and i in shade_rows:
                    self.shade(c, shade_rows[i])
                p = c.paragraphs[0]
                p.paragraph_format.alignment = AL.CENTER if (header and i == 0) else amap[align[j]]
                p.paragraph_format.space_after = Pt(0)
                p.paragraph_format.line_spacing = 1.0
                if i < len(rows) - 1:
                    p.paragraph_format.keep_with_next = True
                rich(p, str(txt), size, bold=(header and i == 0) or (i in bold_rows))
        self.para("", after=4, line=0.8)
        return t

    def note(self, title, text, fill="FDF1DC", size=11):
        t = self.doc.add_table(rows=1, cols=1)
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        t.autofit = False
        c = t.rows[0].cells[0]
        c.width = Inches(TEXT_W - 0.1)
        self._cell_borders(c, 8)
        self.shade(c, fill)
        mar = OxmlElement("w:tblCellMar")
        for edge in ("top", "left", "bottom", "right"):
            e = OxmlElement(f"w:{edge}"); e.set(qn("w:w"), "110"); e.set(qn("w:type"), "dxa"); mar.append(e)
        t._tbl.tblPr.append(mar)
        p = c.paragraphs[0]
        p.paragraph_format.space_after = Pt(2)
        _run(p, title, size, True)
        for line in text if isinstance(text, list) else [text]:
            q = c.add_paragraph()
            q.paragraph_format.alignment = AL.JUSTIFY
            q.paragraph_format.space_after = Pt(2)
            rich(q, line, size)
        self.para("", after=4, line=0.8)
