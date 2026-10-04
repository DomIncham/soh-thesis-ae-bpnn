# Phase 3, item 5.2: fixed discharge voltage window (4.0 -> 3.6 V).
#
# Why: the whole-cycle discharge features (dis_duration, dis_mean_V, dis_mean_T, dis_V_slope) are
# computed over the entire discharge, whose end voltage differs per cell (B0005 2.7 V, B0006 2.5 V,
# B0007 2.2 V, B0018 2.5 V). A window with the SAME two end points for every battery removes that
# source of scale mismatch - which is exactly the failure mode that killed item 5.3.
#
# NOTE ON SCOPE: this is a NEW script rather than a modification of nested_lobo/extract_time_features.py,
# deliberately. Editing that file and re-running it would overwrite time_domain_features.csv, on which
# every earlier Phase 1/2/3 result depends; keeping the window features in their own file means all
# previously committed artifacts stay reproducible from the code as committed.
#
# Every produced feature is then classified with the SAME proxy rule used throughout
# (within-battery OLS R^2 against capacity; PROXY at >= 0.90), before any of them is used.
import os
import numpy as np
import pandas as pd
import scipy.io as sio

BASE = r"C:\Master Degree\Thesis\NASA DataSet\1. BatteryAgingARC-FY08Q4"
OUT = r"C:\Master Degree\Thesis\Autoencoder"
V_HI, V_LO = 4.0, 3.6
BATT = {1: "B0005", 2: "B0006", 3: "B0007", 4: "B0018"}
NEW = ["win_dur", "win_mean_V", "win_mean_T", "win_V_slope", "win_dT", "win_dQ", "win_frac"]


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
                win_mean_T=float(Tew.mean()),
                win_V_slope=float(np.polyfit(Tw, Vw, 1)[0]),
                win_dT=float(Tew[-1] - Tew[0]),
                win_dQ=float(np.trapz(np.abs(Iw), Tw) / 3600.0),
                win_frac=float((Tw[-1] - Tw[0]) / total) if total > 0 else np.nan)


rows, skipped = [], []
for b, nm in BATT.items():
    cyc = sio.loadmat(rf"{BASE}\{nm}.mat", struct_as_record=False, squeeze_me=True)[nm].cycle
    for i, c in enumerate(cyc, start=1):
        if str(c.type) == "discharge":
            f = window_feats(c)
            if f is None:
                skipped.append((b, i))
                f = {k: np.nan for k in NEW}
            rows.append(dict(battery=b, cycle=i, **f))

df = pd.DataFrame(rows)
print(f"discharge cycles: {len(df)}   cycles where the 4.0-3.6 V window does not exist: {len(skipped)}")
if skipped:
    print(f"  {skipped}")

td = pd.read_csv(os.path.join(OUT, "nested_lobo", "time_domain_features.csv"))
td.columns = [c.strip() for c in td.columns]
assert np.array_equal(df.battery.values, td.battery.values) and \
       np.array_equal(df.cycle.values, td.cycle.values), "ALIGNMENT: window rows differ from TD rows"
df = df.merge(td[["battery", "cycle", "capacity", "soh", "dis_duration", "dis_mean_V",
                  "dis_mean_T", "dis_V_slope"]], on=["battery", "cycle"], how="left")
df.to_csv(os.path.join(OUT, "nested_lobo", "window_features.csv"), index=False)
print(f"rows: {len(df)}  NaN per feature:\n{df[NEW].isna().sum().to_string()}")

print("\n=== proxy rule applied to the WINDOW features (within-battery OLS R2 vs capacity) ===")
print(f"{'feature':12s} {'mean R2(cap)':>13s}  {'per-battery R2':>32s}  class")
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
    print(f"{f:12s} {mr:13.3f}  {str([round(x,3) for x in rs]):>32s}  {cls}")

print("\n=== cross-battery domain shift (per-battery mean min..max) vs the whole-cycle analogues ===")
for f in NEW:
    m = df.groupby("battery")[f].mean()
    print(f"  {f:12s} {m.min():12.4f} .. {m.max():12.4f}   spread {m.max()/max(abs(m.min()),1e-12):.3f}x")
print("\n  for comparison, whole-cycle features:")
for f in ["dis_duration", "dis_mean_V", "dis_mean_T", "dis_V_slope"]:
    m = df.groupby("battery")[f].mean()
    print(f"  {f:12s} {m.min():12.4f} .. {m.max():12.4f}   spread {m.max()/max(abs(m.min()),1e-12):.3f}x")
print("\nsaved: nested_lobo/window_features.csv")