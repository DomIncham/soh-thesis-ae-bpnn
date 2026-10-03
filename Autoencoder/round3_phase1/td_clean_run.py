# R3-C3 follow-up: measure the truly proxy-free feature sets under the same nested LOBO protocol.
# TD-Proxy-Free dropped dis_duration only, but dis_mean_V is collinear with it (within-battery
# r = 0.941) and alone explains 94.8% of within-battery capacity variance, so the capacity proxy was
# still in the input under another name. These two sets remove it, then the borderline charge-side
# duration pair as well. Same folds, same seeds, same grid, same leakage discipline as Phase 1/2.
# Usage: python td_clean_run.py [--seeds 42,7,123,2024,11] [--device cpu] [--tag cpu]
import argparse
import os
import pandas as pd
import r3common as R
from r3common import BATT, load_td, soh_range_and_qref, run_fold, OUT

SETS = {"TD-Clean-6": R.FEATS_CLEAN6, "TD-Clean-4": R.FEATS_CLEAN4}

ap = argparse.ArgumentParser()
ap.add_argument("--seeds", default="42,7,123,2024,11")
ap.add_argument("--device", default="cpu", choices=["cpu", "cuda", "auto"])
ap.add_argument("--tag", default="cpu")
a = ap.parse_args()

R.set_device(a.device)
seeds = [int(s) for s in a.seeds.split(",")]
rng_span, qref = soh_range_and_qref()
rows, preds = [], []
for name, feats in SETS.items():
    X, bids, soh, cyc = load_td(feats)
    print(f"\n--- {name}: {len(feats)} features {feats}")
    for seed in seeds:
        for b in [1, 2, 3, 4]:
            r, p = run_fold(X, bids, soh, cyc, b, seed, 500, 30, qref, rng_span, name)
            rows += r
            preds.append(p)
            ref = [x for x in r if x["stage"] == "refit_on_3"][0]
            print(f"{name:12s} seed{seed:<5d} test={BATT[b]} cfg={ref['cfg']} ep={ref['sel_epochs']} "
                  f"| R2={ref['test_R2']:+.3f} RMSE={ref['test_RMSE']:.3f}")

res = pd.DataFrame(rows)
res["device"] = R.DEVICE.type
res.to_csv(os.path.join(OUT, f"td_clean_{a.tag}_results.csv"), index=False)
pd.concat(preds, ignore_index=True).to_csv(
    os.path.join(OUT, f"td_clean_{a.tag}_preds.csv"), index=False)

cols = ["test_MAE", "test_RMSE", "test_R2", "test_MAPE", "test_RMSE_Ah"]
rf = res[res.stage == "refit_on_3"]
print("\n=== refit_on_3, mean / median / std over 4 folds x seeds ===")
print(rf.groupby("setting")[cols].agg(["mean", "median", "std"]).round(3).to_string())
print("\ntest_R2 per fold (mean over seeds):")
print(rf.pivot_table(index="test_battery", columns="setting", values="test_R2",
                     aggfunc="mean").round(3).to_string())
print("\ndegenerate fold-seeds:", int(rf.sel_degenerate.sum()), "/", len(rf))
print("saved")