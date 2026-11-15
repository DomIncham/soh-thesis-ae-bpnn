# Round 6B Closure: What Does One-Cell Output Calibration Contribute?

Addendum to the Round 6 diagnosis report. Source directives: Round 6B Advisor Comment
(2026-11-13) and the research roadmap after Round 6. Work plan: `round6B_work_plan.md`.

## 1. Question and design

The Round 6 report presented "Lc one-cell calibration" without separating two changes that
happened together: the network weights were updated by warm fine-tuning, and an affine output
correction was fitted afterwards. The advisor asked for one final comparison on the same
labeled target cell, so that the contribution of each part is measured:

| Arm | Uses target labels | Network weights | Source |
|---|---|---|---|
| Cal-only | 1 cell | frozen | new, this round |
| FT-only (Adapt2) | 1 cell | updated | Round 5 result, reused |
| FT+Cal (former "Lc") | 1 cell | updated | Round 6 result, renamed |
| L0 (reference) | none | frozen | Round 6 result, reused |
| Lb-affine (reference) | none | frozen | Round 6 result, reused; unsupervised affine feature alignment |
| La-quantile (reference) | none | frozen | Round 6 result, kept as a documented degenerate alignment |

All four informative arms share the same matched keys: 2 pools (room, all13) x 5 seeds x 8
adapt cells = 80 runs, identical test row sets. Cal-only keeps the NASA-trained network
frozen with no weight update and fits y = a*yhat + b on one labeled cell's predictions, then applies the
line to the other 7 cells. No network training takes place in this arm.

Verification of the shared backbone: a retrained pool backbone (room, seed 42, same scaler,
configuration and seed) reproduces the L0 dump predictions to within 0.0219 %SOH. This is a
noise-level tolerance, two orders below the reported error scale; it is disclosed here as a
tolerance, not as an exact-identity claim (`phase6b_backbone_equivalence_check.py`).

The Lb-affine reference row needs one protocol note: its alignment is fitted on the target
training cells' features with no labels, and it is evaluated on the held-out adapt cell
(single-cell rows, 468 to 1,119 cycles), so its MAE is not pooled over the same rows as the
other arms, and the two kinds of number are not comparable. Its median MAE is 11.53 (mean 12.47, 80 runs),
retained here as the unlabeled-alignment reference the advisor asked to keep.

## 2. Main result (MAE in %SOH, run level, n = 80)

| Arm | MAE mean | MAE median | RMSE median | R2 median | labeled cells | weights updated | degenerate calibrations |
|---|---|---|---|---|---|---|---|
| Cal-only | 17.34 | 13.66 | 18.80 | -12.76 | 1 | no | 50 of 80 |
| FT-only | 13.74 | 11.95 | 13.08 | -5.92 | 1 | yes | n/a (no calibration) |
| FT+Cal | 13.20 | 12.18 | 17.31 | -11.22 | 1 | yes | 45 of 80 |
| L0 | 23.54 | 23.75 | 25.51 | -25.76 | 0 | no | n/a |

Mean RMSE: Cal-only 21.07, FT-only 16.34, FT+Cal 19.22, L0 25.82. Mean R2: -21.76, -13.14,
-17.87, -32.39. The R2 values are negative for every arm because each run pools 7 cells whose
SOH ranges are narrow under a domain shift; they are reported for completeness, and their
ranking agrees with the MAE ranking.

Run-level paired tests (Wilcoxon, n = 80): FT-only reaches the lower MAE against Cal-only in
53 of 80 runs (p = 0.0024). FT+Cal against FT-only: no difference we could detect (p = 0.43);
FT-only is lower in 50 of 80 runs, FT+Cal in 30, so the two arms are
indistinguishable at this sample size.

## 3. Recovery under both definitions (R7-C1 correction)

Definition (a), MAE reduction relative to matched L0 = (MAE_L0 - MAE_arm) / MAE_L0:

| Arm | median | mean |
|---|---|---|
| Cal-only | 0.0% | 17.8% |
| FT-only | 42.8% | 36.7% |
| FT+Cal | 37.1% | 27.0% |

Definition (b), transfer-gap recovery with within-CALCE as the reference floor, computed on
matched row sets: the floor for each run is the within-LOCO MAE of the same 7 test cells and
seed (per-run matched floor, median 2.809 %SOH):

| Arm | median | mean |
|---|---|---|
| Cal-only | 0.0% | 18.3% |
| FT-only | 50.1% | 31.3% |
| FT+Cal | 42.7% | 9.7% |

The Cal-only median of 0.0% is a structural fact, not an error: in the 50 runs where the
fitted line is degenerate (slope at or below 0, or far from 1), the run falls back to the
identity correction and its MAE equals the L0 MAE of the same matched rows (50 of 50 exact).

## 4. Diagnostic observation: non-degenerate calibrations (separated from performance claims)

In the 25 runs where both Cal-only and FT+Cal produced a non-degenerate line:

| Arm | median MAE | L0 median on the same runs |
|---|---|---|
| Cal-only | 9.00 | 38.83 |
| FT+Cal | 12.25 | 38.83 |

Cal-only is lower in 10 of 25 runs (p = 0.96, no detected difference). On Cal-only's own
non-degenerate subset (30 runs) the median is 10.22 against L0 30.86. When the fitted line is
sensible, a frozen network with a two-parameter output correction reaches the same level as
the warm-tuned pipeline. This subset is conditioned on calibration success, so it is reported
as a diagnostic observation, not as a performance claim. The count differs from the Round 6
"Lc non-degenerate median 9.24" because that figure used Lc's own 35 non-degenerate runs,
not this matched subset.

## 5. Answer to the Round 6B question

Across 80 matched runs, warm fine-tuning alone reached the lower median MAE (11.95 vs 13.66
%SOH; Wilcoxon p = 0.0024). Adding output calibration on top showed no additional benefit we
could detect (median 12.18, p = 0.43). In the 25 runs where both calibrations were
non-degenerate, calibration alone gave a comparable median (9.00 vs 12.25); because its fitted
line was degenerate in 50 of 80 runs, this comparison is a diagnostic observation, not a
performance claim. The former Lc result is interpreted as warm fine-tuning plus calibration,
and the gain it reported is attributed in greater part to the weight update. For the Stage 1 decision point, the simplest defensible adaptation method on this
evidence is warm fine-tuning alone; calibration serves as a cheap diagnostic whose result is
usable when its fitted line is non-degenerate.

## 6. Units and counting (R7-C1 correction)

The 8 CALCE cells contain 4,922 unique battery cycles. The number 49,220 in the Round 6
report counts prediction instances in the L0 dump (10 pool-seed pairs x 4,922 cycles), and
the Cal-only dump holds 344,540 prediction instances (80 runs x the 7 test cells). All tests
in this addendum operate on the 80 runs; prediction instances are never treated as
independent observations. La-quantile remains documented as a degenerate alignment and is not
counted as recovery.

## 7. Fallback and stability disclosure (R6-C4)

Cal-only: 50 of 80 degenerate calibrations, each disclosed and switched to the identity
correction. FT+Cal: 45 of 80 degenerate, same treatment as in Round 6. Selection fallback
rates are carried in the source CSVs (`sel_degenerate`) and do not differ across arms, since
all arms reuse the same per-pool selection.

## 8. Files and evidence

- `phase6b_calibration_only.py`, `phase6b_cal_only.csv`, `phase6b_cal_only_preds.csv` (full run)
- `phase6b_analysis.py`, `phase6b_matched_3way.csv` (matched 3-way join, 80 rows, MAE/RMSE/R2 per arm)
- `phase6b_backbone_equivalence_check.py` (backbone tolerance check)
- Inputs reused: `phase6_preds_transfer_full.csv` (L0), `phase5_cs2_adapt2_c5t_full.csv` (FT-only),
  `phase6_ladder_Lc.csv` (FT+Cal), `phase5_cs2_within_c5t_full.csv` (floor)
