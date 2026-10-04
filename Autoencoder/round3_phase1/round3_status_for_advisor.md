# Round 3 — status against every advisor item

Basis: the Literature Gap Audit (received 2026-09-26, 7 score-gap factors, R3-C1…C9) and the
advisor's GitHub response of 2026-09-28 (4 repository checks, Plan A approved).
Everything below is measured in `Autoencoder/round3_phase1/`; every number has a committed artifact
and an automated verification script behind it.

## Compliance table

| item | advisor's requirement | status | evidence |
|---|---|---|---|
| **R3-C1** | re-fit on all 3 training batteries | **done** | TD-All mean test R² 0.848 → 0.923; B0006 0.686 → 0.900; all 4 folds positive |
| R3-C1 | *alternative:* make the inner loop a 3-fold LOBO | **done** | 0.9174 vs 0.9231 (Δ −0.006) with a different config in 11/12 fold-seeds |
| R3-C1 | report per-fold **and** pooled R², RMSE in %SOH **and** Ah, **plus MAPE** | **done** | mean/median/std in every summary table; pooled per split |
| R3-C1 | repo check: all 636 cycles, or only EIS-aligned? | **done** | 636 discharge cycles used (168/168/168/132); 887 EIS records exist but were **not** used as a filter |
| R3-C1 | repo check: is the model really re-fitted on 3 batteries? | **done** | `fit_batteries` column = the 3 non-test batteries in every `refit_on_3` row |
| **R3-C2** | protocol-gap: random / chronological / LOBO; expect random > 0.97 | **done, prediction confirmed** | random TD-All **0.979**; pooled random 0.989; LOBO 0.927; chronological −1.028 |
| **R3-C3** | three settings under LOBO × seeds (TD-All / TD-Proxy-Free / oracle) | **done** | 0.927 / 0.845 / 0.671 over 5 seeds |
| R3-C3 | list every TD feature; label each safe or proxy | **done, and it changed a claim** | `r3c3_feature_classification.md`: `dis_duration` 0.972 and `dis_mean_V` 0.948 are proxies |
| R3-C3 | oracle should reach R² ≈ 1 | **confirmed in scope, corrected out of scope** | 0.992 under the same-battery random split; 0.671 under LOBO |
| **R3-C4** | positioning against the 2026 EIS+cross-battery paper | **done** | contribution (1) now quantified on two axes; see below |
| **R3-C5** | proxy-free improvements (items 5.1–5.5) | **done (5.1 supported; 5.2 not established; 5.3, 5.4 rejected; 5.5 done)** | TD-Clean-7 0.772 / Clean-8 0.810 with no feature above 0.49 R²(capacity); see "Phase 3" below |
| **R3-C6** | wider validation (B0025+, CALCE) | **not started** | deliberately deferred |
| **R3-C7** | demote the AE to a negative result | **not started** | deferred |
| **R3-C8** | send back 4 items | **4/4 ready** | this document, section "Answers the advisor asked for" |
| **R3-C9** | citation verification | **not started** | deferred |

## The two axes that explain the score gap

Same data, same model family, same grid, same 5 seeds, same leakage discipline; only one variable
changes per axis.

**Axis 1 — protocol** (per-fold mean R², TD-All): chronological **−1.028** → nested LOBO **0.927** →
random same-battery **0.979** → pooled random **0.989**.

**Axis 2 — capacity proxy** (nested LOBO, per-fold mean R²): TD-Clean-4 **−0.400** →
TD-Clean-6 **0.490** → TD-Proxy-Free **0.845** → TD-All **0.927**.

## The finding that changes a claim

`TD-Proxy-Free` was built by dropping `dis_duration` alone. The R3-C3 audit shows `dis_mean_V` is
collinear with it (within-battery r = 0.941) and alone explains 94.8 % of within-battery capacity
variance, so the proxy was still in the input under another name.

Measured, under the same protocol and seeds:

| set | features | mean R² | median R² | RMSE (%SOH) |
|---|---|---|---|---|
| TD-All | 8 | 0.927 | 0.947 | 2.56 |
| TD-Proxy-Free | 7 | 0.845 | 0.876 | 3.81 |
| TD-Clean-6 | 6 | **0.490** | 0.556 | 6.79 |
| TD-Clean-4 | 4 | **−0.400** | −0.136 | 11.27 |

Removing `dis_mean_V` made **19 of 20 fold-seeds worse** (mean drop 0.354). Therefore the
"proxy-free" figure is **0.490**, not 0.845, and any earlier use of 0.845 in that role is withdrawn.

Two further measurements pin the mechanism:

1. **Leave-one-feature-out (ridge, same protocol).** Dropping `dis_duration` costs −0.500 and
   `dis_mean_V` −0.376; dropping any of the other six changes the score by between +0.024 and
   −0.003. The entire cross-battery signal lives in those two features.
2. **The drop is a generalisation failure, not uninformative features.** TD-Clean-6 fits its own
   training batteries (median train R² 0.934) and fails on the unseen one (0.490). The collapse is
   concentrated in B0006 (0.876 → −0.073), the cell whose reference capacity is the outlier, which
   says the two proxy features also carry the per-battery scale a LOBO model cannot otherwise
   observe.

## Where our measurement disagrees with an advisor expectation

Reported because the disagreement is measured, not argued.

1. **Oracle ≈ 1 is protocol-scoped.** Under LOBO the oracle reaches 0.671, not ≈ 1: `SOH = Q/Q_ref`
   and Q_ref differs per cell (1.842 / 2.018 / 1.883 / 1.840 Ah), so one global duration→SOH map
   cannot be exact across batteries. Under the same-battery random split the oracle reaches 0.992,
   so the original claim is right about the literature's protocol — which is exactly why the
   literature's scores are high.
2. **The alternative inner loop does not specifically help B0006.** The audit expected it to. It
   gives 0.891 on B0006 against 0.900 for the current rule, and 0.9174 overall against 0.9231. What
   helped B0006 was the re-fit on 3 batteries (0.686 → 0.900).
3. **A pooled R² on a chronological split is misleading.** `chronological_within` scores −1.028 per
   fold but +0.850 pooled — audit factor 5 visible in our own numbers.

## Answers the advisor asked for (R3-C8)

1. **Complete definition of every TD feature.** Eight features, defined in
   `nested_lobo/extract_time_features.py` and classified in `r3c3_feature_classification.md`.
   Discharge side (from the labelled discharge cycle itself): `dis_duration` (t_last − t_first),
   `dis_mean_V`, `dis_mean_T`, `dis_V_slope` (OLS slope of V vs t). Charge side (from the charge
   cycle that immediately **precedes** the labelled discharge, so no future information enters):
   `cc_dur` (time to reach 4.19 V), `cv_dur` (remainder), `cv_I_slope` (OLS slope of current during
   CV), `ch_mean_T`. Label alignment is exact: each discharge cycle carries its own measured
   capacity, with no tolerance mapping.
2. **Is the model re-fitted on three batteries?** Yes. Every `refit_on_3` row records the three
   fitting batteries explicitly, and the `pre_refit` stage (2 batteries) is kept alongside so the
   effect is measured rather than assumed: 0.848 → 0.923.
3. **How many TD samples, and are only EIS-aligned cycles used?** 636 discharge cycles
   (B0005/B0006/B0007 168 each, B0018 132). All 636 are used; EIS alignment is **not** a filter.
   For reference, the raw files contain 887 impedance records (278/278/278/53), so restricting to
   EIS-aligned cycles would have discarded a large part of the discharge history.
4. **Per-fold R²/RMSE and pooled R².** Reported in `steps14_16_refit_summary_cpu.csv`,
   `td_proxy_audit_summary_cpu.csv`, `protocol_gap_exp_cpu_summary.csv` and the pooled files, all as
   mean / median / std, with RMSE in %SOH and Ah and MAPE alongside.

## Phase 3 — proxy-free improvements (R3-C5, items 5.1–5.5, complete)

Baseline for all comparisons: **TD-Clean-6** (6 features, no label-correlation above 0.90), mean R²
0.490 under nested LOBO. Paired comparisons are on identical rows (631 cycles: five have no usable
CC phase, so `ic_peak_V` is NaN there); 5 seeds; selection guard active.

| item | advisor's suggestion | result | mechanism / evidence |
|---|---|---|---|
| **5.1** | charging-segment features (CC time in V-windows, CV time, IC peak) | **SUPPORTED** | `ic_peak_V` is the only safe addition (R²(capacity) 0.489): Clean-6 0.490 → Clean-7 **0.772** (improves 15/20 fold-seeds) → Clean-8 **0.810** (+`t_40_41`, but the extra is within noise — 11/20, Δ +0.039). The paired honest claim is 0.664 → 0.810 on identical rows. |
| 5.2 | fixed discharge voltage window 4.0 → 3.6 V | **NOT ESTABLISHED** | 5 of 7 window features are proxies (`win_dur` R²(capacity) 0.995 — worse than the whole-cycle `dis_duration` 0.972, because at constant current window time is a fixed fraction of charge). The one admissible swap (`w_mean_T` for `dis_mean_T`) helps in only 12/20 cells, Δ +0.047 < the known proxy-free instability. Also: ΔV = 0.1/0.2 V cannot form a window on these files (switch-on step ~0.2 V); ΔV = 0.3 V gives only 8–13 samples. |
| 5.3 | self-referenced normalisation (divide by first-cycle value) | **REJECTED** | 0.810 → 0.075; B0018 collapses in 5/5 seeds. Its `cv_I_slope` reference is 6.0× smaller than the other cells, so self-referencing *introduces* a ~6× scale mismatch. The premise (feature offsets) is also wrong: measured feature-level reference spreads are 1.03–1.27× for 6 of 8 features; the B0006 gap (2.035 vs ~1.86 Ah) is a **label** offset, not a feature offset. |
| 5.4 | monotonic prior: predict ΔSOH and accumulate (as EWDC [10]) | **REJECTED** | 0.810 → −4.785. A biased increment integrates linearly: corr(cycle position, \|error\|) up to +0.993; anchor offset < 1 %SOH, so the anchor is not the cause. EWDC's 0.975 does not transfer (their features are proxy-laden with a far stronger per-cycle signal; EWDC is not in the local materials, so the convention could not be checked — question sent to advisor). |
| **5.5** | window-length curve (RMSE vs 5/10/20/30 min) | **DONE — key figure** | Proxy-free curve is **flat**: 0.842 / 0.828 / 0.830 / 0.843 at 5/10/20/30 min (0 of 96 fold-seeds degenerate). Five minutes of discharge is enough. Proxy-laden rises 0.874 → 0.914. Caveat: the W5-PF set also drops `dis_V_slope` and swaps `dis_mean_T` for `w5_mean_T`, so the gain over the full-cycle Clean-7 reference is not attributable to the window alone. |

**Result summary:** one supported improvement (5.1, Clean-8 = 0.810 ≈ 96 % of proxy-laden
TD-Proxy-Free 0.845 — and Clean-8 contains **no feature above 0.49** label-correlation), one usable
figure (5.5), and three measured negatives (5.2, 5.3, 5.4), each with an identified mechanism.

**A caution on the thesis title.** "Proxy-free, partial-window" needs a qualification: a partial
window is **not** proxy-free by virtue of being partial — `mean_V` inside any window is a proxy at
every length, and window durations are the strongest proxies measured. Only window mean-temperature
stays SAFE. The claim survives only with that qualification stated.

## Next

- **R3-C6.** Wider validation: add B0025–B0056 (learning curve vs number of training batteries),
  then cross-dataset to CALCE CS2. Four cells cannot support a generalisation claim.
- **R3-C7** (demote the AE to a documented negative result) and **R3-C9** (citation verification)
  remain deferred by decision, not by omission.

Verification (re-run 2026-10-05, all passing): `phase1_verify.py` 61/61, `protocol_gap_verify.py`
23/23, `td_clean_verify.py` 7/7, `data_provenance_audit.py` 26/26, `phase3_charge_verify.py` 8/8,
`phase3_selfref_verify.py` 9/9, `phase3_window_verify.py` 7/7, `phase3_dsoh_verify.py` 7/7,
`phase3_windowlength_verify.py` 12/12, `phase3_feature_audit.py` 50/50 — **210/210**;
leakage probes `max|diff| = 0.00e+00` on every protocol and on the clean feature sets.

*Last updated: 2026-10-05 — Phase 3 section added (items 5.1–5.5); R3-C5 row moved to done;*
*verification line covers all 10 suites (210 checks).*