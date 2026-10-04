# ACTIVE EXPERIMENT — Round 3, Phases 1–3 Complete

> **READ THIS FIRST (new session):** load skill `soh-research` → read `advisor_directives.md` (SSOT) →
> read `end_to_end_research_workflow_v2.md` → then this file. Use `read_file` with `offset`/`limit` for
> the thesis `.md` files; **never `skill_view`** on them (compression + cache loop).
>
> **Updated:** 2026-10-04 · **Status:** **Round 3 Phases 1–3 complete.** Phases 4–6 not started.
> **Blocked on:** nothing. The next decision is whether to open Phase 4 (wider validation) or to
> consolidate and report.
>
> **Advisor:** Y.F. Luo (YF.Luo@mail.ntust.edu.tw) — collaborator on the private repo
> `github.com/DomIncham/soh-thesis-ae-bpnn`; all progress is pushed to `main` for review.
>
> **Detail lives elsewhere.** Each Round 3 item has its own summary in
> `Autoencoder/round3_phase1/`; `PROJECT_STATE.md` there holds the phase map, the verification ledger
> and the bug log. This card is the entry point, not the archive.

All work runs under **PAEV**: Plan with the 4-Rule → Dom approves → Execute → Verify with gates →
Ablation log → Commit. Division of labour: Capi writes / smoke-tests / verifies (CPU); Dom runs the
long `--full` jobs on the RTX 3050; Capi delivers `.md` only and Dom converts to PDF in Antigravity.

---

## 1. Where we are

Round 2 (steps 1–18: EIS verification, AE, TD-BPNN) is closed and reported. Round 3 was opened by the
advisor's Literature Gap Audit (2026-09-26) and his GitHub response (2026-09-28, Plan A approved).
**Round 3 is now three phases in**, and the shape of the result is: one supported improvement, one
usable figure, and three measured negatives — each with an identified mechanism. That is the honest
result and it should be reported as such.

| Phase | scope | advisor items | status |
|---|---|---|---|
| 1 | protocol fixes + proxy audit | R3-C1, R3-C3 | ✅ complete |
| 2 | protocol-gap experiment | R3-C2 | ✅ complete |
| 3 | proxy-free improvements | R3-C5 (5.1–5.5) | ✅ complete |
| 4 | wider validation | R3-C6 | ⬜ not started |
| 5 | EIS/AE role + documentation | R3-C7 | ⬜ not started |
| 6 | citation verification | R3-C9 | ⬜ not started |

The thesis direction is unchanged: **proxy-free, partial-window, unseen-battery SOH estimation**, with
contribution (1) quantifying how much published accuracy comes from protocol and proxy features, and
contribution (2) the honest cross-battery number under proxy-free conditions. The target paper remains
Sardar et al. 2026 (EIS + discharge + cross-battery already published, so it is not our novelty).

---

## 2. What Round 3 measured

### Axis 1 — the evaluation protocol (per-fold mean R², TD-All, 5 seeds)

| protocol | R² |
|---|---|
| chronological split, same battery | **−1.028** (pooled +0.850) |
| nested LOBO, unseen battery (ours) | **0.927** |
| random split, same battery | **0.979** |
| random split, pooled across batteries | **0.989** |

The advisor's R3-C2 prediction ("random should reach R² > 0.97") is **confirmed at 0.979**. The
chronological split scores −1.028 per fold but +0.850 pooled — audit factor 5 visible in our own
numbers, because pooling adds between-battery variance to the R² denominator.

### Axis 2 — the capacity proxy (nested LOBO)

| feature set | #feat | mean R² | median | note |
|---|---|---|---|---|
| TD-All | 8 | 0.927 | 0.947 | contains both proxies |
| TD-Proxy-Free | 7 | 0.845 | 0.876 | **still contains `dis_mean_V`, a 0.948 proxy** |
| TD-Clean-6 | 6 | 0.490 | 0.556 | no feature above 0.90 |
| **TD-Clean-7** | 7 | **0.772** | 0.827 | + `ic_peak_V` (0.489) — **supported** |
| **TD-Clean-8** | 8 | **0.810** | 0.825 | + `t_40_41` (0.341) — the extra is within noise |
| TD-Clean-4 | 4 | −0.400 | −0.136 | — |

`TD-Clean-8` contains no feature above 0.49 R²(capacity) and reaches ~96 % of the score
`TD-Proxy-Free` reached with a 0.948 proxy inside it.

### The oracle

0.992 under the same-battery random split, 0.671 under LOBO. The advisor's "oracle ≈ 1" is correct
**for the protocol the literature uses** — and that is the mechanism behind the published high scores.
Contribution (1) is measured, not argued.

### The window-length curve (item 5.5, the advisor's "key figure")

| W (min) | PF mean R² | PL mean R² |
|---|---|---|
| 5 | **0.842** | 0.874 |
| 10 | 0.828 | 0.885 |
| 20 | 0.830 | 0.898 |
| 30 | 0.843 | 0.914 |
| full cycle | 0.778 | — |

PF = proxy-free, PL = proxy-laden. **The proxy-free curve is flat from 5 to 30 minutes** — five
minutes of discharge is enough — while the proxy-laden curve rises monotonically. Cleanest run of the
round: 0 of 96 fold-seeds degenerate.

---

## 3. Round 3 work plan and status

### Phase 1 — protocol fixes + proxy audit ✅

| step | what | result |
|---|---|---|
| 1.1 | re-fit on all 3 training batteries | TD-All 0.848 → **0.923**; B0006 0.686 → **0.900** |
| 1.1b | alternative: inner loop as a 3-fold LOBO | 0.9174 vs 0.9231 (Δ −0.006); config differs in 11/12 folds |
| 1.2 | pooled R², MAPE, RMSE in %SOH and Ah, mean/median/std | done in every summary table |
| 1.3 | proxy audit: TD-All / TD-Proxy-Free / Oracle-proxy | 0.927 / 0.845 / 0.671 over 5 seeds |
| — | R3-C3 feature labelling | `dis_duration` 0.972 and `dis_mean_V` 0.948 are PROXY (see §4) |
| — | leakage probe | `max|diff| = 0.00e+00` |

### Phase 2 — protocol-gap experiment ✅

`protocol_gap_exp.py`: four protocols × three settings × five seeds. A regression is built in — the
`lobo_nested` rows reproduce the committed Phase 1 numbers **bit-for-bit** across all 72 fold-stages.

### Phase 3 — proxy-free improvements ✅ (advisor R3-C5, items 5.1–5.5)

| item | advisor's wording | our result |
|---|---|---|
| 5.1 | charging-segment features (CC time in V-windows, CV time, IC peak) | **supported** — `ic_peak_V` improves 15/20 fold-seeds; Clean-6 0.664 → Clean-7 0.772 → Clean-8 0.810 |
| 5.2 | fixed discharge voltage window 4.0 → 3.6 V | **NOT ESTABLISHED** — 5 of 7 window features are proxies and `win_dur` (0.995) beats the whole-cycle `dis_duration` (0.972); the one admissible swap helps in only 12/20 cells |
| 5.3 | self-referenced normalisation | **REJECTED** — 0.810 → 0.075; B0018 collapses in 5/5 seeds |
| 5.4 | monotonic prior: predict ΔSOH and accumulate | **REJECTED** (accumulation) — 0.810 → −4.785; error grows with cycle position |
| 5.5 | window-length curve | **done** — PF flat 0.842 → 0.843 across 5–30 min |

### Phase 4 — wider validation (R3-C6) ⬜

Add B0025–B0056 for a learning curve vs the number of training batteries, then cross-dataset to CALCE
CS2 (the EWDC dataset, directly comparable), Oxford if time allows. **Not started; needs a decision.**

### Phase 5 — EIS/AE role (R3-C7) and documentation ⬜

Extract scalar EIS features (Re, Rct, |Z| range, arc height), fusion test against TD-only, demote the
AE to a documented negative result (AE-on-TD R² 0.43 vs raw TD 0.85; AE does not beat PCA on EIS),
update `advisor_directives.md` append-only, then draft the chapters. **Not started.**

### Phase 6 — citation verification (R3-C9) ⬜

Open the 13 papers, confirm values/units/split protocol, convert everything to %SOH with the protocol
noted, check journal quartiles before citing, cite the originals not the audit summary. **Not started.**

---

## 4. Where our measurement disagrees with an advisor expectation

Report these; do not bury them. Each is measured, not argued.

1. **Oracle ≈ 1 is protocol-scoped.** Under LOBO the oracle reaches 0.671, not ≈1, because
   `SOH = Q/Qref` and Qref differs per cell (1.842 / 2.018 / 1.883 / 1.840 Ah). Under the same-battery
   random split it reaches 0.992. The claim is right about the literature's protocol.
2. **The alternative inner loop does not help B0006.** The audit expected it to; it gives 0.891 against
   0.900, and 0.9174 overall against 0.9231. What helped B0006 was the re-fit (0.686 → 0.900).
3. **Self-referenced normalisation is not "potentially large gain".** B0018's `cv_I_slope` reference is
   6.01× smaller than the others, so dividing by it *introduces* a scale mismatch. The quoted premise
   (B0006 2.035 Ah vs ~1.86 Ah) is a **label** offset, not a feature offset — measured feature-level
   reference spreads are only 1.03–1.27× for six of eight features.
4. **ΔSOH accumulation does not transfer from EWDC.** EWDC reports R² 0.975 under LOBO; here the
   accumulation scores −4.785, because a biased increment integrates linearly (corr(cycle position,
   |error|) up to +0.993). EWDC's number came from proxy-laden features with a far stronger per-cycle
   signal.
5. **The fixed voltage window does not remove the proxy; it strengthens it.** `win_dur` R²(capacity) =
   0.995 against 0.972 for whole-cycle `dis_duration`, because at constant current the time in a fixed
   voltage window is a fixed fraction of the charge. Cross-battery comparability is also worse
   (`win_frac` spread 1.405× against 1.020×).
6. **Two suggested axes are partly unusable on these files.** ΔV = 0.1 V and 0.2 V cannot form a window
   at all (the switch-on step is ~0.2 V between the first two samples) and ΔV = 0.3 V yields only 8–13
   samples. **EWDC [10] is not in the local materials** — all 46 PDFs in `Journal Discovery/` were
   searched by name.

**A caution that matters for the thesis title.** The proposed title promises *"proxy-free,
partial-window"* estimation. Measurement says a partial window is **not** proxy-free by virtue of being
partial: `mean_V` inside any window is a proxy at every length, and window durations are the strongest
proxies in the study. Only the window's mean **temperature** stays SAFE. The claim survives, but only
with that qualification stated.

---

## 5. Artifacts map

All of `Autoencoder/round3_phase1/` is **tracked and pushed to `main`** (Round 3 runs to commit
`e26e205`). Nothing in this round is untracked.

| path | content |
|---|---|
| `round3_phase1/PROJECT_STATE.md` | phase map, the two axes, the 210-check ledger, the 14-entry bug log |
| `round3_phase1/round3_status_for_advisor.md` | compliance table for R3-C1…C9 and the R3-C8 answers — **written before Phase 3; needs a Phase 3 section before it is sent** |
| `round3_phase1/phase1_oracle_findings.md` | oracle analysis + the selection-guard fix |
| `round3_phase1/phase2_summary_two_axes.md` | the Chapter 4 core table |
| `round3_phase1/r3c3_feature_classification.md` | every TD feature labelled safe / proxy |
| `round3_phase1/phase3_charge_features_summary.md` | item 5.1 |
| `round3_phase1/phase3_window_summary.md` | item 5.2 |
| `round3_phase1/phase3_selfref_summary.md` | item 5.3 |
| `round3_phase1/phase3_dsoh_summary.md` | item 5.4 |
| `round3_phase1/phase3_windowlength_summary.md` | item 5.5, the key figure |
| `round3_phase1/r3common.py` | shared runner: `run_fold`, the selection guard, the `inner=` parameter, the CLEAN feature sets |
| `round3_phase1/*_verify.py`, `phase3_feature_audit.py`, `data_provenance_audit.py` | the verification suite (210 checks) |
| `nested_lobo/time_domain_features.csv` | 636 rows, the 8 original TD features |
| `nested_lobo/charge_features.csv` | + 6 charge/ICA features, same row order |
| `nested_lobo/window_features.csv` | + 7 fixed-window (4.0–3.6 V) features |
| `nested_lobo/windowlength_features.csv` | + 35 features for W = 5/10/20/30 min and ΔV = 0.1/0.2/0.3 V |
| `nested_lobo/extract_time_features.py` | Round 2 original — **NOT modified**, kept for reproducibility |
| `nested_lobo/steps14_16_td.py`, `Progress_Report_Steps1-18.md` | Round 2 originals — **NOT modified** |
| `Autoencoder/scripts/`, `Autoencoder/configs/` | the Round 2 pipeline, committed in `2a3d7a8` |
| `Autoencoder/eis_verify/` | steps 1–6: EIS verification scripts and reports |
| `NASA DataSet/1. BatteryAgingARC-FY08Q4/` | verified source data (tracked in Git) |

---

## 6. Verification ledger

**210 checks, all passing.** Re-run the whole suite from `round3_phase1/`:

```
for s in phase1_verify protocol_gap_verify td_clean_verify data_provenance_audit \
         phase3_charge_verify phase3_selfref_verify phase3_window_verify \
         phase3_dsoh_verify phase3_windowlength_verify phase3_feature_audit; do
  "C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe" $s.py | tail -1
done
```

| script | checks | covers |
|---|---|---|
| `phase1_verify.py` | 61 | metrics, formulas, provenance, TD-All identical across scripts |
| `protocol_gap_verify.py` | 23 | four splits + the Phase 1 bit-for-bit regression |
| `td_clean_verify.py` | 7 | clean sets, paired deltas |
| `data_provenance_audit.py` | 26 | raw `.mat` → label → features, against the advisor's own numbers |
| `phase3_charge_verify.py` | 8 | paired 5.1 |
| `phase3_selfref_verify.py` | 9 | paired 5.3 + localisation |
| `phase3_window_verify.py` | 7 | paired 5.2 |
| `phase3_dsoh_verify.py` | 7 | paired 5.4 + the drift mechanism |
| `phase3_windowlength_verify.py` | 12 | paired 5.5 + curve shape |
| `phase3_feature_audit.py` | 50 | new features vs raw `.mat`, `load_td` column order, fold coverage |

Leakage probes: `max|diff| = 0.00e+00` on every protocol and on the clean feature sets.
Data provenance: all 8 original TD features, the 6 charge features and the 7 window features
recomputed from the raw `.mat` files match the committed CSVs to ≤ 2.3e-13; `SOH = capacity/qref×100`
exactly; cycle counts and min SOH match the advisor's own audit (69.9 / 57.2 / 74.4 / 72.9).

---

## 7. Data format notes (needed when writing code)

- Battery ids 1/2/3/4 = B0005/B0006/B0007/B0018 — use the `BATT` dict, the id is not the NASA name
- SOH = `Q / Q_ref × 100 %`, `Q_ref` = mean of the first five discharge capacities
- 636 discharge cycles: 168 / 168 / 168 / 132
- The Phase 3 runs use a **631-row subset**: five cycles (B0005/06/07 cycle 86, B0018 cycles 117 and
  141) have no usable CC phase, so `ic_peak_V` is NaN there. Fold sizes are 167/167/167/130
- Discharge cut-offs differ per cell: B0005 2.7 V, B0006 2.5 V, B0007 2.2 V, B0018 2.5 V
- Sample interval differs per cell: 18.7 s (B0005) against 9.4 s (B0018)
- Charge protocol is CC 1.5 A → 4.19 V → CV for every cell; only the discharge cut-offs differ
- EIS: 887 impedance records (278/278/278/53) against 636 discharges — EIS alignment is **not** used as
  a filter
- EIS interpolation grids `linspace` / `logspace(0.1, 5000)` Hz, 39 measured → 128 dense points;
  feature vector 256 = 128 Re(Z) + 128 −Im(Z)
- Labels: `[battery_id, cycle]` in `Interpolated_*.pt`; `[battery_id, cycle, capacity_Ah, soh_pct]` in
  `Mapped_*.pt`
- Ablation log: one line per run appended to the user profile (`YYYY-MM-DD | exp | key_metric |
  insight`)

---

## 8. Environment facts (this machine)

- Dom's Python 3.11.6 (scipy / numpy / pandas / matplotlib / torch 2.5.1+cu121 / sklearn / reportlab /
  pypandoc): `C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe`
- ⚠️ **In cmd, a bare `python` is NOT Dom's Python** — it resolves to Hermes' 3.14.7, which has no
  torch or pandas, and the run dies on import. Use **`py`** (launcher → 3.11) or the full quoted path.
  `PY="..."` is bash syntax and fails in cmd with `[Errno 22] Invalid argument`
- In bash (the Hermes terminal) the full path works and `PY="..."` is fine
- Hermes' own venv lacks matplotlib — use Dom's Python for everything
- No MiKTeX/LaTeX → no pandoc PDF via xelatex. PDF = Dom's Antigravity
- pandoc 3.9 via pypandoc-binary; `eis_verify/convert_report.py` does .md → .docx
- Git repo: `github.com/DomIncham/soh-thesis-ae-bpnn` (PRIVATE, advisor has access). Root:
  `C:\Master Degree\Thesis\`
- **Never `git add -A`** — stage explicit paths after checking `git status`
- `*.log` is gitignored globally, with an exception for `round3_phase1/*.log` so the run logs stay
  tracked as gate evidence
- CPU runs are ~47 s per fold-seed at 500 epochs. Use `--device cpu` for comparability with every
  committed number — CUDA changes the arithmetic

---

## 9. Lessons (carry these forward)

**From Round 2:** never name a metric variable like its helper function; build masks with `np.isin`,
never a generator; seed `torch.manual_seed` *before* model construction; smoke-test the exact CLI line
including flag parsing; battery id ≠ NASA name.

**From Round 3 — verification is where the bugs are, not the pipeline.** Fourteen defects were found;
every one after the first two lived in the verification code or crashed before writing a file. The data
survived every check; the checkers did not. Rules that would have caught all of them:

1. **State every assertion at the same aggregation level as the claim** it supports (per-cell vs
   per-fold-mean vs per-run). Three failures came from mixing these.
2. **Never assume an equality helper is NaN-safe** (`np.array_equal` returns False when NaN is present)
   **or that a key is unique across batteries** (cycle numbers repeat per cell, so comparing cycle sets
   across batteries always "overlaps").
3. **Compute expected values, never type them.** A hand-typed row count (96 instead of 192), a
   hand-typed fold size (131 instead of 130) and a hardcoded reference number in a print statement all
   produced false signals.
4. **Mask before you stack.** `X, bids = X[mask], bids[mask]` must happen *before* `np.hstack` with a
   masked extra column — doing it after crashed twice with 636-vs-631.
5. **Use `os.path.join` for paths.** `rf"{OUT}\nested_lobo"` is fine but `rf"{OUT}\nnested_lobo"`
   silently becomes a newline plus `nnested_lobo`. Typed wrong twice.
6. **A degenerate config can silently ruin a result.** `fit_bpnn_ep` returns `best_epoch + 1`, so a
   candidate whose validation never improves returns a budget of 1 and its "best" weights are the
   initialisation. The guard in `r3common.run_fold` (`MIN_EP = 20`) fixed this and is a provable no-op
   for TD-All and Oracle. Report `sel_degenerate` counts with every run.
7. **The proxy-free regime is unstable.** Removing 5 of 636 cycles moves TD-Clean-6 between 0.490 and
   0.664, with per-(fold, seed) swings of −0.65 to +0.86. Quote proxy-free numbers with their
   dispersion and prefer paired comparisons on identical rows.
8. **Check the metric before believing it.** R² is not interpretable when the test SOH range collapses
   (the chronological split) or when one fold inverts the sign of the mean (B0018 under
   self-referencing). Report RMSE and MAPE, and the median alongside the mean.

---

## 10. Open items carried forward

| item | status |
|---|---|
| Per-point EIS frequency | open limitation; only fixable by asking the dataset authors — advisor decision |
| Transfer learning (Part K) | still gated: only after the root cause is accepted and Phases 1–3 are done |
| `advisor_directives.md` Round 3 status | append-only update is part of Phase 5 item 7.4 |
| `round3_status_for_advisor.md` | needs the Phase 3 section before it is sent |

---

## 11. What the next session should do

**Immediate, before anything new:**

1. **Update `round3_phase1/round3_status_for_advisor.md`** with a Phase 3 section — it currently covers
   only Phases 1–2 and would understate the round if sent as is.
2. **Report the three Phase 3 negatives** to the advisor with their mechanisms. This is the honest half
   of the result and it is what makes the positive half credible.
3. **Ask the advisor two concrete questions:** (a) the EWDC [10] reference, since its convention could
   not be checked locally and its 0.975 does not transfer; (b) whether the proposed title should be
   qualified given that partial-window features are not proxy-free by construction.

**Then pick one — do not do two:**

- **Option A — open Phase 4 (R3-C6).** Add B0025–B0056 and show a learning curve vs the number of
  training batteries, then cross-dataset to CALCE CS2. This is the largest remaining gap: four cells
  cannot support a generalisation claim, and it is the advisor's own next step.
- **Option B — consolidate and draft.** Write the Round 3 chapters from the summary docs: contribution
  (1) is complete and contribution (2) has a defensible number (0.772 / 0.810 proxy-free, and 0.842
  from five minutes of discharge). Phase 5 (demoting the AE) belongs here.
- **Option C — one bounded robustness run.** Take the proxy-free sets from 5 to 10 seeds to tighten the
  dispersion reported in lesson 7, before any number is written into the thesis.

**Working rules for any new experiment:** PAEV (Plan with 4-Rule → Dom approves → execute → Verify with
gates → ablation log → commit); push to `main` after each phase; keep this file updated so the next
session starts from the state card and not from a re-derivation.

---

*Last updated: 2026-10-04 — Round 3 Phases 1–3 complete (Phases 1–2 verified at 141 checks, Phase 3 at
a further 69; total 210). Artifacts map corrected: `round3_phase1/` is tracked and pushed, and the
Phase 2–3 scripts listed as "NOT CREATED YET" in the previous revision all exist and are committed. The
stale "PAEV Plan for Phase 1 — READY FOR APPROVAL" section has been removed; Phase 1 is finished.*