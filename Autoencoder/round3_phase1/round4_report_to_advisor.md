# Round 4 Report - R3-C1 to C9

Student: Padipat Aincham (M11452803) | Advisor: Y.F. Luo

All numbers in this report were re-checked on 2026-10-06. The full check suite passes
210/210 checks, plus 26/26 data-provenance checks. Each headline number was re-read from the
result CSVs before I put it here. The "data-provenance" suite name refers to the check script
that re-derives the numbers from the raw NASA files. Sources are listed per section, with links
to the repository.

## 0. Summary

All nine items (C1-C9) from the Literature Gap Audit are addressed. On identical features and
model, the split protocol alone moves R2 from -1.03 to +0.99. Removing capacity proxies moves
it from 0.93 to 0.49; adding back two safe charge-segment features recovers it to 0.81. The AE
did not add value on either modality, so it is reported as a negative result and the pipeline
proceeds without it. Cross-dataset transfer to CALCE CS2 fails; a within-CS2 control shows the
cause is domain shift, not data or feature quality. All 13 audit papers were verified from their
full PDFs, and the two anchor numbers of the audit match the originals. One question remains:
the thesis title phrasing (Section 10).

## 1. C1 - Evaluation protocol fixes

- `refit_on_3`: after inner selection, the final model is re-fitted on all three training
  batteries. Mean per-fold R2 (TD-All): 0.848 -> 0.923; median 0.789 -> 0.950.
  (Source: [`inner_loop_lobo3_results.csv`](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/inner_loop_lobo3_results.csv), re-aggregated 2026-10-06.)
- Reporting standard now applied in all tables: per-fold mean R2 and pooled R2, MAE and RMSE
  in %SOH, MAPE, and RMSE in Ah. (Source:
  [`phase1_pooled_metrics.csv`](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/phase1_pooled_metrics.csv) -
  pooled TD-All refit 0.936, MAE 2.20 %SOH, MAPE 2.71 %.)

## 2. C2 - Protocol-gap experiment (becomes Ch.4 section 4.2)

Same features, same model, only the split changes (verified:
[`protocol_gap_verify.py`](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/protocol_gap_verify.py), 23/23):

| Split | Oracle-proxy | TD-All | TD-Proxy-Free |
|---|---|---|---|
| Random, same battery | 0.992 | 0.979 | 0.978 |
| Random, pooled | 0.815 | 0.989 | 0.978 |
| Nested LOBO, unseen battery | 0.663 | 0.927 | 0.854 |
| Chronological, same battery | 0.179 | -1.028 | -5.234 |

- The R3-C2 prediction (random split above 0.97) is met: 0.979.
- Pooling inflates R2. The chronological split scores -1.028 per fold but +0.850 pooled. This
  is audit factor 5, shown on a fixed representation.
- The LOBO numbers above come from the phase-1 audit run (refit_on_3, 3 seeds). The phase-2
  protocol-gap experiment (pre-refit stage) produced its own LOBO numbers (0.634/0.891/0.680)
  on a different row set; Ch.4 quotes them separately with a note, and the two are not compared
  to each other.

## 3. C3 - Feature and proxy audit

- `dis_duration` is a direct proxy. In CC discharge, capacity = I x t, so the feature carries
  the label. It was removed to form the Proxy-Free set.
- `dis_mean_V` is collinear with it (within-battery r = 0.941) and alone explains 94.8 % of
  within-battery capacity variance. It was also removed, giving Clean-6.
- The full classification, with code paths and formulas, is in
  [`r3c3_feature_classification.md`](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/r3c3_feature_classification.md)
  and [`r3c3_feature_classes.csv`](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/r3c3_feature_classes.csv)
  (verified by [`phase3_feature_audit.py`](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/phase3_feature_audit.py), 50/50).

## 4. C5 - Proxy-free improvements (Ch.4 sections 4.3-4.4)

| Item | Result | Verdict |
|---|---|---|
| 5.1 `ic_peak_V` (charge segment) | Clean-7 0.772 vs Clean-6 0.490 (15/20 folds) | Supported |
| 5.2 Fixed discharge window 4.0-3.6 V | `win_dur` R2(cap) 0.995 vs `dis_duration` 0.972 | Not established; window features are proxies |
| 5.3 Self-referenced normalisation | 0.810 -> 0.075; the B0018 reference is 6x smaller, which introduces a scale mismatch | Rejected |
| 5.4 dSOH accumulation | 0.810 -> -4.785; correlation of error with cycle position up to +0.993 | Rejected |
| 5.5 Window length 5-30 min | proxy-free flat at 0.842-0.843; proxy-laden rises 0.874 -> 0.914 | No partial-window penalty |

- The defensible headline is Clean-8 = 0.810 (Clean-6 + `ic_peak_V` + `t_40_41`), nested LOBO,
  5 seeds. The paired claim on identical rows is 0.664 -> 0.810. The verify run notes that
  `t_40_41` alone is within noise (11/20 folds), so `ic_peak_V` is the supported addition; Ch.4
  states this.
- Clean-6 = 0.490 is the strict proxy-free number. The 0.845/0.854 Proxy-Free arms contain a
  proxy-equivalent feature and are not quoted as proxy-free anywhere.

## 5. C6 - Wider validation

- 6.1 Learning curve, NASA B0025-B0056 (420 runs plus integrity checks): adding heterogeneous
  cells does not help. The pulsed-4A cells fail under every setting (B0027 R2 -132.8 at k = 13; Clean-8 mean
  -12.5, median +0.32), and widening the pool hurts same-condition tests (the room-2A protocol
  reproduces at 0.933 with k = 3 and falls to 0.63-0.85 with k = 13). Within-condition curves
  stay positive (medians -1.25 -> +0.15 -> +0.32 for k = 3, 7, 13). The claim is stated per
  condition. (Source:
  [`phase4_learning_curve_summary.md`](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/phase4_learning_curve_summary.md))
- 6.3 NASA -> CALCE CS2, four arms: frozen median R2 -37 (does not transfer); 1-cell scratch
  about -68; 1-cell warm-adapt about -31; within-CS2 control 0.39-0.68 on 6/8 cells. The
  failure is domain shift: a per-cell label offset (CS2 SOH spans 88-114 % vs NASA 72-108 %)
  and a charge rate of 0.5 C vs 0.75 C, which doubles the charge-side feature scale. The data
  and feature quality are sound; the control shows it. (Source:
  [`phase4_cs2_summary.md`](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/phase4_cs2_summary.md))

## 6. C7 - AE demoted to a documented negative result (Ch.4 section 4.6)

| Evidence | Numbers |
|---|---|
| AE-on-TD vs raw TD | 0.43 vs 0.85 |
| AE on EIS vs PCA on EIS (gain over raw) | +0.08 vs +0.61 |
| AE reconstruction | the interpolation grid, not the measurement (+0.1 mOhm offset) |
| E_fusion (EIS latent anchored by TD) | 0.73, below TD-only 0.85 |

The E_fusion pipeline is positive on all four folds, including B0018 (+0.67), so the precise
statement is: the EIS latent adds no value on top of a full TD feature set, and AE features are
worse than raw features on both modalities. The AE as a representation is the negative result;
a small gain on weak-feature regimes remains open.

Claim used in the thesis: "the autoencoder bottleneck adds no measurable value on either
modality; its latent space reconstructs the interpolation grid rather than the impedance
measurement; PCA is the stronger EIS reducer. The AE is reported as a negative result and the
pipeline proceeds without it." Recorded in
[`advisor_directives.md`](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/advisor_directives.md)
(R3-C7 outcome).

## 7. C9 - Citation verification, all 13 studies

Full table:
[`r3c9_citation_verification.md`](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/r3c9_citation_verification.md).
All 13 papers were downloaded and read from the full PDFs.

- [11] Sardar: random-split ET R2 0.9788 -> battery-wise 0.7855. Matches the audit.
- [9] Chen: B0006 LOCO R2 0.2464 -> 0.5286. Matches the audit (0.25 -> 0.53). Their protocol uses
  3 cells, SOH = Q(c)/Q(1), and the cycle index as an input; they note that their conformal
  intervals are not fully calibrated under severe domain shift. They also fail on B0006.
- [10] EWDC 0.975: a within-dataset LOBO (3 train, 1 held out; the same cells as ours:
  B0005/06/07/18 and CS2-35..38), average RMSE 1.21 %, MAE 0.65 %, 10 runs. The feature set is
  17 charge-segment HIs including the cycle index and cumulative charged quantity, and the
  recursive predictor is anchored at yhat_1 = 1. The comparable number on our side is TD-All 0.927
  (same protocol), not Clean-8.
- [3] uses Q(k-1) as an input; [4] uses previous-cycle capacity and cycle number. Every strong
  unseen-battery claim in the list carries a proxy, which supports the Clean-8 framing.
- [7] is the only cross-battery result near R2 0.98: Oxford, 1-train/rest-test, per-cell
  capacity ratio. It is the smallest and cleanest scope in the list; the Ch.2 table annotates it.
- The B0018 fold of [10] has RMSE 1.91 % against their 1.21 % average, consistent with the
  B0018 behaviour in our own runs.

## 7b. Evidence on GitHub

All report, summary, verification and result files are in the private repository
[`DomIncham/soh-thesis-ae-bpnn`](https://github.com/DomIncham/soh-thesis-ae-bpnn):

| What | File |
|---|---|
| Phase 1 - protocol fixes and proxy audit findings | [`phase1_oracle_findings.md`](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/phase1_oracle_findings.md) |
| Phase 2 - two-axis experiment summary | [`phase2_summary_two_axes.md`](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/phase2_summary_two_axes.md) |
| Phase 3 - charge features (5.1) | [`phase3_charge_features_summary.md`](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/phase3_charge_features_summary.md) |
| Phase 3 - self-reference rejection (5.3) | [`phase3_selfref_summary.md`](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/phase3_selfref_summary.md) |
| Phase 3 - window features (5.2/5.5) | [`phase3_window_summary.md`](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/phase3_window_summary.md) |
| Phase 3 - dSOH rejection (5.4) | [`phase3_dsoh_summary.md`](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/phase3_dsoh_summary.md) |
| Phase 3 - window length (5.5) | [`phase3_windowlength_summary.md`](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/phase3_windowlength_summary.md) |
| Phase 4 - learning curve (6.1) | [`phase4_learning_curve_summary.md`](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/phase4_learning_curve_summary.md) |
| Phase 4 - CALCE CS2 transfer (6.3) | [`phase4_cs2_summary.md`](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/phase4_cs2_summary.md) |
| Phase 5 - AE negative result evidence (Round 2) | [`Progress_Report_Steps1-18.md`](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/nested_lobo/Progress_Report_Steps1-18.md), [`Steps_F3_I3_B7_Ablations.md`](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/nested_lobo/Steps_F3_I3_B7_Ablations.md) |
| R3-C9 - 13-paper verification table | [`r3c9_citation_verification.md`](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/r3c9_citation_verification.md) |
| Thesis drafts (v0.1) | [Ch.1](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/thesis_ch1_introduction_draft.md), [Ch.3](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/thesis_ch3_methodology_draft.md), [Ch.4](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/thesis_ch4_protocol_draft.md), [Ch.5](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/thesis_ch5_discussion_draft.md), [Appendix](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/thesis_appendix_negative_results.md) |
| State card and experiment log | [`PROJECT_STATE.md`](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/PROJECT_STATE.md) |

## 8. Verification status (re-run 2026-10-06)

| Suite | Checks |
|---|---|
| phase1_verify | 61/61 |
| protocol_gap_verify | 23/23 |
| td_clean_verify | 7/7 |
| phase3_charge_verify | 8/8 |
| phase3_selfref_verify | 9/9 |
| phase3_window_verify | 7/7 |
| phase3_dsoh_verify | 7/7 |
| phase3_windowlength_verify | 12/12 |
| phase3_feature_audit | 50/50 |
| data_provenance_audit | 26/26 |

Leakage probes: max|diff| = 0.00e+00 on every protocol and clean feature set.

Two corrections came out of this re-verification. First, the Ch.4 draft had quoted the Oracle
LOBO as 0.671; the correct phase-1 value is 0.663, and the draft was fixed. Second, the 0.845
and 0.854 Proxy-Free numbers come from different row sets, so Ch.4 now carries an explicit
row-set note to prevent a cross-row-set comparison.

## 9. Draft status

- Ch.4 (Results), draft v0.1:
  [`thesis_ch4_protocol_draft.md`](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/thesis_ch4_protocol_draft.md) -
  setup, protocol axis, proxy axis, the 5.1-5.5 verdicts, wider validation, the AE negative
  result, a headline table, and limitations.
- Ch.5 (Discussion), Ch.3 (Methodology), Ch.1 (Introduction) and the Appendix are drafted at
  v0.1; Ch.5 section 5.4 states the AE negative result with the E_fusion qualification.
- Ch.2 (Literature Review) is unblocked by C9. The comparison table can be built from
  [`r3c9_citation_verification.md`](https://github.com/DomIncham/soh-thesis-ae-bpnn/blob/main/Autoencoder/round3_phase1/r3c9_citation_verification.md)
  with a unit and protocol note on each row.

## 10. Question for the advisor

Thesis title. A partial window is not proxy-free by construction, because window means are
proxies at every length. I propose "proxy-audited, partial-window, unseen-battery SOH
estimation", which states the claim exactly, even though it is long. Please advise, or
suggest a phrasing you prefer.

Padipat Aincham
M11452803
