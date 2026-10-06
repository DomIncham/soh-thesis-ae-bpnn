# Chapter 5 — Discussion and Limitations (Draft v0.1, 2026-10-06)

> Sources: audit factors (R3 advisor audit), protocol/proxy axes (`phase2_summary_two_axes.md`),
> Phase-3 verdicts 5.1–5.5, Phase-4 wider validation (`phase4_learning_curve_summary.md`,
> `phase4_cs2_summary.md`), AE evidence (`nested_lobo/Progress_Report_Steps1-18.md`),
> citation verification (`r3c9_citation_verification.md`). Numbers re-verified 2026-10-06 (210/210).
> Style: A2-B1, short sentences, no overclaiming; every claim carries its measured number.

---

## 5.1 Why published R² is high — the seven factors, measured

The audit listed seven factors that separate published scores from cross-battery reality. Our
experiments turn the first two from cautions into measurements on our own pipeline:

**Factor 1 — the split protocol (largest effect).** With identical features and model, the split
alone moves R² from **−1.03 (chronological) to +0.98 (random)** on the same data (Ch.4 §4.2).
The literature's headline numbers are produced mostly by same-battery splits: [1] trains on the
first 80 discharges of the same cell it tests; [5] uses the first 80 % of cycles; [6] uses a
random split. Under a nested LOBO — the test battery never seen — the same model scores 0.927.
The direction is confirmed by [11], which reports both protocols on the same pipeline: 0.9788
random vs 0.7855 battery-wise, a drop of 0.19 that our own data reproduces (0.979 → 0.927).

**Factor 2 — capacity proxies (very large, and universal in the strong claims).** The strongest
unseen-battery results in the verified list all consume label-carrying inputs: [3] feeds Q(k−1)
explicitly; [4] feeds previous-cycle capacity and cycle number; [9] includes the cycle index as
a "degradation indicator"; [10] (EWDC, the 0.975 result) uses cycle index and cumulative charged
quantity among its 17 charge-segment features. In CC discharge, capacity = I × t, so a full-cycle
feature family carries the answer. Removing `dis_duration` and `dis_mean_V` from our feature set
moves LOBO R² from 0.927 to **0.490** (Clean-6); recovering with charge-segment `ic_peak_V` gives
**Clean-8 = 0.810**. The proxy axis moves the score between −0.40 and 0.93 (Ch.4 §4.3).

**Factor 3 — number of training batteries.** [11] uses 34 cells; [9] uses 3 (B0005/06/07) and
hits the same B0006 wall we do. Our four-battery pool sits between these, and the learning-curve
experiment (§5.2) shows why more cells do not automatically help.

**Factor 4 — extrapolation.** B0006 falls to 57 %SOH in our data while the others stop at
70–74 %. The best verified LOCO result on B0006 is [9]: R² 0.2464 → 0.5286 — better, but still
nowhere near a same-battery number. The B0006 failure is common to the strict protocols in the
list, not specific to ours.

**Factor 5 — pooled R².** Pooling adds between-battery variance to the denominator. Our
chronological split scores −1.03 per fold but +0.85 pooled (Ch.4 §4.2). A paper that reports only
the pooled number on a chronological split looks healthy while every fold is negative. We report
both, per fold and pooled, everywhere.

**Factor 6 — SOH definition and units.** The verified papers use Q/Q_N ([1], [13]), Q/Q(1)
([9]), Q/Q₀ with ŷ₁ = 1 ([10]), per-cell initial capacity ([7]). An RMSE of 0.02 means 1–2 %SOH
in one definition and a different quantity in another. Our RMSE is stated in %SOH (Q/Q_ref,
first five cycles) and in Ah, side by side. Ch.2's comparison table annotates the unit and the
protocol of every number.

**Factor 7 — discharge cut-off voltages.** B0005 2.7 V, B0006 2.5 V, B0007 2.2 V, B0018 2.5 V.
Whole-cycle mean features carry the per-cell cut-off; a fixed voltage window removes that
difference — this is why `win_mean_T` beats `dis_mean_T` in 5.2 even though it is slightly more
label-correlated (verified note, `phase3_window_verify.py`). It is also why the window arm of
5.2 remains a proxy: the window carries the same per-cell scale information by another route.

## 5.2 "More batteries" does not fix cross-battery estimation

The learning-curve experiment (420 fold-runs, 14 cells) measures the premise behind "just add
more data":

- Only B0025–28 share the original condition (24 °C, 2A/pulsed...). The 43 °C, 4 °C, and
  pulsed-4A cells are different domains, and the pulsed cells are catastrophic under every
  setting (B0027: R² −132 at k = 13), because discharge-side features are functions of the load
  profile first and of degradation second.
- Adding heterogeneous cells to the pool **hurts same-condition tests**: room-2A reference
  protocol reproduces at 0.933 (k = 3), and degrades to 0.63–0.85 when the pool widens to 13.
- Within a condition, the curve is still positive: Clean-8 medians rise −1.25 → +0.15 → +0.32
  for k = 3 → 7 → 13.

Implication: the learning-curve claim must be stated **per condition**. A pooled heterogeneous
LOBO number is a pool-design statement, not a model verdict. The right venue for a pooled
generalisation claim is a dataset where the conditions actually match — which is what the
cross-dataset test addressed.

## 5.3 Cross-dataset transfer fails on per-cell label offset — and the control proves why

NASA → CALCE CS2 (same chemistry, same nominal charge protocol) fails in every transfer arm
(frozen median R² −37; 1-cell warm-adapt −31; scratch −68), while the within-CS2 control reaches
0.39–0.68 on 6 of 8 cells. Three measured facts explain the failure:

1. **Label-scale offset**: CS2 SOH spans 88–114 % vs NASA 72–108 %; a frozen model must
   extrapolate.
2. **Charge-protocol scale**: the 0.5 C CS2 charge makes `t_40_41` / `cc_dur` ≈ 2× the NASA
   scale — the features themselves shift.
3. **One cell is not calibration**: warm-starting on one CS2 cell pulls every prediction toward
   that cell's offset — it improves the worst cells 3–7× and degrades the previously-best cells
   (−2 → −43). This is the same per-cell offset documented inside NASA (B0006's 2.018 vs ~1.85
   Ah reference).

This is consistent with the rejected ΔSOH-accumulation scheme (5.4): integrating biased
per-cycle increments drifts linearly with cycle position (corr up to +0.993). Cross-dataset SOH
prediction requires per-cell calibration information, which the nested protocol deliberately
does not grant. The failure is therefore a protocol-scoped statement, not a data-quality
statement — the control is what makes it sayable.

## 5.4 The AE question — a documented negative result

The two-stage AE+BPNN architecture, the starting point of this thesis, was tested on both
modalities under the strict protocol:

| Evidence | Numbers |
|---|---|
| AE features on TD inputs vs raw TD features | R² 0.43 vs 0.85 |
| AE on EIS vs PCA on EIS (gain over raw) | +0.08 vs +0.61 |
| AE reconstruction target | the interpolated 256-point grid, not the measurement (+0.1 mΩ offset; B0006 anomaly is AE-specific) |
| E_fusion (EIS latent anchored by TD features) | 0.73 — positive on all four folds, including B0018 (+0.67) |

Two honest qualifications accompany this table:

- **Fusion is not zero**: the E_fusion pipeline (0.73) is positive on every fold and beats every
  EIS-only pipeline (8.3–8.6 RMSE). The precise statement is: the EIS latent adds no value **on
  top of a full TD feature set** (0.73 < 0.85), and AE features are worse than raw features on
  both modalities. The AE as a *representation* is the negative result; a small EIS-assisted
  gain on weak-feature regimes remains open.
- The AE's latent reconstructs the interpolation grid we fed it, not the measurement — the
  model-fitting problem identified in Round 1 (pchip interp, 0 % physical reference) propagates
  into representation learning.

Decision (advisor-directed, R3-C7): the AE moves to the Appendix as a negative result; the main
pipeline is TD-BPNN. The thesis title no longer carries "Autoencoder".

## 5.5 Cycle-level vs real-time estimation

All features in this thesis are cycle-level: a complete discharge (or charge) segment is
required. Partial-window features (5.2, 5.5) reduce the observation time to 5–30 minutes but
remain cycle-level constructs — they predict the SOH of the cycle, not a live stream. The
verified partial-window literature ([5]: 10–30 min; [6]: early discharge segment) sits in the
same regime. Real-time (in-flight) estimation is out of scope for this thesis and is stated as
such.

## 5.6 Limitations

1. **Four NASA batteries** (6.1 adds ten more under different conditions — reported separately).
   Cell-to-cell variation is under-sampled; the LOBO folds share one laboratory and one
   chemistry.
2. **EIS frequency assumption**: the NASA .mat files do not carry per-point frequencies; the
   0.1 Hz–5 kHz grid is a declared interpolation assumption. This affects the EIS/AE arm only
   (already the negative result), not the TD pipeline.
3. **Clean-4's collapse is confounded**: its two remaining slope features are numerically fragile
   (per-battery correlation flips sign) — the score is not evidence about proxies in general.
4. **`random_pooled` leaks battery identity by construction**; it is quoted only as a
   protocol-gap data point, never as performance.
5. **Cross-dataset scope**: CS2 has no temperature channel (Clean-6T disclosed); the transfer
   verdict covers one source-target pair, same chemistry.
6. **Proxy-free instability**: 5 of 636 rows swing the proxy-free headline between 0.490 and
   0.664 — the paired claim is always quoted with its row set.
7. **Literature comparison**: every number quoted in Ch.2 carries its unit and protocol; quartile
   checks are confirmed on JCR/SJR before the final PDF (rule 4 of R3-C9).

## 5.7 What the thesis contributes (measured, not asserted)

1. **Quantification of protocol and proxy effects on one fixed pipeline**: split protocol moves
   R² between −1.03 and 0.99; proxy removal moves it between −0.40 and 0.93. Both axes are
   measured on our own runs, not imported from the literature.
2. **A defensible unseen-battery, proxy-audited number**: Clean-8 = 0.810 (nested LOBO, 5
   seeds), with the strict proxy-free floor 0.490 stated alongside.
3. **A cross-dataset negative result with a positive control** — transfer failure located at the
   per-cell label offset, not the pipeline.
4. **A documented AE negative result** with the mechanism (interpolation reconstruction) and the
   exception (E_fusion on weak-feature regimes) both recorded.
5. **A verified literature comparison**: 13 studies checked against their full PDFs; the audit's
   two anchor numbers confirmed verbatim; units and protocols annotated per row.
