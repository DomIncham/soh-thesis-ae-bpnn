# ACTIVE EXPERIMENT — Round 3 Active (Advisor Approved Plan A)

> **READ THIS FIRST (new session):** load skill `soh-research` → read `advisor_directives.md` (SSOT) → read `end_to_end_research_workflow_v2.md` → then this file. Start a fresh session (`/new`) — do NOT continue the old 500k-token session.
>
> **Updated:** 2026-09-29 · **Status:** Round 2 complete (18/18 steps). Round 3 started per advisor's Literature Gap Audit (2026-09-26). Advisor responded on GitHub (2026-09-28) confirming 4 repo checks and **approving Plan A**. B7 direction no longer needed — direction is proxy-free TD path. **Blocked on:** nothing — execute Phase 1 immediately.
>
> **Advisor:** Y.F. Luo (YF.Luo@mail.ntust.edu.tw) — GitHub collaborator accepted (private repo: `github.com/DomIncham/soh-thesis-ae-bpnn` — all progress pushed to `main` for advisor review).
>
> **GitHub repo for progress tracking:** `https://github.com/DomIncham/soh-thesis-ae-bpnn` (private; advisor has access). Push after each phase completion.

---

## 1. Where we are (one paragraph)

Round 2 executed end-to-end under corrected protocol (nested 4-fold LOBO, tolerance 1, %SOH, fold-train-only scaling/standardization, EarlyStopping, seeds 42/7/123). Old Figure 10 collapse diagnosed and removed. Measured verdict: **time-domain features dominate EIS cross-battery** (B6 pattern confirmed). Advisor's Round 3 Literature Gap Audit (2026-09-26) concluded: our lower scores come from **stricter protocol and different inputs, not mistakes**. Core message: *convert strictness into novelty*. Advisor's GitHub inspection (2026-09-28) verified: (1) 8 TD features listed, `dis_duration` confirmed as proxy; (2) model NOT re-fitted on 3 training batteries (inner val used 2 only); (3) TD pipeline uses all 636 cycles (not EIS-aligned 51%); (4) current R² 0.85 is per-fold mean — advisor adding pooled R², MAPE, RMSE (Ah). Advisor **fully agrees with suggested direction** and is executing Plan A: re-fit on 3 batteries, add pooled metrics, run protocol-gap experiment. **New thesis direction:** proxy-free, partial-window, unseen-battery SOH estimation. Target paper: Sardar et al. 2026 (EIS+discharge+cross-battery already published — not our novelty). Our gap: proxy-free + partial-window + cross-dataset validation.

## 2. Final measured results (do NOT re-derive — all from real runs)

| Pipeline (12 runs each) | Test RMSE %SOH | Test R² | B0018 fold R² |
|---|---|---|---|
| **TD-BPNN** (8 time-domain features) | **3.59** | **+0.85** | **+0.79** |
| TD-Ridge | 4.35 | +0.80 | +0.76 |
| **E_fusion** (TD 8 + EIS latent 17, causal backward-time alignment) | 4.89 | +0.73 | +0.67 |
| P1 Raw EIS → BPNN | 8.32 | +0.10 | −1.19 |
| P2 PCA → BPNN | 8.48 | −0.04 | −1.97 |
| P3 AE → BPNN (bottleneck 17) | 8.57 | +0.08 | −1.00 |
| P1n per-row min-max → BPNN | 9.79 | −0.07 | **+0.22** |
| B1 Mean predictor | 11.48 | −0.35 | −0.10 |

Key step results (compressed):
- **Steps 1–4:** CSV = NASA `Rectified_Impedance`, exact on all 34,593 rows; row order low→high f (887/887, indirect); **no per-point frequency in `.mat`** → frequency column = declared assumption; flat Nyquist arc is NASA's own rectification (Case 2); B0018 has only 53 impedance spectra.
- **Step 5:** PCHIP overshoot 0 (all 1,774 checks); Cubic overshoots all 3,548 checks (worst 11.2 mOhm > full −Im span).
- **Step 6 + D3:** AE reconstructs the interpolated input, not the measurement (+~0.1 mOhm offset); B0006 anomaly is AE-specific (Re RMSE 14.6 mOhm ≈ 13× others, identical scaling).
- **Step 8:** tolerance 1/2/3 indistinguishable downstream → **tolerance 1** (pre-declared rule); retention confound = sample count (tol1 keeps 452/887; 3m arm vacuous by construction — backward matching gives identical labels).
- **Steps 9–10 (F2):** AE loses to PCA on all 3 working folds → **AE adds no measurable value**; P1n (per-row min-max) is the only pipeline positive on B0018 (+0.22) → **B0018 failure = amplitude domain shift**; Ridge explodes on B0007 (R² −10.15, deterministic).
- **Step 12:** old Figure 10 = statistically a flat line (RMSE 1.126 × std(y), 12.6% worse than the trivial mean); cause chain: unstable latents (correlation flip, R1-C6) + unstandardized Ah target + fixed 300 epochs + single split.
- **Steps 14–16 (B6 verdict, advisor's criterion applied verbatim):** TD positive on ALL 4 folds while EIS negative on B0018 → **the cross-battery failure is an EIS representation problem, not a model problem; BPNN architecture cleared.**
- **F3/I3 ablations:** bottleneck {3,7,17,37,67}, loss {MSE,MAE,Huber}, interpolation 6 configs — **all indistinguishable downstream** (keep bottleneck 17, loss MSE, log_grid+pchip; no pending re-runs).
- **B7 evidence:** E_fusion +0.73 positive all folds (EIS latent adds value only anchored by TD); **AE-on-TD +0.43 < raw TD +0.85** → AE architecture adds no value on either modality.

## 3. Round 3 Work Plan (R3-C1 → R3-C9 + Advisor GitHub Response)

All tasks under **PAEV** (Plan with 4-Rule → Dom approves → Execute → Verify with gates → Ablation log → Commit). Division of labor: Capi writes/scripts/smoke-tests/verifies (CPU); Dom runs `--full` on RTX 3050; Capi delivers .md only — Dom converts PDF via Antigravity.

### Phase 1: Immediate (Week 1) — Protocol Fixes & Proxy Audit 🔴 HIGHEST PRIORITY

| Step | Task | Script / Input | Output | PAEV Gates |
|---|---|---|---|---|
| **1.1** | **Re-fit TD-BPNN on all 3 training batteries** after inner validation selects hyperparams. Retrain on `remaining` (3 batteries) before outer test. | Modify `steps14_16_td.py` (line 71: `train_b = remaining[1:]` → use all `remaining`) | `steps14_16_results_refit.csv` with per-fold + pooled R², RMSE (%SOH + Ah), MAPE | Leakage probe PASS; per-fold R² all positive (esp. B0006, B0018); pooled R² reported; MAPE added |
| **1.2** | **Add MAPE + pooled R² + RMSE (Ah)** to all results (advisor already doing; ensure our script outputs same) | Same as 1.1 | Updated metrics in CSV | Values match advisor's calculation |
| **1.3** | **Target-Proxy Audit (R3-C3 — Most Important Scientific Question)**. List all 8 TD features, label `safe`/`proxy`. Run 3 settings under nested LOBO × 3 seeds. | New script `td_proxy_audit.py` using `extract_time_features.py` → `time_domain_features.csv` | `proxy_audit.md` (feature table) + `td_proxy_free_results.csv` (3 settings) | Leakage probe PASS; Oracle (I×t) → R² ≈ 1 (sanity); TD-Proxy-Free R² reported per-fold + pooled |
| **1.4** | **Feature labeling** (from advisor GitHub response): | | | |
| | `dis_duration` (T_end − T_0) | ✅ **PROXY** — CC discharge: Capacity = I × t | | |
| | `dis_mean_V` (mean discharge voltage) | ❌ Safe | | |
| | `dis_mean_T` (mean discharge temp) | ❌ Safe | | |
| | `dis_V_slope` (linear V vs t slope) | ❌ Safe | | |
| | `cc_dur` (CC charge duration → 4.19V) | ❌ Safe* — charge protocol identical across batteries | | |
| | `cv_dur` (CV charge duration) | ❌ Safe* | | |
| | `cv_I_slope` (CV current decay slope) | ❌ Safe* | | |
| | `ch_mean_T` (mean charge temp) | ❌ Safe | | |

> *Charge features naturally aligned across batteries (R3-C5-1) — not proxies under constant-current protocol.

**3 TD settings for proxy audit:**
| Setting | Features | Purpose |
|---|---|---|
| **TD-All** | All 8 current features | Baseline comparison |
| **TD-Proxy-Free** | 7 safe features (exclude `dis_duration`) | Honest unseen-battery capability |
| **Oracle-proxy** | `dis_duration` only (I × t) | Should reach R² ≈ 1 — explains high published scores |

---

### Phase 2: Week 1–2 — Protocol-Gap Experiment (R3-C2) 🔴

| Step | Task | Script | Output |
|---|---|---|---|
| **2.1** | Implement 3 splits with identical features/model: (i) Random, (ii) Chronological within each battery, (iii) Nested LOBO | `protocol_gap_exp.py` (reuse `nested_lobo_harness.py`) | `protocol_gap_results.csv` |
| **2.2** | Run TD-All features × 3 seeds on all 3 splits | Dom `--full` | Expect: Random R² > 0.97; Chronological ~0.90; Nested LOBO ~0.85 |
| **2.3** | Document: "How much published accuracy comes from protocol alone" → thesis Ch. 4 section | Thesis draft | Figure + table for Ch. 4 |

---

### Phase 3: Week 2–3 — Proxy-Free Improvements (R3-C5) 🟡 (ordered by benefit/effort)

| Priority | Task | Detail | Script |
|---|---|---|---|
| **5.1** | **Charging-segment features** | CC-charge time in fixed V-windows (3.9–4.0V, 4.0–4.1V), CV time, IC peak voltage/height. Naturally aligned; partial-window by design (refs [9],[10]) | `extract_charge_features.py` |
| **5.2** | **Fixed voltage window for discharge** | 4.0 → 3.6 V (all batteries pass) instead of whole-cycle min V / total time | Modify `extract_time_features.py` |
| **5.3** | **Self-referenced normalization** | Divide each feature by battery's first-cycle value. No label needed at deploy; removes initial offsets (B0006 2.035 Ah vs ~1.86 Ah others) | Add to preprocessing pipeline |
| **5.4** | **Monotonic / physical prior** | Predict ΔSOH + accumulate (EWDC style) OR monotonicity penalty in BPNN loss | `bpnn_monotonic.py` |
| **5.5** | **Window-length curve** | RMSE vs window (5/10/20/30 min or ΔV 0.1/0.2/0.3 V) — key figure for partial-cycle contribution | `window_length_curve.py` |

---

### Phase 4: Week 3–4 — Wider Validation (R3-C6) 🟢

| Task | Detail |
|---|---|
| **6.1** | Add B0025–B0056 (similar conditions) → download NASA data, verify cycles |
| **6.2** | Learning curve: LOBO performance vs #training batteries (3 → 10+) |
| **6.3** | Cross-dataset: Freeze best proxy-free model → test on CALCE CS2 (EWDC [10] dataset) |
| **6.4** | Oxford dataset (if time allows) |

---

### Phase 5: Parallel — EIS/AE Role (R3-C7) & Documentation 🟢

| Task | Detail |
|---|---|
| **7.1** | Extract scalar EIS features: Re, Rct, \|Z\| range, arc height (NASA provided) |
| **7.2** | Fusion test: TD + scalar EIS vs TD-only (keep only if clearly beats TD) |
| **7.3** | **Move AE to ablation/negative-result section** — document AE-TD R² 0.43 vs TD 0.85; AE-EIS does not beat PCA |
| **7.4** | Update `advisor_directives.md` with Round 3 completion status (append-only) |
| **7.5** | Draft thesis chapters per mapping (Section 6 of audit): Ch. 1–5 + Appendix |

---

### Phase 6: Citation Verification (R3-C9) — Ongoing 📋

- Open each of 13 papers → confirm values, units, split protocol
- Convert all to %SOH, note protocol next to each value
- Check journal quartile (JCR/SJR) before citing
- Cite original papers, not audit summary
- Add missing Sci. Rep. 2025 paper when accessible

## 4. Advisor GitHub Response (2026-09-28) — Verified & Actionable

| Question | Advisor Verification | Action Taken |
|---|---|---|
| **1. TD Feature Definitions** | 8 features listed in `extract_time_features.py`. `dis_duration` confirmed as indirect capacity proxy. | Phase 1.3 proxy audit started |
| **2. Model Re-fitting Status** | ❌ NOT re-fitted. Inner val used `train_b = remaining[1:]` (2 batteries). | Phase 1.1 re-fit on all 3 batteries |
| **3. Number of TD Samples** | ✅ 636 cycles total (B0005:168, B0006:168, B0007:168, B0018:132). NOT restricted to EIS-aligned (~51%). | Confirmed — no action needed |
| **4. Current Metrics** | R²≈0.85, RMSE 3.59 %SOH = per-fold averages. Advisor calculating pooled R², MAPE, RMSE (Ah). | Phase 1.2 add to our script output |

**Advisor statement:** *"I fully agree with your suggested direction. I am now executing Plan A within this week: (1) re-fitting on all 3 training batteries, (2) adding pooled R² and MAPE, and (3) running the Protocol-Gap experiment."*

→ **B7 direction resolved** — proxy-free TD path approved. No need to wait for E-fusion/AE-on-TD/EIS-secondary decision.

---

## 5. Artifacts Map (updated — all in Thesis repo, pushed to `main`)

| Path | Content |
|---|---|
| `Autoencoder/nested_lobo/Progress_Report_Steps1-18.md` | Round 2 consolidated report (18-step table, 6 figures, GitHub links ×27) |
| `Autoencoder/nested_lobo/steps14_16_td.py` | Round 2 original — **NOT modified** (kept intact for reproducibility) |
| `Autoencoder/nested_lobo/extract_time_features.py` | Round 2 original — **NOT modified** (Phase 3 will add a separate script) |
| **`Autoencoder/round3_phase1/`** | **NEW (2026-10-03) — all Phase 1 code lives here. Untracked in git.** |
| ├ `r3common.py` | shared utils: imports Round 2 `nested_lobo_harness` (not copied) + device handling (`--device cpu\|cuda\|auto`, default cpu) |
| ├ `steps14_16_refit.py` | **1.1 + 1.2** — `pre_refit` vs `refit_on_3`, MAPE / RMSE (%SOH + Ah) / R², per-sample prediction dumps |
| ├ `td_proxy_audit.py` | **1.3** — TD-All vs TD-Proxy-Free vs Oracle-proxy × 4 folds × 3 seeds |
| ├ `phase1_aggregate.py` | **1.2** — pooled R² / RMSE / MAPE (4 folds concatenated), reported per device |
| ├ `probe_s14b.py` | leakage probe for the refit path — verified `max\|diff\| = 0.00e+00` (PASS) |
| └ `bench_device.py` | CPU vs CUDA timing — measured cpu 47.3 s vs cuda 67.1 s per fold-seed (→ run on CPU) |
| `protocol_gap_exp.py`, `extract_charge_features.py`, `bpnn_monotonic.py`, `window_length_curve.py` | **NOT CREATED YET** — belong to Phases 2–3, not started |
| `Autoencoder/nested_lobo/time_domain_features.csv` | 636 rows, 8 TD features, exact capacity alignment |
| `Autoencoder/nested_lobo/figures/` | 6 Round 2 figures + new Phase 1–3 figures |
| `Autoencoder/eis_verify/` | Steps 1–6: EIS verification scripts, reports, verified dataset |
| `NASA DataSet/1. BatteryAgingARC-FY08Q4/` | Verified source data (tracked in Git) |

---

## 6. Data Format Notes (needed when writing code)

- EIS interpolation grids: `linspace` / `logspace(0.1, 5000)` Hz, 39 measured points → 128 dense points
- Feature vector 256 = 128 Re(Z) + 128 -Im(Z)
- Labels: `[battery_id, cycle]` in `Interpolated_*.pt`; `[battery_id, cycle, capacity_Ah, soh_pct]` in `Mapped_*.pt`
- Battery ids: 1/2/3/4 = B0005/B0006/B0007/B0018 (use BATT dict — id ≠ NASA name)
- SOH: `Q / Q_ref × 100%`, `Q_ref` = mean of first 5 discharge cycles (%SOH)
- Ablation log: append one line per run to `USER.md` (`YYYY-MM-DD | exp_name | key_metric | 1-line insight`)

---

## 7. Environment Facts (this machine)

- Dom's Python (3.11.6 — scipy/numpy/pandas/matplotlib/torch 2.5.1+cu121/sklearn/reportlab/pypandoc): `C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe`
- ⚠️ **In cmd, `python` is NOT Dom's Python** — it resolves to `...\hermes\tools\python-3.14.7...\python.exe` (no torch/pandas) and the run dies on import. Use **`py`** (launcher → 3.11) or the full quoted path. `PY="..."` is bash syntax and fails in cmd with `[Errno 22] Invalid argument`. Verified 2026-10-03.
- Hermes's own venv lacks matplotlib — use Dom's python for everything
- No MiKTeX/LaTeX → no pandoc PDF via xelatex. PDF = Dom's Antigravity
- pandoc 3.9 via pypandoc-binary; `eis_verify/convert_report.py` does .md→.docx
- Git repo: `github.com/DomIncham/soh-thesis-ae-bpnn` (PRIVATE — advisor accepted invite). Root: `C:\Master Degree\Thesis\`
- Do NOT run `git add -A` without checking `git status` first
- Run commands from `nested_lobo/` in **cmd** (not PowerShell — PS redirects logs to UTF-16)

---

## 8. Lessons Added This Round (from real bugs)

| Bug | Rule |
|---|---|
| `rmse_` unpacked as local var shadowed the function (`UnboundLocalError`) | never name metric variables like the helper function; use `t_rmse` |
| `(bids == b for b in train_b)` returned generator not mask → silent crash | boolean masks only from `np.isin` |
| AE/BPNN weights not seeded before init → non-deterministic reruns | `torch.manual_seed(seed)` BEFORE model construction |
| `--full` flag never registered in argparse → Dom's commands crashed | always smoke-test the exact CLI line including flag parsing |
| pandas `tolerance` column read as string after "3m" mixed in | compare with `.astype(str)` |
| Battery id 1 ≠ NASA name B0005 | always use the BATT mapping dict |

---

## 9. Open Items / Status

| Item | Status | Owner |
|---|---|---|
| **Phase 1.1–1.4** (Re-fit + Proxy Audit) | **CODE DONE + smoke PASS** (cpu & cuda) in `Autoencoder/round3_phase1/` — awaiting Dom's `--full`; device = cpu (default; measured 47.3 s vs 67.1 s cuda per fold-seed) | Dom |
| **Phase 2** (Protocol-Gap Experiment) | After Phase 1 | Dom |
| **Phase 3** (Proxy-Free Improvements) | After Phase 2 | Dom |
| **Phase 4** (Wider Validation) | After Phase 3 | Dom |
| **Phase 5** (EIS/AE Role + Docs) | Parallel | Capi + Dom |
| **Phase 6** (Citation Verification) | Ongoing | Dom |
| Per-point EIS frequency | open limitation; only fixable by asking dataset authors | advisor decision |
| Transfer Learning (Part K) | still gated — only after root cause accepted + Phase 1–3 done | advisor |

---

## 10. PAEV Plan for Phase 1 (Steps 1.1–1.4) — READY FOR APPROVAL

### Plan (4-Rule Justification)

| Rule | Content |
|---|---|
| **1. Options considered** | (a) Re-fit on 3 batteries (advisor directive) — **selected**. (b) 3-fold inner LOBO — alternative, more compute. (c) Keep 2-battery training — rejected (advisor flagged). |
| **2. Suitability** | Re-fit uses all available training data → better generalization for unseen battery (especially B0006). Matches standard nested CV practice. |
| **3. Quantitative evidence** | Current: TD-BPNN R² 0.85 (2-battery train). Expected: +0.02–0.05 R² on B0006 fold (advisor: "should help B0006 fold most"). Will measure per-fold + pooled. |
| **4. Side-effect check** | No data leakage (re-fit after inner validation, before outer test). No new hyperparameters. Compute: +1 training run per fold (4 folds × 3 seeds = 12 runs) — negligible on GPU. |

### Steps

1. **Modify `steps14_16_td.py`**: After inner validation selects best hyperparams → retrain on `remaining` (all 3 batteries) → evaluate on outer test battery
2. **Add metrics**: MAPE, pooled R², RMSE (Ah) alongside per-fold
3. **Create `td_proxy_audit.py`**:
   - Load `time_domain_features.csv`
   - Label 8 features safe/proxy (table above)
   - Run 3 settings (TD-All, TD-Proxy-Free, Oracle I×t) under nested LOBO × 3 seeds
   - Output per-fold + pooled metrics
4. **Run both scripts** (`--full` on GPU)
5. **Verify**: Leakage probes PASS; per-battery metrics + mean±std; results match expectations

### Risk
- **Low**: No new data, no architecture change, standard CV practice
- **Compute**: ~12 retrains + 36 proxy audit runs = ~48 training runs (each <2 min on RTX 3050) → ~1.5 hours total

### Verification Gates
- `probe_s14.py` (leakage probe) PASS
- Per-fold R² all positive (especially B0018, B0006)
- Pooled R² reported
- MAPE added
- Oracle (I×t) → R² ≈ 1 (sanity check)

---

## 11. Next Session Instructions

1. `/new` → load skill `soh-research` → read `advisor_directives.md` + `end_to_end_research_workflow_v2.md` + THIS file — **use `read_file` with `offset`/`limit`; never use `skill_view` for thesis files (triggers compression+cache loop)**
2. **Execute Phase 1 PAEV** (Dom approves → Dom runs `--full` → Capi verifies → Dom commits & pushes to GitHub)
3. Push to `main` → advisor sees progress at `github.com/DomIncham/soh-thesis-ae-bpnn`
4. Update this file with Phase 1 results → proceed to Phase 2
5. Any new experiment: PAEV (Plan with 4-Rule → Dom approves → execute → Verify with gates → ablation log → commit)

---

## 12. Budget Note

This session: normal cost. Next phase: ~$1-2 per P2 debate + P3 coding cycle if context pruned. **Start next session with `/new` + this file.**

---

*Last updated: 2026-10-03 — Phase 1 code written and smoke-tested in `Autoencoder/round3_phase1/` (Artifacts Map corrected: the previously listed nested_lobo "NEW/UPDATED" Phase 1–3 paths were never created). Awaiting Dom's `--full` run.*