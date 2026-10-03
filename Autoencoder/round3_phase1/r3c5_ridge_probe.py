# R3-C5 first step: is the proxy-free failure a MODEL limit or a FEATURE limit?
# The BPNN on TD-Clean-6 reaches mean R2 0.490 under nested LOBO. Before adding features, establish
# whether a much simpler model does better on the SAME features - if ridge is no better, the
# features are the ceiling and Phase 3 has to be about inputs, not about the network.
# Also runs a leave-one-feature-out sweep with ridge, which is the cheap per-feature importance
# table the proxy argument needs.
# Same protocol discipline: fold-train-only scaling, inner validation on a second battery to pick
# alpha, outer test battery untouched.
import itertools
import os
import sys
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import MinMaxScaler

sys.path.insert(0, r"C:\Master Degree\Thesis\Autoencoder\round3_phase1")
import r3common as R
from r3common import BATT, FEATS_ALL, OUT, load_td, soh_range_and_qref

REV = {v: k for k, v in BATT.items()}
ALPHAS = [1e-4, 1e-3, 1e-2, 1e-1, 1.0, 10.0]
SEEDS = [42, 7, 123, 2024, 11]


def lo_fold(X, bids, soh, test_b, seed):
    rem = [b for b in [1, 2, 3, 4] if b != test_b]
    val_b, tr_b = rem[0], rem[1:]
    m_tr, m_va, m_te = np.isin(bids, tr_b), bids == val_b, bids == test_b
    sc = MinMaxScaler().fit(X[m_tr])
    mu, sd = soh[m_tr].mean(), soh[m_tr].std()
    A = sc.transform(X[m_tr]); y = (soh[m_tr] - mu) / sd
    V = sc.transform(X[m_va])
    best, bv = None, np.inf
    for a in ALPHAS:
        m = Ridge(alpha=a).fit(A, y)
        v = np.sqrt(np.mean((m.predict(V) * sd + mu - soh[m_va]) ** 2))
        if v < bv:
            bv, best = v, a
    m = Ridge(alpha=best).fit(A, y)
    yh = m.predict(sc.transform(X[m_te])) * sd + mu
    yt = soh[m_te]
    r2 = 1 - ((yt - yh) ** 2).sum() / ((yt - yt.mean()) ** 2).sum()
    return float(r2), float(np.sqrt(np.mean((yt - yh) ** 2))), best


print("=" * 92)
print("[A] RIDGE under nested LOBO - same folds, same seeds, same scaling as the BPNN")
print("=" * 92)
sets = {"TD-All (8)": FEATS_ALL,
        "TD-Proxy-Free (7)": R.FEATS_PROXY_FREE,
        "TD-Clean-6 (6)": R.FEATS_CLEAN6,
        "TD-Clean-4 (4)": R.FEATS_CLEAN4}
res = []
for name, feats in sets.items():
    X, bids, soh, cyc = load_td(feats)
    rs = [lo_fold(X, bids, soh, b, s)[0] for s in SEEDS for b in [1, 2, 3, 4]]
    res.append(dict(setting=name, mean_R2=np.mean(rs), median_R2=np.median(rs),
                    std=np.std(rs, ddof=1), n=len(rs)))
print(pd.DataFrame(res).round(3).to_string(index=False))
print("\nBPNN reference (same protocol): TD-All 0.927 | Proxy-Free 0.845 | Clean-6 0.490 | Clean-4 -0.400")

print("\n" + "=" * 92)
print("[B] LEAVE-ONE-FEATURE-OUT with ridge (full 8-feature set, same protocol)")
print("=" * 92)
rows = []
for drop in [None] + FEATS_ALL:
    feats = [f for f in FEATS_ALL if f != drop] if drop else list(FEATS_ALL)
    X, bids, soh, cyc = load_td(feats)
    rs = [lo_fold(X, bids, soh, b, s)[0] for s in SEEDS for b in [1, 2, 3, 4]]
    rows.append(dict(dropped=drop or "(none)", n_feats=len(feats), mean_R2=np.mean(rs)))
t = pd.DataFrame(rows)
t["delta_vs_full"] = (t.mean_R2 - t.loc[t.dropped == "(none)", "mean_R2"].iloc[0])
print(t.round(4).sort_values("delta_vs_full").to_string(index=False))
print("\n  most negative delta = the feature whose removal hurts most = the biggest carrier of signal")
t.to_csv(os.path.join(OUT, "r3c5_ridge_probe.csv"), index=False)
print("\nsaved: r3c5_ridge_probe.csv")