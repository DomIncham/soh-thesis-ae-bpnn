# ACTIVE EXPERIMENT — Round 2 Complete · Awaiting Advisor B7 Decision

> **READ THIS FIRST (new session):** load skill `soh-research` → read `advisor_directives.md` (SSOT) → read `end_to_end_research_workflow_v2.md` → then this file. Start a fresh session (`/new`) — do NOT continue the old 500k-token session (cost >$6).
>
> **Updated:** 2026-09-25 · **Status:** 18/18 steps executed + all pending items closed. Report sent to advisor. **Blocked on:** advisor's B7 direction decision.
> **Advisor:** Y.F. Luo (YF.Luo@mail.ntust.edu.tw) — GitHub collaborator invitation sent (private repo; links in report work only after he accepts).

---

## 1. Where we are (one paragraph)

Round 2 executed end-to-end under the corrected protocol (nested 4-fold LOBO, tolerance 1, %SOH, fold-train-only scaling/standardization, EarlyStopping, seeds 42/7/123). The old Figure 10 collapse was diagnosed and removed. Measured verdict: **time-domain features dominate EIS cross-battery** (B6 pattern confirmed verbatim). The consolidated report (`Autoencoder/nested_lobo/Progress_Report_Steps1-18.md`) is humanized, link-annotated to GitHub, and was sent to the advisor as PDF (Dom's Antigravity does PDF conversion; Capi delivers .md only).

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

## 3. Artifacts map (all in Thesis repo, pushed to `main`)

| Path | Content |
|---|---|
| `Autoencoder/nested_lobo/Progress_Report_Steps1-18.md` | **The advisor-facing consolidated report** (18-step table, 6 figures, GitHub links ×27, §6 Repository) — humanized (0 em dash, 0 boldface) |
| `Autoencoder/nested_lobo/Steps_7_8_Nested_LOBO.md` | Steps 7–8 protocol + tolerance results |
| `Steps_9_10_Baselines.md` / `Steps_12_Fig10_Collapse.md` / `Steps_14_16_TimeDomain.md` / `Steps_F3_I3_B7_Ablations.md` / `Part_J_BMS_Practicality.md` | Per-topic advisor reports |
| `nested_lobo/nested_lobo_harness.py` | Core harness: nested LOBO, `--smoke/--full/--probe/--matched` |
| `nested_lobo/make_final_figures.py` | Regenerates `figures/R1, R2` from the results CSVs |
| `nested_lobo/md2pdf_report.py` | Styled .md → PDF renderer (reportlab) — kept as fallback; Dom uses Antigravity |
| `nested_lobo/steps9_10_baselines.py`, `steps14_16_td.py`, `ablations_f3_i3.py`, `b7_fusion_aeontd.py` | Pipeline scripts (smoke tested; `--full` runs on Dom's GPU) |
| `nested_lobo/extract_time_features.py` → `time_domain_features.csv` | 636 rows, 8 TD features, exact capacity alignment |
| `nested_lobo/Mapped_EIS_SOH_tol{1,2,3}.pt` | Mapped datasets with %SOH (Q_ref = mean of first 5 discharge cycles) |
| `nested_lobo/gate_optionB.py`, `gate_s9.py`, `gate_s14.py`, `probe_s9.py`, `probe_s14.py` | Validity gates + leakage probes (all PASS) |
| `nested_lobo/step17_checkpoint.py` + `checkpoints/TD_bpnn_B0005_seed42_best.pth` | ModelCheckpoint verified (reload MATCH) |
| `nested_lobo/figures/` | 6 figures embedded in the consolidated report |
| `Autoencoder/eis_verify/` | Steps 1–6: verification scripts, `EIS_Raw_Verification.md`, `Interpolation_Reeval.md`, `EIS_Verified_Dataset.csv` |
| `NASA DataSet/1. BatteryAgingARC-FY08Q4/` | Verified source data (tracked in Git) |

Data format notes (needed when writing code): EIS interpolation grids = `linspace` / `logspace(0.1, 5000)` Hz, 39 measured points → 128 dense points; feature vector 256 = 128 Re(Z) + 128 -Im(Z); labels = `[battery_id, cycle]` in `Interpolated_*.pt`, `[battery_id, cycle, capacity_Ah, soh_pct]` in `Mapped_*.pt`; battery ids 1/2/3/4 = B0005/B0006/B0007/B0018 (use the BATT dict — id ≠ NASA name); full ablation log lines live in `USER.md` (append one line per run).

## 4. Open items / waiting

| Item | Status | Owner |
|---|---|---|
| **B7 direction** (E-fusion vs AE-on-TD vs EIS-secondary) | **awaiting advisor decision** — evidence ready in §2/§3 of consolidated report | Advisor → Dom |
| Per-point EIS frequency | open limitation; only fixable by asking dataset authors (Saha/Goebel, NASA ARC) | advisor decision |
| Transfer Learning (Part K) | still gated — only after root cause accepted + direction chosen | advisor |
| Report status | PDF sent via LINE (message drafted in session 2026-09-25); advisor must accept GitHub invite before links work | Dom |

LINE message sent to advisor (2026-09-25, B1-B2): "Hi Professor — Here's the Round 2 progress report (PDF attached). It covers all 18 steps we discussed. I've also invited you to the GitHub repo (YF.Luo@mail.ntust.edu.tw). The repo is private, so you'll need to accept the invitation email first — then all the file links inside the report will work. The repo contains all the scripts, data, and step-by-step reports that back up the PDF. Let me know if you have any questions or want to discuss the B7 direction (fusion vs AE-on-TD vs EIS secondary)."

## 5. Rules that produced these results (do not skip)

1. **Hard rules (E2E v3):** exit 0 ≠ correct; standardize SOH target before BPNN; use `np.isin` never `list == str` masks; reasoning ON for coding models; repair loop; leakage probe per batch; per-battery metrics + mean ± std.
2. **Protocol constants:** nested 4-fold LOBO; inner val = first remaining battery; tolerance 1; Q_ref = first-5-cycle mean; seeds 42/7/123; EarlyStopping patience 30; structural leakage assert every fold + perturbation probe per batch.
3. **Decision rules are declared BEFORE running** (pre-registered), never after seeing results.
4. **Division of labor:** Capi writes/scripts/smoke-tests/verifies (CPU); Dom runs `--full` on RTX 3050; Capi does .md only — **Dom converts PDF via Antigravity** (do not convert yourself).
5. **Language:** advisor reports = A2-B1 English, short SVO, numbers first, hedged ("results indicate", "consistent with", "may be associated with"); humanized (0 em dash, 0 boldface; pre-send grep: prove/confirm/guarantee/successfully = 0). See skill `humanizer` → "Academic/technical reports for an advisor (Dom, NTUST)" section.
6. **Consolidated report structure:** 18-step status table → figures → ablations → B7 options → declared limitations → Artifacts (no ablation-log sections in advisor files — those live in USER.md).
7. **Ablation log:** append one line per run to `USER.md` (fixed format `YYYY-MM-DD | exp_name | key_metric | 1-line insight`) — never in advisor-facing files.

## 6. Environment facts (this machine)

- Dom's Python (has scipy/numpy/pandas/matplotlib/torch/sklearn/reportlab/pypandoc): `C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe`
- Hermes's own venv python lacks matplotlib — use Dom's python for everything.
- **No MiKTeX/LaTeX** on this machine → no pandoc PDF via xelatex. PDF = Dom's Antigravity.
- pandoc 3.9 available via pypandoc-binary; `eis_verify/convert_report.py` does .md→.docx.
- Git repo: `github.com/DomIncham/soh-thesis-ae-bpnn` (PRIVATE — advisor needs to accept invite). Root: `C:\Master Degree\Thesis\`.
- **Do NOT run `git add -A`** without checking `git status` first (once pulled Dom's local experiment scripts into the repo; removed since).
- Run commands from `nested_lobo/` in **cmd** (not PowerShell — PS redirects logs to UTF-16).

## 7. Lessons added this round (from real bugs)

| Bug | Rule |
|---|---|
| `rmse_` unpacked as local var shadowed the function of the same name (`UnboundLocalError`) | never name metric variables like the helper function; use `t_rmse` |
| `(bids == b for b in train_b)` returned a generator not a mask → silent crash/empty | Hard rule 3 extension: boolean masks only from `np.isin` |
| AE/BPNN weights not seeded before init → non-deterministic reruns, probe false-positive | `torch.manual_seed(seed)` BEFORE model construction, not only inside the train loop |
| `--full` flag never registered in argparse → Dom's 3 commands crashed instantly | always smoke-test the exact CLI line you hand to Dom, including flag parsing |
| pandas `tolerance` column read as string after "3m" mixed in | compare with `.astype(str)` |
| Battery id 1 ≠ NASA name B0005 | always use the BATT mapping dict |

## 8. Budget note

This session consumed >$6 (500k context, one session for debate + code + runs). **Start the next session with `/new` + this file.** Cost projection for next phase: normal (~$1-2 per P2 debate + P3 coding cycle) if context is pruned.

## 9. Next-session instructions

1. `/new` → load skill `soh-research` → read `advisor_directives.md` + `end_to_end_research_workflow_v2.md` + THIS file.
2. Ask Dom: "What did the advisor decide on B7?"
3. Branch by answer:
   - **E-fusion** → alignment is already per-TD-cycle backward-time (latest EIS cycle ≤ that discharge); improvements: learned fusion weights, per-cycle feature-level fusion (not just 17-dim latent), more TD features (rest-period recovery, ICA if feasible).
   - **AE-on-TD** → redesign AE for 8-dim TD input (bottleneck 4 tested; try variational/denoising; compare against raw-TD honestly — evidence says AE adds nothing, so this needs a strong justification for the thesis).
   - **EIS secondary** → write the EIS limitation chapter; TD becomes the main pipeline.
4. Any new experiment: PAEV (Plan with 4-Rule → Dom approves → execute → Verify with gates → ablation log → commit).
5. Update `advisor_directives.md` with Round 3 comments when the advisor responds (append-only).