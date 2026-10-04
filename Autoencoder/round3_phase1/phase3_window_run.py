# Phase 3, item 5.2 confirmation run.
# extract_window_features.py classified the 4.0-3.6 V window features and 5 of 7 came back PROXY:
#   win_dur 0.995, win_dQ 0.995, win_frac 0.979, win_V_slope 0.968, win_dT 0.935  -> PROXY
#   win_mean_V 0.659 BORDERLINE | win_mean_T 0.494 SAFE
# win_dur is a STRONGER proxy than the whole-cycle dis_duration (0.972), because at constant current
# the time in a fixed voltage window is the charge taken in that window, i.e. win_frac x capacity.
# Cross-battery domain shift is also worse: win_frac spread 1.405x, win_dur 1.377x, against
# dis_duration 1.020x. So the window removes neither the proxy nor the incomparability.
#
# The only legitimate substitution is therefore SAFE-for-SAFE: dis_mean_T (0.430) -> win_mean_T
# (0.494). This run measures whether that swap changes anything, on the same 631 rows, folds and
# seeds as the 5.1 run, so it can be compared cell-by-cell against the committed Clean-7 = 0.772.
# Usage: python phase3_window_run.py [--seeds 42,7,123,2024,11] [--device cpu]
import argparse
import os
import numpy as np
import pandas as pd
import r3common as R
from r3common import BATT, load_td, soh_range_and_qref, run_fold, OUT

# Clean-7 minus dis_mean_T, plus win_mean_T, plus ic_peak_V
BASE_FEATS = ["dis_V_slope", "cc_dur", "cv_dur", "cv_I_slope", "ch_mean_T"]
SETTING = "TD-Win-7"
EXTRA = ["win_mean_T", "ic_peak_V"]

ap = argparse.ArgumentParser()
ap.add_argument("--seeds", default="42,7,123,2024,11")
ap.add_argument("--device", default="cpu", choices=["cpu", "cuda", "auto"])
ap.add_argument("--tag", default="cpu")
a = ap.parse_args()

R.set_device(a.device)
seeds = [int(s) for s in a.seeds.split(",")]
rng_span, qref = soh_range_and_qref()

ch = pd.read_csv(os.path.join(os.path.dirname(R.TD_CSV), "charge_features.csv"))
ch.columns = [c.strip() for c in ch.columns]
wn = pd.read_csv(os.path.join(os.path.dirname(R.TD_CSV), "window_features.csv"))
wn.columns = [c.strip() for c in wn.columns]
tdf = pd.read_csv(R.TD_CSV)
tdf.columns = [c.strip() for c in tdf.columns]
for nm, d in (("charge_features", ch), ("window_features", wn)):
    assert np.array_equal(d.battery.values, tdf.battery.values) and \
           np.array_equal(d.cycle.values, tdf.cycle.values), f"ALIGNMENT: {nm} rows differ from TD"

mask = np.isfinite(ch[["ic_peak_V"]].values).all(axis=1)   # same 631-row subset as the 5.1 run
print(f"rows kept: {int(mask.sum())} / {len(ch)} (same subset as the 5.1 run)")

Xb, bids, soh, cyc = load_td(BASE_FEATS)
Xb, bids, soh, cyc = Xb[mask], bids[mask], soh[mask], cyc[mask]
X = np.hstack([Xb, wn.loc[mask, ["win_mean_T"]].values.astype(float),
               ch.loc[mask, ["ic_peak_V"]].values.astype(float)])
assert np.isfinite(X).all(), "NaN in the feature matrix"
print(f"{SETTING}: {X.shape[1]} features = {BASE_FEATS} + {EXTRA}")

rows, preds = [], []
for seed in seeds:
    for b in [1, 2, 3, 4]:
        r, p = run_fold(X, bids, soh, cyc, b, seed, 500, 30, qref, rng_span, SETTING)
        rows += r
        preds.append(p)
        ref = [x for x in r if x["stage"] == "refit_on_3"][0]
        print(f"{SETTING:10s} seed{seed:<5d} test={BATT[b]} cfg={ref['cfg']} ep={ref['sel_epochs']} "
              f"| R2={ref['test_R2']:+.3f} RMSE={ref['test_RMSE']:.3f}")

res = pd.DataFrame(rows)
res["device"] = R.DEVICE.type
res.to_csv(os.path.join(OUT, f"phase3_window_{a.tag}_results.csv"), index=False)
pd.concat(preds, ignore_index=True).to_csv(
    os.path.join(OUT, f"phase3_window_{a.tag}_preds.csv"), index=False)

cols = ["test_MAE", "test_RMSE", "test_R2", "test_MAPE", "test_RMSE_Ah"]
rf = res[res.stage == "refit_on_3"]
print("\n=== refit_on_3, mean / median / std over 4 folds x 5 seeds ===")
print(rf[cols].agg(["mean", "median", "std"]).round(3).to_string())
print("\ntest_R2 per fold (mean over seeds):")
print(rf.groupby("test_battery").test_R2.mean().round(3).to_string())
print(f"\ndegenerate fold-seeds: {int(rf.sel_degenerate.sum())} / {len(rf)}")
print("\nreference (same 631 rows): TD-Clean-7 = 0.772 mean / 0.827 median")
print("saved")