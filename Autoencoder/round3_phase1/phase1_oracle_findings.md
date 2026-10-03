# Phase 1 — Oracle-proxy findings (Round 3)

Date: 2026-10-04 · Device: CPU · Source: `td_proxy_audit_cpu_results.csv` (72 rows = 3 settings x 2 stages x 4 folds x 3 seeds)

## What the gate expected vs what we measured

The Round 3 plan carried a sanity gate: *"Oracle (I x t) -> R2 ~ 1"*, on the reasoning that
`SOH = Q/Qref` and `Q = I * t_dis` with constant current, so discharge duration alone should
reconstruct SOH almost perfectly. If true, the high scores reported in the literature are
explained by the label being trivially recoverable from one feature.

Measured, under the cross-battery LOBO protocol:

| Scope | duration -> SOH | Value |
|---|---|---|
| Within a single battery (per-battery linear fit) | R2 | **0.952 (B0005) / 0.986 (B0006) / 0.964 (B0007) / 0.985 (B0018)** |
| Cross-battery, one global linear map (in-sample ceiling) | R2 | **0.794** (pooled r = 0.891) |
| Cross-battery, LOBO, BPNN with Oracle features | mean R2 | **0.663 +/- 0.239** |

Per-fold Oracle-proxy mean R2 over 3 seeds (refit_on_3): B0005 **0.928**, B0006 **0.308**,
B0007 **0.656**, B0018 **0.762**.

## Diagnosis: the gate is mis-specified, not the pipeline

The oracle claim holds **within a battery** (R2 0.95-0.99) and fails **across batteries**. Two
mechanisms, both already listed among the Round 3 score-gap factors:

1. **Per-battery reference capacity.** `SOH = Q/Qref` and Qref differs per cell
   (first-5-cycle means: 1.842 / 2.018 / 1.883 / 1.840 Ah). The same duration therefore maps to a
   different SOH in each battery, and an unobservable per-battery offset must be learned. B0006 has
   the largest Qref (+~9% over B0005), which is exactly where the oracle collapses (R2 0.31).
2. **Different discharge cut-off voltage.** Duration at 100% SOH is identical for B0005/B0006/B0007
   (3655 s) but 3419 s for B0018, because of its higher internal resistance and 2.5 V cut-off.
   B0018 durations are therefore not directly comparable, capping that fold at R2 0.76.

Both effects are absent in the random / chronological splits that most published work uses, which
is precisely the R3-C2 protocol gap. So "oracle R2 ~ 1" is a *within-battery/same-split* statement,
not a universal one.

## Consequence for the claims

- **R3-C1 / R3-C3 survive, but must be restated.** The claim is not "the label is trivially
  recoverable in general" but "the label is trivially recoverable *under the evaluation protocol the
  literature uses*, which is why published scores are high". Our 0.95-0.99 within-battery number is
  the support for that, and 0.66-0.79 under LOBO is the support for the protocol gap.
- **The oracle becomes a bridge between C2 and C3**, not a failed sanity check: it is the same
  feature set evaluated under both protocols, and the R2 drop (0.95-0.99 -> 0.66-0.79) is the
  protocol effect measured on a fixed representation.
- **Action for Phase 2:** run the Oracle-proxy under the random / chronological splits. Expectation
  is R2 near 1 there. That single number completes the argument.

## Resolved: the TD-Proxy-Free collapse (selection guard, 2026-10-04)

`TD-Proxy-Free` (no `dis_duration`) on fold B0005 collapsed for one seed: **seed123 R2 = -0.602**
with `train_R2 = -0.276`. The cause was not the feature set. `fit_bpnn_ep` returns
`best_epoch + 1`, so when validation never improves on the first epoch the returned budget is 1 and
the "best" weights are the initialisation. The refit then reproduced a flat line (var(y_pred) = 0.21
against var(y_true) = 106.9), while the other two seeds selected 67 and 143 epochs and scored 0.96.

Guard added in `r3common.run_fold`: a candidate may only win on validation RMSE if its selected epoch
budget is >= `MIN_EP` (20). If no candidate converged, the best-by-validation one is retrained for a
fixed `RETRAIN_EP` (200) epochs. Result rows now carry a `sel_degenerate` flag and the driver prints
the `sel_epochs` distribution, so this failure mode is visible instead of silent.

Regression evidence (`td_proxy_audit_cpu.log`, full 36 fold-seeds, guard run compared key-by-key
against the pre-guard baseline):

| setting | fold-stages changed | outcome |
|---|---|---|
| TD-All | **0 / 24** | no-op; the 0.923 headline stands unchanged |
| Oracle-proxy | **0 / 24** | no-op; 0.663 stands unchanged |
| TD-Proxy-Free | **2 / 24** | exactly the degenerate fold-seed, both stages |

| TD-Proxy-Free, refit_on_3 | before | after |
|---|---|---|
| mean R2 | 0.732 +/- 0.434 | **0.854 +/- 0.110** |
| mean RMSE | 4.293 +/- 3.124 | **3.536 +/- 1.475** |
| median R2 | 0.887 | **0.887** (unchanged) |
| B0005 fold | 0.439 | **0.923** (B0006/07/18 bit-identical) |

The median was already robust to the collapse, so mean and median should both be reported and the
median treated as the primary headline for the proxy-free setting.

## Evidence files

- `td_proxy_audit_cpu_results.csv` — per fold-seed metrics, 3 settings x 2 stages
- `td_proxy_audit_cpu_preds.csv` — per-cycle y_true / y_pred
- `td_proxy_audit_summary_cpu.csv` — per-setting means
- `td_proxy_audit_cpu.log` — full 36 fold-seed run under the selection guard
- `refit_full.log` — the 12 fold-seed refit run
- `probe_s14b.log` — leakage probe, `max|diff| = 0.00e+00` on both stages
