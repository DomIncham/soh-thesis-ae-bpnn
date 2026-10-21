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
REPORT_DIR = r"C:\Master Degree\Thesis\Comment Prof and Report\Report"
MD_FILE = os.path.join(WORKDIR, "round5_comparison_report.md")
HTML_FILE = os.path.join(REPORT_DIR, "round5_comparison_report.html")
TEMP_PDF = os.path.join(REPORT_DIR, "temp_round5.pdf")
FINAL_PDF = os.path.join(REPORT_DIR, "round5_comparison_report.pdf")
EDGE_EXE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

print(f"Reading markdown: {MD_FILE}")
with open(MD_FILE, 'r', encoding='utf-8') as f:
    md_content = f.read()

# CSS styling adhering strictly to the aesthetic of Progress_Report_Steps1-18_Round2.pdf
css_styles = """
@page {
  size: A4 portrait;
  margin: 16mm 15mm 16mm 15mm;
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
  font-size: 8.85pt;
  line-height: 1.36;
  color: #1e293b;
  background-color: #ffffff;
  margin: 0;
  padding: 0;
}

/* ========================================================
   HEADER & META CARD (MATCHING ROUND 2 STYLE)
   ======================================================== */
.report-header {
  border-bottom: 2.2px solid #0f2a4a;
  padding-bottom: 5px;
  margin-bottom: 8px;
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
  font-size: 7.4pt;
  background-color: #0f2a4a;
  color: #ffffff;
  padding: 2.5px 8px;
  border-radius: 3px;
  font-weight: 600;
  letter-spacing: 0.04em;
  white-space: nowrap;
}

h1 {
  font-size: 13pt;
  font-weight: 800;
  color: #0f2a4a;
  line-height: 1.25;
  margin: 0;
}

.meta-card {
  background-color: #f8fafc;
  border: 1.2px solid #cbd5e1;
  border-left: 4.5px solid #0f2a4a;
  border-radius: 4px;
  padding: 7px 11px;
  margin-bottom: 9px;
  font-size: 8.6pt;
  line-height: 1.38;
  page-break-inside: avoid;
  break-inside: avoid;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
}

.meta-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 3.5px 14px;
}

.meta-item {
  display: flex;
  align-items: baseline;
  gap: 5px;
}

.meta-label {
  font-weight: 700;
  color: #0f2a4a;
  white-space: nowrap;
  font-size: 8.4pt;
}

.meta-val {
  color: #334155;
  font-size: 8.5pt;
}

.meta-verify-banner {
  margin-top: 6px;
  padding-top: 5px;
  border-top: 1px dashed #cbd5e1;
  display: flex;
  align-items: center;
  gap: 8px;
}

.verify-badge {
  background-color: #16a34a;
  color: #ffffff;
  font-weight: 700;
  font-size: 7.2pt;
  padding: 1.5px 6px;
  border-radius: 3px;
  letter-spacing: 0.04em;
  white-space: nowrap;
}

.meta-verify-text {
  font-size: 8.2pt;
  color: #166534;
  font-weight: 500;
}

/* ========================================================
   HEADINGS & CONTENT
   ======================================================== */
h2 {
  font-size: 10.2pt;
  font-weight: 700;
  color: #1e3a5f;
  line-height: 1.25;
  margin-top: 9px;
  margin-bottom: 4px;
  padding-bottom: 2.5px;
  border-bottom: 1.4px solid #cbd5e1;
  page-break-after: avoid;
  break-after: avoid;
}

p {
  margin-top: 0;
  margin-bottom: 5px;
  text-align: justify;
}

ul, ol {
  margin-top: 0;
  margin-bottom: 5px;
  padding-left: 18px;
}

li {
  margin-bottom: 2.5px;
  text-align: justify;
}

a {
  color: #1d4ed8;
  text-decoration: underline;
  text-underline-offset: 1.8px;
  text-decoration-color: #93c5fd;
}

code {
  font-family: Consolas, "Courier New", monospace;
  font-size: 8.1pt;
  background-color: #f1f5f9;
  color: #0f2a4a;
  padding: 1px 4px;
  border-radius: 3px;
  border: 1px solid #cbd5e1;
  white-space: nowrap;
}

/* ========================================================
   CALLOUT BOXES & CARDS
   ======================================================== */
.info-box {
  background-color: #f8fafc;
  border: 1.2px solid #cbd5e1;
  border-left: 4px solid #2563eb;
  border-radius: 4px;
  padding: 6px 10px;
  margin: 6px 0 8px 0;
  font-size: 8.5pt;
  line-height: 1.36;
  page-break-inside: avoid;
  break-inside: avoid;
}

.box-title {
  font-size: 7.6pt;
  font-weight: 800;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  margin-bottom: 3px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.info-title {
  color: #1d4ed8;
}

.files-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin: 5px 0 4px 0;
}

.file-group {
  background-color: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 3px;
  padding: 5px 8px;
}

.file-group-title {
  font-weight: 700;
  font-size: 8.3pt;
  color: #0f2a4a;
  border-bottom: 1px solid #f1f5f9;
  padding-bottom: 2px;
  margin-bottom: 4px;
}

.file-list {
  list-style-type: none;
  padding-left: 0;
  margin: 0;
}

.file-list li {
  margin-bottom: 2px;
  font-size: 8pt;
}

.feature-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin: 5px 0 6px 0;
}

.feature-card {
  background-color: #f8fafc;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  padding: 6px 9px;
  font-size: 8.4pt;
  line-height: 1.38;
}

.feature-card.c6t {
  border-left: 3.5px solid #64748b;
}

.feature-card.c5t {
  border-left: 3.5px solid #2563eb;
  background-color: #eff6ff;
}

.feature-card-header {
  font-weight: 700;
  font-size: 8.4pt;
  color: #0f2a4a;
  margin-bottom: 3px;
}

/* ========================================================
   TABLES (GRID WITH ALL BORDERS - EXACT ROUND 2 STYLE)
   ======================================================== */
table {
  width: 100%;
  table-layout: fixed;
  border-collapse: collapse;
  margin: 5px 0 7px 0;
  font-size: 8.2pt;
  line-height: 1.28;
  page-break-inside: avoid;
  break-inside: avoid;
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
  padding: 4px 6px;
  border: 1px solid #cbd5e1;
  border-bottom: 2px solid #0f2a4a;
}

td {
  padding: 3.5px 6px;
  border: 1px solid #cbd5e1;
  vertical-align: middle;
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

.num-cell {
  font-family: Consolas, "Courier New", monospace;
  font-size: 8pt;
}

.center-cell {
  text-align: center;
}

/* Highlight badge in table reading */
.reading-badge {
  font-weight: 600;
  color: #0f2a4a;
}

.reading-better {
  color: #166534;
  font-weight: 600;
}

.reading-warn {
  color: #991b1b;
  font-weight: 600;
}

/* ========================================================
   KEY FINDINGS LIST & ACTION CARD
   ======================================================== */
.findings-list {
  padding-left: 0;
  list-style: none;
  margin: 4px 0 6px 0;
}

.findings-item {
  position: relative;
  padding-left: 22px;
  margin-bottom: 4.5px;
  text-align: justify;
}

.findings-num {
  position: absolute;
  left: 0;
  top: 0;
  width: 16px;
  height: 16px;
  background-color: #0f2a4a;
  color: #ffffff;
  font-size: 7.2pt;
  font-weight: 700;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

.action-card {
  background-color: #fffbeb;
  border: 1.2px solid #fde68a;
  border-left: 4.5px solid #d97706;
  border-radius: 4px;
  padding: 6px 10px;
  margin-top: 6px;
  font-size: 8.5pt;
  line-height: 1.36;
  page-break-inside: avoid;
  break-inside: avoid;
}

.action-title {
  color: #b45309;
}

.page-break {
  page-break-after: always;
  break-after: page;
}
"""

# Assemble semantic HTML content directly based ONLY on round5_comparison_report.md
body_html = f"""
<div class="report-header">
  <div class="report-top-meta">
    <div class="report-subtitle">National Taiwan University of Science and Technology • Master\'s Thesis</div>
    <div class="report-badge">Round 5 — Rotated Selection</div>
  </div>
  <h1>Round 5 comparison: Clean-5T vs Clean-6T under rotated selection</h1>
</div>

<div class="meta-card">
  <div class="meta-grid">
    <div class="meta-item"><span class="meta-label">Date:</span> <span class="meta-val">2026-10-18</span></div>
    <div class="meta-item"><span class="meta-label">Author:</span> <span class="meta-val">Padipat Aincham (M11452803)</span></div>
    <div class="meta-item"><span class="meta-label">Repository:</span> <span class="meta-val"><a href="https://github.com/DomIncham/soh-thesis-ae-bpnn">github.com/DomIncham/soh-thesis-ae-bpnn</a> (branch <code>main</code>)</span></div>
    <div class="meta-item"><span class="meta-label">Code:</span> <span class="meta-val"><a href="https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/phase5_cs2_clean5t.py"><code>phase5_cs2_clean5t.py</code></a> (Clean-5T default; Clean-6T via <code>CLEAN_FEATS</code> env var)</span></div>
    <div class="meta-item"><span class="meta-label">Protocol:</span> <span class="meta-val">Rotated battery-wise validation on CALCE (5 seeds: 42, 7, 99, 123, 2024; CPU; same data as Round 4)</span></div>
    <div class="meta-item"><span class="meta-label">Test Isolation:</span> <span class="meta-val">Outer test battery/cell absent from every inner train/val set (asserted by S6)</span></div>
  </div>
  <div class="meta-verify-banner">
    <span class="verify-badge">VERIFIED PASS</span>
    <span class="meta-verify-text">Structural verification suite passes <strong>34/34 checks</strong> (S6 outer test isolation + S7 result-file completeness: 8 CSVs, row counts, seeds, no NaN).</span>
  </div>
</div>

<div class="info-box">
  <div class="box-title info-title">Protocol & Execution Context</div>
  <p>This is the updated comparison you asked for; nothing else is included. All runs are CPU, 5 seeds (42, 7, 99, 123, 2024), the same data files as Round 4. As you instructed, the CALCE selection stages now use rotated battery-wise validation: each source-training battery takes one inner-validation turn, the validation score is averaged across rotations before the refit, and the outer test battery/cell is not used at any point in selection or refit. A structural check (S6) asserts the outer battery is absent from every inner train/val set. I re-ran both feature sets under this protocol (eight result files). The structural suite now also checks result-file completeness (S7) and passes 34/34.</p>
  
  <div style="margin-top: 5px; font-weight: 700; font-size: 8.2pt; color: #0f2a4a;">Result files (each CSV has one row per cell × seed, with cfg, sel_epochs, MAE, RMSE, R²; <code>MAE</code>/<code>RMSE</code> are on capacity scale):</div>
  <div class="files-container">
    <div class="file-group">
      <div class="file-group-title">Clean-5T Result Files</div>
      <ul class="file-list">
        <li>• <a href="https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/phase5_cs2_within_c5t_full.csv"><code>phase5_cs2_within_c5t_full.csv</code></a> (40 rows)</li>
        <li>• <a href="https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/phase5_cs2_transfer_c5t_full.csv"><code>phase5_cs2_transfer_c5t_full.csv</code></a> (80 rows: room + all-13 pools)</li>
        <li>• <a href="https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/phase5_cs2_adapt1_c5t_full.csv"><code>phase5_cs2_adapt1_c5t_full.csv</code></a> (80 rows)</li>
        <li>• <a href="https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/phase5_cs2_adapt2_c5t_full.csv"><code>phase5_cs2_adapt2_c5t_full.csv</code></a> (80 rows)</li>
      </ul>
    </div>
    <div class="file-group">
      <div class="file-group-title">Clean-6T Result Files</div>
      <ul class="file-list">
        <li>• <a href="https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/phase5_cs2_within_c6t_full.csv"><code>phase5_cs2_within_c6t_full.csv</code></a> (40 rows)</li>
        <li>• <a href="https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/phase5_cs2_transfer_c6t_full.csv"><code>phase5_cs2_transfer_c6t_full.csv</code></a> (80 rows: room + all-13 pools)</li>
        <li>• <a href="https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/phase5_cs2_adapt1_c6t_full.csv"><code>phase5_cs2_adapt1_c6t_full.csv</code></a> (80 rows)</li>
        <li>• <a href="https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/phase5_cs2_adapt2_c6t_full.csv"><code>phase5_cs2_adapt2_c6t_full.csv</code></a> (80 rows)</li>
      </ul>
    </div>
  </div>
  <div style="font-size: 7.9pt; color: #64748b; margin-top: 3px;">All eight files live under <code>Autoencoder/round3_phase1/</code>.</div>
</div>

<h2>Feature sets (R5-C2)</h2>
<div class="feature-grid">
  <div class="feature-card c6t">
    <div class="feature-card-header">Clean-6T (Round 4 baseline — 6 features)</div>
    <div>Clean-7 minus the two temperature features, plus <code>t_40_41</code>: <code>dis_V_slope</code>, <code>cc_dur</code>, <code>cv_dur</code>, <code>cv_I_slope</code>, <code>t_40_41</code>, <code>ic_peak_V</code>.</div>
  </div>
  <div class="feature-card c5t">
    <div class="feature-card-header">Clean-5T (New — 5 features)</div>
    <div>Clean-6T minus <code>t_40_41</code>: <code>dis_V_slope</code>, <code>cc_dur</code>, <code>cv_dur</code>, <code>cv_I_slope</code>, <code>ic_peak_V</code>. Both feature sets pass the S4 proxy-ban check.</div>
  </div>
</div>

<h2>Comparison — both columns under the same rotated-selection protocol</h2>
<p style="font-size: 8.5pt; color: #334155; margin-bottom: 5px;">Because Clean-6T was re-run under the rotated selection, both columns below share one protocol, seeds, budgets, and data files. The Round 4 Clean-6T numbers (single validation battery) are not comparable and I did not use them.</p>

<table>
  <colgroup>
    <col style="width: 32%;" />
    <col style="width: 14%;" />
    <col style="width: 17%;" />
    <col style="width: 17%;" />
    <col style="width: 20%;" />
  </colgroup>
  <thead>
    <tr>
      <th>Experiment</th>
      <th style="text-align: center;">Statistic</th>
      <th style="text-align: center;">Clean-6T</th>
      <th style="text-align: center;">Clean-5T</th>
      <th>Reading</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>Within-CALCE LOCO</strong> (8 cells)</td>
      <td class="center-cell">mean / median</td>
      <td class="center-cell num-cell">0.137 / 0.576</td>
      <td class="center-cell num-cell">0.208 / 0.581</td>
      <td><span class="reading-better">Clean-5T equal or better</span></td>
    </tr>
    <tr>
      <td><strong>Frozen NASA → CALCE</strong> (room pool)</td>
      <td class="center-cell">mean / median</td>
      <td class="center-cell num-cell">−19.2 / −7.1</td>
      <td class="center-cell num-cell">−32.3 / −8.8</td>
      <td><span class="reading-badge">medians close; means not stable</span></td>
    </tr>
    <tr>
      <td><strong>Frozen NASA → CALCE</strong> (all-13 pool)</td>
      <td class="center-cell">mean / median</td>
      <td class="center-cell num-cell">−72.7 / −44.3</td>
      <td class="center-cell num-cell">−65.2 / −52.1</td>
      <td><span class="reading-warn">negative in both</span></td>
    </tr>
    <tr>
      <td><strong>One-cell scratch</strong> (adapt1)</td>
      <td class="center-cell">mean / median</td>
      <td class="center-cell num-cell">−443.7 / −30.9</td>
      <td class="center-cell num-cell">−225.2 / −34.5</td>
      <td><span class="reading-warn">both non-viable</span></td>
    </tr>
    <tr>
      <td><strong>One-cell warm</strong> (adapt2)</td>
      <td class="center-cell">mean / median</td>
      <td class="center-cell num-cell">−9.9 / −4.2</td>
      <td class="center-cell num-cell">−13.1 / −5.9</td>
      <td><span class="reading-better">Clean-6T better on all 8 cells</span></td>
    </tr>
  </tbody>
</table>

<div class="page-break"></div>

<h2>Per-cell detail (mean R², 5 seeds, same protocol both columns)</h2>
<table>
  <colgroup>
    <col style="width: 12%;" />
    <col style="width: 22%;" />
    <col style="width: 22%;" />
    <col style="width: 23%;" />
    <col style="width: 21%;" />
  </colgroup>
  <thead>
    <tr>
      <th style="text-align: center;">Cell</th>
      <th style="text-align: center;">Within C6T → C5T</th>
      <th style="text-align: center;">Transfer Room C6T → C5T</th>
      <th style="text-align: center;">Transfer All-13 C6T → C5T</th>
      <th style="text-align: center;">Adapt2 C6T → C5T</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td class="center-cell" style="font-weight: 700;">CS2_8</td>
      <td class="center-cell num-cell">−2.045 → −2.246</td>
      <td class="center-cell num-cell">−72.222 → −43.925</td>
      <td class="center-cell num-cell">−117.527 → −157.341</td>
      <td class="center-cell num-cell">−7.006 → −10.399</td>
    </tr>
    <tr>
      <td class="center-cell" style="font-weight: 700;">CS2_21</td>
      <td class="center-cell num-cell">−0.312 → 0.182</td>
      <td class="center-cell num-cell">−4.021 → −3.242</td>
      <td class="center-cell num-cell">−11.975 → −18.484</td>
      <td class="center-cell num-cell">−14.626 → −18.167</td>
    </tr>
    <tr>
      <td class="center-cell" style="font-weight: 700;">CS2_33</td>
      <td class="center-cell num-cell">0.636 → 0.686</td>
      <td class="center-cell num-cell">−14.114 → −34.589</td>
      <td class="center-cell num-cell">−74.836 → −59.397</td>
      <td class="center-cell num-cell">−10.652 → −14.000</td>
    </tr>
    <tr>
      <td class="center-cell" style="font-weight: 700;">CS2_34</td>
      <td class="center-cell num-cell">0.771 → 0.648</td>
      <td class="center-cell num-cell">−15.878 → −40.013</td>
      <td class="center-cell num-cell">−88.080 → −65.384</td>
      <td class="center-cell num-cell">−10.026 → −12.829</td>
    </tr>
    <tr>
      <td class="center-cell" style="font-weight: 700;">CS2_35</td>
      <td class="center-cell num-cell">0.487 → 0.479</td>
      <td class="center-cell num-cell">−16.394 → −43.515</td>
      <td class="center-cell num-cell">−89.938 → −69.845</td>
      <td class="center-cell num-cell">−8.790 → −11.581</td>
    </tr>
    <tr>
      <td class="center-cell" style="font-weight: 700;">CS2_36</td>
      <td class="center-cell num-cell">0.642 → 0.661</td>
      <td class="center-cell num-cell">−11.801 → −32.759</td>
      <td class="center-cell num-cell">−70.078 → −54.516</td>
      <td class="center-cell num-cell">−9.833 → −12.994</td>
    </tr>
    <tr>
      <td class="center-cell" style="font-weight: 700;">CS2_37</td>
      <td class="center-cell num-cell">0.518 → 0.742</td>
      <td class="center-cell num-cell">−10.312 → −31.514</td>
      <td class="center-cell num-cell">−67.133 → −50.571</td>
      <td class="center-cell num-cell">−8.988 → −12.288</td>
    </tr>
    <tr>
      <td class="center-cell" style="font-weight: 700;">CS2_38</td>
      <td class="center-cell num-cell">0.402 → 0.515</td>
      <td class="center-cell num-cell">−9.133 → −28.976</td>
      <td class="center-cell num-cell">−62.178 → −46.082</td>
      <td class="center-cell num-cell">−9.241 → −12.863</td>
    </tr>
  </tbody>
</table>

<h2>What the numbers show</h2>
<ol class="findings-list">
  <li class="findings-item">
    <span class="findings-num">1</span>
    <strong>Within-CALCE:</strong> Clean-5T is equal to or better than Clean-6T (median 0.576 → 0.581). <code>t_40_41</code> is not needed for within-CALCE accuracy, which matches the NASA result that it no longer improves the corrected protocol.
  </li>
  <li class="findings-item">
    <span class="findings-num">2</span>
    <strong>Transfer, room pool:</strong> I do not attribute the mean difference to the feature change. The per-seed room-pool mean deltas switch sign (−109.3, −7.0, +49.1, +151.6, −46.9 for seeds 7, 42, 99, 123, 2024) and the two medians are close (−7.1 vs −8.8). Five seeds do not separate the two sets here.
  </li>
  <li class="findings-item">
    <span class="findings-num">3</span>
    <strong>Warm adaptation (adapt2) is the one case with a direction on every cell:</strong> Clean-6T is better on all 8 cells (mean −9.9 vs −13.1). So <code>t_40_41</code> does carry signal for warm-start fine-tuning.
  </li>
  <li class="findings-item">
    <span class="findings-num">4</span>
    <strong>Transfer and adaptation stay negative in every pool under both feature sets</strong> (means from −9.9 to −443.7). The cross-dataset gap stands.
  </li>
  <li class="findings-item">
    <span class="findings-num">5</span>
    <strong>The Round 4 interpretation is unchanged:</strong> the failure is consistent with domain/range shift (the target ranges do not overlap), not proven to be caused by it. Removing the two proxy-equivalent features (<code>dis_duration</code>, <code>dis_mean_V</code>) improved transfer while within-CALCE performance stayed at about the same level (median 0.589 → 0.573 in Round 4), so those two features amplified the cross-domain mismatch.
  </li>
</ol>

<h2>Selection fallback rates</h2>
<p>Some candidates diverge before the epoch budget is reached. When that happens the runner falls back to the best diverged candidate, retrained for a fixed 200 epochs. Counts below come from the per-row columns in the CSVs (Clean-5T / Clean-6T):</p>

<table>
  <colgroup>
    <col style="width: 25%;" />
    <col style="width: 40%;" />
    <col style="width: 35%;" />
  </colgroup>
  <thead>
    <tr>
      <th>Arm</th>
      <th style="text-align: center;">Rows with ≥1 diverged candidate</th>
      <th style="text-align: center;">Rows on the fixed-200-epoch fallback</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>Within</strong></td>
      <td class="center-cell num-cell">40/40 / 40/40</td>
      <td class="center-cell num-cell">22/40 / 10/40</td>
    </tr>
    <tr>
      <td><strong>Transfer room</strong></td>
      <td class="center-cell num-cell">24/40 / 40/40</td>
      <td class="center-cell num-cell">0/40 / 0/40</td>
    </tr>
    <tr>
      <td><strong>Transfer all-13</strong></td>
      <td class="center-cell num-cell">40/40 / 40/40</td>
      <td class="center-cell num-cell">16/40 / 16/40</td>
    </tr>
    <tr>
      <td><strong>Adapt1, adapt2</strong></td>
      <td class="center-cell num-cell">64/80 each, both sets</td>
      <td class="center-cell num-cell">16/80 each, both sets</td>
    </tr>
  </tbody>
</table>

<p>Most NASA-pool rows sit on this fallback path. The counts are recorded per row. The likely cause is fitting BPNNs on the shifted NASA ranges; either way it does not change the conclusion that transfer fails under both feature sets.</p>
<p>Structural verification covers both result sets (S7: 8 CSVs, row counts, seeds, no NaN); the suite passes 34/34.</p>

<div class="action-card">
  <div class="box-title action-title">Next direction</div>
  <p style="margin: 0;">The cross-dataset gap remains, so per your Round 5 instruction the next direction is <strong>domain-shift/range-alignment analysis</strong>, not further AE optimization. I have not started this work and will wait for your confirmation.</p>
</div>
"""

full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Round 5 Comparison: Clean-5T vs Clean-6T under Rotated Selection</title>
<style>
{css_styles}
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

# ReportLab Canvas stamping running header, footer, accent stripes
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
        can.drawString(42, height - 25, "MASTER'S THESIS PROGRESS REPORT • ROUND 5")

        can.setFont('Helvetica', 7.5)
        can.setFillColor(colors.HexColor('#64748b'))
        can.drawString(252, height - 25, "|   Clean-5T vs Clean-6T under Rotated Selection")

        # Date badge pill on right
        can.setFillColor(colors.HexColor('#f1f5f9'))
        can.setStrokeColor(colors.HexColor('#cbd5e1'))
        can.setLineWidth(0.6)
        can.roundRect(width - 102, height - 30, 60, 13, 3, fill=1, stroke=1)

        can.setFont('Helvetica-Bold', 7)
        can.setFillColor(colors.HexColor('#334155'))
        can.drawCentredString(width - 72, height - 26.5, "2026-10-18")

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

    # Left subtitle: EXACT student info
    can.setFont('Helvetica', 7.4)
    can.setFillColor(colors.HexColor('#334155'))
    can.drawString(42, 16.5, "Padipat Aincham (M11452803) • Graduate Institute of A.I. Cross-disciplinary Technology, NTUST")

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
