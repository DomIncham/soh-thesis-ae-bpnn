# Chapter 4 — Results (Draft v0.1, 2026-10-06)

> Sources: `phase2_summary_two_axes.md` (protocol + proxy axes), `phase1_oracle_findings.md`,
> `phase3_*_summary.md` (items 5.1–5.5), `phase4_learning_curve_summary.md` + `phase4_cs2_summary.md`
> (wider validation). All numbers verified by the 210-check suite + Phase 4 gates. Protocol noted
> next to every number. Style: A2-B1, short sentences, no overclaiming.

---

## 4.1 Setup (what is held fixed)

All results in this chapter share one protocol unless stated otherwise:

- Data: NASA B0005/06/07/18, 636 discharge cycles. SOH = Q / Q_ref × 100, Q_ref = mean of the
  first five discharge capacities. Results in %SOH.
- Model: TD features → BPNN. Same architecture grid and same inner-selection rule everywhere.
- Leakage discipline: fold-train-only standardisation, train/test masks asserted disjoint,
  leakage probes at max|diff| = 0.00e+00 (measured, not assumed).
- Seeds: 42, 7, 123, 2024, 11 (5 seeds). LOBO uses `refit_on_3` (the final model is re-fitted on
  all three training batteries after inner selection — R3-C1).
- Metrics: MAE, RMSE (%SOH), R² per fold, plus pooled R².

## 4.2 Axis 1 — the evaluation protocol (R3-C2)

Per-fold mean R², TD-All features:

| Protocol | Oracle-proxy | TD-All | TD-Proxy-Free |
|---|---|---|---|
| Random split, same battery | **0.992** | **0.979** | 0.978 |
| Random split, pooled across batteries | 0.815 | 0.989 | 0.978 |
| Nested LOBO, unseen battery (ours) | 0.663 | **0.927** | 0.854 |
| Chronological split, same battery | 0.179 | **−1.028** | −5.234 |

Findings:

1. The protocol alone moves the headline from −1.028 to 0.989 on the same features and the same
   model. The random-split 0.979 confirms the R3-C2 prediction (> 0.97).
2. The "oracle ≈ 1" claim is **protocol-scoped**: 0.992 under the same-battery split the literature
   uses, but 0.663 under LOBO. Published scores are high partly because published protocols are
   same-battery. This is now measured, not asserted.
3. Pooling inflates R²: `chronological_within` scores −1.028 per fold but +0.850 pooled. A paper
   reporting only pooled R² on a chronological split looks healthy while every fold is negative.
   This demonstrates audit factor 5 on a fixed representation.

## 4.3 Axis 2 — the capacity proxy (R3-C3, R3-C5)

Nested LOBO (phase-3 runs, 5 seeds per fold):

| Feature set | Features | Mean R² | Median R² | Mean RMSE |
|---|---|---:|---:|---:|
| TD-All | 8 | **0.927** | 0.947 | 2.56 |
| TD-Proxy-Free (drop `dis_duration`) | 7 | **0.845** | 0.876 | 3.81 |
| TD-Clean-6 (also drop `dis_mean_V`) | 6 | **0.490** | 0.556 | 6.79 |
| TD-Clean-4 (also drop `cc_dur`, `cv_dur`) | 4 | −0.400 | −0.136 | 11.27 |

Row-set note: this table is the phase-2 axis-2 experiment (its own runs). The phase-1 audit
protocol run (§4.2) measured TD-Proxy-Free at 0.854 with a different row set — the two numbers
(0.845 vs 0.854) must not be compared to each other; each is quoted only against numbers from
the same row set.

Paired on identical (fold, seed): removing `dis_mean_V` made **19 of 20** fold-seeds worse
(mean drop 0.354).

Mechanism. `dis_mean_V` is collinear with `dis_duration` (within-battery r = 0.941) and alone
explains 94.8 % of within-battery capacity variance. The proxies do not only carry the label —
they carry the **per-battery scale** that a LOBO model has no other way to observe. Remove them
and the model cannot place an unseen battery on the SOH axis. The collapse concentrates in B0006
(0.876 → −0.073), the cell whose Q_ref is the outlier (2.018 vs ~1.85 Ah).

**Restated contribution (2).** The defensible unseen-battery proxy-audited number is
TD-Clean-8 = **0.810** (Clean-6 + `ic_peak_V` + `t_40_41`); the strict Clean-6 number is 0.490.
The 0.845 figure must not be quoted as proxy-free — it contains a proxy-equivalent feature.

## 4.4 Proxy-free improvements tested (R3-C5: 5.1–5.5)

| Item | Result | Verdict |
|---|---|---|
| 5.1 Charge-segment features (+`ic_peak_V`) | 0.772 vs Clean-6 0.490 (15/20 folds) | **Supported** |
| 5.2 Fixed discharge window 4.0–3.6 V | `win_dur` R²(cap) 0.995 > `dis_duration` 0.972 | **Not established** — window features are proxies |
| 5.3 Self-referenced normalisation | 0.810 → 0.075; B0018 reference scale 6× smaller | **Rejected** — introduces scale mismatch |
| 5.4 ΔSOH accumulation | 0.810 → −4.785; corr(cycle position, error) up to +0.993 | **Rejected** — biased increment integrates linearly |
| 5.5 Window-length curve (5–30 min) | proxy-free flat 0.842–0.843; proxy-laden rises 0.874 → 0.914 | No partial-window penalty; flatness is proxy-free evidence |

Note on 5.2: a partial window is *not* proxy-free by construction — window means are proxies at
every length. The defensible phrasing is "proxy-audited, partial-window".

## 4.5 Wider validation (R3-C6)

**6.1 Learning curve (within NASA).** Adding cells B0025–B0056 under mixed conditions does not
help: only B0025–28 share the 24 °C 4-A pulsed condition; the rest are 43 °C / 4 °C / corrupt.
Cross-condition LOBO (14 cells) reaches mean R² −12 at k = 13 (B0027 alone: −133). Heterogeneous
training helps out-of-domain slightly (all-13 median −24 vs room-only −37) but hurts in-domain
(room 0.933 → 0.75). Report per-condition. The premise "add B0025–B0056 (similar conditions)" is
not supported by the data.

**6.3 Cross-dataset (NASA → CALCE CS2), four arms:**

| Arm | Result |
|---|---|
| Frozen (no adaptation) | median R² −37 — does not transfer |
| Scratch, 1 CS2 cell | ≈ −68 |
| Warm-adapt, 1 CS2 cell (lr 1e-4 + grad-clip) | ≈ −31, no positive cell |
| Within-CS2 control (LOCO) | 0.39–0.68 on 6/8 cells |

The within-domain control proves the failure is **domain shift** (per-cell label offset: CS2 SOH
spans 88–114 % vs NASA 72–108 %; charge 0.5C vs 0.75C doubles `t_40_41`/`cc_dur`), not data or
feature quality.

## 4.6 The AE is a negative result (R3-C7)

| Evidence | Numbers |
|---|---|
| AE-on-TD vs raw TD features | R² 0.43 vs 0.85 |
| AE on EIS vs PCA on EIS | +0.08 vs +0.61 |
| AE reconstruction | reconstructs the interpolation grid, not the measurement |
| E_fusion (EIS latent + TD) | 0.73 < TD-only 0.85 |

Claim: the AE bottleneck adds no measurable value on either modality; PCA is the stronger EIS
reducer. The AE is reported as a negative result (Appendix) and the pipeline proceeds without it.

## 4.7 Headline summary

| Question | Answer (measured) |
|---|---|
| How much of published accuracy is protocol? | Random 0.979 vs LOBO 0.927 (TD-All); oracle 0.992 → 0.663 |
| How much is the capacity proxy? | 0.927 (TD-All) → 0.490 (Clean-6); Clean-8 recovers 0.810 |
| Unseen-battery, proxy-audited number | Clean-8 = 0.810 (nested LOBO, 5 seeds) |
| Does the AE help? | No — negative result on both modalities |
| Does the model transfer cross-dataset? | No — domain shift; within-domain control 0.39–0.68 |

## 4.8 Limitations to state in this chapter

1. Four NASA batteries (6.1 adds 10 more under different conditions — reported separately).
2. Clean-4's low score is confounded by numerically fragile slope features (r flips sign
   per battery) — not evidence about proxies.
3. `random_pooled` leaks battery identity by construction — quoted as a protocol-gap data point only.
4. Per-point EIS frequency is not recoverable from the NASA .mat files (0.1 Hz–5 kHz grid is a
   declared assumption) — affects the EIS/AE arm only.
5. Chapter 2 literature comparisons wait for R3-C9 citation verification (EWDC [10] reference).
