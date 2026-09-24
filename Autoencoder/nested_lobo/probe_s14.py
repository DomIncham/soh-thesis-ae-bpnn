# Leakage probe Steps 14-16: TD_bpnn (selected cfg), fold test=B0005, seed 42
import numpy as np, pandas as pd, torch
from sklearn.preprocessing import MinMaxScaler
from nested_lobo_harness import BPNN, fit_bpnn, reg_metrics
import os

HERE = os.path.dirname(os.path.abspath(__file__))
td = pd.read_csv(os.path.join(HERE, "time_domain_features.csv"))
feats = ["dis_duration","dis_mean_V","dis_mean_T","dis_V_slope","cc_dur","cv_dur","cv_I_slope","ch_mean_T"]
X, bids, soh = td[feats].values, td.battery.values.astype(int), td.soh.values

def run_fold(perturb):
    Xd = X.copy()
    if perturb: Xd[bids == 1] *= 2.0
    remaining = [b for b in [1,2,3,4] if b != 1]
    val_b, train_b = remaining[0], remaining[1:]
    m_tr, m_va, m_te = np.isin(bids, train_b), (bids == val_b), (bids == 1)
    sc = MinMaxScaler().fit(Xd[m_tr])
    Xs = {k: sc.transform(Xd[m]) for k, m in [("tr", m_tr), ("va", m_va), ("te", m_te)]}
    mu, sd = soh[m_tr].mean(), soh[m_tr].std()
    yz = {k: ((soh[m] - mu) / sd).astype(np.float32) for k, m in [("tr", m_tr), ("va", m_va)]}
    bp = fit_bpnn([8, 16], 1e-4, Xs["tr"], yz["tr"], Xs["va"], yz["va"], 42, 100, 10)
    with torch.no_grad():
        ptr = bp(torch.tensor(Xs["tr"], dtype=torch.float32)).numpy() * sd + mu
    return reg_metrics(soh[m_tr], ptr)

a, b = run_fold(False), run_fold(True)
print("baseline :", np.round(a, 6))
print("perturbed:", np.round(b, 6))
diff = float(np.abs(np.array(a) - np.array(b)).max())
print(f"max |diff| = {diff:.2e} -> {'PASS: no leakage' if diff < 1e-2 else 'CHECK'}")