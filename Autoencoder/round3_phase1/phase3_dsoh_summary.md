# Phase 3, item 5.4 — ΔSOH accumulation: REJECTED

Advisor's words (R3-C5 item 4): *"Monotonic / physical prior: predict the degradation increment ΔSOH
and accumulate it (as in EWDC [10]), or add a monotonicity penalty to the BPNN."*

This document covers the **first** of those two options, implemented as specified. Verdict:
**REJECTED, decisively, with an identified mechanism.** The second option (a monotonicity penalty
inside the absolute-SOH loss) is a different mechanism and remains untested; see the end.

## Setup

`bpnn_monotonic.py`. The model predicts `ΔSOH(k) = SOH(k) − SOH(k−1)` from the features and the
series is rebuilt by accumulation:

```
SOH_pred(k) = ANCHOR + Σ_{j≤k} ΔSOH_pred(j)
```

`ANCHOR = 100 %SOH`, applied at each battery's first available cycle. This is definitional rather
than leakage: SOH is defined as `Q/Qref` with `Qref` = mean of the first five discharge capacities,
so a cell starts at ~100 %SOH by construction. The true first-cycle SOH is not exactly 100, and the
resulting offset is recorded and reported per fold — it is under **1 %SOH everywhere**, so it is not
what drives the result below.

Selection uses the same grid, the same guard and the same fold-train-only scaling as every other
run, scoring a candidate by the RMSE of the **accumulated** SOH on the inner-validation battery,
because that is the quantity being optimised. Same 631-row subset, same folds, same 5 seeds.

Two self-tests run before any training: the true Δ series must rebuild the true SOH series exactly
for all four batteries, and the accumulated test series must start exactly at the anchor. Both pass,
so the ordering and the accumulation are correct.

**Note on the reference:** EWDC [10] is not in the local materials — all 46 PDFs in
`Journal Discovery/` were searched by name and it is absent. Their anchor convention could not be
copied, which is why the anchor is justified from first principles here. Confirming it against the
paper belongs to R3-C9 (citation verification) or to asking the advisor for the reference.

## Result

| setting | mean R² | median R² | RMSE (%SOH) |
|---|---|---|---|
| `TD-Clean-7` + ΔSOH accumulation | **−3.689** | 0.090 | 14.18 |
| `TD-Clean-8` + ΔSOH accumulation | **−4.785** | 0.315 | 14.77 |
| *same sets, absolute SOH (5.1)* | *0.772 / 0.810* | *0.827 / 0.825* | *4.63 / 4.27* |

Per fold, mean R² over 5 seeds:

| fold | TD-Clean-7 | TD-Clean-8 |
|---|---|---|
| B0005 | 0.453 | 0.673 |
| B0006 | 0.267 | −0.054 |
| B0007 | 0.289 | 0.425 |
| **B0018** | **−15.763** | **−20.185** |

Paired against the absolute-SOH model on identical cells: **1 of 20** cells better for `TD-Clean-7`
and **0 of 20** for `TD-Clean-8`.

The monotone projection (cumulative minimum, i.e. forcing the series non-increasing) changes almost
nothing: −3.689 → −3.660 for `TD-Clean-7`, −4.785 → −4.769 for `TD-Clean-8`.

## The mechanism: the error integrates

This is not noise. The absolute error grows with cycle position, in every fold:

| fold | corr(cycle position, \|error\|) | slope over the full cycle range |
|---|---|---|
| B0005 | +0.568 / +0.368 | +8.1 / +3.5 %SOH |
| B0006 | +0.874 / +0.891 | +17.9 / +18.0 %SOH |
| B0007 | +0.896 / +0.592 | +10.6 / +6.1 %SOH |
| **B0018** | **+0.993 / +0.988** | **+55.0 / +60.0 %SOH** |

*(TD-Clean-7 / TD-Clean-8)*

A biased increment summed over N cycles produces an error that grows like N × bias. That is exactly
what the table shows, and B0018 — whose SOH range is the narrowest (72.9–100.8) — is punished hardest
because the same absolute drift is large relative to the span it must be measured against.

This also explains why the monotone projection cannot help: clamping the accumulated series removes
positive increments but does not remove a systematic linear drift.

## Consequence

- **Item 5.4, option 1 (ΔSOH accumulation): closed as rejected**, with the mechanism documented.
  This is the third of the advisor's five Phase 3 items to fail on measurement, and the second where
  the advisor's stated expectation ("as in EWDC [10]", where EWDC reports R² 0.975 under LOBO) does
  not reproduce here. The difference worth stating: EWDC's 0.975 was measured with proxy-laden
  features under a LOBO protocol, so its accumulation had a much stronger per-cycle signal to
  integrate.
- The proxy-free result is unchanged: **`TD-Clean-7` = 0.772**, **`TD-Clean-8` = 0.810**.
- **Untested residual:** the advisor's alternative, a monotonicity penalty added to the loss of the
  *absolute*-SOH model. That attacks a different failure (non-physical wiggles in an already-absolute
  prediction) and would not be invalidated by the drift shown above. It is the only part of item 5.4
  not yet measured.

Evidence: `bpnn_monotonic.py`, `phase3_dsoh_cpu_results.csv`, `phase3_dsoh_cpu_preds.csv`,
`phase3_dsoh_verify.py` (7/7 checks pass), `phase3_dsoh_cpu.log`.