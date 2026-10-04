# Verification for the Phase 3.5 window-length run.
import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, r"C:\Master Degree\Thesis\Autoencoder\round3_phase1")
import r3common as R
from r3common import OUT, BATT

fails, notes = [], []


def ck(cond, label, detail=""):
    (notes if cond else fails).append(
        f"{'PASS' if cond else 'FAIL'} | {label}{(' | ' + detail) if detail else ''}")
    return cond


rng_span, qref = R.soh_range_and_qref()
X, bids, soh, cyc = R.load_td(R.FEATS_ALL)
soh_by = {BATT[b]: soh[bids == b] for b in [1, 2, 3, 4]}
cyc_by = {BATT[b]: cyc[bids == b] for b in [1, 2, 3, 4]}

g = pd.read_csv(os.path.join(OUT, "phase3_windowlength_cpu_results.csv"))
p = pd.read_csv(os.path.join(OUT, "phase3_windowlength_cpu_preds.csv"))
for d in (g, p):
    d.columns = [c.strip() for c in d.columns]

print("=" * 96)
print("[1] structure, provenance, metric recomputation")
ns = g.setting.nunique()
ck(len(g) == ns * 2 * 4 * 3, f"{ns} settings x 2 stages x 4 folds x 3 seeds", str(len(g)))
ck(set(g.curve) == {"PF", "PL"}, "both curves present")
ck(set(g.window_min) == {5.0, 10.0, 20.0, 30.0}, "all four window lengths present")
ck(int(g.sel_degenerate.sum()) == 0, "zero degenerate fold-seeds in this run",
   str(int(g.sel_degenerate.sum())))
worst, bad = 0.0, []
rf = g[g.stage == "refit_on_3"]
for _, r in rf.iterrows():
    gg = p[(p.setting == r.setting) & (p.stage == r.stage) & (p.seed == r.seed)
           & (p.test_battery == r.test_battery)].sort_values("cycle")
    y, yh = gg.y_true.values, gg.y_pred.values
    m = np.isin(cyc_by[r.test_battery], gg.cycle.values)
    if m.sum() != len(gg):
        bad.append((r.setting, r.seed, r.test_battery))
    else:
        worst = max(worst, abs(np.sqrt(np.mean((y - yh) ** 2)) - r.test_RMSE),
                    abs((1 - ((y - yh) ** 2).sum() / ((y - y.mean()) ** 2).sum()) - r.test_R2))
        if np.abs(gg.y_true.values - soh_by[r.test_battery][m]).max() > 1e-9:
            bad.append(("ytrue", r.setting, r.seed, r.test_battery))
ck(not bad, "every block traces to the raw feature file, y_true == raw SOH", str(bad[:3]))
ck(worst < 5e-4, "recomputed RMSE and R2 match every row", f"max|diff|={worst:.2e}")

print("\n[2] fold coverage: the four folds must partition the 631 cycles (from the preds dump)")
prf = p[p.stage == "refit_on_3"]
sizes, dups = set(), 0
for (se, sd), gg in prf.groupby(["setting", "seed"]):
    keys = set(zip(gg.test_battery, gg.cycle))
    sizes.add(len(keys))
    if len(keys) != len(gg):
        dups += 1
ck(sizes == {631}, "every (setting, seed) covers exactly 631 disjoint keys", str(sizes))
ck(dups == 0, "no duplicate (battery, cycle) keys anywhere", str(dups))

print("\n[3] the curve")
print(rf.pivot_table(index="window_min", columns="curve", values="test_R2",
                     aggfunc="mean").round(3).to_string())
print()
print(rf.pivot_table(index="window_min", columns="curve", values="test_RMSE",
                     aggfunc="mean").round(3).to_string())
pf = rf[rf.curve == "PF"].groupby("window_min").test_R2.mean()
pl = rf[rf.curve == "PL"].groupby("window_min").test_R2.mean()
ck(abs(pf.loc[5.0] - pf.loc[30.0]) < 0.02,
   "PF curve is FLAT between 5 and 30 minutes",
   f"5min {pf.loc[5.0]:.3f} vs 30min {pf.loc[30.0]:.3f}")
ck(bool((pl.diff().dropna() > 0).all()),
   "PL curve rises monotonically with window length", str(pl.round(3).to_dict()))
ck(bool((pl > pf).all()), "PL beats PF at every window length")

print("\n[4] what actually differs between the W5-PF set and the full-cycle reference")
print("  W5-PF  (6 feats): cc_dur, cv_dur, cv_I_slope, ch_mean_T, ic_peak_V, w5_mean_T")
print("  Clean-7(7 feats): dis_mean_T, dis_V_slope, cc_dur, cv_dur, cv_I_slope, ch_mean_T,")
print("                    ic_peak_V")
notes.append("NOTE | W5-PF differs from the full-cycle Clean-7 reference by MORE than the window: "
             "it also drops dis_V_slope (R2(capacity) 0.600, and numerically fragile at 1e-4 with a "
             "sign-flipping per-battery correlation) and swaps dis_mean_T (0.430) for w5_mean_T "
             "(0.086). The gain over the full-cycle reference therefore cannot be attributed to the "
             "shorter window alone.")
c5 = pd.read_csv(os.path.join(OUT, "phase3_charge_cpu_results.csv"))
c5.columns = [c.strip() for c in c5.columns]
ref = c5[(c5.setting == "TD-Clean-7") & (c5.stage == "refit_on_3") & (c5.seed.isin([42, 7, 123]))]
ck(len(ref) == 12, "full-cycle reference has 12 fold-seeds (3 seeds)", str(len(ref)))
print(f"\n  full-cycle reference (same rows, same seeds): R2 {ref.test_R2.mean():.3f} "
      f"RMSE {ref.test_RMSE.mean():.3f}")
print(f"  W5-PF:                                        R2 {pf.loc[5.0]:.3f} "
      f"RMSE {rf[(rf.curve=='PF') & (rf.window_min==5.0)].test_RMSE.mean():.3f}")

print("\n" + "=" * 96)
for x in notes:
    if not x.startswith("NOTE"):
        print(x)
print()
if fails:
    print(f"*** {len(fails)} FAILURE(S) ***")
    for f in fails:
        print("  " + f)
else:
    print(f"ALL {len([x for x in notes if x.startswith('PASS')])} CHECKS PASSED")
print("\nNotes:")
for x in notes:
    if x.startswith("NOTE"):
        print("  " + x)