# Phase 4 (advisor R3-C6): widen validation to B0025-B0056.
# Survey (phase4_survey_B0025_B0056.md): only B0025-28 (24C, pulsed 4A), B0029-32 (43C, 4A),
# B0033/34/36 (24C, corrupt early heads), B0045-48 (4C, 1A) have usable labelled discharge data.
# B0038-40/41-44/49-56 are excluded (mixed conditions, documented corrupt/zero capacities,
# ragged arrays) - the exclusion rule is committed here, not hand-picked later.
# Features are byte-identical definitions to nested_lobo/extract_time_features.py (8 TD features)
# + extract_charge_features.py (t_40_41, ic_peak_V). Labels come from each discharge cycle's OWN
# Capacity field (same definition as the old CSV join); Q_ref = mean of the first 5 capacities.
# Causality: discharge row k uses its own measurements + the PRECEDING charge cycle only.
# Hygiene (committed rules):
#   row-level:  drop discharge rows with missing Capacity or Capacity < 1.0 Ah (README: "several
#               discharge runs where the capacity was very low"); every drop is counted.
#   cell-level: include a cell only if (a) >= 20 usable discharge rows remain, (b) the first-5-mean
#               Q_ref deviates from the cell's max capacity by <= 10 % (a corrupt head makes SOH
#               start far below 100 %), and (c) max capacity <= 2.1 Ah (2 Ah nominal; B0036 has
#               spurious 2.44 Ah readings). Excluded cells keep their rows in the CSV with
#               include_cell = False, so every exclusion is auditable.
import os
import numpy as np
import pandas as pd
import scipy.io as sio

BASE = r"C:\Master Degree\Thesis\NASA DataSet"
OUT = os.path.dirname(os.path.abspath(__file__))
CC_V = 4.19
# condition = temperature regime + discharge load, used later for the per-condition subgroup
CELLS = {
    "B0005": ("2A-const-24C", "room"), "B0006": ("2A-const-24C", "room"),
    "B0007": ("2A-const-24C", "room"), "B0018": ("2A-const-24C", "room"),
    "B0025": ("4A-pulse-24C", "room"), "B0026": ("4A-pulse-24C", "room"),
    "B0027": ("4A-pulse-24C", "room"), "B0028": ("4A-pulse-24C", "room"),
    "B0029": ("4A-const-43C", "hot"), "B0030": ("4A-const-43C", "hot"),
    "B0031": ("4A-const-43C", "hot"), "B0032": ("4A-const-43C", "hot"),
    "B0033": ("4A-const-24C", "room"), "B0034": ("4A-const-24C", "room"),
    "B0036": ("2A-const-24C", "room"),
    "B0045": ("1A-const-4C", "cold"), "B0046": ("1A-const-4C", "cold"),
    "B0047": ("1A-const-4C", "cold"), "B0048": ("1A-const-4C", "cold"),
}
DIRS = [d for d in os.listdir(BASE) if d[0].isdigit() and os.path.isdir(os.path.join(BASE, d))]
SMOKE = os.environ.get("P4_SMOKE", "") == "1"
if SMOKE:
    CELLS = {k: v for k, v in CELLS.items() if k in ("B0005", "B0025")}


def find_mat(nm):
    for d in DIRS:
        p = os.path.join(BASE, d, f"{nm}.mat")
        if os.path.exists(p):
            return p
    raise FileNotFoundError(nm)


def charge_feats(c):
    """t_40_41 + ic_peak_V - identical maths to extract_charge_features.py (lines 30-67).
    c=None (no preceding charge cycle) -> NaN, matching the old pipeline's missing join."""
    if c is None:
        return dict(t_40_41=np.nan, ic_peak_V=np.nan)
    V = np.asarray(c.data.Voltage_measured, float).ravel()
    I = np.asarray(c.data.Current_measured, float).ravel()
    T = np.asarray(c.data.Time, float).ravel()
    ci = np.where(V >= CC_V)[0]
    end = int(ci[0]) if len(ci) else len(V) - 1
    n = max(end, 2)
    dt = np.diff(T[:n])
    t401 = float(dt[np.logical_and(V[:n - 1] >= 4.0, V[:n - 1] < 4.1)].sum())
    Q = np.concatenate([[0.0], np.cumsum((I[:n - 1] + I[1:n]) / 2 * dt) / 3600.0])
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
            k = int(np.argmax(np.gradient(Qg, grid)))
            ic_V = float(grid[k])
        else:
            ic_V = np.nan
    else:
        ic_V = np.nan
    return dict(t_40_41=t401, ic_peak_V=ic_V)


def td_feats(c, ch, ch_cycle):
    """8 TD features - identical maths to extract_time_features.py (lines 27-45).
    cc_dur / cv_dur / cv_I_slope / ch_mean_T come from the PRECEDING CHARGE cycle (ch),
    exactly as in the old pipeline - they must never be recomputed from the discharge cycle."""
    V = np.asarray(c.data.Voltage_measured, float).ravel()
    Tm = np.asarray(c.data.Time, float).ravel()
    Te = np.asarray(c.data.Temperature_measured, float).ravel()
    return dict(dis_duration=float(Tm[-1] - Tm[0]), dis_mean_V=float(V.mean()),
                dis_mean_T=float(Te.mean()), dis_V_slope=float(np.polyfit(Tm, V, 1)[0]),
                cc_dur=ch["cc_dur"], cv_dur=ch["cv_dur"], cv_I_slope=ch["cv_I_slope"],
                ch_mean_T=ch["ch_mean_T"], **charge_feats(ch_cycle))


rows, dropped = [], []
for nm, (cond, regime) in CELLS.items():
    path = find_mat(nm)
    top = sio.loadmat(path, struct_as_record=False, squeeze_me=True)[nm]
    cyc = np.atleast_1d(top.cycle)
    charges = {}
    charges_raw = {}
    for i, c in enumerate(cyc, start=1):
        t = str(c.type)
        if t == "charge":
            charges_raw[i] = c
            V = np.asarray(c.data.Voltage_measured, float).ravel()
            T = np.asarray(c.data.Time, float).ravel()
            cc_idx = np.where(V >= CC_V)[0]
            cv_I = np.asarray(c.data.Current_measured, float).ravel()[cc_idx[0]:] if len(cc_idx) else \
                np.asarray(c.data.Current_measured, float).ravel()
            charges[i] = dict(
                cc_dur=float(T[cc_idx[0]] - T[0]) if len(cc_idx) else float(T[-1] - T[0]),
                cv_dur=float(T[-1] - T[0]) - (float(T[cc_idx[0]] - T[0]) if len(cc_idx) else float(T[-1] - T[0])),
                cv_I_slope=float(np.polyfit(np.arange(len(cv_I)), cv_I, 1)[0]) if len(cv_I) > 10 else 0.0,
                ch_mean_T=float(np.asarray(c.data.Temperature_measured, float).mean()))
        elif t == "discharge":
            cap = float(np.asarray(c.data.Capacity, float).ravel()[0]) if hasattr(c.data, "Capacity") else np.nan
            if not np.isfinite(cap) or cap < 1.0:
                dropped.append((nm, i, cap))
                continue
            prev = [j for j in charges if j < i]
            ch = charges[max(prev)] if prev else dict(cc_dur=np.nan, cv_dur=np.nan,
                                                      cv_I_slope=np.nan, ch_mean_T=np.nan)
            ch_cycle = charges_raw.get(max(prev)) if prev else None
            # ch_cycle=None -> charge-side features NaN by construction (no preceding charge)
            rows.append(dict(battery=nm, condition=cond, regime=regime, cycle=i, capacity=cap,
                             has_prev_charge=bool(prev),
                             **td_feats(c, ch, ch_cycle)))

df = pd.DataFrame(rows)
df["soh"] = df.capacity / df.groupby("battery").capacity.transform(lambda s: s.head(5).mean()) * 100.0
# cell-level inclusion rules (auditable in the CSV)
cell_stats = df.groupby("battery").agg(Q_ref=("capacity", lambda s: s.head(5).mean()),
                                       cap_max=("capacity", "max"), rows=("capacity", "size"))
bad = (cell_stats.cap_max > 2.1) | (cell_stats.Q_ref < 0.9 * cell_stats.cap_max) | (cell_stats.rows < 20)
df["include_cell"] = ~df.battery.map(bad).fillna(True)
out = os.path.join(OUT, "phase4_features.csv")
df.to_csv(out, index=False)
print(f"saved {out}: {len(df)} rows, {df.battery.nunique()} cells")
print("\nper-cell row counts / capacity range / Q_ref:")
g = df.groupby("battery").agg(rows=("capacity", "size"), cap_min=("capacity", "min"),
                              cap_max=("capacity", "max"), Q_ref=("capacity", lambda s: s.head(5).mean()),
                              include=("include_cell", "first"))
print(g.round(3).to_string())
print("\nexcluded cells (rule):", sorted(bad[bad].index.tolist()))
print(f"\ndropped by hygiene rule (<1.0 Ah or missing): {len(dropped)} rows")
for nm in sorted(set(d[0] for d in dropped)):
    n = [d for d in dropped if d[0] == nm]
    print(f"  {nm}: {len(n)} (e.g. cycles {[d[1] for d in n[:5]]} caps {[round(d[2],3) for d in n[:5]]})")
print("\nNaN per feature:")
print(df.drop(columns=["battery", "condition", "regime", "cycle"]).isna().sum().to_string())
fcols = [c for c in df.columns if c not in ("battery", "condition", "regime", "cycle", "include_cell")]
nan_rows = int(df[fcols].isna().any(axis=1).sum())
print(f"\nfinite check: rows with any NaN = {nan_rows} (expected: early-cycle rows with no preceding "
      f"charge cycle, same as the old pipeline; NaN columns listed above)")
