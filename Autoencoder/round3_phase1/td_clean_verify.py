# Verification + characterisation of the TD-Clean run.
# 1. recompute every metric from the preds dump, and confirm y_true == raw SOH
# 2. paired comparison against TD-Proxy-Free / TD-All on the SAME (fold, seed) cells
# 3. separate "cannot fit the training batteries" from "cannot generalise" via train_R2
# 4. quantify how often the inner-validation selection had no usable signal
import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, r"C:\Master Degree\Thesis\Autoencoder\round3_phase1")
import r3common as R
from r3common import OUT, BATT

REV = {v: k for k, v in BATT.items()}
fails, notes = [], []


def ck(cond, label, detail=""):
    (notes if cond else fails).append(
        f"{'PASS' if cond else 'FAIL'} | {label}{(' | ' + detail) if detail else ''}")
    return cond


rng_span, qref = R.soh_range_and_qref()
X, bids, soh, cyc = R.load_td(R.FEATS_ALL)
soh_by = {BATT[b]: soh[bids == b] for b in [1, 2, 3, 4]}
cyc_by = {BATT[b]: cyc[bids == b] for b in [1, 2, 3, 4]}

cl = pd.read_csv(os.path.join(OUT, "td_clean_cpu_results.csv"))
cp = pd.read_csv(os.path.join(OUT, "td_clean_cpu_preds.csv"))
cl.columns = [c.strip() for c in cl.columns]
cp.columns = [c.strip() for c in cp.columns]

print("=" * 100)
print("[1] structure and metric recomputation")
ck(len(cl) == 80, "80 rows = 2 settings x 2 stages x 4 folds x 5 seeds", str(len(cl)))
ck(set(cl.setting) == {"TD-Clean-6", "TD-Clean-4"}, "both clean settings present")
w = {k: 0.0 for k in ("rmse", "r2", "mape")}
bad = []
for _, r in cl.iterrows():
    g = cp[(cp.setting == r.setting) & (cp.stage == r.stage) & (cp.seed == r.seed)
           & (cp.test_battery == r.test_battery)].sort_values("cycle")
    y, yh = g.y_true.values, g.y_pred.values
    m = np.isin(cyc_by[r.test_battery], g.cycle.values)
    if m.sum() != len(g):
        bad.append((r.setting, r.seed, r.test_battery))
    else:
        w["rmse"] = max(w["rmse"], abs(np.sqrt(np.mean((y - yh) ** 2)) - r.test_RMSE))
        w["r2"] = max(w["r2"], abs((1 - ((y - yh) ** 2).sum() / ((y - y.mean()) ** 2).sum())
                                   - r.test_R2))
        w["mape"] = max(w["mape"], abs(np.mean(np.abs((y - yh) / y)) * 100 - r.test_MAPE))
    if np.abs(g.y_true.values - soh_by[r.test_battery][m]).max() > 1e-9:
        bad.append(("ytrue", r.setting, r.seed, r.test_battery))
ck(not bad, "every block matches the feature file and y_true == raw SOH", str(bad[:3]))
for k, v in w.items():
    ck(v < 5e-4, f"recomputed {k} matches", f"max|diff|={v:.2e}")

print("\n[2] can the model FIT the training batteries? (train_R2, refit_on_3)")
rf = cl[cl.stage == "refit_on_3"]
print(rf.groupby("setting")[["train_R2", "test_R2"]].agg(["mean", "median", "min", "max"]).round(3).to_string())
print("\n  -> if train_R2 is low too, the features are uninformative, not overfitting")
print("\n  worst-fitting fold-seeds (lowest train_R2):")
print(rf.nsmallest(6, "train_R2")[["setting", "seed", "test_battery", "cfg", "sel_epochs",
                                   "train_R2", "test_R2"]].to_string(index=False))

print("\n[3] PAIRED comparison on identical (fold, seed) cells")
lobo = pd.read_csv(os.path.join(OUT, "protocol_gap_exp_cpu_preds.csv"))
lobo.columns = [c.strip() for c in lobo.columns]
lr = pd.read_csv(os.path.join(OUT, "protocol_gap_exp_cpu_results.csv"))
lr.columns = [c.strip() for c in lr.columns]
base = lr[(lr.split == "lobo_nested") & (lr.stage == "refit_on_3")
          & (lr.setting.isin(["TD-All", "TD-Proxy-Free"]))][
    ["setting", "seed", "test_battery", "test_R2", "test_RMSE"]]
clean = rf[["setting", "seed", "test_battery", "test_R2", "test_RMSE"]]
rows = []
for (sd, tb), g in clean.groupby(["seed", "test_battery"]):
    d = {"seed": sd, "test_battery": tb}
    for s in ("TD-All", "TD-Proxy-Free", "TD-Clean-6", "TD-Clean-4"):
        src = base if s in ("TD-All", "TD-Proxy-Free") else clean
        v = src[(src.setting == s) & (src.seed == sd) & (src.test_battery == tb)]
        d[s] = float(v.test_R2.iloc[0]) if len(v) else np.nan
    rows.append(d)
piv = pd.DataFrame(rows).sort_values(["test_battery", "seed"])
piv["PF-C6"] = piv["TD-Proxy-Free"] - piv["TD-Clean-6"]
print(piv.round(3).to_string(index=False))
print("\n  mean drop Proxy-Free -> Clean-6 per fold:")
print(piv.groupby("test_battery")["PF-C6"].mean().round(3).to_string())
ck(int((piv["PF-C6"] > 0).sum()) >= 19,
   "at least 19 of 20 fold-seeds got WORSE when dis_mean_V was removed",
   f"worse in {int((piv['PF-C6'] > 0).sum())}/20, mean drop = {piv['PF-C6'].mean():.3f}")
print(f"\n  overall: TD-Proxy-Free mean R2 {piv['TD-Proxy-Free'].mean():.3f} -> "
      f"TD-Clean-6 {piv['TD-Clean-6'].mean():.3f}  (delta {piv['TD-Clean-6'].mean() - piv['TD-Proxy-Free'].mean():+.3f})")
print(f"  overall: TD-All {piv['TD-All'].mean():.3f} -> TD-Clean-4 {piv['TD-Clean-4'].mean():.3f}"
      f"  (delta {piv['TD-Clean-4'].mean() - piv['TD-All'].mean():+.3f})")

print("\n[4] did the inner validation have any usable signal?")
print(f"  degenerate fold-seeds flagged: {int(rf.sel_degenerate.sum())} / {len(rf)}")
print("  sel_val_rmse (the quantity the selection minimises):")
print(rf.groupby("setting").sel_val_rmse.agg(["min", "median", "max"]).round(2).to_string())
print("  compare: SOH span of the training batteries is ~30-45 %SOH, so a validation RMSE of")
print("  25-45 %SOH means the selection was choosing between candidates that all failed.")

print("\n" + "=" * 100)
for n in notes:
    print(n)
if fails:
    print(f"\n*** {len(fails)} FAILURE(S) ***")
    for f in fails:
        print("  " + f)
else:
    print(f"\nALL {len(notes)} CHECKS PASSED")