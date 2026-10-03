# Deep data-provenance audit: go back to the raw .mat files and re-derive everything the pipeline
# claims to have measured. This checks the LABEL and the FEATURES, not just the metrics.
#   A. capacity label  : integrate |I| dt over each discharge and compare with NASA_Capacity_Data.csv
#   B. qref            : mean of the first five discharge capacities
#   C. SOH             : capacity / qref * 100
#   D. features        : recompute dis_duration / dis_mean_V / dis_mean_T / dis_V_slope from raw
#   E. charge features : confirm they come from the charge cycle IMMEDIATELY BEFORE the discharge
#   F. proxy check     : does dis_duration * I reproduce capacity? (independent confirmation)
#   G. advisor's own numbers: 168/168/168/132 cycles and min SOH 69.9 / 57.2 / 74.4 / 72.9 %
import numpy as np
import pandas as pd
import scipy.io as sio

BASE = r"C:\Master Degree\Thesis\NASA DataSet\1. BatteryAgingARC-FY08Q4"
OUT = r"C:\Master Degree\Thesis\Autoencoder"
TD = pd.read_csv(rf"{OUT}\nested_lobo\time_domain_features.csv")
CAP = pd.read_csv(rf"{OUT}\NASA_Capacity_Data.csv", dtype={"Battery_ID": int, "Cycle": int})
BATT = {1: "B0005", 2: "B0006", 3: "B0007", 4: "B0018"}
REV = {v: k for k, v in BATT.items()}
CC_V = 4.19
fails, passes = [], []


def ck(cond, label, detail=""):
    (passes if cond else fails).append(
        f"{'PASS' if cond else 'FAIL'} | {label}{(' | ' + detail) if detail else ''}")


print("=" * 100)
print("DATA-PROVENANCE AUDIT (raw .mat -> label -> features)")
print("=" * 100)

minsoh, ncyc = {}, {}
cap_err, dur_cap, feat_err = {}, {}, {}
charge_src_ok, charge_src_n = 0, 0

for b, nm in BATT.items():
    cyc = sio.loadmat(rf"{BASE}\{nm}.mat", struct_as_record=False, squeeze_me=True)[nm].cycle
    capb = CAP[CAP.Battery_ID == b].set_index("Cycle").Capacity_Ah
    tdb = TD[TD.battery == b].set_index("cycle")

    # ---- walk the file, mirroring extract_time_features.py, and recompute everything ----
    charges, dis_rows = {}, []
    for i, c in enumerate(cyc, start=1):
        t = str(c.type)
        if t == "charge":
            V = np.asarray(c.data.Voltage_measured, float).ravel()
            I = np.asarray(c.data.Current_measured, float).ravel()
            T = np.asarray(c.data.Time, float).ravel()
            dur = float(T[-1] - T[0])
            ci = np.where(V >= CC_V)[0]
            cc = float(T[ci[0]] - T[0]) if len(ci) else dur
            cv_I = I[ci[0]:] if len(ci) else I
            charges[i] = dict(cc_dur=cc, cv_dur=dur - cc,
                              cv_I_slope=float(np.polyfit(np.arange(len(cv_I)), cv_I, 1)[0])
                              if len(cv_I) > 10 else 0.0,
                              ch_mean_T=float(np.asarray(c.data.Temperature_measured, float).mean()),
                              idx=i)
        elif t == "discharge":
            V = np.asarray(c.data.Voltage_measured, float).ravel()
            I = np.asarray(c.data.Current_measured, float).ravel()
            Tm = np.asarray(c.data.Time, float).ravel()
            Te = np.asarray(c.data.Temperature_measured, float).ravel()
            prev = [j for j in charges if j < i]
            ch = charges[max(prev)] if prev else None
            ah = float(np.trapz(np.abs(I), Tm) / 3600.0)      # <-- independent capacity
            dis_rows.append(dict(cycle=i, ah=ah,
                                 dis_duration=float(Tm[-1] - Tm[0]), dis_mean_V=float(V.mean()),
                                 dis_mean_T=float(Te.mean()),
                                 dis_V_slope=float(np.polyfit(Tm, V, 1)[0]),
                                 mean_I=float(np.abs(I).mean()),
                                 charge_idx=(ch["idx"] if ch else None),
                                 cc_dur=(ch["cc_dur"] if ch else np.nan),
                                 cv_dur=(ch["cv_dur"] if ch else np.nan),
                                 cv_I_slope=(ch["cv_I_slope"] if ch else np.nan),
                                 ch_mean_T=(ch["ch_mean_T"] if ch else np.nan)))
    D = pd.DataFrame(dis_rows).set_index("cycle")
    ncyc[nm] = len(D)

    # A. capacity label vs independent integration
    common = D.index.intersection(capb.index)
    e = float(np.abs(D.loc[common, "ah"].values - capb.loc[common].values).max())
    cap_err[nm] = e
    # D. features vs the committed feature file
    fe = {}
    for f in ["dis_duration", "dis_mean_V", "dis_mean_T", "dis_V_slope", "cc_dur", "cv_dur",
              "cv_I_slope", "ch_mean_T"]:
        m = D.index.intersection(tdb.index)
        fe[f] = float(np.abs(D.loc[m, f].values - tdb.loc[m, f].values).max())
    feat_err[nm] = fe
    # F. proxy check: duration x mean current vs capacity
    dur_cap[nm] = float(np.abs(D.loc[common, "dis_duration"].values
                               * D.loc[common, "mean_I"].values / 3600.0
                               - capb.loc[common].values).max())
    # C. SOH
    q = float(capb.head(5).mean())
    soh = capb / q * 100
    minsoh[nm] = float(soh.min())
    m = D.index.intersection(tdb.index)
    ck(float(np.abs(soh.loc[m].values - tdb.loc[m, "soh"].values).max()) < 1e-6,
       f"{nm}: SOH == capacity/qref*100 (qref = mean of first 5 = {q:.4f} Ah)")
    ck(float(np.abs(capb.loc[m].values - tdb.loc[m, "capacity"].values).max()) < 1e-9,
       f"{nm}: feature-file capacity == NASA_Capacity_Data.csv")

print("\n[A] capacity label vs independent integral of |I| dt over each discharge")
print("    (the pipeline uses NASA's own reported capacity - verified exactly equal to the CSV.")
print("     This integral is an independent cross-check, so the tolerance is relative: the two")
print("     integration schemes need not agree to the last digit.)")
for nm, e in cap_err.items():
    ref = float(CAP[CAP.Battery_ID == REV[nm]].Capacity_Ah.mean())
    ck(e / ref < 0.02, f"{nm}: max|integrated Ah - NASA capacity| = {e:.5f} Ah "
                       f"= {e / ref * 100:.2f}% of mean capacity (tolerance 2%)")

print("\n[D] features recomputed from raw vs time_domain_features.csv")
worst = {}
for f in ["dis_duration", "dis_mean_V", "dis_mean_T", "dis_V_slope", "cc_dur", "cv_dur",
          "cv_I_slope", "ch_mean_T"]:
    w = max(feat_err[nm][f] for nm in BATT.values())
    worst[f] = w
    ck(w < 1e-6, f"{f}: max abs diff over all 4 batteries = {w:.3e}")

print("\n[F] proxy check: dis_duration x mean discharge current vs capacity")
for nm, e in dur_cap.items():
    ref = float(CAP[CAP.Battery_ID == REV[nm]].Capacity_Ah.mean())
    ck(e < 0.05, f"{nm}: max|duration*I - capacity| = {e:.4f} Ah "
                 f"({e / ref * 100:.2f}% of mean capacity)")

print("\n[G] against the advisor's own verified numbers")
print("  cycles  :", ncyc, " expected 168/168/168/132")
ck(list(ncyc.values()) == [168, 168, 168, 132], "cycle counts match the advisor's audit")
print("  min SOH :", {k: round(v, 1) for k, v in minsoh.items()},
      " expected 69.9 / 57.2 / 74.4 / 72.9")
exp = {"B0005": 69.9, "B0006": 57.2, "B0007": 74.4, "B0018": 72.9}
ck(all(abs(minsoh[k] - v) <= 0.05 for k, v in exp.items()),
   "min SOH per battery matches the advisor's audit to 0.1 %")

print("\n" + "=" * 100)
for p in passes:
    print(p)
if fails:
    print(f"\n*** {len(fails)} FAILURE(S) ***")
    for f in fails:
        print("  " + f)
else:
    print(f"\nALL {len(passes)} CHECKS PASSED")