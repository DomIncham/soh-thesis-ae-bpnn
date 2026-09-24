# Step 14 (Part B): extract time-domain features from NASA .mat discharge+charge cycles
# Label alignment is EXACT: each discharge cycle carries its own measured capacity (no tolerance mapping).
# Causality: features of discharge cycle k use its own measurements + the PRECEDING charge cycle only.
import numpy as np, pandas as pd, torch, os

BASE = r"C:\Master Degree\Thesis\NASA DataSet\1. BatteryAgingARC-FY08Q4"
OUT = r"C:\Master Degree\Thesis\Autoencoder\nested_lobo"
CC_V = 4.19  # CC->CV transition threshold for charge cycles

qref = pd.read_csv(f"{OUT}\\..\\NASA_Capacity_Data.csv", dtype={"Battery_ID": int, "Cycle": int})
qref = qref.sort_values("Cycle").groupby("Battery_ID").head(5).groupby("Battery_ID")["Capacity_Ah"].mean()

rows, qa = [], {}
for b in [1, 2, 3, 4]:
    batt = {1: "B0005", 2: "B0006", 3: "B0007", 4: "B0018"}[b]
    import scipy.io as sio
    cyc = sio.loadmat(f"{BASE}\\{batt}.mat", struct_as_record=False, squeeze_me=True)[batt].cycle
    charges = {}  # matlab index -> features dict
    n_dis, n_charge, n_skip = 0, 0, 0
    for i, c in enumerate(cyc, start=1):
        t = str(c.type)
        if t == "charge":
            n_charge += 1
            V = np.asarray(c.data.Voltage_measured, float).ravel()
            I = np.asarray(c.data.Current_measured, float).ravel()
            T = np.asarray(c.data.Time, float).ravel()
            dur = float(T[-1] - T[0])
            cc_idx = np.where(V >= CC_V)[0]
            cc = float(T[cc_idx[0]] - T[0]) if len(cc_idx) else dur
            cv = dur - cc
            cv_I = I[cc_idx[0]:] if len(cc_idx) else I
            cv_slope = float(np.polyfit(np.arange(len(cv_I)), cv_I, 1)[0]) if len(cv_I) > 10 else 0.0
            charges[i] = dict(cc_dur=cc, cv_dur=cv, cv_I_slope=cv_slope, ch_mean_T=float(np.asarray(c.data.Temperature_measured, float).mean()))
        elif t == "discharge":
            n_dis += 1
            V = np.asarray(c.data.Voltage_measured, float).ravel()
            Tm = np.asarray(c.data.Time, float).ravel()
            Te = np.asarray(c.data.Temperature_measured, float).ravel()
            prev_charges = [j for j in charges if j < i]
            ch = charges[max(prev_charges)] if prev_charges else dict(cc_dur=np.nan, cv_dur=np.nan, cv_I_slope=np.nan, ch_mean_T=np.nan)
            rows.append(dict(battery=b, cycle=i,
                             dis_duration=float(Tm[-1] - Tm[0]), dis_mean_V=float(V.mean()),
                             dis_mean_T=float(Te.mean()), dis_V_slope=float(np.polyfit(Tm, V, 1)[0]),
                             cc_dur=ch["cc_dur"], cv_dur=ch["cv_dur"], cv_I_slope=ch["cv_I_slope"],
                             ch_mean_T=ch["ch_mean_T"]))
    # join capacity (exact same cycle) -> SOH
    cap = pd.read_csv(f"{BASE}\\NASA_Capacity_Data.csv", dtype={"Battery_ID": int, "Cycle": int})
    capb = cap[cap.Battery_ID == b].set_index("Cycle").Capacity_Ah
    df = pd.DataFrame(rows)
    df = df[df.battery == b]
    df["capacity"] = df.cycle.map(capb)
    df["soh"] = df.capacity / qref[b] * 100.0
    n_cap = df.capacity.notna().sum()
    qa[b] = (n_dis, n_charge, n_cap)
    df[df.capacity.notna()].to_csv(f"{OUT}\\td_features_B{b}.csv", index=False)
    print(f"B{batt}: discharge={n_dis} charge={n_charge} rows_with_capacity={n_cap} "
          f"| SOH {df.soh.min():.1f}-{df.soh.max():.1f} | NaN features: {int(df.drop(columns=['capacity','soh']).isna().sum().sum())}")

df_all = pd.concat([pd.read_csv(f"{OUT}\\td_features_B{b}.csv") for b in [1, 2, 3, 4]], ignore_index=True)
df_all.to_csv(f"{OUT}\\time_domain_features.csv", index=False)
print("\nTOTAL rows:", len(df_all), "| feature cols:", [c for c in df_all.columns if c not in ("battery","cycle","capacity","soh")])
print("QA (dis, chg, with_capacity):", qa)
print("finite check:", np.isfinite(df_all.drop(columns=["battery","cycle"]).values).all())