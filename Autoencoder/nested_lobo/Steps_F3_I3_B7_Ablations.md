# F3/I3 Ablations + B7 Evidence (Pipeline E Fusion, AE-on-TD): Completing the Pending Items

Date: 2026-09-25
Scope: closes the five items previously declared pending: F3 bottleneck ablation, I3 loss comparison, F3 interpolation 6-config ablation (all under the corrected nested protocol), Part J (separate report `Part_J_BMS_Practicality.md`), and B7 supporting evidence (Pipeline E fusion + AE applied to time-domain features).
Protocol: identical nested 4-fold LOBO, tolerance 1, %SOH, fold-train-only scaling/standardization, EarlyStopping, seeds {42,7,123}. Structural leakage assert inside every fold of every run.

## 1. Validity Gate

| Set | Rows | NaN | test R² bounds | Coverage |
|---|---|---|---|---|
| Bottleneck (5 sizes × 12) | 60/60 | 0 | −1.69…+0.80 ✓ | 3 per (size×fold) ✓ |
| Loss (3 × 12) | 36/36 | 0 | −1.36…+0.80 ✓ | ✓ |
| Interpolation (6 × 12) | 72/72 | 0 | −1.98…+0.83 ✓ | ✓ |
| B7 (2 pipelines × 12) | 24/24 | 0 |: | ✓ |

## 2. Bottleneck ablation (F3): AE → BPNN, %SOH

| Bottleneck | Test RMSE | Test R² |
|---|---|---|
| 3 | 8.744 | +0.008 |
| 7 | 8.815 | −0.019 |
| 17 | 8.566 | +0.080 |
| 37 | 8.557 | +0.076 |
| 67 | 8.300 | +0.096 |

All sizes within ~0.5 %SOH against ±3.7-4.2 std: statistically indistinguishable. The old protocol's bottleneck sensitivity did not reappear under the corrected pipeline; 17 remains a reasonable choice, and no size rescues the B0018 fold.

## 3. Loss comparison (I3): MSE / MAE / Huber, %SOH

| Loss | Test RMSE | Test R² |
|---|---|---|
| MSE | 8.572 | +0.077 |
| MAE | 8.316 | +0.121 |
| Huber | 8.479 | +0.086 |

Within 1 std of each other: no loss function changes the conclusion on this dataset. (The advisor's I3 concern about local capacity fluctuations is not resolved by switching the loss here.)

## 4. Interpolation 6-config ablation (F3): %SOH

| Config | Test RMSE | Test R² |
|---|---|---|
| linear_grid / cubic | 7.995 | +0.191 |
| log_grid / cubic | 8.045 | +0.176 |
| linear_grid / linear | 8.311 | +0.111 |
| log_grid / linear | 8.574 | +0.031 |
| log_grid / pchip | 8.578 | +0.077 |
| linear_grid / pchip | 8.624 | +0.049 |

Differences (~0.6 %SOH) are inside the ±3.4-4.1 std: no interpolation method is distinguishable downstream under the corrected protocol. Note the tension with Step 5: cubic's measured overshoot (all 3,548 checks) does not translate into a downstream SOH penalty here; the SOH-relevant information survives interpolation regardless of method. The Linear-vs-PCHIP decision therefore rests on the Step 5 distortion measure (PCHIP is the defensible choice for shape preservation), not on downstream differences.

## 5. B7 evidence: fusion and AE-on-TD

| Pipeline (12 runs) | Test RMSE | Test R² | nRMSE |
|---|---|---|---|
| E_fusion (TD 8 + EIS latent 17, causal backward-time alignment) | 4.893 | +0.726 | 0.158 |
| AE_on_TD (AE 8→4 on TD features) | 7.092 | +0.427 | 0.200 |
| (reference: TD-BPNN alone, Steps 14–16) | 3.590 | +0.848 | 0.106 |

Per-fold R²:

| Fold | E_fusion | AE_on_TD | TD-BPNN (ref) |
|---|---|---|---|
| B0005 | 0.652 | 0.363 | 0.950 |
| B0006 | 0.819 | −0.449 | 0.686 |
| B0007 | 0.917 | 0.917 | 0.967 |
| B0018 | 0.668 | 0.877 | 0.789 |

Findings (hedged):

1. Fusion (TD + EIS latent) is positive on all four folds including B0018 (+0.67) and beats every EIS-only pipeline: the EIS latent adds value only when anchored by time-domain features; it fails as a standalone input (Steps 9–10).
2. AE applied to time-domain features does not help either (overall R² +0.43 vs +0.85 for raw TD features; degrades fold B0006 to −0.45). The AE architecture has now been tested on both modalities and underperforms raw features in both. This is a direct, measured answer to the thesis-architecture question: the two-stage AE+BPNN structure, as currently formulated, is not the strongest configuration on this dataset.
3. Fusion sits between pure TD and pure EIS: consistent with the EIS latent contributing some complementary information (B0006, B0007 improve over TD alone) while diluting the TD signal elsewhere.

## 6. Part J

Delivered separately in `Part_J_BMS_Practicality.md` (measurement requirements, sensors, complexity, online feasibility, sensitivity: no new runs needed).

---

#
## Artifacts

`ablations_f3_i3.py`, `abl_bottleneck*.csv`, `abl_loss*.csv`, `abl_interp*.csv`, `b7_fusion_aeontd.py`, `b7_results.csv`, `b7_summary.csv`, `gate_optionB.py`, `Steps_F3_I3_B7_Ablations.md`