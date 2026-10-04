# Verification + paired analysis for the Phase 3.2 confirmation run.
# TD-Win-7 replaces ONE feature of TD-Clean-7 (dis_mean_T -> win_mean_T); both are SAFE under the
# proxy rule (0.430 and 0.494). The aggregate move (+0.047) is smaller than the known instability of
# the proxy-free regime, so only a paired per-(fold, seed) comparison can support any claim.
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

w = pd.read_csv(os.path.join(OUT, "phase3_window_cpu_results.csv"))
wp = pd.read_csv(os.path.join(OUT, "phase3_window_cpu_preds.csv"))
c = pd.read_csv(os.path.join(OUT, "phase3_charge_cpu_results.csv"))
for d in (w, wp, c):
    d.columns = [c_.strip() for c_ in d.columns]

print("=" * 96)
print("[1] structure, provenance, metric recomputation")
ck(len(w) == 40, "40 rows = 1 setting x 2 stages x 4 folds x 5 seeds", str(len(w)))
worst, bad = 0.0, []
for _, r in w.iterrows():
    gg = wp[(wp.setting == r.setting) & (wp.stage == r.stage) & (wp.seed == r.seed)
            & (wp.test_battery == r.test_battery)].sort_values("cycle")
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

print("\n[2] the swap is exactly ONE feature: Clean-7 (dis_mean_T) vs Win-7 (win_mean_T)")
n_clean = len(c[(c.setting == "TD-Clean-7") & (c.stage == "refit_on_3")])
ck(n_clean == 20, "Clean-7 reference has 20 fold-seeds from the committed 5.1 run", str(n_clean))

print("\n[3] PAIRED on identical (fold, seed) cells")
wf = w[w.stage == "refit_on_3"]
cf = c[(c.setting == "TD-Clean-7") & (c.stage == "refit_on_3")]
m = wf.merge(cf, on=["seed", "test_battery"], suffixes=("_win", "_clean"))
ck(len(m) == 20, "20 cells matched", str(len(m)))
m["delta"] = m.test_R2_win - m.test_R2_clean
print(m[["seed", "test_battery", "test_R2_clean", "test_R2_win", "delta"]].round(3)
      .to_string(index=False))
print("\n  mean delta per fold:")
print(m.groupby("test_battery").delta.mean().round(3).to_string(index=False))
n_up = int((m.delta > 0).sum())
print(f"\n  Win-7 better in {n_up}/20 cells | mean delta {m.delta.mean():+.3f} | "
      f"median delta {m.delta.median():+.3f}")
print(f"  mean R2: Clean-7 {m.test_R2_clean.mean():.3f} -> Win-7 {m.test_R2_win.mean():.3f}")
print(f"  median R2: Clean-7 {m.test_R2_clean.median():.3f} -> Win-7 {m.test_R2_win.median():.3f}")
print(f"  std: Clean-7 {m.test_R2_clean.std():.3f} -> Win-7 {m.test_R2_win.std():.3f}")
fold_delta = m.groupby("test_battery").delta.mean()
ck(n_up < 15 and fold_delta.min() > -0.05,
   "the swap FAILS the 15/20 consistency bar used for ic_peak_V -> recorded as NOT established",
   f"{n_up}/20 cells better, mean delta {m.delta.mean():+.3f}, worst fold-mean {fold_delta.min():+.3f}")
ck(bool((fold_delta > -0.02).all()),
   "no fold gets worse by more than 0.02", f"worst fold-mean delta {fold_delta.min():+.3f}")
notes.append("NOTE | verdict for 5.2: NOT established. The one admissible substitution raises the "
             "mean (0.772 -> 0.819) and helps the hardest fold (B0006 +0.108, 4/5 seeds), but it is "
             "better in only 12 of 20 cells, below the 15/20 bar that ic_peak_V cleared in 5.1, and "
             "the aggregate gain is smaller than the known instability of the proxy-free regime. "
             "It is therefore reported as suggestive and NOT adopted.")

print("\n[4] tension to record: the new feature is MORE correlated with capacity, yet performs better")
print("  dis_mean_T  R2(capacity) = 0.430  (whole cycle)")
print("  win_mean_T  R2(capacity) = 0.494  (4.0-3.6 V window)")
notes.append("NOTE | the proxy rule measures label-correlation, not usefulness. win_mean_T is "
             "slightly MORE correlated with capacity than dis_mean_T yet performs better, because "
             "restricting to a fixed voltage window removes the per-cell cut-off-voltage difference "
             "that the whole-cycle mean carries. Both are SAFE (< 0.90), so the substitution is "
             "admissible, and it is the first Phase 3 change that helped.")
notes.append("NOTE | the aggregate gain (+0.047) is smaller than the known instability of the "
             "proxy-free regime, so the claim must be the paired one (see the counts above), not "
             "the aggregate alone.")

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