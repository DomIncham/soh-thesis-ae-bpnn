# Phase 3, item 5.5 — the window-length curve

Advisor's words (R3-C5 item 5): *"Window-length curve: RMSE vs window length (5/10/20/30 min, or
ΔV = 0.1/0.2/0.3 V) — answers 'how little data is enough?'; key figure for the partial-cycle
contribution."*

This is the figure the advisor called key, and it is the cleanest run of the round: **0 of 96
fold-seeds flagged degenerate**, against 19/40 in item 5.4 and 14/60 in item 5.1.

## A constraint found before the curve could be built

**The ΔV axis is only partly usable on these files.** At current switch-on the discharge voltage
steps about 0.2 V between the first two samples, so the advisor's ΔV = 0.1 V and 0.2 V never leave
ten samples and cannot form a window at all; ΔV = 0.3 V yields only 8–13 samples. Measured on
B0005: `4.1915 → 4.1907 → 3.9749`, sample interval 18.7 s (against 9.4 s for B0018). The curve is
therefore built on the **time** axis, which works.

## The window features are proxy-laden, and the proxy grows with the window

Every window-length feature was classified with the same rule used throughout (within-battery OLS
R² against capacity; PROXY at ≥ 0.90) before use:

| feature inside the window | W = 5 | W = 10 | W = 20 | W = 30 |
|---|---|---|---|---|
| `mean_V` | **0.947 PROXY** | **0.953 PROXY** | **0.975 PROXY** | **0.979 PROXY** |
| `V_slope` | 0.555 BORDER | 0.861 BORDER | **0.983 PROXY** | **0.983 PROXY** |
| `dT` | **0.920 PROXY** | 0.720 BORDER | 0.887 BORDER | **0.942 PROXY** |
| `mean_T` | **0.086 SAFE** | **0.162 SAFE** | **0.288 SAFE** | **0.466 SAFE** |

Only `mean_T` stays SAFE at every window length. This is the same lesson as item 5.2, at finer
resolution: **the mean discharge voltage inside any window is a capacity proxy**, so a "partial
window" feature set is not proxy-free by virtue of being partial.

## The curve

Two curves are reported so the contrast is visible rather than argued. Both use the same 631 rows,
the same folds and the same seeds (42/7/123), and both use the window's `mean_T` plus the charge-side
features and `ic_peak_V`; `PL` adds the window's `mean_V` (R²(capacity) 0.947 at W = 5).

| W (min) | PF mean R² | PF RMSE | PL mean R² | PL RMSE |
|---|---|---|---|---|
| 5 | **0.842** | 3.760 | 0.874 | 3.231 |
| 10 | 0.828 | 3.892 | 0.885 | 3.072 |
| 20 | 0.830 | 3.897 | 0.898 | 2.840 |
| 30 | **0.843** | 3.750 | 0.914 | 2.644 |
| *full cycle (reference)* | *0.778* | *4.581* | — | — |

**The answer to "how little data is enough?" for the proxy-free set: five minutes.** The PF curve is
flat from 5 to 30 minutes (0.842 → 0.843, a change of 0.001), so nothing is gained by using more of
the discharge. The PL curve, by contrast, rises monotonically (0.874 → 0.914) and beats PF at every
window length, so the proxy feature keeps extracting value from a longer window while the safe
feature does not.

A second observation, stated carefully: the 5-minute proxy-free set scores **0.842 against 0.778**
for the full-cycle proxy-free reference. That gain **cannot be attributed to the shorter window**,
because `W5-PF` differs from the full-cycle `TD-Clean-7` by more than the window: it also drops
`dis_V_slope` (R²(capacity) 0.600, numerically fragile at 1e-4 with a sign-flipping per-battery
correlation) and swaps `dis_mean_T` (0.430) for `w5_mean_T` (0.086). Three changes move together, so
the comparison is suggestive, not isolated.

## Consequence

- **Item 5.5 is complete and supports the thesis title's "partial-window" framing** — but only for
  the temperature feature. The honest headline is: *a proxy-free partial-window model reaches
  R² ≈ 0.84 from the first five minutes of discharge, and the curve is flat thereafter.*
- It does not raise the proxy-free best result: `TD-Clean-8` remains the best proxy-free set at
  0.810 on 5 seeds / 0.842 for the 5-minute variant on 3 seeds. Both are of the same order; neither
  is claimed as a new best.
- The proxy classification inside windows reinforces item 5.2: partial windows are not proxy-free by
  construction.

Evidence: `extract_windowlength_features.py`, `nested_lobo/windowlength_features.csv`,
`phase3_windowlength_run.py`, `phase3_windowlength_cpu_results.csv`,
`phase3_windowlength_verify.py` (12/12 checks pass).