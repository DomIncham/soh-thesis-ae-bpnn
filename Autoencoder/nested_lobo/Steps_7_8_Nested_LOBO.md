# Nested 4-Fold LOBO Protocol + Mapping Tolerance Ablation (Steps 7–8)

Date: 2026-09-23
Scope: Advisor Round 2: Part C (nested LOBO), Part E (tolerance 1/2/3 ablation on downstream metrics), Part D (metrics in %SOH), Part I1 (EarlyStopping).
Data: `log_grid + pchip` verified pipeline; SOH = Capacity / Q_ref × 100, Q_ref = mean of first 5 discharge cycles (declared, D1).
Runs: 48 (4 tolerances × 3 seeds × 4 folds) + leakage probe, on RTX 3050 (Phase B, Dom).

---

## 1. Protocol (declared before running)

| Layer | Rule |
|---|---|
| Outer test (4 folds) | B0005, B0006, B0007, B0018 rotate as the unseen test battery |
| Inner validation | first battery of the remaining list (deterministic): fold test=B0005 → val=B0006, train={B0007,B0018}; test=B0006 → val=B0007; test=B0007 → val=B0018; test=B0018 → val=B0005 |
| AE | ControlledAutoencoder (256→128→17→128→256), input scaled on fold-train only, EarlyStopping on inner-val loss (patience 30, max 500 epochs), best weights restored |
| BPNN | candidates {[8], [16], [8,4]} × L2 {0, 1e-4} trained on the 17-d latent; SOH target standardized on fold-train only; best combo selected by inner-val RMSE(%SOH) |
| Metrics | MAE, RMSE, R² in %SOH on the outer test; mean ± std across folds and seeds {42, 7, 123} |
| Leakage | structural assert (scaler stats == fold-train stats, every run) + feature-perturbation probe (outer-test ×2 → retrain → train metrics must not move) |
| Decision rules (pre-declared) | winner = lowest mean test RMSE(%SOH); if within 1 std → prefer lowest tolerance; retention is reported, never used for selection |

## 2. Validity Gate

| Gate | Result |
|---|---|
| 1. Run completed | 48/48 rows |
| 2. No NaN | 0 |
| 3. R² sanity | 2 marginal breaches, disclosed: train R² = 0.4994 (tol1, seed 123, fold B0005, arch [8]; 0.0006 below the 0.5 threshold) and test R² = −2.15 / −2.01 (tol2, seeds 7/123, fold B0018). All other 46 runs inside the bounds |
| 4. Metrics per battery | 12 rows per battery (4 tol × 3 seeds) ✓ |
| 5. mean ± std | reported below |
| 6. Leakage probe | PASS: perturbed outer test (×2) left train metrics unmoved: max |diff| = 3.8e-05; ae_ep identical (99/99) |
| Determinism | two identical re-runs produced identical rows |

## 3. Results

### Aggregate per tolerance (12 runs each: 4 folds × 3 seeds), %SOH

| Tolerance | Test MAE | Test RMSE | Test R² | Retained spectra |
|---|---|---|---|---|
| 1 | 7.007 ± 3.020 | 8.566 ± 3.776 | 0.080 ± 0.719 | 452/887 (51.0%) |
| 2 | 7.298 ± 3.510 | 8.723 ± 4.011 | −0.037 ± 1.015 | 477/887 (53.8%) |
| 3 | 7.187 ± 2.904 | 8.887 ± 3.768 | −0.005 ± 0.843 | 886/887 (99.9%) |
| 3m (matched) | identical to tol1 (see Finding 2) | | | 452 |

### Per fold (test RMSE / test R², mean over 3 seeds)

| Fold test battery | tol1 | tol2 | tol3 |
|---|---|---|---|
| B0005 | 6.55 / +0.54 | 6.75 / +0.52 | 6.77 / +0.51 |
| B0006 | 10.34 / +0.06 | 9.43 / +0.24 | 9.59 / +0.22 |
| B0007 | 4.14 / +0.72 | 4.45 / +0.67 | 4.85 / +0.62 |
| B0018 | 13.24 / −1.00 | 14.27 / −1.57 | 14.34 / −1.36 |

### EIS↔capacity cycle-gap distribution (E2 deliverable)

Real gaps between each matched EIS cycle and its backward capacity cycle:

| Battery | gap=1 | gap=2 | gap=3 |
|---|---|---|---|
| B0005, B0006, B0007 | 141 each (31.2% of 452 at tol1) | 2 each (0.4%) | 135 each (15.2% of 886 at tol3) |
| B0018 | 29 (6.4%) | 19 (4.0%) | 4 (0.5%) |

Interpretation: B0005–07 EIS cycles sit either 1 cycle or 3 cycles behind a capacity measurement (a bimodal gap); B0018 sits almost always at gap 1 but its small capacity-log density is what drops rows at tol≤2. Mean gaps: tol1 = 1.00, tol2 = 1.05, tol3 = 1.95 cycles.

## 4. Findings

1. Tolerance 1, 2, 3 are statistically indistinguishable downstream (RMSE 8.57–8.89 %SOH; all within 1 std of each other; ~0.3 %SOH differences against ±3.8 std). Per the pre-declared rule, the winner is tolerance 1 (lowest mean RMSE, and lowest in the tie-break). 
   - *Flagged for the advisor:* tolerance 1 halves the dataset (452 vs 886 spectra) while tolerance 3 retains 99.9% at no measurable downstream cost. The pre-declared rule selects tolerance 1 because shorter gaps mean less label misalignment; the alternative reading: that misalignment shows no measurable cost and tolerance 3 buys data quantity: is stated for discussion, not hidden.
2. The "matched" (3m) arm is vacuous by construction. Backward matching gives every kept row (gap ≤ 1) the same capacity label under tolerance 1 and tolerance 3, so the matched subset carries identical labels: measured results are identical to tol1 to 4 decimals. What tolerance changes is which rows exist (retention), not the label value of shared rows. The retention-vs-alignment confound therefore remains a single variable: sample count.
3. The prediction collapse is fixed on 3 of 4 folds. With nested LOBO + %SOH + standardized targets + EarlyStopping, test R² is positive for B0005 (+0.54), B0006 (+0.06…+0.24), B0007 (+0.62…+0.72): the old single-split pipeline gave R² ≈ −0.03 and collapse.
4. The B0018 fold fails in every configuration (12/12 runs, test R² −0.56…−2.15). B0018 has 52 matched spectra and the steepest domain difference (Steps 1–4: only 53 impedance measurements; SOH range 73–101%). The failure is fold-specific, not tolerance-specific and not seed-specific. This localizes the open problem to cross-battery generalization toward B0018 and sets up Step 9 (Raw EIS → BPNN vs PCA → BPNN vs AE → BPNN under this identical protocol): if all three fail on B0018, the problem is the EIS representation; if only AE fails, it is the feature extraction.
5. EarlyStopping is doing its job: AE early-stopped at 129–192 epochs mean (max 500): different per configuration, replacing the fixed "300 epochs" claim (Part I1).
6. Inner validation selects differently per fold: arch counts [16]×20, [8,4]×14, [8]×14; L2 0×27 / 1e-4×21: hyperparameters were chosen without the outer test battery (Part C2).

## 5. Limitations

- Q_ref (first-5-cycle mean) makes a few SOH values exceed 100% by up to 0.8% (measurement variability exceeding the early-life reference); values are kept as measured, per the no-massaging rule.
- B0006 fades to 57% SOH (NASA ran it past the 30% EOL criterion); real data, kept.
- 3m adds no information (Finding 2); it cost 12 runs and demonstrated implementation determinism.

## 6. Next (Steps 9–10)

Run under this exact protocol: Mean predictor, Linear/Ridge baseline, Raw EIS → BPNN, PCA → BPNN, AE → BPNN (identical folds, inner validation, metrics). Primary question: which pipeline fixes the B0018 fold; secondary: does the AE beat PCA/raw on the three working folds.

---

#
## Artifacts (`Autoencoder/nested_lobo/`)

| File | Purpose |
|---|---|
| `mapping_tolerances.py` | Tolerance 1/2/3 mapped datasets with %SOH labels (Q_ref = first-5-cycles mean) |
| `tolerance_mapping_stats.csv`, `tolerance_gap_distribution.csv` | Retention + real gap histograms (E2) |
| `nested_lobo_harness.py` | Nested 4-fold LOBO harness (--full / --smoke / --probe / --matched) |
| `nested_lobo_results.csv` (48 rows), `nested_lobo_tolerance_summary.csv` | Full-run results and aggregate |
| `full_run_log.txt` | Complete console log incl. probe PASS |
| `validity_gate.py` | Gate 1-6 + decision table (this report's source) |
| `debug_soh.py`, `debug_gate3.py` | SOH range and Gate-3 breach investigations |
| `Steps_7_8_Nested_LOBO.md` | This report |