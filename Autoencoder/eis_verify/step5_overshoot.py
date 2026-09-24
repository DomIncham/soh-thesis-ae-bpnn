# Step 5 (advisor A8): quantitative interpolation distortion/overshoot on verified raw EIS
# Definition: dense interpolated points outside the chord envelope between adjacent
# measured points. Magnitude normalized by chord height (or spectrum range if chord ~ flat).
import numpy as np, pandas as pd, torch
from scipy.interpolate import interp1d, PchipInterpolator

BASE = r"C:\Master Degree\Thesis\NASA DataSet\1. BatteryAgingARC-FY08Q4"
OUT = r"C:\Master Degree\Thesis\Autoencoder\eis_verify"
N_T, F_MIN, F_MAX = 128, 0.1, 5000.0

df = pd.read_csv(f"{BASE}\\NASA_Impedance_Data.csv")
keys = list(df.groupby(["Battery_ID", "Cycle"]).groups.keys())
print("spectra:", len(keys))

def make_x(kind, n):
    return np.linspace(F_MIN, F_MAX, n) if kind == "linear" else \
           np.logspace(np.log10(F_MIN), np.log10(F_MAX), n)

METHODS = ["linear", "cubic", "pchip"]
def interp_fn(method, x, y):
    if method == "linear":  return interp1d(x, y, kind="linear")
    if method == "cubic":   return interp1d(x, y, kind="cubic")
    return PchipInterpolator(x, y)

def overshoot(y_meas, y_dense, seg_idx):
    """seg_idx: list of (start_i, dense_indices) per measured segment."""
    gmax = y_dense.max() - y_dense.min()
    per_spec_max_pct, per_spec_max_ohm = 0.0, 0.0
    for i, d_idx in seg_idx:
        lo, hi = min(y_meas[i], y_meas[i+1]), max(y_meas[i], y_meas[i+1])
        span = hi - lo
        denom = span if span > 1e-12 else gmax
        if denom <= 0: continue
        seg = y_dense[d_idx]
        up = np.maximum(seg - hi, 0.0).max()
        dn = np.maximum(lo - seg, 0.0).max()
        over = max(up, dn)
        if over > 0:
            per_spec_max_pct = max(per_spec_max_pct, over / denom * 100.0)
            per_spec_max_ohm = max(per_spec_max_ohm, over)
    return per_spec_max_pct, per_spec_max_ohm

rows, worst = [], {"name": None, "val": -1, "data": None}
for gk, gkind in [("linear_grid", "linear"), ("log_grid", "log")]:
    x_t = make_x(gkind, N_T)
    for b, c in keys:
        s = df[(df.Battery_ID == b) & (df.Cycle == c)]
        x_r = make_x(gkind, len(s))
        for comp, y in [("Re_Z", s.Re_Z.values), ("Neg_Im_Z", s.Neg_Im_Z.values)]:
            for m in METHODS:
                yd = interp_fn(m, x_r, y)(x_t)
                seg_idx = [(i, np.where((x_t > x_r[i]) & (x_t < x_r[i+1]))[0])
                           for i in range(len(x_r) - 1)]
                pct, ohm = overshoot(y, yd, seg_idx)
                rows.append((gk, m, comp, b, c, pct, ohm))
                if m == "cubic" and gk == "log_grid" and comp == "Neg_Im_Z" and pct > worst["val"]:
                    worst = {"name": (b, c), "val": pct,
                             "data": (x_r, y, x_t, yd, gk)}
res = pd.DataFrame(rows, columns=["grid", "method", "component", "batt", "cycle", "max_overshoot_pct", "max_overshoot_ohm"])
agg = res.groupby(["grid", "method", "component"])[["max_overshoot_pct", "max_overshoot_ohm"]].agg(["mean", "std", "max"]).reset_index()
print("\nspectra with any overshoot (per method, both grids combined):")
print(res[res.max_overshoot_pct > 0].groupby("method").size().to_string(), "| total spectra per method:", len(res) // 6)
agg.to_csv(f"{OUT}\\interpolation_overshoot_results.csv", index=False)
print(agg.to_string(index=False))

# cross-check: rebuilt log_grid_pchip curve vs pipeline .pt (B0005 c41)
pt = torch.load(r"C:\Master Degree\Thesis\Autoencoder\Interpolated_EIS_log_grid_pchip.pt", weights_only=True)
lbl = pt["labels"].numpy(); row = np.where((lbl[:,0]==1) & (lbl[:,1]==41))[0][0]
s41 = df[(df.Battery_ID==1)&(df.Cycle==41)]
x_r = make_x("log", len(s41)); x_t = make_x("log", N_T)
rebuilt = np.concatenate([PchipInterpolator(x_r, s41.Re_Z.values)(x_t),
                          PchipInterpolator(x_r, s41.Neg_Im_Z.values)(x_t)])
print("cross-check vs .pt (B0005 c41): max abs diff =", np.abs(rebuilt - pt['features'][row].numpy()).max())

# worst-case figure (cubic on log grid)
b, c = worst["name"]; x_r, y, x_t, yd, gk = worst["data"]
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
fig, axes = plt.subplots(1, 3, figsize=(16, 4.6), sharey=True)
s = df[(df.Battery_ID==b)&(df.Cycle==c)]; x_r = make_x(gk, len(s))
for ax, m in zip(axes, METHODS):
    yd_m = interp_fn(m, x_r, y)(x_t)
    p_max = overshoot(y, yd_m, [(i, np.where((x_t>x_r[i])&(x_t<x_r[i+1]))[0]) for i in range(38)])[0]
    ax.plot(x_t, yd_m, lw=1, label=f"{m} (interpolated)")
    ax.scatter(x_r, y, c="k", s=22, zorder=5, label="measured points")
    ax.set_xscale("log"); ax.set_title(f"{m}: B{b:04d} c{c}, max overshoot {p_max:.1f}%")
    ax.set_xlabel("nominal freq [Hz] (assumed)"); ax.grid(alpha=.3)
axes[0].set_ylabel("-Im(Z) [Ohm]"); axes[0].legend(fontsize=8)
fig.suptitle(f"Step 5: interpolation overshoot vs chord envelope — worst cubic spectrum (B{b:04d} cycle {c}); measured points are the reference")
plt.tight_layout(); plt.savefig(f"{OUT}\\Step5_overshoot_worst_case.png", dpi=150)
print("saved Step5_overshoot_worst_case.png; worst cubic/log -Im spectrum:", worst["name"], f"{worst['val']:.1f}%")