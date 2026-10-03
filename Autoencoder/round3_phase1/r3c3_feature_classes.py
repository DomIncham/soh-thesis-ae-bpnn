# R3-C3 (first half): label every TD feature safe / proxy, as the advisor requires.
# Rule, stated up front so it cannot be tuned after seeing the answer:
#   within a battery, fit y ~ a + b*feature (OLS) and read R^2 against CAPACITY (the label's
#   numerator) and against SOH.
#     PROXY      : R^2(capacity) >= 0.90  -> the feature is (near) mechanically the label
#     BORDERLINE : 0.50 <= R^2 < 0.90
#     SAFE       : R^2 < 0.50             -> can only help through degradation physics
# Also reports cross-battery domain shift (per-battery mean spread / pooled std) because audit
# factor 7 says the discharge cut-offs differ per cell.
import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, r"C:\Master Degree\Thesis\Autoencoder\round3_phase1")

F = r"C:\Master Degree\Thesis\Autoencoder\nested_lobo\time_domain_features.csv"
df = pd.read_csv(F)
df.columns = [c.strip() for c in df.columns]
FEATS = ["dis_duration", "dis_mean_V", "dis_mean_T", "dis_V_slope",
         "cc_dur", "cv_dur", "cv_I_slope", "ch_mean_T"]
SIDE = {f: ("discharge" if f.startswith("dis_") else "charge(previous cycle)") for f in FEATS}


def r2_lin(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    m = np.isfinite(x) & np.isfinite(y)
    if m.sum() < 10 or np.std(x[m]) == 0:
        return float("nan")
    b, a = np.polyfit(x[m], y[m], 1)
    yh = a + b * x[m]
    ss = ((y[m] - y[m].mean()) ** 2).sum()
    return float(1 - ((y[m] - yh) ** 2).sum() / ss) if ss > 0 else float("nan")


rows = []
for f in FEATS:
    cap_r2, soh_r2, cap_r, soh_r = [], [], [], []
    for b, g in df.groupby("battery"):
        cap_r2.append(r2_lin(g[f], g["capacity"]))
        soh_r2.append(r2_lin(g[f], g["soh"]))
        cap_r.append(np.corrcoef(g[f], g["capacity"])[0, 1])
        soh_r.append(np.corrcoef(g[f], g["soh"])[0, 1])
    pooled = np.corrcoef(df[f], df["soh"])[0, 1]
    mean_cap_r2 = float(np.nanmean(cap_r2))
    cls = "PROXY" if mean_cap_r2 >= 0.90 else ("BORDERLINE" if mean_cap_r2 >= 0.50 else "SAFE")
    means = df.groupby("battery")[f].mean()
    rows.append(dict(feature=f, side=SIDE[f],
                     mean_R2_capacity=round(mean_cap_r2, 3),
                     mean_R2_soh=round(float(np.nanmean(soh_r2)), 3),
                     mean_r_capacity=round(float(np.nanmean(cap_r)), 3),
                     pooled_r_soh=round(float(pooled), 3),
                     per_battery_R2_capacity=[round(x, 3) for x in cap_r2],
                     across_battery_spread=round(float(means.max() - means.min()), 3),
                     class_=cls))
out = pd.DataFrame(rows).sort_values("mean_R2_capacity", ascending=False)
pd.set_option("display.width", 250)
print("=== R3-C3 feature classification (rule fixed before looking: R2(capacity) >= 0.90 -> PROXY) ===\n")
print(out[["feature", "side", "mean_R2_capacity", "mean_R2_soh", "pooled_r_soh",
           "across_battery_spread", "class_"]].to_string(index=False))
print("\nper-battery R2 vs capacity:")
for _, r in out.iterrows():
    print(f"  {r.feature:14s} {r.per_battery_R2_capacity}  -> {r.class_}")
print("\n=== cross-battery domain shift (per-battery mean, min..max) ===")
for f in FEATS:
    m = df.groupby("battery")[f].mean()
    print(f"  {f:14s} {m.min():12.4f} .. {m.max():12.4f}   (ratio max/min = {m.max()/m.min():.3f})")
out.to_csv(r"C:\Master Degree\Thesis\Autoencoder\round3_phase1\r3c3_feature_classes.csv", index=False)
print("\nsaved: r3c3_feature_classes.csv")