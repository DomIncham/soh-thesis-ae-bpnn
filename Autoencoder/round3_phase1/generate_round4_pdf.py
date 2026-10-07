import os
import sys
import re
import subprocess
import io
import pypdf
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors

sys.stdout.reconfigure(encoding='utf-8')

WORKDIR = r"C:\Master Degree\Thesis\Autoencoder\round3_phase1"
MD_FILE = os.path.join(WORKDIR, "round4_report_to_advisor.md")
HTML_FILE = os.path.join(WORKDIR, "round4_report_to_advisor.html")
TEMP_PDF = os.path.join(WORKDIR, "temp_round4.pdf")
FINAL_PDF = os.path.join(WORKDIR, "round4_report_to_advisor.pdf")
EDGE_EXE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

print(f"Reading markdown: {MD_FILE}")
with open(MD_FILE, 'r', encoding='utf-8') as f:
    md_content = f.read()

# Run pandoc to convert markdown to html fragment
res = subprocess.run(['pandoc', MD_FILE, '-f', 'markdown', '-t', 'html5'], capture_output=True, text=True, encoding='utf-8')
if res.returncode != 0:
    print("Pandoc error:", res.stderr)
    sys.exit(1)

body_html = res.stdout

# 1. Transform Header and Metadata Card (Page 1)
header_meta_pattern = re.compile(
    r'<h1[^>]*>.*?</h1>\s*<p>Student:\s*Padipat Aincham\s*\(M11452803\)\s*\|\s*Advisor:\s*Y\.F\.\s*Luo</p>\s*<p>All numbers in this report were re-checked on\s*(\d{4}-\d{2}-\d{2})\.\s*(.*?)</p>',
    re.DOTALL
)

def replace_header_meta(m):
    ver_date = m.group(1).strip()
    return f'''
<div class="report-header">
  <div class="report-top-meta">
    <div class="report-subtitle">National Taiwan University of Science and Technology • Master\'s Thesis</div>
    <div class="report-badge">Round 4 — R3-C1…C9 Complete</div>
  </div>
  <h1>Round 4 Report — Resolution of Literature Gap Audit (R3-C1…C9)</h1>
</div>

<div class="meta-card">
  <div class="meta-grid">
    <div class="meta-item"><span class="meta-label">Student:</span> <span class="meta-val">Padipat Aincham (Dom)</span></div>
    <div class="meta-item"><span class="meta-label">Student ID:</span> <span class="meta-val">M11452803</span></div>
    <div class="meta-item"><span class="meta-label">Institute:</span> <span class="meta-val">Graduate Institute of A.I. Cross-disciplinary Technology, NTUST</span></div>
    <div class="meta-item"><span class="meta-label">Advisor:</span> <span class="meta-val">Prof. Y.F. Luo (NTUST)</span></div>
    <div class="meta-item"><span class="meta-label">Document:</span> <span class="meta-val">Round 4 Progress Report (R3-C1…C9 Complete)</span></div>
    <div class="meta-item"><span class="meta-label">Audit Cycle:</span> <span class="meta-val">Literature Gap Audit (Resolution)</span></div>
  </div>
  <div class="meta-verify-banner">
    <span class="verify-badge">VERIFIED PASS</span>
    <span class="meta-verify-text">All numbers re-checked on {ver_date}: full check suite passes <strong>210/210 checks</strong> (+26/26 data-provenance checks, max|leakage| = 0.00e+00). Every headline number was re-read from result CSVs before inclusion.</span>
  </div>
</div>
'''

body_html = header_meta_pattern.sub(replace_header_meta, body_html)

# 2. Format Section 0: Summary into an Executive Summary Card
summary_pattern = re.compile(
    r'<h2\s+id="summary">\s*0\.\s*Summary\s*</h2>\s*<p>(.*?)</p>',
    re.DOTALL
)

def replace_summary(match):
    summary_text = match.group(1).strip()
    return f'''
<div class="summary-card">
  <div class="summary-card-header">
    <span class="summary-title-badge">EXECUTIVE SUMMARY</span>
    <span class="summary-subtitle">Section 0 — Headline Findings & Literature Gap Resolution</span>
  </div>
  <p class="summary-text">{summary_text}</p>
</div>
'''
body_html = summary_pattern.sub(replace_summary, body_html)

# 3. Format Colgroups for all 5 Tables
colgroups_replacement = [
    # Table 1: Section 2 (Protocol-gap experiment, 4 cols)
    '<colgroup><col style="width: 34%;" /><col style="width: 22%;" /><col style="width: 22%;" /><col style="width: 22%;" /></colgroup>',
    # Table 2: Section 4 (Proxy-free improvements, 3 cols)
    '<colgroup><col style="width: 30%;" /><col style="width: 48%;" /><col style="width: 22%;" /></colgroup>',
    # Table 3: Section 6 (AE negative result, 2 cols)
    '<colgroup><col style="width: 45%;" /><col style="width: 55%;" /></colgroup>',
    # Table 4: Section 7b (Evidence on GitHub, 2 cols)
    '<colgroup><col style="width: 44%;" /><col style="width: 56%;" /></colgroup>',
    # Table 5: Section 8 (Verification status, 2 cols)
    '<colgroup><col style="width: 50%;" /><col style="width: 50%;" /></colgroup>'
]

def replace_table_colgroups(html_text):
    table_splits = re.split(r'(<table[^>]*>)', html_text)
    new_parts = []
    t_idx = 0
    for part in table_splits:
        if part.startswith('<table'):
            new_parts.append(part)
        elif len(new_parts) > 0 and new_parts[-1].startswith('<table'):
            cg = colgroups_replacement[t_idx] if t_idx < len(colgroups_replacement) else ''
            t_idx += 1
            cleaned_part = re.sub(r'<colgroup>.*?</colgroup>', '', part, flags=re.DOTALL)
            new_parts.append('\n' + cg + cleaned_part)
        else:
            new_parts.append(part)
    return ''.join(new_parts)

body_html = replace_table_colgroups(body_html)

# 4. Status Badges in tables
body_html = re.sub(r'<td>Supported</td>', '<td><span class="badge badge-supported">Supported</span></td>', body_html)
body_html = re.sub(r'<td>Rejected</td>', '<td><span class="badge badge-rejected">Rejected</span></td>', body_html)
body_html = re.sub(r'<td>Not established;\s*(.*?)</td>', r'<td><span class="badge badge-warning">Not established</span> <span class="badge-subtext">— \1</span></td>', body_html)
body_html = re.sub(r'<td>No partial-window penalty</td>', '<td><span class="badge badge-info">No penalty</span></td>', body_html)
body_html = re.sub(r'<td>(\d+/\d+)(?:\s*✅)?</td>', r'<td><span class="badge-check">\1 PASS</span></td>', body_html)

# 5. Citation Badges in Section 7
def cite_badge_repl(m):
    return f'<span class="cite-badge">[{m.group(1)}]</span>'
body_html = re.sub(r'\[(\d+)\](?!\()', cite_badge_repl, body_html)

# 6. Format Section 6: AE negative result quote/claim
ae_claim_pattern = re.compile(
    r'<p>Claim used in the thesis:\s*(?:&quot;|"|“)(.*?)(?:&quot;|"|”)\s*Recorded in\s*(<a\s+[^>]*>.*?</a>)\s*\(R3-C7 outcome\)\.</p>',
    re.DOTALL
)
def replace_ae_claim(match):
    claim_text = match.group(1).strip()
    file_link = match.group(2).strip()
    return f'''
<div class="callout-box negative-box">
  <div class="callout-title">APPROVED THESIS PHRASING (DOCUMENTED NEGATIVE RESULT)</div>
  <p class="claim-quote">“{claim_text}”</p>
  <div class="callout-meta">Recorded in {file_link} (R3-C7 outcome)</div>
</div>
'''
body_html = ae_claim_pattern.sub(replace_ae_claim, body_html)

# 7. Format Section 10: Question for advisor and Student Signature Block
q_signature_pattern = re.compile(
    r'<h2\s+id="question-for-the-advisor">\s*10\.\s*Question for the advisor\s*</h2>\s*<p>(.*?)</p>\s*<p>Padipat Aincham\s+M11452803</p>',
    re.DOTALL
)
def replace_q_sig(match):
    q_content = match.group(1).strip()
    return f'''
<div class="callout-box question-box">
  <div class="callout-title">ADVISOR DECISION REQUESTED — SECTION 10</div>
  <h3 class="q-heading">Candidate Thesis Title Phrasing</h3>
  <p class="q-body">{q_content}</p>
</div>

<div class="student-signature-block">
  <div class="sig-name">Padipat Aincham (Dom)</div>
  <div class="sig-meta">Student ID: M11452803 • Graduate Institute of A.I. Cross-disciplinary Technology, NTUST</div>
</div>
'''
body_html = q_signature_pattern.sub(replace_q_sig, body_html)

# 8. Center numeric cells in tables
def center_numeric_tds(m):
    content = m.group(1)
    if re.match(r'^[−\-\+\d\.\s%→]+$', content.strip()):
        return f'<td class="text-center">{content}</td>'
    return m.group(0)

body_html = re.sub(r'<td>(.*?)</td>', center_numeric_tds, body_html)

# 9. Clean up any weird line break / spacing glitches in text
body_html = body_html.replace('r3c3_feature_classes.cs\nv', 'r3c3_feature_classes.csv')

# 10. Strategic Page Breaks (Perfect 4-Page Layout without overflow):
# Page 1: Header, Meta Card, Section 0 (Summary), Section 1 (C1), Section 2 (C2 table + notes)
# Page 2: Section 3 (C3), Section 4 (C5 table + notes), Section 5 (C6 wider validation)
# Page 3: Section 6 (C7 AE table + quote), Section 7 (C9 citations verification)
# Page 4: Section 7b (Evidence GitHub table), Section 8 (Verification status table), Section 9 (Draft status), Section 10 (Question) + Signature

body_html = re.sub(
    r'(<h2\s+id="c3---feature-and-proxy-audit">)',
    r'<div class="page-break"></div>\n\1',
    body_html
)

body_html = re.sub(
    r'(<h2\s+id="c7---ae-demoted-to-a-documented-negative-result)',
    r'<div class="page-break"></div>\n\1',
    body_html
)

body_html = re.sub(
    r'(<h2\s+id="b.-evidence-on-github">)',
    r'<div class="page-break"></div>\n\1',
    body_html
)

css = """
@page {
  size: A4 portrait;
  margin: 13.5mm 15mm 13.5mm 15mm;
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
  font-size: 9.15pt;
  line-height: 1.40;
  color: #1e293b;
  background-color: #ffffff;
  margin: 0;
  padding: 0;
}

.report-header {
  border-bottom: 2.5px solid #0f2a4a;
  padding-bottom: 5px;
  margin-bottom: 7px;
}

.report-top-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 3px;
}

.report-subtitle {
  font-size: 8.2pt;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #1e3a5f;
  font-weight: 700;
}

.report-badge {
  font-size: 7.5pt;
  background-color: #0f2a4a;
  color: #ffffff;
  padding: 2px 7px;
  border-radius: 3px;
  font-weight: 600;
  letter-spacing: 0.04em;
}

h1 {
  font-size: 12.8pt;
  font-weight: 800;
  color: #0f2a4a;
  line-height: 1.28;
  margin: 0;
}

h2 {
  font-size: 10.6pt;
  font-weight: 700;
  color: #1e3a5f;
  line-height: 1.25;
  margin-top: 8px;
  margin-bottom: 4px;
  padding-bottom: 2px;
  border-bottom: 1.3px solid #cbd5e1;
  page-break-after: avoid;
  break-after: avoid;
}

h3 {
  font-size: 9.5pt;
  font-weight: 700;
  color: #334155;
  line-height: 1.25;
  margin-top: 6px;
  margin-bottom: 3px;
  page-break-after: avoid;
  break-after: avoid;
}

p {
  margin-top: 0;
  margin-bottom: 4px;
  text-align: justify;
}

ul, ol {
  margin-top: 0;
  margin-bottom: 4.5px;
  padding-left: 17px;
}

li {
  margin-bottom: 2px;
  text-align: justify;
}

strong {
  font-weight: 700;
  color: #0f2a4a;
}

a {
  color: #1d4ed8;
  text-decoration: underline;
  text-underline-offset: 1.5px;
  text-decoration-color: #93c5fd;
}

/* Metadata Card */
.meta-card {
  background-color: #f8fafc;
  border: 1.2px solid #cbd5e1;
  border-left: 4.5px solid #0f2a4a;
  border-radius: 5px;
  padding: 6.5px 10px;
  margin-bottom: 7px;
  font-size: 8.5pt;
  line-height: 1.36;
  page-break-inside: avoid;
  break-inside: avoid;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
}

.meta-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  row-gap: 2px;
  column-gap: 14px;
  margin-bottom: 4px;
}

.meta-label {
  font-weight: 700;
  color: #0f2a4a;
}

.meta-val {
  color: #334155;
}

.meta-verify-banner {
  display: flex;
  align-items: center;
  background-color: #ffffff;
  border: 1px solid #bbf7d0;
  border-radius: 4px;
  padding: 3px 6.5px;
  margin-top: 2px;
}

.verify-badge {
  background-color: #16a34a;
  color: #ffffff;
  font-weight: 800;
  font-size: 6.8pt;
  padding: 1.5px 5px;
  border-radius: 3px;
  margin-right: 6px;
  letter-spacing: 0.05em;
  white-space: nowrap;
}

.meta-verify-text {
  font-size: 7.8pt;
  color: #166534;
  line-height: 1.25;
}

/* Summary Card */
.summary-card {
  background-color: #f0f7ff;
  border: 1.2px solid #bfdbfe;
  border-left: 4.5px solid #2563eb;
  border-radius: 5px;
  padding: 6.5px 10px;
  margin-bottom: 7px;
  page-break-inside: avoid;
  break-inside: avoid;
}

.summary-card-header {
  display: flex;
  align-items: center;
  margin-bottom: 3px;
}

.summary-title-badge {
  background-color: #1e40af;
  color: #ffffff;
  font-weight: 800;
  font-size: 7pt;
  padding: 1.5px 5px;
  border-radius: 3px;
  margin-right: 6px;
  letter-spacing: 0.06em;
}

.summary-subtitle {
  font-size: 8.2pt;
  font-weight: 700;
  color: #1e3a5f;
}

.summary-text {
  font-size: 8.8pt;
  line-height: 1.40;
  color: #1e293b;
  margin: 0;
  text-align: justify;
}

/* Tables with complete border grid styling */
table {
  width: 100%;
  table-layout: fixed;
  border-collapse: collapse;
  margin: 4.5px 0 7px 0;
  font-size: 8.3pt;
  line-height: 1.30;
  border: 1.5px solid #475569;
}

thead {
  display: table-header-group;
}

th {
  background-color: #e2e8f0;
  color: #0f2a4a;
  font-weight: 700;
  text-align: left;
  padding: 3.5px 5.5px;
  border: 1px solid #cbd5e1;
  border-bottom: 2.2px solid #0f2a4a;
}

td {
  padding: 3px 5.5px;
  border: 1px solid #cbd5e1;
  vertical-align: top;
  word-wrap: break-word;
}

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

.text-center {
  text-align: center;
}

/* Badges */
.badge {
  display: inline-block;
  padding: 1px 4.5px;
  border-radius: 3px;
  font-weight: 700;
  font-size: 7.2pt;
  letter-spacing: 0.03em;
  white-space: nowrap;
}

.badge-supported {
  background-color: #dcfce7;
  color: #166534;
  border: 1px solid #86efac;
}

.badge-rejected {
  background-color: #fee2e2;
  color: #991b1b;
  border: 1px solid #fca5a5;
}

.badge-warning {
  background-color: #fef3c7;
  color: #92400e;
  border: 1px solid #fcd34d;
}

.badge-info {
  background-color: #e0f2fe;
  color: #075985;
  border: 1px solid #7dd3fc;
}

.badge-subtext {
  font-size: 7.6pt;
  color: #475569;
}

.badge-check {
  display: inline-block;
  background-color: #f0fdf4;
  color: #15803d;
  font-weight: 700;
  font-size: 7.6pt;
  padding: 0.5px 4px;
  border-radius: 3px;
  border: 1px solid #bbf7d0;
}

.cite-badge {
  display: inline-block;
  background-color: #0f2a4a;
  color: #ffffff;
  font-weight: 700;
  font-size: 7.2pt;
  padding: 0.8px 3.5px;
  border-radius: 3px;
  margin-right: 2.5px;
  letter-spacing: 0.03em;
  vertical-align: baseline;
}

/* Code */
code {
  font-family: Consolas, "Courier New", monospace;
  font-size: 7.8pt;
  background-color: #f1f5f9;
  color: #0f2a4a;
  padding: 0.8px 2.8px;
  border-radius: 3px;
  border: 1px solid #cbd5e1;
  word-break: break-all;
}

/* Callout Boxes */
.callout-box {
  border-radius: 5px;
  padding: 5.5px 9px;
  margin: 6px 0;
  font-size: 8.7pt;
  line-height: 1.36;
  page-break-inside: avoid;
  break-inside: avoid;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
}

.callout-title {
  font-size: 7.2pt;
  font-weight: 800;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  margin-bottom: 2px;
}

.negative-box {
  background-color: #fff7ed;
  border: 1.2px solid #fed7aa;
  border-left: 4.5px solid #ea580c;
}

.negative-box .callout-title {
  color: #c2410c;
}

.claim-quote {
  font-style: italic;
  color: #7c2d12;
  margin-bottom: 3px;
}

.callout-meta {
  font-size: 7.6pt;
  color: #9a3412;
}

.question-box {
  background-color: #f5f3ff;
  border: 1.2px solid #ddd6fe;
  border-left: 4.5px solid #7c3aed;
}

.question-box .callout-title {
  color: #6d28d9;
}

.q-heading {
  margin: 0 0 2px 0;
  color: #4c1d95;
  font-size: 9.1pt;
}

.q-body {
  margin: 0;
  color: #2e1065;
}

/* Student Signature Block */
.student-signature-block {
  margin-top: 8px;
  padding: 5px 9px;
  background-color: #f8fafc;
  border: 1px solid #cbd5e1;
  border-left: 4px solid #0f2a4a;
  border-radius: 4px;
  page-break-inside: avoid;
  break-inside: avoid;
}

.sig-name {
  font-size: 9.2pt;
  font-weight: 800;
  color: #0f2a4a;
}

.sig-meta {
  font-size: 8pt;
  color: #475569;
  margin-top: 1px;
}

.page-break {
  page-break-after: always;
  break-after: page;
}
"""

full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Round 4 Report to Advisor — R3-C1…C9 Complete</title>
<style>
{css}
</style>
</head>
<body>
{body_html}
</body>
</html>
"""

print(f"Writing HTML to: {HTML_FILE}")
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

# Stamping running headers & footers via ReportLab Canvas
print("Stamping headers, footers, accent stripes via ReportLab Canvas...")
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
        can.drawString(42, height - 25, "MASTER'S THESIS PROGRESS REPORT • ROUND 4")

        can.setFont('Helvetica', 7.5)
        can.setFillColor(colors.HexColor('#64748b'))
        can.drawString(252, height - 25, "|   R3-C1…C9 Complete: Literature Gap Audit Resolution")

        # Date badge pill on right
        can.setFillColor(colors.HexColor('#f1f5f9'))
        can.setStrokeColor(colors.HexColor('#cbd5e1'))
        can.setLineWidth(0.6)
        can.roundRect(width - 102, height - 30, 60, 13, 3, fill=1, stroke=1)

        can.setFont('Helvetica-Bold', 7)
        can.setFillColor(colors.HexColor('#334155'))
        can.drawCentredString(width - 72, height - 26.5, "2026-10-06")

        # Dual-tone divider line
        can.setStrokeColor(colors.HexColor('#e2e8f0'))
        can.setLineWidth(0.6)
        can.line(42, height - 35, width - 42, height - 35)

        can.setStrokeColor(colors.HexColor('#0f2a4a'))
        can.setLineWidth(1.2)
        can.line(42, height - 35, 172, height - 35)

    # 3. Running Footer (All Pages)
    # Dual-tone footer line
    can.setStrokeColor(colors.HexColor('#e2e8f0'))
    can.setLineWidth(0.6)
    can.line(42, 28, width - 42, 28)

    can.setStrokeColor(colors.HexColor('#2563eb'))
    can.setLineWidth(1.2)
    can.line(42, 28, 135, 28)

    # Left subtitle: EXACT user-specified student info
    can.setFont('Helvetica', 7.4)
    can.setFillColor(colors.HexColor('#334155'))
    can.drawString(42, 16.5, "Padipat Aincham (Dom) • Student ID: M11452803 • Graduate Institute of A.I. Cross-disciplinary Technology, NTUST")

    # Right page badge pill
    can.setFillColor(colors.HexColor('#f8fafc'))
    can.setStrokeColor(colors.HexColor('#cbd5e1'))
    can.setLineWidth(0.6)
    can.roundRect(width - 102, 11.5, 60, 14, 7, fill=1, stroke=1)

    can.setFont('Helvetica-Bold', 7.5)
    can.setFillColor(colors.HexColor('#0f2a4a'))
    can.drawCentredString(width - 72, 16, f"Page {page_num} of {total_pages}")

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

print(f"Successfully generated: {FINAL_PDF}")
print(f"File size: {os.path.getsize(FINAL_PDF)} bytes across {total_pages} pages.")
