# P6B verification: is the L0 dump backbone the same model that Lc/Adapt2 warm-started from?
# Method: retrain the pool backbone for (room, seed 42) with the EXACT Lc code path
# (MinMaxScaler fit on source pool only, cfg [8,4]/l2=0.0001, sel_epochs=210, seed 42)
# and compare its predictions on all 8 CALCE cells against the L0 dump rows.
# Result (2026-11-13): max |diff| = 0.0219 %SOH (8-thread and 1-thread runs identical),
# i.e. deterministic reproduction at noise level, two orders below the effect sizes
# (run MAE 10-23 %SOH). The two backbones are treated as equivalent with this
# tolerance disclosed. NOT bit-exact — do not claim identity, claim tolerance.
import numpy as np
import pandas as pd
import r3common as rc
from sklearn.preprocessing import MinMaxScaler

FEATS = ["dis_V_slope", "cc_dur", "cv_dur", "cv_I_slope", "ic_peak_V"]
ROOM = ["B0005", "B0006", "B0007", "B0018"]
rc.set_device("cpu")
nasa = pd.read_csv("phase4_features.csv")
nasa = nasa[nasa.include_cell].dropna(subset=FEATS).reset_index(drop=True)
nd = nasa[nasa.battery.isin(ROOM)].reset_index(drop=True)
Xn, yn = nd[FEATS].values, nd.soh.values
sc = MinMaxScaler().fit(Xn)
Xs = sc.transform(Xn)
bp, _ = rc.fit_bpnn_ep([Xs.shape[1]] + [8, 4], 0.0001, Xs, (yn - yn.mean()) / yn.std(),
                       None, None, 42, 300, 20, epochs=210)
cs2 = pd.read_csv("phase4_cs2_features.csv")
cs2 = cs2[cs2.include_cell & cs2.cap_ok].dropna(subset=FEATS).reset_index(drop=True)
d = pd.read_csv("phase6_preds_transfer_full.csv", low_memory=False)
d0 = d[(d.pool == "room") & (d.seed == 42)]
maxdiff = 0.0
for cell in sorted(d0.cell.unique()):
    X = sc.transform(cs2[cs2.battery == cell][FEATS].values)
    p = rc.predict(bp, X, yn.mean(), yn.std())
    ref = d0[d0.cell == cell].sort_values("cycle").yhat.values
    maxdiff = max(maxdiff, float(np.abs(np.round(p, 4) - ref).max()))
print(f"max |diff| = {maxdiff:.4f} %SOH")
assert maxdiff < 0.05, "backbone reproduction exceeded the disclosed noise tolerance"
