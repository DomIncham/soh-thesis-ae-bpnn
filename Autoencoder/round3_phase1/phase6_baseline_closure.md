# P6-4 Closure — what the two-family limitation means and how far the claim is bounded

Status: verified 2026-10-21. Companion to `phase6_interpretation_guards.md`. This file states,
for the Round 6 report, exactly what the Ridge 2x2 establishes, what stays open, and the
one sentence that closes the residual objection without expanding the model set (R6-C2.4).

## The 2x2 (median MAE across runs, identical protocol/row sets)

| | within-CALCE | NASA→CALCE transfer |
|---|---|---|
| BPNN | 2.54 (medR² 0.58) | 20.99 (medR² −28.3) |
| Ridge | 2.68 (medR² 0.45) | 51.14 (medR² −148.7) |

## What this establishes (strong form, no new families needed)

1. **Model class is not the cause.** Ridge is essentially as good as BPNN in-domain
   (2.68 vs 2.54) and collapses only under transfer. If linear extrapolation were a
   model-class weakness, Ridge-within would degrade too; it does not.
2. **The failure is a property of the input distribution.** Both families trained on NASA
   features mispredict the same CALCE rows: of rows where both models are badly wrong
   (|err| > 20%), 96.9% sit in the n_out ≥ 3 support-violation zone (1.15× concentration
   over the zone's 84.4% base rate). Two structurally different estimators failing on the
   same rows is the signature of a data/domain problem, not estimator noise.
3. **Direction of difficulty matches extrapolation theory.** Ridge degrades faster than
   BPNN as support violation grows (Ridge MedAE 14.9 → 55.2 vs BPNN 4.5 → 22.5 from
   n_out ≤ 2 to ≥ 3) — expected if the target function itself is extrapolative, with
   nonlinearity merely softening the blow.

## Report sentence that closes the residual objection

> "The diagnosis is controlled with one deterministic baseline (Ridge) plus its in-domain
> counterpart under the identical protocol: both model families perform comparably
> within CALCE and collapse under NASA→CALCE transfer, failing on largely the same cycles
> concentrated in the feature-support-violation zone. Any model fitted on NASA features
> must extrapolate beyond the training support to score these cycles, so the failure is
> attributable to the domain shift itself rather than to the choice of estimator."

## What stays open (stated honestly in the report, limits subsection)

- Only two model families were tested; the advisor's R6-C2.4 instruction prohibits a wider
  study, so "no model class escapes the shift" is an argument from convergent evidence +
  shared-row concentration, not an exhaustive enumeration.
- Whether alignment (P6-5) closes the gap is the operative test — if it does, the causal
  story gains interventional support and the model-class question becomes moot in practice.

## Why this satisfies R6-C2.4 as written

The advisor asked for ONE simple deterministic baseline to separate BPNN-specific
instability from broader domain shift — and prohibited expansion. The 2x2 delivers exactly
that separation with the single baseline plus a control re-run of the same baseline
(no new model, no new features, no hyperparameter search beyond the same 6-alpha grid).
The shared-row analysis is post-hoc reading of existing dumps, costing zero extra training.
