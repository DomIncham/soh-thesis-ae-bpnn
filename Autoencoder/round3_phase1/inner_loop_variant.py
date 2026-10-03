# Advisor audit 5-A, alternative protocol: "make the inner loop a 3-fold LOBO".
# Compares the current fixed single-battery inner validation (inner="single", the Phase 1 headline)
# against the rotated 3-fold inner LOBO (inner="lobo3") on the SAME outer folds, seeds and grid.
# Only the inner selection changes; the outer test battery never enters any fit in either variant.
# Writes its own tagged outputs so the committed Phase 1 files stay untouched.
# Usage: python inner_loop_variant.py [--inner single|lobo3] [--seeds 42,7,123] [--device cpu]
import argparse
import os
import pandas as pd
import r3common as R
from r3common import BATT, FEATS_ALL, load_td, soh_range_and_qref, run_fold, OUT

ap = argparse.ArgumentParser()
ap.add_argument("--inner", default="lobo3", choices=["single", "lobo3"])
ap.add_argument("--seeds", default="42,7,123")
ap.add_argument("--device", default="cpu", choices=["cpu", "cuda", "auto"])
a = ap.parse_args()

R.set_device(a.device)
seeds = [int(s) for s in a.seeds.split(",")]
X, bids, soh, cyc = load_td(FEATS_ALL)
rng_span, qref = soh_range_and_qref()
rows, preds = [], []
for seed in seeds:
    for b in [1, 2, 3, 4]:
        r, p = run_fold(X, bids, soh, cyc, b, seed, 500, 30, qref, rng_span, "TD-All", inner=a.inner)
        rows += r
        preds.append(p)
        ref = [x for x in r if x["stage"] == "refit_on_3"][0]
        print(f"seed{seed} test={BATT[b]} cfg={ref['cfg']} sel_epochs={ref['sel_epochs']} | "
              f"R2={ref['test_R2']:+.3f} RMSE={ref['test_RMSE']:.3f}")

res = pd.DataFrame(rows)
res["device"] = R.DEVICE.type
res.to_csv(os.path.join(OUT, f"inner_loop_{a.inner}_results.csv"), index=False)
pd.concat(preds, ignore_index=True).to_csv(
    os.path.join(OUT, f"inner_loop_{a.inner}_preds.csv"), index=False)

cols = ["test_MAE", "test_RMSE", "test_R2", "test_MAPE", "test_RMSE_Ah"]
rf = res[res.stage == "refit_on_3"]
print(f"\n=== inner={a.inner}: refit_on_3, mean / median / std over 4 folds x {len(seeds)} seeds ===\n")
print(rf[cols].agg(["mean", "median", "std"]).round(3).to_string())
print("\ntest_R2 per fold (mean over seeds):")
print(rf.groupby("test_battery").test_R2.mean().round(3).to_string())
print("saved")