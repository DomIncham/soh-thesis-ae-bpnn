# Leakage probe for Steps 9-10 batch: P1 (raw->BPNN [8], l2=0), fold test=B0005, seed 42
# Rule 6: perturb outer-test features x2 -> refit + retrain -> TRAIN metrics must not move.
import numpy as np, torch
from sklearn.preprocessing import MinMaxScaler
from nested_lobo_harness import BPNN, fit_bpnn, reg_metrics
import os

HERE = os.path.dirname(os.path.abspath(__file__))
d = torch.load(os.path.join(HERE, "Mapped_EIS_SOH_tol1.pt"), weights_only=True)
X, y = d["features"].numpy(), d["labels"].numpy()
bids = y[:, 0].astype(int); soh = y[:, 3]

def run_fold(perturb):
    Xd = X.copy()
    if perturb:
        Xd[bids == 1] *= 2.0
    remaining = [b for b in [1, 2, 3, 4] if b != 1]
    val_b, train_b = remaining[0], remaining[1:]
    m_tr, m_va, m_te = np.isin(bids, train_b), (bids == val_b), (bids == 1)
    sc = MinMaxScaler().fit(Xd[m_tr])
    Xs = {k: sc.transform(Xd[m]) for k, m in [("tr", m_tr), ("va", m_va), ("te", m_te)]}
    mu, sd = soh[m_tr].mean(), soh[m_tr].std()
    yz = {k: ((soh[m] - mu) / sd).astype(np.float32) for k, m in [("tr", m_tr), ("va", m_va)]}
    bp = fit_bpnn([256, 8], 0.0, Xs["tr"], yz["tr"], Xs["va"], yz["va"], 42, 100, 10)
    with torch.no_grad():
        ptr = bp(torch.tensor(Xs["tr"], dtype=torch.float32)).numpy() * sd + mu
    return reg_metrics(soh[m_tr], ptr)

a = run_fold(False); b = run_fold(True)
print("baseline train :", np.round(a, 6))
print("perturbed train:", np.round(b, 6))
diff = float(np.abs(np.array(a) - np.array(b)).max())
print(f"max |diff| = {diff:.2e} -> {'PASS: no leakage' if diff < 1e-2 else 'CHECK'}")
