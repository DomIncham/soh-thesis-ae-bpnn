import os
import sys
import base64
import subprocess

html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>State-of-Health (SOH) Estimation — Progress Report (Round 2)</title>
<style>
  @page {
    size: A4 portrait;
    margin: 16mm 18mm 18mm 18mm;
  }
  
  *, *:before, *:after {
    box-sizing: border-box;
  }

  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    color: #1e293b;
    background-color: #ffffff;
    line-height: 1.55;
    font-size: 13.5pt; /* Requested font size 13-15 pt */
    margin: 0;
    padding: 0;
  }

  /* Document Header Banner */
  .doc-header {
    border-bottom: 3px solid #1e3a8a;
    padding-bottom: 12px;
    margin-bottom: 16px;
  }
  .doc-banner-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 8px;
  }
  .thesis-title-badge {
    font-size: 12.5pt;
    font-weight: 800;
    color: #1e3a8a;
    letter-spacing: 0.2px;
    line-height: 1.35;
    flex: 1;
  }
  .badge-status {
    background-color: #dcfce7;
    color: #15803d;
    padding: 4px 12px;
    border-radius: 9999px;
    font-size: 10.5pt;
    font-weight: 800;
    border: 1.5px solid #86efac;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    white-space: nowrap;
  }
  h1.doc-title {
    font-size: 21pt;
    font-weight: 850;
    color: #0f172a;
    margin: 8px 0 6px 0;
    line-height: 1.25;
    letter-spacing: -0.4px;
  }
  .doc-subtitle {
    font-size: 13.5pt;
    color: #475569;
    margin: 0;
    font-weight: 500;
    line-height: 1.4;
  }

  /* Meta Cards Grid */
  .meta-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
    margin: 16px 0;
  }
  .meta-card {
    background: #f8fafc;
    border: 1.5px solid #e2e8f0;
    border-radius: 8px;
    padding: 10px 12px;
  }
  .meta-label {
    font-size: 10pt;
    font-weight: 700;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 2px;
  }
  .meta-value {
    font-size: 13pt;
    color: #0f172a;
    font-weight: 750;
    line-height: 1.3;
  }
  .meta-sub {
    font-size: 10.5pt;
    color: #64748b;
    margin-top: 2px;
  }

  /* Executive Summary Box */
  .exec-summary {
    background: linear-gradient(135deg, #f0fdf4 0%, #f8fafc 100%);
    border: 1.5px solid #bbf7d0;
    border-left: 5px solid #16a34a;
    border-radius: 8px;
    padding: 14px 18px;
    margin: 16px 0;
    break-inside: avoid;
    page-break-inside: avoid;
  }
  .exec-title {
    font-size: 13.5pt;
    font-weight: 850;
    color: #14532d;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .exec-list {
    margin: 0;
    padding-left: 20px;
    font-size: 12.5pt;
    color: #1e293b;
    line-height: 1.5;
  }
  .exec-list li {
    margin-bottom: 6px;
  }

  /* Protocol Rigor Box */
  .protocol-box {
    background: #f8fafc;
    border: 1.5px solid #cbd5e1;
    border-left: 5px solid #2563eb;
    border-radius: 8px;
    padding: 12px 16px;
    margin: 16px 0;
    break-inside: avoid;
    page-break-inside: avoid;
  }
  .protocol-title {
    font-size: 12.5pt;
    font-weight: 800;
    color: #1e3a8a;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 6px;
  }
  .protocol-list {
    margin: 0;
    padding-left: 20px;
    font-size: 11.5pt;
    color: #334155;
    line-height: 1.45;
  }
  .protocol-list li {
    margin-bottom: 4px;
  }

  /* Section Titles */
  h2.section-title {
    font-size: 16pt;
    font-weight: 850;
    color: #1e3a8a;
    border-bottom: 2px solid #cbd5e1;
    padding-bottom: 4px;
    margin: 24px 0 12px 0;
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    break-after: avoid;
    page-break-after: avoid;
  }
  h2.section-title .section-tag {
    font-size: 10.5pt;
    font-weight: 700;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  h3.subsection-title {
    font-size: 13.5pt;
    font-weight: 800;
    color: #0f172a;
    margin: 16px 0 8px 0;
    break-after: avoid;
    page-break-after: avoid;
  }

  /* Tables */
  table.data-table {
    width: 100%;
    border-collapse: collapse;
    margin: 12px 0 16px 0;
    font-size: 11pt;
    background: #ffffff;
    border: 1.5px solid #cbd5e1;
    border-radius: 6px;
  }
  table.data-table thead {
    display: table-header-group;
    background: #f1f5f9;
  }
  table.data-table th {
    font-weight: 800;
    color: #0f172a;
    padding: 8px 8px;
    text-align: left;
    border-bottom: 2px solid #94a3b8;
    border-right: 1px solid #e2e8f0;
    font-size: 10.5pt;
    text-transform: uppercase;
    letter-spacing: 0.3px;
  }
  table.data-table th:last-child {
    border-right: none;
  }
  table.data-table td {
    padding: 7px 8px;
    border-bottom: 1px solid #e2e8f0;
    border-right: 1px solid #e2e8f0;
    vertical-align: top;
    line-height: 1.38;
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

  /* Badges */
  .pill {
    display: inline-block;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 9.5pt;
    font-weight: 800;
    white-space: nowrap;
    line-height: 1.2;
  }
  .pill-green {
    background: #dcfce7;
    color: #15803d;
    border: 1px solid #86efac;
  }
  .pill-blue {
    background: #dbeafe;
    color: #1d4ed8;
    border: 1px solid #93c5fd;
  }
  .pill-amber {
    background: #fef3c7;
    color: #b45309;
    border: 1px solid #fde68a;
  }
  .pill-red {
    background: #fee2e2;
    color: #b91c1c;
    border: 1px solid #fca5a5;
  }
  .pill-slate {
    background: #f1f5f9;
    color: #475569;
    border: 1px solid #cbd5e1;
  }

  /* Figure Containers */
  .fig-card {
    background: #ffffff;
    border: 1.5px solid #cbd5e1;
    border-radius: 8px;
    padding: 8px 10px;
    margin: 10px 0 14px 0;
    break-inside: avoid;
    page-break-inside: avoid;
  }
  .fig-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin: 10px 0 14px 0;
  }
  .fig-card-header {
    font-size: 11.5pt;
    font-weight: 800;
    color: #1e3a8a;
    margin-bottom: 6px;
  }
  .fig-card img {
    width: 100%;
    height: auto;
    display: block;
    border-radius: 5px;
    border: 1px solid #e2e8f0;
    background-color: #ffffff;
  }
  .fig-caption {
    font-size: 11pt;
    color: #475569;
    margin-top: 6px;
    line-height: 1.35;
    font-style: italic;
  }
  .fig-caption strong {
    color: #0f172a;
    font-style: normal;
  }

  /* Callout boxes */
  .callout {
    border-radius: 8px;
    padding: 10px 14px;
    margin: 12px 0 16px 0;
    font-size: 12.5pt;
    line-height: 1.45;
    break-inside: avoid;
    page-break-inside: avoid;
  }
  .callout-info {
    background: #eff6ff;
    border: 1.5px solid #bfdbfe;
    border-left: 4.5px solid #2563eb;
    color: #1e3a8a;
  }
  .callout-warning {
    background: #fffbeb;
    border: 1.5px solid #fef3c7;
    border-left: 4.5px solid #d97706;
    color: #92400e;
  }

  /* Ranking Banner */
  .ranking-banner {
    background: #0f172a;
    color: #ffffff;
    border-radius: 8px;
    padding: 10px 14px;
    margin: 12px 0 16px 0;
    text-align: center;
    font-size: 12.5pt;
    font-weight: 750;
    line-height: 1.4;
    break-inside: avoid;
    page-break-inside: avoid;
  }
  .ranking-banner span.metric {
    color: #38bdf8;
    font-weight: 850;
  }

  /* Decision Cards */
  .decision-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
    margin: 12px 0 16px 0;
  }
  .decision-card {
    background: #ffffff;
    border: 1.5px solid #cbd5e1;
    border-top: 3.5px solid #2563eb;
    border-radius: 8px;
    padding: 10px 10px;
    break-inside: avoid;
    page-break-inside: avoid;
  }
  .decision-card.featured {
    border-top: 3.5px solid #16a34a;
    background: #f0fdf4;
    border-color: #86efac;
  }
  .decision-tag {
    font-size: 10pt;
    font-weight: 800;
    text-transform: uppercase;
    color: #2563eb;
    margin-bottom: 3px;
  }
  .decision-card.featured .decision-tag {
    color: #16a34a;
  }
  .decision-title {
    font-size: 12pt;
    font-weight: 850;
    color: #0f172a;
    margin-bottom: 4px;
    line-height: 1.25;
  }
  .decision-body {
    font-size: 10.5pt;
    color: #334155;
    line-height: 1.35;
  }

  /* Limitations List */
  .limits-list {
    margin: 8px 0;
    padding-left: 22px;
    font-size: 12pt;
    color: #334155;
    line-height: 1.45;
  }
  .limits-list li {
    margin-bottom: 6px;
  }

  /* Page Break Utility */
  .page-break {
    page-break-after: always;
    break-after: page;
  }
  .avoid-break {
    page-break-inside: avoid;
    break-inside: avoid;
  }

  /* Document Footer */
  .doc-footer {
    border-top: 1.5px solid #cbd5e1;
    padding-top: 8px;
    margin-top: 24px;
    font-size: 10pt;
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

<!-- ==================== COVER & OVERVIEW ==================== -->
<div class="doc-header">
  <div class="doc-banner-top">
    <div class="thesis-title-badge">
      State-of-Health (SOH) Estimation of Lithium-Ion Batteries Using Two-Stage Autoencoder and BPNN
    </div>
    <div class="badge-status">PROGRESS REPORT (ROUND 2) &bull; ALL 18 STEPS COMPLETED</div>
  </div>
  <h1 class="doc-title">EIS Verification &rarr; Pipeline Comparison &rarr; Time-Domain Benchmark</h1>
  <div class="doc-subtitle">A Rigorous 18-Step Systematic Investigation under Strict Nested 4-Fold LOBO Cross-Validation</div>
</div>

<div class="meta-grid">
  <div class="meta-card">
    <div class="meta-label">Evaluation Date</div>
    <div class="meta-value">2026-09-25</div>
    <div class="meta-sub">Milestone Round 2 Delivery</div>
  </div>
  <div class="meta-card">
    <div class="meta-label">Dataset Verification</div>
    <div class="meta-value">NASA ARC-FY08Q4</div>
    <div class="meta-sub">B0005, B0006, B0007, B0018</div>
  </div>
  <div class="meta-card">
    <div class="meta-label">Validation Protocol</div>
    <div class="meta-value">Nested 4-Fold LOBO</div>
    <div class="meta-sub">Unseen test + Inner-val tuning</div>
  </div>
  <div class="meta-card">
    <div class="meta-label">Leakage Controls</div>
    <div class="meta-value">100% Structural PASS</div>
    <div class="meta-sub">Perturbation diff &le; 3.8e-05</div>
  </div>
</div>

<div class="exec-summary">
  <div class="exec-title">&#9733; Executive Summary &amp; Core Scientific Breakthroughs</div>
  <ul class="exec-list">
    <li><strong>Time-Domain Modality Superiority:</strong> The Time-Domain BPNN (TD-BPNN) achieves an overall <strong>RMSE of 3.59 %SOH</strong> and <strong>R&sup2; = +0.85</strong>, maintaining strong positive R&sup2; across <strong>all four batteries</strong> (including out-of-distribution B0018 with R&sup2; = +0.79). TD features cut the best EIS prediction error in half.</li>
    <li><strong>Root Cause of EIS Cross-Battery Failure:</strong> The persistent negative R&sup2; on B0018 in EIS models (&minus;1.0 to &minus;1.2) is definitively diagnosed as an <strong>EIS representation &amp; amplitude domain shift problem</strong> rather than a neural model capacity flaw. The BPNN architecture is fully cleared.</li>
    <li><strong>Zero Data Leakage Guarantee:</strong> Full nested LOBO protocol enforced. Strict structural assertions and outer-test feature perturbation probes confirmed zero information leakage across fold boundaries.</li>
  </ul>
</div>

<div class="protocol-box">
  <div class="protocol-title">&#9881; Methodological Integrity &amp; Strict Protocol Controls</div>
  <ul class="protocol-list">
    <li><strong>Nested 4-Fold LOBO:</strong> Each battery (B0005, B0006, B0007, B0018) serves as the completely unseen outer test in turn. Inner validation selects all model hyperparameters.</li>
    <li><strong>Ground Truth SOH Calculation:</strong> SOH in % with \(Q_{\text{ref}}\) defined rigorously as the mean capacity of the first 5 discharge cycles. Target standardization computed on fold-train only.</li>
    <li><strong>Deterministic Leakage Probes:</strong> Feature perturbation probes (outer test &times; 2 &rarr; retrain &rarr; verify train metrics do not move) passed with max delta &le; 3.8e-05 (one probe exactly 0).</li>
    <li><strong>Statistical Convergence:</strong> EarlyStopping on inner-validation loss, ModelCheckpoint weight preservation, and aggregation over 12 independent runs (4 folds &times; 3 seeds: 42, 7, 123).</li>
  </ul>
</div>

<div class="page-break"></div>

<!-- ==================== SECTION 1: MASTER STATUS ==================== -->
<h2 class="section-title">
  <span>1. Master Status of the 18-Step Sequence</span>
  <span class="section-tag">Advisor Part A &ndash; J Full Audit</span>
</h2>

<table class="data-table">
  <thead>
    <tr>
      <th style="width: 8%;">Step</th>
      <th style="width: 24%;">Task / Advisor Part</th>
      <th style="width: 48%;">Key Results &amp; Quantitative Findings</th>
      <th style="width: 20%;">Evidence &amp; Artifact</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>1&ndash;2</strong></td>
      <td>Verify NASA EIS variables &amp; freq ordering (A1&ndash;A2, M-A/B)</td>
      <td>CSV matches <code>Rectified_Impedance</code> exactly on all 34,593 rows (diff &lt; 1e-15 &Omega;). Row order consistent with low&rarr;high frequency (887/887 spectra). Flat Nyquist arc is an inherent property of NASA rectified data (max |Im| &asymp; 2&ndash;6 m&Omega;).</td>
      <td><span class="pill pill-green">Verified</span> <code>EIS_Raw_Verification.md</code></td>
    </tr>
    <tr>
      <td><strong>3&ndash;4</strong></td>
      <td>Frequency-ordered table, plots &amp; integrity (A3&ndash;A5, M-C/D)</td>
      <td>39 pts &times; 887 spectra = 34,593 CSV rows; timestamps strictly monotonic; 0 NaN/Inf/duplicates; no isolated outlier points detected.</td>
      <td><span class="pill pill-green">PASS</span> <code>A3_*_3plots.png</code>, <code>A7_*</code></td>
    </tr>
    <tr>
      <td><strong>5</strong></td>
      <td>Re-evaluate interpolation with quantitative metric (A8)</td>
      <td>Chord-envelope overshoot: <strong>PCHIP: 0 in all 1,774 checks</strong>. Cubic spline overshoots by 0.25&ndash;1.76 m&Omega; (worst 11.2 m&Omega;, exceeding total reactive span). Linear also 0 but lacks C&sup1; smoothness.</td>
      <td><span class="pill pill-blue">PCHIP Standard</span> <code>Interpolation_Reeval.md</code></td>
    </tr>
    <tr>
      <td><strong>6b</strong></td>
      <td>Expanded AE reconstruction metrics (D3)</td>
      <td>Re(Z) / Im(Z) RMSE separated + nRMSE + relative error per battery. <strong>B0006 anomaly isolated:</strong> Re(Z) RMSE = 14.6 m&Omega; (&sim;13&times; higher than B0005/07/18).</td>
      <td><span class="pill pill-amber">Anomaly Found</span> <code>ae_reconstruction_d3_metrics.csv</code></td>
    </tr>
    <tr>
      <td><strong>6</strong></td>
      <td>Recheck Figure 6 reconstruction target (H2)</td>
      <td>AE strictly reconstructs the <strong>interpolated input target</strong>, not the raw discrete measurement points. B0006 anomaly is confirmed to be AE-specific.</td>
      <td><span class="pill pill-green">Clarified</span> <code>Step6_Fig6_recheck.png</code></td>
    </tr>
    <tr>
      <td><strong>7</strong></td>
      <td>Nested 4-fold LOBO implementation (C1&ndash;C3)</td>
      <td>Fully implemented. Outer unseen test + inner validation fold for hyperparameter selection. Zero leakage verified via perturbation probes.</td>
      <td><span class="pill pill-green">Zero Leakage</span> <code>Steps_7_8_Nested_LOBO.md</code></td>
    </tr>
    <tr>
      <td><strong>8</strong></td>
      <td>Tolerance 1/2/3 downstream evaluation (E1&ndash;E3)</td>
      <td>Downstream RMSE (8.57&ndash;8.89 %SOH) is statistically indistinguishable within 1 std. Pre-declared protocol rule selects <strong>Tolerance 1</strong>. Bimodal gap reported.</td>
      <td><span class="pill pill-blue">Tol 1 Selected</span> <code>Steps_7_8_Nested_LOBO.md</code></td>
    </tr>
    <tr>
      <td><strong>9</strong></td>
      <td>Raw EIS / PCA / AE &rarr; BPNN comparison (F1.3&ndash;4)</td>
      <td>On working folds, <strong>PCA achieves best performance (RMSE 5.92, R&sup2; +0.61)</strong>. AE loses to PCA across all three working folds.</td>
      <td><span class="pill pill-blue">PCA &gt; AE</span> <code>Steps_9_10_Baselines.md</code></td>
    </tr>
    <tr>
      <td><strong>10</strong></td>
      <td>Mean &amp; Linear regression baselines (F1.1&ndash;2)</td>
      <td>Trivial mean predictor marks the baseline floor (R&sup2; &minus;0.77). 256-dim Ridge is fragile across fold domain shifts.</td>
      <td><span class="pill pill-slate">Floor Set</span> <code>Steps_9_10_Baselines.md</code></td>
    </tr>
    <tr>
      <td><strong>11</strong></td>
      <td>Per-fold MAE/RMSE/R&sup2; for every battery (D2)</td>
      <td>Full per-fold performance disclosed transparently across all tested configurations.</td>
      <td><span class="pill pill-green">Completed</span> Disclosed in reports</td>
    </tr>
    <tr>
      <td><strong>12</strong></td>
      <td>Explain Figure 10 collapse quantitatively (G1&ndash;G3)</td>
      <td>Old RMSE = 1.126 &times; std(y) &rarr; flatline prediction (12.6% worse than trivial mean). Root cause: latent correlation flip + unstandardized targets + fixed epochs.</td>
      <td><span class="pill pill-red">Root Cause Found</span> <code>Steps_12_Fig10_Collapse.md</code></td>
    </tr>
    <tr>
      <td><strong>13</strong></td>
      <td>Mean &plusmn; Std aggregation across folds &amp; seeds (C3)</td>
      <td>All reported summary metrics computed across 12 independent runs (4 folds &times; 3 seeds: 42, 7, 123).</td>
      <td><span class="pill pill-green">Stat. Rigor</span> 12 runs/model</td>
    </tr>
    <tr>
      <td><strong>14&ndash;15</strong></td>
      <td>Time-domain baseline &amp; comparison (B1&ndash;B5)</td>
      <td><strong>TD-BPNN: RMSE 3.59 %SOH, R&sup2; +0.85</strong>. Positive on ALL four folds including B0018 (+0.79). EIS pipelines negative on B0018 (&minus;1.0 to &minus;1.2).</td>
      <td><span class="pill pill-green">TD Winner</span> <code>Steps_14_16_TimeDomain.md</code></td>
    </tr>
    <tr>
      <td><strong>16</strong></td>
      <td>Justify EIS vs Time-Domain scientifically (B6)</td>
      <td>Direct confirmation of B6 criterion: R&sup2;<sub>time</sub> &gt;&gt; 0 while R&sup2;<sub>EIS</sub> &lt; 0 &rarr; cross-battery failure is an <strong>EIS representation problem</strong>, not BPNN model capacity.</td>
      <td><span class="pill pill-green">BPNN Cleared</span> <code>Steps_14_16_TimeDomain.md</code></td>
    </tr>
    <tr>
      <td><strong>17</strong></td>
      <td>EarlyStopping &amp; ModelCheckpoint validation (I1)</td>
      <td>EarlyStopping validated (AE stops at 129&ndash;192 epochs). ModelCheckpoint verified: best weights saved at epoch 325/355, exact metric reproducibility (RMSE 2.5210).</td>
      <td><span class="pill pill-green">Reproducible</span> <code>checkpoints/</code></td>
    </tr>
    <tr>
      <td><strong>18</strong></td>
      <td>Reconstruct complete pipeline results</td>
      <td>Unified master report synthesis + all regenerated figures and tables.</td>
      <td><span class="pill pill-green">Delivered</span> <code>figures/</code>, this report</td>
    </tr>
  </tbody>
</table>

<div class="page-break"></div>

<!-- ==================== SECTION 2: HEADLINE RESULTS ==================== -->
<h2 class="section-title">
  <span>2. Headline Comparative Results (Step 18 Visual Synthesis)</span>
  <span class="section-tag">Cross-Modality Benchmark</span>
</h2>

<div class="fig-grid">
  <div class="fig-card">
    <div class="fig-card-header">Figure R1: Per-Fold Generalization (Test R&sup2;)</div>
    <img src="REPLACE_IMG_R1" alt="Figure R1: Per-Fold Test R2">
    <div class="fig-caption">
      <strong>Figure R1.</strong> Per-fold test R&sup2; under corrected nested-LOBO (mean of 3 seeds). Corrected EIS resolves the collapse on B0005, B0006, and B0007. Time-domain features achieve strong positive R&sup2; across <em>all four folds</em> including the difficult B0018 (+0.79).
    </div>
  </div>

  <div class="fig-card">
    <div class="fig-card-header">Figure R2: Overall Test Error Ranking (RMSE %SOH)</div>
    <img src="REPLACE_IMG_R2" alt="Figure R2: Overall RMSE Ranking">
    <div class="fig-caption">
      <strong>Figure R2.</strong> Overall test RMSE in %SOH (mean &plusmn; std across 12 runs). Time-domain features (3.59 %SOH) cut error in half compared to the best EIS pipeline (8.30 %SOH). Both dramatically outperform trivial mean prediction (11.5 %SOH).
    </div>
  </div>
</div>

<div class="ranking-banner">
  Empirical Performance Hierarchy: <br>
  TD-BPNN (<span class="metric">3.59</span>) &gt; TD-Ridge (<span class="metric">4.35</span>) &gt; Pipeline E Fusion (<span class="metric">4.89</span>) &gt; EIS Pipelines (<span class="metric">8.3&ndash;8.6</span>) &gt; Trivial Mean (<span class="metric">11.5</span>)
</div>

<!-- ==================== SECTION 2B: RAW EIS & RECONSTRUCTION ==================== -->
<h2 class="section-title">
  <span>2b. Experimental Evidence: Raw EIS Spectra &amp; Interpolation Audit</span>
  <span class="section-tag">Steps 1&ndash;6 Data Verification</span>
</h2>

<div class="fig-grid">
  <div class="fig-card">
    <div class="fig-card-header">Figure F1: Verified Raw Nyquist Spectra (Steps 3&ndash;4)</div>
    <img src="REPLACE_IMG_F1" alt="Figure F1: Raw Nyquist Spectra">
    <div class="fig-caption">
      <strong>Figure F1.</strong> Raw measured EIS points (no interpolation) across 4 spectra from 3 batteries, connected in verified low&rarr;high frequency order. Highlights the compressed reactive arc scale (2&ndash;6 m&Omega;).
    </div>
  </div>

  <div class="fig-card">
    <div class="fig-card-header">Figure F2: Sequence &amp; Interpolation Integrity (A3, M-C)</div>
    <img src="REPLACE_IMG_F2" alt="Figure F2: Cycle 41 3-Plot Diagnostic">
    <div class="fig-caption">
      <strong>Figure F2.</strong> Diagnostic for B0005 Cycle 41: raw points only (left), array order trajectory (center), and interpolation overlay (right), proving monotonic ordering without artifacts.
    </div>
  </div>
</div>

<div class="fig-grid">
  <div class="fig-card">
    <div class="fig-card-header">Figure F3: Interpolation Overshoot Quantification (Step 5, A8)</div>
    <img src="REPLACE_IMG_F3" alt="Figure F3: Interpolation Overshoot">
    <div class="fig-caption">
      <strong>Figure F3.</strong> Worst-case cubic spline overshoot vs. Linear and PCHIP. Cubic spline creates spurious oscillations up to 11.2 m&Omega; (exceeding total reactive span), whereas PCHIP remains strictly shape-preserving (0 overshoot).
    </div>
  </div>

  <div class="fig-card">
    <div class="fig-card-header">Figure F4: Autoencoder Reconstruction Target Verification (Step 6)</div>
    <img src="REPLACE_IMG_F4" alt="Figure F4: AE Reconstruction Recheck">
    <div class="fig-caption">
      <strong>Figure F4.</strong> Autoencoder reconstruction vs. interpolated target (grey line) vs. raw measured points (black dots). Proves the AE reconstructs the interpolated curve, with B0006 anomaly isolated to the AE representation.
    </div>
  </div>
</div>

<div class="avoid-break">
  <h3 class="subsection-title">Expanded Autoencoder Reconstruction Metrics (Part D3 Audit)</h3>
  <table class="data-table">
    <thead>
      <tr>
        <th style="width: 22%;">Battery Partition</th>
        <th style="width: 26%;">Re(Z) RMSE (&plusmn; std, &Omega;)</th>
        <th style="width: 24%;">Im(Z) RMSE (&plusmn; std, &Omega;)</th>
        <th style="width: 13%;">nRMSE</th>
        <th style="width: 15%;">Relative Error %</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>Train B0005</strong></td>
        <td>0.00111 &plusmn; 0.00028</td>
        <td>0.00023 &plusmn; 0.00007</td>
        <td>0.064</td>
        <td>22.2 &plusmn; 24.7 %</td>
      </tr>
      <tr style="background-color: #fef2f2;">
        <td><strong>Train B0006 (Anomaly)</strong></td>
        <td><strong style="color: #b91c1c;">0.01461 &plusmn; 0.00234</strong></td>
        <td>0.00090 &plusmn; 0.00016</td>
        <td><strong style="color: #b91c1c;">0.519</strong></td>
        <td>58.2 &plusmn; 64.4 %</td>
      </tr>
      <tr>
        <td><strong>Val B0007</strong></td>
        <td>0.00163 &plusmn; 0.00087</td>
        <td>0.00027 &plusmn; 0.00009</td>
        <td>0.075</td>
        <td>27.7 &plusmn; 41.0 %</td>
      </tr>
      <tr>
        <td><strong>Test B0018</strong></td>
        <td>0.00129 &plusmn; 0.00030</td>
        <td>0.00034 &plusmn; 0.00009</td>
        <td>0.144</td>
        <td>23.3 &plusmn; 20.7 %</td>
      </tr>
    </tbody>
  </table>

  <div class="callout callout-warning">
    <strong>Analytical Takeaway on B0006 Anomaly:</strong> The B0006 reconstruction anomaly manifests prominently in Re(Z) RMSE (&asymp;14.6 m&Omega;, roughly 13&times; higher than all other batteries). This directly accounts for the AE-specific latent space degradation identified in Steps 6 and 9&ndash;10. The high relative error percentages across all partitions reflect the miniature absolute scale of the NASA rectified impedance arc (denominators of only 1&ndash;6 m&Omega;).
  </div>
</div>

<div class="page-break"></div>

<!-- ==================== SECTION 2C & 3: ABLATIONS & ADVISOR PATHWAYS ==================== -->
<h2 class="section-title">
  <span>2c. Ablation Suite &amp; Multi-Modal Fusion (Parts F3, I3 &amp; B7)</span>
  <span class="section-tag">Ablation Findings</span>
</h2>

<table class="data-table">
  <thead>
    <tr>
      <th style="width: 25%;">Ablation Dimension</th>
      <th style="width: 40%;">Tested Configurations</th>
      <th style="width: 35%;">Empirical Finding &amp; Decision</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>AE Bottleneck Size</strong></td>
      <td>Latent dimensions &isin; {3, 7, 17, 37, 67}</td>
      <td>Downstream RMSE ranges 8.30&ndash;8.82 %SOH (all within 1 std). Indistinguishable; <strong>dimension 17 retained</strong>.</td>
    </tr>
    <tr>
      <td><strong>BPNN Loss Function (I3)</strong></td>
      <td>MSE, MAE, Huber Loss</td>
      <td>RMSE spans 8.32&ndash;8.57 %SOH (indistinguishable). Loss formulation does not overcome cross-battery EIS shift.</td>
    </tr>
    <tr>
      <td><strong>Interpolation Protocol</strong></td>
      <td>6 Grid &times; Method combinations</td>
      <td>Downstream RMSE ranges 7.99&ndash;8.62 %SOH (neutral impact). <strong>PCHIP retained</strong> for strict shape preservation.</td>
    </tr>
  </tbody>
</table>

<div class="callout callout-info">
  <strong>Key Finding on Multi-Modal Fusion (Pipeline E):</strong> Fusion of time-domain discharge features with causal, backward-aligned EIS latents reaches test <strong>R&sup2; = +0.726</strong>, remaining positive across <strong>all four folds including B0018 (+0.67)</strong>, outperforming every EIS-only pipeline. Autoencoder compression on time-domain features degrades accuracy (R&sup2; +0.43 vs. +0.85 for raw TD), showing that lossy compression hurts clean signals.
</div>

<h2 class="section-title">
  <span>3. Strategic Pathways for Advisor Consultation</span>
  <span class="section-tag">Thesis Scope Decision (Part B7)</span>
</h2>

<div class="decision-grid">
  <div class="decision-card featured">
    <div class="decision-tag">&#9733; Option 1 (Recommended)</div>
    <div class="decision-title">Pipeline E: Multi-Modal Fusion</div>
    <div class="decision-body">
      <strong>Concept:</strong> Fuse time-domain V/I/T features with backward-aligned EIS latents.<br><br>
      <strong>Strengths:</strong> Delivers R&sup2; = +0.726 (positive on all 4 folds including B0018). Preserves EIS investigation while achieving practical accuracy.<br><br>
      <strong>Thesis Impact:</strong> High novelty; demonstrates multi-modality synergy and solves domain shift.
    </div>
  </div>

  <div class="decision-card">
    <div class="decision-tag">Option 2 (Architecture Pivot)</div>
    <div class="decision-title">Two-Stage AE on Time-Domain</div>
    <div class="decision-body">
      <strong>Concept:</strong> Retain thesis architecture ("Two-Stage AE + BPNN"), pivot modality to time-domain.<br><br>
      <strong>Strengths:</strong> Preserves neural pipeline structure.<br><br>
      <strong>Tradeoff:</strong> Raw TD achieves R&sup2; = 0.85; AE compression yields R&sup2; = 0.43. EIS results serve as the ablation motivating the pivot.
    </div>
  </div>

  <div class="decision-card">
    <div class="decision-tag">Option 3 (Scientific Dissection)</div>
    <div class="decision-title">EIS with Domain-Shift Framing</div>
    <div class="decision-body">
      <strong>Concept:</strong> Keep EIS as primary modality; frame cross-battery amplitude shift as core finding.<br><br>
      <strong>Strengths:</strong> Documents why EIS fails cross-pack without per-cell recalibration.<br><br>
      <strong>Tradeoff:</strong> Requires accepting negative R&sup2; on B0018 unless row-wise normalization is used.
    </div>
  </div>
</div>

<div class="callout callout-info">
  <strong>Supporting Evidence Base for Advisor Consultation:</strong>
  (1) B0006 AE-specific degradation isolated in Re(Z) RMSE; 
  (2) B0018 cross-battery failure proven to stem from amplitude shift rather than network capacity; 
  (3) Formal Part B6 satisfaction confirming the BPNN architecture is cleared.
</div>

<!-- ==================== SECTION 4 & 5: LIMITATIONS & ARTIFACTS ==================== -->
<h2 class="section-title">
  <span>4. Declared Methodological Limitations</span>
  <span class="section-tag">Scientific Rigor &amp; Transparency</span>
</h2>

<ul class="limits-list">
  <li><strong>Unrecoverable Per-Point EIS Frequencies:</strong> Frequencies absent from NASA's distributed <code>.mat</code>; interpolation rests on documented 0.1 Hz &ndash; 5 kHz sweep (declared assumption).</li>
  <li><strong>Discharge Cycle Scope:</strong> Time-domain features reflect completed discharge profiles for cycle-level BMS logging rather than intra-discharge estimation (detailed in <code>Part_J_BMS_Practicality.md</code>).</li>
  <li><strong>Feature Granularity:</strong> ICA/DVA and pulse resistance omitted due to telemetry sampling limitations; declared proactively rather than skipped.</li>
  <li><strong>Capacity Reference Boundaries:</strong> SOH temporarily exceeds 100% by up to 0.8% due to early-life relaxation; B0006 degrades to 57% as testing continued past standard EOL.</li>
  <li><strong>Disclosure of Gate Breaches:</strong> Mild gate breaches in individual non-working runs disclosed in step reports; no working conclusions depend on breached runs.</li>
</ul>

<h2 class="section-title" style="margin-top: 20px;">
  <span>5. Repository Artifacts &amp; Deliverables</span>
  <span class="section-tag">Code &amp; Data Provenance</span>
</h2>

<table class="data-table">
  <thead>
    <tr>
      <th style="width: 32%;">Directory Path</th>
      <th style="width: 68%;">Artifact Scope &amp; Deliverables</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>Autoencoder/eis_verify/</code></td>
      <td>Steps 1&ndash;6 verification codebase, raw Nyquist generation scripts, verified dataset, <code>EIS_Raw_Verification.md</code>, <code>Interpolation_Reeval.md</code>.</td>
    </tr>
    <tr>
      <td><code>Autoencoder/nested_lobo/</code></td>
      <td>Steps 7&ndash;18 execution engine, mapped datasets, result CSVs, leakage probes, ModelCheckpoint weights, step reports, and <code>figures/</code>.</td>
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

    final_html = html_content
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
