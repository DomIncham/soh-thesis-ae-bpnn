import os
import sys
import re
import base64
import subprocess
import io
import pypdf
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors

sys.stdout.reconfigure(encoding='utf-8')

WORKDIR = r"C:\Master Degree\Thesis\Autoencoder\nested_lobo"
MD_FILE = os.path.join(WORKDIR, "Progress_Report_Steps1-18.md")
HTML_FILE = os.path.join(WORKDIR, "Progress_Report_Steps1-18.html")
TEMP_PDF = os.path.join(WORKDIR, "temp_report.pdf")
FINAL_PDF = os.path.join(WORKDIR, "Progress_Report_Steps1-18.pdf")
FIGURES_DIR = os.path.join(WORKDIR, "figures")
EDGE_EXE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

print(f"Reading {MD_FILE}...")
with open(MD_FILE, 'r', encoding='utf-8') as f:
    md_content = f.read()

# Run pandoc to convert markdown to html fragment
res = subprocess.run(['pandoc', MD_FILE, '-f', 'markdown', '-t', 'html5'], capture_output=True, text=True, encoding='utf-8')
if res.returncode != 0:
    print("Pandoc error:", res.stderr)
    sys.exit(1)

body_html = res.stdout

# Base64 encode all images
def b64_img(rel_path):
    fn = os.path.basename(rel_path)
    full_path = os.path.join(FIGURES_DIR, fn)
    if os.path.exists(full_path):
        with open(full_path, "rb") as img_f:
            b64_data = base64.b64encode(img_f.read()).decode('utf-8')
            return f"data:image/png;base64,{b64_data}"
    else:
        print(f"Warning: Figure not found: {full_path}")
        return rel_path

# Process figure replacements with Card Components & Badges
figure_pattern = re.compile(
    r'<figure>\s*<img\s+src="([^"]+)"\s+alt="([^"]*)"\s*/>\s*<figcaption[^>]*>.*?</figcaption>\s*</figure>\s*<p><em>(.*?)</em></p>',
    re.DOTALL
)

def replace_figure(match):
    src = match.group(1)
    alt = match.group(2)
    caption = match.group(3).strip()
    data_uri = b64_img(src)
    
    fn = os.path.basename(src)
    if "R2_rmse_ranking" in fn:
        card_cls = "figure-card ranking-img"
    elif "A7_Raw_Nyquist" in fn:
        card_cls = "figure-card standard-img"
    else:
        card_cls = "figure-card full-width"
    
    # Extract figure tag e.g. "Figure R1" to make an UPPERCASE tag badge
    m_tag = re.match(r'^(Figure\s+[A-Za-z0-9]+)\.\s*(.*)', caption, re.DOTALL)
    if m_tag:
        tag_text = m_tag.group(1).upper()
        rest_caption = m_tag.group(2)
        caption_formatted = f'<span class="fig-tag">{tag_text}</span> {rest_caption}'
    else:
        caption_formatted = caption
    
    return f'''
<div class="{card_cls}">
  <img src="{data_uri}" alt="{alt}" />
  <div class="figure-caption">{caption_formatted}</div>
</div>
'''

body_html = figure_pattern.sub(replace_figure, body_html)

# Extract and format metadata block (matches with or without strong tags and handles newlines)
meta_pattern = re.compile(
    r'<p>(?:<strong>)?Date:(?:</strong>)?\s*(.*?)\s*(?:<strong>)?Data:(?:</strong>)?\s*(.*?)\s*(?:<strong>)?Protocol\s*\([^)]*\):(?:</strong>)?\s*(.*?)\s*(?:<strong>)?Leakage\s+controls\s*\([^)]*\):(?:</strong>)?\s*(.*?)</p>\s*<hr\s*/>',
    re.DOTALL
)

def replace_meta(match):
    date_val = match.group(1).strip()
    data_val = match.group(2).strip()
    protocol_val = match.group(3).strip()
    leakage_val = match.group(4).strip()
    
    return f'''
<div class="meta-card">
  <div class="meta-row"><span class="meta-label">Date:</span> <span class="meta-val">{date_val}</span></div>
  <div class="meta-row"><span class="meta-label">Data Source:</span> <span class="meta-val">{data_val}</span></div>
  <div class="meta-row"><span class="meta-label">Protocol (identically evaluated):</span> <span class="meta-val">{protocol_val}</span></div>
  <div class="meta-row"><span class="meta-label">Leakage Controls (every run):</span> <span class="meta-val">{leakage_val}</span></div>
</div>
'''

body_html = meta_pattern.sub(replace_meta, body_html)

# Fix colgroups for tables to make column widths proportional and clear
colgroups_replacement = [
    # Table 1: Section 1 (Status of 18 Steps)
    '<colgroup><col style="width: 8.5%;" /><col style="width: 23.5%;" /><col style="width: 50%;" /><col style="width: 18%;" /></colgroup>',
    # Table 2: Section 2b (Expanded AE metrics)
    '<colgroup><col style="width: 16%;" /><col style="width: 22%;" /><col style="width: 22%;" /><col style="width: 15%;" /><col style="width: 25%;" /></colgroup>',
    # Table 3: Section 2c (Ablations)
    '<colgroup><col style="width: 38%;" /><col style="width: 62%;" /></colgroup>',
    # Table 4: Section 5 (Artifacts)
    '<colgroup><col style="width: 34%;" /><col style="width: 66%;" /></colgroup>'
]

def replace_colgroups(html_text):
    idx = 0
    def sub_cg(m):
        nonlocal idx
        if idx < len(colgroups_replacement):
            res_cg = colgroups_replacement[idx]
            idx += 1
            return res_cg
        return m.group(0)
    return re.sub(r'<colgroup>.*?</colgroup>', sub_cg, html_text, flags=re.DOTALL)

body_html = replace_colgroups(body_html)

# Style B7 supporting evidence block
b7_support_pattern = re.compile(
    r'<p>(?:<strong>)?B7\s+supporting\s+evidence\s*\(added\):(?:</strong>)?\s*(.*?)</p>',
    re.DOTALL
)
def replace_b7(match):
    content = match.group(1).strip()
    return f'''<div class="callout-box info-box">
  <div class="callout-title">KEY FINDING / B7 SUPPORTING EVIDENCE</div>
  <p><strong>B7 supporting evidence (added):</strong> {content}</p>
</div>'''

body_html = b7_support_pattern.sub(replace_b7, body_html)

# Style Section 6 (Repository) cleanly into a highlighted repo card
repo_pattern = re.compile(
    r'(<h2\s+id="repository">6\.?\s*Repository</h2>\s*<p>.*?</p>\s*<p><a\s+href="https://github\.com/DomIncham/soh-thesis-ae-bpnn".*?</p>)',
    re.DOTALL
)
def replace_repo(match):
    content = match.group(1)
    return f'<div class="repo-card"><div class="repo-badge">SOURCE CODE & REPOSITORY</div>{content}</div>'

body_html = repo_pattern.sub(replace_repo, body_html)

# Strategic page breaks for a clean, professional 7-page academic layout:
# 1. Before Section 2 (Headline result) -> Page 3
body_html = body_html.replace(
    '<h2 id="headline-result-step-18-figure">',
    '<div class="page-break"></div>\n<h2 id="headline-result-step-18-figure">'
)

# 2. Before Section 2b (Steps 1–6 evidence, F1 & F2) -> Page 4
body_html = body_html.replace(
    '<h2 id="b.-steps-16-evidence-figures-reconstructed-from-verified-raw-data">',
    '<div class="page-break"></div>\n<h2 id="b.-steps-16-evidence-figures-reconstructed-from-verified-raw-data">'
)

# 3. Before Figure F3 & F4 -> Page 5
body_html = re.sub(
    r'(<div class="figure-card full-width">\s*<img[^>]*Step5_overshoot_worst_case)',
    r'<div class="page-break"></div>\n\1',
    body_html
)

# 4. Before Expanded AE metrics & Section 2c Ablations -> Page 6
body_html = body_html.replace(
    '<h3 id="expanded-ae-reconstruction-metrics-part-d3">',
    '<div class="page-break"></div>\n<h3 id="expanded-ae-reconstruction-metrics-part-d3">'
)

# 5. Before Section 3 (Advisor decision, limitations, artifacts, repo) -> Page 7
body_html = body_html.replace(
    '<h2 id="findings-for-the-advisors-decision-b7">',
    '<div class="page-break"></div>\n<h2 id="findings-for-the-advisors-decision-b7">'
)

# Custom CSS for high-quality academic report with ALL BORDERS tables
css = """
@page {
  size: A4 portrait;
  margin: 17mm 16mm 17mm 16mm;
}

@media print {
  body {
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }
}

* {
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  font-size: 10.6pt;
  line-height: 1.46;
  color: #1e293b;
  background-color: #ffffff;
  margin: 0;
  padding: 0;
}

.report-header {
  border-bottom: 2.5px solid #0f2a4a;
  padding-bottom: 6px;
  margin-bottom: 10px;
}

.report-top-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.report-subtitle {
  font-size: 8.8pt;
  text-transform: uppercase;
  letter-spacing: 0.09em;
  color: #1e3a5f;
  font-weight: 700;
}

.report-badge {
  font-size: 7.8pt;
  background-color: #0f2a4a;
  color: #ffffff;
  padding: 2px 7px;
  border-radius: 3px;
  font-weight: 600;
  letter-spacing: 0.04em;
}

h1 {
  font-size: 13.8pt;
  font-weight: 800;
  color: #0f2a4a;
  line-height: 1.32;
  margin: 0;
}

h2 {
  font-size: 12pt;
  font-weight: 700;
  color: #1e3a5f;
  line-height: 1.28;
  margin-top: 12px;
  margin-bottom: 6px;
  padding-bottom: 3px;
  border-bottom: 1.5px solid #cbd5e1;
  page-break-after: avoid;
  break-after: avoid;
}

h3 {
  font-size: 11pt;
  font-weight: 700;
  color: #334155;
  line-height: 1.28;
  margin-top: 10px;
  margin-bottom: 5px;
  page-break-after: avoid;
  break-after: avoid;
}

p {
  margin-top: 0;
  margin-bottom: 6px;
  text-align: justify;
}

ul, ol {
  margin-top: 0;
  margin-bottom: 7px;
  padding-left: 20px;
}

li {
  margin-bottom: 3px;
  text-align: justify;
}

a {
  color: #1d4ed8;
  text-decoration: underline;
  text-underline-offset: 2px;
  text-decoration-color: #93c5fd;
}

a:hover {
  color: #1e40af;
  text-decoration-color: #1d4ed8;
}

.meta-card {
  background-color: #f8fafc;
  border: 1.2px solid #cbd5e1;
  border-left: 4.5px solid #0f2a4a;
  border-radius: 5px;
  padding: 8px 12px;
  margin-bottom: 11px;
  font-size: 9.3pt;
  line-height: 1.42;
  page-break-inside: avoid;
  break-inside: avoid;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
}

.meta-row {
  margin-bottom: 4px;
}

.meta-row:last-child {
  margin-bottom: 0;
}

.meta-label {
  font-weight: 700;
  color: #0f2a4a;
}

.meta-val {
  color: #334155;
}

/* ========================================================
   TABLES WITH ALL BORDERS (GRID STYLE AS REQUESTED)
   ======================================================== */
table {
  width: 100%;
  table-layout: fixed;
  border-collapse: collapse;
  margin: 7px 0 10px 0;
  font-size: 8.8pt;
  line-height: 1.34;
  page-break-inside: auto;
  break-inside: auto;
  border: 1.5px solid #475569; /* Outer table border: 1.5px solid #475569 */
}

thead {
  display: table-header-group;
}

th {
  background-color: #e2e8f0;
  color: #0f2a4a;
  font-weight: 700;
  text-align: left;
  padding: 5px 7px;
  border: 1px solid #cbd5e1; /* ALL borders for th: 1px solid #cbd5e1 */
  border-bottom: 2px solid #0f2a4a; /* Blue header bottom border: 2px solid #0f2a4a */
}

td {
  padding: 4px 7px;
  border: 1px solid #cbd5e1; /* ALL borders for td: horizontal & vertical 1px solid #cbd5e1 */
  vertical-align: top;
  word-wrap: break-word;
}

/* Row alternating fills: #ffffff / #f8fafc */
tr:nth-child(even) td {
  background-color: #f8fafc;
}

tr:nth-child(odd) td {
  background-color: #ffffff;
}

tr {
  page-break-inside: avoid;
  break-inside: avoid;
}

/* Center first column in Status table */
table tbody tr td:first-child {
  text-align: center;
  font-weight: 600;
}

code {
  font-family: Consolas, "Courier New", monospace;
  font-size: 8.2pt;
  background-color: #f1f5f9;
  color: #0f2a4a;
  padding: 1px 3px;
  border-radius: 3px;
  border: 1px solid #cbd5e1;
  word-break: break-all;
}

a code {
  color: #1d4ed8;
  background-color: #eff6ff;
  border-color: #bfdbfe;
  text-decoration: underline;
  text-underline-offset: 1.5px;
  text-decoration-color: #93c5fd;
}

.figure-card {
  margin: 10px auto 12px auto;
  padding: 6px;
  background-color: #ffffff;
  border: 1.2px solid #cbd5e1;
  border-radius: 5px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  page-break-inside: avoid;
  break-inside: avoid;
  text-align: center;
}

.figure-card img {
  display: block;
  margin: 0 auto;
  border: 1px solid #e2e8f0;
  border-radius: 3px;
}

.figure-card.full-width img {
  width: 100%;
  max-width: 100%;
}

.figure-card.standard-img img {
  width: 88%;
  max-width: 88%;
}

.figure-card.ranking-img img {
  width: 80%;
  max-width: 80%;
}

.figure-caption {
  font-size: 9pt;
  color: #334155;
  margin-top: 6px;
  text-align: justify;
  line-height: 1.36;
  padding: 0 4px;
}

.fig-tag {
  display: inline-block;
  background-color: #0f2a4a;
  color: #ffffff;
  font-weight: 700;
  font-size: 7.6pt;
  padding: 1px 5px;
  border-radius: 3px;
  margin-right: 5px;
  letter-spacing: 0.04em;
  vertical-align: baseline;
}

.callout-box {
  background-color: #f0fdf4;
  border: 1.2px solid #86efac;
  border-left: 4.5px solid #16a34a;
  border-radius: 5px;
  padding: 7px 11px;
  margin: 9px 0;
  font-size: 9.4pt;
  line-height: 1.42;
  page-break-inside: avoid;
  break-inside: avoid;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
}

.callout-title {
  font-size: 8pt;
  font-weight: 800;
  color: #166534;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  margin-bottom: 3px;
}

.callout-box p {
  margin: 0;
}

.repo-card {
  background-color: #f8fafc;
  border: 1.2px solid #93c5fd;
  border-left: 4.5px solid #1d4ed8;
  border-radius: 5px;
  padding: 7px 11px;
  margin-top: 8px;
  page-break-inside: avoid;
  break-inside: avoid;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
}

.repo-badge {
  font-size: 7.6pt;
  font-weight: 800;
  color: #1e40af;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  margin-bottom: 3px;
}

.repo-card h2 {
  margin-top: 0;
  margin-bottom: 4px;
  padding-bottom: 2px;
  border-bottom: 1px solid #bfdbfe;
  font-size: 11pt;
  color: #1e3a5f;
}

.repo-card p {
  margin-bottom: 3px;
}

.repo-card p:last-child {
  margin-bottom: 0;
}

.page-break {
  page-break-after: always;
  break-after: page;
}
"""

# Clean up title heading into report header with Institutional subtitle & Badge
body_html = re.sub(
    r'<h1[^>]*>(.*?)</h1>',
    r'<div class="report-header">'
    r'<div class="report-top-meta">'
    r'<div class="report-subtitle">National Taiwan University of Science and Technology • Master\'s Thesis</div>'
    r'<div class="report-badge">Round 2 — All 18 Steps</div>'
    r'</div>'
    r'<h1>\1</h1>'
    r'</div>',
    body_html,
    count=1
)

full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Progress Report — Round 2</title>
<style>
{css}
</style>
</head>
<body>
{body_html}
</body>
</html>
"""

print(f"Writing {HTML_FILE}...")
with open(HTML_FILE, 'w', encoding='utf-8') as f:
    f.write(full_html)

print("Compiling PDF via Microsoft Edge headless...")
cmd = [
    EDGE_EXE,
    '--headless=new',
    '--disable-gpu',
    '--no-first-run',
    '--no-default-browser-check',
    '--no-pdf-header-footer',
    f'--print-to-pdf={TEMP_PDF}',
    HTML_FILE
]
res = subprocess.run(cmd, capture_output=True, text=True)
if res.returncode != 0 or not os.path.exists(TEMP_PDF):
    print("Edge error:", res.stderr)
    sys.exit(1)

print(f"Edge PDF generated: {os.path.getsize(TEMP_PDF)} bytes")

# Stamp running headers, footers and page numbers via ReportLab Canvas
print("Stamping running headers, footers, and canvas elements...")
reader = pypdf.PdfReader(TEMP_PDF)
total_pages = len(reader.pages)
print(f"Total pages: {total_pages}")

writer = pypdf.PdfWriter()

for page_idx in range(total_pages):
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=A4)
    width, height = A4
    page_num = page_idx + 1
    
    # 1. Top Decorative Accent Stripe (All Pages)
    can.setFillColor(colors.HexColor('#0f2a4a'))
    can.rect(0, height - 3.5, width, 3.5, fill=1, stroke=0)
    can.setFillColor(colors.HexColor('#2563eb'))
    can.rect(0, height - 5.5, width, 2, fill=1, stroke=0)
    
    # 2. Running Header (Pages 2+)
    if page_num > 1:
        # Document title / subject
        can.setFont('Helvetica-Bold', 7.5)
        can.setFillColor(colors.HexColor('#0f2a4a'))
        can.drawString(45, height - 25, "MASTER'S THESIS PROGRESS REPORT • ROUND 2")
        
        can.setFont('Helvetica', 7.5)
        can.setFillColor(colors.HexColor('#64748b'))
        can.drawString(255, height - 25, "|   EIS Verification → LOBO Comparison → Time-Domain")
        
        # Date badge pill on right
        can.setFillColor(colors.HexColor('#f1f5f9'))
        can.setStrokeColor(colors.HexColor('#cbd5e1'))
        can.setLineWidth(0.6)
        can.roundRect(width - 105, height - 30, 60, 13, 3, fill=1, stroke=1)
        
        can.setFont('Helvetica-Bold', 7)
        can.setFillColor(colors.HexColor('#334155'))
        can.drawCentredString(width - 75, height - 26.5, "2026-09-25")
        
        # Dual-tone divider line
        can.setStrokeColor(colors.HexColor('#e2e8f0'))
        can.setLineWidth(0.6)
        can.line(45, height - 35, width - 45, height - 35)
        
        can.setStrokeColor(colors.HexColor('#0f2a4a'))
        can.setLineWidth(1.2)
        can.line(45, height - 35, 175, height - 35)
    
    # 3. Running Footer (All Pages)
    # Dual-tone footer line
    can.setStrokeColor(colors.HexColor('#e2e8f0'))
    can.setLineWidth(0.6)
    can.line(45, 32, width - 45, 32)
    
    can.setStrokeColor(colors.HexColor('#2563eb'))
    can.setLineWidth(1.2)
    can.line(45, 32, 125, 32)
    
    # Left subtitle
    can.setFont('Helvetica', 7.8)
    can.setFillColor(colors.HexColor('#475569'))
    can.drawString(45, 19, "Thesis: SOH Estimation via Two-Stage Autoencoder & BPNN (NASA Battery Aging)")
    
    # Right page badge pill
    can.setFillColor(colors.HexColor('#f8fafc'))
    can.setStrokeColor(colors.HexColor('#cbd5e1'))
    can.setLineWidth(0.6)
    can.roundRect(width - 105, 14, 60, 14, 7, fill=1, stroke=1)
    
    can.setFont('Helvetica-Bold', 7.5)
    can.setFillColor(colors.HexColor('#0f2a4a'))
    can.drawCentredString(width - 75, 18.5, f"Page {page_num} of {total_pages}")
    
    can.save()
    packet.seek(0)
    
    overlay = pypdf.PdfReader(packet)
    page = reader.pages[page_idx]
    page.merge_page(overlay.pages[0])
    writer.add_page(page)

with open(FINAL_PDF, 'wb') as f:
    writer.write(f)

if os.path.exists(TEMP_PDF):
    os.remove(TEMP_PDF)

print(f"Successfully created: {FINAL_PDF}")
print(f"Final file size: {os.path.getsize(FINAL_PDF)} bytes across {total_pages} pages.")
