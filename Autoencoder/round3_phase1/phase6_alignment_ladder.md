# P6-5 Sub-plan — Alignment Ladder (R6-C2.5), for Dom's approval before full runs

Approved base: PAEV plan 2026-10-21 (step P6-5) + advisor R6-C2.5 wording. This sub-plan
fixes the definitions the ladder needs before any run, per the agreed discipline.

## Ladder definition (increasing target information — advisor's exact order)

Baseline reference for every rung = P6-2 transfer rerun (parity-EXACT vs Round 5):
median MAE 20.99, MedAE 19.5 (fallback rate 0.80 — R6-C4 recorded on every rung too).

| Rung | Target information used | Method (fixed, minimal) | Never touches |
|---|---|---|---|
| L0 | none (= P6-2 rerun) | source MinMax + source y-normalisation (already run) | — |
| **La** "source-only scaling alternatives" | none beyond L0 (still zero target labels/cycles) | 3 scaler variants, chosen by the SAME rotated source-battery selection: (1) RobustScaler (median/IQR) (2) StandardScaler (z-score) (3) QuantileTransformer(output uniform, n=100) — all fit on SOURCE pool only | target entirely |
| **Lb** "unsupervised target-domain feature alignment" | target TRAINING cells' features only (no labels) | per-feature affine match to source scale: for each feature j, transform target values by (x_j - median_j,target) * IQR_j,source/IQR_j,target + median_j,source — fit on target TRAINING cells only. Guard: assertion in code that the test cell's rows are excluded from ALL fits. Alternative variant (recorded, not tuned): source-projected PCA-whiten/PCA-reconstruct on target training features (components fixed at 5 = full rank, deterministic). | test cell, any target label |
| **Lc** "simple one-cell output calibration" | + 1 target cell WITH labels (the LOCO adapt cell, same split as adapt2) | isotonic-free linear recalibration: fit yhat->y affine correction (slope+intercept, least squares) on the ONE adapt cell's predictions, then re-predict the remaining 7 test cells with the corrected output layer. This precedes any NN fine-tuning (advisor's "before trying additional neural-network fine-tuning"). | the 7 evaluated cells' labels |

Guard rails carried from R6-C3/C4:
- same seeds (5), same architecture/config selection path as phase5 transfer (rotated battery-wise over source), same outer-test isolation (test cell never used anywhere);
- every rung CSV records `sel_degenerate` (fallback) + `variant` label;
- no AE touching, no feature additions, no new estimator beyond the ladder item itself;
- BPNN stays the backbone for La/Lb/Lc (the ladder aligns the DATA fed to the same trained model family — we are diagnosing recoverability of the SAME transfer setup, not model shopping).

## Runs and costs

- La: 3 variants × 2 pools × 5 seeds, but selection reuses phase5's selected config per (pool,seed) — only refit + predict per variant ⇒ cheap (~30 min CPU total, est.).
- Lb: 2 variants × 2 pools × 5 seeds (affine, PCA) ⇒ similar (~30 min CPU).
- Lc: 1 protocol × 2 pools × 5 seeds × 8 adapt cells (same shape as adapt2 run) ⇒ ~similar to adapt2 arm (~35 min CPU, est.).
- All rung runs use `--dump-preds` equivalents for per-cycle analysis (support-zone decomposition applies to every rung).

## Success/stop criteria (pre-registered)

- Rung improved over L0 iff median MAE drops ≥ 5% absolute-relative with the same-direction MedAE movement; otherwise record as "no recovery".
- Stop and report if any rung uses test-cell information (assertion) — that rung is void.
- P6-5b (Clean-6T ablation) stays OPTIONAL and LAST: only Lc+fine-tune warm-start variant, one run, compared against Round 5 adapt2_C6T; skipped without affecting the main report.

## Deliverables

- `phase6_ladder_La/b/c_*.csv` + per-cycle dumps + `phase6_alignment_summary.md` (progression table L0→Lc with MAE/MedAE/frac(yhat>115%)/fallback per rung).
- Report section follows R6-C5 progression as the final block before conclusions.
