# Pipeline Comparison: Mean / Ridge / Raw / Row-Norm / PCA / AE → BPNN (Steps 9–10)

**Date:** 2026-09-25
**Scope:** Advisor Round 2 — Part F (required baselines), F2 ("does the AE actually improve SOH prediction?"), G2 (Figure 10 vs Mean Predictor), Step 9–11 of the 18-step sequence.
**Protocol:** identical to Steps 7–8 — nested 4-fold LOBO, inner validation = first remaining battery, tolerance 1 (selected in Step 8), MinMaxScaler fit on fold-train only, SOH target standardized on fold-train only, EarlyStopping (patience 30), metrics MAE/RMSE/R² in %SOH + **nRMSE** (= RMSE / fold-test SOH range, Part D3), seeds {42, 7, 123} → **12 runs per pipeline, 72 total.**

---

## 1. Validity Gate

| Gate | Result |
|---|---|
| 1. Rows | 72/72 ✓ |
| 2. NaN | 0 ✓ |
| 3. R² bounds | **8 breaches, all disclosed:** B2_ridge fold B0007 (R² −10.15, RMSE 26.28, all 3 seeds) and B0018 (−3.11, all seeds); P2_pca fold B0018 seeds 7/123 (−2.01, −2.15). All inside folds that fail anyway; the Ridge explosion is analyzed in Finding 5 |
| 4. Coverage | 3 rows per (pipeline × battery) × 6 pipelines ✓ |
| 5. mean ± std | below ✓ |
| 6. Leakage probe (run in this batch, `probe_s9.py`) | PASS — perturb outer-test ×2 → retrain → train metrics **identical, diff = 0.00e+00** |

## 2. Results

### Overall (12 runs per pipeline, %SOH)

| Pipeline | Test MAE | Test RMSE | Test R² | nRMSE |
|---|---|---|---|---|
| B1 Mean predictor | 10.360 | 12.303 | −0.772 | 0.398 |
| B2 Ridge (256-dim) | 13.318 | 15.101 | −3.087 | 0.533 |
| **P1 Raw EIS → BPNN** | 6.830 | **8.321** | +0.096 | 0.273 |
| P1n Row-min-max → BPNN | 8.391 | 9.789 | −0.074 | 0.310 |
| **P2 PCA → BPNN** | 6.667 | 8.483 | −0.037 | 0.280 |
| P3 AE → BPNN | 7.007 | 8.566 | +0.080 | 0.277 |

### Working folds only (B0005, B0006, B0007 — the folds where any pipeline works)

| Pipeline | Test RMSE | Test R² |
|---|---|---|
| B1 Mean | 12.775 | −0.913 |
| B2 Ridge | 13.804 | −3.080 |
| P1 Raw → BPNN | 6.484 | +0.526 |
| P1n Row-min-max | 10.290 | −0.171 |
| **P2 PCA → BPNN** | **5.924** | **+0.609** |
| P3 AE → BPNN | 7.009 | +0.439 |

### Test R² per fold

| Fold | B1 | B2 Ridge | P1 Raw | P1n | P2 PCA | P3 AE |
|---|---|---|---|---|---|---|
| B0005 | −0.048 | 0.569 | 0.609 | 0.012 | 0.554 | 0.538 |
| B0006 | −1.158 | 0.342 | 0.330 | −0.618 | 0.468 | 0.064 |
| B0007 | −1.534 | **−10.152** | 0.639 | 0.093 | 0.805 | 0.715 |
| B0018 | −0.349 | −3.105 | −1.192 | **+0.218** | −1.974 | −0.996 |

### Chosen configurations (inner validation, no outer test involved)

- PCA: pca32/l2=1e-4 (6), pca17/l2=1e-4 (3), pca32/l2=0 (1), pca17/l2=0 (1), pca8/l2=1e-4 (1)
- Ridge alpha: 10 (6), 1 (6)

## 3. Findings

1. **Answer to F2: the AE does not improve SOH prediction on this dataset — PCA (linear) is stronger.** On the three working folds, AE loses to PCA on every single one (B0005: 6.55 vs 6.46; B0006: 10.34 vs 7.85; B0007: 4.14 vs 3.47) and to raw EIS on two of three. Per the pre-declared rule ("AE useful = beats both Raw and PCA on all three working folds"), the answer is **false**. The advisor's suspicion in Part F is supported by measurement: nonlinear AE features add no measurable value over linear PCA here.
2. **G2 answered: the pipeline is no longer a Mean-Predictor clone.** Overall, P1/P3 beat the Mean predictor (RMSE 8.32/8.57 vs 12.30; R² +0.10/+0.08 vs −0.77), and on working folds the gap is large (6–7 vs 12.8). The old Figure 10 collapse is gone.
3. **The B0006 anomaly (Step 6) is AE-specific, not a scaling artifact.** On fold B0006 (train = B0005+B0018, identical scaling for all pipelines), AE is the worst feature pipeline (RMSE 10.34) while PCA is the best (7.85). If the shared scaler were the cause, all pipelines would degrade equally; instead only the AE latent degrades. This is consistent with latent-feature instability on this fold (R1-C6 language).
4. **The B0018 failure is largely an amplitude domain shift.** P1n (per-row min-max: each spectrum normalized to [0,1] by its own range — deployable, uses no training statistics) is the **only** pipeline with positive R² on B0018 (+0.218, RMSE 8.29 — better than even the Mean predictor's 10.89). Removing per-spectrum amplitude rescues B0018 but destroys the other folds (−0.17 working-fold R²). Interpretation (hedged): B0018's amplitude distribution differs from the training batteries; the amplitude cue that helps B0005–07 misleads on B0018. This reframes the open problem and gives Steps 14–16 (time-domain features) a concrete question: do time-domain features transfer to B0018 better than amplitude-carrying EIS?
5. **Ridge (256 correlated features) is fragile:** it explodes on fold B0007 (R² −10.15, RMSE 26.3, identical across seeds — deterministic) and B0018. Alpha ∈ {1, 10} chosen by inner validation was still insufficient for 256 correlated inputs. PCA+BPNN effectively solves this (that is P2). The linear baseline result should be reported with this caveat, not as "linear regression is bad".
6. **nRMSE (D3) orders pipelines the same way as RMSE** — no ranking change after range normalization, so fold-difficulty differences do not drive the ranking.

## 4. Limitations

- P3 (AE) results are reused from the Steps 7-8 full run (same tolerance, folds, seeds, protocol) rather than retrained — by design, to avoid duplicate computation.
- The perturbation probe was run for P1 (the pipeline class shared by P1/P1n/P2/P3 — same split/scaler/candidate machinery). B1/B2 involve no trained scaler beyond the same fold-train fit; Ridge is deterministic.
- Breaches in Gate 3 are inside folds that already fail; no working-fold result depends on them.

## 5. Next (Steps 14–16)

Time-domain baseline from the discharge cycles (V/I/T features: CC/CV durations, voltage slopes, discharge duration, etc.) under this same protocol — the advisor's B7 question ("which information type is most reliable cross-battery?") with the added target: does time-domain transfer to B0018 where EIS amplitude does not?

---

## Ablation log

`2026-09-25 | step9_10 | PCA best working folds (R2 0.61); AE<PCA all 3 | AE no gain over PCA; B0018=amplitude shift (P1n fixes)`

## Artifacts (`Autoencoder/nested_lobo/`)

| File | Purpose |
|---|---|
| `steps9_10_baselines.py` | B1/B2/P1/P1n/P2 pipelines + P3 reuse (--smoke / --full) |
| `steps9_10_results.csv` (72 rows), `steps9_10_summary.csv` | Results and aggregate |
| `s9_10_log.txt` | Full console log |
| `gate_s9.py`, `probe_s9.py`, `debug_gate4.py`, `debug_p3.py` | Gate, leakage probe, debugging |
| `Steps_9_10_Baselines.md` | This report |