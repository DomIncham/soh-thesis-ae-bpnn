
import numpy as np, pandas as pd
BASE = r"C:\Master Degree\Thesis\NASA DataSet\1. BatteryAgingARC-FY08Q4"
df = pd.read_csv(BASE + r"\NASA_Impedance_Data.csv")
# B0005 cycle 43 Re: where is the big step, and what do the values look like around it?
s = df[(df.Battery_ID==1)&(df.Cycle==43)].sort_index()
re_ = s.Re_Z.values
d = np.abs(np.diff(re_)); i = d.argmax()
print("B0005 cycle 43 Re(Z): step idx", i, "->", i+1,
      f"| values: {re_[i]:.6f} -> {re_[i+1]:.6f} (step {d[i]:.6f} Ohm)")
print("points 0..38 Re:", np.round(re_, 4).tolist())
print("context: neighbors around step:", np.round(re_[max(0,i-2):i+4], 5).tolist())
# stats over all flagged jumps: are they isolated spikes or edge-of-arc transitions?
js = []
for (b, c), s in df.groupby(["Battery_ID","Cycle"]):
    re_, im_ = s.Re_Z.values, s.Neg_Im_Z.values
    for name, v in [("Re", re_), ("NegIm", im_)]:
        dd = np.abs(np.diff(v)); span = v.max()-v.min()
        if span <= 0: continue
        r = dd.max()/span
        if r > 0.5: js.append((name, int(dd.argmax()), len(v)-1, r))
import collections
pos = collections.Counter((n, "last-step" if i==L-1 else ("first-step" if i==0 else "middle"))
                          for n, i, L, r in js)
print("\nflagged jump positions:", dict(pos))
print("max jump ratio overall:", max(r for _,_,_,r in js))
