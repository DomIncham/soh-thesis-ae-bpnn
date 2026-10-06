# Round 4 Report to Advisor — R3-C1…C9 Complete (2026-10-06)

> Student: Padipat Aincham (M11452803) · Advisor: Y.F. Luo · For: Round 4 progress report
> All numbers below were re-verified 2026-10-06: the full check suite passes **210/210 checks**
> (plus 26/26 data-provenance checks), and every headline number was re-read from the result CSVs
> before inclusion. Sources are listed per section.

## 0. One-paragraph summary

All nine items (C1–C9) from the Literature Gap Audit are addressed. The strict protocol is now
quantified as a contribution: on identical features and model, the split protocol alone moves
R² from −1.03 to +0.99, and removing capacity proxies moves it from 0.93 to 0.49 (recovering to
0.81 with two safe charge-segment features). The AE is demoted to a documented negative result.
Cross-dataset transfer fails (domain shift), with a within-domain control proving the cause.
All 13 audit papers were verified from their full PDFs; the two anchor numbers of the audit are
confirmed verbatim. One question remains for the advisor: thesis title phrasing.

## 1. C1 — Evaluation protocol fixes ✅

- `refit_on_3`: after inner selection, the final model is re-fitted on all three training
  batteries. Mean per-fold R² (TD-All): **0.848 → 0.923**; median 0.789 → 0.950.
  (Source: [`inner_loop_lobo3_results.csv`](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/inner_loop_lobo3_results.csv), re-aggregated 2026-10-06.)
- Reporting standard applied everywhere: per-fold mean R² + pooled R², MAE/RMSE in %SOH,
  MAPE, RMSE in Ah. (Source: [`phase1_pooled_metrics.csv`](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/phase1_pooled_metrics.csv) — pooled TD-All refit 0.936,
  MAE 2.20%SOH, MAPE 2.71%.)

## 2. C2 — Protocol-gap experiment ✅ (becomes Ch.4 §4.2)

Same features, same model, only the split changes (verified: [`protocol_gap_verify.py`](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/protocol_gap_verify.py) 23/23):

| Split | Oracle-proxy | TD-All | TD-Proxy-Free |
|---|---|---|---|
| Random, same battery | 0.992 | 0.979 | 0.978 |
| Random, pooled | 0.815 | 0.989 | 0.978 |
| Nested LOBO, unseen battery | 0.663 | 0.927 | 0.854 |
| Chronological, same battery | 0.179 | −1.028 | −5.234 |

- The R3-C2 prediction (random split > 0.97) is confirmed: 0.979.
- Pooling inflates R²: chronological is −1.028 per fold but +0.850 pooled — audit factor 5
  demonstrated on a fixed representation.
- Note: LOBO numbers quoted from the phase-1 audit run (refit_on_3, 3 seeds). The phase-2
  protocol-gap experiment (pre-refit stage) has its own LOBO numbers (0.634/0.891/0.680) —
  different row set, quoted separately in Ch.4 with an explicit note.

## 3. C3 — Feature/proxy audit ✅

- `dis_duration` is a direct proxy (CC discharge: capacity = I × t). Removed → Proxy-Free.
- `dis_mean_V` is collinear with it (within-battery r = 0.941) and alone explains 94.8 % of
  within-battery capacity variance. Also removed → Clean-6.
- Full classification with code paths and formulas: [`r3c3_feature_classification.md`](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/r3c3_feature_classification.md) +
  [`r3c3_feature_classes.csv`](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/r3c3_feature_classes.csv) (verified: [`phase3_feature_audit.py`](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/phase3_feature_audit.py) 50/50).

## 4. C5 — Proxy-free improvements ✅ (Ch.4 §4.3–4.4)

| Item | Result | Verdict |
|---|---|---|
| 5.1 `ic_peak_V` (charge segment) | Clean-7 0.772 vs Clean-6 0.490 (15/20 folds) | Supported |
| 5.2 Fixed discharge window 4.0–3.6 V | `win_dur` R²(cap) 0.995 > `dis_duration` 0.972 | Not established — window features are proxies |
| 5.3 Self-referenced normalisation | 0.810 → 0.075; B0018 reference 6× smaller → scale mismatch | Rejected |
| 5.4 ΔSOH accumulation | 0.810 → −4.785; corr(cycle pos., error) up to +0.993 | Rejected |
| 5.5 Window length 5–30 min | proxy-free flat 0.842–0.843; proxy-laden 0.874 → 0.914 | No partial-window penalty |

- Defensible headline: **Clean-8 = 0.810** (Clean-6 + `ic_peak_V` + `t_40_41`), nested LOBO,
  5 seeds, paired claim 0.664 → 0.810 on identical rows (verify note: `t_40_41` alone is
  within-noise, 11/20; `ic_peak_V` is the supported addition — stated honestly in Ch.4).
- TD-Clean-6 = 0.490 is the strict proxy-free number; 0.845/0.854 are Proxy-Free arms that
  contain a proxy-equivalent feature and are never quoted as proxy-free.

## 5. C6 — Wider validation ✅

- **6.1** Learning curve, NASA B0025–B0056 (420 runs + integrity checks): adding heterogeneous
  cells does not help — pulsed-4A cells are catastrophic (B0027 R² −132.8 at k = 13; Clean-8
  mean −12.5, median +0.32), and widening the pool hurts same-condition tests (room-2A
  protocol reproduction 0.933 at k = 3 → 0.63–0.85 at k = 13). Within-condition curves stay
  positive (medians −1.25 → +0.15 → +0.32 for k = 3 → 7 → 13). Claim stated per condition.
- **6.3** NASA → CALCE CS2, four arms: frozen median R² −37 (does not transfer); 1-cell scratch
  ≈ −68; 1-cell warm-adapt ≈ −31; **within-CS2 control 0.39–0.68 on 6/8 cells** — the failure is
  domain shift (per-cell label offset, charge 0.5C vs 0.75C), not data or feature quality.

## 6. C7 — AE demoted to a documented negative result ✅ (Ch.4 §4.6)

| Evidence | Numbers |
|---|---|
| AE-on-TD vs raw TD | 0.43 vs 0.85 |
| AE on EIS vs PCA on EIS | +0.08 vs +0.61 |
| AE reconstruction | the interpolation grid, not the measurement (+0.1 mΩ offset) |
| E_fusion (EIS latent + TD) | 0.73 < TD-only 0.85 |

Claim (approved phrasing): "the autoencoder bottleneck adds no measurable value on either
modality; its latent space reconstructs the interpolation grid rather than the impedance
measurement; PCA is the stronger EIS reducer. The AE is reported as a negative result and the
pipeline proceeds without it." Recorded in [`advisor_directives.md`](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/advisor_directives.md) (R3-C7 outcome, commit `4f3feec`).

## 7. C9 — Citation verification: all 13 studies ✅

Full table: [`r3c9_citation_verification.md`](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/r3c9_citation_verification.md). Verified from full PDFs (all 13 downloaded):

- [11] Sardar: random-split ET R² **0.9788** → strict battery-wise **0.7855** — confirmed verbatim.
- [9] Chen: B0006 LOCO R² **0.2464 → 0.5286** — confirmed (audit said 0.25 → 0.53). Their protocol:
  3 cells, SOH = Q(c)/Q(1), **cycle index as an explicit input**, and they self-declare the
  conformal intervals "not fully calibrated under severe domain shift". They also hit the B0006 wall.
- [10] EWDC 0.975: **within-dataset LOBO** (3-train/1-held-out, same cells as ours: B0005/06/07/18
  + CS2-35..38), avg RMSE 1.21 %, MAE 0.65 %, 10 runs. Feature set = 17 charge-segment HIs
  **including cycle index + cumulative charged quantity**, and the recursive predictor is anchored
  at ŷ₁ = 1. Compare against our **TD-All 0.927** (same protocol), not Clean-8.
- [3] uses Q(k−1) explicitly; [4] uses previous-cycle capacity + cycle number. Every strong
  unseen-battery claim in the list is proxy-laden — supports our Clean-8 framing.
- [7] is the only cross-battery R² ≈ 0.98 result: Oxford, 1-train/rest-test, per-cell capacity
  ratio — smallest, cleanest scope; annotated in the Ch.2 table.
- B0018 fold of [10]: RMSE 1.91 % (their worst) vs 1.21 % average — consistent with our B0018 history.

## 7b. Evidence on GitHub (clickable)

All report, summary, verification and result files referenced above live in the private
repository [`DomIncham/soh-thesis-ae-bpnn`](https://github.com/DomIncham/soh-thesis-ae-bpnn):

| What | File |
|---|---|
| Phase 1 — protocol fixes + proxy audit findings | [`phase1_oracle_findings.md`](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/phase1_oracle_findings.md) |
| Phase 2 — two-axis experiment summary | [`phase2_summary_two_axes.md`](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/phase2_summary_two_axes.md) |
| Phase 3 — charge features (5.1) | [`phase3_charge_features_summary.md`](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/phase3_charge_features_summary.md) |
| Phase 3 — self-reference rejection (5.3) | [`phase3_selfref_summary.md`](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/phase3_selfref_summary.md) |
| Phase 3 — window features (5.2/5.5) | [`phase3_window_summary.md`](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/phase3_window_summary.md) |
| Phase 3 — ΔSOH rejection (5.4) | [`phase3_dsoh_summary.md`](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/phase3_dsoh_summary.md) |
| Phase 3 — window length (5.5) | [`phase3_windowlength_summary.md`](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/phase3_windowlength_summary.md) |
| Phase 4 — learning curve (6.1) | [`phase4_learning_curve_summary.md`](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/phase4_learning_curve_summary.md) |
| Phase 4 — CALCE CS2 transfer (6.3) | [`phase4_cs2_summary.md`](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/phase4_cs2_summary.md) |
| Phase 5 — AE negative result evidence (Round 2) | [`Progress_Report_Steps1-18.md`](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/nested_lobo/Progress_Report_Steps1-18.md), [`Steps_F3_I3_B7_Ablations.md`](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/nested_lobo/Steps_F3_I3_B7_Ablations.md) |
| R3-C9 — 13-paper verification table | [`r3c9_citation_verification.md`](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/r3c9_citation_verification.md) |
| Thesis drafts (v0.1) | [Ch.1](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/thesis_ch1_introduction_draft.md) · [Ch.3](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/thesis_ch3_methodology_draft.md) · [Ch.4](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/thesis_ch4_protocol_draft.md) · [Ch.5](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/thesis_ch5_discussion_draft.md) · [Appendix](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/thesis_appendix_negative_results.md) |
| State card / experiment log | [`PROJECT_STATE.md`](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/PROJECT_STATE.md) |

## 8. Verification status (re-run 2026-10-06)

| Suite | Checks |
|---|---|
| phase1_verify | 61/61 ✅ |
| protocol_gap_verify | 23/23 ✅ |
| td_clean_verify | 7/7 ✅ |
| phase3_charge_verify | 8/8 ✅ |
| phase3_selfref_verify | 9/9 ✅ |
| phase3_window_verify | 7/7 ✅ |
| phase3_dsoh_verify | 7/7 ✅ |
| phase3_windowlength_verify | 12/12 ✅ |
| phase3_feature_audit | 50/50 ✅ |
| data_provenance_audit | 26/26 ✅ |

Leakage probes: max|diff| = 0.00e+00 on every protocol and clean feature set.
**Corrections found during this re-verification:** (a) Ch.4 draft quoted Oracle LOBO as 0.671 —
the correct phase-1 value is **0.663** (fixed); (b) 0.845 vs 0.854 are different row sets —
an explicit row-set note was added to Ch.4 to prevent a cross-row-set comparison.

## 9. Draft status

- **Ch.4 (Results) draft v0.1**: [`thesis_ch4_protocol_draft.md`](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/thesis_ch4_protocol_draft.md) — setup, protocol axis, proxy
  axis, 5.1–5.5 verdicts, wider validation, AE negative result, headline table, limitations.
- Ch.5 (Discussion), Ch.3 (Methodology), Ch.1 (Introduction), Appendix (negative results):
  drafting in progress.
- Ch.2 (Literature Review): **unblocked by C9** — comparison table can be built from
  `r3c9_citation_verification.md` with per-row unit and protocol annotations.

## 10. Question for the advisor (one item)

**Thesis title:** given that a partial window is not proxy-free by construction (window means are
proxies at every length), we propose **"proxy-audited, partial-window, unseen-battery SOH
estimation"** — precision over brevity. Please confirm or suggest phrasing.
