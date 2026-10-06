# Phase 4 item 6.3 (R3-C6): NASA -> CALCE CS2 cross-dataset results (all four arms)

Run: 2026-10-05, commits `d44f224` (extraction), `7ab9205` (frozen), `267c5aa`/`713acdc` (adaptation),
`1807a6c` (control). All runs checkpointed and resumable; every verify passed before hand-off.

Data: 8 CS2 cells (33–38 xlsx, 8/21 txt), 7,730 rows, 4,922 full cycles (cap ≥ 0.8 × cell max).
Capacity cross-check vs CALCE's own coulomb counting: max|diff| ≤ 0.004 Ah on every cell.
Feature set: **Clean-6T** (Clean-8 minus the two temperature features; the CS2_33–38 logs have no
temperature channel).

## Results (mean R² per CS2 test cell, 5 seeds)

| test cell | frozen NASA→CS2 | warm 1-cell adapt | LOCO within CS2 (control) |
|---|---|---|---|
| CS2_33 | −178 | −50 | **0.64** |
| CS2_34 | −179 | −50 | **0.39** |
| CS2_35 | −2.2 | −44 | **0.58** |
| CS2_36 | −1.5 | −43 | **0.68** |
| CS2_37 | −1.5 | −43 | **0.60** |
| CS2_38 | −2.0 | −40 | **0.46** |
| CS2_21 | −92 | −51 | 0.13 |
| CS2_8 | −401 | −52 | −1.59 |
| **median / mean** | −37 / −107 | −31 / −47 | **0.59 / 0.24** |

(The frozen all13-pool variant scored median −24, mean −48; the 1-cell scratch arm −68.)

## Findings

1. **The frozen model does not transfer** (median −37), driven by a label-scale offset: CS2 SOH
   spans 88–114 % while NASA spans 72–108 %, and the 0.5 C CS2 charge makes `t_40_41` / `cc_dur`
   ≈ 2× the NASA scale - the frozen model extrapolates on every feature.
2. **One-cell adaptation equalises but does not fix**: warm-starting the frozen weights on 1 CS2
   cell pulls every prediction toward the adapt cell's offset (median −31; worst cell improved
   3–7×, the previously-best cells degraded −2 → −43). Training from scratch on 1 cell is worse
   still (−68). One cell is not enough calibration, and adaptation trades off cells.
3. **The control proves it is domain shift, not data quality**: leave-one-cell-out *within* CS2
   reaches R² 0.39–0.68 on 6 of 8 cells (pooled median 0.59) - the parser, the features and the
   CS2 data are sound. (CS2_8 is its own anomaly, failing even within-CS2; CS2_21 is weak.)
4. **Consistent with the thesis's core claim**: the failure mode is the same per-cell label offset
   documented inside NASA (B0006's 2.035 vs ~1.86 Ah reference; the ΔSOH-accumulation rejection).
   Cross-dataset SOH prediction requires per-cell calibration information, which is exactly what
   the nested protocol does not grant - reinforcing the protocol-scoping argument of contribution (1).

## Advisor-alignment check (R3-C6)

| audit item | status |
|---|---|
| 6.1 learning curve vs number of training batteries (B0025–B0056) | done (`phase4_learning_curve_summary.md`) |
| 6.2 cross-dataset to CALCE CS2 | done - this file, all four arms |
| protocol consistency | same nested selection + selection guard everywhere; Clean-6T is Clean-8 minus the two features CS2 cannot measure, disclosed |
| honest reporting | the negative cross-dataset result is reported alongside the positive within-CS2 control |

Files: `phase4_cs2_features.csv`, `phase4_cs2_transfer_full.csv`, `phase4_cs2_adapt1_full.csv`
(scratch arm), `phase4_cs2_adapt2_full.csv` (warm arm), `phase4_cs2_within_full.csv` (control).
