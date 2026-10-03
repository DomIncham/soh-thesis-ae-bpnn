# Phase 3, item 5.1 — charging-segment / ICA features

Question this answers: the ridge probe showed the proxy-free ceiling is a **feature** limit, not a
model limit (BPNN 0.490 on TD-Clean-6 where ridge gives −0.526). Can a genuinely proxy-free feature
addition recover any of the accuracy that the capacity proxies were carrying?

## What was added

`extract_charge_features.py` computes, per charge cycle, and attaches them to the **following**
discharge cycle (the same causality rule the existing four charge features already follow):

| feature | definition |
|---|---|
| `t_39_40`, `t_40_41` | time spent in fixed charge-voltage windows (3.9–4.0 V, 4.0–4.1 V) |
| `ic_peak_V`, `ic_peak_h` | incremental-capacity peak position and height on the CC phase |
| `cc_dTdt`, `cc_V_slope` | temperature and voltage rate during the CC phase |

Each new feature was then run through the **same proxy rule** used for the original eight
(within-battery OLS R² against capacity; PROXY at ≥ 0.90), before any of them was used:

| feature | R²(capacity) | per battery | verdict |
|---|---|---|---|
| `ic_peak_V` | 0.489 | .621/.749/.283/.305 | SAFE (just under the 0.50 line) |
| `t_40_41` | 0.341 | .377/.668/.106/.213 | SAFE |
| `cc_dTdt` | 0.394 | .510/.665/.297/.104 | SAFE |
| `cc_V_slope` | 0.479 | .557/.750/.011/.599 | SAFE |
| `t_39_40` | 0.716 | .805/.860/.674/.523 | BORDERLINE — not used |
| `ic_peak_h` | **0.906** | .935/.936/.879/.873 | **PROXY — not used** |

The window matters: the upper window (4.0–4.1 V) is markedly less proxy-like than the lower one
(3.9–4.0 V), and the ICA peak *position* is safe while the peak *height* is a proxy.

## A bug found and fixed during extraction

The first IC implementation took the argmax over the whole 3.0–4.19 V grid. For many cycles the
maximum landed on the grid edge — the voltage climb off the discharge cut-off, not the ICA peak
(`ic_peak_V` min/max were exactly 3.000/4.180). Restricting to V ≥ 3.6 and strictly rising made the
peak interior (median 4.00–4.06 V, 0.9 % still at the upper edge). **The fix changed a verdict**:
`ic_peak_h` went from BORDERLINE 0.681 to PROXY 0.906, so an unfixed version would have admitted a
capacity proxy into a "proxy-free" feature set.

## Result — paired, on identical rows and seeds

Five cycles (B0005/06/07 cycle 86, B0018 cycles 117 and 141; all early life, SOH 90.9–100.6) have no
usable CC phase, so `ic_peak_V` is NaN there. Rather than impute, those rows were dropped and
**TD-Clean-6 was re-run as the reference on exactly the same 631 rows**, so every number below is
comparable cell-by-cell.

| setting | features | mean R² | median R² | std | RMSE (%SOH) |
|---|---|---|---|---|---|
| `TD-Clean-6*` (reference, 631 rows) | 6 | 0.664 | 0.598 | 0.177 | 5.594 |
| `TD-Clean-7` (+ `ic_peak_V`) | 7 | **0.772** | 0.827 | 0.155 | 4.626 |
| `TD-Clean-8` (+ `t_40_41`, `ic_peak_V`) | 8 | **0.810** | 0.825 | 0.109 | 4.272 |

Per fold, mean over 5 seeds:

| fold | CLEAN-6* | CLEAN-7 | CLEAN-8 |
|---|---|---|---|
| B0005 | 0.674 | 0.802 | 0.862 |
| B0006 | 0.555 | 0.597 | 0.657 |
| B0007 | 0.818 | 0.922 | 0.924 |
| B0018 | 0.611 | 0.767 | 0.799 |

Paired per (fold, seed):

- **`ic_peak_V` improves 15 of 20 fold-seeds**, mean Δ +0.107. **Supported.**
- `t_40_41` on top improves only 11 of 20, mean Δ +0.039. **Not supported** — within noise.
- CLEAN-6 → CLEAN-8 improves 16 of 20, mean Δ +0.146, and every fold improves at every step.

## The limitation that must travel with the number

The proxy-free regime is **unstable**. Removing 5 of 636 cycles (0.8 %) moves the TD-Clean-6 score
from 0.490 to 0.664 (+0.174), with per-(fold, seed) swings between −0.647 and +0.860. That is larger
than the effect being claimed, which is why the claim above is stated as a **paired** result on
identical rows and never as "0.490 → 0.810" across different row sets.

The instability is itself a finding: with the proxies removed, the inner-validation signal is weak
(14 of 60 fold-seeds flagged degenerate in this run) and the selected configuration flips between
nearby data versions, so the score is not a stable property of the feature set in the way TD-All's
0.927 is.

## Consequence for the contributions

- **Contribution (2)** improves materially. The defensible proxy-free number is no longer 0.490.
  With `ic_peak_V` it is **≈ 0.77 (median 0.83)**, and with `t_40_41` as well **≈ 0.81 (median
  0.83)** — against `TD-Proxy-Free` 0.845, whose headline rested on a 0.948 proxy-equivalent
  feature. So a feature set with **no feature above 0.49 R²(capacity)** reaches ~96 % of the score
  the proxy-bearing set reached.
- The claim must be quoted with its dispersion and with the instability note, not as a point value.

## Next in Phase 3

- **5.2** fixed discharge voltage window (4.0 → 3.6 V) instead of whole-cycle duration — attacks the
  same proxy problem from the discharge side, and is the natural partner to what was done here.
- **5.3** self-referenced normalisation (divide each feature by the battery's first-cycle value) —
  this is the item that directly targets the per-battery scale problem identified in the R3-C3 work,
  where removing the proxies cost B0006 0.873 R².
- **5.5** window-length curve, the figure the advisor asked for.

Evidence: `extract_charge_features.py`, `nested_lobo/charge_features.csv`,
`phase3_charge_features_run.py`, `phase3_charge_cpu_results.csv`, `phase3_charge_verify.py` (8/8),
`data_provenance_audit.py` (26/26).