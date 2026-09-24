# Steps 14–16: Time-Domain Baseline vs EIS Pipelines (advisor Part B, B6 verdict)

**Date:** 2026-09-25
**Scope:** Steps 14 (time-domain baseline), 15 (time-domain vs EIS under identical protocol), 16 (justify the choice with evidence) — plus the concluding section of Step 12 (cross-ref: `Steps_12_Fig10_Collapse.md`).
**Protocol:** identical nested 4-fold LOBO (inner val = first remaining battery, tolerance-1 EIS rows, %SOH, fold-train-only scaling and target standardization, EarlyStopping, seeds 42/7/123 → 12 runs per pipeline, 60 total).
**TD features (8, from raw `.mat` discharge + preceding charge cycles):** discharge duration, mean voltage, mean temperature, voltage slope, CC duration, CV duration, CV current decay slope, charge mean temperature. Label alignment is **exact** — capacity is measured in the same discharge cycle, so no tolerance mapping is needed (the E2 misalignment concern does not apply to this modality).

---

## 1. Validity Gate

| Gate | Result |
|---|---|
| 1. Rows | 60/60 ✓ |
| 2. NaN | 0 ✓ |
| 3. R² bounds | −1.696 … +0.972 — inside [−2, 1] ✓ (no breaches) |
| 4. Coverage | 3 per (pipeline × battery) ✓ |
| 5. mean ± std | below ✓ |
| 6. Leakage probe (`probe_s14.py`, TD-BPNN selected config) | PASS — diff = 0.00e+00; TD-Ridge is deterministic (identical rows across seeds) |

## 2. Results (%SOH, mean ± std over 12 runs)

| Pipeline | Test MAE | Test RMSE | Test R² | nRMSE |
|---|---|---|---|---|
| B1 Mean predictor | 9.815 | 11.482 | −0.348 | 0.359 |
| P1 Raw EIS → BPNN | 6.830 | 8.321 | +0.096 | 0.267 |
| P3 AE → BPNN | 7.007 | 8.566 | +0.080 | 0.270 |
| TD Ridge | 3.821 | 4.350 | +0.797 | 0.128 |
| **TD BPNN** | **3.013** | **3.590** | **+0.848** | **0.106** |

### Per fold — test R² (the advisor's B6 pattern, verbatim)

| Fold | B1 | P1 Raw EIS | P3 AE | TD Ridge | TD BPNN |
|---|---|---|---|---|---|
| B0005 | −0.006 | 0.609 | 0.538 | 0.874 | **0.950** |
| B0006 | −0.581 | 0.330 | 0.064 | 0.592 | **0.686** |
| B0007 | −0.708 | 0.639 | 0.715 | 0.960 | **0.967** |
| **B0018** | −0.099 | **−1.192** | **−0.996** | **+0.763** | **+0.789** |

### Test RMSE per fold

| Fold | B1 | P1 Raw | P3 AE | TD Ridge | TD BPNN |
|---|---|---|---|---|---|
| B0005 | 10.338 | 6.054 | 6.550 | 3.665 | **2.279** |
| B0006 | 15.659 | 8.850 | 10.337 | 7.954 | **6.770** |
| B0007 | 11.140 | 4.547 | 4.140 | 1.699 | **1.556** |
| B0018 | 8.789 | 13.834 | 13.237 | 4.083 | **3.755** |

## 3. B6 verdict (the advisor's decision criterion, applied verbatim)

> *Advisor B6: "If under the same LOBO protocol: R²_time-domain ≫ 0 while R²_EIS < 0 → problem is unlikely BPNN architecture → EIS data representation, preprocessing, or cross-battery consistency is problematic."*

The measured pattern matches this criterion, and is stronger:

1. **Time-domain is positive on all four folds — including B0018** (TD-BPNN R² +0.65…+0.97; TD-Ridge +0.59…+0.96), where **both EIS pipelines are negative** (Raw −1.19, AE −1.00). Under the identical protocol, split, and metrics.
2. **Time-domain error is less than half of EIS error** overall (RMSE 3.59 vs 8.32/8.57 %SOH; nRMSE 0.106 vs 0.267).
3. Even on the three "working" EIS folds, TD beats EIS (working-fold R² 0.87 vs 0.53/0.44).

**Conclusion (Step 15–16, per B6):** the cross-battery generalization failure of the EIS pipeline is **not a model problem** — a simple Ridge on 8 time-domain features outperforms every EIS pipeline. The problem is in the EIS data representation for cross-battery transfer (amplitude domain shift being the measured candidate, Steps 9–10 P1n) and possibly in what NASA's rectified EIS retains after calibration. The BPNN architecture is thereby cleared.

## 4. What this means for the research question (advisor B7)

> *"Which type of battery health information provides the most reliable cross-battery SOH estimation: time-domain features, EIS frequency-domain features, or their combination?"*

On this dataset and protocol, the evidence orders them: **time-domain > EIS(raw/PCA/AE)**. Consequences for the thesis direction (for the advisor to decide):

- The EIS+AE storyline ("two-stage AE+BPNN on EIS") is currently the **weakest** of the tested pipelines cross-battery. PCA on EIS beats the AE (Steps 9–10), and time-domain beats both (this report).
- Constructive directions that keep the thesis structure: (a) **Pipeline E fusion** (time-domain + EIS features → one model, listed as optional in Part B5); (b) **AE applied to time-domain features** (keeps the two-stage AE+BPNN architecture, changes the input modality); (c) reframe EIS as a secondary/complementary modality with its domain-shift limitation documented.
- The choice among (a)/(b)/(c) is an advisor-level decision — the evidence for the discussion is complete in Steps 7–16.

## 5. Limitations and honest caveats

1. **TD features describe a completed discharge cycle** (duration, mean voltage, slope) — the same granularity as the capacity label itself. This is practical for cycle-level SOH logging (the BMS records every V/I/T cycle; advisor B1), but it does not estimate SOH mid-discharge. The EIS measurement is also post-hoc per cycle (dedicated sweep), so both modalities are cycle-level; neither is a mid-cycle estimator.
2. Charge-side features come from the **preceding** charge cycle only (causal; no future data).
3. ICA/DVA and pulse-resistance features were not built (data granularity insufficient) — declared, not silently skipped (Part B3).
4. The perturbation probe was run for TD-BPNN (PASS, diff 0); TD-Ridge is a closed-form deterministic method. EIS pipelines reuse the machinery already probed in Steps 9–10.
5. All conclusions are for the NASA 4-battery dataset under this protocol; no cross-dataset claim is made.

## 6. Step 12 conclusion (completing `Steps_12_Fig10_Collapse.md`)

With Steps 14–16 complete, the Figure 10 story closes: the old collapse was a **pipeline failure on an EIS representation that does not transfer across batteries** — established by three measurements: (a) the corrected protocol removes it on 3 of 4 folds (Step 12), (b) the remaining fold is rescued by time-domain features under the identical protocol (this report), and (c) the model itself is cleared (a linear model on 8 features solves what the AE+BPNN could not).

---

## Ablation log

`2026-09-25 | step14_16 | TD_bpnn R2 0.85, positive all 4 folds (B0018 +0.79) | B6 pattern: EIS representation problem; TD > EIS everywhere`

## Artifacts (`Autoencoder/nested_lobo/`)

| File | Purpose |
|---|---|
| `extract_time_features.py` → `time_domain_features.csv` | 636 rows, 8 TD features, exact capacity alignment |
| `steps14_16_td.py`, `steps14_16_results.csv` (60 rows), `steps14_16_summary.csv`, `s14_16_log.txt` | Pipelines and results |
| `gate_s14.py`, `probe_s14.py` | Validity gate + leakage probe (PASS) |
| `Steps_14_16_TimeDomain.md` | This report |