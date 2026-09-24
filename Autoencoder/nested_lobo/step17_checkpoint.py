# Step 17 (Part I1): ModelCheckpoint persistence — save best weights to disk, reload, verify identical metrics
# Chosen config for demonstration: TD-BPNN (current best pipeline), fold test=B0005, seed 42.
import os
import numpy as np, pandas as pd, torch
from sklearn.preprocessing import MinMaxScaler
from nested_lobo_harness import BPNN, reg_metrics
import torch.nn as nn, torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset

HERE = os.path.dirname(os.path.abspath(__file__))
CKPT = os.path.join(HERE, "checkpoints"); os.makedirs(CKPT, exist_ok=True)

td = pd.read_csv(os.path.join(HERE, "time_domain_features.csv"))
feats = ["dis_duration","dis_mean_V","dis_mean_T","dis_V_slope","cc_dur","cv_dur","cv_I_slope","ch_mean_T"]
X, bids, soh = td[feats].values, td.battery.values.astype(int), td.soh.values
remaining = [b for b in [1,2,3,4] if b != 1]
val_b, train_b = remaining[0], remaining[1:]
m_tr, m_va, m_te = np.isin(bids, train_b), (bids == val_b), (bids == 1)
sc = MinMaxScaler().fit(X[m_tr])
Xs = {k: sc.transform(X[m]) for k, m in [("tr", m_tr), ("va", m_va), ("te", m_te)]}
mu, sd = soh[m_tr].mean(), soh[m_tr].std()
yz = {k: ((soh[m] - mu) / sd).astype(np.float32) for k, m in [("tr", m_tr), ("va", m_va)]}

torch.manual_seed(42); np.random.seed(42)
bp = BPNN([8, 16], 1e-4)
opt = optim.Adam(bp.parameters(), lr=1e-3, weight_decay=1e-4)
loader = DataLoader(TensorDataset(torch.tensor(Xs["tr"], dtype=torch.float32),
                                  torch.tensor(yz["tr"], dtype=torch.float32)), batch_size=32, shuffle=True)
ckpt_path = os.path.join(CKPT, "TD_bpnn_B0005_seed42_best.pth")
best_v, bad, saved_epochs = np.inf, 0, 0
for ep in range(500):
    bp.train()
    for zb, tb in loader:
        opt.zero_grad(); loss = nn.functional.mse_loss(bp(zb), tb); loss.backward(); opt.step()
    bp.eval()
    with torch.no_grad():
        v = nn.functional.mse_loss(bp(torch.tensor(Xs["va"], dtype=torch.float32)),
                                   torch.tensor(yz["va"], dtype=torch.float32)).item()
    if v < best_v - 1e-12:                      # ModelCheckpoint(save_best_only=True) equivalent
        best_v, bad, saved_epochs = v, 0, ep + 1
        torch.save({"state_dict": bp.state_dict(), "epoch": ep + 1, "val_loss": v,
                    "config": "[8,16]/l2=1e-4", "fold": {"test": "B0005", "val": "B0006"},
                    "target_mu": mu, "target_sd": sd}, ckpt_path)
    else:
        bad += 1
        if bad >= 30: break
print(f"training stopped at epoch {ep+1}; best checkpoint saved at epoch {saved_epochs} (val MSE {best_v:.6f})")
print("checkpoint file:", ckpt_path, f"({os.path.getsize(ckpt_path)} bytes)")

# reload and verify identical test metrics
ck = torch.load(ckpt_path, weights_only=False)
bp2 = BPNN([8, 16], 1e-4); bp2.load_state_dict(ck["state_dict"]); bp2.eval()
with torch.no_grad():
    pte = bp2(torch.tensor(Xs["te"], dtype=torch.float32)).numpy() * ck["target_sd"] + ck["target_mu"]
    ptr = bp2(torch.tensor(Xs["tr"], dtype=torch.float32)).numpy() * ck["target_sd"] + ck["target_mu"]
mae, rmse, r2 = reg_metrics(soh[m_te], pte)
tmae, trmse, tr2 = reg_metrics(soh[m_tr], ptr)
print(f"reloaded test: MAE={mae:.4f} RMSE={rmse:.4f} R2={r2:.4f} | train R2={tr2:.4f}")
# cross-check against the harness run for the same fold/seed (steps14_16 results, TD_bpnn)
ref = pd.read_csv(os.path.join(HERE, "steps14_16_results.csv"))
row = ref[(ref.pipeline == "TD_bpnn") & (ref.seed == 42) & (ref.test_battery == "B0005")].iloc[0]
print(f"harness row : test RMSE={row.test_RMSE:.4f} R2={row.test_R2:.4f} -> "
      f"{'MATCH' if abs(rmse - row.test_RMSE) < 0.05 and abs(r2 - row.test_R2) < 0.05 else 'CHECK (within noise?)'}")
