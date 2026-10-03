# Phase 3, item 5.1 (advisor R3-C5): charging-segment features.
# Rationale: the ridge probe showed the proxy-free ceiling is a FEATURE limit (BPNN 0.490 on
# TD-Clean-6 where ridge gives -0.526), so Phase 3 has to add inputs, not architecture. The audit's
# factor 2 says whole-cycle duration and mean discharge voltage are capacity proxies; these new
# features are PARTIAL-window charge quantities and curve-shape quantities, which by construction
# do not contain the full discharge capacity.
#
# Produces, per CHARGE cycle, and attaches to the immediately FOLLOWING discharge cycle (so the
# label's own cycle still contributes nothing but its own discharge measurements - same causality
# rule as the existing charge features):
#   t_39_40, t_40_41      time spent in fixed charge-voltage windows (advisor's 5.1)
#   ic_peak_V, ic_peak_h  incremental-capacity peak position and height on the CC phase
#   cc_dTdt               temperature rise rate during the CC phase
#   cc_V_slope            voltage rise rate during the CC phase
#
# IMPORTANT: every new feature is then run through the SAME proxy rule used for the existing eight
# (within-battery OLS R^2 against capacity >= 0.90 -> PROXY). A feature is only usable as
# "proxy-free" if it passes that test; this is printed, not assumed.
import numpy as np
import pandas as pd
import scipy.io as sio

BASE = r"C:\Master Degree\Thesis\NASA DataSet\1. BatteryAgingARC-FY08Q4"
OUT = r"C:\Master Degree\Thesis\Autoencoder"
CC_V = 4.19
BATT = {1: "B0005", 2: "B0006", 3: "B0007", 4: "B0018"}
NEW = ["t_39_40", "t_40_41", "ic_peak_V", "ic_peak_h", "cc_dTdt", "cc_V_slope"]


def charge_feats(c):
    V = np.asarray(c.data.Voltage_measured, float).ravel()
    I = np.asarray(c.data.Current_measured, float).ravel()
    T = np.asarray(c.data.Time, float).ravel()
    Te = np.asarray(c.data.Temperature_measured, float).ravel()
    ci = np.where(V >= CC_V)[0]
    end = int(ci[0]) if len(ci) else len(V) - 1          # CC phase = start .. first V >= 4.19
    n = max(end, 2)
    dt = np.diff(T[:n])
    # fixed voltage windows on the CC phase
    t390 = float(dt[np.logical_and(V[:n - 1] >= 3.9, V[:n - 1] < 4.0)].sum())
    t401 = float(dt[np.logical_and(V[:n - 1] >= 4.0, V[:n - 1] < 4.1)].sum())
    Q = np.concatenate([[0.0], np.cumsum((I[:n - 1] + I[1:n]) / 2 * dt) / 3600.0])
    # incremental capacity: restrict to the informative part of the CC phase. At the very start of a
    # charge the voltage climbs off the discharge cut-off toward the plateau, so dQ/dV is largest
    # there - an edge artefact, not the ICA peak. Only V >= 3.6 V and strictly rising is used.
    lo = 3.6
    seg = np.where(V[:n] >= lo)[0]
    if len(seg) > 10:
        s = seg[0]
        Vs, Qs = V[s:n], Q[s:n]
        keep = np.concatenate([[True], np.diff(Vs) > 0])
        Vs, Qs = Vs[keep], Qs[keep]
        grid = np.arange(lo, float(Vs[-1]) + 1e-9, 0.01)
        if len(grid) > 5 and len(Vs) > 5:
            Qg = np.interp(grid, Vs, Qs)
            ic = np.gradient(Qg, grid)
            k = int(np.argmax(ic))
            ic_V, ic_h = float(grid[k]), float(ic[k])
        else:
            ic_V, ic_h = np.nan, np.nan
    else:
        ic_V, ic_h = np.nan, np.nan
    # CC-phase rates
    dTdt = float(np.polyfit(T[:n], Te[:n], 1)[0]) if n > 10 else np.nan
    Vslope = float(np.polyfit(T[:n], V[:n], 1)[0]) if n > 10 else np.nan
    return dict(t_39_40=t390, t_40_41=t401, ic_peak_V=ic_V, ic_peak_h=ic_h,
                cc_dTdt=dTdt, cc_V_slope=Vslope)


rows = []
for b, nm in BATT.items():
    cyc = sio.loadmat(rf"{BASE}\{nm}.mat", struct_as_record=False, squeeze_me=True)[nm].cycle
    charges = {}
    for i, c in enumerate(cyc, start=1):
        t = str(c.type)
        if t == "charge":
            charges[i] = charge_feats(c)
        elif t == "discharge":
            prev = [j for j in charges if j < i]
            f = charges[max(prev)] if prev else {k: np.nan for k in NEW}
            rows.append(dict(battery=b, cycle=i, **f))

df = pd.DataFrame(rows)
td = pd.read_csv(rf"{OUT}\nested_lobo\time_domain_features.csv")
td.columns = [c.strip() for c in td.columns]
df = df.merge(td[["battery", "cycle", "capacity", "soh"]], on=["battery", "cycle"], how="inner")
df.to_csv(rf"{OUT}\nested_lobo\charge_features.csv", index=False)
print(f"rows: {len(df)} (expected 636)  |  NaN per new feature:")
print(df[NEW].isna().sum().to_string())

print("\n=== proxy rule applied to the NEW features (within-battery OLS R2 vs capacity) ===")
print(f"{'feature':14s} {'mean R2(cap)':>13s} {'per-battery R2':>34s}  class")
for f in NEW:
    rs = []
    for b, g in df.groupby("battery"):
        x, y = g[f].values.astype(float), g["capacity"].values.astype(float)
        m = np.isfinite(x)
        if m.sum() < 10 or np.std(x[m]) == 0:
            rs.append(np.nan)
            continue
        bb, aa = np.polyfit(x[m], y[m], 1)
        yh = aa + bb * x[m]
        ss = ((y[m] - y[m].mean()) ** 2).sum()
        rs.append(1 - ((y[m] - yh) ** 2).sum() / ss)
    mr = float(np.nanmean(rs))
    cls = "PROXY" if mr >= 0.90 else ("BORDERLINE" if mr >= 0.50 else "SAFE")
    print(f"{f:14s} {mr:13.3f} {str([round(x,3) for x in rs]):>34s}  {cls}")

print("\n=== cross-battery domain shift (per-battery mean min..max) ===")
for f in NEW:
    m = df.groupby("battery")[f].mean()
    print(f"  {f:14s} {m.min():12.4f} .. {m.max():12.4f}")
print("\nsaved: nested_lobo/charge_features.csv")