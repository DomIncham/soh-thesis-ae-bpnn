# Active Experiment — Session Handoff and Pruning State Card

> **Session pruning card:** read this after `advisor_directives.md`. This file is intentionally short and is updated only when current state, blocker, objective, or next action changes. Load detailed files only for the task at hand.
>
> **Normal session mode:** Dom combines reasoning, planning, implementation, and coding in one session. The current scope is read from Section 1 and the latest handoff; never hard-code a round, phase, blocker, or thesis-writing status in the start prompt.
>
> **Current state:** This is mutable session state. Read Section 1 for the current advisor round, work phase, objective, blocker, and scope; do not treat this line as a permanent instruction.
>
> **Advisor:** Y.F. Luo (YF.Luo@mail.ntust.edu.tw) — collaborator on the private repo
> `github.com/DomIncham/soh-thesis-ae-bpnn`; all progress is pushed to `main` for review.
>
> **NEW WORKING RULE (2026-10-05): every step of every task ends with a git commit + push** — code,
> results CSVs, run logs, summary `.md` and this state card are committed as soon as the step is
> verified. Never batch several steps into one commit; never leave verified work un-pushed.
>
> **File ownership (2026-10-07):** `round4_report_to_advisor.md` (source of truth) is Capi's —
> committed. `generate_round4_pdf.py`, `round4_report_to_advisor.pdf`, `round4_report_to_advisor.html`
> are Antigravity's — NEVER `git add` them (stay untracked).
>
> **Detail lives elsewhere.** Each item has its own summary in `Autoencoder/round3_phase1/`;
> `PROJECT_STATE.md` there holds the phase map, verification ledger and bug log. This card is the
> entry point, not the archive.

All work runs under **PAEV**: Plan with the 4-Rule → Dom approves → Execute → Verify with gates →
Ablation log → Commit. Division of labour: Capi writes / smoke-tests / verifies (CPU); Dom runs the
long `--full` jobs on the RTX 3050; Capi delivers `.md` only and Dom converts to PDF in Antigravity.

---

## 1. Current Project State

> This section is mutable. Update it whenever the advisor round, work phase, objective, blocker, scope, or thesis-writing status changes.

- Current advisor round: Round 4 — **all 6 items answered and verified (2026-10-10); progress report drafted and committed (`round4_progress_report.md`), awaiting Dom's PDF conversion + email to advisor**
- Current work phase: Round-4 corrections COMPLETE (code + full runs + structural suite + report draft); waiting on advisor's Round 5 reply
- Current objective: send the Round 4 progress report to the advisor, then start Round 5 per the advisor's chosen direction (charge-side features vs domain-shift)
- Current blocker: the report draft awaits Dom's read-through + Antigravity PDF conversion + advisor email; one open interpretation question sits in the report for the advisor (CS2 inner rotation)
- Thesis drafting: still out of scope (advisor item 6 gates it); Ch.2 waits on the title answer
- Item 5 (AE): nothing to do — matches the existing negative-result decision (untouched, git-verified)

When a new advisor round starts, update these fields. Never leave a previous round's waiting status as a permanent instruction.

## 2. Previous Session Handoff

> Replace this section's mutable fields after every session. Keep only the latest factual handoff here; use Git history and experiment summaries for older sessions.

Record only the latest session's handoff. Do not paste full logs or historical detail here.

### Completed

- **All 6 advisor items closed and verified (2026-10-10, commits `aea8cf4..e2ea3a9` + report `70d7a7b..db47f1d`).**
- Item 1 (nested LOBO): two real bugs fixed in `r3common.run_fold` — the lobo3 branch rotated inner folds over only 2 batteries (B0006 never validated) and selection was not aggregated over 3 folds. Now: 3-fold rotation, mean-val-RMSE selection, refit on 3, tested on outer. Empirically enumerated for all 4 outer folds; S1 spy check = 3.
- Item 2 (Clean-6T): advisor was right — all 4 CS2 scripts still carried `dis_duration`+`dis_mean_V`. Corrected to 6 features (`dis_V_slope, cc_dur, cv_dur, cv_I_slope, t_40_41, ic_peak_V`); S4 structural check guards it.
- Item 3 (selection disjoint): transfer + adapt1 refit on the FULL pool after disjoint selection (matching within/adapt2/run_fold); `val_battery` recorded in all CS2 CSVs; within dedupes on save.
- Item 4 (structural suite): `round4_structural_verify.py` — 25/25 PASS (S1 3-fold count, S2 disjoint, S2b within completeness + val≠test, S3 declared==fed, S4 proxy ban, S5 identical lists), exits 1 on drift.
- Item 5 (AE): untouched (git-verified). Item 6: before/after table produced; no next-round experiments started.
- Full corrected re-runs completed (Dom, CPU, ~3.5 h): NASA proxy_audit 5 seeds, charge (Clean-6*/7/8), CS2 4 arms; all fresh files committed.
- Round 4 progress report drafted, humanized (4 audit passes: overclaim=0, -ly adverbs stripped, causal wording hedged), every number tied to a committed CSV, 19 GitHub links verified against the git tree.

### Evidence

- Report: `Autoencoder/round3_phase1/round4_progress_report.md` (+ `r4_fig_clean_sets.png`, `r4_fig_b0006_c7_c8.png`, `r4_ridge_probe.py`)
- Corrected results (all committed): `td_proxy_audit_r4full5_results.csv` (TD-All 0.923, ProxyFree 0.874, Oracle 0.655), `td_clean_cpu_results.csv` (Clean-4 −0.349, Clean-6 0.601), `phase3_charge_r4_results.csv` (C6* 0.735, C7 0.807, C8 0.776), `phase4_cs2_{within,transfer,adapt1,adapt2}_full.csv` (within 0.158/med 0.573; transfer room −14.3/all13 −92.3; adapt1 −437/adapt2 −3.49)
- Old-protocol "before" numbers preserved at commits `c5ddbd4` (CS2 arms) and `af1d278` (NASA Clean sets, proxy_audit 3 seeds)
- Suite: `round4_structural_verify.py` — 25/25 PASS (2026-10-10)

### Decisions

- **New finding (verified, not a bug):** Clean-8 0.776 < Clean-7 0.807 under the corrected protocol — the old 0.810 > 0.772 gain from `t_40_41` does not survive 3-fold rotation. Evidence: inner-val RMSE ranks C8 best while its test R² on B0006 is worst (0.44 vs 0.63); drop is B0006-specific (all 5 seeds negative); ridge probe (no selection) shows no gain. Clean-7 is now the strongest proxy-audited set.
- Inner "single" branch kept only for bit-identical Phase 1 reproduction (explicit arg).
- CS2 selection uses one seed-drawn validation battery (NOT rotated) — flagged to the advisor in the report §3 as an open interpretation question (rerun cost ~1 h if the advisor wants rotation).
- adapt1 (scratch) vs adapt2 (warm) use different adaptation scales — kept as designed, per-arm definitions.
- Seeds: NASA {42,7,123,2024,11}; CS2 {42,7,99,123,2024} — each family matches its own committed baseline.

### Unresolved

- Dom: read the report draft, convert to PDF in Antigravity, email the advisor.
- Advisor: Round 5 reply (direction choice + CS2 rotation answer + title).
- Title answer (carried); Ch.2 waits.

### Files changed

- Code: `r3common.py`, `phase4_cs2_{within,transfer,adapt1,adapt2}.py`, `td_proxy_audit.py`, `round4_structural_verify.py` (new), `r4_ridge_probe.py` (new)
- Results: `td_clean_cpu_results.csv`, `td_proxy_audit_r4full5_*.csv`, `phase3_charge_r4_*.csv`, `phase4_cs2_*_full.csv` (4 files)
- Report: `round4_progress_report.md` + 2 figures

### Verification

- Structural suite 25/25 PASS (exit 0, 2026-10-10). In-process reproduction of one transfer and one adapt1 selection matches the committed CSVs exactly. All report numbers re-derived from CSVs in the final audit.

### Objective

- Send the Round 4 progress report to the advisor; await Round 5 direction.

### First action

- Ask Dom whether the advisor email was sent and whether a Round 5 reply exists in `Comment Prof and Report/Comment Prof/`; if yes, read it before anything else.

### Required files

- `advisor_directives.md`, `active_experiment.md`, `Autoencoder/round3_phase1/round4_progress_report.md` (the verified results + before/after table), `round4_structural_verify.py`.

### Stop conditions

- Stop before a major experiment, protocol change, feature-policy change, or thesis-direction change unless a PAEV plan has been approved.
- Stop if a result cannot be tied to its row set, unit, protocol, feature set, and source artifact.
- Round 4 headline numbers are now the corrected-protocol values in the report; do not quote the pre-correction numbers (0.490 / 0.810 / −0.59 etc.) without the "before" label.

## 4. Where we are

| Phase | scope | advisor items | status |
|---|---|---|---|
| 1 | protocol fixes + proxy audit | R3-C1, R3-C3 | ✅ complete |
| 2 | protocol-gap experiment | R3-C2 | ✅ complete |
| 3 | proxy-free improvements | R3-C5 (5.1–5.5) | ✅ complete |
| 4 | wider validation | R3-C6 (6.1–6.3) | ✅ complete (2026-10-05) |
| 5 | EIS/AE role + documentation | R3-C7 | ✅ complete (7.4 + all chapter drafts v0.1) |
| 6 | citation verification | R3-C9 | ✅ complete (2026-10-06) — 13/13 papers verified from full PDFs |

Thesis direction: **proxy-audited, partial-window, unseen-battery SOH estimation** — title proposal
awaiting the advisor's answer (report §10). Contribution (1) = how much published accuracy comes from
protocol + proxy features (**measured**: −1.03…0.99 protocol axis; −0.40…0.93 proxy axis).
Contribution (2) = the honest cross-battery / cross-dataset number (**measured**, incl. the within-CS2
control). Target paper: Sardar et al. 2026 [11] (EIS + discharge + cross-battery already published —
not our novelty).

---

## 5. Headline results needed for current decisions

**Protocol axis (TD-All, nested LOBO):** random 0.979 / ours 0.927 / chronological −1.028 per-fold
(+0.850 pooled). Oracle 0.992 same-battery vs 0.663 LOBO (phase-1, refit_on_3; the phase-2 run gives
0.671 — different row set, never compared). "Oracle ≈ 1" is protocol-scoped.
**Round 4 corrected protocol (true 3-fold inner LOBO):** TD-All 0.923 (unchanged), Proxy-Free 0.874,
Oracle 0.655.

**Proxy axis (Round 4 corrected protocol — supersedes the numbers below):** TD-All 0.923 → Clean-6
0.601 (636-row set) / Clean-6* 0.735 (631-row set) → **Clean-7 0.807** (+`ic_peak_V`, still helps) →
**Clean-8 0.776** (+`t_40_41`, **now below Clean-7** — the old 0.810 gain was selection-variant;
verified: inner-val ranks C8 best while B0006 test is worst, and a selection-free ridge probe shows
no gain). Clean-4 −0.349 (too few features).
Pre-correction values (single inner validation): Clean-6 0.490, Clean-7 0.772, Clean-8 0.810,
Clean-4 −0.400, Proxy-Free 0.854, Oracle 0.663 — quote only with the "before" label.
Window curve: proxy-free flat 0.842–0.843 across 5–30 min (caveat: W5-PF also drops `dis_V_slope`
and swaps `dis_mean_T`).

**Cross-dataset (Round 4 corrected Clean-6T, 6 features — supersedes "within 0.59 / transfer −37"
below):** within-CS2 LOCO mean 0.158 / median 0.573 (old 8-feature: 0.235/0.589 — the two removed
proxies carried little); transfer room −14.3 (median −2.8) / all13 −92.3; scratch −437, warm −3.5
(both medians improved vs old −68/−31 but still non-viable). Root cause: target range mismatch
(NASA SOH 57–101% vs CS2 87–113%) + 5 of 6 features outside the NASA min–max range on a large share
of CS2 cycles (cc_dur 93% above, cv_dur 62% below, ic_peak_V 41% below, t_40_41 37% above) —
transfer is not viable without target-range alignment or domain adaptation.

**Three negatives with mechanisms:** fixed V-window (5/7 window features are proxies; `win_dur`
0.995 > `dis_duration` 0.972); self-referenced normalisation (0.075; B0018 `cv_I_slope` reference
6× smaller — it *introduces* scale mismatch); ΔSOH accumulation (−4.785; biased increment
integrates linearly, corr(cycle position, |error|) up to +0.993).

**Key literature facts (verified from full PDFs, `r3c9_citation_verification.md`):**
[11] random 0.9788 → battery-wise 0.7855 (matches audit verbatim); [9] B0006 LOCO 0.2464→0.5286,
uses cycle index, self-declares conformal limits, also fails B0006; **[10] EWDC 0.975 = within-dataset
LOBO on the same cells as ours**, proxy-laden features (cycle index + cumulative charge), ŷ₁=1 anchor
→ compare against our TD-All 0.927, never against Clean-8; [7] is the only cross-battery R²≈0.98
(Oxford, 1-train/rest-test — smallest scope); B0018 is [10]'s worst fold (1.91 % vs avg 1.21 %).

**Disagreements with advisor expectations (report, don't bury).** Oracle protocol-scoped; the
alternative inner loop does not help B0006 (the re-fit did, 0.686 → 0.900); self-reference hurts;
the fixed window strengthens the proxy; ΔV = 0.1/0.2 V cannot form a window on these files. Title
caution: a partial window is **not** proxy-free by construction — defensible phrasing is
"proxy-audited, partial-window". (7) "add B0025–B0056 (similar conditions)" is not supported — the
premise is false and mixed-condition pooling hurts; (8) "more batteries ⇒ better" holds only within a
condition.

---

## 6. Completed work pointer

Detailed Round 3 phase history, verification ledger, bug log, data notes, environment facts, and artifact map live in `Autoencoder/round3_phase1/PROJECT_STATE.md` and the phase summary files. Do not copy that detail into this card.

## 7. Round 3 work plan and status (all phases done)

> This section is retained as a compact transition record. For normal pruning, load only sections 1–3, 11, and 12; load the detailed sections only when coding, verification, or artifact lookup requires them.

### Phases 1–3 ✅ (detail in PROJECT_STATE.md)

Phase 1: re-fit on 3 (TD-All 0.848→0.923; B0006 0.686→0.900); 3-fold inner LOBO alternative
0.9174 (Δ−0.006); proxy audit 0.927/0.845/0.671; `dis_duration` 0.972 and `dis_mean_V` 0.948 are
PROXY. Phase 2: `protocol_gap_exp.py`, four protocols × three settings × five seeds, `lobo_nested`
reproduces Phase 1 bit-for-bit. Phase 3: 5.1 supported (paired 0.664→0.810) · 5.2 not established ·
5.3 rejected · 5.4 rejected · 5.5 done (PF flat 0.842–0.843).

### Phase 4 ✅ (2026-10-05)

**6.1 Learning curve:** 420 fold-runs, per-condition reporting, integrity proven (determinism,
840 leakage asserts, 4-cell reproduction 0.933). **6.3 CS2:** four arms — frozen −37 /
scratch-1-cell −68 / warm-1-cell −31 / **within-CS2 control 0.59** — failure is domain shift from
per-cell label offset. **R3-C6 closed.**

### Phase 5 ✅ (2026-10-06/07)

- **(7.4)** `advisor_directives.md` carries the R3-C7 outcome: AE demoted to a documented negative
  result (commit `4f3feec`).
- **Chapter drafts v0.1, all committed:** Ch.1 (title = PLACEHOLDER + [TITLE-DEPENDENT] marks,
  `e39f56b`), Ch.3 (`0a81aea`), Ch.4 (`edd66f0`, corrections in `8f4d766`), Ch.5 (`6d3becb`),
  Appendix A.1–A.9 (`e39f56b`, tolerance detail corrected).
- **Round 4 report to advisor** (`8f4d766`, links `f156bc9`, humanized `69c8ea3`):
  `round3_phase1/round4_report_to_advisor.md` — **ready to send**; one question left (title).
  PDF/HTML generator belongs to Antigravity (do not commit).

### Phase 6 ✅ (R3-C9, 2026-10-06)

- EWDC [10] identified from the local PDF (`Journal Prof Recommend/`): Zhao, J.; Qian, X.; et al.,
  *Energies* 2026, 19, 4326 — recorded in `advisor_directives.md` (R3-C9 Part 1, commit `244d69d`).
- All 13 audit papers downloaded by Dom into `Journal Discovery/Gap_audit_paper_Prof_Recommend/`,
  verified from full PDFs into `round3_phase1/r3c9_citation_verification.md` (commit `8b4135b`).
  Quartiles are provisional — confirm on JCR/SJR before the final thesis PDF.

---

## 8. Artifacts map (all tracked and pushed; HEAD `248d5b8`)

| path | content |
|---|---|
| `round3_phase1/round4_progress_report.md` | **Round 4 progress report (corrected-protocol results, before/after table, 2 figures, humanized) — ready for Dom's PDF + advisor email** |
| `round3_phase1/round4_structural_verify.py` | structural suite: 25 checks (S1 3-fold count, S2 disjoint, S2b within completeness, S3/S4/S5 feature guards); exit 1 on drift |
| `round3_phase1/r4_ridge_probe.py` | selection-free ridge probe (Clean-8 finding, Section 1.1 evidence) |
| `round3_phase1/round4_report_to_advisor.md` | the earlier Round 4 report (protocol description; superseded by `round4_progress_report.md` for the results tables) |
| `round3_phase1/r4_fig_clean_sets.png`, `r4_fig_b0006_c7_c8.png` | report figures (from `phase3_charge_r4_*.csv`) |
| `round3_phase1/td_proxy_audit_r4full5_results.csv` | TD-All / Proxy-Free / Oracle, 5 seeds, true lobo3 |
| `round3_phase1/phase3_charge_r4_results.csv` | Clean-6*(631r) / Clean-7 / Clean-8, 5 seeds, true lobo3 |
| `round3_phase1/phase4_cs2_{within,transfer,adapt1,adapt2}_full.csv` | corrected Clean-6T 4 arms (with `val_battery` column) |
| `round3_phase1/td_clean_cpu_results.csv` | Clean-4 / Clean-6 (636-row set), 5 seeds, true lobo3 |
| `round3_phase1/r3c9_citation_verification.md` | 13 papers × value/unit/protocol/proxy/quartile table |
| `round3_phase1/PROJECT_STATE.md` | phase map, two axes, 210-check ledger, bug log (Phases 1–3) |
| `round3_phase1/round3_status_for_advisor.md` | R3-C1…C9 compliance + Phases 1–4 (superseded by the Round 4 report but kept) |
| `round3_phase1/thesis_ch1_introduction_draft.md` | Ch.1 v0.1 (title placeholder) |
| `round3_phase1/thesis_ch3_methodology_draft.md` | Ch.3 v0.1 (justifies LOBO, leakage, refit_on_3) |
| `round3_phase1/thesis_ch4_protocol_draft.md` | Ch.4 v0.1 (results; row-set notes) |
| `round3_phase1/thesis_ch5_discussion_draft.md` | Ch.5 v0.1 (7 factors, AE qualification, limitations, contributions) |
| `round3_phase1/thesis_appendix_negative_results.md` | Appendix v0.1 (A.1–A.9: AE, interp, tolerance, self-ref, ΔSOH, window, 6.1/6.3, config ablations, instability) |
| `round3_phase1/phase1_oracle_findings.md` | oracle analysis + the selection-guard fix |
| `round3_phase1/phase2_summary_two_axes.md` | the Chapter 4 core table |
| `round3_phase1/r3c3_feature_classification.md` | every TD feature labelled safe / proxy |
| `round3_phase1/phase3_*_summary.md` | items 5.1–5.5 summaries |
| `round3_phase1/phase4_survey_B0025_B0056.md` | premise audit (why "similar conditions" is false) |
| `round3_phase1/phase4_extract_features.py` + `.csv` + `phase4_verify.py` | wide extraction (19 cells / 1,695 rows / 14 included) + 20-check suite |
| `round3_phase1/phase4_charge_common.py` | shared charge-feature maths (single source of truth) |
| `round3_phase1/phase4_learning_curve_summary.md` + `_full_results.csv` | 6.1 (420 runs) |
| `round3_phase1/phase4_cs2_summary.md` | 6.3 four-arm summary |
| `round3_phase1/phase4_cs2_features.py` + `.csv` | CS2 extraction (xlsx + txt parsers) |
| `round3_phase1/phase4_cs2_transfer.py` / `phase4_cs2_adapt1.py` / `phase4_cs2_adapt2.py` / `phase4_cs2_within.py` | frozen / scratch / warm / control + their `_full.csv` |
| `round3_phase1/r3common.py` | shared runner: `run_fold`, the selection guard, CLEAN feature sets |
| `round3_phase1/*_verify.py`, `phase3_feature_audit.py`, `data_provenance_audit.py` | the Phase 1–3 verification suite (210 checks) |
| `nested_lobo/*.csv`, `nested_lobo/extract_time_features.py` | Round 2 originals — **NOT modified** |
| `Autoencoder/scripts/`, `Autoencoder/configs/`, `Autoencoder/eis_verify/` | Round 2 pipeline + EIS verification |
| `NASA DataSet/`, `CALCE/` | source data (CALCE CS2_33–38, 8, 21; added to the manifest, gitignored by size — `248d5b8`) |
| `Journal Discovery/Gap_audit_paper_Prof_Recommend/` | the 13 verified papers (+ `R3-C9_verify/` text extracts; PDFs gitignored by size) |

---

## 9. Verification ledger

**Phases 1–3: 210 checks** (61+23+7+26+8+9+7+7+12+50) — re-run 2026-10-06 from `round3_phase1/`,
**all pass**:

```
for s in phase1_verify protocol_gap_verify td_clean_verify data_provenance_audit \
         phase3_charge_verify phase3_selfref_verify phase3_window_verify \
         phase3_dsoh_verify phase3_windowlength_verify phase3_feature_audit; do
  "C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe" $s.py | tail -1
done
```

**Phase 4:** `phase4_verify.py` 20/20 (wide extraction) + learning-curve integrity (determinism,
840 leakage asserts, 4-cell reproduction 0.933) + CS2 capacity cross-check ≤ 0.004 Ah + CS2 run
completeness grids (420 / 80 / 40 / 40 / 40, all exact). Leakage probes `max|diff| = 0.00e+00`
everywhere; provenance matches the advisor's audit (69.9 / 57.2 / 74.4 / 72.9).

**Round 4 report corrections found and fixed (2026-10-06):** Oracle LOBO 0.671 → **0.663** in Ch.4
(phase-1 value); 0.845 vs 0.854 row-set note added; §6.1 numbers synced to the phase-4 file
(per-condition medians). All three files (Ch.4, report, appendix) now consistent.

---

## 10. Data format notes (needed when writing code)

**NASA**
- Battery ids 1/2/3/4 = B0005/B0006/B0007/B0018 (`BATT` dict; id ≠ NASA name)
- SOH = `Q / Q_ref × 100`, Q_ref = mean of first 5 discharge capacities; 636 cycles (168/168/168/132)
- Phase 3 runs use a 631-row subset (5 cycles lack a usable CC phase → `ic_peak_V` NaN)
- Discharge cut-offs 2.7/2.5/2.2/2.5 V; sample interval 18.7 s (B0005) vs 9.4 s (B0018)
- Charge CC 1.5 A → 4.19 V → CV (CC_V = 4.19 everywhere)
- `.mat` beyond B0018: data under key = cell name (`m['B0025'].cycle`)

**Phase 4 wide pool** (`phase4_features.csv`): 14 included cells (B0005/6/7/18 + B0025–28 pulsed +
B0029–32 43 °C + B0047/48 4 °C); excluded B0033/34/36 (corrupt heads / 2.44 Ah spurious), B0045
(1 usable row), B0046 (Q_ref 11 % off); row rule: drop capacity < 1.0 Ah; `has_prev_charge` column
marks the 9 structural-NaN rows.

**CALCE CS2** (`C:\Master Degree\Thesis\CALCE\`, 8 cells)
- `CS2_33–38`: `.xlsx` — data in the sheet starting `Channel` (sheet 0 is an Info header); columns
  `Voltage(V)`, `Current(A)`, `Charge_Capacity(Ah)`; **no temperature**; sample ~10–30 s
- `CS2_8/21`: `.txt` Arbin, tab-separated; `Time` column is **MINUTES**; has Temperature
- Charge CC 0.5 C → 4.2 V → CV to 0.05 A; pairing rule: discharge ↔ the LONGEST charge segment
  since the previous discharge; charges longer than 4 h are not recharges (trickle over breaks)
- Hygiene: full cycle = cap ≥ 0.8 × cell max (`cap_ok`); cell included if ≥ 20 full cycles;
  all 8 cells included; 4,922 full cycles

**Feature sets:** TD-All = 8 features; Clean-8 = Clean-6 + `ic_peak_V` + `t_40_41`;
**Clean-6T** = Clean-8 minus `dis_mean_T`/`ch_mean_T` (the CS2-usable set)

**EIS (Round 2, unchanged):** 887 impedance records; interpolation grids `linspace` /
`logspace(0.1, 5000)` Hz, 39 measured → 128 dense points; 256-dim vector. Ablation log:
`YYYY-MM-DD | exp | key_metric | insight` in the user profile.

---

## 11. Environment facts (this machine)

- Dom's Python 3.11.6 (scipy / numpy / pandas / matplotlib / torch 2.5.1+cu121 / sklearn / reportlab
  / pypandoc / openpyxl):
  `C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe`
- ⚠️ **In cmd, a bare `python` is NOT Dom's Python** — it resolves to Hermes' 3.14.7 (no torch/pandas).
  Use **`py`** or the full quoted path. `PY="..."` is bash syntax and fails in cmd with `[Errno 22]`.
- In the Hermes bash terminal the full path works and `PY="..."` is fine.
- `pdftotext` is available in the Hermes bash terminal (used for the C9 PDF verification).
- No MiKTeX → PDF = Dom's Antigravity; pandoc 3.9 via pypandoc-binary for .md → .docx.
- Git repo: `github.com/DomIncham/soh-thesis-ae-bpnn` (PRIVATE, advisor has access). Root:
  `C:\Master Degree\Thesis\`. **Never `git add -A`** — stage explicit paths after `git status`.
  Antigravity-owned files (`generate_round4_pdf.py`, `round4_report_to_advisor.pdf/.html`) stay
  untracked.
- `*.log` gitignored except `round3_phase1/*.log` (run logs stay tracked as gate evidence).
- CPU ~47 s per fold-seed at 500 epochs; CUDA changes arithmetic — `--device cpu` for comparability.

---

## 12. Lessons (carry forward — full list in PROJECT_STATE.md)

Round 3 meta-lesson: **verification is where the bugs are, not the pipeline.** Phase 1–3 rules:
assert at the claim's aggregation level; NaN-safe helpers; compute expected values, never type them;
mask before stack; degenerate-config guard (`MIN_EP`); report dispersion with proxy-free numbers;
check the metric before believing it (R² dies when the test range collapses).

**Phase 4 additions:**
1. Re-derived extractors must byte-match the old CSVs (max|diff| = 0) before use; cc_dur / cv_dur /
   cv_I_slope come from the PRECEDING CHARGE cycle, never recomputed from the discharge cycle; rows
   with no preceding charge must be NaN, not fallback values.
2. Units/format traps: Arbin txt `Time` = minutes; pandas attribute access fails on `Voltage(V)`
   (use `d["Voltage(V)"]`); datetime → seconds before `np.diff`; `.mat` key = cell name; xlsx sheet
   0 may be a header — pick the `Channel_*` sheet.
3. Cross-domain findings: heterogeneous training helps out-of-domain but hurts in-domain — report
   per-condition; a divergent candidate (NaN val loss) is a skipped candidate, not a crash.
4. Harness resilience: guard every fit (selection AND refit AND retrain paths), checkpoint per seed
   with resume; a "fine-tune" that actually re-inits is a different experiment — load the state
   dict, keep the source normalisation fixed, use a low LR when inputs fall outside the source
   range (lr 1e-3 diverges on CS2, 1e-4 + grad-clip is stable).
5. Always run a within-domain control before calling a cross-domain failure a model failure.

**Round 4 additions (documentation phase):**
6. Row-set discipline: numbers from different row sets (0.845 vs 0.854; 0.663 vs 0.671) must be
   quoted only against their own row set, with a note at the point of use — verify scripts flag
   cross-row-set comparisons.
7. Cite from the full PDF, never from an audit summary; annotate unit + protocol next to every
   quoted number (R3-C9 rules 1–3).
8. Agent-generated prose gets a humanize pass before it goes to the advisor: no bold-sculpted
   numbers, no emoji headers, no em dashes, no overclaim adverbs, first person, signed.

---

## 13. Open items carried forward

| item | status |
|---|---|
| **Send the Round 4 progress report** | Dom: read + Antigravity PDF + advisor email — the immediate next action |
| Advisor Round 5 reply | direction choice (charge-side vs domain-shift) + CS2 inner-rotation answer |
| Advisor's reply on the thesis title | the only Ch.1/Ch.2 blocker (carried) |
| Quartile confirmation (JCR/SJR) | before the final thesis PDF (provisional list in `r3c9_citation_verification.md`) |
| Per-point EIS frequency | open limitation; ask dataset authors — advisor decision |
| Transfer learning (Part K) | superseded by the Round 4 domain-shift finding — now an advisor-direction item |
| Ch. 2 Literature Review | ready to draft — table source is `r3c9_citation_verification.md`; waits on title |
| CS2_8 / CS2_21 anomalies | noted in the summary; CALCE's condition table is not machine-readable — low priority |

---

## 14. What the next session should do

**Round 5 session (thesis/research).** The authoritative handoff is Section 3. Expected state: the
advisor has received the Round 4 progress report (`round4_progress_report.md`) and replied. Read the
Round 5 comment from `Comment Prof and Report/Comment Prof/` first — the next direction is the
advisor's choice between (a) charge-side features, (b) domain-shift mitigation (start with the
target-range observation in §5), (c) other models for protocol consistency, or (d) thesis writing.
Do not start any of these before reading the reply. If no reply exists, the session can only do
low-risk maintenance (suite re-run, link checks).

---

## 16. Final report workflow

After the work requested by an advisor round is completed, create or update the final round report as a Markdown file in the relevant research-work folder under `Autoencoder/`. The report is a human-readable evidence record, not a raw log.

### Report requirements

1. Link every important result, script, table, verification file, and relevant artifact to its exact GitHub path or commit so the advisor can inspect the evidence.
2. Write from the verified evidence. Preserve the correct row set, unit, protocol, feature set, and proxy status next to every metric.
3. Perform a detailed humanize pass before delivery. The prose must read as Dom's own writing, with no unexplained AI-written style, inflated claims, unnecessary adverbs, or excessive `-ly` wording.
4. Prefer direct sentences and measured claims. Do not add conclusions that are not supported by the experiment or verification output.
5. Keep the final `.md` as the content source of truth.

### Antigravity handoff

After Capi completes the Markdown report and humanize pass, Dom sends the `.md` to Antigravity. Antigravity may convert it to PDF and apply visual styling, but must preserve the Markdown content exactly: no additions, deletions, reinterpretation, or new claims.

### Naming convention

Use one final report per advisor round:

```text
advisor_round_03_final_report.md
advisor_round_04_final_report.md
advisor_round_05_final_report.md
```

Keep the final Markdown source with the research work so it is easy to update alongside verified results. Store only Antigravity's converted PDF deliverable in `Comment Prof and Report/Report/`; HTML is optional and should be stored there only when needed. Do not duplicate the Markdown report in the report-deliverables folder. Add the Markdown path to the current handoff only when it is needed for the next task. Keep reusable conversion scripts in the working/research area and track them explicitly.

---

## 15. Permanent session-start pruning protocol

Use this unchanged prompt at the start of every new research, coding, experiment, verification, or thesis session:

```text
Load the `soh-research` skill first.
Read these two live files with explicit offset/limit pagination:
1. `C:\Master Degree\Thesis\advisor_directives.md`
2. `C:\Master Degree\Thesis\active_experiment.md`

This is a combined reasoning + implementation/coding session. If the current state says thesis writing is active, include thesis drafting; otherwise follow the current scope in `active_experiment.md`.
Continue from the latest session handoff in `active_experiment.md`.
Do not assume that any particular advisor round, phase, blocker, or work type is pending, active, or complete; read the current state from the state card and source files.
Do not infer advisor requirements that are not present in the source files.

Before acting:
1. State the current objective, blocker, and smallest useful next step.
2. Decide whether the task is reasoning, coding, verification, or a combination.
3. Load only the specific workflow section, summary, script, data contract, or verification file needed for that step.
4. If a file is over 200 lines, find headings first and read only the relevant line window.

During work:
- Keep reasoning and coding in the same session.
- Follow PAEV: plan → approval when required → execute → verify → ablation log if applicable → commit/push.
- Do not start a major experiment, change protocol, change feature policy, or change advisor/thesis direction without an explicit plan and approval.
- Small maintenance, targeted inspection, smoke tests, and verification may proceed directly.
- Never use `git add -A`; stage explicit paths only.
- Preserve row-set, unit, protocol, feature set, and proxy labels next to every metric.
- Never overwrite original advisor comment files.

At the end:
1. Verify the real output or test result.
2. Update `active_experiment.md` as the latest handoff: current state, completed work, evidence, decisions, unresolved items, changed files, verification, next action, required files, and stop conditions.
3. If a final advisor-round report was completed, verify its GitHub links and complete the humanize check before handing the `.md` to Antigravity.
4. Keep the handoff factual and concise; do not copy full logs or historical detail.
5. Commit and push verified work using explicit paths.
6. Report the next session's smallest useful action.
```

### Loading rules for this mode

- Normal session: `advisor_directives.md` + `active_experiment.md`.
- Coding/experiment planning: add the relevant section of `end_to_end_research_workflow_v2.md` and the relevant phase summary.
- Coding implementation: add only the target script and its direct verification script.
- Verification: add the relevant summary, verification script, and result file.
- Historical advisor question: add the relevant file under `advisor_rounds/` only.
- Do not load `advisor_rounds/advisor_directives_archive.md` during a normal session.
- Do not load thesis chapter drafts unless the task explicitly changes scope to thesis writing.

---

*Last updated: 2026-10-10 — Round 4 complete: 6 advisor items verified, corrected-protocol re-runs
committed, structural suite 25/25, progress report drafted and humanized (`round4_progress_report.md`,
commit `db47f1d`). Next: Dom sends the report; Round 5 = advisor's chosen direction. Headline numbers
in §5 are the corrected-protocol values.*
