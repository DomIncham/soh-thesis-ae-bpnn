# Advisor Directives — SOH Estimation of Li-Ion Batteries via Two-Stage AE + BPNN

> **Single Source of Truth.** All advisor comments, rules, prohibitions, and required steps.  
> **Update:** Append only. Each new round extends this file.

---

## Advisor's Core Principles (Apply to All Decisions)

### The 4-Rule Justification Framework
Every design choice — method, parameter, network structure, preprocessing technique, or evaluation strategy — must be defended with:

1. **Options considered:** What alternatives were evaluated?
2. **Suitability:** Why is the selected method appropriate for this problem?
3. **Quantitative evidence:** What metrics/experiments support the choice?
4. **Side-effect check:** Does the choice affect data leakage, generalization, or real-time implementation?

These justifications must appear in the Methodology and Experimental Setup sections of the final paper — not only in presentations.

### Cardinal Rule: Do Not Assume — Compare
> **"Do not first decide that a method is correct and then find a reason to support it. Every important design choice should be supported by comparison, validation, or quantitative evidence."**

### Critical Principle: PCA Variance ≠ SOH Relevance
> **"High PCA variance does not necessarily mean high relevance to SOH. A component with large variance may not be important for battery degradation, while a component with smaller variance may still contain useful SOH information."**  
> PCA variance retention is a **data compression metric**, not a **feature relevance metric**. The final bottleneck must be selected by downstream SOH prediction performance, not by PCA explained variance alone.

---

### Permanently Forbidden (Advisor has rejected these — never repeat)

| # | Forbidden Claim/Action | Correct Alternative |
|---|---|---|
| 1 | "AE bottleneck = 9 because PCA retains 99% variance" — PCA ≠ AE; different dimensionality-reduction mechanisms | Bottleneck selected via inner-validation on downstream SOH metrics |
| 2 | "Cubic Spline preserves the true physical shape" — Cubic Spline can produce overshoot; does not guarantee physical correctness | "PCHIP was selected because it avoided the overshoot observed with Cubic Spline and better preserved the local shape of measured EIS points" |
| 3 | "Moving Average causes data leakage" — only true for centered (future-peeking) MA; causal MA does not leak | "Any smoothing method using future-cycle information would compromise real-time prediction" |
| 4 | "Perfect reconstruction" without quantitative evidence | Report MSE/RMSE/MAE for train/val/unseen-test, with mean ± std |
| 5 | "The AE is the root cause of the correlation flip" — causality not proven | "AE latent representation exhibits instability under unseen battery domain" (latent feature instability / cross-battery domain shift) |
| 6 | "Mean Prediction Trap" (informal terminology) | "Prediction collapse toward a near-constant value" or "regression toward the mean" |
| 7 | PCHIP interpolated curves are "ground truth" | Only raw measured EIS points are experimental reference; PCHIP = fewer interpolation artifacts relative to measured points |
| 8 | Locking bottleneck at 17 based on PCA 95% variance alone | PCA provides an initial candidate; final bottleneck selected by inner-validation performance |
| 9 | 300 epochs = no overfitting | Implement EarlyStopping with ModelCheckpoint based on inner-validation loss |
| 10 | "Capacity fluctuations are caused by rest-time recovery or sensor error" — unless NASA documentation confirms | "Capacity fluctuations **may be associated with** recovery effects, measurement variability, or other experimental factors" |
| 11 | B0018 as permanent held-out test set without rotation → turns it into development data | Complete 4-fold LOBO: B0005, B0006, B0007, B0018 each serve as unseen test in turn |
| 12 | Tolerance=3 selected based on data retention rate only (99.89%) | Compare Tolerance=1,2,3 using **downstream SOH metrics** (MAE, RMSE, R²) |
| 13 | "Shallow Network + L2 Regularization will force smooth monotonic degradation" — L2 prevents large weights, not non-monotonicity | Select architecture and L2 coefficient through validation experiments |
| 14 | EIS is assumed to be the best input for SOH | Must establish time-domain baseline and compare under identical protocol |
| 15 | Smoothing applied to make Nyquist plots "look better" | Smoothing an incorrectly processed signal only produces a smoother incorrect signal |

### Style & Language Rules

- **English level:** A2-B1. Short sentences (Subject-Verb-Object). Remove all unnecessary adverbs.
- **No overclaiming.** Every statement must be supported by quantitative evidence.
- **Never treat interpolation outputs as physical ground truth.** Only raw measured points are experimental reference.
- **When evidence is insufficient:** use "may be associated with" / "potentially related to" / "suggests the possibility of."
- **Confidence language:** "is observed," "the results indicate," NOT "proves," "confirms," "guarantees."
- **Standard metrics required for all experiments:** MAE, RMSE, R².
- **For AE reconstruction:** add Re(Z) RMSE, Im(Z) RMSE, Normalized RMSE, and relative error (Mean ± Std).

---

## Round 1 (Previous Review)
**Date Received:** Before 2026-09-02  
**Status:** ✅ All resolved in Progress Report 2026-09-02

### R1-C1: AE Bottleneck Size Selection
- **Advisor's Directive:** PCA 9 components → 99% variance does not mathematically prove AE bottleneck = 9. PCA and AE are different dimensionality-reduction methods. Compare sizes (5, 7, 9, 12, 15, 20) and evaluate final SOH prediction performance.
- **Resolution:** Conducted ablation study of 108 configurations with bottleneck sizes 1, 3, 7, 17, 37, 67 — evaluating downstream SOH prediction.
- **Status:** ✅ Resolved

### R1-C2: Data Leakage and Causal Mapping
- **Advisor's Directive:** Avoid random mixing of cycles from same battery into train/test. Use battery-level validation (Leave-One-Battery-Out). EIS ↔ Capacity mapping must not use future cycles. All scalers/PCA must fit on training data only. **If some cycles do not contain EIS measurements, explain how they are handled** — this defines the input-output relationship of the entire AI pipeline.
- **Resolution:** Implemented Strict LOBO (Train: B0005, 06, 07; Test: B0018). Created Causal Backward Mapping with 3-cycle tolerance.
- **Status:** ✅ Resolved

### R1-C3: Moving Average Justification
- **Advisor's Directive:** Do not say "Moving Average causes data leakage" (causal MA does not). Explain why preserving raw temporal fluctuation is suitable for real-time SOH.
- **Resolution:** Explained that capacity fluctuations represent physical battery recovery during rest periods. Smoothed data creates synthetic trend unusable by real-time BMS.
- **Status:** ✅ Resolved

### R1-C4: Interpolation and Physical Validity
- **Advisor's Directive:** "Cubic Spline preserves the true physical shape" is too strong. Compare Linear, Cubic, PCHIP on linear/log grids. Check for overshoot.
- **Resolution:** Compared Linear, Cubic, PCHIP. Selected Log-PCHIP to prevent Cubic Spline overshoot.
- **Status:** ✅ Resolved

### R1-C5: AE Reconstruction Claims
- **Advisor's Directive:** Do not claim "perfect reconstruction." Provide quantitative metrics (MSE/RMSE/MAE) for train, validation, and unseen test.
- **Resolution:** Reported Mean RMSE for Train, Val, B0018 — revealing domain shift despite low RMSE.
- **Status:** ✅ Resolved

### R1-C6: Latent Space Diagnostics
- **Advisor's Directive:** Do not only observe sawtooth patterns. Analyze whether latent variables contain useful SOH information using Pearson/Spearman correlation. **Also examine the correlation among the latent nodes themselves** — to determine whether the AE extracts independent, meaningful degradation-related features rather than simply compressing EIS data redundantly.
- **Resolution:** Calculated correlations; discovered "Correlation Flip" anomaly between Train and Unseen Test.
- **Status:** ✅ Resolved

### R1-C7: BPNN Baseline Metrics
- **Advisor's Directive:** Report MAE, RMSE, **and R²** for every LOBO test result and all subsequent ablation studies.
- **Status:** ✅ Resolved

### R1 Priority Sequence (from Round 1)
1. Confirm data split → eliminate leakage
2. Confirm EIS-Capacity/SOH mapping + interpolation
3. Establish BPNN baseline → report MAE/RMSE/R²
4. Perform bottleneck + regularization ablation
5. Finalize AE + BPNN configurations for paper

---

## Round 2 (Current — Received 2026-09-02)
**Status:** ⏳ NOT YET ADDRESSED — Requires complete pipeline freeze and data verification

---

### PART A: Raw EIS Data Verification (HIGHEST PRIORITY — Must Do First)

> **Advisor's Warning:** "If the EIS input itself is unreliable, then further optimization of AE or BPNN will not solve the fundamental problem."  
> **"Before optimizing the model, we must first prove that the EIS input itself is correct."**

#### A1: Verify Original NASA EIS Variables
- Identify exact original variables from `.mat` files used to construct Re(Z), Im(Z), -Im(Z), Frequency.
- Show mapping: `Original NASA variable → complex impedance → Re(Z)/Im(Z) → CSV`.
- Confirm correct impedance variable extracted; no sign, scaling, or conversion error.

#### A2: Recover and Verify True Measurement Frequency Vector
- Each EIS point should conceptually be: `{f_i, Re(Z_i), Im(Z_i)}`.
- Confirm actual measurement frequency is available from original NASA data.
- Do NOT assume CSV row order = frequency order unless verified.
- If frequency info was lost when creating CSV → regenerate EIS dataset preserving frequency column.
- New dataset format: `Battery, Cycle, Frequency, Re(Z), -Im(Z)`

#### A3: Verify Frequency Ordering of EIS Points
- For **one representative example** (e.g., B0005 Cycle 41), show ALL raw EIS points ordered by **actual measured frequency**.
- Provide table: `Point, Frequency, Re(Z), -Im(Z)`.
- Create 3 plots:
  1. Raw measured EIS points only
  2. Raw points connected according to actual frequency order
  3. Raw points + Linear/Cubic/PCHIP interpolation overlay
- **Critical:** If points are connected by CSV row/index instead of frequency → Nyquist becomes irregular → entire preprocessing pipeline may be invalid.

#### A4: Confirm All 39 Points Belong to Same EIS Spectrum
- Verify for each spectrum: same Battery ID, same EIS measurement/cycle, correct number of frequency points, no mixing between different measurements.

#### A5: EIS Data Quality Checklist
Before any interpolation, check raw EIS data for:
- NaN values
- Inf values
- Missing frequency points
- Duplicated frequencies
- Duplicated impedance values
- Inconsistent frequency ordering
- Abnormal jumps or isolated outliers
- Correct units (Ω vs mΩ)
- Correct sign convention for Im(Z) and -Im(Z)

Summarize how many samples are affected by each issue. **Do NOT remove or smooth points only because Nyquist looks unattractive** — any removal rule must have clear, reproducible justification.

#### A6: Two Possible Cases
- **Case 1:** Raw Nyquist becomes reasonable after correct frequency ordering → current preprocessing/ordering was likely incorrect.
- **Case 2:** Correctly ordered original NASA EIS points are still highly irregular → determine whether irregularity comes from original measurement, measurement noise, or specific impedance variable.

#### A7: Redraw Figures 3 & 4 with Verified Raw EIS
- Redraw Nyquist plots using verified raw EIS data **without interpolation** first.
- Clearly identify: measured data vs interpolated data.
- Define the reference used in each figure.

#### A8: Reevaluate Interpolation Methods
- **Only after** Steps A1-A7 are confirmed → repeat Linear/Cubic/PCHIP comparison.
- If overshoot is confirmed after verification: "PCHIP was selected because it avoided overshoot observed with Cubic Spline and better preserved local shape of measured points."
- Add quantitative measure of interpolation distortion/overshoot if possible — not visual inspection alone.

---

### PART B: Time-Domain Baseline (FUNDAMENTAL DIRECTION — Possibly Redirect Research)

> **Advisor's Directive:** "At this stage, we should not assume that EIS is necessarily the best input for SOH estimation."

#### B1: Do Not Assume EIS Outperforms Time-Domain
- EIS is attractive because impedance at different frequencies may contain electrochemical degradation information.
- However, this advantage only exists if EIS measurement is **reliable and consistently available**.
- For practical BMS: V(t), I(t), T(t) are already measured during normal operation → may be more stable.

#### B2: Check Whether NASA Has Time-Domain Data
- Verify availability of: V(t), I(t), T(t) from NASA dataset.
- If available → construct time-domain baseline **before** any complex DL model.

#### B3: Extract Time-Domain Features
Possible features (if data available):
- Charging duration within a fixed voltage interval
- CC charging time
- CV charging time
- Current decay during CV charging
- Voltage slope
- Discharge duration
- Voltage recovery after rest
- Pulse resistance (if current-step data available)
- ICA/DVA features (if data quality sufficient)

#### B4: Build Simple Baselines First
- `Time-domain features → Linear/Ridge Regression → SOH`
- `Time-domain features → BPNN → SOH`
- Do not start with complex models.

#### B5: Four Pipelines to Compare (Identical Protocol)
All must use the same: LOBO evaluation, inner validation, SOH definition, train/test batteries, metrics.

| Pipeline | Description |
|---|---|
| **A** | Time-domain features → BPNN → SOH |
| **B** | Raw/processed EIS → BPNN → SOH |
| **C** | PCA-EIS → BPNN → SOH |
| **D** | AE-EIS → BPNN → SOH |

Later investigation (optional):
| **E** | Time-domain + EIS feature fusion → SOH |

#### B6: Use Time-Domain to Diagnose EIS Problems
- If under same LOBO protocol: R²_time-domain ≫ 0 while R²_EIS < 0 → problem is unlikely BPNN architecture → EIS data representation, preprocessing, or cross-battery consistency is problematic.
- If corrected EIS pipeline performs well after frequency verification → stronger evidence for EIS-based approach.

#### B7: Broader Research Question
> **Reframe:** *"Which type of battery health information provides the most reliable cross-battery SOH estimation: time-domain features, EIS frequency-domain features, or their combination?"*

This is more fundamental and meaningful than comparing AE bottleneck sizes.

---

### PART C: Nested 4-Fold LOBO Protocol (CRITICAL — Structural Rework Required)

#### C1: Current Problem
- B0018 has been used repeatedly to compare: interpolation methods, bottleneck sizes, L2 regularization, loss functions, and other choices.
- B0018 is gradually becoming **development data** instead of a completely untouched test battery.

#### C2: Required Protocol
- **Outer LOBO:** Each of B0005, B0006, B0007, B0018 serves as unseen test battery in turn (4 folds).
- **Inner validation:** Used for model and hyperparameter selection (within training folds).
- **All design choices** (bottleneck size, L2, epochs, mapping tolerance) must be determined **without using the outer test battery**.
- No hyperparameter may be selected using the battery assigned as the outer test fold.

#### C3: Final Report Format
- Report results as **mean ± standard deviation across the LOBO folds**.
- If possible, across multiple random seeds.

---

### PART D: Metrics Standardization (%SOH)

#### D1: SOH Definition
$$SOH_k = \frac{Q_k}{Q_{reference}} \times 100\%$$

- Clearly explain how Q_reference is determined for each battery.
- Main results in **%SOH**, not Ah (capacity can be reported additionally).

#### D2: Required Metrics for Every Experiment
1. MAE (%SOH)
2. RMSE (%SOH)
3. R²

#### D3: AE Reconstruction Metrics (Expanded)
- Re(Z) RMSE
- Im(Z) RMSE
- Normalized RMSE
- Relative reconstruction error (Mean ± Std)
- Report for each battery separately
- Show representative reconstruction plots from more than one cycle and more than one battery

---

### PART E: Causal Mapping — Tolerance Ablation (Rigorous Evaluation Required)

#### E1: Current Problem
Tolerance = 3 selected based solely on data retention rate (99.89%). This proves data quantity, not label accuracy.

#### E2: Required Comparison
Compare Tolerance = 1, 2, 3 using:
- Retention rate
- **Downstream MAE**
- **Downstream RMSE**
- **Downstream R²**

Also report the actual EIS-to-capacity cycle-gap distribution.

#### E3: Important Note
A 3-cycle backward match does not cause future-data leakage, but may still introduce label misalignment.

---

### PART F: BPNN & Ablation Baselines (4 Additional Baselines Required)

#### F1: Required Baselines
All must use identical LOBO split, inner validation, data mapping, preprocessing, SOH definition, BPNN procedure, and metrics:

1. **Mean Predictor:** 
   $$\hat{SOH} = \text{mean SOH of training set}$$
   or
   $$\hat{Q} = \text{mean capacity of training set}$$

2. **Linear Regression / Ridge Regression:** Simple baselines.

3. **Raw EIS → BPNN** (bypass AE entirely).

4. **PCA → BPNN** (linear feature extraction vs AE's nonlinear).

#### F2: Key Question to Answer
> *"Does the AE actually improve SOH prediction, or does it make cross-battery generalization worse?"*

#### F3: Planned Ablation Studies for Final Paper
| Ablation | What it Tests |
|---|---|
| Raw EIS → BPNN | Baseline with no feature extraction |
| PCA → BPNN | Linear dimensionality reduction |
| AE → BPNN | Nonlinear feature extraction |
| Different AE bottleneck sizes | Optimal latent dimensionality |
| Different interpolation methods | Data preprocessing impact |
| BPNN with/without L2 regularization | Regularization effect |
| Tolerance = 1, 2, 3 | Mapping accuracy impact |

---

### PART G: Figure 10 — Prediction Collapse Analysis

#### G1: Current State
- Ground-truth capacity decreases with cycling.
- Predicted result remains almost flat near a constant value.
- RMSE ≈ 0.1744 Ah, R² ≈ -0.029.
- **This is a failed prediction, not a successful degradation model.**

#### G2: Required Investigation
- Why does prediction collapse toward a nearly constant value?
- Compare AE-BPNN directly with Mean Predictor on: MAE, RMSE, R², and prediction trajectory.
- If AE-BPNN ≈ Mean Predictor → model learned **zero** degradation information.

#### G3: Bottleneck=1 Warning
- Do NOT describe bottleneck=1 as "best model" because it gives lowest RMSE.
- A model with lower RMSE is useless for SOH if it does not follow degradation trajectory.

---

### PART H: Overclaiming — Interpretation Corrections

#### H1: Terminology Changes Required

| Current (Wrong) | Correct |
|---|---|
| "Correlation Flip proves AE is root cause" | "AE latent representation exhibits instability under unseen battery domain" |
| "Mean Prediction Trap" | "Prediction collapse toward a near-constant value" |
| "Capacity fluctuations caused by rest-time recovery" | "Capacity fluctuations may be associated with recovery effects, measurement variability, or other experimental factors" |
| "PCHIP preserves the true physical shape" | "PCHIP produces fewer interpolation artifacts relative to the measured EIS points" |
| "Bottleneck is locked at 17" | "PCA suggests 17 as initial candidate based on 95% cumulative variance; final bottleneck selected by inner-validation" |
| "Cubic Spline preserves true physical shape" | "Cubic Spline introduces overshoot; PCHIP selected to avoid this artifact" |
| "300 epochs guarantees no overfitting" | "Early Stopping with ModelCheckpoint based on inner-validation loss" |

#### H2: Figure 6 Clarification
- Black curve in Figure 6 = preprocessed/interpolated AE input target — **not** independent physical ground truth.
- Logic chain: `Measured EIS points → interpolation → AE input → AE reconstruction`.
- If interpolation is incorrect → good AE reconstruction means AE successfully reconstructs an incorrectly processed signal.

#### H3: Latent Feature Attribution
- Do NOT attribute observed "correlation flip" to AE until EIS frequency information, Nyquist plotting, interpolation, and evaluation protocol are verified.
- Pipeline of potential failure: `Incorrect EIS extraction/order → incorrect EIS representation → unstable AE features → poor BPNN prediction`.
- The correlation flip may be a **consequence of earlier preprocessing problem**, not the original cause.

---

### PART I: Early Stopping & Training Protocol

#### I1: Replace Fixed Epoch Claims
- Convergence ≈ 300 epochs does NOT prove no overfitting.
- Implement: `EarlyStopping(monitor='val_loss', patience=N)` with `ModelCheckpoint(save_best_only=True)`.
- Different model configurations may require different numbers of epochs.

#### I2: BPNN Architecture Selection
- L2 regularization reduces model complexity — does NOT guarantee smooth or monotonic output.
- Shallow network reduces overfitting risk — does NOT guarantee ignoring temporal noise.
- Number of hidden layers, neurons, and L2 coefficient must be selected through validation experiments.

#### I3: Loss Function Comparison
- Compare MSE, MAE, Huber Loss — especially if capacity data contain local fluctuations or outliers.
- MAE/Huber may provide more direct way of reducing sensitivity to abnormal fluctuations without future-cycle information.

---

### PART J: BMS Practicality Discussion

When claiming real-time BMS suitability, compare:
- Measurement requirements
- Computational complexity
- Required sensors/hardware
- Online feasibility
- Sensitivity to operating conditions

A practical BMS already measures V(t), I(t), T(t) during normal operation. Full EIS measurement may require additional excitation, frequency-domain processing, or dedicated measurement procedures.

---

### PART K: Transfer Learning Gate (DO NOT PROCEED YET)

> **"Please do not move to Transfer Learning until we know whether the current cross-battery failure comes from the EIS data, the feature representation, or the prediction model."**

Transfer Learning is only justified after:
1. EIS quality verified
2. Time-domain baseline established
3. Time-domain vs EIS compared
4. Feature extraction methods evaluated
5. Feature fusion considered
6. Root cause of generalization failure identified

---

### PART L: The Required 18-Step Sequence (FOR NEXT PROGRESS REPORT)

> **Advisor's Mandate:** "Please do not move to Transfer Learning yet. For the next progress report, please confirm the issues in the following order:"

| Step | Task | Dependency |
|---|---|---|
| **1** | Verify original NASA EIS frequency information | — |
| **2** | Verify raw EIS points ordered correctly by frequency | Step 1 |
| **3** | Redraw Figures 3 & 4 using verified raw EIS | Steps 1-2 |
| **4** | Clearly identify measured data vs interpolated data; define reference per figure | Step 3 |
| **5** | Reevaluate Linear, Cubic, PCHIP **only after** raw Nyquist is confirmed | Steps 1-4 |
| **6** | Recheck Figure 6 using corrected preprocessing pipeline | Steps 1-5 |
| **7** | Establish complete nested 4-fold LOBO protocol | Steps 1-6 |
| **8** | Reevaluate mapping tolerance using downstream MAE, RMSE, R² | Step 7 |
| **9** | Compare: Raw EIS→BPNN, PCA→BPNN, and AE→BPNN | Steps 7-8 |
| **10** | Add Mean Predictor and Linear/Ridge Regression baselines | Step 9 |
| **11** | Report MAE (%SOH), RMSE (%SOH), R² for every unseen battery | Steps 7-10 |
| **12** | Explain Figure 10 quantitatively — why prediction collapses toward constant | Steps 9-11 |
| **13** | Report final results as mean ± std across LOBO folds (and across random seeds if possible) | Steps 7-12 |
| **14** | Establish time-domain baseline (if NASA data available) | Steps 1-2 |
| **15** | Compare time-domain vs EIS pipelines under identical protocol | Step 14 |
| **16** | Justify EIS vs time-domain choice with experimental evidence | Steps 14-15 |
| **17** | Implement EarlyStopping + ModelCheckpoint | Step 9 |
| **18** | Reconstruct all figures/results using corrected pipeline | Steps 1-17 |

---

### PART M: Additional EIS Extraction Verification (7 Supplementary Steps)

From the supplementary EIS Data Extraction document — must be done **before** continuing interpolation/AE/BPNN:

| Step | Task |
|---|---|
| **A** | Identify exact original NASA impedance variables (show mapping to CSV) |
| **B** | Confirm actual measurement frequency available from original data |
| **C** | For B0005 Cycle 41: show table of raw points ordered by frequency + 3 diagnostic plots |
| **D** | Confirm all 39 points belong to same EIS spectrum (no mixing between measurements) |
| **E** | Check for: NaN, Inf, missing/duplicated frequencies, abnormal jumps, wrong units, wrong sign convention |
| **F** | Do NOT apply smoothing to make Nyquist "look better" — smoothing incorrect signal = smoother incorrect signal |
| **G** | Distinguish Case 1 (correct ordering fixes it) vs Case 2 (NASA data itself is irregular) |
| **H** | This issue may also explain Figure 10 poor result: `Incorrect EIS → incorrect representation → unstable AE → poor BPNN` |

---

## Experiment Pipelines — Summary for Final Paper

All under identical protocol (outer LOBO, inner validation, same SOH definition, same metrics):

| Pipeline | Input | Feature Extraction | Regressor |
|---|---|---|---|
| **Baseline 1 (Mean)** | — | — | Mean(SOH_train) |
| **Baseline 2 (Linear)** | Time-domain features | — | Linear/Ridge Regression |
| **Pipeline A** | Time-domain features | — | BPNN |
| **Pipeline B** | Verified raw EIS | — | BPNN |
| **Pipeline C** | Verified EIS | PCA (linear) | BPNN |
| **Pipeline D** | Verified EIS | AE (nonlinear) | BPNN |
| **Pipeline E** | Time-domain + EIS fusion | TBD | BPNN |

---

## Research Sequence (Not to Be Skipped or Reordered)

```
Verify EIS quality (Steps 1-4, A-H)
    │
    ▼
Establish time-domain baseline (Step 14)
    │
    ▼
Compare time-domain vs EIS (Step 15)
    │
    ▼
Evaluate feature extraction methods (Steps 9-10)
    │
    ▼
Consider feature fusion (Pipeline E)
    │
    ▼
[Only then] Consider Transfer Learning
```

---

## Key Principle — Repeated by Advisor in Both Rounds

> **"Before optimizing the model, we must first prove that the input itself is correct."**
> 
> **"Do not assume that the AE is the problem until the original EIS frequency information, Nyquist plotting, interpolation procedure, and evaluation protocol have all been verified."**
>
> **"Let the experimental evidence determine whether time-domain features, EIS features, or multi-domain fusion should become the main direction of the study."**

---

*Last updated: 2026-09-20 — All Round 1 + Round 2 comments consolidated.*
*Next update: Append Round 3 as new section.*