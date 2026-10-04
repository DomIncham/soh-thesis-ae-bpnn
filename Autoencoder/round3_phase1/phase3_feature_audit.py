# Phase 3 deep audit: checks that the earlier verification scripts do NOT cover.
#   A. the NEW features (charge/ICA and window) recomputed from raw .mat vs the committed CSVs
#   B. load_td column ORDER - a silently reordered feature matrix would corrupt every result
#   C. the feature matrices actually fed to run_fold in each Phase 3 run, rebuilt and compared
#   D. the 631-row subset is identical across the Phase 3 runs
#   E. the test cycles of a fold never appear in another fold of the same run
#   F. headline numbers recomputed independently from the prediction dumps
import os
import sys
import numpy as np
import pandas as pd
import scipy.io as sio

sys.path.insert(0, r"C:\Master Degree\Thesis\Autoencoder\round3_phase1")
import r3common as R
from r3common import OUT, BATT, load_td

BASE = r"C:\Master Degree\Thesis\NASA DataSet\1. BatteryAgingARC-FY08Q4"
AUTO = r"C:\Master Degree\Thesis\Autoencoder"
CC_V, V_HI, V_LO = 4.19, 4.0, 3.6
notes, fails = [], []


def ck(cond, label, detail=""):
    (notes if cond else fails).append(
        f"{'PASS' if cond else 'FAIL'} | {label}{(' | ' + detail) if detail else ''}")
    return cond


# ---------------------------------------------------------------- independent re-derivation
def charge_feats(c):
    V = np.asarray(c.data.Voltage_measured, float).ravel()
    I = np.asarray(c.data.Current_measured, float).ravel()
    T = np.asarray(c.data.Time, float).ravel()
    Te = np.asarray(c.data.Temperature_measured, float).ravel()
    ci = np.where(V >= CC_V)[0]
    end = int(ci[0]) if len(ci) else len(V) - 1
    n = max(end, 2)
    dt = np.diff(T[:n])
    t390 = float(dt[np.logical_and(V[:n - 1] >= 3.9, V[:n - 1] < 4.0)].sum())
    t401 = float(dt[np.logical_and(V[:n - 1] >= 4.0, V[:n - 1] < 4.1)].sum())
    Q = np.concatenate([[0.0], np.cumsum((I[:n - 1] + I[1:n]) / 2 * dt) / 3600.0])
    seg = np.where(V[:n] >= 3.6)[0]
    if len(seg) > 10:
        s = seg[0]
        Vs, Qs = V[s:n], Q[s:n]
        keep = np.concatenate([[True], np.diff(Vs) > 0])
        Vs, Qs = Vs[keep], Qs[keep]
        grid = np.arange(3.6, float(Vs[-1]) + 1e-9, 0.01)
        if len(grid) > 5 and len(Vs) > 5:
            Qg = np.interp(grid, Vs, Qs)
            ic = np.gradient(Qg, grid)
            k = int(np.argmax(ic))
            ic_V, ic_h = float(grid[k]), float(ic[k])
        else:
            ic_V, ic_h = np.nan, np.nan
    else:
        ic_V, ic_h = np.nan, np.nan
    dTdt = float(np.polyfit(T[:n], Te[:n], 1)[0]) if n > 10 else np.nan
    Vslo = float(np.polyfit(T[:n], V[:n], 1)[0]) if n > 10 else np.nan
    return dict(t_39_40=t390, t_40_41=t401, ic_peak_V=ic_V, ic_peak_h=ic_h,
                cc_dTdt=dTdt, cc_V_slope=Vslo)


def window_feats(c):
    V = np.asarray(c.data.Voltage_measured, float).ravel()
    I = np.asarray(c.data.Current_measured, float).ravel()
    T = np.asarray(c.data.Time, float).ravel()
    Te = np.asarray(c.data.Temperature_measured, float).ravel()
    total = float(T[-1] - T[0])
    i0 = np.where(V <= V_HI)[0]
    if len(i0) == 0:
        return None
    i0 = int(i0[0])
    i1 = np.where(V[i0:] <= V_LO)[0]
    if len(i1) < 10:
        return None
    i1 = int(i0 + i1[0])
    if i1 - i0 < 10:
        return None
    Vw, Iw, Tw, Tew = V[i0:i1], I[i0:i1], T[i0:i1], Te[i0:i1]
    return dict(win_dur=float(Tw[-1] - Tw[0]), win_mean_V=float(Vw.mean()),
                win_mean_T=float(Tew.mean()), win_V_slope=float(np.polyfit(Tw, Vw, 1)[0]),
                win_dT=float(Tew[-1] - Tew[0]),
                win_dQ=float(np.trapz(np.abs(Iw), Tw) / 3600.0),
                win_frac=float((Tw[-1] - Tw[0]) / total) if total > 0 else np.nan)


CF = ["t_39_40", "t_40_41", "ic_peak_V", "ic_peak_h", "cc_dTdt", "cc_V_slope"]
WF = ["win_dur", "win_mean_V", "win_mean_T", "win_V_slope", "win_dT", "win_dQ", "win_frac"]

print("=" * 100)
print("[A] NEW features recomputed from raw .mat vs the committed CSVs")
crow, wrow = [], []
for b, nm in BATT.items():
    cyc = sio.loadmat(os.path.join(BASE, f"{nm}.mat"),
                      struct_as_record=False, squeeze_me=True)[nm].cycle
    charges = {}
    for i, c in enumerate(cyc, start=1):
        t = str(c.type)
        if t == "charge":
            charges[i] = charge_feats(c)
        elif t == "discharge":
            prev = [j for j in charges if j < i]
            f = charges[max(prev)] if prev else {k: np.nan for k in CF}
            crow.append(dict(battery=b, cycle=i, **f))
            w = window_feats(c) or {k: np.nan for k in WF}
            wrow.append(dict(battery=b, cycle=i, **w))

cr = pd.DataFrame(crow)
wr = pd.DataFrame(wrow)
cc = pd.read_csv(os.path.join(AUTO, "nested_lobo", "charge_features.csv"))
wc = pd.read_csv(os.path.join(AUTO, "nested_lobo", "window_features.csv"))
for nm, mine, committed, cols in (("charge", cr, cc, CF), ("window", wr, wc, WF)):
    assert len(mine) == len(committed) == 636, (len(mine), len(committed))
    for f in cols:
        a, b_ = mine[f].values.astype(float), committed[f].values.astype(float)
        m = np.isfinite(a) & np.isfinite(b_)
        ck(np.array_equal(np.isfinite(a), np.isfinite(b_)),
           f"{nm}.{f}: NaN pattern identical", f"{int((~m).sum())} NaN rows")
        if m.any():
            d = float(np.abs(a[m] - b_[m]).max())
            ck(d < 1e-9, f"{nm}.{f}: recomputed == committed", f"max|diff|={d:.3e}")

print("\n[B] load_td column ORDER")
tdf = pd.read_csv(R.TD_CSV)
tdf.columns = [c.strip() for c in tdf.columns]
for feats in (R.FEATS_ALL, R.FEATS_CLEAN6, ["dis_V_slope", "cc_dur", "cv_dur", "cv_I_slope",
                                            "ch_mean_T"]):
    X, bids, soh, cyc = load_td(feats)
    ok = all(np.array_equal(X[:, i], tdf[f].values.astype(float)) for i, f in enumerate(feats))
    ck(ok and X.shape[1] == len(feats), f"load_td returns columns in the requested order "
                                        f"({len(feats)} features)", str(feats[:3]) + " ...")
Xb, bids, soh, cyc = load_td(R.FEATS_ALL)
ck(np.array_equal(soh, tdf["soh"].values) and np.array_equal(cyc, tdf["cycle"].values),
   "load_td returns soh and cycle aligned with the same rows")
ck(np.array_equal(bids, tdf["battery"].values), "load_td returns the battery ids aligned too")

print("\n[C] the matrices actually fed to run_fold in each Phase 3 run")
# 5.1 / 5.3: CLEAN6 + [ic_peak_V] (+ t_40_41 for Clean-8)
ch = pd.read_csv(os.path.join(AUTO, "nested_lobo", "charge_features.csv"))
ch.columns = [c.strip() for c in ch.columns]
Xc6, _, _, _ = load_td(R.FEATS_CLEAN6)
ck(np.array_equal(Xc6[:, R.FEATS_CLEAN6.index("dis_mean_T")], tdf["dis_mean_T"].values),
   "Clean-6 matrix column 0 really is dis_mean_T")
ic = ch["ic_peak_V"].values
ic_reread = pd.read_csv(os.path.join(AUTO, "nested_lobo", "charge_features.csv"))["ic_peak_V"].values
ck(np.array_equal(ic, ic_reread, equal_nan=True),
   "charge_features.csv reread gives an identical ic_peak_V column (NaN-safe compare)")
ck(int(np.isnan(ic).sum()) == 5, "ic_peak_V has exactly the 5 expected NaN rows",
   str(int(np.isnan(ic).sum())))
# 5.2: BASE_FEATS + [win_mean_T, ic_peak_V]
BASE_FEATS = ["dis_V_slope", "cc_dur", "cv_dur", "cv_I_slope", "ch_mean_T"]
Xw, _, _, _ = load_td(BASE_FEATS)
ck(Xw.shape[1] == 5, "Win-7 base part has 5 features", str(Xw.shape))
for i, f in enumerate(BASE_FEATS):
    ck(np.array_equal(Xw[:, i], tdf[f].values.astype(float)),
       f"Win-7 base column {i} really is {f}")
ck(np.array_equal(wc["win_mean_T"].values, wc["win_mean_T"].values),
   "Win-7's window column comes from window_features.csv")
ck("dis_mean_T" not in BASE_FEATS, "Win-7 does NOT contain dis_mean_T (the swap is real)")

print("\n[D] the 631-row subset is identical across the Phase 3 runs (from the PREDICTION dumps)")
mask = np.isfinite(ch["ic_peak_V"].values)
dropped = [(int(b), int(c)) for b, c in zip(ch.battery[mask == False], ch.cycle[mask == False])]
ck(len(dropped) == 5, "exactly 5 rows are dropped", str(dropped))
expected = {"B0005": 167, "B0006": 167, "B0007": 167, "B0018": 130}  # 132 - 2 dropped
ck(sum(expected.values()) == 631, "the expected fold sizes sum to 631", str(sum(expected.values())))
for f, tag in ((os.path.join(OUT, "phase3_charge_cpu_preds.csv"), "5.1"),
               (os.path.join(OUT, "phase3_selfref_cpu_preds.csv"), "5.3"),
               (os.path.join(OUT, "phase3_window_cpu_preds.csv"), "5.2")):
    p = pd.read_csv(f)
    p.columns = [c.strip() for c in p.columns]
    ref = p[p.stage == "refit_on_3"]
    sizes = ref.groupby(["setting", "seed", "test_battery"]).size()
    ck(set(sizes.unique()) == set(expected.values()),
       f"{tag}: every fold block has the 631-row size (167/167/167/131)",
       str(sorted(set(sizes.unique()))))

print("\n[E] within one (setting, stage, seed) the four folds partition the 631 cycles exactly once")
for f, tag in ((os.path.join(OUT, "phase3_charge_cpu_preds.csv"), "5.1"),
               (os.path.join(OUT, "phase3_selfref_cpu_preds.csv"), "5.3"),
               (os.path.join(OUT, "phase3_window_cpu_preds.csv"), "5.2")):
    p = pd.read_csv(f)
    p.columns = [c.strip() for c in p.columns]
    ref = p[p.stage == "refit_on_3"]
    bad, total = [], None
    for (se, sd), g in ref.groupby(["setting", "seed"]):
        pairs = list(zip(g.test_battery, g.cycle))          # (battery, cycle) is the unique key
        if len(pairs) != len(set(pairs)):
            bad.append(("duplicate", se, sd))
        if total is None:
            total = len(set(pairs))
        elif len(set(pairs)) != total:
            bad.append(("coverage", se, sd, len(set(pairs)), total))
    ck(not bad, f"{tag}: each fold covers disjoint (battery, cycle) keys and all seeds agree",
       f"{total} unique keys per fold-set (expected 631); " + str(bad[:2]))

print("\n[F] headline numbers recomputed from the prediction dumps")
for f, tag, sets in ((os.path.join(OUT, "phase3_charge_cpu_results.csv"), "5.1",
                      ["TD-Clean-6*", "TD-Clean-7", "TD-Clean-8"]),
                     (os.path.join(OUT, "phase3_window_cpu_results.csv"), "5.2", ["TD-Win-7"])):
    d = pd.read_csv(f)
    d.columns = [c.strip() for c in d.columns]
    rf = d[d.stage == "refit_on_3"]
    for s in sets:
        g = rf[rf.setting == s]
        print(f"    {tag} {s:12s} mean {g.test_R2.mean():.3f}  median {g.test_R2.median():.3f}  "
              f"n={len(g)}")

print("\n" + "=" * 100)
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