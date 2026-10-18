# Round 5 comparison: Clean-5T vs Clean-6T with rotated selection

Date: 2026-10-18
Author: Padipat Aincham (M11452803)
Repository: github.com/DomIncham/soh-thesis-ae-bpnn (branch `main`)

This report answers your Round 5 comment. Per your instruction it contains only the updated
comparison. All runs are CPU, 5 seeds (42, 7, 99, 123, 2024), the same data files as Round 4,
and the CALCE selection stages now use rotated battery-wise validation exactly as you asked
(R5-C1): every source-training battery takes one inner-validation turn, the validation score
is aggregated across rotations before refit, and the outer test battery/cell stays untouched
throughout selection and refit. The outer battery is now also guarded by a structural check
(S6): it asserts that the outer battery never appears in any inner train or validation set.
The suite passes 26/26.

Files: [`phase5_cs2_clean5t.py`](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/phase5_cs2_clean5t.py) and the four result CSVs
([within](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/phase5_cs2_within_c5t_full.csv),
[transfer](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/phase5_cs2_transfer_c5t_full.csv),
[adapt1](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/phase5_cs2_adapt1_c5t_full.csv),
[adapt2](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/phase5_cs2_adapt2_c5t_full.csv))
under `Autoencoder/round3_phase1/`.

## Feature sets (R5-C2)

- Clean-6T (Round 4 baseline) = Clean-7 minus the two temperature features, plus t_40_41:
  dis_V_slope, cc_dur, cv_dur, cv_I_slope, t_40_41, ic_peak_V (6 features).
- Clean-5T (new) = Clean-6T minus t_40_41: dis_V_slope, cc_dur, cv_dur, cv_I_slope, ic_peak_V
  (5 features). Both sets pass the S4 proxy-ban check.

## Updated comparison (test R², refit stage, mean over 5 seeds)

| Experiment | statistic | Clean-6T | Clean-5T | Change |
|---|---|---|---|---|
| Within-CALCE LOCO (8 cells) | mean / median | 0.158 / 0.573 | 0.208 / 0.581 | +0.050 mean, +0.008 median |
| Frozen NASA → CALCE (room pool) | mean | −14.3 | −32.3 | worse without t_40_41 |
| — per-cell means (room) | per cell | −3.2 … −48.6 | −3.2 … −43.9 | 6 of 8 cells worse without t_40_41 |
| Frozen NASA → CALCE (all-13 pool) | mean | −92.3 | −65.2 | better but still deeply negative |
| One-cell scratch (adapt1) | mean | −437.1 | −225.2 | better but still deeply negative |
| One-cell warm (adapt2) | mean | −3.5 | −13.1 | worse without t_40_41 |

Per-cell detail (mean R², 5 seeds):

| Cell | within C6T → C5T | transfer room C6T → C5T | transfer all13 C6T → C5T |
|---|---|---|---|
| CS2_8 | −2.332 → −2.246 | −48.604 → −43.925 | −156.460 → −157.341 |
| CS2_21 | 0.071 → 0.182 | −3.226 → −3.242 | −13.517 → −18.484 |
| CS2_33 | 0.656 → 0.686 | −10.471 → −34.589 | −94.105 → −59.397 |
| CS2_34 | 0.377 → 0.648 | −14.301 → −40.013 | −110.361 → −65.384 |
| CS2_35 | 0.617 → 0.479 | −12.680 → −43.515 | −112.453 → −69.845 |
| CS2_36 | 0.678 → 0.661 | −9.156 → −32.759 | −87.703 → −54.516 |
| CS2_37 | 0.736 → 0.742 | −8.278 → −31.514 | −84.793 → −50.571 |
| CS2_38 | 0.459 → 0.515 | −7.714 → −28.976 | −78.673 → −46.082 |

adapt1/adapt2 per-cell means are in the result CSVs; the summary values above are the
per-cell means averaged over the 8 CS2 cells.

## What the comparison says

1. Within-CALCE: Clean-5T is equal or slightly better than Clean-6T (median 0.573 → 0.581),
   so t_40_41 is not needed for within-CALCE accuracy — consistent with the NASA finding
   that it no longer improves the corrected result.
2. Cross-dataset transfer: the Clean-5T room-pool per-cell means are lower than the Clean-6T
   values (−28.9…−43.5 vs −7.7…−14.3 on six of eight cells) and warm adaptation is also lower
   (−13.1 vs −3.5), while the all-13 pool and scratch adaptation improve but remain deeply
   negative. We flag two comparability caveats before any direction is read into this:
   (a) the Clean-6T numbers were produced under the previous single-validation-battery
   selection, so the two columns differ in both feature set and selection protocol;
   (b) the per-seed difference is not stable (per-seed room-pool mean deltas: −45.4, −33.7,
   −7.7, −3.8, +0.5), so with five seeds we cannot attribute the room-pool difference to the
   feature change itself. The cross-dataset gap remains large under both feature sets, which
   is the conclusion that matters for the next direction.
3. The Round 4 interpretation stands unchanged: the failure is consistent with domain/range
   shift (target ranges do not overlap), and the two proxy-equivalent features
   (dis_duration, dis_mean_V) are the ones whose removal improved transfer — they appear to
   have amplified the cross-domain mismatch. No direction is claimed for t_40_41 (see the
   comparability caveats above).

## Selection honesty note

Candidate divergence during rotated selection, recorded per (pool, seed) in the CSVs:

| Arm | rows with at least one diverged candidate | rows using the fixed-200-epoch fallback |
|---|---|---|
| within | 40/40 | 22/40 |
| transfer room | 24/40 | 0/40 |
| transfer all-13 | 40/40 | 16/40 |
| adapt1 / adapt2 | 64/80 each | 16/80 each |

The transfer numbers are therefore partly carried by the documented fallback path (best
diverged candidate retrained for a fixed 200 epochs). This is recorded per row and does not
change the conclusion: transfer fails under both feature sets.

## Next direction

Per your Round 5 instruction, since the cross-dataset gap remains, the next research direction
is domain-shift/range-alignment analysis rather than further AE optimization. No work has been
started on it pending your confirmation.
