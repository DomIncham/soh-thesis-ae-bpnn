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
| **R3-C5** | proxy-free improvements | **started** | ridge probe: not a model limit (see below) |
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

## Next

- **R3-C5.** The ridge probe shows the proxy-free limit is a **feature** limit, not a model limit
  (ridge on TD-Clean-6 gives −0.526 where the BPNN gives 0.490), so the next step is candidate
  inputs that are genuine health indicators rather than capacity proxies — incremental-capacity /
  differential-voltage peak features are the natural candidate, since they shift with degradation
  and are not functions of capacity.
- **R3-C6 / R3-C7 / R3-C9** remain deferred by decision, not by omission.

Verification: `phase1_verify.py` 61/61, `protocol_gap_verify.py` 23/23, `td_clean_verify.py` 7/7,
leakage probes `max|diff| = 0.00e+00` on every protocol and on the clean feature sets.