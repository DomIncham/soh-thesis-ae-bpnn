# Phase 3, item 5.3 — self-referenced normalisation: REJECTED

Advisor's plan, item 5.3: *"Self-referenced normalization — divide each feature by battery's
first-cycle value. No label needed at deploy; removes initial offsets (B0006 2.035 Ah vs ~1.86 Ah
others)."*

**Verdict: it does not work. It provides no benefit on three folds and destroys the fourth.** The
result is reported in full because it is a clean negative result with an identified mechanism, and
because it closes off one explanation of the per-battery scale problem found in the R3-C3 work.

## What was run

Same 631-row subset, folds, seeds (42/7/123/2024/11) and protocol as the 5.1 run. `r3common.run_fold`
was reused **unchanged** — the feature matrix was divided by the per-battery first-cycle vector
before the call — so the protocol is identical by construction and no selection logic was duplicated.
Assertions in the runner: the reference vector has no zero and no NaN, the normalised matrix is
finite, and each battery's first cycle normalises to exactly 1.0.

## Result — paired on identical (fold, seed) cells

| setting | mean R² | median R² | B0005 | B0006 | B0007 | **B0018** |
|---|---|---|---|---|---|---|
| `TD-Clean-6` + self-ref | −0.212 | 0.506 | 0.802 | 0.449 | 0.927 | **−3.026** |
| `TD-Clean-7` + self-ref | −0.054 | 0.744 | 0.877 | 0.539 | 0.931 | **−2.563** |
| `TD-Clean-8` + self-ref | 0.075 | 0.766 | 0.886 | 0.579 | 0.939 | **−2.105** |
| *same sets, unnormalised (5.1)* | *0.664 / 0.772 / 0.810* | *0.598 / 0.827 / 0.825* | *.674 / .802 / .862* | *.555 / .597 / .657* | *.818 / .922 / .924* | *+.611 / +.767 / +.799* |

Paired deltas, self-referenced minus unnormalised:

| fold | TD-Clean-6 | TD-Clean-7 | TD-Clean-8 |
|---|---|---|---|
| B0005 | +0.128 | +0.075 | +0.024 |
| B0006 | −0.106 | −0.057 | −0.078 |
| B0007 | +0.109 | +0.010 | +0.014 |
| **B0018** | **−3.637** | **−3.330** | **−2.904** |

- B0018 collapses in **all 5 seeds, all 3 settings** (worst single cell −6.66).
- No other fold-mean is damaged by more than 0.106.
- **Excluding B0018 the normalisation changes nothing**: +0.044 / +0.009 / −0.013.

So the three-fold behaviour is a wash, and the entire effect is one fold being destroyed.

## Why — and it is the opposite of the intended mechanism

The first-cycle references are, per feature, across the four batteries:

| feature | reference spread (max/min of \|ref\|) |
|---|---|
| `cv_I_slope` | **6.014×** |
| `t_40_41` | 1.517× |
| `cc_dur` | 1.265× |
| `dis_V_slope` | 1.242× |
| `cv_dur` | 1.098× |
| `ch_mean_T` / `dis_mean_T` | 1.037× / 1.027× |
| `ic_peak_V` | 1.000× (degenerate, see below) |

B0018's `cv_I_slope` reference is −3.84e-4 against −2.26e-3 / −2.31e-3 / −2.28e-3 for the others.
Dividing B0018 by its own reference therefore **inflates that feature about 6× relative to the rest
of the training set**. Self-referencing was meant to remove a per-battery offset; on this feature it
**introduces** one, in the opposite direction and larger. The model trained on the other three
batteries then faces B0018 on an incompatible scale, which is exactly the failure it produces.

This also falsifies the premise behind item 5.3. The offset quoted in the plan (B0006's 2.035 Ah vs
~1.86 Ah) is an offset in the **label** (Q_ref), not in the features: measured feature-level
reference spreads are only 1.03–1.27× for six of the eight features. Dividing features by their own
first cycle cannot remove a label-level offset, and where the feature reference is itself an outlier
it makes the scale mismatch worse.

## A limitation found before running, worth keeping

`ic_peak_V`'s first-cycle value is 4.18 for **all four** batteries — the top of the IC grid — so
dividing by it is a pure rescale carrying no per-battery information. Six cycles in total sit at
that grid edge. The feature is sound for 99 % of cycles (median 4.00–4.06 V) but its first-cycle
reference is not usable as a battery signature.

## Consequence

- Phase 3 item 5.3 is **closed as rejected**, with the mechanism documented. The per-battery scale
  problem identified in the R3-C3 work is **not** solved by self-referencing features.
- The proxy-free result stands at **TD-Clean-7 = 0.772 (median 0.827)** / **TD-Clean-8 = 0.810
  (median 0.825)** from item 5.1. Nothing in 5.3 improves on it.
- The remaining Phase 3 candidates that could address scale are **5.2** (fixed discharge voltage
  window, which removes the cut-off-voltage difference between cells — B0018's is 2.5 V against
  2.7/2.5/2.2 V) and **5.4** (predict ΔSOH and accumulate, which sidesteps absolute scale entirely).
  Given that the failure above is a scale mismatch on one cell, **5.2 is now the better-motivated
  next step than it was before this experiment**.

Evidence: `phase3_selfref_run.py`, `phase3_selfref_cpu_results.csv`, `phase3_selfref_cpu_preds.csv`,
`phase3_selfref_verify.py` (9/9 checks pass), `phase3_selfref_cpu.log`.