# Phase 4 item 6.3 (R3-C6): CALCE CS2 cross-dataset feature extraction.
# Cells: CS2_33..38 (.xlsx, Arbin MITS, no temperature channel), CS2_8 / CS2_21 (.txt, Arbin,
# has Temperature). Charge protocol per CALCE: CC 0.5C -> 4.2 V, CV until I < 0.05 A - the same
# CC->CV shape the NASA pipeline expects, so the charge-side features transfer by construction.
# Feature maths is SHARED with phase4_extract_features.py: charge_feats(V, I, T) there is the
# single source of t_40_41 / ic_peak_V; this file feeds it arrays in (volts, amps, seconds).
# Per-cell Q_ref = mean of the first 5 usable discharge capacities; SOH = cap / Q_ref * 100.
# Hygiene (committed, CS2-adapted): drop discharge cycles with capacity < 0.8 * cell max
# (the NASA rule cap > 1.0 Ah is capacity-scale-specific; CS2 starts near 1.1 Ah) or missing.
import os
import numpy as np
import pandas as pd
import scipy.io as sio
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from phase4_charge_common import charge_feats, CC_V  # noqa: E402

BASE = r"C:\Master Degree\Thesis\CALCE"
OUT = os.path.dirname(os.path.abspath(__file__))
CELLS = ["CS2_33", "CS2_34", "CS2_35", "CS2_36", "CS2_37", "CS2_38", "CS2_8", "CS2_21"]
I_CH, I_DIS = 0.05, -0.05  # amps: segment thresholds


def segs_by_index(t, v, i):
    """Contiguous charge / discharge segments from a current trace."""
    out = []
    cur = None
    start = 0
    lab = None
    for k in range(len(i)):
        if i[k] > I_CH:
            lab = "ch"
        elif i[k] < I_DIS:
            lab = "dis"
        else:
            lab = None
        if lab != cur:
            if cur in ("ch", "dis") and k - start > 5:
                out.append((cur, start, k))
            cur, start = lab, k
    if cur in ("ch", "dis") and len(i) - start > 5:
        out.append((cur, start, len(i)))
    return out


def load_xlsx(path):
    xl = pd.ExcelFile(path)
    sheet = next(s for s in xl.sheet_names if s.startswith("Channel"))
    d = xl.parse(sheet)  # Channel_1-00x data sheet (sheet 0 is the Info header)
    t = (pd.to_datetime(d.Date_Time) - pd.to_datetime(d.Date_Time).iloc[0]).dt.total_seconds().values
    return (t, d["Voltage(V)"].values.astype(float),
            d["Current(A)"].values.astype(float),
            d["Charge_Capacity(Ah)"].values.astype(float), d["Discharge_Capacity(Ah)"].values.astype(float),
            None)  # no temperature in the 33-38 xlsx logs


def load_txt(path):
    d = pd.read_csv(path, sep="\t")
    return (d.Time.values.astype(float) * 60.0, d.mV.values / 1000.0, d.mA.values / 1000.0,
            None, None, d.Temperature.values.astype(float))  # Time column is MINUTES -> seconds


def cycles_from_stream(times, v, i, qch, qdis, temp):
    """Split the stream into discharge events; each discharge is paired with the LONGEST charge
    segment since the previous discharge (CS2 logs interleave short top-up charges between
    partial cycles, so 'the nearest charge' is often a top-up, not the real recharge)."""
    rows = []
    segs = segs_by_index(times, v, i)
    last_dis_end = 0
    for si, (lab, a, b) in enumerate(segs):
        if lab != "dis":
            continue
        prev_charges = [(a2, b2) for l2, a2, b2 in segs[:si] if l2 == "ch" and b2 > last_dis_end]
        # committed rule: a charge segment longer than 4 h is not a recharge (0.5C full charge is
        # ~2.5 h; longer segments are CV-current trickle held over breaks) - skip them.
        prev_charges = [s for s in prev_charges if times[s[1]] - times[s[0]] <= 14400.0]
        last_dis_end = b
        if not prev_charges:
            continue
        ca2, cb2 = max(prev_charges, key=lambda s: times[s[1]] - times[s[0]])
        ca, cb = a, b
        vc, ic_, tc = v[ca2:cb2], i[ca2:cb2], times[ca2:cb2]
        dt = np.diff(tc)
        dt = np.where(dt <= 0, np.nan, dt)
        ch = charge_feats(vc, ic_, tc)
        ch["cc_dur"] = ch["cv_dur"] = ch["cv_I_slope"] = np.nan
        ci = np.where(vc >= CC_V)[0]
        if len(ci):
            ch["cc_dur"] = float(tc[ci[0]] - tc[0])
            ch["cv_dur"] = float(tc[-1] - tc[ci[0]])
            cvI = ic_[ci[0]:]
            ch["cv_I_slope"] = float(np.polyfit(np.arange(len(cvI)), cvI, 1)[0]) if len(cvI) > 10 else 0.0
        vd, td = v[ca:cb], times[ca:cb]
        cap = float(-(np.trapz(i[ca:cb], td)) / 3600.0) if len(td) > 1 else np.nan
        if qdis is not None:
            q0, q1 = qdis[ca], qdis[cb - 1]
            qcol = float(q1 - q0) if abs(q0) > 1e-9 and q1 >= q0 else float(q1)  # cumulative or per-cycle
        else:
            qcol = np.nan
        rows.append(dict(capacity=cap, cap_col=qcol,
                         dis_duration=float(td[-1] - td[0]), dis_mean_V=float(vd.mean()),
                         dis_V_slope=float(np.polyfit(td, vd, 1)[0]),
                         dis_mean_T=float(temp[ca:cb].mean()) if temp is not None else np.nan,
                         ch_mean_T=float(temp[ca2:cb2].mean()) if temp is not None else np.nan, **ch))
    return rows


def main():
    frames = []
    for cell in CELLS:
        d = os.path.join(BASE, cell)
        files = sorted(os.listdir(d))
        streams = []
        for f in files:
            p = os.path.join(d, f)
            try:
                streams.append(load_xlsx(p) if f.endswith(".xlsx") else load_txt(p))
            except Exception as e:
                print(f"  {f}: SKIPPED {type(e).__name__}")
        rows = []
        for st in streams:
            rows += cycles_from_stream(st[0], st[1], st[2], st[3], st[4], st[5])
        df = pd.DataFrame(rows)
        df.insert(0, "battery", cell)
        df.insert(1, "condition", "CALCE-CS2")
        df.insert(2, "regime", "cs2")
        df.insert(3, "cycle", np.arange(1, len(df) + 1))
        df.insert(4, "has_prev_charge", True)
        frames.append(df)
        if len(df):
            print(f"{cell}: {len(df)} discharge cycles, cap {df.capacity.min():.3f}-{df.capacity.max():.3f} Ah, "
                  f"NaN: {int(df[['t_40_41','ic_peak_V','cc_dur','cv_dur','cv_I_slope']].isna().sum().sum())}, "
                  f"cap_col cross-check max|diff| = {np.nanmax(np.abs(df.capacity - df.cap_col)) if df.cap_col.notna().any() else 'n/a'}")
    df = pd.concat(frames, ignore_index=True)
    qref = df.groupby("battery").capacity.transform(lambda s: s.head(5).mean())
    df["soh"] = df.capacity / qref * 100.0
    capmax = df.groupby("battery").capacity.transform("max")
    # committed CS2 hygiene rule: a discharge with < 0.8 x cell-max capacity is a partial cycle
    # (CS2_8/21 contain mid-life partial recharges); a cell is included only if >= 20 full
    # cycles remain. Partial-cycle rows stay in the CSV, flagged cap_ok = False.
    df["cap_ok"] = df.capacity >= 0.8 * capmax
    n_full = df.groupby("battery").cap_ok.sum()
    df["include_cell"] = df.battery.map(n_full >= 20)
    out = os.path.join(OUT, "phase4_cs2_features.csv")
    df.to_csv(out, index=False)
    print(f"\nsaved {out}: {len(df)} rows, {df.battery.nunique()} cells")
    print(df.groupby("battery").agg(rows=("capacity", "size"), full=("cap_ok", "sum"),
                                    cap_min=("capacity", "min"), cap_max=("capacity", "max"),
                                    include=("include_cell", "first")).round(3).to_string())
    print("included:", sorted(df[df.include_cell].battery.unique()))


if __name__ == "__main__":
    main()
