# ACTIVE EXPERIMENT — Round 3, Phase 4 Complete (Phases 5–6 remain)

> **READ THIS FIRST (new session):** load skill `soh-research` → read `advisor_directives.md` (SSOT) →
> read `end_to_end_research_workflow_v2.md` → then this file. Use `read_file` with `offset`/`limit` for
> the thesis `.md` files; **never `skill_view`** on them (compression + cache loop).
>
> **Updated:** 2026-10-05 · **Status:** **Round 3 Phase 4 complete — R3-C6 closed (6.1 + 6.2 + 6.3).**
> Phases 5–6 not started. **Blocked on:** nothing experimental — two questions to the advisor
> (EWDC [10] reference; thesis-title qualification) block only citations/title, not work.
>
> **Advisor:** Y.F. Luo (YF.Luo@mail.ntust.edu.tw) — collaborator on the private repo
> `github.com/DomIncham/soh-thesis-ae-bpnn`; all progress is pushed to `main` for review.
>
> **NEW WORKING RULE (2026-10-05): every step of every task ends with a git commit + push** — code,
> results CSVs, run logs, summary `.md` and this state card are committed as soon as the step is
> verified. Never batch several steps into one commit; never leave verified work un-pushed.
>
> **Detail lives elsewhere.** Each item has its own summary in `Autoencoder/round3_phase1/`;
> `PROJECT_STATE.md` there holds the phase map, verification ledger and bug log. This card is the
> entry point, not the archive.

All work runs under **PAEV**: Plan with the 4-Rule → Dom approves → Execute → Verify with gates →
Ablation log → Commit. Division of labour: Capi writes / smoke-tests / verifies (CPU); Dom runs the
long `--full` jobs on the RTX 3050; Capi delivers `.md` only and Dom converts to PDF in Antigravity.

---

## 1. Where we are

| Phase | scope | advisor items | status |
|---|---|---|---|
| 1 | protocol fixes + proxy audit | R3-C1, R3-C3 | ✅ complete |
| 2 | protocol-gap experiment | R3-C2 | ✅ complete |
| 3 | proxy-free improvements | R3-C5 (5.1–5.5) | ✅ complete |
| 4 | wider validation | R3-C6 (6.1–6.3) | ✅ complete (2026-10-05) |
| 5 | EIS/AE role + documentation | R3-C7 | ⬜ next — the 7.3 demote-AE draft claim is already written in the advisor doc |
| 6 | citation verification | R3-C9 | ⬜ blocked on the EWDC [10] reference |

Thesis direction: **proxy-audited, partial-window, unseen-battery SOH estimation** (qualify "proxy-
free" — see §4). Contribution (1) = how much published accuracy comes from protocol + proxy features
(**measured**). Contribution (2) = the honest cross-battery / cross-dataset number (**measured,
including its limits**). Target paper: Sardar et al. 2026 (EIS + discharge + cross-battery already
published — not our novelty).

---

## 2. What Round 3 measured (headline numbers)

**Protocol axis (TD-All, nested LOBO):** random 0.979 / ours 0.927 / chronological −1.028 per-fold
(+0.850 pooled). Oracle 0.992 same-battery vs 0.671 LOBO — "oracle ≈ 1" is protocol-scoped.

**Proxy axis (nested LOBO):** TD-All 0.927 → Clean-6 0.490 → **Clean-7 0.772** (+`ic_peak_V`,
supported, 15/20) → **Clean-8 0.810** (+`t_40_41`, within noise). No feature above 0.49
R²(capacity) in Clean-8. Window curve: proxy-free flat 0.842–0.843 across 5–30 min (caveat: W5-PF
also drops `dis_V_slope` and swaps `dis_mean_T`).

**Three negatives with mechanisms:** fixed V-window (5/7 window features are proxies; `win_dur`
0.995 > `dis_duration` 0.972); self-referenced normalisation (0.075; B0018 `cv_I_slope` reference
6× smaller — it *introduces* scale mismatch); ΔSOH accumulation (−4.785; biased increment
integrates linearly, corr(cycle position, |error|) up to +0.993). EWDC's 0.975 does not transfer.

**Disagreements with advisor expectations (report, don't bury).** Oracle protocol-scoped; the
alternative inner loop does not help B0006 (the re-fit did, 0.686 → 0.900); self-reference hurts;
the fixed window strengthens the proxy; ΔV = 0.1/0.2 V cannot form a window on these files; EWDC
[10] is not in the local materials. Title caution: a partial window is **not** proxy-free by
construction — the defensible phrasing is "proxy-audited, partial-window". **Phase 4 adds two more:**
(7) "add B0025–B0056 (similar conditions)" is not supported by the data — the premise is false and
mixed-condition pooling hurts; (8) "more batteries ⇒ better" holds only within a condition, while
heterogeneous training marginally helps out-of-domain (all13 median −24 vs room −37).

---

## 3. Round 3 work plan and status

### Phases 1–3 ✅ (detail unchanged from the previous revision, kept in PROJECT_STATE.md)

Phase 1: re-fit on 3 (TD-All 0.848→0.923; B0006 0.686→0.900); 3-fold inner LOBO alternative
0.9174 (Δ−0.006); proxy audit 0.927/0.845/0.671; `dis_duration` 0.972 and `dis_mean_V` 0.948 are
PROXY. Phase 2: `protocol_gap_exp.py`, four protocols × three settings × five seeds, `lobo_nested`
reproduces Phase 1 bit-for-bit. Phase 3: 5.1 supported (paired 0.664→0.810) · 5.2 not established ·
5.3 rejected · 5.4 rejected · 5.5 done (PF flat 0.842–0.843).

### Phase 4 ✅ (2026-10-05)

**6.1 Learning curve:** see §2-disagreements and §4-Phase-4 numbers; 420 fold-runs, per-condition
reporting, integrity proven (determinism, 840 leakage asserts, 4-cell reproduction 0.933).
**6.3 CS2:** four arms — frozen −37 / scratch-1-cell −68 / warm-1-cell −31 / **within-CS2 control
0.59** — failure is domain shift from per-cell label offset. **R3-C6 closed (6.1+6.2+6.3).**

### Phase 5 ⬜ (next)

7.3 demote AE — draft claim already in `round3_status_for_advisor.md` (AE-on-TD 0.43 vs TD 0.85;
AE+0.08 vs PCA+0.61 on EIS; E_fusion 0.73 < TD 0.85). Then `advisor_directives.md` append-only
update (7.4), then chapter drafts (recommended order: Ch. 4 protocol → Ch. 5 results → Ch. 1–3).

### Phase 6 ⬜ (blocked on EWDC [10])

Open the 13 papers, confirm values/units/split protocol, convert to %SOH with the protocol noted,
check quartiles, cite originals.

---

## 4. Artifacts map (all tracked and pushed; HEAD `6a8ada2`)

| path | content |
|---|---|
| `round3_phase1/PROJECT_STATE.md` | phase map, two axes, 210-check ledger, bug log (Phases 1–3) |
| `round3_phase1/round3_status_for_advisor.md` | R3-C1…C9 compliance + Phase 3 + Phase 4 sections + AE-demotion draft + 2 questions — **ready to send** |
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
| `NASA DataSet/`, `CALCE/` | source data (CALCE CS2_33–38, 8, 21 downloaded 2026-10-05) |

---

## 5. Verification ledger

**Phases 1–3: 210 checks** (61+23+7+26+8+9+7+7+12+50) — re-run from `round3_phase1/`:

```
for s in phase1_verify protocol_gap_verify td_clean_verify data_provenance_audit \
         phase3_charge_verify phase3_selfref_verify phase3_window_verify \
         phase3_dsoh_verify phase3_windowlength_verify phase3_feature_audit; do
  "C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe" $s.py | tail -1
done
```

**Phase 4:** `phase4_verify.py` 20/20 (wide extraction) + learning-curve integrity (determinism,
840 leakage asserts, 4-cell reproduction 0.933) + CS2 capacity cross-check ≤ 0.004 Ah + CS2 run
completeness grids (420 / 80 / 40 / 40 / 40, all exact). Re-run 2026-10-05: **all passing.**
Leakage probes `max|diff| = 0.00e+00` everywhere; provenance matches the advisor's audit
(69.9 / 57.2 / 74.4 / 72.9).

---

## 6. Data format notes (needed when writing code)

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

## 7. Environment facts (this machine)

- Dom's Python 3.11.6 (scipy / numpy / pandas / matplotlib / torch 2.5.1+cu121 / sklearn / reportlab
  / pypandoc / **openpyxl — installed 2026-10-05 for the CS2 xlsx**):
  `C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe`
- ⚠️ **In cmd, a bare `python` is NOT Dom's Python** — it resolves to Hermes' 3.14.7 (no torch/pandas).
  Use **`py`** or the full quoted path. `PY="..."` is bash syntax and fails in cmd with `[Errno 22]`.
- In the Hermes bash terminal the full path works and `PY="..."` is fine.
- No MiKTeX → PDF = Dom's Antigravity; pandoc 3.9 via pypandoc-binary for .md → .docx.
- Git repo: `github.com/DomIncham/soh-thesis-ae-bpnn` (PRIVATE, advisor has access). Root:
  `C:\Master Degree\Thesis\`. **Never `git add -A`** — stage explicit paths after `git status`.
- `*.log` gitignored except `round3_phase1/*.log` (run logs stay tracked as gate evidence).
- CPU ~47 s per fold-seed at 500 epochs; CUDA changes arithmetic — `--device cpu` for comparability.

---

## 8. Lessons (carry forward — full list in PROJECT_STATE.md)

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

---

## 9. Open items carried forward

| item | status |
|---|---|
| Per-point EIS frequency | open limitation; ask dataset authors — advisor decision |
| Transfer learning (Part K) | still gated: needs the advisor to accept the root-cause finding |
| `advisor_directives.md` append-only update | Phase 5 item 7.4 |
| 2 advisor questions | EWDC [10] reference; title qualification — sent in the status doc, awaiting reply |
| CS2_8 / CS2_21 anomalies | noted in the summary; CALCE's condition table is not machine-readable — low priority |

---

## 10. What the next session should do

**Immediate:** git is clean, everything pushed (HEAD `6a8ada2`). Nothing to clean up. Dom should
point the advisor to `round3_status_for_advisor.md` (it now covers Phases 1–4 + the 2 questions).

**Then pick one (Phase 5 recommended):**
- **Phase 5 (R3-C7):** confirm the demote-AE draft with the advisor, update `advisor_directives.md`
  append-only (7.4), then draft chapters — recommended order: Ch. 4 (protocol) → Ch. 5 (results,
  from the summary docs) → Ch. 1–3. All numbers are final and verified.
- Optional pre-gate: re-run the full verification suite (210 + 20 + CS2 checks) for a fresh gate
  before writing.
- **Phase 6 (R3-C9)** stays blocked on the EWDC [10] answer.

**Working rules:** PAEV; **commit + push after every verified step**; keep this card updated.

---

*Last updated: 2026-10-05 — Phase 4 closed (6.1: 420 runs + integrity checks; 6.3: four arms +
within-CS2 control; all verified and pushed, HEAD `6a8ada2`). Working rule added: commit + push
after every verified step. Next: Phase 5.*
