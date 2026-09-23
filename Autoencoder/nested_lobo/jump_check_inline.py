
import numpy as np, pandas as pd
BASE = r"C:\Master Degree\Thesis\NASA DataSet\1. BatteryAgingARC-FY08Q4"
df = pd.read_csv(BASE + r"\NASA_Impedance_Data.csv")
n_spec, jumps = 0, []
for (b, c), s in df.groupby(["Battery_ID", "Cycle"]):
    re_, im_ = s.Re_Z.values, s.Neg_Im_Z.values
    for name, v in [("Re", re_), ("NegIm", im_)]:
        d = np.abs(np.diff(v)); span = v.max() - v.min()
        if span <= 0: continue
        if d.max() / span > 0.5:
            jumps.append((b, c, name, round(float(d.max()),6), round(float(d.max()/span),3)))
    n_spec += 1
print(f"spectra checked: {n_spec}")
print("spectra with any single step > 50% of component range:", len(jumps))
for j in jumps[:12]: print("  ", j)
if not jumps: print("-> no abnormal jumps detected")
