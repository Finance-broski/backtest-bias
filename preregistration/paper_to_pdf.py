"""Render PAPER_selection_lookahead_SSRN.md as an SSRN-style working-paper PDF, the same layout as
the survivorship paper (SSRN 7099378): Times, A4, centred title block, indented abstract, results on
a new page."""
import re, io
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                HRFlowable, KeepTogether, PageBreak)

SRC = r"C:\dev\backtest-bias\preregistration\PAPER_selection_lookahead_SSRN.md"
import os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "PAPER_selection_lookahead_SSRN.pdf")

INK = colors.HexColor("#111111"); GREY = colors.HexColor("#444444")
title_s = ParagraphStyle("t", fontName="Times-Bold", fontSize=15.5, leading=19,
                         alignment=TA_CENTER, textColor=INK, spaceAfter=8)
auth_s = ParagraphStyle("a", fontName="Times-Roman", fontSize=10.5, leading=14,
                        alignment=TA_CENTER, textColor=INK)
ver_s = ParagraphStyle("v", fontName="Times-Italic", fontSize=9, leading=12,
                       alignment=TA_CENTER, textColor=GREY, spaceAfter=10)
h2_s = ParagraphStyle("h2", fontName="Times-Bold", fontSize=12, leading=15,
                      textColor=INK, spaceBefore=9, spaceAfter=4)
h3_s = ParagraphStyle("h3", fontName="Times-BoldItalic", fontSize=10.8, leading=14,
                      textColor=INK, spaceBefore=6, spaceAfter=3)
body_s = ParagraphStyle("b", fontName="Times-Roman", fontSize=11, leading=14.4,
                        alignment=TA_JUSTIFY, textColor=INK, spaceAfter=5.5)
abst_s = ParagraphStyle("ab", parent=body_s, leftIndent=22, rightIndent=22, fontSize=10.2,
                        leading=13.8)
ref_s = ParagraphStyle("r", parent=body_s, leftIndent=14, firstLineIndent=-14,
                       spaceAfter=1.5, fontSize=9.7, leading=12.4)
# No dictionary hyphenation: pyphen split "full-window" as "ful-l-window". Compound words may
# still break at their own hyphen.
for _s in (body_s, abst_s, ref_s):
    _s.embeddedHyphenation = 1
num_s = ParagraphStyle("num", parent=body_s, leftIndent=14, firstLineIndent=-14, spaceAfter=2.5)
bmh_s = ParagraphStyle("bmh", fontName="Times-Bold", fontSize=10.5, leading=13,
                       textColor=INK, spaceBefore=5, spaceAfter=2)
bm_s = ParagraphStyle("bm", parent=body_s, fontSize=9.7, leading=12.6, spaceAfter=3)
cell_s = ParagraphStyle("c", fontName="Times-Roman", fontSize=9.7, leading=12.5,
                        alignment=TA_CENTER)
kw_s = ParagraphStyle("kw", fontName="Times-Roman", fontSize=9.3, leading=12.5,
                      leftIndent=22, rightIndent=22, textColor=GREY, spaceAfter=2)
cellh_s = ParagraphStyle("ch", parent=cell_s, fontName="Times-Bold")

def inline(s):
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", s)
    s = s.replace("Table 1", "Table 1")
    return s

lines = io.open(SRC, encoding="utf-8").read().splitlines()
story, i, in_refs, in_back = [], 0, False, False
para_buf = []

def flush_para():
    global para_buf
    if para_buf:
        txt = " ".join(x.strip() for x in para_buf)
        story.append(Paragraph(inline(txt), ref_s if in_refs else (bm_s if in_back else body_s)))
        para_buf = []

while i < len(lines):
    ln = lines[i].rstrip()
    if not ln.strip():
        flush_para(); i += 1; continue
    if ln.startswith("# "):
        flush_para(); story.append(Paragraph(inline(ln[2:]), title_s)); i += 1; continue
    if ln.startswith("**Keywords:**") or ln.startswith("**JEL"):
        flush_para(); story.append(Paragraph(inline(ln), kw_s)); i += 1; continue
    if ln.startswith("**Ayan Jain**"):
        flush_para(); story.append(Paragraph(inline(ln), auth_s)); i += 1; continue
    if ln.startswith("*Working paper"):
        flush_para(); story.append(Paragraph(inline(ln.strip("*")), ver_s))
        story.append(HRFlowable(width="100%", thickness=0.7, color=GREY, spaceAfter=8))
        i += 1; continue
    if ln.startswith("## "):
        flush_para()
        head = ln[3:]
        in_refs = head.lower().startswith("references")
        if head.lower() == "abstract":
            story.append(Paragraph("<b>Abstract</b>", ParagraphStyle("abh", parent=h2_s, alignment=TA_CENTER)))
            # abstract body = next non-empty paragraph, styled abst_s
            i += 1
            buf = []
            while i < len(lines) and not lines[i].startswith("## "):
                if lines[i].strip(): buf.append(lines[i].strip())
                elif buf: break
                i += 1
            story.append(Paragraph(inline(" ".join(buf)), abst_s))
            continue
        if head.lower().startswith(("4. results", "references")):
            story.append(PageBreak())
        if head.lower().startswith(("acknowledg", "declaration", "conflict")):
            in_back = True
            story.append(Paragraph(inline(head), bmh_s)); i += 1; continue
        story.append(Paragraph(inline(head), h2_s)); i += 1; continue
    if ln.startswith("### "):
        flush_para(); story.append(Paragraph(inline(ln[4:]), h3_s)); i += 1; continue
    if ln.startswith("|"):
        flush_para()
        rows = []
        while i < len(lines) and lines[i].startswith("|"):
            cells = [c.strip() for c in lines[i].strip("|").split("|")]
            if not all(re.fullmatch(r":?-+:?", c) for c in cells):
                rows.append(cells)
            i += 1
        data = [[Paragraph(inline(c), cellh_s if r == 0 else (cellh_s if ci == 0 else cell_s))
                 for ci, c in enumerate(row)] for r, row in enumerate(rows)]
        tw = 160*mm
        ncol = len(rows[0])
        widths = [tw*0.4] + [tw*0.3]*(ncol-1) if ncol <= 3 else [tw*0.34] + [tw*0.66/(ncol-1)]*(ncol-1)
        tbl = Table(data, colWidths=widths)
        tbl.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#999999")),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#efefef")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        group = [Spacer(1, 4), tbl, Spacer(1, 6)]
        while story and isinstance(story[-1], Paragraph) and story[-1].style.name in ("h2", "h3"):
            group.insert(0, story.pop())
        story.append(KeepTogether(group))
        continue
    if re.match(r"^\d+\. \S", ln):
        flush_para(); story.append(Paragraph(inline(ln), num_s)); i += 1; continue
    if ln.startswith("- "):
        flush_para()
        pref = "&bull; " if not in_refs else ""
        story.append(Paragraph(pref + inline(ln[2:]),
                               ref_s if in_refs else ParagraphStyle("bl", parent=body_s, leftIndent=24, firstLineIndent=-11, spaceAfter=3)))
        i += 1; continue
    para_buf.append(ln); i += 1
flush_para()

# keep-with-next: bind each heading (and heading runs) to the following flowable
merged, j = [], 0
while j < len(story):
    el = story[j]
    if isinstance(el, Paragraph) and el.style.name in ("h2", "h3", "bmh"):
        grp, k = [el], j + 1
        while k < len(story) and isinstance(story[k], Paragraph) and story[k].style.name in ("h2", "h3", "bmh"):
            grp.append(story[k]); k += 1
        if k < len(story):
            grp.append(story[k]); k += 1
        merged.append(KeepTogether(grp)); j = k
    else:
        merged.append(el); j += 1
story = merged

def footer(canvas, doc):
    canvas.saveState(); canvas.setFont("Times-Roman", 8.5); canvas.setFillColor(GREY)
    canvas.drawCentredString(A4[0]/2, 12*mm, str(doc.page))
    canvas.restoreState()

doc = SimpleDocTemplate(OUT, pagesize=A4, leftMargin=25*mm, rightMargin=25*mm,
                        topMargin=20*mm, bottomMargin=18*mm,
                        title="Selection Look-Ahead Is Not a Data Problem",
                        author="Ayan Jain")
doc.build(story, onFirstPage=footer, onLaterPages=footer)
from pypdf import PdfReader
print("pages:", len(PdfReader(OUT).pages), "->", OUT)
