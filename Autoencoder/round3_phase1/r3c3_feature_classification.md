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

## Consequence for the thesis claims

- Contribution (1) "quantify how much published accuracy comes from protocol + capacity proxies" is
  now measurable on both axes: the protocol axis is done (Phase 2), the proxy axis needs a feature
  set that is actually proxy-free.
- Contribution (2) "unseen-battery accuracy under proxy-free conditions" currently rests on a set
  that still contains a 0.948 proxy. The number must be re-measured on a cleaned set before it is
  quoted.

## Next experiment (proposed)

Add two settings under the same nested LOBO protocol and the same seeds:

| setting | features | purpose |
|---|---|---|
| `TD-Clean-6` | drop `dis_duration`, `dis_mean_V` | the two R² ≥ 0.90 features gone |
| `TD-Clean-4` | also drop `cc_dur`, `cv_dur` | plus the borderline charge-duration pair |

Cost: 2 settings × 4 folds × 3 seeds = 24 fold-seeds, about 20 minutes on CPU. The drop from
`TD-Proxy-Free` (0.845) to `TD-Clean-6` is the honest measure of how much of our accuracy was still
proxy-driven.

Evidence files: `r3c3_feature_classes.py` (rule + measurement), `r3c3_feature_classes.csv` (output).