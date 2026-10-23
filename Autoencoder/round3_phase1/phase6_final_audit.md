# Round 6 — FINAL AUDIT (pre-P6-6): advisor-comment coverage matrix

Every R6 point checked against real evidence files. Status: READY FOR P6-6 with the
disclosure items below mandatory in the report.

| R6 point | Requirement | Evidence | Status |
|---|---|---|---|
| C0 | Clean-5T primary; Clean-6T ablation | All P6-1..P6-5 used Clean-5T only; Clean-6T appears in no R6 experiment | OK — **P6-5b DEFERRED (disclosed)** |
| C1 | Overlap wording fixed | repo grep "do not overlap"/"non-overlap": clean (3 fixes committed 888d1eb/0aee5e1) | OK |
| C2-1 | Per-feature distribution comparison | `phase6_feature_shift.csv/.png/_summary.md` (cc_dur 93.4% out, cv_I_slope 99.8%, cv_dur 84.6%, ic_peak_V 41.6%, dis_V_slope 0.1%) | OK |
| C2-2 | Common-SOH-range diagnostic (87–101%), NOT a final result | `phase6_common_range_diag.csv` + closure C4 (n=39,870, MedAE 19.33, P90 48.74) | OK |
| C2-3 | Feature-support split (in/out NASA support) | `phase6_support_split.csv` (strict + majority definitions agree; n_out gradient Wilcoxon p=0.002, 10/10 runs) | OK |
| C2-4 | One simple deterministic baseline, no model-comparison expansion | `phase6_ridge_transfer.csv` + `phase6_ridge_within.csv` (2x2 closed: Ridge-within 2.68 ≈ BPNN 2.54; Ridge-transfer 51.1 → domain shift, not model class) + `phase6_baseline_closure.md` | OK |
| C2-5 | Alignment ladder: scaling → unsupervised align → one-cell calibration | `phase6_ladder_La/Lb/Lc.csv`; test-cell exclusion asserted (code lines 179–180, no violations in log) | OK |
| C3 | Rotated battery-wise validation + outer-test isolation unchanged | P6-2 rerun parity EXACT vs Round 5 (80/80 rows identical cfg/epochs/metrics) | OK |
| C4 | Fallback rate recorded in every experiment/table | fallback_rate column on 7/7 result tables; support_split.py reproduces its own column | OK |
| C5 | Compact progression report | P6-6 (next) — all inputs verified | PENDING (this audit is its gate) |

## Matched recovery numbers (R6-C5 headline, row-set matched)

- L0 reference (rerun, parity-exact): median MAE 20.99
- **La-quantile: NOT valid recovery** — MAE 6.76 is *worse* than a constant predictor (4.06);
  per-cell yhat/y std ratio 0.063 = degenerate alignment (interventionally closed via
  quantile_varrestored MAE 37.1)
- **Lb-affine (unsupervised, target-training features only): MAE 12.47 vs matched-L0 24.64
  → 49% of the gap recovered** — the simplest defensible alignment
- **Lc one-cell calibration (non-degenerate 35/80): MAE 11.09 vs matched-L0 26.44 → 58%**
- Within-CALCE ceiling (BPNN): median MAE 2.54 — alignment closes ~half of the transfer gap;
  the remaining half requires more target information (fine-tuning = future work)

## Mandatory disclosures in the P6-6 report (closing these = closing the audit)

1. P6-5b (Clean-6T ablation) was DEFERRED, not forgotten — advisor's wording permits
   ("can remain as an ablation"); the Round 5 adapt2_C6T result stands as the C6T evidence.
2. NN fine-tuning after Lc was NOT tried — the advisor's ladder places calibration *before*
   fine-tuning; stopping at Lc answers the diagnostic question and leaves fine-tuning as the
   explicit next step.
3. La-quantile must be reported as degenerate alignment (worse than constant predictor),
   never as "best MAE".
4. Lc: 45/80 (56%) calibrations degenerate; non-degenerate median MAE 9.24 is the reportable
   number.
5. Fallback rate 0.80 is selection-level (broadcast per run), identical across all rungs —
   it is a property of the source-side selection, not of the alignment method.
6. Smoke CSVs are nondeterministic (noted in commit 9efbbe4); ALL full-run conclusions rest
   on the parity-exact full reruns.
