# Chapter 1 — Introduction (Draft v0.1, 2026-10-06)

> **Thesis title — PLACEHOLDER, awaiting advisor's answer (Round 4 report §10):**
> *"Proxy-audited, Partial-Window, Unseen-Battery State-of-Health Estimation for Lithium-Ion
> Batteries"* (proposed). The alternative carries "Autoencoder" only if the advisor reinstates
> the AE. All title-dependent text is marked [TITLE-DEPENDENT].
> Sources: R3-C4 contributions, Ch.4–5 drafts, `r3c9_citation_verification.md`.

---

## 1.1 Background

Lithium-ion batteries age, and their true capacity cannot be measured directly during use. A
battery management system therefore estimates the **state of health (SOH)** — the ratio of
current deliverable capacity to a reference capacity — from measurable electrical signals.
Accurate SOH estimates decide when a battery pack is serviced, replaced, or repurposed.

Two signal families dominate the literature: **electrochemical impedance spectroscopy (EIS)**,
measured at discrete laboratory checkpoints, and **time-domain charge–discharge curves**,
measured every cycle. Under constant-current discharge, the discharge duration itself is the
capacity divided by the current — so many feature families carry the answer they are supposed to
predict. How the estimator is evaluated matters as much as the estimator: if a model is trained
and tested on cycles of the *same* battery, the task it solves is interpolation of a single
degradation curve, not prediction for an unseen cell.

## 1.2 Problem statement

This thesis asks one question: **how much of the reported accuracy in SOH estimation survives a
strict, transfer-oriented evaluation — and what remains when it does not?**

The question is motivated by a measured gap. On identical features and an identical model, our
experiments move the headline R² from **−1.03 to +0.99** by changing only the split protocol, and
from **0.93 to 0.49** by removing only the capacity-proxy features. Published high scores are
concentrated in the regimes those experiments expose as easy: same-battery splits and
proxy-carrying inputs (verified across the 13 studies of the advisor's audit
[R3-C9 verification table]).

## 1.3 Research gap

Verified against the full texts (not summaries):

1. **Cross-battery estimation under strict protocols is under-reported.** Only [11] reports both
   random and battery-wise validation on the same pipeline (0.9788 → 0.7855); the rest of the
   strong claims use same-battery or proxy-assisted settings.
2. **EIS + discharge + cross-battery already exists** ([11], [12], [13]) — fusion itself is not
   the gap. The open problem is the *evaluation honesty* of fusion claims under unseen cells.
3. **Proxy-free claims are rare and rarely audited.** Where a capacity proxy enters the feature
   set ([3], [4], [9], [10]), the reported score is not comparable to a proxy-free one; no study
   in the verified list reports both regimes on one fixed pipeline.
4. **Cross-dataset transfer is usually asserted, not controlled.** Our NASA→CALCE experiment
   shows the failure mode (per-cell label offset) and includes the within-dataset control that
   makes the diagnosis sayable.

## 1.4 Objectives

1. Build a leakage-disciplined evaluation harness: nested LOBO, fold-train-only normalisation,
   mechanical leakage probes, provenance checks against the raw NASA files.
2. Quantify the two accuracy axes — **evaluation protocol** and **capacity proxy** — on one fixed
   pipeline, holding everything else constant.
3. Establish the defensible unseen-battery, proxy-audited performance (feature audit → Clean
   sets → paired claims only).
4. Test the pipeline's robustness: wider NASA pool (14 cells), cross-dataset (CALCE CS2) with a
   within-domain control.
5. Evaluate the autoencoder representation against linear (PCA) and raw-feature alternatives on
   both modalities, and report the verdict as a documented negative result if it does not add
   value.

## 1.5 Contributions [TITLE-DEPENDENT — phrasing follows the title decision]

1. **Quantification, not assertion:** the protocol axis (R² −1.03…0.99) and the proxy axis
   (−0.40…0.93) measured on one fixed pipeline — the first such two-axis measurement on the NASA
   4-cell benchmark at this strictness level.
2. **A defensible number:** Clean-8 = **0.810 R²** (nested LOBO, 5 seeds, unseen battery,
   proxy-audited feature set), with the strict proxy-free floor (0.490) and the paired-row-set
   discipline stated alongside.
3. **A controlled cross-dataset negative result:** NASA→CS2 transfer fails (median R² −37),
   the within-CS2 control succeeds (0.39–0.68 on 6/8), locating the failure at the per-cell label
   offset rather than the pipeline.
4. **A documented AE negative result** with mechanism (interpolation reconstruction, not the
   measurement) and the recorded exception (E-fusion on weak-feature regimes).
5. **A verified literature comparison:** 13 studies re-checked from their full PDFs; the audit's
   anchor numbers confirmed verbatim; unit and protocol annotated per row for Ch.2.

## 1.6 Thesis outline

- **Ch.2** reviews the verified literature in five groups (time-domain, EIS, fusion,
  cross-battery, partial-window) and explains the R² spread through the seven audit factors.
- **Ch.3** specifies the data, SOH definition, nested LOBO protocol, leakage discipline, feature
  audit, and verification suites.
- **Ch.4** reports the protocol axis, the proxy axis, the proxy-free improvements (5.1–5.5), the
  wider validation, and the AE negative result.
- **Ch.5** discusses the seven factors as measured quantities, the learning-curve and
  cross-dataset findings, the AE decision, and the limitations.
- **Appendix** records the negative results in full: AE on EIS and TD, interpolation and
  tolerance ablations, self-reference and ΔSOH rejections.
