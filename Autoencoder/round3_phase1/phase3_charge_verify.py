# Verification + paired analysis of the Phase 3 charge-feature run.
# The aggregate improvement (0.664 -> 0.810) is of the same order as the subsetting noise
# (TD-Clean-6 scores 0.490 on 636 rows but 0.664 on the 631-row subset), so the aggregate alone
# cannot support the claim. The paired per-(fold, seed) comparison below can: all three settings
# ran on identical rows and identical seeds, so every cell is directly comparable.
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

g = pd.read_csv(os.path.join(OUT, "phase3_charge_cpu_results.csv"))
p = pd.read_csv(os.path.join(OUT, "phase3_charge_cpu_preds.csv"))
g.columns = [c.strip() for c in g.columns]
p.columns = [c.strip() for c in p.columns]

print("=" * 96)
print("[1] structure, provenance, metric recomputation")
ck(len(g) == 120, "120 rows = 3 settings x 2 stages x 4 folds x 5 seeds", str(len(g)))
ck(set(g.setting) == {"TD-Clean-6*", "TD-Clean-7", "TD-Clean-8"}, "all 3 settings present")
ck(g.test_R2.notna().all() and g.sel_epochs.notna().all(), "no NaN in the metric columns")
worst, bad = 0.0, []
for _, r in g.iterrows():
    gg = p[(p.setting == r.setting) & (p.stage == r.stage) & (p.seed == r.seed)
           & (p.test_battery == r.test_battery)].sort_values("cycle")
    y, yh = gg.y_true.values, gg.y_pred.values
    m = np.isin(cyc_by[r.test_battery], gg.cycle.values)
    if m.sum() != len(gg):
        bad.append((r.setting, r.seed, r.test_battery, len(gg), int(m.sum())))
    else:
        worst = max(worst, abs(np.sqrt(np.mean((y - yh) ** 2)) - r.test_RMSE),
                    abs((1 - ((y - yh) ** 2).sum() / ((y - y.mean()) ** 2).sum()) - r.test_R2))
        if np.abs(gg.y_true.values - soh_by[r.test_battery][m]).max() > 1e-9:
            bad.append(("ytrue", r.setting, r.seed, r.test_battery))
ck(not bad, "every block traces to the raw feature file and y_true == raw SOH", str(bad[:3]))
ck(worst < 5e-4, "recomputed RMSE and R2 match every row", f"max|diff|={worst:.2e}")
n_per = {tb: len(cyc_by[tb]) for tb in cyc_by}
print(f"  note: 5 cycles are dropped, so test sizes are 167/167/167/131 for folds "
      f"B0005/B0006/B0007/B0018 (full battery sizes {n_per})")

print("\n" + "=" * 96)
print("[2] PAIRED per-(fold, seed) comparison - identical rows and seeds for all three settings")
rf = g[g.stage == "refit_on_3"]
piv = rf.pivot_table(index=["test_battery", "seed"], columns="setting", values="test_R2")
piv = piv[["TD-Clean-6*", "TD-Clean-7", "TD-Clean-8"]]
piv["+ic_peak_V"] = piv["TD-Clean-7"] - piv["TD-Clean-6*"]
piv["+t_40_41"] = piv["TD-Clean-8"] - piv["TD-Clean-7"]
piv["total"] = piv["TD-Clean-8"] - piv["TD-Clean-6*"]
print(piv.round(3).to_string())
for col, label in (("+ic_peak_V", "adding ic_peak_V"), ("total", "CLEAN6 -> CLEAN8 total")):
    n_up = int((piv[col] > 0).sum())
    ck(n_up >= 15, f"{label}: improves in {n_up}/20 fold-seeds", f"mean delta {piv[col].mean():+.3f}")
n_t = int((piv["+t_40_41"] > 0).sum())
notes.append(f"NOTE | t_40_41 added on top of ic_peak_V is NOT supported: it improves in only "
             f"{n_t}/20 fold-seeds with a mean delta of {piv['+t_40_41'].mean():+.3f}, i.e. within "
             f"noise. Report ic_peak_V as the supported addition and t_40_41 as untested/unsupported.")
print(f"\n  mean R2   : CLEAN6* {piv['TD-Clean-6*'].mean():.3f} -> CLEAN7 "
      f"{piv['TD-Clean-7'].mean():.3f} -> CLEAN8 {piv['TD-Clean-8'].mean():.3f}")
print(f"  median R2 : CLEAN6* {piv['TD-Clean-6*'].median():.3f} -> CLEAN7 "
      f"{piv['TD-Clean-7'].median():.3f} -> CLEAN8 {piv['TD-Clean-8'].median():.3f}")
print(f"  std       : CLEAN6* {piv['TD-Clean-6*'].std():.3f} -> CLEAN7 "
      f"{piv['TD-Clean-7'].std():.3f} -> CLEAN8 {piv['TD-Clean-8'].std():.3f}")
print("\n  per-fold mean R2:")
print(rf.pivot_table(index="test_battery", columns="setting", values="test_R2",
                     aggfunc="mean").round(3).to_string())
ck(bool((rf.pivot_table(index="test_battery", columns="setting", values="test_R2", aggfunc="mean")
         .diff(axis=1).dropna(axis=1) > 0).all().all()),
   "every fold improves at every step")

print("\n" + "=" * 96)
print("[3] the instability that makes the aggregate unusable on its own")
cl = pd.read_csv(os.path.join(OUT, "td_clean_cpu_results.csv"))
cl.columns = [c.strip() for c in cl.columns]
a = cl[(cl.setting == "TD-Clean-6") & (cl.stage == "refit_on_3")].test_R2
b = rf[rf.setting == "TD-Clean-6*"].test_R2
print(f"  TD-Clean-6 on 636 rows : mean {a.mean():.3f} median {a.median():.3f} std {a.std():.3f}")
print(f"  TD-Clean-6* on 631 rows: mean {b.mean():.3f} median {b.median():.3f} std {b.std():.3f}")
print(f"  -> removing 5 of 636 cycles (0.8%) moves the score by {b.mean() - a.mean():+.3f}")
notes.append("NOTE | therefore the honest claim is the PAIRED result (0.664 -> 0.810 on identical "
             "rows), not a comparison of 0.490 against 0.810 across different row sets")
print("\n  worst per-fold-seed swing from those 5 rows:")
mm = a.reset_index(drop=True).to_frame("six36").join(
    b.reset_index(drop=True).to_frame("six31"))
mm["delta"] = mm.six31 - mm.six36
print(f"    min {mm.delta.min():+.3f}  max {mm.delta.max():+.3f}")

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