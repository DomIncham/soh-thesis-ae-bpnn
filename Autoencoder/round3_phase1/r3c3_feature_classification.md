# R3-C3 — TD feature classification: safe vs proxy

Advisor's directive: *"List every TD feature; label each `safe` or `proxy`. Proxies include:
discharge duration, end-of-discharge time, ∫I dt (accumulated Ah), cycle index, previous-cycle
capacity."* This document is that list, with the measurement behind each label.

Source of truth for the definitions: `Autoencoder/nested_lobo/extract_time_features.py`.
Label alignment is exact — each discharge cycle carries its own measured capacity, no tolerance
mapping. Causality is respected: the four charge-side features come from the charge cycle that
**precedes** the labelled discharge cycle, so no future information enters the input.

## Classification rule (fixed before looking at the numbers)

Within each battery, fit `feature ~ a + b·capacity` by OLS and read R². Also report the same against
SOH, the pooled correlation with SOH, and the per-battery mean spread (audit factor 7: the discharge
cut-offs differ per cell, B0005 2.7 V / B0006 2.5 V / B0007 2.2 V / B0018 2.5 V).

- **PROXY** — R²(capacity) ≥ 0.90 within battery: the feature is, or is collinear with, the label.
- **BORDERLINE** — 0.50 ≤ R² < 0.90.
- **SAFE** — R² < 0.50: it can only help through degradation physics, not by re-reading the label.

## Result

| feature | side | R²(capacity) | R²(SOH) | pooled r(SOH) | per-battery R² vs capacity | class |
|---|---|---|---|---|---|---|
| `dis_duration` | discharge | **0.972** | 0.972 | 0.891 | 0.952 / 0.986 / 0.964 / 0.985 | **PROXY** |
| `dis_mean_V` | discharge | **0.948** | 0.948 | 0.955 | 0.965 / 0.932 / 0.924 / 0.971 | **PROXY** |
| `cc_dur` | charge (prev) | 0.651 | 0.651 | 0.847 | 0.742 / 0.824 / 0.615 / 0.423 | BORDERLINE |
| `dis_V_slope` | discharge | 0.600 | 0.600 | −0.225 | 0.123 / 0.417 / 0.944 / 0.915 | BORDERLINE |
| `cv_I_slope` | charge (prev) | 0.556 | 0.556 | −0.545 | 0.395 / 0.535 / 0.440 / 0.853 | BORDERLINE |
| `cv_dur` | charge (prev) | 0.552 | 0.552 | −0.782 | 0.661 / 0.758 / 0.587 / 0.203 | BORDERLINE |
| `dis_mean_T` | discharge | 0.430 | 0.430 | −0.564 | 0.656 / 0.677 / 0.346 / 0.040 | SAFE |
| `ch_mean_T` | charge (prev) | 0.018 | 0.018 | 0.022 | 0.000 / 0.052 / 0.006 / 0.013 | SAFE |

## The finding that matters: the proxy survived its own removal

`TD-Proxy-Free` was built by dropping `dis_duration` only. That is not enough, because
**`dis_mean_V` is collinear with `dis_duration`** (within-battery Pearson r = 0.922 / 0.955 /
0.894 / 0.991, mean 0.941) and on its own explains **94.8 %** of within-battery capacity variance.

So the 0.845 "proxy-free" number is **not** a clean proxy-free number: the capacity proxy was
removed under one name and re-entered under another. Any claim of the form "our model achieves X
without capacity proxies" must use a feature set that drops both, and ideally the borderline
charge-side duration pair as well.

## Secondary observations

1. **The two slope features are numerically fragile.** `dis_V_slope` lives at 1e-4
   (global range −3.08e-4 … −6.85e-5) and `cv_I_slope` at 1e-3. Under `MinMaxScaler` their dynamic
   range is stretched to [0,1], so numerical noise is amplified, and their per-battery correlation
   with capacity even flips sign (`dis_V_slope`: −0.351, −0.646, +0.971, +0.956). They should be
   treated as unreliable inputs, not as evidence.
2. **`dis_mean_T` is weak and unstable** (per-battery R² 0.656, 0.677, 0.346, 0.040; correlation
   −0.81 on two cells, −0.20 on another). Kept as SAFE, but not dependable.
3. **Domain shift is mild for the discharge features** (per-battery mean spread 1.6–5.5 % of level)
   and larger for the charge-side durations (`cc_dur` 2002 s … 2588 s, a 1.29× spread), which is
   consistent with audit factor 7.
4. `ch_mean_T` is essentially uninformative (R² 0.018) and is the only feature with no measurable
   relationship to capacity in any cell.

## Measured outcome (both clean sets were run)

Nested LOBO, 4 folds × 5 seeds, same grid and selection rule as Phase 1/2:

| feature set | features | mean R² | median R² | RMSE (%SOH) | median train R² |
|---|---|---|---|---|---|
| `TD-All` | 8 | 0.927 | 0.947 | 2.56 | 0.987 |
| `TD-Proxy-Free` | 7 | 0.845 | 0.876 | 3.81 | — |
| `TD-Clean-6` | 6 | **0.490** | 0.556 | 6.79 | 0.934 |
| `TD-Clean-4` | 4 | **−0.400** | −0.136 | 11.27 | 0.610 |

Paired on identical (fold, seed) cells, removing `dis_mean_V` made **19 of 20 fold-seeds worse**
(mean drop 0.354). The single exception is B0005/seed123 (0.851 → 0.939).

**Leave-one-feature-out with ridge**, same protocol, full 8-feature set:

| dropped | mean R² | Δ vs full |
|---|---|---|
| `dis_duration` | 0.323 | **−0.500** |
| `dis_mean_V` | 0.447 | **−0.376** |
| `cc_dur` | 0.820 | −0.003 |
| `cv_I_slope` | 0.824 | +0.001 |
| `cv_dur` | 0.825 | +0.002 |
| `dis_mean_T` | 0.827 | +0.004 |
| `dis_V_slope` | 0.842 | +0.019 |
| `ch_mean_T` | 0.847 | +0.024 |
| (none) | 0.823 | — |

The entire cross-battery signal lives in two features; removing any of the other six changes the
score by at most 0.024 and in three cases improves it.

**Not a model limit.** Ridge on the same features scores 0.823 / 0.323 / −0.526 / −1.965 for
All / Proxy-Free / Clean-6 / Clean-4, against the BPNN's 0.927 / 0.845 / 0.490 / −0.400. The network
already extracts more than a linear model from these inputs, so the proxy-free ceiling is set by
the features, not by the network.

## Consequence for the thesis claims

- **Contribution (1)** — "quantify how much published accuracy comes from protocol and capacity
  proxies" — is answered on both axes with our own numbers.
- **Contribution (2)** — "unseen-battery accuracy under proxy-free conditions" — **must be restated
  as `TD-Clean-6` = 0.490 (median 0.556)**. The earlier 0.845 figure rested on `dis_mean_V` and is
  withdrawn from that role.
- Audit factor 2 moves from a caution to a measurement: for this feature family the capacity proxy
  is worth roughly +0.44 R² of cross-battery accuracy.

## Why the drop happens

It is a generalisation failure, not uninformative features: `TD-Clean-6` fits its own training
batteries (median train R² 0.934) and then fails on the unseen one. The collapse is concentrated in
**B0006** (0.876 → −0.073, against 0.16–0.21 on the other folds) — the cell whose reference capacity
is the outlier. That identifies the mechanism: the two proxy features also carry the **per-battery
scale** that a LOBO model has no other way to observe. A second symptom agrees: with the proxies
gone, 22 of 40 fold-seeds were flagged degenerate and the inner-validation RMSE sits at a median of
6.5 %SOH (up to 29.8) against a training SOH span of about 30–45 %SOH, so the selection is choosing
between candidates that all failed.

## Limitation on `TD-Clean-4`

Its low score is confounded. The two surviving slope features sit at 1e-4–1e-3 and their
per-battery correlation with capacity flips sign, and the two thermal features are weak. A low
score there is evidence about the inputs, not about proxies.

Evidence files: `r3c3_feature_classes.py` / `.csv` (rule + measurement), `td_clean_run.py`,
`td_clean_cpu_results.csv`, `td_clean_verify.py` (7/7), `r3c5_ridge_probe.py` / `.csv`,
`phase2_summary_two_axes.md`.