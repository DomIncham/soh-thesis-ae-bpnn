# Phase 3, item 5.5 (advisor R3-C5 item 5): the window-length curve.
# "RMSE vs window length - answers 'how little data is enough?'"
#
# Measured constraints found before running (extract_windowlength_features.py + a diagnostic):
#   - the dV axis the advisor suggested is only partly usable on these files. At current switch-on
#     the voltage steps ~0.2 V between the first two samples, so dV = 0.1 V and 0.2 V never leave 10
#     samples and are infeasible; dV = 0.3 V yields only 8-13 samples. The TIME axis is fine, so the
#     curve is built on time windows.
#   - sample interval differs per cell (18.7 s for B0005 against 9.4 s for B0018), so a W-minute
#     window holds a different number of samples per battery.
#   - within the window, mean_V is a PROXY at every W (0.947/0.953/0.975/0.979) and dT is a proxy at
#     W = 5 and 30 (0.920/0.942); only mean_T stays SAFE at every W (0.086/0.162/0.288/0.466).
#
# Two curves are produced so the contrast is visible rather than argued:
#   PF = proxy-free : the window's mean_T only, plus the charge-side features and ic_peak_V
#   PL = proxy-laden: the same, plus the window's mean_V (R2(capacity) 0.947 at W = 5)
# Both on the same 631-row subset, same folds, seeds 42/7/123 (the Phase 1 seed set).
# Usage: python phase3_windowlength_run.py [--seeds 42,7,123] [--device cpu]
import argparse
import os
import numpy as np
import pandas as pd
import r3common as R
from r3common import BATT, load_td, soh_range_and_qref, run_fold, OUT

WS = [5, 10, 20, 30]
BASE_FEATS = ["cc_dur", "cv_dur", "cv_I_slope", "ch_mean_T"]   # charge side, W-independent

ap = argparse.ArgumentParser()
ap.add_argument("--seeds", default="42,7,123")
ap.add_argument("--device", default="cpu", choices=["cpu", "cuda", "auto"])
ap.add_argument("--tag", default="cpu")
a = ap.parse_args()

R.set_device(a.device)
seeds = [int(s) for s in a.seeds.split(",")]
rng_span, qref = soh_range_and_qref()

wl = pd.read_csv(os.path.join(os.path.dirname(R.TD_CSV), "windowlength_features.csv"))
wl.columns = [c.strip() for c in wl.columns]
ch = pd.read_csv(os.path.join(os.path.dirname(R.TD_CSV), "charge_features.csv"))
ch.columns = [c.strip() for c in ch.columns]
tdf = pd.read_csv(R.TD_CSV)
tdf.columns = [c.strip() for c in tdf.columns]
for nm, d in (("windowlength", wl), ("charge", ch)):
    assert np.array_equal(d.battery.values, tdf.battery.values) and \
           np.array_equal(d.cycle.values, tdf.cycle.values), f"ALIGNMENT: {nm} rows differ from TD"

mask = np.isfinite(ch["ic_peak_V"].values)
print(f"rows kept: {int(mask.sum())} / {len(ch)} (same 631-row subset as the other Phase 3 runs)")

Xb, bids, soh, cyc = load_td(BASE_FEATS)
Xb, bids, soh, cyc = Xb[mask], bids[mask], soh[mask], cyc[mask]
icp = ch.loc[mask, ["ic_peak_V"]].values.astype(float)

rows, preds = [], []
for W in WS:
    for curve, extra in (("PF", []), ("PL", ["mean_V"])):
        cols = [f"w{W}_mean_T"] + [f"w{W}_{e}" for e in extra]
        X = np.hstack([Xb, icp, wl.loc[mask, cols].values.astype(float)])
        assert np.isfinite(X).all(), f"NaN in the W={W} {curve} matrix"
        name = f"W{W}-{curve}"
        print(f"\n--- {name}: {X.shape[1]} features = {BASE_FEATS} + ic_peak_V + {cols}")
        for seed in seeds:
            for b in [1, 2, 3, 4]:
                r, p = run_fold(X, bids, soh, cyc, b, seed, 500, 30, qref, rng_span, name)
                rows += r
                preds.append(p)
                ref = [x for x in r if x["stage"] == "refit_on_3"][0]
                print(f"{name:10s} seed{seed:<5d} test={BATT[b]} cfg={ref['cfg']} "
                      f"ep={ref['sel_epochs']} | R2={ref['test_R2']:+.3f} "
                      f"RMSE={ref['test_RMSE']:.3f}")

res = pd.DataFrame(rows)
res["device"] = R.DEVICE.type
res["window_min"] = res.setting.str.extract(r"^W(\d+)-")[0].astype(float)
res["curve"] = res.setting.str.extract(r"-(PF|PL)$")[0]
res.to_csv(os.path.join(OUT, f"phase3_windowlength_{a.tag}_results.csv"), index=False)
pd.concat(preds, ignore_index=True).to_csv(
    os.path.join(OUT, f"phase3_windowlength_{a.tag}_preds.csv"), index=False)

rf = res[res.stage == "refit_on_3"]
print("\n=== the curve: refit_on_3, mean / median over 4 folds x seeds ===")
print(rf.groupby(["curve", "window_min"])[["test_R2", "test_RMSE", "test_MAPE"]]
      .agg(["mean", "median"]).round(3).to_string())
print("\nRMSE (%SOH) vs window length, one row per curve:")
print(rf.pivot_table(index="window_min", columns="curve", values="test_RMSE",
                     aggfunc="mean").round(3).to_string())
print("\nR2 vs window length:")
print(rf.pivot_table(index="window_min", columns="curve", values="test_R2",
                     aggfunc="mean").round(3).to_string())
print(f"\ndegenerate fold-seeds: {int(rf.sel_degenerate.sum())} / {len(rf)}")
c5 = pd.read_csv(os.path.join(OUT, "phase3_charge_cpu_results.csv"))
c5.columns = [c.strip() for c in c5.columns]
c7 = c5[(c5.setting == "TD-Clean-7") & (c5.stage == "refit_on_3") & (c5.seed.isin(seeds))]
print(f"\nreference point (full cycle, same 631 rows, same seeds {seeds}): "
      f"TD-Clean-7 mean R2 = {c7.test_R2.mean():.3f}, RMSE = {c7.test_RMSE.mean():.3f} "
      f"(n={len(c7)})")
print("saved")