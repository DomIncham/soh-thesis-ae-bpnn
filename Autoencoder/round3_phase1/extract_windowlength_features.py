# Phase 3, item 5.5 (advisor R3-C5 item 5): the window-length curve.
# Advisor's words: "RMSE vs window length (5/10/20/30 min, or dV = 0.1/0.2/0.3 V) - answers 'how
# little data is enough?'; key figure for the partial-cycle contribution."
#
# This extractor produces, for each candidate window length, the discharge features computable from
# ONLY the first W minutes of the discharge (or the first dV of voltage drop), so a later run can ask
# how much accuracy survives as the window shrinks.
#
# Window lengths: W = 5, 10, 20, 30 minutes, and dV = 0.1, 0.2, 0.3 V of drop from the discharge
# start. Every produced feature is classified with the same proxy rule used throughout
# (within-battery OLS R^2 against capacity; PROXY at >= 0.90) BEFORE it is used.
import os
import numpy as np
import pandas as pd
import scipy.io as sio

BASE = r"C:\Master Degree\Thesis\NASA DataSet\1. BatteryAgingARC-FY08Q4"
AUTO = r"C:\Master Degree\Thesis\Autoencoder"
BATT = {1: "B0005", 2: "B0006", 3: "B0007", 4: "B0018"}
WS = [5, 10, 20, 30]          # minutes
DVS = [0.1, 0.2, 0.3]         # volts of drop from the start of discharge


def nan_feats(tag):
    return {f"{tag}_mean_V": np.nan, f"{tag}_mean_T": np.nan,
            f"{tag}_V_slope": np.nan, f"{tag}_dT": np.nan, f"{tag}_n": 0}


def seg_feats(V, Te, T, i0, i1, tag):
    Vw, Tw, Tew = V[i0:i1], T[i0:i1], Te[i0:i1]
    if len(Vw) < 10:
        return nan_feats(tag)
    return {f"{tag}_mean_V": float(Vw.mean()), f"{tag}_mean_T": float(Tew.mean()),
            f"{tag}_V_slope": float(np.polyfit(Tw, Vw, 1)[0]),
            f"{tag}_dT": float(Tew[-1] - Tew[0]), f"{tag}_n": int(i1 - i0)}


rows = []
for b, nm in BATT.items():
    cyc = sio.loadmat(os.path.join(BASE, f"{nm}.mat"),
                      struct_as_record=False, squeeze_me=True)[nm].cycle
    for i, c in enumerate(cyc, start=1):
        if str(c.type) != "discharge":
            continue
        V = np.asarray(c.data.Voltage_measured, float).ravel()
        Te = np.asarray(c.data.Temperature_measured, float).ravel()
        T = np.asarray(c.data.Time, float).ravel()
        rec = dict(battery=b, cycle=i)
        for W in WS:
            i1 = int(np.searchsorted(T, T[0] + W * 60.0))
            i1 = min(max(i1, 0), len(V))
            if i1 < 10:
                rec.update(nan_feats(f"w{W}"))
            else:
                rec.update(seg_feats(V, Te, T, 0, i1, f"w{W}"))
        for dv in DVS:
            lim = V[0] - dv
            idx = np.where(V <= lim)[0]
            i1 = int(idx[0]) if len(idx) else len(V) - 1
            if i1 < 10:
                rec.update(nan_feats(f"dv{dv}"))
            else:
                rec.update(seg_feats(V, Te, T, 0, i1, f"dv{dv}"))
        rows.append(rec)

df = pd.DataFrame(rows)
td = pd.read_csv(os.path.join(AUTO, "nested_lobo", "time_domain_features.csv"))
td.columns = [c.strip() for c in td.columns]
assert np.array_equal(df.battery.values, td.battery.values) and \
       np.array_equal(df.cycle.values, td.cycle.values), "ALIGNMENT: window rows differ from TD rows"
df = df.merge(td[["battery", "cycle", "capacity", "soh"]], on=["battery", "cycle"], how="left")
out = os.path.join(AUTO, "nested_lobo", "windowlength_features.csv")
df.to_csv(out, index=False)

print(f"rows: {len(df)}  (expected 636)")
NEW = [c for c in df.columns if c not in ("battery", "cycle", "capacity", "soh")]
print(f"features: {len(NEW)}  NaN counts (non-zero only):")
nz = df[NEW].isna().sum()
print(nz[nz > 0].to_string() if (nz > 0).any() else "  (none)")

print("\n=== proxy rule on every window-length feature (within-battery OLS R2 vs capacity) ===")
res = []
for f in NEW:
    rs = []
    for b, g in df.groupby("battery"):
        x, y = g[f].values.astype(float), g["capacity"].values.astype(float)
        m = np.isfinite(x) & np.isfinite(y)
        if m.sum() < 10 or np.std(x[m]) == 0:
            rs.append(np.nan)
            continue
        bb, aa = np.polyfit(x[m], y[m], 1)
        yh = aa + bb * x[m]
        ss = ((y[m] - y[m].mean()) ** 2).sum()
        rs.append(1 - ((y[m] - yh) ** 2).sum() / ss)
    mr = float(np.nanmean(rs))
    cls = "PROXY" if mr >= 0.90 else ("BORDERLINE" if mr >= 0.50 else "SAFE")
    res.append(dict(feature=f, mean_R2_capacity=round(mr, 3), cls=cls,
                    per_battery=[round(x, 3) for x in rs]))
R = pd.DataFrame(res)
for tag in [f"w{W}" for W in WS] + [f"dv{d}" for d in DVS]:
    sub = R[R.feature.str.startswith(tag)]
    print(f"\n  --- {tag}")
    for _, r in sub.iterrows():
        print(f"    {r.feature:16s} R2(cap)={r.mean_R2_capacity:7.3f}  {r.cls:11s} {r.per_battery}")
R.to_csv(os.path.join(AUTO, "round3_phase1", "r3c5_windowlength_classes.csv"), index=False)
print(f"\nsaved: {out}")
print("saved: round3_phase1/r3c5_windowlength_classes.csv")