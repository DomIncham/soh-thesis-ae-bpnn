# Step 6 (advisor Step 6 + H2): recheck Figure 6 — AE reconstructs the interpolated
# input, not the measurement. Quantify: RMSE(recon vs interp input) vs RMSE(recon vs measured).
import numpy as np, pandas as pd, torch
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import torch.nn as nn, torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error

BASE = r"C:\Master Degree\Thesis\NASA DataSet\1. BatteryAgingARC-FY08Q4"
OUT = r"C:\Master Degree\Thesis\Autoencoder\eis_verify"
N_T, F_MIN, F_MAX = 128, 0.1, 5000.0
torch.manual_seed(42); np.random.seed(42)

class ControlledAutoencoder(nn.Module):
    def __init__(self, input_dim=256, bottleneck_dim=17):
        super().__init__()
        self.encoder = nn.Sequential(nn.Linear(input_dim, 128), nn.ReLU(), nn.Linear(128, bottleneck_dim))
        self.decoder = nn.Sequential(nn.Linear(bottleneck_dim, 128), nn.ReLU(), nn.Linear(128, input_dim))
    def forward(self, x):
        z = self.encoder(x); return self.decoder(z), z

data = torch.load(r"C:\Master Degree\Thesis\Autoencoder\Interpolated_EIS_log_grid_pchip.pt", weights_only=True)
X = data["features"].numpy(); lbl = data["labels"].numpy(); bids = lbl[:, 0].astype(int)
mask_tr = np.isin(bids, [1, 2]); mask_va = bids == 3; mask_te = bids == 4

scaler = MinMaxScaler().fit(X[mask_tr])           # fit on train only (zero-leakage)
Xs = {k: scaler.transform(X[m]) for k, m in [("tr", mask_tr), ("va", mask_va), ("te", mask_te)]}
t = {k: torch.tensor(v, dtype=torch.float32) for k, v in Xs.items()}
ae = ControlledAutoencoder()
opt = optim.Adam(ae.parameters(), lr=0.001)
loader = DataLoader(TensorDataset(t["tr"], t["tr"]), batch_size=16, shuffle=True)
ae.train()
for ep in range(300):
    for bx, _ in loader:
        opt.zero_grad(); rec, _ = ae(bx)
        loss = nn.functional.mse_loss(rec, bx); loss.backward(); opt.step()
print("AE trained (bottleneck=17, 300 epochs, seed 42, CPU)")
ae.eval()
with torch.no_grad():
    recon = {k: ae(t[k])[0].numpy() for k in t}
inv = {k: scaler.inverse_transform(v) for k, v in recon.items()}

# measured points -> nearest grid index (nominal log grid)
f_meas = np.logspace(np.log10(F_MIN), np.log10(F_MAX), 39)
f_grid = np.logspace(np.log10(F_MIN), np.log10(F_MAX), N_T)
idx39 = np.array([np.abs(f_grid - f).argmin() for f in f_meas])
df_raw = pd.read_csv(f"{BASE}\\NASA_Impedance_Data.csv")

def rmse(a, b): return float(np.sqrt(mean_squared_error(a, b)))
rows = []
for name, m in [("Train B0005", 1), ("Train B0006", 2), ("Val B0007", 3), ("Test B0018", 4)]:
    ids = np.where(bids == m)[0]
    r_in, r_meas = [], []
    for i in ids:
        recon_i = inv["tr" if m in (1,2) else ("va" if m==3 else "te")][np.where(np.where(bids==m)[0]==i)[0][0]]
        r_in.append(rmse(X[i], recon_i))
        s = df_raw[(df_raw.Battery_ID == m) & (df_raw.Cycle == int(lbl[i,1]))]
        meas = np.concatenate([s.Re_Z.values, s.Neg_Im_Z.values])
        r_meas.append(rmse(recon_i[np.concatenate([np.arange(128)[idx39], 128 + np.arange(128)[idx39]])], meas))
    rows.append((name, len(ids), np.mean(r_in), np.std(r_in), np.mean(r_meas), np.std(r_meas)))
res = pd.DataFrame(rows, columns=["battery", "n", "RMSE_recon_vs_input(Ohm)", "std", "RMSE_recon_vs_measured(Ohm)", "std "])
res.to_csv(f"{OUT}\\fig6_recheck_metrics.csv", index=False)
print(res.to_string(index=False))

# figure: measured points + interpolated AE input + AE reconstruction (2 spectra)
fig, axes = plt.subplots(1, 2, figsize=(13, 5.2))
for ax, (bid, cyc) in zip(axes, [(1, 41), (4, int(lbl[bids==4][len(lbl[bids==4])//2,1]) )]):
    i = int(np.where((bids == bid) & (lbl[:,1] == cyc))[0][0])
    grp = "tr" if bid in (1,2) else ("va" if bid==3 else "te")
    rec = inv[grp][np.where(np.where(bids==bid)[0]==i)[0][0]]
    s = df_raw[(df_raw.Battery_ID == bid) & (df_raw.Cycle == cyc)]
    ax.scatter(s.Re_Z.values, s.Neg_Im_Z.values, c="k", s=34, zorder=5, label="measured points (raw)")
    ax.plot(X[i][:128], X[i][128:], color="0.55", lw=1.6, label="AE input target = interpolation output")
    ax.plot(rec[:128], rec[128:], "r--", lw=1.6, label="AE reconstruction")
    ax.set_title(f"{'B0005' if bid==1 else 'B0018'} cycle {cyc}\nRMSE recon-vs-input {rmse(X[i], rec):.6f} | recon-vs-measured "
                 f"{rmse(np.concatenate([rec[:128][idx39], rec[128:][idx39]]), np.concatenate([s.Re_Z.values, s.Neg_Im_Z.values])):.6f} Ohm", fontsize=9)
    ax.set_xlabel("Re(Z) [Ohm]"); ax.set_ylabel("-Im(Z) [Ohm]"); ax.legend(fontsize=8); ax.grid(alpha=.3)
fig.suptitle("Step 6: Figure 6 recheck — the AE reconstructs the interpolated input (grey), not the measurement (black points)")
plt.tight_layout(); plt.savefig(f"{OUT}\\Step6_Fig6_recheck.png", dpi=150)
print("saved Step6_Fig6_recheck.png")