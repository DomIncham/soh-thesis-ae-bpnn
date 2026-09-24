# Convert Progress_Report_Steps1-18.md -> styled advisor PDF (reportlab platypus)
# Design: A4, DejaVu fonts (full unicode arrows/math), navy headings, styled tables, embedded figures, page footer.
import os, re
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                Image, KeepTogether, HRFlowable)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER

HERE = os.path.dirname(os.path.abspath(__file__))
MD = os.path.join(HERE, "Progress_Report_Steps1-18.md")
OUT = os.path.join(HERE, "Progress_Report_Steps1-18.pdf")
FIG = os.path.join(HERE, "figures")

FONTDIR = os.path.join(__import__("matplotlib").get_data_path(), "fonts", "ttf")
pdfmetrics.registerFont(TTFont("DejaVu", os.path.join(FONTDIR, "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("DejaVu-Bold", os.path.join(FONTDIR, "DejaVuSans-Bold.ttf")))
pdfmetrics.registerFont(TTFont("DejaVu-Italic", os.path.join(FONTDIR, "DejaVuSans-Oblique.ttf")))
pdfmetrics.registerFont(TTFont("DejaVu-Mono", os.path.join(FONTDIR, "DejaVuSansMono.ttf")))
registerFontFamily("DejaVu", normal="DejaVu", bold="DejaVu-Bold", italic="DejaVu-Italic")

NAVY = colors.HexColor("#1F3B60")
ACCENT = colors.HexColor("#2E5E8C")
LIGHT = colors.HexColor("#E9EEF5")
GRAY = colors.HexColor("#444444")

S = {
    "title": ParagraphStyle("title", fontName="DejaVu-Bold", fontSize=16, leading=20, textColor=NAVY, spaceAfter=6),
    "meta": ParagraphStyle("meta", fontName="DejaVu", fontSize=9, leading=13, textColor=colors.HexColor("#333333")),
    "h1": ParagraphStyle("h1", fontName="DejaVu-Bold", fontSize=12.5, leading=16, textColor=colors.white,
                          backColor=ACCENT, borderPadding=(3, 6, 3, 6), spaceBefore=14, spaceAfter=8),
    "h2": ParagraphStyle("h2", fontName="DejaVu-Bold", fontSize=10.5, leading=14, textColor=NAVY, spaceBefore=8, spaceAfter=4),
    "body": ParagraphStyle("body", fontName="DejaVu", fontSize=9, leading=13, spaceAfter=5),
    "bullet": ParagraphStyle("bullet", fontName="DejaVu", fontSize=9, leading=13, leftIndent=14, spaceAfter=3),
    "caption": ParagraphStyle("caption", fontName="DejaVu-Italic", fontSize=8, leading=11,
                               textColor=colors.HexColor("#555555"), spaceBefore=2, spaceAfter=8),
    "cell": ParagraphStyle("cell", fontName="DejaVu", fontSize=7.6, leading=10),
    "cellh": ParagraphStyle("cellh", fontName="DejaVu-Bold", fontSize=8, leading=10.5, textColor=colors.white),
    "quote": ParagraphStyle("quote", fontName="DejaVu-Italic", fontSize=8.5, leading=12,
                             leftIndent=14, textColor=colors.HexColor("#444555"), spaceAfter=5),
}

def esc(t): return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def inline(t, in_cell=False):
    t = esc(t)
    t = t.replace("\\|", "§PIPE§")
    t = __import__("re").sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    if not in_cell:
        t = __import__("re").sub(r"`([^`]*)`", r'<font face="DejaVu-Mono" size="7.6" color="#204060">\1</font>', t)
    else:
        t = t.replace("`", "")
    t = t.replace("§PIPE§", "|")
    return t

def make_table(rows, usable):
    header = rows[0]
    data = [[Paragraph(inline(c, True), S["cellh"]) for c in header]]
    for r in rows[1:]:
        data.append([Paragraph(inline(c, True), S["cell"]) for c in r] + [Paragraph("", S["cell"])] * (len(header) - len(r)))
    lens = [max((len(c) for c in col), default=5) for col in zip(*rows)]
    lens = [max(x, 6) for x in lens]
    total = sum(lens)
    minw = 1.3 * cm
    extra = max(usable - minw * len(lens), 0)
    widths = [minw + extra * (x / total) for x in lens]
    # long-text tables: give more room to the widest columns, cap the first narrow col
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#B9C6D8")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F6FA")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t

def split_row(line):
    line = line.strip()
    if line.startswith("|"): line = line[1:]
    if line.endswith("|"): line = line[:-1]
    return [c.strip() for c in line.split("|")]

def build():
    usable = A4[0] - 3.6 * cm
    md = open(MD, encoding="utf-8").read().splitlines()
    story, i = [], 0
    # cover header band
    title = md[0].lstrip("# ").strip()
    band = Table([[Paragraph("SOH Estimation of Li-ion Batteries<br/>Round 2 Progress Report — Steps 1–18", 
                   ParagraphStyle("ct", fontName="DejaVu-Bold", fontSize=14, leading=18, textColor=colors.white))]],
                 colWidths=[usable])
    band.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), NAVY),
                              ("LEFTPADDING", (0, 0), (-1, -1), 10), ("TOPPADDING", (0, 0), (-1, -1), 10),
                              ("BOTTOMPADDING", (0, 0), (-1, -1), 10)]))
    story.append(band); story.append(Spacer(1, 8))
    while i < len(md):
        line = md[i].rstrip()
        if not line or line.startswith("# "):
            i += 1; continue
        if line == "---":
            story.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#B9C4D4"), spaceAfter=6))
            i += 1; continue
        if line.startswith("## "):
            story.append(Paragraph(inline(line[3:]), S["h1"])); i += 1; continue
        if line.startswith("### "):
            story.append(Paragraph(inline(line[4:]), S["h2"])); i += 1; continue
        if line.startswith("!["):
            alt = line[2:line.index("](")]
            path = line[line.index("](") + 2:line.rindex(")")]
            p = os.path.join(os.path.dirname(MD), path.replace("/", os.sep))
            if os.path.exists(p):
                from PIL import Image as PILImage
                w, h = __import__("PIL.Image", fromlist=["open"]).open(p).size
                img = Image(p, width=usable, height=usable * h / w)
                story.append(img)
            i += 1; continue
        if line.startswith("*") and line.endswith("*") and not line.startswith("**"):
            story.append(Paragraph(inline(line[1:-1]), ParagraphStyle(
                "cap", fontName="DejaVu-Italic", fontSize=8, leading=11,
                textColor=colors.HexColor("#555555"), spaceAfter=6))); i += 1; continue
        if line.startswith("|"):
            trows = []
            while i < len(md) and md[i].startswith("|"):
                r = split_row(md[i])
                if not all(set(c) <= set("-: ") for c in r):
                    trows.append(r)
                i += 1
            story.append(make_table(trows, usable)); story.append(Spacer(1, 6)); continue
        if line.startswith("- "):
            story.append(Paragraph(inline(line[2:]), ParagraphStyle(
                "b", fontName="DejaVu", fontSize=9, leading=13, leftIndent=14, bulletIndent=4, spaceAfter=3),
                bulletText="•")); i += 1; continue
        if line.startswith("> "):
            story.append(Paragraph(inline(line[2:]), ParagraphStyle(
                "q", fontName="DejaVu-Italic", fontSize=8.5, leading=12, leftIndent=14,
                textColor=colors.HexColor("#445066"), spaceAfter=5))); i += 1; continue
        if line.startswith("**") and ":" in line:
            story.append(Paragraph(inline(line), S["meta"])); i += 1; continue
        story.append(Paragraph(inline(line), S["body"])); i += 1

    def footer(canv, doc):
        canv.saveState()
        canv.setFont("DejaVu", 7.5); canv.setFillColor(GRAY)
        canv.drawString(2 * cm, 1.1 * cm, "Dom Padipat Aincham · NTUST — SOH via Two-Stage AE+BPNN")
        canv.drawRightString(A4[0] - 2 * cm, 1.1 * cm, f"page {doc.page}")
        canv.restoreState()

    doc = SimpleDocTemplate(OUT, pagesize=A4, leftMargin=1.8 * cm, rightMargin=1.8 * cm,
                            topMargin=1.6 * cm, bottomMargin=1.8 * cm,
                            title="Round 2 Progress Report — Steps 1-18",
                            author="Dom Padipat Aincham")
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print("saved:", OUT, os.path.getsize(OUT), "bytes")

if __name__ == "__main__":
    build()