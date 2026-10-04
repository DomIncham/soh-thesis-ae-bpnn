# Phase 3, item 5.3: self-referenced normalisation.
# Advisor's plan: divide each feature by the battery's FIRST-CYCLE value. Motivation from the R3-C3
# work: the two capacity proxies were also carrying the per-battery SCALE, and removing them cost
# B0006 0.873 R^2. Self-referencing makes every battery's features start at 1.0, i.e. it removes the
# per-battery offset without using the label (at deploy you have the first cycle, not the capacity).
#
# Why no control group is needed: MinMaxScaler is affine, so dividing every row by the SAME constant
# vector and then MinMax-scaling is IDENTICAL to just MinMax-scaling. A global rescale is therefore a
# provable no-op here, and any effect of this experiment must come from the per-battery (per-row)
# divisor alone. That is exactly the mechanism being tested.
#
# Design notes / limits, measured before running:
#   - no first-cycle value is zero or NaN (min |ref| = 1.9e-4), so the division is safe
#   - reference spread across batteries: cv_I_slope 6.01x, cc_dur 1.27x, dis_V_slope 1.24x,
#     dis_mean_T / cv_dur / ch_mean_T 1.03-1.10x
#   - ic_peak_V's first-cycle value is 4.18 for ALL four batteries (the top of the IC grid), so
#     dividing it is a pure rescale with no per-battery information. Reported as a limitation.
#   - both slope features have all-negative references, so the division does not flip sign for one
#     battery relative to another.
# Same 631-row subset as the 5.1 run (5 cycles have no usable CC phase), same folds, same seeds,
# and run_fold itself is reused unchanged, so the protocol is identical by construction.
# Usage: python phase3_selfref_run.py [--seeds 42,7,123,2024,11] [--device cpu]
import argparse
import os
import numpy as np
import pandas as pd
import r3common as R
from r3common import BATT, load_td, soh_range_and_qref, run_fold, OUT

SETS = {"TD-Clean-6": [],
        "TD-Clean-7": ["ic_peak_V"],
        "TD-Clean-8": ["t_40_41", "ic_peak_V"]}

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
tdf = pd.read_csv(R.TD_CSV)
tdf.columns = [c.strip() for c in tdf.columns]
assert np.array_equal(ch.battery.values, tdf.battery.values) and \
       np.array_equal(ch.cycle.values, tdf.cycle.values), "ALIGNMENT: charge_features.csv mismatch"

used = sorted({f for v in SETS.values() for f in v})
mask = np.isfinite(ch[used].values).all(axis=1)
print(f"rows kept: {int(mask.sum())} / {len(ch)}")

base6, bids, soh, cyc = load_td(R.FEATS_CLEAN6)
bids, soh, cyc = bids[mask], soh[mask], cyc[mask]
base6 = base6[mask]

rows, preds = [], []
for name, extra in SETS.items():
    feats = R.FEATS_CLEAN6 + extra
    X = base6 if not extra else np.hstack([base6, ch.loc[mask, extra].values.astype(float)])

    # ---- self-referenced divisor: the battery's own first cycle, per feature ----
    D = pd.DataFrame(X, columns=feats)
    D.insert(0, "battery", bids)
    first = D.groupby("battery").head(1).set_index("battery")[feats]
    div = first.loc[bids].values
    assert np.isfinite(div).all() and (np.abs(div) > 1e-12).all(), "unsafe first-cycle reference"
    Xn = X / div
    assert np.isfinite(Xn).all(), "non-finite feature matrix after normalisation"
    chk = pd.DataFrame(Xn, columns=feats)
    chk.insert(0, "battery", bids)
    f1 = chk.groupby("battery").head(1)[feats].values
    assert np.allclose(f1, 1.0), "each battery's first cycle should normalise to exactly 1.0"
    print(f"\n--- {name} + self-ref: {Xn.shape[1]} features; "
          f"first-cycle values per battery all == 1.0")

    for seed in seeds:
        for b in [1, 2, 3, 4]:
            r, p = run_fold(Xn, bids, soh, cyc, b, seed, 500, 30, qref, rng_span, name)
            rows += r
            preds.append(p)
            ref = [x for x in r if x["stage"] == "refit_on_3"][0]
            print(f"{name:12s} seed{seed:<5d} test={BATT[b]} cfg={ref['cfg']} ep={ref['sel_epochs']} "
                  f"| R2={ref['test_R2']:+.3f} RMSE={ref['test_RMSE']:.3f}")

res = pd.DataFrame(rows)
res["device"] = R.DEVICE.type
res.to_csv(os.path.join(OUT, f"phase3_selfref_{a.tag}_results.csv"), index=False)
pd.concat(preds, ignore_index=True).to_csv(
    os.path.join(OUT, f"phase3_selfref_{a.tag}_preds.csv"), index=False)

cols = ["test_MAE", "test_RMSE", "test_R2", "test_MAPE", "test_RMSE_Ah"]
rf = res[res.stage == "refit_on_3"]
print("\n=== refit_on_3, mean / median / std over 4 folds x seeds ===")
print(rf.groupby("setting")[cols].agg(["mean", "median", "std"]).round(3).to_string())
print("\ntest_R2 per fold (mean over seeds):")
print(rf.pivot_table(index="test_battery", columns="setting", values="test_R2",
                     aggfunc="mean").round(3).to_string())
print(f"\ndegenerate fold-seeds: {int(rf.sel_degenerate.sum())} / {len(rf)}")
print("\nUNNORMALISED reference on the same 631 rows (5.1 run): "
      "Clean-6 0.664 | Clean-7 0.772 | Clean-8 0.810")
print("saved")