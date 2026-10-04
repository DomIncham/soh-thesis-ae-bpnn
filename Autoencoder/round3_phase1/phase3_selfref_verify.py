# Verification + paired analysis for the self-referenced normalisation run (Phase 3.3).
# Two questions: (1) are the numbers sound, (2) on identical (fold, seed) cells, what exactly did
# self-referencing change - and is the damage localised?
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

s = pd.read_csv(os.path.join(OUT, "phase3_selfref_cpu_results.csv"))
sp = pd.read_csv(os.path.join(OUT, "phase3_selfref_cpu_preds.csv"))
u = pd.read_csv(os.path.join(OUT, "phase3_charge_cpu_results.csv"))
for d in (s, sp, u):
    d.columns = [c.strip() for c in d.columns]

print("=" * 96)
print("[1] structure and metric recomputation")
ck(len(s) == 120, "120 rows = 3 settings x 2 stages x 4 folds x 5 seeds", str(len(s)))
ck(not s.test_R2.isna().any(), "no NaN in test_R2")
worst, bad = 0.0, []
for _, r in s.iterrows():
    gg = sp[(sp.setting == r.setting) & (sp.stage == r.stage) & (sp.seed == r.seed)
            & (sp.test_battery == r.test_battery)].sort_values("cycle")
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

print("\n[2] PAIRED on identical (fold, seed) cells: normalised vs unnormalised")
srf = s[s.stage == "refit_on_3"].copy()
urf = u[u.stage == "refit_on_3"].copy()
srf["setting"] = srf.setting.replace({"TD-Clean-6": "TD-Clean-6"})
urf["setting"] = urf.setting.replace({"TD-Clean-6*": "TD-Clean-6"})
m = srf.merge(urf, on=["setting", "seed", "test_battery"], suffixes=("_self", "_none"))
ck(len(m) == 60, "60 cells matched between the two runs", str(len(m)))
m["delta"] = m.test_R2_self - m.test_R2_none
print(m.pivot_table(index="test_battery", columns="setting", values="delta",
                    aggfunc="mean").round(3).to_string())
print("\n  per-fold mean R2, self-ref vs unnormalised:")
for st in ["TD-Clean-6", "TD-Clean-7", "TD-Clean-8"]:
    g = m[m.setting == st]
    print(f"    {st}: self {g.test_R2_self.mean():+.3f}  none {g.test_R2_none.mean():+.3f}  "
          f"delta {g.delta.mean():+.3f}   (B0018 alone: "
          f"{g[g.test_battery == 'B0018'].delta.mean():+.3f})")

print("\n[3] is the damage localised to one fold?")
for st in ["TD-Clean-6", "TD-Clean-7", "TD-Clean-8"]:
    g = m[m.setting == st]
    b18 = g[g.test_battery == "B0018"]
    ok = g[g.test_battery != "B0018"]
    ck(b18.delta.mean() < -1.0 and int((b18.delta < 0).sum()) >= 4,
       f"{st}: B0018 collapses under self-ref (mean delta < -1, >=4/5 seeds negative)",
       f"mean {b18.delta.mean():+.2f}, seeds negative {int((b18.delta < 0).sum())}/5, "
       f"worst {b18.delta.min():+.2f}")
    print(f"    {st}: excluding B0018, mean R2 self {ok.test_R2_self.mean():.3f} vs "
          f"none {ok.test_R2_none.mean():.3f}  (delta {ok.delta.mean():+.3f})")
fold_delta = m[m.test_battery != "B0018"].groupby(["setting", "test_battery"]).delta.mean()
ck(bool((fold_delta > -0.15).all()),
   "no other FOLD-MEAN is damaged by more than 0.15",
   f"min fold-mean delta {fold_delta.min():+.3f}")
notes.append("NOTE | the mean R2 is dragged below zero by B0018 alone; the median stays 0.766. "
             "Both must be quoted - a single fold can invert the sign of the mean.")

print("\n[4] why B0018: its first-cycle references are outliers")
ch = pd.read_csv(os.path.join(os.path.dirname(R.TD_CSV), "charge_features.csv"))
ch.columns = [c.strip() for c in ch.columns]
tdf = pd.read_csv(R.TD_CSV)
tdf.columns = [c.strip() for c in tdf.columns]
feats = R.FEATS_CLEAN6 + ["t_40_41", "ic_peak_V"]
D = pd.DataFrame({"battery": bids, **{f: ch[f].values if f in ch.columns else
                                     tdf[f].values for f in feats}})
mask = np.isfinite(D[feats].values).all(axis=1)
D = D[mask]
first = D.groupby("battery").head(1).set_index("battery")[feats]
print(first.round(6).to_string())
print("\n  reference spread across batteries (max/min of |ref|):")
for f in feats:
    v = np.abs(first[f].values)
    print(f"    {f:14s} {v.max() / v.min():8.3f}x   refs {np.round(first[f].values, 6)}")
notes.append("NOTE | cv_I_slope's reference is 6.0x smaller for B0018 than for the others, so "
             "dividing B0018 by its own reference inflates that feature ~6x relative to the rest - "
             "self-referencing INTRODUCES a scale mismatch instead of removing one.")

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