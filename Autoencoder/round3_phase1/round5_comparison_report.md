# Round 5 comparison: Clean-5T vs Clean-6T under rotated selection

Date: 2026-10-18
Author: Padipat Aincham (M11452803)
Repository: github.com/DomIncham/soh-thesis-ae-bpnn (branch `main`)

This is the updated comparison you asked for; nothing else is included. All runs are CPU,
5 seeds (42, 7, 99, 123, 2024), the same data files as Round 4. As you instructed, the CALCE
selection stages now use rotated battery-wise validation: each source-training battery takes
one inner-validation turn, the validation score is averaged across rotations before the
refit, and the outer test battery/cell is not used at any point in selection or refit.
A structural check (S6) asserts the outer battery is absent from every inner train/val set.
I re-ran both feature sets under this protocol (eight result files). The structural suite
now also checks result-file completeness (S7) and passes 34/34.

Code: [`phase5_cs2_clean5t.py`](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/phase5_cs2_clean5t.py)
(Clean-5T by default; Clean-6T via the `CLEAN_FEATS` environment variable). Results: eight
CSVs, `{within,transfer,adapt1,adapt2}_c5t_full.csv` and `{...}_c6t_full.csv`, under
`Autoencoder/round3_phase1/`.

## Feature sets (R5-C2)

- Clean-6T (Round 4 baseline) = Clean-7 minus the two temperature features, plus t_40_41:
  dis_V_slope, cc_dur, cv_dur, cv_I_slope, t_40_41, ic_peak_V (6 features).
- Clean-5T (new) = Clean-6T minus t_40_41: dis_V_slope, cc_dur, cv_dur, cv_I_slope, ic_peak_V
  (5 features). Both sets pass the S4 proxy-ban check.

## Comparison — both columns under the same rotated-selection protocol

Because Clean-6T was re-run under the rotated selection, both columns below share one
protocol, seeds, budgets, and data files. The Round 4 Clean-6T numbers (single validation
battery) are not comparable and I did not use them.

| Experiment | statistic | Clean-6T | Clean-5T | Reading |
|---|---|---|---|---|
| Within-CALCE LOCO (8 cells) | mean / median | 0.137 / 0.576 | 0.208 / 0.581 | Clean-5T equal or better |
| Frozen NASA → CALCE (room pool) | mean / median | −19.2 / −7.1 | −32.3 / −8.8 | medians close; means not stable |
| Frozen NASA → CALCE (all-13 pool) | mean / median | −72.7 / −44.3 | −65.2 / −52.1 | both deeply negative |
| One-cell scratch (adapt1) | mean / median | −443.7 / −30.9 | −225.2 / −34.5 | both non-viable |
| One-cell warm (adapt2) | mean / median | −9.9 / −4.2 | −13.1 / −5.9 | Clean-6T better on all 8 cells |

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

## What the numbers show

1. Within-CALCE: Clean-5T is equal to or better than Clean-6T (median 0.576 → 0.581).
   t_40_41 is not needed for within-CALCE accuracy, which matches the NASA result that it
   no longer improves the corrected protocol.
2. Transfer, room pool: I do not attribute the mean difference to the feature change. The
   per-seed room-pool mean deltas switch sign (−109.3, −7.0, +49.1, +151.6, −46.9 for seeds
   7, 42, 99, 123, 2024) and the two medians are close (−7.1 vs −8.8). Five seeds do not
   separate the two sets here.
3. Warm adaptation (adapt2) is the one case with a direction on every cell: Clean-6T is
   better on all 8 cells (mean −9.9 vs −13.1). So t_40_41 does carry signal for warm-start
   fine-tuning.
4. Every transfer and adaptation pool stays deeply negative under both feature sets. The
   cross-dataset gap stands.
5. The Round 4 interpretation is unchanged: the failure is consistent with domain/range
   shift (the target ranges do not overlap), not proven to be caused by it. Removing the two
   proxy-equivalent features (dis_duration, dis_mean_V) improved transfer while within-CALCE
   performance stayed at the same level (median 0.589 → 0.573 in Round 4), so those two
   features amplified the cross-domain mismatch.

## Selection fallback rates

During rotated selection many candidates diverge before the epoch budget; the runner then
falls back to the best diverged candidate retrained for a fixed 200 epochs. Counts come from
the per-row columns in the CSVs (Clean-5T / Clean-6T):

| Arm | rows with ≥1 diverged candidate | rows on the fixed-200-epoch fallback |
|---|---|---|
| within | 40/40 / 40/40 | 22/40 / 10/40 |
| transfer room | 24/40 / 40/40 | 0/40 / 0/40 |
| transfer all-13 | 40/40 / 40/40 | 16/40 / 16/40 |
| adapt1, adapt2 | 64/80 each, both sets | 16/80 each, both sets |

Most NASA-pool rows sit on the fallback path. This is recorded per row and is a property of
fitting BPNNs on the shifted NASA ranges; it does not change the conclusion that transfer
fails under both feature sets.

Structural verification covers both result sets (S7: 8 CSVs, row counts, seeds, no NaN);
the suite passes 34/34.

## Next direction

The cross-dataset gap remains, so per your Round 5 instruction the next direction is
domain-shift/range-alignment analysis, not further AE optimization. I have not started this
work and will wait for your confirmation.
