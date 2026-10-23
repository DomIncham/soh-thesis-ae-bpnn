# P6-5 interventional flag test: quantile_varrestored (all13, seed 42, single-pool probe).
# Purpose: close the La-quantile "degenerate alignment" flag. If restoring per-feature std in
# quantile space returns MedAE to ~L0 levels, the quantile gain was a mean-predictor artifact
# (saturation). If it stays low, the signal is real and the finding upgrades.
import os
import numpy as np
import pandas as pd
import r3common as rc
import phase6_alignment_ladder as lad
from sklearn.preprocessing import QuantileTransformer

rc.set_device("cpu")
nasa, cs2 = lad.pools()
Xc, yc = cs2[lad.FEATS].values, cs2.soh.values
cells = sorted(set(cs2.battery))

nd = nasa.reset_index(drop=True)  # all13
Xn_, yn_, bn_ = nd[lad.FEATS].values, nd.soh.values, nd.bid.values
dims, l2, ep, deg = lad.select_config(42, Xn_, yn_, bn_, 300, 20)
print("selected cfg:", dims, l2, "ep", ep, "DEG", deg, flush=True)

Sc = QuantileTransformer(n_quantiles=100, output_distribution="uniform")
Xtr = Sc.fit_transform(Xn_)
Xte_all = Sc.transform(Xc)
ratios = []
for j in range(Xtr.shape[1]):
    s_src, s_tgt = Xtr[:, j].std(), Xte_all[:, j].std()
    r = s_src / s_tgt if s_tgt > 1e-12 else 1.0
    ratios.append(r)
    Xte_all[:, j] *= r
print("restore ratios per feature:", np.round(ratios, 2).tolist(), flush=True)

mu, sd = yn_.mean(), yn_.std()
bp = lad.fit_backbone(Xtr, yn_, dims, l2, ep, 42, 300, 20)
errs, maes = [], []
for c_ in cells:
    m_c = cs2.battery.values == c_
    p = lad.predict_scaled(bp, Xte_all[np.where(m_c)[0]], mu, sd)
    mae, rmse, r2 = lad.reg(yc[m_c], p)
    errs.append(mae)
    print(f"{c_}: MAE {mae:.2f} R2 {r2:.2f}", flush=True)
print("varrestored all13 s42: mean MAE", round(float(np.mean(errs)), 2),
      "| reference: quantile-plain median 5.51, L0 20.99", flush=True)
