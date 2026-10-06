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
| 16 | "EIS + discharge features + cross-battery evaluation" claimed as our novelty — already published: Sardar et al. 2026, *Batteries* 12(8):291, DOI 10.3390/batteries12080291 (admits proxy leakage itself, no proxy-free version) | Target the proxy-free, partial-window, unseen-battery gap (R3-C4) |

### Style & Language Rules

- **English level:** A2-B1. Short sentences (Subject-Verb-Object). Remove all unnecessary adverbs.
- **No overclaiming.** Every statement must be supported by quantitative evidence.
- **Never treat interpolation outputs as physical ground truth.** Only raw measured points are experimental reference.
- **When evidence is insufficient:** use "may be associated with" / "potentially related to" / "suggests the possibility of."
- **Confidence language:** "is observed," "the results indicate," NOT "proves," "confirms," "guarantees."
- **Standard metrics required for all experiments:** MAE, RMSE, R².
- **For AE reconstruction:** add Re(Z) RMSE, Im(Z) RMSE, Normalized RMSE, and relative error (Mean ± Std).

---

## Round 3 (Current — Literature Gap Audit, Received 2026-09-26)
**Source:** `Comment Prof and Report/Literature_Gap_Audit_NASA_SOH.pdf` — Advisor's audit, basis: Round 2 Progress Report (2026-09-25) + 2022–2026 literature search.
**Status:** ⏳ NOT YET ADDRESSED
**Advisor's verdict:** No data-processing error found in our pipeline (capacity data matches original NASA files: 168/168/168/132 cycles; min SOH 69.9/57.2/74.4/72.9%). Our lower scores come from a **stricter protocol and different inputs, not mistakes**. Core message: convert our strictness into novelty.

### The 7 Score-Gap Factors (ordered by expected impact)
| # | Factor | Typical high-score papers | Us | Effect |
|---|---|---|---|---|
| 1 | Train/test split | Random or chronological split inside one battery | Nested LOBO — test battery never seen | **Largest.** Random → battery-wise dropped R² 0.979 → 0.786 [11] |
| 2 | Capacity-proxy inputs | Q(k−1) [3]; previous-cycle maximum capacity [4]; cycle number, discharge duration [11]; accumulated charge, cycle index [10] | TD feature list not yet audited | **Very large** — CC discharge: Capacity = I × t, model is given the answer |
| 3 | Training batteries | 34 NASA cells, 24 for training [13] | 4 batteries; final model may train on only 2 | Two batteries cannot represent cell-to-cell variation |
| 4 | Extrapolation | Not an issue with same-battery splits | B0006 falls to 57 %SOH (others stop 70–74%) | Chen et al. [9] (physics-consistent monotone LightGBM + covariance alignment + conformal; LOCO 2-train/1-test — closest to our conditions): B0006 only R² 0.25→0.53 |
| 5 | R² computation | One R² pooled over many batteries | Per battery (narrow SOH range, std 8–12 %SOH), then averaged | Pooling adds between-battery variance to the denominator → inflates R² at the same RMSE |
| 6 | SOH definition/units | Q/2.0 Ah nominal, Q/Q₀, or 0–1 fraction | Q/Qref (first 5 cycles), %SOH | RMSE 0.02 looks small but = only 1–2 %SOH; unify units first |
| 7 | Discharge cut-off voltages | No effect with same-battery splits | B0005 2.7 V / B0006 2.5 V / B0007 2.2 V / B0018 2.5 V | min-voltage, voltage-drop, duration features have different scales → domain shift |

### R3-C1: Evaluation Protocol Fixes (within 1 week; may improve scores without changing the model)
- **Advisor's Directive:** After inner validation selects hyperparameters, **re-fit the final model on ALL THREE training batteries** before testing. Alternative: make the inner loop a 3-fold LOBO. Expected to help the B0006 fold most.
- **Reporting standard:** R² both as per-fold mean AND pooled; RMSE in both %SOH and Ah; **add MAPE**. Unify units before any literature comparison.
- **Repository checks required (from audit):**
  - Does the TD model use all 636 discharge cycles, or only EIS-aligned cycles (tolerance=1 keeps ~51%)?
  - TD-Ridge RMSE 4.35 suggests full discharge duration is NOT an input — but every feature must still be listed and checked (R3-C3).
  - Confirm whether the model is re-fitted on all three training batteries after inner selection.

### R3-C2: Protocol-Gap Experiment (directly becomes a thesis section)
- With identical features and model, run three splits: (i) random, (ii) chronological within each battery, (iii) nested LOBO.
- Expected: random split reaches R² > 0.97 — quantifies how much published accuracy comes from the protocol alone.

### R3-C3: Target-Proxy Audit (MOST IMPORTANT scientific question)
- List every TD feature; label each `safe` or `proxy`. Proxies include: discharge duration, end-of-discharge time, ∫I dt (accumulated Ah), cycle index, previous-cycle capacity.
- Run three settings under the same nested LOBO × 3 seeds:

| Setting | Purpose |
|---|---|
| **TD-All** | Current feature set (for comparison) |
| **TD-Proxy-Free** | Honest unseen-battery capability |
| **Oracle-proxy** (I × t only) | Should reach R² ≈ 1 — explains where high published scores come from |

### R3-C4: Novelty Constraint — Closest Published Paper (Verified)
- **Sardar S. A. et al. 2026**, "Multi-Source Impedance and Discharge Feature Learning for Cross-Battery SOH Estimation of Lithium-Ion Batteries," *Batteries*, 12(8):291, DOI 10.3390/batteries12080291 (2026-08-06).
- NASA 34 cells / 1,830 EIS–SOH pairs; RF/ET/GB/HGB/XGBoost. Random: R² 0.979 / RMSE 2.18%. Strict battery-wise (7 unseen): R² 0.786 / RMSE 7.37%. Repeated battery-wise (5 partitions): R² 0.881 / RMSE 3.22% (RF).
- **Their features (audit Section 3 table):** EIS = Re/Im statistics, slopes, Nyquist area, resampled points, NASA-provided Re and Rct. TD = mean voltage, voltage drop, discharge duration, current/temperature, cycle number, EIS index. Stated limitations: discharge duration + cycle number act as indirect SOH proxies; EIS resampling not frequency-aligned.
- **Benchmark positioning (audit summary):** under a strict unseen-battery protocol with only B0005/06/07/18, recent 2026 papers report R² ≈ 0.53–0.88 and RMSE ≈ 4–7 %SOH; our TD-BPNN (R² ≈ 0.85, RMSE 3.59 %SOH) is at the same level or slightly better. However, R² 0.85 is NOT yet a novelty claim because: (1) TD features have not been audited for capacity proxies; (2) the final model may be trained on only two batteries; (3) [11] already combines EIS + discharge features + cross-battery evaluation.
- **They admit proxy leakage themselves** (discharge duration + cycle number) and do NOT report a proxy-free version → **this is the gap we target.**
- Conclusion: "EIS + discharge features + cross-battery evaluation" is already published — cannot be our novelty. Interim strengths (stricter nested protocol, PCHIP/frequency-assumption analysis, evidence EIS-only fails unseen batteries) show research quality but are not yet a new contribution.
- **Suggested thesis title:** *Proxy-Controlled, Cross-Battery SOH Estimation from Partial Charge/Discharge Windows: Quantifying the Protocol Gap on the NASA Dataset* ("Cross-Dataset" if cross-dataset validation succeeds).
- **Three claimable contributions:** (1) quantify how much published accuracy comes from protocol + capacity proxies (protocol-gap + oracle proxy); (2) unseen-battery accuracy under proxy-free, partial-window conditions; (3) cross-dataset validation.

### Literature Pattern — Comparison Table Digest (audit Section 4, 2022–2026)
Yellow rows in the audit = strict unseen-battery (LOBO/LOCO) protocol; green row = this thesis. Values below are transcribed from the audit PDF — verify against full texts per R3-C9 before citing.

| # | Study (journal, year) | Validation | Key reported result | Notes |
|---|---|---|---|---|
| 1 | Zhang D., TCN (Front. Energy Res., 2022) | Same battery, chronological (start cycle 90) | RMSE ≤1.80 %, MAE ≤1.46 % | NASA B5/7/18; temperature-variation-rate HI |
| 2 | Dong H., improved GPR (IJES, 2022) | Not stated | RMSE <1.5 % | dQ/dV, dV/dT; abstract-level info only |
| 3 | Xu G., STL-LSTM (PLOS ONE, 2024) | Same battery, first 50/70 % | RMSE ~0.016–0.019 Ah | Charge-time windows 3.9–4.0/4.0–4.1 V + Q(k−1) proxy |
| 4 | Giuliano A., Transformer TL (Energies, 2025) | Pre-train NASA → 1-epoch fine-tune Oxford | RMSE 0.0146 | NASA 34 cells; previous-cycle capacity proxy |
| 5 | Salem N., short-term discharge (Energy Reports, 2026) | Chronological 80/20, same battery | R² 0.90 (full) / 0.94 (10-min); RMSE 0.023–0.030 | 10/20/30-min partial windows; no cross-battery test |
| 6 | Okour M., limited voltage (JLPEA, 2026) | Random 80/20 | R² 0.92–0.96; RMSE 1.28–2.87 %SOH | Only 5 early-discharge voltage points (1-min sampling) |
| 7 | Zhao Y., GAF-CNN-LSTM (Sci. Rep., 2025) | Same battery, 50 % training | R² ~0.995; RMSE ≤0.004 | IC curves from CC charging; NASA 4 + Oxford |
| 8 | Mohamud N., BiLSTM–RF (Batteries, 2026) | LOBO-CV | RMSE 0.0229 (B0007) | Wavelet-denoised V/I/T, ICA, PCA; only partial results listed |
| 9 | Chen B., physics-consistent (Batteries, 2026) | LOCO (2 train, 1 test) | B0006 R² 0.25→0.53; mean RMSE 0.0499→0.0425 | 13 charge-side HIs + cycle index; closest to our conditions |
| 10 | Zhao J., EWDC (Energies, 2026) | LOBO within each dataset | R² 0.975; RMSE 1.21 %; MAE 0.65 % | 17 CC-CV charge HIs incl. cycle index + accumulated charge; ΔSOH recursion from ŷ₁ = 1 |
| 11 | Sardar S. A. (Batteries, 2026) | Random / battery-wise (7 unseen) / repeated | R² 0.979 / 0.786 / 0.881; RMSE 2.18 / 7.37 / 3.22 % | Closest to this thesis; admits proxy leakage |
| 12 | Meng Y., HSSA-Mamba (Batteries, 2026) | Not detailed; out-of-sample B28 | MAE 0.89 / 1.46 / 2.71 % (11/5/4-cell scales) | Mamba + Q-former fusion; discharge V/I/T + EIS |
| 13 | Shi X., DS-Transformer (Sci. Rep., 2026) | Battery-wise 24/5/5 cells | R² 0.978 (pooled); RMSE 1.67 %; MAE 1.24 %; MAPE 1.51 % | NASA 34 cells / 2,794 pairs; full-discharge sequence implicitly contains discharge time |
| — | **This thesis: TD-BPNN** | Nested 4-fold LOBO × 3 seeds | R² 0.85; RMSE 3.59 %SOH | Strictest protocol in the table |

**Pattern in the table:**
- Same-battery split or random split → R² 0.90–0.995 (rows 1, 3, 5, 6, 7)
- Strict cross-cell, only 3–4 cells, no capacity-proxy inputs → R² 0.53–0.88, RMSE 4–7 %SOH (row 9)
- LOBO but proxy-laden features → still very high (EWDC 0.975; DS-Transformer 0.978)
- This thesis: strictest protocol → R² 0.85
- MAPE: most papers do not report it (only DS-Transformer: 1.51 %) — so it was not a separate column in the audit; we must add MAPE to our own results (R3-C1)
- Journal quartiles are not listed in the audit — check JCR/SJR before citing (R3-C9)

### R3-C5: Proxy-Free Accuracy Improvements (ordered by expected benefit / effort)
1. **Charging-segment features:** all 4 batteries share the same charge protocol (CC 1.5 A → 4.2 V → CV); only discharge cut-offs differ. Use CC-charge time in fixed voltage windows (3.9–4.0 V, 4.0–4.1 V), CV-phase time, IC-peak voltage/height. Naturally aligned across batteries; partial-window by design (approach of audit refs [9],[10]).
2. **Fixed voltage window for discharge features:** e.g. 4.0 → 3.6 V (all batteries pass through it) instead of whole-cycle minimum voltage / total time.
3. **Self-referenced normalization:** divide/subtract each feature by the same battery's first-cycle value. No label needed at deployment; removes initial cell-to-cell offsets (B0006 starts at 2.035 Ah vs ~1.86 Ah for others). Low cost, potentially large gain.
4. **Monotonic / physical prior:** predict degradation increment ΔSOH and accumulate it (as EWDC [10]), or add a monotonicity penalty to the BPNN.
5. **Window-length curve:** RMSE vs window length (5/10/20/30 min, or ΔV = 0.1/0.2/0.3 V) — answers "how little data is enough?"; key figure for the partial-cycle contribution.

### R3-C6: Wider Validation
- **Within NASA:** add B0025–B0056 (similar conditions) → training grows from 3 to 10+ batteries; show a learning curve of LOBO performance vs number of training batteries.
- **Cross-dataset:** develop and freeze the model on NASA, then test directly on CALCE CS2 (dataset used by EWDC [10] → directly comparable); Oxford later if time allows.

### R3-C7: Role of EIS and the Autoencoder
- Replace the 256-dim interpolated spectrum with a few scalars (NASA-provided Re and Rct, \|Z\| range, arc height) as auxiliary fusion features.
- Keep fusion in the main method ONLY if it clearly beats TD-only.
- **Move the AE to the ablation / negative-result section** (AE-TD R² 0.43 vs raw TD 0.85). Do not keep the AE just to match the old thesis title.

### R3-C8: Information to Send Back to Advisor
1. Complete definition of every TD feature (code path and formula).
2. Whether the model is re-fitted on three batteries after inner selection.
3. Number of TD samples, and whether only EIS-aligned cycles are used.
4. Per-fold R² / RMSE, and pooled R².

### R3-C9: Citation Verification Rules (before using ANY number from the audit)
1. Open the full paper; confirm the value, unit, and split protocol yourself.
2. Cite the original paper, not this audit summary.
3. Convert all compared numbers to the same unit (%SOH) and note the protocol next to each value.
4. Check journal quartile (JCR/SJR).
- The literature comparison table (13 studies, 2022–2026) and IEEE reference list [1]–[14] live in the audit PDF, written for direct reuse in Ch. 2.
- One Sci. Rep. 2025 paper ("Cycle based state of health estimation of lithium ion cells using deep learning architectures") was not accessible (rate-limited) — not yet included.

### Thesis Chapter Mapping (audit Section 6)
| Chapter | What to include from the audit |
|---|---|
| Ch. 1 Introduction | Research gap: EIS + discharge + cross-battery exists [11]; open problem = proxy-free, partial-window, unseen-battery SOH. State contributions (R3-C4). |
| Ch. 2 Literature Review | Comparison table extended to 20–30 papers; group by (A) time-domain (B) EIS (C) fusion (D) cross-battery (E) cross-dataset (F) partial-cycle; use the pattern table to explain why published R² varies so much. |
| Ch. 3 Methodology | Justify nested LOBO, fold-train-only normalization, leakage probes, SOH definition, proxy-feature definitions (R3-C3); cite weaker protocols as motivation. |
| Ch. 4 Results | Protocol-gap experiment (random vs chronological vs LOBO); TD-All vs TD-Proxy-Free vs oracle; window-length curve; final table vs literature in unified units. |
| Ch. 5 Discussion & Limitations | The 7 score-gap factors; EIS frequency assumption; cycle-level vs real-time estimation. |
| Appendix | Negative results: AE on EIS and TD features; interpolation ablation; tolerance ablation. |

---

*Last updated: 2026-09-29 — Round 2 marked resolved (Steps 1–18, 2026-09-25); Round 3 (Literature Gap Audit, 2026-09-26) appended as R3-C1…C9; Forbidden Claim #16 added.*
*Next update: Append Round 4 as new section.*
---

## R3-C7 Outcome (Appended 2026-10-06 — Phase 5, item 7.4)

### The AE Is Demoted to a Documented Negative Result (measured, not assumed)

Per the advisor's R3-C7 directive ("move the AE to the ablation / negative-result section"), the
evidence below is complete and the demotion is now a standing directive:

| Evidence | Numbers |
|---|---|
| AE-on-TD vs raw TD features (BPNN, same LOBO) | R² 0.43 vs **0.85** — AE features strictly worse |
| AE on EIS vs PCA on EIS (R² gain over raw) | AE **+0.08** vs PCA **+0.61** — AE loses to a linear projection |
| AE reconstruction target | the interpolated 256-dim input, not the measurement (+0.1 mΩ offset; B0006 anomaly is AE-specific) |
| E_fusion (EIS latent anchored by TD) | R² +0.73 < TD-only 0.85 — the EIS latent adds nothing once TD features are present |

**Claim (approved phrasing for the thesis):** "the autoencoder bottleneck adds no measurable value
on either modality; its latent space reconstructs the interpolation grid rather than the impedance
measurement; PCA is the stronger EIS reducer. The AE is reported as a negative result and the
pipeline proceeds without it."

**Consequences:**
1. Thesis direction = **proxy-audited, partial-window, unseen-battery SOH estimation** (TD-BPNN main pipeline). The title no longer needs "Autoencoder".
2. AE material goes to the Appendix / negative-results section: AE on EIS, AE on TD, interpolation ablation, tolerance ablation.
3. Advisor email (2 questions: EWDC [10] reference; title qualification) blocks **citations/title only** — Ch. 4–5 drafting proceeds without it.
4. Chapter 2 literature numbers must not be quoted until R3-C9 verification is done.

### R3-C9 Resolution Part 1 — EWDC [10] identified and verified (2026-10-06)

**Source verified:** Zhao, J.; Qian, X.; et al. "Unseen-Cell SOH Prediction via Energy-Aware
Warm-Up and Degradation-Consistency Constraints." *Energies* 2026, 19, 4326.
DOI 10.3390/en19184326. Local PDF: `Journal Discovery/Journal Prof Recommend/`.

Verified facts (read from the full paper, not the audit summary):
1. **The 0.975 is NOT a random-split number.** Protocol = within-dataset, source-only LOBO
   (3 source cells train, 1 held out), same batteries as ours: B0005/06/07/18 + CS2-35..38.
   Average R2 0.975 / RMSE 1.21% / MAE 0.65% over the 8 held-out cells, 10 runs.
2. **But the comparison to our proxy-free numbers is still not direct**, for three reasons:
   (a) Feature set = 17 charge-segment HIs **including the cycle index** and cumulative charged
       quantity - proxy-laden by our R3-C3 standard (comparable arm is our TD-All, not Clean-6/8).
   (b) SOH definition = Q/Q0 with y1 = 1 by definition, and the recursive predictor is
       **anchored at yhat1 = 1**. Our 5.4 dSOH test was rejected (0.810 -> -4.785) under Q/Qref
       without that anchor - the anchor, not the recursion, is the difference.
   (c) Their ablation "None" (graph + dSOH recursion, no warm-up/constraints) = R2 0.934,
       worse than the direct GNN baseline 0.950 - the recursion alone is not the win.
3. Per-cell: B0018 fold R2 0.946 (no B0018 collapse - consistent with cycle-index + anchor
   features carrying per-battery scale).
4. **Consequence for the thesis:** compare EWDC 0.975 against our TD-All 0.927 (same LOBO
   protocol), noting (a)-(c). Never against Clean-8 0.810 as if like-for-like.
5. Advisor question 1 is now ANSWERED locally - the email question reduces to the title
   question only. Citation usable in Ch.2 after journal-quartile check (Energies).
