# Phase 4 (R3-C6): learning curve vs number of training batteries — results and integrity checks

Run: 2026-10-05, `phase4_learning_curve.py` (CPU, 420 fold-runs), commit `79c678b` harness.
Data: `phase4_features.csv`, 14 included cells (see `phase4_survey_B0025_B0056.md` for the survey
and the committed hygiene rules). Protocol: for each (k, seed, test cell) sample k train cells
from the other 13; 1 of them is the inner-validation battery (config selection + selection guard);
the selected config is refit on all k; the untouched test cell is scored. Settings: TD-All (8
features), Clean-8 (6 clean + ic_peak_V + t_40_41).

## Integrity verification (all pass)

| check | result |
|---|---|
| completeness | 420/420 fold-runs (2 settings × k∈{3,7,13} × 5 seeds × 14 test cells), no missing/NaN metric |
| leakage asserts | scaler must equal fold-train min/max, asserted per fold — 840 asserts, none fired |
| determinism | fold (TD-All, k=13, seed 42, B0005) re-run: ΔR² = 1.6e-05 (CSV rounding) |
| protocol reproduction | the SAME harness restricted to the 4 original cells (k=3, 5 seeds) gives **mean R² = 0.933** vs the Phase 1 reference 0.923 (`steps14_16_refit`) — 20 folds, range 0.827–0.991 |

## Results

Aggregate means are **dominated by catastrophic cross-condition folds** — medians and per-condition
breakdowns are the honest reporting unit:

| setting | k | mean R² | median R² |
|---|---|---|---|
| TD-All | 3 | −26.6 | −3.45 |
| TD-All | 7 | −19.4 | −0.05 |
| TD-All | 13 | −16.1 | −0.02 |
| Clean-8 | 3 | −20.2 | −1.25 |
| Clean-8 | 7 | −22.3 | +0.15 |
| Clean-8 | 13 | −12.5 | +0.32 |

Per condition (Clean-8, k=13, mean over 5 seeds — test cell level):

| condition | cells | mean R² | range |
|---|---|---|---|
| room 2A (original pool) | B0005/6/7/18 | **0.74** | 0.55–0.85 |
| room 4A pulsed | B0025–28 | **−44.7** | −132.8 – −0.9 |
| hot 43°C 4A | B0029–32 | **0.25** | 0.05–0.40 |
| cold 4°C 1A | B0047/48 | **0.18** | 0.04–0.33 |

## Findings

1. **Features do not transfer across load profiles.** The pulsed 4A cells (B0025–28) are
   catastrophic under every setting (B0027: R² −132 at k=13): discharge-side features
   (`dis_duration`, `dis_mean_V`, `dis_V_slope`) are functions of the load profile first and of
   degradation second. The charge-side Clean-8 features do not rescue them (2 % of pulsed
   fold-runs score R² > 0).
2. **"More batteries" only helps within a condition.** Room-2A test cells degrade from the
   4-cell homogeneous pool (0.933) to 0.63–0.85 when the training pool is widened to 13
   heterogeneous cells — heterogeneous additions are anti-informative for same-condition tests.
   Within-condition curves are still positive: room-2A Clean-8 medians rise −1.25 → +0.15 → +0.32
   for k = 3 → 7 → 13.
3. **Selection degeneracy is a symptom of the same effect.** 259/420 fold-runs had no converging
   selection candidate (71 % at k=3, 36 % at k=13 for Clean-8): validating a config on a battery
   from a different condition selects nothing, because the cross-condition residual signal swamps
   the degradation signal.
4. Implication for the thesis claim: the learning-curve claim must be stated **per condition**;
   a pooled heterogeneous LOBO number (mean R² −12.5 at k=13) is not a model failure but a
   pool-design statement, and Option C's cross-dataset test (CALCE CS2, same chemistry, same
   charge protocol) is the right venue for a *pooled* generalisation claim.

## Reproduction

`phase4_verify_protocol.py` re-runs the 4-cell protocol check (mean R² = 0.933 vs 0.923; ~15 min
CPU). Full per-fold data: `phase4_learning_curve_full_results.csv`.
