# Appendix — Negative Results and Ablations (Draft v0.1, 2026-10-06)

> Purpose: record every rejected direction with its measured evidence, so no reader can assume a
> negative result was never tried, and so future work starts from the recorded failure mode.
> All numbers verified 2026-10-06. Sources per section.

## A.1 The autoencoder on both modalities (R3-C7)

| Configuration | Result | Source |
|---|---|---|
| AE features on TD inputs → BPNN | R² 0.43 vs 0.85 for raw TD features (B0006 degrades to −0.45) | `Steps_F3_I3_B7_Ablations.md` |
| AE on interpolated EIS (gain over raw) | +0.08; PCA +0.61 — PCA wins on all three working folds | `Steps_9_10_Baselines.md` |
| AE reconstruction target | the interpolated 256-point grid, not the measurement: +0.1 mΩ offset; B0006 Re(Z) RMSE ≈ 13× other cells, AE-specific | `Progress_Report_Steps1-18.md` |
| E_fusion (EIS latent anchored by TD) | R² 0.726 — positive on all four folds incl. B0018 (+0.67); adds nothing on top of full TD features (0.726 < 0.85) | `Progress_Report_Steps1-18.md` (B7) |
| Bottleneck size {3, 7, 17, 37, 67} | RMSE 8.30–8.82 %SOH, within 1 std — indistinguishable; 17 retained | `Steps_F3_I3_B7_Ablations.md` |
| AE pipeline vs ranking | TD-BPNN 3.59 > TD-Ridge 4.35 > E-fusion 4.89 > EIS pipelines 8.3–8.6 > mean 11.5 | Round 2 steps 14–16 |

Verdict (advisor-directed, recorded in `advisor_directives.md` R3-C7): the AE is a negative
result on both modalities; the pipeline proceeds without it; E_fusion's small gain on
weak-feature regimes is recorded as the open exception.

## A.2 Interpolation ablation (EIS representation)

Six grid × method configurations (linear/pchip/cubic × grids): RMSE 7.99–8.62 %SOH,
indistinguishable. Cubic's Step-5 overshoot shows no measured downstream penalty; PCHIP kept for
shape preservation. Root fact (Round 1): the AE fits the interpolated grid, and raw EIS has no
per-point frequency data in the NASA .mat files — the 0.1 Hz–5 kHz grid is a declared assumption.
*Source: `ablation_summary.csv`, `AE_Ablation_Results.csv`.*

## A.3 EIS tolerance ablation

EIS↔discharge cycle alignment tolerances 1/2/3: downstream metrics indistinguishable (RMSE
8.57–8.89 %SOH, all within 1 std) → pre-declared rule selects tolerance 1; the gap distribution
is bimodal (gap 1 or 3 for B0005–07). Tolerance = 1 keeps ~51 % of cycles EIS-aligned. The TD
feature family provably does not require EIS alignment (TD-All uses all 636 discharge cycles —
confirmed by the audit's repository checks). *Source: `Steps_7_8_Nested_LOBO.md` (steps 7–8);
R3 audit repository checks.*

## A.4 Self-referenced normalisation — rejected (5.3)

Dividing each battery's features by its own early reference (intended to remove per-cell scale):
Clean-8 0.810 → **0.075**. Mechanism measured: `cv_I_slope`'s reference is 6× smaller for B0018
than for the others, so self-referencing inflates that feature ~6× — self-referencing
*introduces* a scale mismatch instead of removing one. The mean is dragged below zero by B0018
alone (median 0.766); both are quoted. *Source: `phase3_selfref_verify.py` (9/9), summary md.*

## A.5 ΔSOH accumulation — rejected (5.4)

Predicting per-cycle decrements and accumulating: Clean-8 0.810 → **−4.785**. Error grows with
cycle position (corr up to +0.993) — the signature of integrating a biased increment. A monotone
projection cannot rescue it: clamping does not remove a linear drift. Anchor offset < 1 %SOH
everywhere, so the anchor is not the driver. Cross-check with [10]: EWDC's recursive predictor
succeeds *with* the ŷ₁ = 1 anchor of the Q/Q₀ definition; our Q/Qref scheme lacks that anchor,
and the two numbers must not be compared directly. *Source: `phase3_dsoh_verify.py` (7/7).*

## A.6 Partial-window features — not established as proxy-free (5.2)

Fixed 4.0–3.6 V discharge window: `win_dur` R²(capacity) = 0.995 > `dis_duration` 0.972 — the
window duration is a *stronger* proxy than the full discharge duration. Window means are proxies
at every length by construction. The window-length experiment (5.5) therefore measures the
*partial-window penalty*, not proxy-freeness: proxy-free flat 0.842–0.843 over 5–30 min;
proxy-laden rises 0.874 → 0.914. One caveat recorded by verification: W5-PF also drops
`dis_V_slope` and swaps `dis_mean_T` → `w5_mean_T`, so the W5 gain over the full-cycle reference
cannot be attributed to the shorter window alone. *Source: `phase3_window_verify.py` (7/7),
`phase3_windowlength_verify.py` (12/12).*

## A.7 Learning-curve and transfer rejections (R3-C6)

| Premise tested | Measured verdict |
|---|---|
| "Add B0025–B0056 (similar conditions)" | Not supported: pulsed-4A cells catastrophic (B0027 −132.8); heterogeneous pool hurts same-condition tests (0.933 at k=3 → 0.63–0.85 at k=13); within-condition curves positive (medians −1.25 → +0.15 → +0.32) |
| "Frozen model transfers to CALCE CS2" | median R² −37; label span 88–114 % vs 72–108 %; 0.5 C charge doubles charge-side feature scale |
| "One CS2 cell calibrates the model" | warm-adapt median −31; improves worst cells 3–7×, degrades best cells −2 → −43; scratch −68 |
| Control: LOCO within CS2 | 0.39–0.68 on 6/8 cells (pooled median 0.59) — parser/features/data are sound; failure is per-cell label offset |

*Source: `phase4_learning_curve_summary.md`, `phase4_cs2_summary.md`.*

## A.8 Configuration ablations that did NOT change conclusions

- BPNN loss MSE/MAE/Huber: RMSE 8.32–8.57, indistinguishable → MSE retained.
- Selection-guard fix regression: TD-All/Oracle 0/24 unchanged (fix touches only the degenerate
  Proxy-Free case, 0.732 → 0.854).
- `t_40_41` on top of `ic_peak_V`: 11/20 fold-seeds, mean Δ +0.039 — within noise; reported as
  unsupported (the Clean-8 claim is the paired 0.664 → 0.810 with `ic_peak_V` as the supported
  addition). *Source: `phase3_charge_verify.py` (8/8).*

## A.9 Instability disclosure

The proxy-free regime is unstable at the row level: 5 of 636 rows swing the headline between
0.490 and 0.664 across earlier runs. Every proxy-free claim is therefore quoted as a **paired**
result on identical (fold, seed) rows, never as a cross-run comparison. *Source: Phase 1
verification notes; Ch.4 row-set note.*
