# D3 (Part D3): expanded AE reconstruction metrics — Re/Im RMSE separately, nRMSE, relative error
# Protocol: same AE as Step 6 (log_grid+pchip, bottleneck 17, seed 42, scaler fit on train only).
import numpy as np, pandas as pd, torch
import torch.nn as nn, torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sklearn.preprocessing import MinMaxScaler

AUTO = r"C:\Master Degree\Thesis\Autoencoder"
torch.manual_seed(42); np.random.seed(42)

class ControlledAutoencoder(nn.Module):
    def __init__(self, input_dim=256, bottleneck_dim=17):
        super().__init__()
        self.encoder = nn.Sequential(nn.Linear(input_dim, 128), nn.ReLU(), nn.Linear(128, bottleneck_dim))
        self.decoder = nn.Sequential(nn.Linear(bottleneck_dim, 128), nn.ReLU(), nn.Linear(128, input_dim))
    def forward(self, x):
        z = self.encoder(x); return self.decoder(z), z

data = torch.load(rf"{AUTO}\Interpolated_EIS_log_grid_pchip.pt", weights_only=True)
X = data["features"].numpy(); lbl = data["labels"].numpy(); bids = lbl[:, 0].astype(int)
m_tr, m_va = np.isin(bids, [1, 2]), (bids == 3)
scaler = MinMaxScaler().fit(X[m_tr])
Xs = {k: torch.tensor(scaler.transform(X[m]), dtype=torch.float32) for k, m in [("tr", m_tr), ("va", m_va), ("te", bids == 4)]}
ae = ControlledAutoencoder()
opt = optim.Adam(ae.parameters(), lr=1e-3)
loader = DataLoader(TensorDataset(Xs["tr"], Xs["tr"]), batch_size=16, shuffle=True)
best_v, best_state, bad = np.inf, None, 0
for ep in range(500):
    ae.train()
    for bx, _ in loader:
        opt.zero_grad(); rec, _ = ae(bx); loss = nn.functional.mse_loss(rec, bx); loss.backward(); opt.step()
    ae.eval()
    with torch.no_grad():
        v = nn.functional.mse_loss(ae(Xs["va"])[0], Xs["va"]).item()
    if v < best_v - 1e-12:
        best_v, bad = v, 0; best_state = {k: t.clone() for k, t in ae.state_dict().items()}
    else:
        bad += 1
        if bad >= 30: break
ae.load_state_dict(best_state); ae.eval()
with torch.no_grad():
    rec = {k: scaler.inverse_transform(ae(v)[0].numpy()) for k, v in Xs.items()}

rows = []
for name, m in [("Train B0005", 1), ("Train B0006", 2), ("Val B0007", 3), ("Test B0018", 4)]:
    ids = np.where(bids == m)[0]
    re_r, im_r, nrm, rel = [], [], [], []
    span = X[ids].max(0) - X[ids].min(0)
    re_span, im_span = span[:128], span[128:]
    for i in ids:
        grp = "tr" if m in (1, 2) else ("va" if m == 3 else "te")
        r = rec[grp][np.where(ids == i)[0][0]]
        x = X[i]
        re_r.append(float(np.sqrt(np.mean((x[:128] - r[:128]) ** 2))))
        im_r.append(float(np.sqrt(np.mean((x[128:] - r[128:]) ** 2))))
        nrm.append(float(np.sqrt(np.mean(((x - r) / np.maximum(span, 1e-9)) ** 2))))
        rel.append(float(np.mean(np.abs(x - r) / np.maximum(np.abs(x), 1e-6)) * 100))
    rows.append(dict(battery=name, n=len(ids),
                     Re_RMSE_mean=round(float(np.mean(re_r)), 6), Re_RMSE_std=round(float(np.std(re_r)), 6),
                     Im_RMSE_mean=round(float(np.mean(im_r)), 6), Im_RMSE_std=round(float(np.std(im_r)), 6),
                     nRMSE_mean=round(float(np.mean(nrm)), 4), nRMSE_std=round(float(np.std(nrm)), 4),
                     rel_err_pct_mean=round(float(np.mean(rel)), 3), rel_err_pct_std=round(float(np.std(rel)), 3)))
res = pd.DataFrame(rows)
res.to_csv(rf"{AUTO}\nested_lobo\ae_reconstruction_d3_metrics.csv", index=False)
print(res.to_string(index=False))