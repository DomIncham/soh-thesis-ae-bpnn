# Round 6, R6-C2 step 4: Ridge baseline (the one simple deterministic baseline the advisor
# requested). "Add one simple deterministic baseline, such as Ridge regression, using exactly
# the same Clean-5T features and protocol. This is only to check whether the transfer failure
# is specific to BPNN instability or is a broader domain-shift problem. Please do not expand
# this into a large model-comparison study."
#
# Protocol mirrors phase5_cs2_clean5t.transfer arm EXACTLY:
#   - same Clean-5T features, same row sets (include_cell / include_cell & cap_ok / dropna)
#   - same two source pools: room = {B0005,B0006,B0007,B0018}, all13 = all 14 NASA cells
#   - same rotated battery-wise selection: each source battery is the validation battery once,
#     candidate score = mean RMSE over rotations
#   - same outer test: the CALCE test battery is never used in selection or fitting
#   - same 5 seeds
# Difference (the point of the baseline): the estimator is deterministic Ridge (closed form),
# so there is NO early-stopping epoch and NO training divergence -> fallback is N/A by design
# (recorded explicitly per R6-C4).
#
# Ridge configuration kept minimal and fixed (no search): alpha in {1e-3, 1e-2, 1e-1, 1, 10,
# 100} selected with the SAME rotated-battery rule; standardization via MinMaxScaler fit on the
# source pool only (identical scaling choice as phase5). No other model, no feature changes.
#
# Outputs: phase6_ridge_transfer.csv (per pool/seed/battery rows, same columns as phase5),
#          phase6_ridge_preds.csv (per-cycle dump, same format as phase6_preds_transfer_full.csv),
#          printed summary + fallback N/A note.
# Diagnostic only (R6-C2.4): NOT a competing model — used to separate BPNN instability from
# broader domain shift.
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import MinMaxScaler

FEATS = ["dis_V_slope", "cc_dur", "cv_dur", "cv_I_slope", "ic_peak_V"]
ROOM = ["B0005", "B0006", "B0007", "B0018"]
SEEDS = [42, 123, 2024, 7, 99]
ALPHAS = [1e-3, 1e-2, 1e-1, 1.0, 10.0, 100.0]
assert "dis_duration" not in FEATS and "dis_mean_V" not in FEATS, "S4 proxy-ban violated"

nasa = pd.read_csv("phase4_features.csv")
nasa = nasa[nasa.include_cell].dropna(subset=FEATS).reset_index(drop=True)
cs2 = pd.read_csv("phase4_cs2_features.csv")
cs2 = cs2[cs2.include_cell & cs2.cap_ok].dropna(subset=FEATS).reset_index(drop=True)

Xc, yc = cs2[FEATS].values, cs2.soh.values
cells = sorted(set(cs2.battery))
rows, pred_rows = [], []
PRED = "phase6_ridge_preds.csv"
import os
if os.path.exists(PRED):
    os.remove(PRED)

def reg_metrics(y, p):
    err = p - y
    return (np.abs(err).mean(), np.sqrt((err ** 2).mean()),
            1 - (err ** 2).sum() / ((y - y.mean()) ** 2).sum())

for pool_name in ["room", "all13"]:
    nd = nasa[nasa.battery.isin(ROOM)] if pool_name == "room" else nasa
    nd = nd.reset_index(drop=True)
    Xn, yn, bn = nd[FEATS].values, nd.soh.values, nd.battery.values
    uniq = np.unique(bn)
    print(f"[ridge {pool_name}] source {len(nd)} rows, {len(uniq)} batteries, "
          f"{len(cells)} CALCE test cells x {len(SEEDS)} seeds", flush=True)
    for seed in SEEDS:
        r = np.random.RandomState(seed)
        # rotated battery-wise selection (identical rule to phase5): each source battery is
        # the validation battery once; score = mean RMSE over rotations. Ridge is closed-form,
        # so the "rotation" only enters through the standardizer + fit data.
        cand_scores = []
        for alpha in ALPHAS:
            rmses = []
            for v in uniq:
                m_fit, m_va = bn != v, bn == v
                sc = MinMaxScaler().fit(Xn[m_fit])
                mu, sd = yn[m_fit].mean(), yn[m_fit].std()
                rg = Ridge(alpha=alpha).fit(sc.transform(Xn[m_fit]), (yn[m_fit] - mu) / sd)
                pv = rg.predict(sc.transform(Xn[m_va])) * sd + mu
                rmses.append(float(np.sqrt(np.mean((pv - yn[m_va]) ** 2))))
            cand_scores.append((float(np.mean(rmses)), alpha))
        best_rmse, best_alpha = min(cand_scores)
        print(f"[ridge {pool_name} s{seed}] selected alpha={best_alpha} "
              f"(mean val RMSE {best_rmse:.3f}) — fallback N/A (deterministic)", flush=True)
        # refit on the FULL source pool with the selected alpha, evaluate every CALCE cell
        sc = MinMaxScaler().fit(Xn)
        mu, sd = yn.mean(), yn.std()
        rg = Ridge(alpha=best_alpha).fit(sc.transform(Xn), (yn - mu) / sd)
        for c_ in cells:
            m_c = cs2.battery.values == c_
            p = rg.predict(sc.transform(Xc[m_c])) * sd + mu
            pd.DataFrame(dict(seed=seed, arm="ridge", pool=pool_name, cell=c_,
                              cycle=np.arange(1, int(m_c.sum()) + 1),
                              y=np.round(yc[m_c], 4), yhat=np.round(p, 4))
                         ).to_csv(PRED, mode="a", header=not os.path.exists(PRED), index=False)
            mae, rmse, r2 = reg_metrics(yc[m_c], p)
            rows.append(dict(arm="ridge", pool=pool_name, seed=seed, test_battery=c_,
                             n_cycles=int(m_c.sum()), cfg=f"ridge/a={best_alpha}",
                             sel_epochs="N/A", sel_degenerate="N/A",
                             MAE=round(float(mae), 3), RMSE=round(float(rmse), 3),
                             R2=round(float(r2), 3)))
df = pd.DataFrame(rows)
df.to_csv("phase6_ridge_transfer.csv", index=False)
print("\n== phase6_ridge_transfer.csv:", len(df), "rows ==")
print("fallback: N/A for every row (deterministic estimator) — recorded per R6-C4")
print(df.groupby("pool")[["MAE", "RMSE", "R2"]].agg(["mean", "median"]).round(3).to_string())
print("\n=== per battery (mean across seeds) ===")
print(df.groupby(["pool", "test_battery"])[["MAE", "R2"]].mean().round(3).to_string())
