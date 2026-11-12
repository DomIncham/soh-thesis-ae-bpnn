# Round 7 Work Plan — Detailed Step-by-Step (written 2026-11-13)

> Source: `Round 6B Advisor Comment.txt` (two letters) + `Round 6B _Dom_Research_Roadmap_After_Round6.pdf`.
> Transcription verified in `advisor_directives.md` §Round 7 (R7-C0…C4).
> **Hard gate (R7-C4):** Round 7 proper (Stage 2) does NOT start until the Round 6B comparison
> is submitted and the advisor reviews it. So this plan = Stage 1 in full execution detail,
> Stage 2 at design level only.

---

## What the advisor said, and why this plan matches it

| # | Advisor's comment (source) | Why our plan answers it this way |
|---|---|---|
| 1 | **"The current Lc is not a pure one-cell output calibration"** — the BPNN is warm-fine-tuned first, then calibration fitted on the SAME cell; the Lc gain "cannot be attributed to output calibration alone" (Letter 1 ¶3; PDF Stage 1 purpose) | The confound is structural: Lc changed weights AND output scale at once. The only clean fix is to add the missing ablation arm (calibration-only, weights frozen) while reusing the existing Adapt2 and Lc arms unchanged. Re-running Lc differently would break matched comparability with the Round 6 report. |
| 2 | **3-way comparison on the same labeled target cell** (Letter 1 ¶2; PDF: "exactly matched cells and seeds") | All three arms share: same 8 CALCE pools, same 10 seeds, same adapt cell per pool, same test row set per held-out cell. No new fitting protocol is invented — we reuse the Round 6 loop scaffolding so cells/seeds/rows are identical by construction. |
| 3 | **"Retain L0 zero-shot transfer and the unlabeled affine feature alignment as references"** (PDF Stage 1) | L0 and La already exist as dumped predictions from Round 6 (P6-5). We include them in the same table rather than recomputing — they anchor "how much of the gap remains after the cheapest interventions." |
| 4 | **Report whether labels are used and whether NN weights are updated, per method** (PDF Stage 1) | The 5-row comparison table carries two explicit columns: `labels_used` (0 / 1 cell's labels) and `weights_updated` (no / yes). This makes the attribution question un-answerable-by-ambiguity. |
| 5 | **"Clarify the definition of gap recovered"** (Letter 1 ¶5) — if it is relative MAE reduction from L0, rename to **"MAE reduction relative to matched L0"**; true gap recovery = within-CALCE as reference floor, computed on matched row sets | We report BOTH numbers, each with its own name and definition, so no single ambiguous "recovered %" appears anywhere in the report. |
| 6 | **Unique cycles vs prediction instances** (Letter 1 ¶6) — 49,220 / 39,870 are accumulated prediction rows, not unique cycles; emphasize run-level consistency (10/10, paired run-level test) | Every table/figure caption states the unit explicitly. Statistics move from row-level to run-level: n = 80 runs (8 pools × 10 seeds), paired run-level Wilcoxon for arm differences, 10/10 directional counts. No row-level p-values anywhere. |
| 7 | **La-quantile stays documented as degenerate** (Letter 1 ¶7) | No change: La keeps its "degenerate alignment" label with the interventionally-verified closure (quantile_varrestored 37.27). It appears in the table as a reference row, never counted as recovery. |
| 8 | **Research rules (R7-C3):** no random cycle-wise split; no fitting on the held-out test cell; matched cells/seeds/row sets for any quantitative claim; mean AND median when unstable; diagnostics separated from performance; keep negative results; no AE return | The Stage 1 design satisfies all six by construction: fitting a,b uses only the adapt cell; held-out cells touch nothing; fallback rate column (R6-C4) stays on every table; degenerate runs are separated, not dropped. |

**Decision point after Stage 1 (PDF):** select the simplest defensible adaptation method.
The 3-way table IS that evidence — whatever arm wins with the least machinery becomes the
default "adaptation strategy" carried into Stages 2 and 5.

---

## Stage 1 — Round 6B: step-by-step execution plan

**Objective:** answer, with matched evidence, whether the remaining Lc improvement comes mainly
from output-scale correction (a, b) or from changing the network weights.

### P6B-1 — Calibration-only script (Capi, CPU)

1. **Read the loading path once:** `phase6_alignment_ladder.py` — how L0 predictions, adapt-cell
   labels, and pool/seed loops are set up; reuse the same IO and the same row-set definitions.
2. **Write `phase6b_calibration_only.py`:**
   - Load the frozen NASA-trained BPNN backbone predictions on ALL 8 CALCE cells per pool × seed
     (no forward passes needed if Round 6 dumps already contain them — check `phase6_ladder_preds.csv`
     first; if L0 rows per (pool, seed, cell, cycle) exist, calibration-only needs ZERO NN compute).
   - Per (pool, seed): fit `y = a·ŷ + b` by least squares on the ONE labeled adapt cell's rows only;
     apply to the other 7 cells' predictions.
   - Output per-run summary CSV: pool, seed, adapt cell, a, b, slope/intercept degenerate flag
     (slope ≤ 0 or |slope−1| ≥ 1, same criterion as Lc), fallback rate, per-cell MAE/RMSE/R²,
     `labels_used=1`, `weights_updated=no`.
   - Per-row dump CSV (same schema as `phase6_ladder_preds.csv`, arm = `cal_only`) for matched row-set
     joins.
   - Degenerate fallback: if a calibration is degenerate, record it and fall back to identity (a=1, b=0)
     — SAME treatment Lc already receives, so arms stay comparable; the fallback column discloses it (R6-C4).
3. **Smoke test (1 pool × 2 seeds, CPU):** assert (i) adapt cell rows never enter fitting for other
   cells, (ii) row counts match L0 dump exactly, (iii) a degenerate run is flagged and falls back.
4. **Commit** script + smoke CSV with explicit paths.

### P6B-2 — Full run (Dom, CPU/GPU; ~minutes — no NN fits)

5. Launch full 8 pools × 10 seeds. Verify: 80/80 runs present, row-set parity vs L0 dump
   (exact same (pool, seed, cell, cycle) keys), fallback column populated, degenerate counts reported.

### P6B-3 — Matched 3-way analysis (Capi)

6. Build the comparison table (one row per arm × pool aggregation, plus per-cell detail):
   **Cal-only / FT-only (Adapt2) / FT+Cal (Lc) / L0 reference / La reference (degenerate, labeled).**
   Metrics: MAE, RMSE, R² per cell and mean+median over pools (median mandatory — Lc had unstable runs),
   labeled-cell count, weights-updated flag, fallback rate.
7. Statistics at RUN level only: paired Wilcoxon (Cal-only vs FT-only vs FT+Cal) on the 80 matched
   run-level MAEs; directional counts (e.g. "Cal-only better than FT-only in k/10 seeds for pool X").
8. Compute both recovery numbers per R7-C1:
   - **MAE reduction relative to matched L0** = (MAE_L0 − MAE_arm)/MAE_L0 on matched rows.
   - **Transfer-gap recovery** = (MAE_L0 − MAE_arm)/(MAE_L0 − MAE_within) with within-CALCE as floor,
     same matched rows. Label each number with its definition in every table.
9. Answer the R7-C0 question explicitly in one sentence backed by numbers, e.g. "calibration alone
   recovers X% of what FT+Cal recovers" (whatever the data says — negative/ambiguous results are
   reported as-is, R7-C3).

### P6B-4 — Reporting + closure (Capi → Dom)

10. Round 6 closure addendum in the report (or a short `round6b_closure.md` appended to the
    Round 6 report package): corrected Lc interpretation ("warm fine-tuning + calibration"),
    renamed headline numbers, both recovery definitions, unique-cycles vs prediction-instances
    distinction, run-level statistics, fallback disclosure.
11. Verification gates: every number programmatically asserted against source CSVs; pre-send grep
    checklist (no prove/confirm/successfully, no em dash, no curly quotes, no -ly adverbs); GitHub
    evidence links checked HTTP 200.
12. Update `active_experiment.md` §2 (at Dom's pruning point), commit + push explicit paths,
    hand `.md` to Dom for Antigravity → advisor review.

**Stop conditions:** (a) any missing Lc/L0 dump for a pool/seed → report the matched count and
shrink the table, never impute; (b) Cal-only broadly degenerate → that IS the answer (report as
negative result); (c) anything pointing toward a bigger adaptation model → out of scope, Stage 1 only.

---

## Stage 2 — Round 7 proper: design-level outline (NOT started, blocked on advisor review of 6B)

Per the roadmap PDF, prepared so the follow-up plan is quick once the advisor approves 6B:

- **Objective:** target-data learning curve — how much labeled target data is enough.
- **Levels:** 0 / 1 / 2 / 3 labeled target cells + full target-domain training reference.
- **Arms per level:** zero-shot, output calibration, warm fine-tuning, training from scratch
  (where applicable — scratch needs ≥1 cell by definition).
- **Selection:** the target cell(s) used for adaptation are re-drawn across multiple splits so no
  conclusion rests on one convenient cell; held-out test cells never touch selection/alignment/
  calibration/fine-tuning.
- **Cost tracking (new for Stage 2):** labeled cells, labeled cycles, training time, inference cost —
  recorded per run alongside accuracy.
- **Expected deliverable:** learning curve (labeled cells vs MAE/RMSE), transfer vs full-retraining
  comparison, minimum data level reaching ~80–90% of full-retraining performance.
- **Decision point:** best balance of target-data demand, stability, accuracy.
- A full PAEV plan for Stage 2 will be drafted ONLY after the advisor reviews the 6B results
  (R7-C4), incorporating whatever Stage 1 shows about which adaptation arm is worth carrying forward.

Stages 3–5 (frequency branch → fusion → final benchmark) stay at roadmap level; each gets its own
PAEV plan when its turn arrives.
