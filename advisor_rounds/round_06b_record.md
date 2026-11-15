# Advisor Round 6B — Calibration Closure

- **Received:** 2026-11-13 (`Round 6B Advisor Comment.txt`, two letters + `Round 6B _Dom_Research_Roadmap_After_Round6.pdf`)
- **Status:** Executed, report written — awaiting submission (PDF) and advisor review
- **Original source:** `Comment Prof and Report/Comment Prof/` (files renamed by Dom from "Round 7 ..." on 2026-11-13)
- **Work plan:** `Autoencoder/round3_phase1/round6B_work_plan.md`
- **Report:** `Autoencoder/round3_phase1/round6b_closure.md` (61 asserted numbers, grep checklist clean)
- **Round 7 (Stage 2) gate:** not started until the advisor reviews this round (R7-C4)

## Advisor's Main Direction

The current Lc mixes warm fine-tuning and output calibration on the same cell, so its gain
cannot be attributed to calibration alone. Round 6B must isolate the two parts with a matched
3-way comparison, fix two reporting ambiguities, and then Round 6 is complete. The roadmap
defines Stages 1-5 after that; no broad model expansion and no return to autoencoder work.

## Required Items and Status

| Item | Source | Status | Evidence |
|---|---|---|---|
| Cal-only: frozen BPNN, fit y=a*yhat+b on 1 labeled cell, apply to other 7 | Letter 1 item 1 | Done | `phase6b_calibration_only.py`, `phase6b_cal_only.csv` (80/80 runs, 0 NN fits) |
| FT-only = existing Adapt2 reused | Letter 1 item 2 | Done | `phase5_cs2_adapt2_c5t_full.csv` (C5T, 80 runs) |
| FT+Cal = former Lc, renamed | Letter 1 item 3 | Done | `phase6_ladder_Lc.csv`, renamed in the report |
| Exactly matched cells and seeds | Letter 1 | Done | keys (pool, seed, adapt_cell) identical across arms, verified 1:1; backbone tolerance 0.0219 %SOH disclosed |
| L0 + Lb-affine + La retained as references | Roadmap Stage 1 | Done (Lb added in final audit) | L0 in the main table; Lb-affine median 11.53 with a protocol note (single-cell rows, not pooled); La kept as documented degenerate alignment |
| Table states labels used / weights updated | Roadmap Stage 1 | Done | report section 2 table columns |
| Table contains MAE, RMSE, R2 | Roadmap Stage 1 | Done (added in final audit) | report section 2 + `phase6b_matched_3way.csv` |
| "gap recovered" clarified | Letter 1 item 4 | Done | both definitions reported with labels: (a) MAE reduction relative to matched L0; (b) transfer-gap recovery with per-run matched within floor |
| Unique cycles vs prediction instances | Letter 1 item 5 | Done | 4,922 unique cycles vs 49,220 / 344,540 prediction instances; statistics at run level (n=80) |
| La-quantile stays degenerate | Letter 1 item 6 | Done | kept as reference row, not counted as recovery |
| Degenerate/fallback disclosure | R6-C4 standing | Done | Cal-only 50/80, Lc 45/80 (replicates Round 6), identity fallback exact 50/50 |
| Clear answer: does calibration alone explain most of the benefit | Roadmap Stage 1 | Done | No: warm fine-tuning carries the gain (11.95 vs 13.66 median MAE, p=0.0024); adding calibration shows no further benefit we could detect (p=0.43); calibration alone matches only when non-degenerate (9.00 vs 12.25, n=25, diagnostic) |
| Decision point: simplest defensible adaptation method | Roadmap Stage 1 | Done | stated in report section 5: warm fine-tuning alone; calibration as a non-degeneracy-gated diagnostic |
| Do NOT start Stage 2 before review | R7-C4 | Respected | Stage 2 outline only, in the work plan |

## Key Numbers (MAE %SOH, run level, n = 80)

- Median: Cal-only 13.66 / FT-only 11.95 / FT+Cal 12.18 / L0 23.75
- Recovery (a) median: 0.0% / 42.8% / 37.1%; recovery (b, matched floor) median: 0.0% / 50.1% / 42.7%
- Cal-only median recovery of 0.0% is structural: 50 identity-fallback runs equal L0 exactly

## Verification

- Cal-only recomputed independently with scipy linregress, 80/80 runs match
- Lc summary re-checked against the raw ladder dump, 80/80; Adapt2 row sets match the L0 dump
- Backbone retrained and compared: 0.0219 %SOH noise tolerance, disclosed in the report
- 57/57 report numbers asserted against source CSVs; grep checklist clean
- Two analysis bugs were caught by audit and fixed before reporting (L0 pooling 8 vs 7 cells;
  smoke/full output contamination)

## Remaining (outside this record's scope)

- Dom: convert `round6b_closure.md` to PDF in Antigravity and send to the advisor
- After advisor review: Stage 2 (Round 7) target-data-efficiency PAEV plan
