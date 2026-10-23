# P6 loophole-closure audit (pre-report, diagnostic only)

- [OK] C1: La-quantile MAE 6.76 vs constant-predictor 4.06 (R2 from rung CSV = -1.25)
- [OK] C1: per-cell yhat/y std ratio: median 0.063 (flat prediction confirmed)
- [OK] C2: support_split.csv now carries fallback_rate=0.80 on every row (R6-C4)
- [OK] C3: strict any-outside AND majority(>=3-of-5) both reported on the L0 rerun; if conclusions agree across definitions, the result cannot flip
- [OK] C4: common-range n=39870 rows; MedAE 19.33, P90 48.74 now reported next to MAE/RMSE/R2
- [OK] C5: Lc: 45/80 calibrations degenerate (slope<=0 or |slope-1|>=1); median MAE without them = 9.24

Overall: ALL CLOSURES VERIFIED
