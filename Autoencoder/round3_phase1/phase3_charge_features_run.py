# Phase 3, item 5.1 run: does a genuinely proxy-free addition help?
# TD-Clean-6 scores 0.490 (median 0.556) under nested LOBO. The ridge probe showed the ceiling is a
# FEATURE limit, not a model limit. This adds only features that passed the same proxy rule used for
# the original eight (within-battery R^2 vs capacity < 0.90):
#   ic_peak_V  0.489  SAFE (just under the 0.50 borderline line)  ICA peak position
#   t_40_41    0.341  SAFE                                        CC-charge time in 4.0-4.1 V
#   ic_peak_h  0.906  PROXY        -> rejected
#   t_39_40    0.716  BORDERLINE   -> rejected
#   cc_dTdt 0.394 / cc_V_slope 0.479  SAFE but NaN on the same 5 cycles and 1e-4..1e-3 magnitude
#
# Five cycles (B0005/06/07 cycle 86, B0018 cycles 117 and 141 - all early life, SOH 90.9-100.6) have
# no usable CC phase, so ic_peak_V is NaN there. Rather than impute (which would either leak or need
# per-fold machinery) those rows are dropped and the TD-Clean-6 REFERENCE is re-run on exactly the
# same subset, so every comparison below is apples-to-apples on identical rows and seeds.
# Usage: python phase3_charge_features_run.py [--seeds 42,7,123,2024,11] [--device cpu]
import argparse
import os
import numpy as np
import pandas as pd
import r3common as R
from r3common import BATT, load_td, soh_range_and_qref, run_fold, OUT

SETS = {"TD-Clean-6*": [],                              # reference: same rows, same seeds
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
       np.array_equal(ch.cycle.values, tdf.cycle.values), \
    "ALIGNMENT: charge_features.csv rows do not match time_domain_features.csv"

used = sorted({f for v in SETS.values() for f in v})
mask = np.isfinite(ch[used].values).all(axis=1)
print(f"rows kept: {int(mask.sum())} / {len(ch)}  (dropped {int((~mask).sum())}: no usable CC phase)")
print(f"dropped (battery, cycle): {ch.loc[~mask, ['battery', 'cycle']].values.tolist()}")

Xb, bids, soh, cyc = load_td(R.FEATS_CLEAN6)
bids, soh, cyc = bids[mask], soh[mask], cyc[mask]
Xb = Xb[mask]

rows, preds = [], []
for name, extra in SETS.items():
    X = Xb if not extra else np.hstack([Xb, ch.loc[mask, extra].values.astype(float)])
    assert np.isfinite(X).all(), "NaN in the feature matrix"
    print(f"\n--- {name}: {X.shape[1]} features"
          + (f" = CLEAN6 + {extra}" if extra else " (reference on the same rows)"))
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
res.to_csv(os.path.join(OUT, f"phase3_charge_{a.tag}_results.csv"), index=False)
pd.concat(preds, ignore_index=True).to_csv(
    os.path.join(OUT, f"phase3_charge_{a.tag}_preds.csv"), index=False)

cols = ["test_MAE", "test_RMSE", "test_R2", "test_MAPE", "test_RMSE_Ah"]
rf = res[res.stage == "refit_on_3"]
print("\n=== refit_on_3, mean / median / std over 4 folds x seeds ===")
print(rf.groupby("setting")[cols].agg(["mean", "median", "std"]).round(3).to_string())
print("\ntest_R2 per fold (mean over seeds):")
print(rf.pivot_table(index="test_battery", columns="setting", values="test_R2",
                     aggfunc="mean").round(3).to_string())
print(f"\ndegenerate fold-seeds: {int(rf.sel_degenerate.sum())} / {len(rf)}")
print("reference: TD-Clean-6 mean 0.490 / median 0.556 (same protocol, same 5 seeds)")
print("saved")