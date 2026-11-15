# Round 6B (R7-C0/R7-C1): matched 3-way analysis — Cal-only vs Warm-FT-only (Adapt2)
# vs Warm-FT+Cal (Lc), same labeled target cell, keys (pool, seed, adapt_cell) x 80 runs.
# L0 zero-shot reference from the P6-2 dump (same protocol, verified identical cfg/epochs).
# Statistics at RUN level only (R7-C1); recovery reported under BOTH definitions with labels:
#  (a) "MAE reduction relative to matched L0" = (MAE_L0 - MAE_arm)/MAE_L0
#  (b) "Transfer-gap recovery" = (MAE_L0 - MAE_arm)/(MAE_L0 - MAE_within_floor),
#      within-CALCE median MAE as the floor, matched rows.
# Usage: python phase6b_analysis.py
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

K = ["pool", "seed", "adapt_cell"]
cal = pd.read_csv("phase6b_cal_only.csv")
ft = pd.read_csv("phase5_cs2_adapt2_c5t_full.csv")     # warm fine-tuning only
lc = pd.read_csv("phase6_ladder_Lc.csv")               # warm fine-tune + calibration
w = pd.read_csv("phase5_cs2_within_c5t_full.csv")      # within-CALCE floor
d = pd.read_csv("phase6_preds_transfer_full.csv", low_memory=False)

# Lc degenerate from its recorded fitted slope (same criterion as cal_only)
lc["slope"] = lc.variant.str.replace("slope=", "").astype(float)
lc["cal_degenerate"] = (lc.slope <= 0) | ((lc.slope - 1).abs() >= 1)

# L0 run-level MAE, pooled over the 7 non-adapt cells (same definition as cal_only)
l0 = d.groupby(["pool", "seed"]).apply(lambda x: np.abs(x.yhat - x.y).mean(),
                                       include_groups=False)
base = pd.DataFrame({"MAE_L0": cal.apply(lambda r: l0[(r.pool, r.seed)], axis=1).values})
m = cal[K + ["MAE", "cal_slope", "cal_degenerate"]].rename(
    columns={"MAE": "MAE_cal", "cal_degenerate": "deg_cal"})
m = m.merge(ft[K + ["MAE"]].rename(columns={"MAE": "MAE_ft"}), on=K, how="inner", validate="1:1")
m = m.merge(lc[K + ["MAE", "slope", "cal_degenerate"]].rename(
    columns={"MAE": "MAE_ftcal", "cal_degenerate": "deg_lc"}), on=K, how="inner", validate="1:1")
m = m.join(base)
floor = w.MAE.median()
print(f"within-CALCE median MAE (floor): {floor:.3f} (n={len(w)} runs)\n")
assert len(m) == 80, len(m)
assert m.notna().all().all()

print("== 3-way matched table (MAE, run-level, n=80) ==")
tbl = {}
for arm, col in [("Cal-only", "MAE_cal"), ("FT-only", "MAE_ft"), ("FT+Cal", "MAE_ftcal"),
                 ("L0 ref", "MAE_L0")]:
    tbl[arm] = dict(mean=m[col].mean(), median=m[col].median())
tbl = pd.DataFrame(tbl).T.round(3)
print(tbl.to_string())
print("\n== paired run-level Wilcoxon (n=80) ==")
for a, b in [("MAE_cal", "MAE_ft"), ("MAE_cal", "MAE_ftcal"), ("MAE_ft", "MAE_ftcal")]:
    p = wilcoxon(m[a], m[b]).pvalue
    print(f"{a} vs {b}: better {int((m[a] < m[b]).sum())}/80, p = {p:.4f}")

print("\n== recovery, definition (a): MAE reduction relative to matched L0 ==")
for arm, col in [("Cal-only", "MAE_cal"), ("FT-only", "MAE_ft"), ("FT+Cal", "MAE_ftcal")]:
    red = (m.MAE_L0 - m[col]) / m.MAE_L0
    print(f"{arm}: median {red.median():.1%}, mean {red.mean():.1%}")
print("\n== recovery, definition (b): transfer-gap recovery (within floor) ==")
for arm, col in [("Cal-only", "MAE_cal"), ("FT-only", "MAE_ft"), ("FT+Cal", "MAE_ftcal")]:
    rec = (m.MAE_L0 - m[col]) / (m.MAE_L0 - floor)
    print(f"{arm}: median {rec.median():.1%}, mean {rec.mean():.1%}")

print("\n== non-degenerate subset (Lc criterion applied to its own arm) ==")
nd = m[~m.deg_cal & ~m.deg_lc]
print(f"matched non-degenerate runs: {len(nd)}/80")
for arm, col in [("Cal-only", "MAE_cal"), ("FT+Cal", "MAE_ftcal")]:
    print(f"{arm}: median {nd[col].median():.2f} (L0 {nd.MAE_L0.median():.2f})")
p = wilcoxon(nd.MAE_cal, nd.MAE_ftcal).pvalue
print(f"Cal-only vs FT+Cal (non-degenerate): Cal better {int((nd.MAE_cal < nd.MAE_ftcal).sum())}/{len(nd)}, p = {p:.4f}")

print("\n== degeneracy / fallback disclosure (R6-C4) ==")
print(f"Cal-only degenerate: {int(m.deg_cal.sum())}/80 | Lc degenerate: {int(m.deg_lc.sum())}/80")
print(f"\nunits: MAE in %SOH | rows here = 80 RUNS (2 pools x 5 seeds x 8 adapt cells); "
      f"prediction-instance rows in dumps are NOT observations (R7-C1)")
m.to_csv("phase6b_matched_3way.csv", index=False)
print("\nwritten: phase6b_matched_3way.csv")
