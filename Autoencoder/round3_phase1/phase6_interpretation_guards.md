# P6-3 Interpretation Guards (R6-C4 compliance + negative-control resolution)

Status: verified 2026-10-21, all numbers reproducible from `phase6_dump_with_support.csv`
(49,220 per-cycle rows, 10 (pool,seed) runs) + `phase6_transfer_rerun_c5t.csv` (parity-EXACT
vs Round 5). Written before P6-4 so the report writers cannot misstate these points.

---

## Guard 1 — Fallback 0.80 applies equally to both support groups (R6-C4, closed)

**Claim to avoid:** "errors in the outside-support group reflect selection fallback."

**Evidence it is safe to conclude the support gradient is a model property, not selection instability:**

1. Fallback (`sel_degenerate`) is a **run-level** flag: each (pool, seed) run is entirely
   degenerate or entirely not (10/10 runs agree with the Round 5 CSV). It cannot vary
   within a run, so it cannot explain differences **between rows inside the same run**.
2. The n_out gradient replicates **within every single run**, including the 2 non-fallback
   runs (room s123: MedAE 5.6 → 34.4; room s2024: 2.9 → 13.9 for le2 vs 3–4) — direction
   positive in **10/10 runs**, mean within-run Spearman(n_out, |err|) = 0.527.
3. Stratified by fallback status, the gradient is the same shape in both strata:
   - non-fallback runs: MedAE le2 = 3.79 vs 3–4 = 19.52 (frac bad-pred 0.008 vs 0.514)
   - fallback runs: MedAE le2 = 4.64 vs 3–4 = 22.83 (0.124 vs 0.568)
   Fallback shifts the level slightly upward but does not create or alter the gradient.
4. Paired Wilcoxon across the 10 runs: MedAE(le2) < MedAE(≥3) in 10/10, p = 0.00195.

**Conclusion allowed in the report:** the support-violation gradient is a property of the
trained models' behaviour, not a selection artifact. Report must still state the run-level
fallback rate (0.80) once as context, per R6-C4.

## Guard 2 — "n_out 1–2 is BETTER than n_out = 0" is a real negative control, resolved

**Observation:** MedAE by number of features outside the NASA range (n_out):
0 → 13.3% | 1 → 5.7% | 2 → 3.4% | 3 → 19.8% | 4 → 26.2% | 5 → 25.0%.

Naive reading ("closer to support is better") is WRONG — monotonicity is violated at n_out=0.

**Resolution (mechanism, verified from feature magnitudes):**

- n_out = 0 rows (n=50, 0.1% of data) are nearly all **early CS2_21 cycles** whose behaviour
  sits at extreme NASA values (they are inside support but at its boundary/atypical corner);
  tiny sample, high leverage, MedAE 13.3% — not a counterexample, a sparse-corner effect.
- n_out = 1–2 rows (n=769): the violating features are `cv_I_slope` (98.8% of these rows)
  and `cc_dur` (57.7%), but their **violation magnitudes are small** (cc_dur median relative
  overshoot 0.037 of the range, max 0.33; cv_dur stays in-range with median deviation ≈ 0).
  These are rows whose *charging dynamics remain NASA-like* — the model interpolates well.
- n_out = 3–5 rows (n=4,153): `cc_dur` AND `cv_dur` are out **together, massively**
  (cc_dur median overshoot 0.59 of the NASA range, up to 0.93; cv_dur median −1.18 = at/below
  the NASA minimum). Both simultaneous, large violations = qualitatively different cycles
  (much longer CC, much shorter CV than any NASA cycle).

**Correct report phrasing:** "prediction error grows with the *magnitude* of feature-support
violation, not merely the count: rows violating one feature mildly (median overshoot ≈ 4% of
the NASA range) predict better than in-support corner cases, while rows combining severe
cc_dur overshoot (~0.6 range) with cv_dur collapse (median −1.2 range) produce MedAE ≥ 20%
and exploding predictions (>115% SOH) in 47–65% of cycles."

**Statistical anchors:** paired Wilcoxon p = 0.00195 (10/10 runs); chi²(cell × bad-pred)
χ² = 8,899; chi²(n_out × bad-pred) χ² = 5,413 (both p < 0.001); Spearman within-run
0.21–0.63, positive in all 10 runs. Clipping predictions at 115% shrinks the n_out=4 MedAE
from 26.2 → 14.9 but does NOT remove the gradient (3.35 → 19.8 leap between n_out=2 and 3
survives clipping) — the support effect is not an artifact of unbounded outliers.

## Guard 3 — Outlier handling standard for all Round 6 tables

Every Round 6 table/reports quote **MAE and MedAE side by side** plus frac(yhat>115%)
("exploding-prediction rate"). MAE alone is outlier-dominated (7.3% of rows have |err|>50%;
48.6% of rows predict >115% SOH). Clipped variants go in an appendix table, not the main one.

## What this does NOT establish (limits, per honesty rule)

- Support violation is **necessary context but not proven sufficient causation**; the causal
  claim rests on observational stratification, not intervention. P6-4 (Ridge) and P6-5
  (alignment ladder) test whether removing/reducing support violation closes the gap.
- The n_out=0 corner effect (n=50) is underpowered; treat as anecdote in the report.
- Fallback remains 0.80 overall: even if alignment recovers accuracy, the selection
  instability itself stays an open item for the advisor (it was flagged in R6-C4 and is
  NOT solved by this diagnosis).
