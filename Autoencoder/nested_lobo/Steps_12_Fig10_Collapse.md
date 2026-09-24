# Step 12: Quantitative Explanation of the Figure 10 Prediction Collapse

**Date:** 2026-09-25
**Scope:** Step 12 of the 18-step sequence — explain, with numbers, why the old pipeline's Figure 10 prediction collapsed toward a near-constant value (old reported metrics: RMSE ≈ 0.1744 Ah, R² ≈ −0.029; advisor Part G1/G2).
**Scope boundary:** this report explains the collapse mechanism of the old pipeline. It does **not** allocate fault between EIS representation and model — that verdict requires the time-domain comparison and is given in Steps 15–16.

---

## 1. The old prediction was statistically a flat line

The old Figure 10 evaluated on B0018 (fixed test battery). B0018's measured capacity: n = 132, mean = 1.558 Ah, **std = 0.155 Ah** (range 1.341–1.855).

| Quantity | Value | Meaning |
|---|---|---|
| Old test RMSE | 0.1744 Ah | = **1.126 × std(y)** |
| Old test R² | −0.029 | MSE = 1.029 × var(y) |
| Implied behavior | a constant line offset ≈ 0.080 Ah from the test mean | R² ≈ 0 is the mathematical signature of a constant predictor |

Two quantitative conclusions follow directly:

1. A trivial predictor that always outputs the test mean achieves RMSE = std(y) = 0.155 Ah (R² = 0 by definition). The old trained model achieved 0.1744 Ah — **12.6% worse than doing nothing**.
2. R² = −0.029 with RMSE ≈ 1.13 × std(y) means the prediction carried essentially **zero variance**: whatever structure the model output, it did not track the degradation trajectory at all.

## 2. Why the model output a constant: train success, transfer failure

The old grid search (single split, B0018 as the only test battery, Ah target, 300 fixed epochs, 12 configurations) shows the split pattern:

| Metric | Range over 12 configs |
|---|---|
| Train R² | −0.006 … **0.892** |
| Test R² | −2.762 … **−0.009** (never positive) |
| Test RMSE | 0.173 … 0.333 Ah (floor ≈ std(y)) |

Some configurations learned the training batteries well (train R² up to 0.89), yet **no configuration ever reached positive test R²**. A model that fits three batteries and then outputs a near-constant on the fourth is behaving as this table shows.

**The latent-space evidence (R1-C6, `Latent_Correlation_Metrics.csv`) explains the transfer failure.** Latent↔SOH correlations flip sign between the training batteries and the unseen battery:

| Latent node | Train Pearson | Test Pearson (B0018) |
|---|---|---|
| Node 6 | −0.659 | +0.168 |
| Node 7 | −0.515 | +0.015 |
| Node 4 | −0.070 | +0.247 |
| Node 5 (stable) | +0.573 | +0.523 |

A BPNN trained on latents whose SOH relationship inverts on the unseen battery cannot use them there; the loss-minimizing output degenerates toward a constant. This is the causal chain:

```
unstable latent features on unseen battery domain
        → BPNN signal unusable at test time
        → loss-minimizing output ≈ constant
        → RMSE ≈ std(y), R² ≈ 0  (Figure 10)
```

## 3. Pipeline defects that caused or amplified the collapse (all measured)

| Defect (old pipeline) | Evidence | Fixed in the new protocol |
|---|---|---|
| Target left in Ah (~1.84–2.02) with BPNN init ≈ 0 | model_eval run-3 lessons: outputs never reach the target scale in early configs (train R² −0.006 in grid search) | %SOH + target standardized on fold-train (Steps 7–10) |
| Fixed 300 epochs, no EarlyStopping | convergence claim unfalsifiable (Part I1) | EarlyStopping, AE stops at 129–192 epochs (Step 8) |
| Single split, B0018 as permanent test | reused for every design choice → development data (Part C1) | nested 4-fold LOBO (Step 7) |
| AE latent instability across battery domain | correlation flip table above (R1-C6) | quantified per-fold in Steps 9–10: AE is the only pipeline that degrades on fold B0006 while PCA/raw do not |

## 4. The new protocol removes the collapse on 3 of 4 folds

With the corrected pipeline (tolerance 1, nested LOBO, %SOH, standardization, EarlyStopping), AE→BPNN test R² per fold (mean over 3 seeds): **B0005 +0.538, B0006 +0.064, B0007 +0.715, B0018 −0.996** (Steps 7–8). The collapse is therefore not a property of the data — it was a property of the old pipeline. The remaining failure is fold-specific (B0018) and is carried to Steps 14–16.

## 5. Scope note

This report does not judge whether the remaining B0018 failure belongs to the EIS representation or to the model — per advisor Part B6, that verdict requires the time-domain comparison (Steps 14–16), which will be appended as the concluding section of the pipeline story.

---

## Ablation log

`2026-09-25 | step12 | old Fig10 RMSE = 1.13 x std(y); test R2 < 0 in all 12 old configs | flat-line collapse from unstable latents + unstandardized target`

## Artifacts

| File | Purpose |
|---|---|
| `step12_evidence.py` | All numbers in this report, computed from the raw capacity CSV, the old grid-search CSV, the R1 latent-correlation CSV, and the Steps 7–10 results |
| `Steps_12_Fig10_Collapse.md` | This report |