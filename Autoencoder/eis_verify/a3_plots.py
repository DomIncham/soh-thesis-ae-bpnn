# Step A3: B0005 Cycle 41 — table + 3 diagnostic plots + fixed time check
import scipy.io as sio
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from datetime import datetime
import os

BASE = r"C:\Master Degree\Thesis\NASA DataSet\1. BatteryAgingARC-FY08Q4"
OUT = r"C:\Master Degree\Thesis\Autoencoder\eis_verify"
os.makedirs(OUT, exist_ok=True)

def m2datetime(t):
    t = np.asarray(t, dtype=float).ravel()
    return datetime(int(t[0]), int(t[1]), int(t[2])) if t[0] > 1e3 else \
           datetime(int(t[0])+2000, int(t[1]), int(t[2]), *[int(x) for x in t[3:6]] if len(t) >= 6 else [0]*3)

cyc = sio.loadmat(f"{BASE}\\B0005.mat", struct_as_record=False, squeeze_me=True)["B0005"].cycle
imps = [(i, c) for i, c in enumerate(cyc) if str(c.type) == "impedance"]
i41, c41 = imps[0]
ri = np.asarray(c41.data.Rectified_Impedance)
re_, negim = ri.real, -ri.imag

# proper datenum monotonic check across all cycles
dts = [m2datetime(c.time) for c in cyc]
mono = all(d2 > d1 for d1, d2 in zip(dts, dts[1:]))
print("time strictly increasing (proper datetime):", mono)
if not mono:
    bad = [i for i in range(1, len(dts)) if dts[i] <= dts[i-1]]
    print("non-monotonic at cycle idx:", bad[:10], "count:", len(bad))

# nominal frequency (ASSUMPTION: log-spaced 0.1->5kHz, 39 pts; documented range only)
f_nom = np.logspace(np.log10(0.1), np.log10(5000), 39)

with open(f"{OUT}\\A3_B0005_cycle41_table.csv", "w") as f:
    f.write("Point,Freq_nominal_Hz,Re_Z_Ohm,NegIm_Z_Ohm\n")
    for k in range(39):
        f.write(f"{k+1},{f_nom[k]:.6g},{re_[k]:.9f},{negim[k]:.9f}\n")
print("table saved:", f"{OUT}\\A3_B0005_cycle41_table.csv")

fig, axes = plt.subplots(1, 3, figsize=(16, 4.6))
ax = axes[0]; ax.scatter(re_, negim, c="k", s=28)
ax.set_title("Plot 1: Raw measured EIS points only (no line)"); ax.set_xlabel("Re(Z) [Ohm]"); ax.set_ylabel("-Im(Z) [Ohm]"); ax.grid(alpha=.3)
ax = axes[1]; ax.scatter(re_, negim, c="k", s=12, zorder=3); ax.plot(re_, negim, "r-", lw=1)
ax.set_title("Plot 2: Points connected in array order\n(low -> high frequency, verified 887/887)"); ax.set_xlabel("Re(Z) [Ohm]"); ax.set_ylabel("-Im(Z) [Ohm]"); ax.grid(alpha=.3)
ax = axes[2]
ax.scatter(re_, negim, c="k", s=28, zorder=5, label="Measured points")
idx = np.arange(39)
for name, kind in [("Linear","linear"), ("Cubic","cubic"), ("PCHIP","pchip")]:
    re_i = np.interp(np.linspace(0,38,300), idx, re_)
    if kind != "linear":
        from scipy.interpolate import PchipInterpolator, CubicSpline
        fn = PchipInterpolator(idx, negim) if kind=="pchip" else CubicSpline(idx, negim)
        re_f = PchipInterpolator(idx, re_) if kind=="pchip" else CubicSpline(idx, re_)
        ax.plot(re_f(np.linspace(0,38,300)), fn(np.linspace(0,38,300)), lw=1, label=f"{name} (index-domain)")
    else:
        ax.plot(re_i, np.interp(np.linspace(0,38,300), idx, negim), lw=1, label="Linear (index-domain)")
ax.set_title("Plot 3: Interpolation overlay (index-domain)")
ax.set_xlabel("Re(Z) [Ohm]"); ax.set_ylabel("-Im(Z) [Ohm]"); ax.legend(fontsize=8); ax.grid(alpha=.3)
plt.tight_layout()
plt.savefig(f"{OUT}\\A3_B0005_cycle41_3plots.png", dpi=150)
print("plots saved:", f"{OUT}\\A3_B0005_cycle41_3plots.png")
