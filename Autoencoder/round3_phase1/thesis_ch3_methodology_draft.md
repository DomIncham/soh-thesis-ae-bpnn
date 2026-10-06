# Chapter 3 — Methodology (Draft v0.1, 2026-10-06)

> Sources: `end_to_end_research_workflow_v2.md`, Round 2 steps 1–18 (`nested_lobo/Progress_Report_Steps1-18.md`),
> R3-C3 feature audit (`r3c3_feature_classification.md`), R3-C1 refit rule, leakage/verification
> suites (210/210 checks, re-run 2026-10-06). Justifies each design choice against the weaker
> protocols documented in the verified literature (`r3c9_citation_verification.md`).
> Style: A2-B1, short sentences.

---

## 3.1 Data and SOH definition

- **Dataset:** NASA Ames randomized battery aging set, cells B0005, B0006, B0007, B0018 —
  636 discharge cycles in total (168/168/168/132). Cycle counts and minimum SOH (69.9 / 57.2 /
  74.4 / 72.9 %) were re-checked against the original NASA files by the advisor's audit
  (provenance suite: 26/26 checks, `data_provenance_audit.py`).
- **SOH definition:** SOH = Q(c) / Q_ref × 100, where Q_ref is the mean discharge capacity of the
  first five cycles. Rationale: Q/Q_N (rated capacity) hides real degradation start-points;
  per-cycle initial capacity ([7], [9]) ties the scale to each cell. Q_ref over the first five
  cycles is fixed per cell, shared across all folds, and never uses test information.
- **Units everywhere:** %SOH for errors, Ah for capacity; RMSE is reported in both.

## 3.2 The evaluation protocol: nested LOBO

The test battery must be unseen. The protocol has two loops:

1. **Inner loop (selection):** leave one battery out for *validation* — 3-fold over the training
   batteries. Configurations (BPNN architecture grid, epochs, learning rate) are selected by the
   inner-validation RMSE only. A selection guard rejects degenerate candidates (a candidate that
   fails to fit its own training fold cannot be selected; fixing this bug moved Proxy-Free from
   0.732 to 0.854 in Phase 1).
2. **Outer loop (test):** the selected configuration is **re-fitted on all three training
   batteries** (R3-C1 `refit_on_3`) and scored once on the untouched battery. Five seeds
   (42, 7, 123, 2024, 11); every table in Ch.4 reports mean and median over folds × seeds.

This is stricter than the protocols in the verified literature: same-battery chronological
([1], [5]), random splits ([6], [11]-random), or 1-cell-held-out within one condition ([7]).
The protocol axis experiment (Ch.4 §4.2) quantifies what that strictness costs — and the
quantification itself is a contribution.

## 3.3 Leakage discipline

Three mechanisms, each verified mechanically rather than asserted:

1. **Fold-train-only normalisation.** Standardisation statistics are computed on the fold's
   training batteries only. Split-wise normalisation — the same discipline — is applied by [8],
   which we cite as the comparable example.
2. **Mask assertions.** Train/validation/test masks are asserted disjoint at every run;
   840 asserts in the Phase-4 learning-curve run, none fired.
3. **Leakage probes.** Perturbation probes confirm that test rows do not influence training
   statistics: max|diff| = 0.00e+00 on every protocol and on every clean feature set (Ch.4 §4.1).

## 3.4 Feature families (R3-C3)

| Family | Features | Proxy status |
|---|---|---|
| TD-All (8) | `dis_duration`, `dis_mean_V`, `dis_V_slope`, `cc_dur`, `cv_dur`, `dis_mean_T`, `t_40_41`, `ic_peak_V` | mixed — see below |
| Proxy-carrying | `dis_duration` (direct: capacity = I × t in CC discharge), `dis_mean_V` (collinear r = 0.941; 94.8 % within-battery capacity variance alone) | removed in Clean-6 |
| Charge-segment | `ic_peak_V`, `t_40_41` | audited: label-correlation below the 0.90 gate; added back in Clean-7/8 |
| Window (5.2, rejected) | fixed 4.0–3.6 V window features | `win_dur` R²(cap) 0.995 — proxy at every window length; not used |

Full classification with code paths and formulas: `r3c3_feature_classification.md`;
verified by `phase3_feature_audit.py` (50/50). The 0.90 label-correlation gate and every feature's
R²(capacity) are recorded there. Features extracted once from the raw .mat files, cached to CSV,
and re-audited against the raw files by the provenance suite.

## 3.5 Model

- **Main pipeline: TD features → BPNN.** One hidden architecture grid for every experiment
  (identical across protocol arms so that the split protocol is the only variable in §4.2).
- Training: Adam, early stopping on inner-validation RMSE, five seeds, per-fold standardisation.
- **Loss selection** (ablation, Round 2): MSE/MAE/Huber indistinguishable (RMSE 8.32–8.57 on the
  EIS arm) — MSE retained.
- **Monotonicity variant** (Appendix): a monotone-projected BPNN was tested for the ΔSOH scheme
  and cannot rescue it — clamping does not remove a linear drift (`phase3_dsoh_verify.py`).

## 3.6 Baselines and the AE arm

- Baselines per fold: mean predictor, TD-Ridge. Pipeline ranking (Round 2, RMSE %SOH):
  **TD-BPNN 3.59 > TD-Ridge 4.35 > E-fusion 4.89 > EIS pipelines 8.3–8.6 > mean 11.5**.
- The AE (bottleneck 17) was trained on the interpolated EIS representation and on TD features.
  Method note recorded in the Appendix: the AE reconstructs its interpolation grid input, not the
  measurement — this is a property of the input representation, identified in Round 1 and carried
  into Round 2's ablations (bottleneck size {3..67} and loss ablations are indistinguishable).
  Ch.5 §5.4 states the negative result and its one qualification (E_fusion).
- **PCA on EIS** is the stronger linear reducer (+0.61 vs AE +0.08) and is reported alongside.

## 3.7 Wider-validation protocols (R3-C6)

- **6.1 Learning curve:** for each (k, seed, test cell), k train cells are sampled from the other
  13 of the 14 eligible cells (B0005/06/07/18 + B0025–B0032, 47/48); one sampled cell serves as
  the inner-validation battery; the selected config is refit on all k; the untouched cell is
  scored. 420 fold-runs, determinism check ΔR² = 1.6e-05.
- **6.3 Cross-dataset:** NASA → CALCE CS2 (8 cells, 4,922 full cycles, capacity cross-checked
  against CALCE coulomb counting: max|diff| ≤ 0.004 Ah). Four arms: frozen / 1-cell scratch /
  1-cell warm-adapt (lr 1e-4 + gradient clipping) / within-CS2 LOCO control. Feature set Clean-6T
  (CS2_33–38 logs have no temperature channel — disclosed, not hidden).
- **Exclusion rules** (committed in `phase4_survey_B0025_B0056.md`): corrupt file heads and
  spurious-capacity cells are excluded before any model sees them; the rule is written down and
  applied identically to every arm.

## 3.8 Verification and reproducibility

- Ten verification suites totalling **210 checks** (plus 26 provenance checks) re-runnable from
  the repository; all pass as of 2026-10-06 (list in the Round 4 report §8).
- Every headline number in Ch.4–5 carries a source CSV path; the aggregation was re-computed from
  raw result files during the Round 4 check, not copied from earlier summaries.
- Where two experiments share a setting but differ in row set (e.g. Proxy-Free 0.845 vs 0.854),
  the row-set identity is stated at the point of use — numbers are quoted only against numbers
  from the same row set.

## 3.9 Justification summary (why each strictness is kept)

| Design choice | Weaker alternative in the literature | What it costs us | Why kept |
|---|---|---|---|
| Nested LOBO + refit_on_3 | same-battery splits ([1], [5], [6]) | 0.979 → 0.927 (and exposes −1.03 chronological) | the test battery must be unseen for the claim to mean transfer |
| Proxy-free feature sets | Q(k−1) / cycle-index inputs ([3], [4], [9], [10]) | 0.927 → 0.490 floor (0.810 with audited charge features) | a proxy input is the answer in disguise under CC discharge |
| Per-fold + pooled reporting | pooled-only R² | pooled inflates −1.03 → +0.85 | per-fold numbers are the honest unit |
| Q/Q_ref, %SOH units | mixed Q/Q_N, Q/Q(1), ŷ₁=1 | numbers look larger in %SOH | comparability and no hidden re-baselining |
| 5 seeds, mean+median | single-run headline | median vs mean diverge under one catastrophic fold (B0018) | a single fold can invert the mean's sign |
