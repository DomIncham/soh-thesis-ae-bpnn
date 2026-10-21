# Round 6, R6-C2 step 1: per-feature NASA vs CALCE distribution comparison for Clean-5T.
# Features = Clean-5T (advisor R5 definition) = {dis_V_slope, cc_dur, cv_dur, cv_I_slope, ic_peak_V}.
# Row sets (identical to phase5_cs2_clean5t.pools()):
#   NASA = phase4_features.csv, include_cell, dropna(FEATS)   -> 14-cell wide pool
#   CALCE = phase4_cs2_features.csv, include_cell & cap_ok, dropna(FEATS) -> 4,922 full cycles
# Outputs per feature:
#   phase6_feature_shift.csv  - NASA min/max, CALCE min/max, overlap band, % CALCE below/above
#                               NASA range, KS statistic + p, Wasserstein distance
#   phase6_feature_hist.png   - per-feature NASA vs CALCE histograms
#   phase6_feature_shift_summary.md - compact numbers for the report
# Diagnostic only (R6-C2.1): no model is trained here.
# Run: python phase6_feature_shift.py   (CPU, seconds)
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

FEATS = ["dis_V_slope", "cc_dur", "cv_dur", "cv_I_slope", "ic_peak_V"]

nasa = pd.read_csv("phase4_features.csv")
nasa = nasa[nasa.include_cell].dropna(subset=FEATS).reset_index(drop=True)
cs2 = pd.read_csv("phase4_cs2_features.csv")
cs2 = cs2[cs2.include_cell & cs2.cap_ok].dropna(subset=FEATS).reset_index(drop=True)

rows = []
fig, axes = plt.subplots(2, 3, figsize=(14, 8))
axes = axes.ravel()
for i, f in enumerate(FEATS):
    a, b = nasa[f].values, cs2[f].values
    lo, hi = float(np.min(a)), float(np.max(a))
    below = float(np.mean(b < lo) * 100)
    above = float(np.mean(b > hi) * 100)
    outside = below + above
    ks = stats.ks_2samp(a, b)
    wd = stats.wasserstein_distance(a, b)
    # normalised shift: Wasserstein divided by NASA range, so features are comparable
    wdn = wd / (hi - lo) if hi > lo else np.nan
    rows.append(dict(feature=f, nasa_min=lo, nasa_max=hi, nasa_mean=float(np.mean(a)),
                     calce_min=float(np.min(b)), calce_max=float(np.max(b)),
                     calce_mean=float(np.mean(b)), pct_below_nasa=round(below, 2),
                     pct_above_nasa=round(above, 2), pct_outside_nasa=round(outside, 2),
                     ks_stat=round(float(ks.statistic), 4), ks_p=float(ks.pvalue),
                     wasserstein=round(float(wd), 6), wasserstein_over_range=round(float(wdn), 4)))
    ax = axes[i]
    ax.hist(a, bins=50, alpha=0.55, label="NASA", density=True)
    ax.hist(b, bins=50, alpha=0.55, label="CALCE", density=True)
    ax.axvline(lo, color="k", ls="--", lw=0.8)
    ax.axvline(hi, color="k", ls="--", lw=0.8)
    ax.set_title(f"{f}\noutside NASA range: {outside:.1f}%")
    ax.legend(fontsize=8)
axes[-1].axis("off")
fig.tight_layout()
fig.savefig("phase6_feature_hist.png", dpi=150)

df = pd.DataFrame(rows)
df.to_csv("phase6_feature_shift.csv", index=False)
print(df.to_string(index=False))

lines = ["# Phase 6 feature-shift summary (R6-C2.1, diagnostic only)", "",
         "Row sets: NASA = phase4_features.csv include_cell dropna (14 cells, "
         f"{len(nasa)} rows); CALCE = phase4_cs2_features.csv include_cell & cap_ok dropna "
         f"({cs2.battery.nunique()} cells, {len(cs2)} rows). Unit = each feature's raw unit "
         "from the Phase 4 extractors; KS/Wasserstein computed on raw values.", ""]
for r in rows:
    lines.append(f"- **{r['feature']}**: NASA [{r['nasa_min']:.4g}, {r['nasa_max']:.4g}] vs "
                 f"CALCE [{r['calce_min']:.4g}, {r['calce_max']:.4g}]; "
                 f"{r['pct_below_nasa']:.1f}% below / {r['pct_above_nasa']:.1f}% above the NASA "
                 f"range ({r['pct_outside_nasa']:.1f}% outside); "
                 f"KS={r['ks_stat']:.3f} (p={r['ks_p']:.1e}), "
                 f"Wasserstein/range={r['wasserstein_over_range']:.3f}")
with open("phase6_feature_shift_summary.md", "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines) + "\n")
print("\nWrote phase6_feature_shift.csv, phase6_feature_hist.png, "
      "phase6_feature_shift_summary.md")
