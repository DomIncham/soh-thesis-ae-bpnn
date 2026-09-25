import os
import sys
import base64
import subprocess

html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>State-of-Health (SOH) Estimation of Lithium-Ion Batteries — Progress Report (Round 2)</title>
<style>
  @page {
    size: A4 portrait;
    margin: 12mm 16mm 12mm 16mm;
  }
  
  *, *:before, *:after {
    box-sizing: border-box;
  }

  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    color: #1e293b;
    background-color: #ffffff;
    line-height: 1.45;
    font-size: 11.5pt; /* Sized within 11-14 pt */
    margin: 0;
    padding: 0;
  }

  /* Page break controls */
  .page-break {
    page-break-after: always;
    break-after: page;
  }
  .avoid-break {
    page-break-inside: avoid;
    break-inside: avoid;
  }

  /* Document Header */
  .doc-header {
    border-bottom: 2.5px solid #1e3a8a;
    padding-bottom: 10px;
    margin-bottom: 14px;
  }
  .doc-top-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 6px;
  }
  .thesis-subject {
    font-size: 12pt;
    font-weight: 800;
    color: #1e3a8a;
    letter-spacing: 0.2px;
    line-height: 1.35;
    flex: 1;
  }
  .report-badge {
    background-color: #e0f2fe;
    color: #0369a1;
    padding: 3px 12px;
    border-radius: 9999px;
    font-size: 9.5pt;
    font-weight: 800;
    border: 1.5px solid #bae6fd;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    white-space: nowrap;
  }
  h1.doc-title {
    font-size: 17.5pt;
    font-weight: 850;
    color: #0f172a;
    margin: 6px 0 0 0;
    line-height: 1.25;
    letter-spacing: -0.3px;
  }

  /* Metadata Box (Exact verbatim text from markdown) */
  .meta-box {
    background: #f8fafc;
    border: 1px solid #cbd5e1;
    border-left: 4.5px solid #1e3a8a;
    border-radius: 6px;
    padding: 12px 16px;
    margin-top: 14px;
    font-size: 11pt;
    line-height: 1.52;
  }
  .meta-item {
    margin-bottom: 8px;
  }
  .meta-item:last-child {
    margin-bottom: 0;
  }
  .meta-item strong {
    color: #0f172a;
    font-weight: 750;
  }

  /* Section Headings */
  h2.section-title {
    font-size: 13.5pt;
    font-weight: 800;
    color: #1e3a8a;
    border-bottom: 1.5px solid #cbd5e1;
    padding-bottom: 3px;
    margin-top: 16px;
    margin-bottom: 8px;
    break-after: avoid;
    page-break-after: avoid;
  }
  h2.section-title:first-child {
    margin-top: 0;
  }
  h3.subsection-title {
    font-size: 12pt;
    font-weight: 800;
    color: #0f172a;
    margin-top: 12px;
    margin-bottom: 5px;
    break-after: avoid;
    page-break-after: avoid;
  }

  /* Paragraphs and Lists */
  p {
    font-size: 11pt;
    line-height: 1.48;
    color: #1e293b;
    margin: 7px 0;
  }
  ul, ol {
    font-size: 11pt;
    line-height: 1.48;
    margin: 7px 0;
    padding-left: 22px;
  }
  li {
    margin-bottom: 4px;
  }

  /* Tables */
  table.data-table {
    width: 100%;
    border-collapse: collapse;
    margin: 6px 0 10px 0;
    font-size: 9.5pt; /* Fitted perfectly so 8 rows fit per page */
    background: #ffffff;
    border: 1.5px solid #cbd5e1;
    border-radius: 6px;
    overflow: hidden;
  }
  table.data-table thead {
    display: table-header-group;
    background: #f1f5f9;
  }
  table.data-table th {
    font-weight: 750;
    color: #0f172a;
    padding: 5px 7px;
    text-align: left;
    border-bottom: 1.5px solid #94a3b8;
    border-right: 1px solid #e2e8f0;
    font-size: 9pt;
    letter-spacing: 0.2px;
  }
  table.data-table th:last-child {
    border-right: none;
  }
  table.data-table td {
    padding: 4px 7px;
    border-bottom: 1px solid #e2e8f0;
    border-right: 1px solid #e2e8f0;
    vertical-align: top;
    line-height: 1.32;
  }
  table.data-table td:last-child {
    border-right: none;
  }
  table.data-table tr:nth-child(even) td {
    background-color: #f8fafc;
  }
  table.data-table tr {
    break-inside: avoid;
    page-break-inside: avoid;
  }

  /* Code elements */
  code {
    font-family: SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace;
    font-size: 8.8pt;
    background-color: #f1f5f9;
    padding: 1.5px 3.5px;
    border-radius: 3px;
    border: 1px solid #e2e8f0;
    color: #0f172a;
  }

  /* Large, Clear Figure Containers */
  .figure-container {
    margin: 10px 0 14px 0;
    break-inside: avoid;
    page-break-inside: avoid;
  }
  .figure-card {
    background: #ffffff;
    border: 1.5px solid #cbd5e1;
    border-radius: 8px;
    padding: 8px 10px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
  }
  .figure-card img {
    width: 100%;
    max-height: 86mm; /* Large display */
    object-fit: contain;
    display: block;
    margin: 0 auto;
    border-radius: 4px;
    background-color: #ffffff;
  }
  .figure-card img.ranking-img {
    max-height: 86mm;
    max-width: 90%;
  }
  .figure-card img.nyquist-img {
    max-height: 96mm;
    max-width: 85%;
  }
  .figure-caption {
    font-size: 10pt;
    color: #334155;
    margin-top: 5px;
    line-height: 1.35;
    font-style: italic;
  }
  .figure-caption strong {
    color: #0f172a;
    font-style: normal;
  }

  /* Highlight Card for Key Section Text */
  .text-card {
    background: #f8fafc;
    border: 1px solid #cbd5e1;
    border-left: 4.5px solid #2563eb;
    border-radius: 6px;
    padding: 9px 13px;
    margin: 8px 0 12px 0;
    font-size: 10.5pt;
    line-height: 1.45;
    break-inside: avoid;
    page-break-inside: avoid;
  }

  /* Clean Document Footer */
  .doc-footer {
    border-top: 1px solid #cbd5e1;
    padding-top: 6px;
    margin-top: 16px;
    font-size: 9pt;
    color: #64748b;
    display: flex;
    justify-content: space-between;
    align-items: center;
    break-inside: avoid;
    page-break-inside: avoid;
  }
</style>
</head>
<body>

<!-- ==================== PAGE 1: TITLE & METADATA ==================== -->
<div class="doc-header">
  <div class="doc-top-bar">
    <div class="thesis-subject">
      State-of-Health (SOH) Estimation of Lithium-Ion Batteries Using Two-Stage Autoencoder and BPNN
    </div>
    <div class="report-badge">PROGRESS REPORT (ROUND 2)</div>
  </div>
  <h1 class="doc-title">
    Progress Report &mdash; Round 2: All 18 Steps Completed (EIS Verification &rarr; Pipeline Comparison &rarr; Time-Domain)
  </h1>
</div>

<div class="meta-box">
  <div class="meta-item">
    <strong>Date:</strong> 2026-09-25
  </div>
  <div class="meta-item">
    <strong>Data:</strong> NASA BatteryAgingARC-FY08Q4 (B0005, B0006, B0007, B0018), verified raw files tracked in this repository.
  </div>
  <div class="meta-item">
    <strong>Protocol (used identically for every comparison):</strong> nested 4-fold LOBO &mdash; each battery serves as the unseen outer test in turn; inner validation = first remaining battery; all hyperparameters chosen by inner validation only; SOH in % (Q_ref = mean of first 5 discharge cycles); targets standardized on fold-train only; EarlyStopping on inner-val loss; metrics MAE/RMSE/R&sup2; + nRMSE in %SOH; seeds {42, 7, 123}.
  </div>
  <div class="meta-item">
    <strong>Leakage controls (every run):</strong> structural assert (scaler statistics equal fold-train statistics) + feature-perturbation probes (outer test &times;2 &rarr; retrain &rarr; train metrics must not move; three probes across batches, all PASS with diff &le; 3.8e-05, one exactly 0).
  </div>
</div>

<div class="page-break"></div>

<!-- ==================== PAGE 2: SECTION 1 (PART 1: STEPS 1-8) ==================== -->
<h2 class="section-title">1. Status of the 18-Step Sequence (Steps 1&ndash;8)</h2>

<table class="data-table">
  <thead>
    <tr>
      <th style="width: 8%;">Step</th>
      <th style="width: 25%;">Task (advisor Part)</th>
      <th style="width: 47%;">Result</th>
      <th style="width: 20%;">Evidence</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>1&ndash;2</strong></td>
      <td>Verify NASA EIS variables and frequency ordering (A1&ndash;A2, M-A/B)</td>
      <td>CSV = <code>Rectified_Impedance</code>, exact on all 34,593 rows (max diff &lt; 1e-15 Ohm); row order consistent with low&rarr;high frequency (887/887 spectra, indirect evidence); <strong>no per-point frequency exists in the distributed <code>.mat</code></strong> &mdash; any frequency column is a declared assumption. The flat Nyquist arc is a property of NASA's <code>Rectified_Impedance</code> itself (Case 2): max |Im| &asymp; 2&ndash;6 mOhm across all 887 spectra, while the raw <code>Battery_impedance</code> differs by 32&ndash;68&times; and contains values that are not physically plausible</td>
      <td><code>eis_verify/EIS_Raw_Verification.md</code></td>
    </tr>
    <tr>
      <td><strong>3&ndash;4</strong></td>
      <td>Frequency-ordered table + plots; spectrum integrity (A3&ndash;A5, M-C/D)</td>
      <td>39 points &times; 887 spectra = 34,593 CSV rows; timestamps monotonic; 0 NaN/Inf/duplicates; no isolated outlier points</td>
      <td>same + <code>A3_*_3plots.png</code>, <code>A7_*</code></td>
    </tr>
    <tr>
      <td><strong>5</strong></td>
      <td>Re-evaluate interpolation with a quantitative measure (A8)</td>
      <td>Chord-envelope overshoot: <strong>PCHIP 0 in all 1,774 checks; Cubic 0.25&ndash;1.76 mOhm mean, worst 11.2 mOhm</strong> (exceeds the full reactive span 2&ndash;6 mOhm); Linear also 0 but not smooth</td>
      <td><code>Interpolation_Reeval.md</code></td>
    </tr>
    <tr>
      <td><strong>6b</strong></td>
      <td>Expanded AE reconstruction metrics (D3)</td>
      <td>Re(Z) RMSE / Im(Z) RMSE separately + nRMSE + relative error, per battery (table in Section 4); reproduces the B0006 Re RMSE anomaly (14.6 mOhm, ~13&times; the other batteries)</td>
      <td><code>ae_reconstruction_d3_metrics.csv</code></td>
    </tr>
    <tr>
      <td><strong>6</strong></td>
      <td>Recheck Figure 6 (H2)</td>
      <td>AE reconstructs the <strong>interpolated input</strong>, not the measurement (recon-vs-measured = recon-vs-input + ~0.1 mOhm); B0006 anomaly is AE-specific</td>
      <td><code>Step6_Fig6_recheck.png</code></td>
    </tr>
    <tr>
      <td><strong>7</strong></td>
      <td>Nested 4-fold LOBO (C1&ndash;C3)</td>
      <td>Implemented; inner validation selects different configs per fold; leakage probes PASS</td>
      <td><code>Steps_7_8_Nested_LOBO.md</code></td>
    </tr>
    <tr>
      <td><strong>8</strong></td>
      <td>Tolerance 1/2/3 on downstream metrics (E1&ndash;E3)</td>
      <td>Tolerances indistinguishable downstream (RMSE 8.57&ndash;8.89 %SOH, all within 1 std) &rarr; pre-declared rule selects <strong>tolerance 1</strong>; gap distribution reported (bimodal: gap 1 or 3 for B0005&ndash;07)</td>
      <td>same</td>
    </tr>
  </tbody>
</table>

<div class="page-break"></div>

<!-- ==================== PAGE 3: SECTION 1 (PART 2: STEPS 9-18) ==================== -->
<h2 class="section-title">1. Status of the 18-Step Sequence (Steps 9&ndash;18)</h2>

<table class="data-table">
  <thead>
    <tr>
      <th style="width: 8%;">Step</th>
      <th style="width: 25%;">Task (advisor Part)</th>
      <th style="width: 47%;">Result</th>
      <th style="width: 20%;">Evidence</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>9</strong></td>
      <td>Raw EIS / PCA / AE &rarr; BPNN (F1.3&ndash;4)</td>
      <td>Working folds: <strong>PCA best (RMSE 5.92, R&sup2; +0.61)</strong>; AE loses to PCA on all three</td>
      <td><code>Steps_9_10_Baselines.md</code></td>
    </tr>
    <tr>
      <td><strong>10</strong></td>
      <td>Mean + Linear baselines (F1.1&ndash;2)</td>
      <td>Mean predictor marks the collapse baseline (R&sup2; &minus;0.77); 256-dim Ridge is fragile (disclosed breaches)</td>
      <td>same</td>
    </tr>
    <tr>
      <td><strong>11</strong></td>
      <td>MAE/RMSE/R&sup2; for every unseen battery (D2)</td>
      <td>Per-fold tables in both reports above</td>
      <td>&mdash;</td>
    </tr>
    <tr>
      <td><strong>12</strong></td>
      <td>Explain Figure 10 quantitatively (G1&ndash;G3)</td>
      <td>Old RMSE = 1.126 &times; std(y) &rarr; statistically a flat line, 12.6% worse than the trivial mean; cause chain: unstable latents (correlation flip) + unstandardized target + fixed epochs + single split</td>
      <td><code>Steps_12_Fig10_Collapse.md</code></td>
    </tr>
    <tr>
      <td><strong>13</strong></td>
      <td>mean &plusmn; std across folds and seeds (C3)</td>
      <td>All aggregates use 12 runs (4 folds &times; 3 seeds)</td>
      <td>&mdash;</td>
    </tr>
    <tr>
      <td><strong>14&ndash;15</strong></td>
      <td>Time-domain baseline and comparison (B1&ndash;B5)</td>
      <td><strong>TD-BPNN: RMSE 3.59, R&sup2; +0.85, positive on ALL four folds including B0018 (+0.79)</strong>; EIS pipelines negative on B0018 (&minus;1.0 to &minus;1.2)</td>
      <td><code>Steps_14_16_TimeDomain.md</code></td>
    </tr>
    <tr>
      <td><strong>16</strong></td>
      <td>Justify EIS vs time-domain (B6)</td>
      <td>Measured pattern matches the B6 criterion verbatim: R&sup2;_time &gt;&gt; 0 while R&sup2;_EIS &lt; 0 &rarr; the cross-battery failure is an <strong>EIS representation problem, not a model problem</strong>; the BPNN architecture is cleared</td>
      <td>same</td>
    </tr>
    <tr>
      <td><strong>17</strong></td>
      <td>EarlyStopping + ModelCheckpoint (I1)</td>
      <td>EarlyStopping verified (AE stops at 129&ndash;192 epochs); ModelCheckpoint demonstrated: best weights saved at epoch 325/355, reloaded, metrics reproduce exactly (test RMSE 2.5210, R&sup2; 0.9402)</td>
      <td><code>checkpoints/</code>, <code>step17_checkpoint.py</code></td>
    </tr>
    <tr>
      <td><strong>18</strong></td>
      <td>Reconstruct all results with the corrected pipeline</td>
      <td>This report + the regenerated figures below</td>
      <td><code>figures/</code></td>
    </tr>
  </tbody>
</table>

<div class="page-break"></div>

<!-- ==================== PAGE 4: SECTION 2 HEADLINE RESULTS (FIGURES R1 & R2) ==================== -->
<h2 class="section-title">2. Headline result (Step 18 figure)</h2>

<div class="figure-container">
  <div class="figure-card">
    <img src="REPLACE_IMG_R1" alt="Figure R1: Per-fold test R2">
    <div class="figure-caption">
      <strong>Figure R1.</strong> Per-fold test R&sup2; under the corrected nested-LOBO protocol (mean of 3 seeds). The old collapse (R&sup2; &asymp; 0 or negative everywhere) is removed on three folds by the corrected EIS protocol, and on all four folds by time-domain features. Reference: raw measured data (Steps 1&ndash;4); time-domain features carry the exact same-cycle capacity label.
    </div>
  </div>
</div>

<div class="figure-container">
  <div class="figure-card" style="text-align: center;">
    <img src="REPLACE_IMG_R2" class="ranking-img" alt="Figure R2: Overall test RMSE ranking">
    <div class="figure-caption">
      <strong>Figure R2.</strong> Overall test RMSE (%SOH, mean &plusmn; std over 12 runs). Time-domain features halve the best EIS error.
    </div>
  </div>
</div>

<div class="page-break"></div>

<!-- ==================== PAGE 5: SECTION 2B EVIDENCE (FIGURES F1 & F2) ==================== -->
<h2 class="section-title">2b. Steps 1&ndash;6 evidence (figures reconstructed from verified raw data)</h2>

<div class="figure-container">
  <div class="figure-card" style="text-align: center;">
    <img src="REPLACE_IMG_F1" class="nyquist-img" alt="Figure F1: Raw Nyquist 4 spectra">
    <div class="figure-caption">
      <strong>Figure F1.</strong> Raw measured EIS points (no interpolation) for 4 spectra across 3 batteries, connected in the verified frequency order (Steps 3&ndash;4, A7).
    </div>
  </div>
</div>

<div class="figure-container">
  <div class="figure-card">
    <img src="REPLACE_IMG_F2" alt="Figure F2: B0005 cycle 41 3-plot diagnostic">
    <div class="figure-caption">
      <strong>Figure F2.</strong> B0005 cycle 41: raw points only / points connected in array order / interpolation overlay (Steps 3&ndash;4, A3, M-C).
    </div>
  </div>
</div>

<div class="page-break"></div>

<!-- ==================== PAGE 6: SECTION 2B EVIDENCE CONT. (FIGURES F3 & F4) ==================== -->
<h2 class="section-title">2b. Steps 1&ndash;6 evidence (Cont.)</h2>

<div class="figure-container">
  <div class="figure-card">
    <img src="REPLACE_IMG_F3" alt="Figure F3: Interpolation overshoot worst-case">
    <div class="figure-caption">
      <strong>Figure F3.</strong> Worst cubic-spline spectrum vs Linear/Cubic/PCHIP (Step 5, A8): cubic overshoots beyond the full reactive signal span; PCHIP stays inside the chord envelope.
    </div>
  </div>
</div>

<div class="figure-container">
  <div class="figure-card">
    <img src="REPLACE_IMG_F4" alt="Figure F4: Figure 6 recheck">
    <div class="figure-caption">
      <strong>Figure F4.</strong> Figure 6 recheck (Step 6, H2): the AE reconstructs the interpolated input target (grey), not the measurement (black markers).
    </div>
  </div>
</div>

<div class="page-break"></div>

<!-- ==================== PAGE 7: AE RECONSTRUCTION METRICS & SECTION 2C ABLATIONS ==================== -->
<h2 class="section-title">2b. Steps 1&ndash;6 evidence (Cont.)</h2>

<h3 class="subsection-title">Expanded AE reconstruction metrics (Part D3)</h3>

<table class="data-table">
  <thead>
    <tr>
      <th style="width: 20%;">Battery</th>
      <th style="width: 25%;">Re(Z) RMSE (&plusmn; std, Ohm)</th>
      <th style="width: 25%;">Im(Z) RMSE (&plusmn; std, Ohm)</th>
      <th style="width: 15%;">nRMSE</th>
      <th style="width: 15%;">Relative error % (&plusmn; std)</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Train B0005</td>
      <td>0.00111 &plusmn; 0.00028</td>
      <td>0.00023 &plusmn; 0.00007</td>
      <td>0.064</td>
      <td>22.2 &plusmn; 24.7</td>
    </tr>
    <tr style="background-color: #fef2f2;">
      <td>Train B0006</td>
      <td><strong>0.01461</strong> &plusmn; 0.00234</td>
      <td>0.00090 &plusmn; 0.00016</td>
      <td>0.519</td>
      <td>58.2 &plusmn; 64.4</td>
    </tr>
    <tr>
      <td>Val B0007</td>
      <td>0.00163 &plusmn; 0.00087</td>
      <td>0.00027 &plusmn; 0.00009</td>
      <td>0.075</td>
      <td>27.7 &plusmn; 41.0</td>
    </tr>
    <tr>
      <td>Test B0018</td>
      <td>0.00129 &plusmn; 0.00030</td>
      <td>0.00034 &plusmn; 0.00009</td>
      <td>0.144</td>
      <td>23.3 &plusmn; 20.7</td>
    </tr>
  </tbody>
</table>

<p>
The B0006 anomaly appears in Re(Z) RMSE (&asymp;13&times; the other batteries) with identical scaling &mdash; consistent with the AE-specific latent degradation reported in Steps 6 and 9&ndash;10. High relative error percentages reflect the tiny absolute scale of this rectified arc (denominators of 1&ndash;6 mOhm), not large absolute errors.
</p>

<h2 class="section-title" style="margin-top: 18px;">2c. Ablations (Part F3 / I3) &mdash; completed</h2>

<p>
All previously pending ablations are now executed under the corrected nested protocol (full tables in <code>Steps_F3_I3_B7_Ablations.md</code>):
</p>

<table class="data-table">
  <thead>
    <tr>
      <th style="width: 32%;">Ablation</th>
      <th style="width: 68%;">Result</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>AE bottleneck sizes {3, 7, 17, 37, 67}</td>
      <td>RMSE 8.30&ndash;8.82 %SOH, all within 1 std &mdash; indistinguishable; 17 retained</td>
    </tr>
    <tr>
      <td>BPNN loss MSE/MAE/Huber (I3)</td>
      <td>RMSE 8.32&ndash;8.57, indistinguishable &mdash; no loss changes the conclusion</td>
    </tr>
    <tr>
      <td>Interpolation 6 grid&times;method configs</td>
      <td>RMSE 7.99&ndash;8.62, indistinguishable &mdash; cubic's Step-5 overshoot has no measured downstream penalty; PCHIP kept for shape preservation</td>
    </tr>
  </tbody>
</table>

<div class="text-card">
<strong>B7 supporting evidence (added):</strong> Pipeline E fusion (time-domain + causal backward-aligned EIS latent) reaches R&sup2; <strong>+0.726</strong>, positive on <strong>all four folds including B0018 (+0.67)</strong>, and beats every EIS-only pipeline &mdash; the EIS latent adds value only when anchored by time-domain features. AE applied to time-domain features also does not help (R&sup2; +0.43 vs +0.85 for raw TD features). The complete pipeline ranking across 10 tested configurations: <strong>TD-BPNN (3.59) &gt; TD-Ridge (4.35) &gt; E-fusion (4.89) &gt; EIS pipelines (8.3&ndash;8.6) &gt; Mean (11.5)</strong>.
</div>

<div class="page-break"></div>

<!-- ==================== PAGE 8: SECTION 3, 4, 5, 6 ==================== -->
<h2 class="section-title">3. Findings for the advisor's decision (B7)</h2>

<p>
The measured evidence orders the three information sources cross-battery: <strong>time-domain &gt; EIS(PCA) &gt; EIS(raw) &asymp; EIS(AE)</strong>. Three constructive directions remain open, per the advisor's B5/B7 framing &mdash; the choice is an advisor-level decision:
</p>

<ol>
  <li><strong>Pipeline E fusion</strong> (time-domain + EIS features in one model; Part B5 optional row).</li>
  <li><strong>AE applied to time-domain features</strong> (keeps the thesis architecture "Two-Stage AE + BPNN", changes the input modality; the current AE-on-EIS result becomes the ablation evidence that motivated it).</li>
  <li><strong>EIS as a secondary/complementary modality</strong> with the amplitude domain shift documented (Steps 9&ndash;10: per-row normalization rescues B0018 but costs the other folds).</li>
</ol>

<p>
Supporting evidence collected for that discussion: the B0006 AE-specific degradation (Step 6/9&ndash;10), the B0018 amplitude domain shift (Step 9&ndash;10 P1n), and the B6 verdict above.
</p>

<h2 class="section-title" style="margin-top: 14px;">4. Declared limitations</h2>

<ul>
  <li>Per-point EIS frequencies are not recoverable from the distributed <code>.mat</code>; the interpolation grid rests on the documented 0.1 Hz&ndash;5 kHz sweep (declared assumption, Step 1&ndash;2).</li>
  <li>Time-domain features describe a completed discharge cycle &mdash; practical for cycle-level SOH logging (the BMS records every V/I/T cycle), not a mid-discharge estimator; the full BMS practicality comparison (Part J) is delivered in <code>Part_J_BMS_Practicality.md</code>.</li>
  <li>ICA/DVA and pulse-resistance features were not built (granularity insufficient) &mdash; declared, not skipped.</li>
  <li>SOH can exceed 100% by up to 0.8% (measurement variability vs the early-life reference); B0006 fades to 57% (NASA ran past EOL) &mdash; data kept as measured.</li>
  <li>Gate breaches in individual runs were disclosed in each step report (Steps 7&ndash;10) and none of the working-fold conclusions depend on them.</li>
</ul>

<h2 class="section-title" style="margin-top: 14px;">5. Ablation log (summary)</h2>

<p>
<code>eis_raw</code> &rarr; <code>step5_6</code> &rarr; <code>step7_8</code> &rarr; <code>step9_10</code> &rarr; <code>step12</code> &rarr; <code>step14_16</code> (full lines in <code>USER.md</code> / step reports)
</p>

<h2 class="section-title" style="margin-top: 14px;">6. Artifacts</h2>

<table class="data-table" style="margin-bottom: 4px;">
  <thead>
    <tr>
      <th style="width: 35%;">Folder</th>
      <th style="width: 65%;">Content</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>Autoencoder/eis_verify/</code></td>
      <td>Steps 1&ndash;6: verification scripts, raw Nyquist figures, verified dataset, <code>EIS_Raw_Verification.md</code>, <code>Interpolation_Reeval.md</code></td>
    </tr>
    <tr>
      <td><code>Autoencoder/nested_lobo/</code></td>
      <td>Steps 7&ndash;17: mapped datasets, harnesses, all results CSVs, gates, probes, checkpoint, step reports, <code>figures/</code> (this report's images)</td>
    </tr>
    <tr>
      <td><code>NASA DataSet/1. BatteryAgingARC-FY08Q4/</code></td>
      <td>Original raw NASA battery aging records, tracked in version control since Steps 1&ndash;4.</td>
    </tr>
  </tbody>
</table>

<div class="doc-footer">
  <span>State-of-Health (SOH) Estimation Using Two-Stage Autoencoder and BPNN &bull; Progress Report (Round 2)</span>
  <span>Author: Graduate Researcher &bull; Evaluation Date: 2026-09-25</span>
</div>

</body>
</html>
'''

def main():
    fig_dir = r'C:\Master Degree\Thesis\Autoencoder\nested_lobo\figures'
    fig_map = {
        'REPLACE_IMG_R1': 'R1_per_fold_R2.png',
        'REPLACE_IMG_R2': 'R2_rmse_ranking.png',
        'REPLACE_IMG_F1': 'A7_Raw_Nyquist_4spectra.png',
        'REPLACE_IMG_F2': 'A3_B0005_cycle41_3plots.png',
        'REPLACE_IMG_F3': 'Step5_overshoot_worst_case.png',
        'REPLACE_IMG_F4': 'Step6_Fig6_recheck.png',
    }

    final_html = html_template
    for placeholder, fname in fig_map.items():
        p = os.path.join(fig_dir, fname)
        if os.path.exists(p):
            with open(p, 'rb') as f:
                b64 = 'data:image/png;base64,' + base64.b64encode(f.read()).decode('utf-8')
            final_html = final_html.replace(placeholder, b64)
            print(f'Embedded figure: {fname}')
        else:
            print(f'WARNING: Figure not found: {p}')

    out_html = r'C:\Master Degree\Thesis\Autoencoder\nested_lobo\Progress_Report_Steps1-18.html'
    with open(out_html, 'w', encoding='utf-8') as f:
        f.write(final_html)
    print(f'Wrote HTML: {out_html} ({os.path.getsize(out_html)} bytes)')

    out_pdf = r'C:\Master Degree\Thesis\Autoencoder\nested_lobo\Progress_Report_Steps1-18.pdf'
    edge_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'

    cmd = [
        edge_path,
        '--headless=new',
        '--disable-gpu',
        '--run-all-compositor-stages-before-draw',
        '--no-pdf-header-footer',
        f'--print-to-pdf={out_pdf}',
        f'file:///{out_html.replace(os.sep, "/")}'
    ]

    print('Converting HTML to PDF via Edge headless...')
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f'Error running Edge: {res.stderr}')
        return

    if os.path.exists(out_pdf):
        size = os.path.getsize(out_pdf)
        print(f'SUCCESS! Created PDF: {out_pdf} ({size} bytes)')
        import pypdf
        reader = pypdf.PdfReader(out_pdf)
        print(f'Total Pages in PDF: {len(reader.pages)}')
    else:
        print('PDF file was not created.')

if __name__ == '__main__':
    main()
