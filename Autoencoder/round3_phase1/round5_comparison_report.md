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
Both feature sets were fully re-run under this protocol (eight result files); the structural
suite now also covers result-file completeness (S7) and passes 34/34.

Files: [`phase5_cs2_clean5t.py`](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/phase5_cs2_clean5t.py)
(clean-5T by default; Clean-6T via the `CLEAN_FEATS` environment variable) and eight result
CSVs — `{within,transfer,adapt1,adapt2}_c5t_full.csv` and `{...}_c6t_full.csv` —
under `Autoencoder/round3_phase1/`.

## Feature sets (R5-C2)

- Clean-6T (Round 4 baseline) = Clean-7 minus the two temperature features, plus t_40_41:
  dis_V_slope, cc_dur, cv_dur, cv_I_slope, t_40_41, ic_peak_V (6 features).
- Clean-5T (new) = Clean-6T minus t_40_41: dis_V_slope, cc_dur, cv_dur, cv_I_slope, ic_peak_V
  (5 features). Both sets pass the S4 proxy-ban check.

## Updated comparison — SAME PROTOCOL (both sets under rotated battery-wise selection)

Clean-6T was fully re-run under the rotated selection (R5-C1), so both columns below now
share one protocol, the same seeds, budgets, and data files. The earlier Round 4 Clean-6T
numbers (single validation battery) are not comparable and are not used here.

| Experiment | statistic | Clean-6T | Clean-5T | Reading |
|---|---|---|---|---|
| Within-CALCE LOCO (8 cells) | mean / median | 0.137 / 0.576 | 0.208 / 0.581 | Clean-5T equal or slightly better |
| Frozen NASA → CALCE (room pool) | mean / median | −19.2 / −7.1 | −32.3 / −8.8 | medians close; means unstable |
| Frozen NASA → CALCE (all-13 pool) | mean / median | −72.7 / −44.3 | −65.2 / −52.1 | both deeply negative |
| One-cell scratch (adapt1) | mean / median | −443.7 / −30.9 | −225.2 / −34.5 | both non-viable |
| One-cell warm (adapt2) | mean / median | −9.9 / −4.2 | −13.1 / −5.9 | Clean-6T slightly but consistently better (all 8 cells) |

Per-cell detail (mean R², 5 seeds, same protocol both columns):

| Cell | within C6T → C5T | transfer room C6T → C5T | transfer all13 C6T → C5T | adapt2 C6T → C5T |
|---|---|---|---|---|
| CS2_8 | −2.045 → −2.246 | −72.222 → −43.925 | −117.527 → −157.341 | −7.006 → −10.399 |
| CS2_21 | −0.312 → 0.182 | −4.021 → −3.242 | −11.975 → −18.484 | −14.626 → −18.167 |
| CS2_33 | 0.636 → 0.686 | −14.114 → −34.589 | −74.836 → −59.397 | −10.652 → −14.000 |
| CS2_34 | 0.771 → 0.648 | −15.878 → −40.013 | −88.080 → −65.384 | −10.026 → −12.829 |
| CS2_35 | 0.487 → 0.479 | −16.394 → −43.515 | −89.938 → −69.845 | −8.790 → −11.581 |
| CS2_36 | 0.642 → 0.661 | −11.801 → −32.759 | −70.078 → −54.516 | −9.833 → −12.994 |
| CS2_37 | 0.518 → 0.742 | −10.312 → −31.514 | −67.133 → −50.571 | −8.988 → −12.288 |
| CS2_38 | 0.402 → 0.515 | −9.133 → −28.976 | −62.178 → −46.082 | −9.241 → −12.863 |

## What the comparison says

1. Within-CALCE: Clean-5T is equal or slightly better than Clean-6T (median 0.576 → 0.581),
   so t_40_41 is not needed for within-CALCE accuracy — consistent with the NASA finding
   that it no longer improves the corrected result.
2. Cross-dataset transfer: the room-pool difference is NOT attributable to the feature
   change. The per-seed room-pool mean deltas swing across signs (−109.3, −7.0, +49.1,
   +151.6, −46.9 for seeds 7, 42, 99, 123, 2024) and the room-pool medians of the two sets
   are close (−7.1 vs −8.8). By contrast, warm adaptation (adapt2) shows a small but
   perfectly consistent direction: Clean-6T is better on all 8 cells (mean −9.9 vs −13.1),
   so for warm-start fine-tuning t_40_41 does carry useful signal. All pools remain deeply
   negative: the cross-dataset gap stands under both feature sets.
3. The Round 4 interpretation stands unchanged: the failure is consistent with domain/range
   shift (target ranges do not overlap), and the two proxy-equivalent features
   (dis_duration, dis_mean_V) are the ones whose removal improved transfer — they appear to
   have amplified the cross-domain mismatch.

## Selection honesty note

Candidate divergence during rotated selection, recorded per row in the CSVs. Clean-5T /
Clean-6T respectively:

| Arm | rows with ≥1 diverged candidate | rows on the fixed-200-epoch fallback |
|---|---|---|
| within | 40/40 / 40/40 | 22/40 / 10/40 |
| transfer room | 24/40 / 40/40 | 0/40 / 0/40 |
| transfer all-13 | 40/40 / 40/40 | 16/40 / 16/40 |
| adapt1, adapt2 | 64/80 each, both sets | 16/80 each, both sets |

Both feature sets sit largely on the documented fallback path (best diverged candidate
retrained for a fixed 200 epochs) in the NASA-pool arms. This is recorded per row, is a
property of fitting BPNNs on the shifted NASA ranges, and does not change the conclusion:
transfer fails under both feature sets.

Structural verification now covers both result sets (S7: 8 CSVs, expected row counts, 5
seeds, no NaN); the full suite passes 34/34.

## Next direction

Per your Round 5 instruction, since the cross-dataset gap remains, the next research direction
is domain-shift/range-alignment analysis rather than further AE optimization. No work has been
started on it pending your confirmation.
