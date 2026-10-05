# Bug-check part 2: Phase-1 protocol on ONLY the 4 original cells (k=3 train, 5 seeds).
# Reference: steps14_16_refit (Phase 1 refit_on_3) gave TD-All mean R2 = 0.923.
import numpy as np, pandas as pd, itertools, sys, os
sys.path.insert(0, r"C:\Master Degree\Thesis\Autoencoder\round3_phase1")
os.chdir(r"C:\Master Degree\Thesis\Autoencoder\round3_phase1")
import r3common as rc
from sklearn.preprocessing import MinMaxScaler

rc.set_device("cpu")
df = pd.read_csv("phase4_features.csv")
sub = df[df.battery.isin(["B0005", "B0006", "B0007", "B0018"])].dropna(subset=rc.FEATS_ALL).reset_index(drop=True)
X, b4, s4 = sub[rc.FEATS_ALL].values, sub.battery.astype("category").cat.codes.values, sub.soh.values
qref = df.groupby("battery").capacity.apply(lambda s: s.head(5).mean())
rng = {n: (df[df.battery == n].capacity.max() - df[df.battery == n].capacity.min()) / qref[n] * 100
       for n in ["B0005", "B0006", "B0007", "B0018"]}
r2s, rmses = [], []
for seed in [42, 123, 2024, 7, 99]:
    r = np.random.RandomState(seed)
    for test_i in range(4):
        pool = [b for b in range(4) if b != test_i]
        tr = list(r.choice(pool, size=3, replace=False))
        val_b, fit_b = tr[0], tr
        m_te, m_va = b4 == test_i, b4 == val_b
        m_fit = np.isin(b4, fit_b)
        m_sl = np.isin(b4, [b for b in fit_b if b != val_b])
        sc = MinMaxScaler().fit(X[m_sl])
        mu, sd = s4[m_sl].mean(), s4[m_sl].std()
        cands = []
        for dm, l2 in itertools.product(rc.ARCHS, rc.L2S):
            bp, ep = rc.fit_bpnn_ep([8] + dm, l2, sc.transform(X[m_sl]), (s4[m_sl] - mu) / sd,
                                    sc.transform(X[m_va]), (s4[m_va] - mu) / sd, seed, 300, 20)
            v = float(np.sqrt(np.mean((rc.predict(bp, sc.transform(X[m_va]), mu, sd) - s4[m_va]) ** 2)))
            cands.append((v, dm, l2, ep))
        okc = [c for c in cands if c[3] >= rc.MIN_EP and np.isfinite(c[0])]
        if not okc:
            print(f"seed {seed} test {test_i}: no converged candidate (skipped)")
            continue
        v, dm, l2, ep = min(okc, key=lambda c: c[0])
        sc2 = MinMaxScaler().fit(X[m_fit])
        mu2, sd2 = s4[m_fit].mean(), s4[m_fit].std()
        bp_rf, _ = rc.fit_bpnn_ep([8] + dm, l2, sc2.transform(X[m_fit]), (s4[m_fit] - mu2) / sd2,
                                  None, None, seed, 300, 20, epochs=ep)
        p = rc.predict(bp_rf, sc2.transform(X[m_te]), mu2, sd2)
        mae, rmse, r2 = rc.reg_metrics(s4[m_te], p)
        r2s.append(r2); rmses.append(rmse)
        print(f"seed {seed} test {test_i}: R2={r2:.3f}")
print(f"\n4-cell-only LOBO: mean R2 = {np.nanmean(r2s):.3f}, mean RMSE = {np.nanmean(rmses):.3f}")
print("Phase 1 reference (steps14_16, refit_on_3, same seeds): R2 = 0.923")
