# Round 6, P6-4 completion: Ridge WITHIN-CALCE control (the missing quadrant).
#
# Advisor question (R6-C2.4): is the transfer failure BPNN-specific instability or a broader
# domain-shift problem? To answer with the single Ridge baseline (no model-comparison expansion),
# we need the 2x2:
#                 within-CALCE (in-domain)      NASA->CALCE (transfer)
#   BPNN          phase5 within arm (0.928*)    phase5 transfer arm
#   Ridge         THIS SCRIPT                   phase6_ridge_baseline.py
# (*phase5 within median R2 across full runs; verified from phase5_cs2_within_c5t_full.csv)
#
# If Ridge-within is GOOD and Ridge-transfer is BAD, then no linear model works cross-dataset
# while linear models work in-domain => the failure is the domain shift itself, not the model
# class, not merely BPNN training noise. This upgrades the P6-4 conclusion from
# "pure linear model is worse" to a model-class-controlled statement.
#
# Protocol mirrors phase5 within arm EXACTLY:
#   - LOCO over the 8 CALCE cells; the 7 remaining cells are the fit pool
#   - rotated selection: each of the 7 training cells is the validation battery once,
#     candidate score = mean RMSE across rotations
#   - same alpha grid {1e-3..100}; same MinMaxScaler fit on the fit pool only
#   - same 5 seeds (Ridge deterministic -> seeds only matter through nothing here; recorded
#     for format parity). Fallback N/A (R6-C4).
# Outputs: phase6_ridge_within.csv, phase6_ridge_within_preds.csv, printed 2x2 summary.
import os
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import MinMaxScaler

FEATS = ["dis_V_slope", "cc_dur", "cv_dur", "cv_I_slope", "ic_peak_V"]
ALPHAS = [1e-3, 1e-2, 1e-1, 1.0, 10.0, 100.0]
SEEDS = [42, 123, 2024, 7, 99]

cs2 = pd.read_csv("phase4_cs2_features.csv")
cs2 = cs2[cs2.include_cell & cs2.cap_ok].dropna(subset=FEATS).reset_index(drop=True)
Xc, yc, bc = cs2[FEATS].values, cs2.soh.values, cs2.battery.values
cells_u = sorted(set(bc))
PRED = "phase6_ridge_within_preds.csv"
if os.path.exists(PRED):
    os.remove(PRED)

rows = []
for seed in SEEDS:
    for test_name in cells_u:
        pool_cells = sorted(set(bc[bc != test_name]))
        cands = []
        for alpha in ALPHAS:
            rmses = []
            for v in pool_cells:
                m_fit = np.isin(bc, [c for c in pool_cells if c != v])
                m_va = bc == v
                sc = MinMaxScaler().fit(Xc[m_fit])
                mu, sd = yc[m_fit].mean(), yc[m_fit].std()
                rg = Ridge(alpha=alpha).fit(sc.transform(Xc[m_fit]), (yc[m_fit] - mu) / sd)
                pv = rg.predict(sc.transform(Xc[m_va])) * sd + mu
                rmses.append(float(np.sqrt(np.mean((pv - yc[m_va]) ** 2))))
            cands.append((float(np.mean(rmses)), alpha))
        best_rmse, best_alpha = min(cands)
        m_fit = np.isin(bc, pool_cells)
        m_te = bc == test_name
        sc = MinMaxScaler().fit(Xc[m_fit])
        mu, sd = yc[m_fit].mean(), yc[m_fit].std()
        rg = Ridge(alpha=best_alpha).fit(sc.transform(Xc[m_fit]), (yc[m_fit] - mu) / sd)
        p = rg.predict(sc.transform(Xc[m_te])) * sd + mu
        pd.DataFrame(dict(seed=seed, arm="ridge_within", pool="cs2", cell=test_name,
                          cycle=np.arange(1, int(m_te.sum()) + 1),
                          y=np.round(yc[m_te], 4), yhat=np.round(p, 4))
                     ).to_csv(PRED, mode="a", header=not os.path.exists(PRED), index=False)
        err = p - yc[m_te]
        mae = np.abs(err).mean(); rmse = np.sqrt((err ** 2).mean())
        r2 = 1 - (err ** 2).sum() / ((yc[m_te] - yc[m_te].mean()) ** 2).sum()
        rows.append(dict(arm="ridge_within", seed=seed, test_battery=test_name,
                         n_cycles=int(m_te.sum()), cfg=f"ridge/a={best_alpha}",
                         sel_epochs="N/A", sel_degenerate="N/A",
                         MAE=round(float(mae), 3), RMSE=round(float(rmse), 3),
                         R2=round(float(r2), 3)))
        print(f"[ridge-within s{seed}] test={test_name} alpha={best_alpha} R2={r2:.3f}", flush=True)

df = pd.DataFrame(rows)
df.to_csv("phase6_ridge_within.csv", index=False)

# ---- 2x2 summary ----
def med(d, col="MAE"):
    return d[col].median()

tr_ridge = pd.read_csv("phase6_ridge_transfer.csv")
tr_bpnn = pd.read_csv("phase6_transfer_rerun_c5t.csv")
wi_bpnn = pd.read_csv("phase5_cs2_within_c5t_full.csv")
wi_all = pd.read_csv("phase6_ridge_within.csv")

print("\n== 2x2: median MAE (R2 where available) ==")
print(f"BPNN  within-CALCE : MAE {med(wi_bpnn):.3f}  (median R2 {wi_bpnn.R2.median():.3f})")
print(f"Ridge within-CALCE : MAE {med(wi_all):.3f}  (median R2 {wi_all.R2.median():.3f})")
print(f"BPNN  transfer     : MAE {med(tr_bpnn):.3f}")
print(f"Ridge transfer     : MAE {med(tr_ridge):.3f}")
print("\nInterpretation rule: Ridge-within good + Ridge-transfer bad => domain shift,")
print("not model class. Ridge-within bad too => linear model class itself insufficient.")
print("\nfallback: N/A for every row (deterministic) — R6-C4")
