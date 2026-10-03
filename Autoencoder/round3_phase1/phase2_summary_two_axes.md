# Phase 2 summary — the two independent axes that explain the score gap

Everything below is measured on the same data (NASA B0005/06/07/18, 636 discharge cycles), the same
model family (BPNN, same architecture grid and the same inner-selection rule), the same leakage
discipline (fold-train-only scaling, masks asserted disjoint, probes at `max|diff| = 0.00e+00`),
and the same 5 seeds (42, 7, 123, 2024, 11). Only the variable named in each axis changes.

## Axis 1 — the evaluation protocol

| protocol | Oracle-proxy | TD-All | TD-Proxy-Free |
|---|---|---|---|
| random split, same battery (`random_within`) | **0.992** | **0.979** | 0.978 |
| random split, pooled across batteries (`random_pooled`) | 0.815 | 0.989 | 0.978 |
| nested LOBO, unseen battery (ours) | 0.671 | **0.927** | 0.845 |
| chronological split, same battery (`chronological_within`) | 0.179 | **−1.028** | −5.234 |

Per-fold mean R², `refit_on_3` for LOBO and `fit` for the rest.

Two things fall out of this table:

1. **The advisor's R3-C2 prediction is confirmed**: the random split reaches TD-All R² = 0.979,
   above the predicted 0.97. The gap between 0.979 and our 0.927 is therefore the protocol.
2. **The advisor's oracle claim is protocol-scoped.** Under the split the literature uses, the
   oracle reaches **0.992 ≈ 1** exactly as predicted. Under LOBO it reaches 0.671. The oracle
   explains published scores *because published papers evaluate on same-battery splits* — that is
   the mechanism, and it is now measured rather than asserted.

### Audit factor 5 is visible in our own numbers

`chronological_within` scores **−1.028 per fold** but **+0.850 pooled**. Pooling adds
between-battery variance to the R² denominator, so a paper reporting only pooled R² on a
chronological split looks healthy while every individual fold is negative. This is audit factor 5
demonstrated on a fixed representation.

## Axis 2 — the capacity proxy

`TD-Proxy-Free` was built by dropping `dis_duration` alone. The R3-C3 audit showed that is not
enough: `dis_mean_V` is collinear with it (within-battery r = 0.941) and alone explains 94.8 % of
within-battery capacity variance. Two further sets were therefore measured.

| feature set | features | mean R² | median R² | mean RMSE | train_R² (median) |
|---|---|---|---|---|---|
| `TD-All` | 8 | **0.927** | 0.947 | 2.56 | 0.987 |
| `TD-Proxy-Free` | 7 (drop `dis_duration`) | **0.845** | 0.876 | 3.81 | — |
| `TD-Clean-6` | 6 (also drop `dis_mean_V`) | **0.490** | 0.556 | 6.79 | 0.934 |
| `TD-Clean-4` | 4 (also drop `cc_dur`, `cv_dur`) | **−0.400** | −0.136 | 11.27 | 0.610 |

Paired on identical (fold, seed) cells, removing `dis_mean_V` made **19 of 20 fold-seeds worse**,
mean drop **0.354**. The single exception (B0005/seed123, 0.851 → 0.939) is why the claim is stated
as 19/20 and not as a universal.

### What the drop means

The drop is a **generalisation failure, not uninformative features**. `TD-Clean-6` fits its own
training batteries well (median train_R² 0.934) and then fails on the unseen one (mean test R²
0.490). `TD-Clean-4` is worse in both respects (median train_R² 0.610), consistent with its
remaining inputs being the two numerically fragile slope features plus two weak thermal features.

The collapse is concentrated in **B0006** (0.876 → −0.073, a drop of 0.873; other folds 0.16–0.21).
B0006 is the cell whose reference capacity is the outlier (Qref 2.018 Ah vs ~1.85 for the others).
That identifies the mechanism: `dis_duration` and `dis_mean_V` do not merely carry the label, they
also carry the **per-battery scale** that a LOBO model has no other way to observe. Remove them and
the model can no longer place an unseen battery on the SOH axis.

A second symptom points the same way: with the proxies gone, **22 of 40 fold-seeds were flagged
degenerate** and the inner-validation RMSE the selection minimises sits at a median of 6.5 %SOH
(up to 29.8), against a training SOH span of roughly 30–45 %SOH. The selection is choosing between
candidates that all failed, i.e. the inner-validation signal is largely unusable without the proxies.

## Consequences for the thesis claims

- **Contribution (1)** — "quantify how much published accuracy comes from protocol and capacity
  proxies" — is now answered on both axes with our own numbers: the protocol axis moves TD-All
  between −1.03 and 0.989, and the proxy axis moves it between −0.40 and 0.927.
- **Contribution (2)** — "unseen-battery accuracy under proxy-free conditions" — must be restated.
  The defensible number is **TD-Clean-6 = 0.490 (median 0.556)**, not 0.845. The 0.845 figure
  depended on a proxy-equivalent feature and cannot be quoted as proxy-free.
- The proxy axis strengthens audit factor 2 from a caution into a measurement: for this feature
  family, cross-battery SOH estimation without a capacity proxy is close to the level a
  mean-predictor would reach on the harder folds.

## Limitations to state with the numbers

1. Four batteries only. This does not answer R3-C6 (wider validation, B0025+ / CALCE).
2. `TD-Clean-4`'s low score is confounded: its surviving inputs include `dis_V_slope` and
   `cv_I_slope`, which sit at 1e-4–1e-3 and whose per-battery correlation with capacity flips sign.
   A low score there is not evidence about proxies.
3. `random_pooled` leaks battery identity into training by construction and must never be quoted as
   a performance result; it is a protocol-gap data point only.
4. The 5-seed upgrade changed the LOBO headline only marginally (TD-All 0.923 → 0.927,
   TD-Proxy-Free 0.854 → 0.845), so the 3-seed Phase 1 numbers remain valid as an independent check.

Evidence: `protocol_gap_exp_cpu_*.csv` (axis 1), `td_clean_cpu_*.csv` (axis 2),
`protocol_gap_verify.py` (23/23), `td_clean_verify.py` (7/7), `r3c3_feature_classification.md`.