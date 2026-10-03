# Phase 1 audit: recompute every published number from the raw artifacts and compare with the
# committed summaries. Read-only. Purpose is to find bugs, not to restate the results.
#
# Checks: row counts, no NaN, fold coverage, test-battery never inside fit-batteries, predictions
# match the feature file cycle-for-cycle, nRMSE / RMSE(Ah) formulas, independent recompute of
# mean/median/std, independent recompute of pooled R2, TD-All identical across the two scripts,
# the log file against the CSV, and every per-fold-seed R2 sign.
import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, r"C:\Master Degree\Thesis\Autoencoder\round3_phase1")
import r3common as R
from r3common import OUT, BATT

REV = {v: k for k, v in BATT.items()}
fails, warns, notes = [], [], []


def ck(cond, label, detail=""):
    (notes if cond else fails).append(f"{'PASS' if cond else 'FAIL'} | {label}{(' | ' + detail) if detail else ''}")
    return cond


def near(a, b, tol=1e-3):
    return abs(float(a) - float(b)) <= tol


print("=" * 100)
print("PHASE 1 AUDIT")
print("=" * 100)

# ---------------------------------------------------------------- 0. inputs
rng_span, qref = R.soh_range_and_qref()
X, bids, soh, cyc = R.load_td(R.FEATS_ALL)
n_per = {BATT[b]: int((bids == b).sum()) for b in [1, 2, 3, 4]}
print(f"\n[0] raw data: {len(bids)} cycles, per battery {n_per}, total {sum(n_per.values())}")
ck(sum(n_per.values()) == 636, "raw cycle count = 636", str(n_per))

ref = pd.read_csv(os.path.join(OUT, "steps14_16_refit_cpu_results.csv"))
prx = pd.read_csv(os.path.join(OUT, "td_proxy_audit_cpu_results.csv"))
rpred = pd.read_csv(os.path.join(OUT, "steps14_16_refit_cpu_preds.csv"))
ppred = pd.read_csv(os.path.join(OUT, "td_proxy_audit_cpu_preds.csv"))
pool = pd.read_csv(os.path.join(OUT, "phase1_pooled_metrics.csv"))
for d in (ref, prx, rpred, ppred, pool):
    d.columns = [c.strip() for c in d.columns]

# ---------------------------------------------------------------- 1. shape + NaN
print("\n[1] shape and NaN")
ck(len(ref) == 24, "refit results = 24 rows (1 setting x 2 stages x 4 folds x 3 seeds)", str(len(ref)))
ck(len(prx) == 72, "proxy results = 72 rows (3 settings x 2 stages x 4 folds x 3 seeds)", str(len(prx)))
ck(len(rpred) == 3816, "refit preds = 3816 rows", str(len(rpred)))
ck(len(ppred) == 11448, "proxy preds = 11448 rows", str(len(ppred)))
for nm, d in (("refit_results", ref), ("proxy_results", prx), ("refit_preds", rpred),
              ("proxy_preds", ppred), ("pooled", pool)):
    ck(not d.isna().any().any(), f"no NaN in {nm}",
       str(d.columns[d.isna().any()].tolist()) if d.isna().any().any() else "")

# ---------------------------------------------------------------- 2. fold coverage + fit batteries
print("\n[2] fold coverage and test/fit separation")
for nm, d in (("refit", ref), ("proxy", prx)):
    for (s, st, sd), g in d.groupby(["setting", "stage", "seed"]):
        ok = set(g.test_battery) == set(BATT.values()) and len(g) == 4
        ck(ok, f"{nm} {s}/{st}/seed{sd} covers all 4 folds exactly once", str(sorted(g.test_battery)))
bad_fit = []
for _, r in prx.iterrows():
    if r.test_battery in str(r.fit_batteries):
        bad_fit.append((r.setting, r.stage, r.seed, r.test_battery, r.fit_batteries))
ck(not bad_fit, "no proxy row has the test battery inside fit_batteries", str(bad_fit[:3]))
nfit = {st: {len(eval(fb)) for fb in g.fit_batteries} for st, g in prx.groupby("stage")}
ck(nfit["pre_refit"] == {2}, "pre_refit fits on exactly 2 batteries", str(nfit["pre_refit"]))
ck(nfit["refit_on_3"] == {3}, "refit_on_3 fits on exactly 3 batteries", str(nfit["refit_on_3"]))

# ---------------------------------------------------------------- 3. preds match the feature file
print("\n[3] predictions trace back to the raw feature file")
soh_by = {BATT[b]: soh[bids == b] for b in [1, 2, 3, 4]}
cyc_by = {BATT[b]: cyc[bids == b] for b in [1, 2, 3, 4]}
for nm, d, nstage in (("refit", rpred, 2), ("proxy", ppred, 6)):
    miss, order_bad = [], []
    for (s, st, sd, tb), g in d.groupby(["setting", "stage", "seed", "test_battery"]):
        want_cyc = cyc_by[tb]
        if len(g) != len(want_cyc):
            miss.append((s, st, sd, tb, len(g), len(want_cyc)))
        elif not np.array_equal(np.sort(g.cycle.values), np.sort(want_cyc)):
            order_bad.append((s, st, sd, tb))
    ck(not miss, f"{nm}: every (setting,stage,seed,battery) block has the right row count", str(miss[:3]))
    ck(not order_bad, f"{nm}: cycle sets match the feature file", str(order_bad[:3]))

# y_true must equal the raw per-battery SOH
worst_yt = 0.0
for (s, st, sd, tb), g in ppred.groupby(["setting", "stage", "seed", "test_battery"]):
    g2 = g.sort_values("cycle")
    m = np.isin(cyc_by[tb], g2.cycle.values)
    worst_yt = max(worst_yt, float(np.abs(g2.y_true.values - soh_by[tb][m]).max()))
ck(worst_yt < 1e-9, "y_true == raw SOH of the test battery, cycle-for-cycle", f"max|diff|={worst_yt:.2e}")

# the split must not depend on the setting: same cycles for the same (stage,seed,battery)
split_shifts = []
for (st, sd, tb), g in ppred.groupby(["stage", "seed", "test_battery"]):
    if g.setting.nunique() != 3:
        split_shifts.append((st, sd, tb))
    else:
        sets = {s: tuple(sorted(gg.cycle)) for s, gg in g.groupby("setting")}
        if len(set(sets.values())) != 1:
            split_shifts.append((st, sd, tb))
ck(not split_shifts, "all 3 settings see the identical test split", str(split_shifts[:3]))

# ---------------------------------------------------------------- 4. metric formulas
print("\n[4] metric definitions recomputed")
worst_rmse, worst_r2, worst_mape, worst_ah, worst_nrmse = 0.0, 0.0, 0.0, 0.0, 0.0
for _, r in prx.iterrows():
    g = ppred[(ppred.setting == r.setting) & (ppred.stage == r.stage) & (ppred.seed == r.seed)
              & (ppred.test_battery == r.test_battery)]
    y, yh = g.y_true.values, g.y_pred.values
    rmse = float(np.sqrt(np.mean((y - yh) ** 2)))
    r2 = 1 - ((y - yh) ** 2).sum() / ((y - y.mean()) ** 2).sum()
    mape = float(np.mean(np.abs((y - yh) / y)) * 100)
    bad = REV[r.test_battery]
    worst_rmse = max(worst_rmse, abs(rmse - r.test_RMSE))
    worst_r2 = max(worst_r2, abs(r2 - r.test_R2))
    worst_mape = max(worst_mape, abs(mape - r.test_MAPE))
    worst_ah = max(worst_ah, abs(rmse / 100 * qref.loc[bad] - r.test_RMSE_Ah))
    worst_nrmse = max(worst_nrmse, abs(rmse / rng_span.loc[bad] - r.test_nRMSE))
ck(worst_rmse < 5e-4, "test_RMSE = RMSE(pred, true) from the preds dump", f"max|diff|={worst_rmse:.2e}")
ck(worst_r2 < 5e-4, "test_R2 = 1 - SSres/SStot on the outer battery only", f"max|diff|={worst_r2:.2e}")
ck(worst_mape < 5e-3, "test_MAPE = mean|(y-yh)/y|*100", f"max|diff|={worst_mape:.2e}")
ck(worst_ah < 5e-4, "test_RMSE_Ah = RMSE/100 * Qref(battery)", f"max|diff|={worst_ah:.2e}")
ck(worst_nrmse < 5e-4, "test_nRMSE = RMSE / per-battery SOH span", f"max|diff|={worst_nrmse:.2e}")

# ---------------------------------------------------------------- 5. summaries recomputed
print("\n[5] summary CSVs recomputed independently")
s1 = pd.read_csv(os.path.join(OUT, "steps14_16_refit_summary_cpu.csv"), header=[0, 1], index_col=[0, 1])
cols = ["test_MAE", "test_RMSE", "test_R2", "test_MAPE", "test_RMSE_Ah", "test_nRMSE"]
mine = ref.groupby(["setting", "stage"])[cols].agg(["mean", "median", "std"]).round(3)
worst = float(np.abs(mine.values - s1[cols].values).max())
ck(worst < 1e-9, "refit summary == recomputed mean/median/std", f"max|diff|={worst:.2e}")
s2 = pd.read_csv(os.path.join(OUT, "td_proxy_audit_summary_cpu.csv"), header=[0, 1], index_col=0)
c2 = ["test_MAE", "test_RMSE", "test_R2", "test_MAPE", "test_RMSE_Ah"]
rf = prx[prx.stage == "refit_on_3"]
mine2 = rf.groupby("setting")[c2].agg(["mean", "median", "std"]).round(3)
worst = float(np.abs(mine2.values - s2[c2].values).max())
ck(worst < 1e-9, "proxy summary == recomputed mean/median/std", f"max|diff|={worst:.2e}")

# ---------------------------------------------------------------- 6. pooled R2 recomputed
print("\n[6] pooled metrics recomputed")
worst_r2p, worst_n = 0.0, []
ps = pool[pool.scope == "per_seed_pooled_4_folds"]
for _, r in ps.iterrows():
    src = rpred if "refit" in r.source else ppred
    stg = r.stage
    g = src[(src.setting == r.setting) & (src.stage == stg) & (src.seed == r.seed)]
    y, yh = g.y_true.values, g.y_pred.values
    if len(y) != r.n:
        worst_n.append((r.source, r.setting, stg, r.seed, len(y), r.n))
    r2p = 1 - ((y - yh) ** 2).sum() / ((y - y.mean()) ** 2).sum()
    worst_r2p = max(worst_r2p, abs(r2p - r.pooled_R2))
ck(not worst_n, "pooled block sizes match the preds dumps", str(worst_n[:3]))
ck(worst_r2p < 5e-4, "pooled_R2 == recomputed over the 4 concatenated folds",
   f"max|diff|={worst_r2p:.2e}")
gn = pool[pool.scope == "grand_pooled_all_seeds"]
ck(set(gn.n) == {1908}, "grand pooled n = 1908 = 3 seeds x 636 cycles", str(sorted(set(gn.n))))

# ---------------------------------------------------------------- 7. TD-All identical across scripts
print("\n[7] internal consistency: TD-All in both scripts")
a = ref[["stage", "seed", "test_battery", "cfg", "sel_epochs", "train_R2",
         "test_RMSE", "test_R2", "test_MAPE", "test_nRMSE", "test_RMSE_Ah"]]
b = prx[prx.setting == "TD-All"][a.columns]
m = a.merge(b, on=["stage", "seed", "test_battery"], suffixes=("_ref", "_prx"))
worst = 0.0
for c in a.columns:
    if c in ("stage", "seed", "test_battery"):
        continue
    if c in ("cfg",):
        worst = max(worst, float((m[f"{c}_ref"].astype(str) != m[f"{c}_prx"].astype(str)).sum()))
    else:
        worst = max(worst, float(np.abs(m[f"{c}_ref"].astype(float) - m[f"{c}_prx"].astype(float)).max()))
ck(worst < 1e-9, "TD-All rows byte-identical between the refit script and the audit script",
   f"max|diff|={worst:.2e} (24 fold-stages)")

# ---------------------------------------------------------------- 8. log file vs CSV
print("\n[8] refit_full.log against the results CSV")
lines = [l.strip() for l in open(os.path.join(OUT, "refit_full.log")) if l.startswith("seed")]
ck(len(lines) == 12, "log has 12 fold-seed lines", str(len(lines)))
worst = 0.0
for l in lines:
    head, tail = l.split("|", 1)
    sd = int(head.split("seed")[1].split()[0])
    tb = head.split("test=")[1].split()[0]
    val = float(tail.split("refit_on_3 R2=")[1].split()[0])
    row = ref[(ref.seed == sd) & (ref.test_battery == tb) & (ref.stage == "refit_on_3")]
    worst = max(worst, abs(val - float(row.test_R2.iloc[0])))
ck(worst < 5e-4, "every log R2 matches the CSV", f"max|diff|={worst:.2e}")

# ---------------------------------------------------------------- 9. sign + spread
print("\n[9] per-fold-seed R2 signs")
for nm, d in (("TD-All", ref), ("TD-Proxy-Free", prx[prx.setting == "TD-Proxy-Free"]),
              ("Oracle-proxy", prx[prx.setting == "Oracle-proxy"])):
    rr = d[d.stage == "refit_on_3"]
    ck(bool((rr.test_R2 > 0).all()), f"{nm}: all 12 fold-seed R2 positive",
       f"min={rr.test_R2.min():+.4f}")
print("\n[9b] per-fold mean R2, refit_on_3")
piv = prx[prx.stage == "refit_on_3"].pivot_table(index="test_battery", columns="setting",
                                                 values="test_R2", aggfunc="mean").round(3)
print(piv.to_string())
refpiv = ref[ref.stage == "refit_on_3"].groupby("test_battery").test_R2.mean().round(3)
print(refpiv.to_string())
b6 = refpiv.loc["B0006"]
ck(near(b6, 0.900, 5e-3), "B0006 fold mean R2 == 0.900 (the claimed improvement)", f"{b6:.4f}")

# ---------------------------------------------------------------- 10. probe scope
print("\n[10] leakage probe scope")
pl = open(os.path.join(OUT, "probe_s14b.log"), encoding="utf-8", errors="replace").read()
ck("max|diff| = 0.00e+00" in pl and "PASS" in pl, "probe_s14b.log verdict PASS")
notes.append("NOTE | probe covers fold B0005/seed42 only, at a reduced epoch budget (BP_MAX=100, "
             "PAT=10); it is not a whole-suite proof")
notes.append("NOTE | the pre_refit stage is fitted on 2 batteries by design - it is the Round 2 "
             "protocol kept for comparison, not a bug")

# ---------------------------------------------------------------- report
print("\n" + "=" * 100)
print("RESULT")
print("=" * 100)
for n in notes:
    if not n.startswith("NOTE"):
        print(n)
print()
for w in warns:
    print(w)
if fails:
    print(f"\n*** {len(fails)} FAILURE(S) ***")
    for f in fails:
        print("  " + f)
else:
    print(f"\nALL {len([n for n in notes if n.startswith('PASS')])} CHECKS PASSED")
print("\nNotes / limitations:")
for n in notes:
    if n.startswith("NOTE"):
        print("  " + n)
