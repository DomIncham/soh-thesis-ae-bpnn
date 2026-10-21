# Phase 6 support-split summary (R6-C2.3, diagnostic only)

Row set: CALCE include_cell & cap_ok, Clean-5T, 49,220 dump rows x 10 (pool,seed) runs.
Inside = all 5 features within NASA min-max; Outside = >=1 feature outside (strict per-feature).

- Overall: MAE 23.52%, MedAE 19.51%, frac(yhat>115%) 0.49
- INSIDE  (50.0 rows): MAE 11.90, MedAE 13.26, P90 20.90, frac(yhat>115) 0.000
- OUTSIDE (49,170.0 rows): MAE 23.53, MedAE 19.52, P90 48.33, frac(yhat>115) 0.486
- Spearman(cell MedAE, mean n-features-outside) = 0.491

Reading: compare MedAE/P90 between groups — if OUTSIDE is markedly worse, feature-range
extrapolation drives the transfer failure (R6-C2.3). Fallback context (R6-C4): selection
fallback rate 0.80 in the underlying rerun applies to BOTH groups equally.
