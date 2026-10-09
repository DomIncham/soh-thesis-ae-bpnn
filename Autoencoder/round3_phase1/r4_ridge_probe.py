# Ridge probe for the Round 4 report (Section 1.1, observation 3): does t_40_41 help without
# any model selection? Same 631 rows, same folds, ridge instead of the BPNN - if the direction
# matches the nested runs, the Clean-8 drop is a data property, not a selection artifact.
# Usage: python r4_ridge_probe.py
import numpy as np, pandas as pd
import r3common as rc
from sklearn.linear_model import Ridge
from sklearn.preprocessing import MinMaxScaler
ch = pd.read_csv('../nested_lobo/charge_features.csv'); ch.columns = [c.strip() for c in ch.columns]
mask = np.isfinite(ch[['ic_peak_V', 't_40_41']].values).all(axis=1)
X6, bids, soh, cyc = rc.load_td(rc.FEATS_CLEAN6)
bids, soh = bids[mask], soh[mask]
X6 = X6[mask]
BATT = {1: 'B0005', 2: 'B0006', 3: 'B0007', 4: 'B0018'}
for extra, name in [([], 'C6-631r'), (['ic_peak_V'], 'C7'), (['ic_peak_V', 't_40_41'], 'C8')]:
    X = np.hstack([X6, ch.loc[mask, extra].values]) if extra else X6
    acc = {b: [] for b in [1, 2, 3, 4]}
    for seed in [42, 7, 123]:
        for tb in [1, 2, 3, 4]:
            rem = [b for b in [1, 2, 3, 4] if b != tb]
            m_te, m_fit = bids == tb, np.isin(bids, rem)
            sc = MinMaxScaler().fit(X[m_fit])
            model = Ridge(alpha=1.0).fit(sc.transform(X[m_fit]), soh[m_fit])
            p = model.predict(sc.transform(X[m_te]))
            ss_res = ((soh[m_te] - p) ** 2).sum(); ss_tot = ((soh[m_te] - soh[m_te].mean()) ** 2).sum()
            acc[tb].append(1 - ss_res / ss_tot)
    print(name, {BATT[b]: round(float(np.mean(v)), 3) for b, v in acc.items()})
