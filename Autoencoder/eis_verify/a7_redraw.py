# A7: Nyquist redraw from verified raw points — 4 spectra, >1 battery + >1 cycle, no interpolation
import scipy.io as sio
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = r"C:\Master Degree\Thesis\NASA DataSet\1. BatteryAgingARC-FY08Q4"
OUT = r"C:\Master Degree\Thesis\Autoencoder\eis_verify"
PICKS = [("B0005", 1), ("B0005", 160), ("B0006", 1), ("B0018", 50)]  # (battery, impedance ordinal 1-based)

fig, axes = plt.subplots(2, 2, figsize=(12, 9))
for ax, (batt, ord_) in zip(axes.ravel(), PICKS):
    cyc = sio.loadmat(f"{BASE}\\{batt}.mat", struct_as_record=False, squeeze_me=True)[batt].cycle
    imps = [c for c in cyc if str(c.type) == "impedance"]
    c = imps[ord_ - 1]
    struct_idx = list(cyc).index(c) + 1  # MATLAB cycle index used in CSV
    ri = np.asarray(c.data.Rectified_Impedance)
    re_, negim = ri.real, -ri.imag
    ax.scatter(re_, negim, c="k", s=30, zorder=3, label="Measured points (raw)")
    ax.plot(re_, negim, "r-", lw=0.8, alpha=0.7, label="Connected in array order")
    ax.set_title(f"{batt}  impedance #{ord_}  (CSV cycle {struct_idx})\n"
                 f"{len(ri)} points, no interpolation", fontsize=10)
    ax.set_xlabel("Re(Z) [Ohm]"); ax.set_ylabel("-Im(Z) [Ohm]")
    ax.legend(fontsize=8); ax.grid(alpha=0.3)
fig.suptitle("Verified raw EIS (Rectified_Impedance from NASA .mat, no interpolation)\n"
             "Reference = raw measured points; line = connection of measured points only", fontsize=11)
plt.tight_layout()
plt.savefig(f"{OUT}\\A7_Raw_Nyquist_4spectra.png", dpi=150)
print("saved A7_Raw_Nyquist_4spectra.png")

# one interpolation-overlay panel for reference definition (B0005 cycle 41)
from scipy.interpolate import CubicSpline, PchipInterpolator
idx = np.arange(39); xg = np.linspace(0, 38, 300)
fig2, ax = plt.subplots(figsize=(6.4, 5))
ax.scatter(re_, negim, c="k", s=30, zorder=5, label="Measured points (raw)")
ax.plot(PchipInterpolator(idx, re_)(xg), PchipInterpolator(idx, negim)(xg), lw=1, label="PCHIP interpolation")
ax.plot(CubicSpline(idx, re_)(xg), CubicSpline(idx, negim)(xg), lw=1, ls="--", label="Cubic Spline (index-domain)")
ax.plot(np.interp(xg, idx, re_), np.interp(xg, idx, negim), lw=1, ls=":", label="Linear (index-domain)")
ax.set_xlabel("Re(Z) [Ohm]"); ax.set_ylabel("-Im(Z) [Ohm]")
ax.set_title("B0005 impedance #1 (CSV cycle 41): measured vs interpolated\n"
             "Reference = raw measured points (black); curves = interpolation only", fontsize=10)
ax.legend(fontsize=8); ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(f"{OUT}\\A7_Measured_vs_Interpolated_B0005c41.png", dpi=150)
print("saved A7_Measured_vs_Interpolated_B0005c41.png")