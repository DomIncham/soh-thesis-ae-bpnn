# Phase 2 audit: completeness, leakage structure, metric formulas, and the regression check that the
# lobo_nested split inside protocol_gap_exp.py reproduces the committed Phase 1 numbers exactly.
import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, r"C:\Master Degree\Thesis\Autoencoder\round3_phase1")
import r3common as R
from r3common import OUT, BATT

REV = {v: k for k, v in BATT.items()}
notes, fails = [], []


def ck(cond, label, detail=""):
    (notes if cond else fails).append(
        f"{'PASS' if cond else 'FAIL'} | {label}{(' | ' + detail) if detail else ''}")
    return cond


rng_span, qref = R.soh_range_and_qref()
X, bids, soh, cyc = R.load_td(R.FEATS_ALL)
soh_by = {BATT[b]: soh[bids == b] for b in [1, 2, 3, 4]}
cyc_by = {BATT[b]: cyc[bids == b] for b in [1, 2, 3, 4]}

g = pd.read_csv(os.path.join(OUT, "protocol_gap_exp_cpu_results.csv"))
p = pd.read_csv(os.path.join(OUT, "protocol_gap_exp_cpu_preds.csv"))
g.columns = [c.strip() for c in g.columns]
p.columns = [c.strip() for c in p.columns]
old = pd.read_csv(os.path.join(OUT, "td_proxy_audit_cpu_results.csv"))
old.columns = [c.strip() for c in old.columns]

print("=" * 100)
print("PHASE 2 AUDIT")
print("=" * 100)

print("\n[1] completeness")
print(g.groupby(["split", "setting"]).size().unstack().to_string())
seeds = sorted(g.seed.unique())
ck(set(seeds) == {7, 42, 123, 2024, 11}, "5 seeds present (F3: 2024 and 11 are new)", str(seeds))
ck(set(g.split) == {"lobo_nested", "random_within", "chronological_within", "random_pooled"},
   "all 4 splits present", str(sorted(set(g.split))))
ck(set(g.setting) == {"TD-All", "TD-Proxy-Free", "Oracle-proxy"}, "all 3 settings present")
metric_cols = ["test_MAE", "test_RMSE", "test_R2", "test_MAPE", "test_RMSE_Ah",
               "test_nRMSE", "train_RMSE", "train_R2", "sel_epochs", "sel_val_rmse"]
ck(not g[metric_cols].isna().any().any(), "no NaN in any metric column",
   str(g[metric_cols].columns[g[metric_cols].isna().any()].tolist())
   if g[metric_cols].isna().any().any() else "")
# n_train / n_val are only defined for the split-based protocols (LOBO's fitting set differs per
# stage), so NaN there is by design, not a defect.
ck(g[g.split != "lobo_nested"][["n_train", "n_val", "n_test"]].notna().all().all(),
   "n_train/n_val/n_test populated for every split-based block")
ck(g[g.split == "lobo_nested"][["n_train", "n_val"]].isna().all().all(),
   "n_train/n_val are NaN for lobo_nested by design (its fitting set differs per stage)")
ck(not p.isna().any().any(), "no NaN in preds")
lobo = g[g.split == "lobo_nested"]
ck(set(lobo.stage) == {"pre_refit", "refit_on_3"}, "lobo_nested keeps both stages")
ck(set(g[g.split != "lobo_nested"].stage) == {"fit"}, "the new splits have a single stage")
n_lobo = lobo.groupby(["setting", "seed"]).size()
ck(set(n_lobo) == {8}, "lobo_nested: 4 folds x 2 stages per (setting, seed)", str(sorted(set(n_lobo))))

print("\n[2] split structure")
for sp in ("random_within", "chronological_within", "random_pooled"):
    s = g[g.split == sp]
    frac_ok, blocks = True, set()
    for _, r in s.iterrows():
        n = r.n_train + r.n_val + r.n_test
        want = 636 if r.test_battery == "pooled" else int((bids == REV[r.test_battery]).sum())
        if n != want:
            frac_ok = False
        if not (0.68 < r.n_train / n < 0.72 and 0.08 < r.n_val / n < 0.12
                and 0.18 < r.n_test / n < 0.22):
            frac_ok = False
        blocks.add(r.test_battery)
    ck(frac_ok, f"{sp}: 70/10/20 partition covers every cycle exactly once")
    print(f"    {sp:20s} blocks = {sorted(blocks)}")
# masks must partition: preds test cycles for a block must not include any train cycle
s = g[g.split == "random_within"].iloc[0]
pr = p[(p.split == "random_within") & (p.setting == s.setting) & (p.seed == s.seed)
       & (p.test_battery == s.test_battery)]
ck(len(pr) == s.n_test, "preds row count == n_test for a sampled block",
   f"{len(pr)} vs {s.n_test}")

print("\n[3] predictions trace to the raw feature file")
worst, bad = 0.0, []
for (sp, se, st, sd, tb), gg in p.groupby(["split", "setting", "stage", "seed", "test_battery"]):
    if tb == "pooled":
        continue
    gg = gg.sort_values("cycle")
    m = np.isin(cyc_by[tb], gg.cycle.values)
    if m.sum() != len(gg):
        bad.append((sp, st, sd, tb))
    else:
        worst = max(worst, float(np.abs(gg.y_true.values - soh_by[tb][m]).max()))
ck(not bad, "every per-battery block matches the feature file row-for-row", str(bad[:3]))
ck(worst < 1e-9, "y_true == raw SOH", f"max|diff|={worst:.2e}")

print("\n[4] metric formulas recomputed (all 4 splits)")
ALL_B = [1, 2, 3, 4]
w = {k: 0.0 for k in ("rmse", "r2", "mape", "ah")}
for _, r in g.iterrows():
    gg = p[(p.split == r.split) & (p.setting == r.setting) & (p.stage == r.stage)
           & (p.seed == r.seed) & (p.test_battery == r.test_battery)]
    y, yh = gg.y_true.values, gg.y_pred.values
    rmse = float(np.sqrt(np.mean((y - yh) ** 2)))
    r2 = 1 - ((y - yh) ** 2).sum() / ((y - y.mean()) ** 2).sum()
    mape = float(np.mean(np.abs((y - yh) / y)) * 100)
    q = (float(qref.loc[ALL_B].mean()) if r.test_battery == "pooled"
         else float(qref.loc[REV[r.test_battery]]))
    w["rmse"] = max(w["rmse"], abs(rmse - r.test_RMSE))
    w["r2"] = max(w["r2"], abs(r2 - r.test_R2))
    w["mape"] = max(w["mape"], abs(mape - r.test_MAPE))
    w["ah"] = max(w["ah"], abs(rmse / 100 * q - r.test_RMSE_Ah))
for k, v in w.items():
    ck(v < 5e-4, f"recomputed {k} matches every row", f"max|diff|={v:.2e}")

print("\n[5] REGRESSION: lobo_nested must reproduce the committed Phase 1 numbers exactly")
cols = ["setting", "stage", "seed", "test_battery", "cfg", "sel_epochs", "train_R2",
        "test_RMSE", "test_R2", "test_MAPE", "test_nRMSE"]
a = old[cols].copy()
b = lobo[lobo.seed.isin([42, 7, 123])][cols].copy()
m = a.merge(b, on=["setting", "stage", "seed", "test_battery"], suffixes=("_p1", "_p2"))
ck(len(m) == 72, "72 fold-stages matched between Phase 1 and Phase 2 lobo_nested", str(len(m)))
worst = 0.0
for c in cols:
    if c in ("setting", "stage", "seed", "test_battery"):
        continue
    if c == "cfg":
        worst = max(worst, float((m.cfg_p1.astype(str) != m.cfg_p2.astype(str)).sum()))
    else:
        worst = max(worst, float(np.abs(m[f"{c}_p1"].astype(float) - m[f"{c}_p2"].astype(float)).max()))
ck(worst < 1e-9, "lobo_nested bit-identical to the committed Phase 1 audit", f"max|diff|={worst:.2e}")

print("\n[6] advisor expectation R3-C2: random split should reach R2 > 0.97")
rf = g[g.stage.isin(["refit_on_3", "fit"])]
piv = rf.pivot_table(index="split", columns="setting", values="test_R2", aggfunc="mean").round(3)
print(piv.to_string())
med = rf.pivot_table(index="split", columns="setting", values="test_R2", aggfunc="median").round(3)
print("\nmedians:")
print(med.to_string())
rw = float(piv.loc["random_within", "TD-All"])
ck(rw > 0.97, "R3-C2 expectation met: random split TD-All R2 > 0.97", f"got {rw:.3f}")
orc = piv["Oracle-proxy"]
print("\nOracle-proxy per split (the advisor expects ~1; measured LOBO 0.663):")
print(orc.to_string())

print("\n[7] per-fold R2, all splits, TD-All")
kk = rf[(rf.setting == "TD-All") & (rf.split == "lobo_nested")]
print(kk.pivot_table(index="test_battery", values="test_R2", aggfunc="mean").round(3).to_string())
print("\ndegenerate blocks per split:")
print(g.groupby("split").sel_degenerate.agg(["sum", "count"]).to_string())

print("\n" + "=" * 100)
for n in notes:
    print(n)
if fails:
    print(f"\n*** {len(fails)} FAILURE(S) ***")
    for f in fails:
        print("  " + f)
else:
    print(f"\nALL {len(notes)} CHECKS PASSED")