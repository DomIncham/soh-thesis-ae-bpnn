# Residual checks: (1) gap distribution numbers for report, (2) abnormal-jump check (A5 leftover)
import numpy as np, pandas as pd, torch

NL = r"C:\Master Degree\Thesis\Autoencoder\nested_lobo"
gd = pd.read_csv(f"{NL}\\tolerance_gap_distribution.csv")
print("=== gap distribution (E2 deliverable) ===")
for tol, g in gd.groupby("tolerance"):
    tot = g["count"].sum()
    print(f"tol{tol}: total={tot} | " + "  ".join(
        f"gap{int(r['gap_cycles'])}={int(r['count'])} ({r['count']/tot*100:.1f}%)"
        for _, r in g.iterrows()))
per = gd.pivot_table(index="battery", columns=["tolerance", "gap"], values="count", fill_value=0)
print(per.to_string())

# A5 residual: abnormal jumps between consecutive measured points (verified raw points, all spectra)
BASE = r"C:\Master Degree\Thesis\NASA DataSet\1. BatteryAgingARC-FY08Q4"
df = pd.read_csv(f"{BASE}\\NASA_Impedance_Data.csv")
n_spec, jumps, worst = 0, [], []
for (b, c), s in df.groupby(["Battery_ID", "Cycle"]):
    s = s.sort_index()
    re_, im_ = s.Re_Z.values, s.Neg_Im_Z.values
    for name, v in [("Re", re_), ("NegIm", im_)]:
        d = np.abs(np.diff(v))
        span = v.max() - v.min()
        if span <= 0:
            continue
        ratio = d.max() / span
        if ratio > 0.5:  # single step > half the spectrum's full range = suspicious jump
            jumps.append((b, c, name, round(float(d.max()), 6), round(float(ratio), 3)))
    n_spec += 1
print(f"\n=== abnormal-jump check (A5): {n_spec} spectra ===")
print("spectra with any single step > 50% of that component's full range:", len(jumps))
for j in jumps[:12]:
    print("  batt, cycle, comp, |step| Ohm, step/range:", j)
if not jumps:
    print("no abnormal jumps detected (no consecutive-point step exceeds 50% of the component range)")
