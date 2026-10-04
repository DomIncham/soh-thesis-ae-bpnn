# Phase 3, item 5.4 (advisor R3-C5 item 4): monotonic / physical prior.
# Advisor's words: "predict the degradation increment dSOH and accumulate it (as in EWDC [10]),
# or add a monotonicity penalty to the BPNN."
#
# Implemented: the first option. The model predicts dSOH(k) = SOH(k) - SOH(k-1) from the features,
# and the SOH series is rebuilt by accumulation:
#     SOH_pred(k) = ANCHOR + sum_{j<=k} dSOH_pred(j)
#
# ANCHOR = 100 %SOH, applied at the battery's first available cycle. This is DEFINITIONAL, not label
# leakage: SOH is defined as Q/Qref with Qref = mean of the first five discharge capacities, so a
# cell starts at ~100 %SOH by construction. The true first-cycle SOH is not exactly 100 (B0005 is
# 100.55), so a small constant offset is carried; it is recorded per fold as `anchor_offset`.
# The EWDC paper itself is NOT in the local materials (searched all 46 PDFs in Journal Discovery),
# so their convention could not be copied - confirming it belongs to R3-C9 citation verification.
#
# Selection uses the same grid, the same guard and the same fold-train-only scaling as every other
# Phase 1/2/3 run, but scores a candidate by the RMSE of the ACCUMULATED SOH on the inner-validation
# battery, because that is the quantity being optimised.
#
# A monotone variant is also reported: the accumulated series projected onto the non-increasing
# cone (cumulative minimum). Both are reported side by side; neither is preferred silently.
# Usage: python bpnn_monotonic.py [--seeds 42,7,123,2024,11] [--device cpu]
import argparse
import itertools
import os
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

import r3common as R
from r3common import (BATT, ARCHS, L2S, MIN_EP, RETRAIN_EP, load_td, soh_range_and_qref,
                      fit_bpnn_ep, predict, reg_metrics, OUT)

ANCHOR = 100.0
SETS = {"TD-Clean-7": ["ic_peak_V"], "TD-Clean-8": ["t_40_41", "ic_peak_V"]}

ap = argparse.ArgumentParser()
ap.add_argument("--seeds", default="42,7,123,2024,11")
ap.add_argument("--device", default="cpu", choices=["cpu", "cuda", "auto"])
ap.add_argument("--tag", default="cpu")
a = ap.parse_args()

R.set_device(a.device)
seeds = [int(s) for s in a.seeds.split(",")]

ch = pd.read_csv(os.path.join(os.path.dirname(R.TD_CSV), "charge_features.csv"))
ch.columns = [c.strip() for c in ch.columns]
tdf = pd.read_csv(R.TD_CSV)
tdf.columns = [c.strip() for c in tdf.columns]
assert np.array_equal(ch.battery.values, tdf.battery.values) and \
       np.array_equal(ch.cycle.values, tdf.cycle.values), "ALIGNMENT: charge_features.csv mismatch"

mask = np.isfinite(ch["ic_peak_V"].values) & np.isfinite(ch["t_40_41"].values)
print(f"rows kept: {int(mask.sum())} / {len(ch)} (same 631-row subset as the other Phase 3 runs)")


def run_fold_dsoh(X, bids, soh, cyc, dsoh, test_b, seed, bp_max, pat, setting):
    n_in = X.shape[1]
    remaining = [b for b in [1, 2, 3, 4] if b != test_b]
    val_b, train_b = remaining[0], remaining[1:]
    has_d = np.isfinite(dsoh)
    m_tr = np.isin(bids, train_b) & has_d
    m_all = np.isin(bids, remaining) & has_d
    m_te = bids == test_b

    def battery_rows(b):
        idx = np.where(bids == b)[0]
        return idx[np.argsort(cyc[idx])]

    # ---- selection: score a candidate by the RMSE of the ACCUMULATED SOH on the val battery ----
    sc = MinMaxScaler().fit(X[m_tr])
    assert np.allclose(sc.data_min_, X[m_tr].min(0)), "LEAKAGE: selection scaler != fold-train"
    mu, sd = dsoh[m_tr].mean(), dsoh[m_tr].std()
    vidx = battery_rows(val_b)
    vra = vidx[np.isfinite(dsoh[vidx])]                 # every row except the first has a delta
    assert len(vra) == len(vidx) - 1, "CHECK: val delta mask is not 'all but the first'"
    va_s = sc.transform(X[vra])
    y_va = (dsoh[vra] - mu) / sd

    cands = []
    for dims, l2 in itertools.product(ARCHS, L2S):
        bp, ep = fit_bpnn_ep([n_in] + dims, l2, sc.transform(X[m_tr]), (dsoh[m_tr] - mu) / sd,
                             va_s, y_va, seed, bp_max, pat)
        d_pred = predict(bp, va_s, mu, sd)
        pred_soh = ANCHOR + np.concatenate([[0.0], np.cumsum(d_pred)])
        v = float(np.sqrt(np.mean((pred_soh - soh[vidx]) ** 2)))
        cands.append((v, dims, l2, ep, bp))
    ok = [c for c in cands if c[3] >= MIN_EP]
    sel_degenerate = len(ok) < len(cands)
    if not ok:
        _, dims, l2, _, _ = min(cands, key=lambda c: c[0])
        ok = [(min(c[0] for c in cands), dims, l2, RETRAIN_EP, None)]
        sel_degenerate = True
        print(f"  [guard] no candidate converged; using {dims}/l2={l2} {RETRAIN_EP}ep")
    v, dims, l2, ep, _ = min(ok, key=lambda c: c[0])

    # ---- refit on all 3 remaining batteries, then accumulate on the test battery ----
    sc2 = MinMaxScaler().fit(X[m_all])
    assert np.allclose(sc2.data_min_, X[m_all].min(0)), "LEAKAGE: refit scaler != 3-battery train"
    mu2, sd2 = dsoh[m_all].mean(), dsoh[m_all].std()
    bp_rf, _ = fit_bpnn_ep([n_in] + dims, l2, sc2.transform(X[m_all]), (dsoh[m_all] - mu2) / sd2,
                           None, None, seed, bp_max, pat, epochs=ep)

    tidx = battery_rows(test_b)
    tra = tidx[np.isfinite(dsoh[tidx])]
    d_pred = predict(bp_rf, sc2.transform(X[tra]), mu2, sd2)
    pred_soh = ANCHOR + np.concatenate([[0.0], np.cumsum(d_pred)])
    pred_mono = np.minimum.accumulate(pred_soh)
    true_soh = soh[tidx]
    assert len(pred_soh) == len(true_soh) == len(tidx), "CHECK: accumulation length mismatch"

    def metrics(y, yh):
        mae, rmse, r2 = reg_metrics(y, yh)
        return dict(MAE=float(mae), RMSE=float(rmse), R2=float(r2),
                    MAPE=float(np.mean(np.abs((y - yh) / y)) * 100))
    mr = metrics(true_soh, pred_soh)
    mm = metrics(true_soh, pred_mono)

    row = dict(setting=setting, stage="dsoh_refit", seed=seed, test_battery=BATT[test_b],
               cfg=f"{dims}/l2={l2}", sel_epochs=ep, sel_degenerate=sel_degenerate,
               sel_val_rmse=round(v, 4), anchor_offset=round(float(true_soh[0] - ANCHOR), 4),
               n_test=len(tidx),
               test_MAE=round(mr["MAE"], 4), test_RMSE=round(mr["RMSE"], 4),
               test_R2=round(mr["R2"], 4), test_MAPE=round(mr["MAPE"], 4),
               mono_MAE=round(mm["MAE"], 4), mono_RMSE=round(mm["RMSE"], 4),
               mono_R2=round(mm["R2"], 4), mono_MAPE=round(mm["MAPE"], 4))
    pred = pd.DataFrame(dict(setting=setting, stage="dsoh_refit", seed=seed,
                             test_battery=BATT[test_b], cycle=cyc[tidx],
                             y_true=true_soh, y_pred=pred_soh, y_pred_mono=pred_mono))
    return row, pred


rows, preds = [], []
for name, extra in SETS.items():
    Xb, bids, soh, cyc = load_td(R.FEATS_CLEAN6)
    Xb, bids, soh, cyc = Xb[mask], bids[mask], soh[mask], cyc[mask]
    X = np.hstack([Xb, ch.loc[mask, extra].values.astype(float)])
    assert np.isfinite(X).all(), "NaN in the feature matrix"

    # dSOH per battery, in cycle order. Self-test: true deltas must rebuild the true series.
    dsoh = np.full(len(soh), np.nan)
    for b in [1, 2, 3, 4]:
        idx = np.where(bids == b)[0]
        idx = idx[np.argsort(cyc[idx])]
        dsoh[idx[1:]] = np.diff(soh[idx])
        assert np.allclose(soh[idx][0] + np.cumsum(dsoh[idx[1:]]), soh[idx][1:]), \
            f"CHECK: true dSOH does not rebuild the true SOH series for battery {b}"
    print(f"\n--- {name}: {X.shape[1]} features | dSOH self-test passed for all 4 batteries")

    for seed in seeds:
        for b in [1, 2, 3, 4]:
            r, p = run_fold_dsoh(X, bids, soh, cyc, dsoh, b, seed, 500, 30, name)
            rows.append(r)
            preds.append(p)
            print(f"{name:12s} seed{seed:<5d} test={BATT[b]} cfg={r['cfg']} ep={r['sel_epochs']} "
                  f"| R2={r['test_R2']:+.3f} RMSE={r['test_RMSE']:.3f} "
                  f"| mono R2={r['mono_R2']:+.3f} RMSE={r['mono_RMSE']:.3f} "
                  f"| anchor_offset={r['anchor_offset']:+.2f}")

res = pd.DataFrame(rows)
res["device"] = R.DEVICE.type
res.to_csv(os.path.join(OUT, f"phase3_dsoh_{a.tag}_results.csv"), index=False)
pd.concat(preds, ignore_index=True).to_csv(
    os.path.join(OUT, f"phase3_dsoh_{a.tag}_preds.csv"), index=False)

print("\n=== accumulated SOH, mean / median / std over 4 folds x 5 seeds ===")
print(res.groupby("setting")[["test_R2", "test_RMSE", "test_MAPE",
                              "mono_R2", "mono_RMSE", "mono_MAPE"]]
      .agg(["mean", "median", "std"]).round(3).to_string())
print("\ntest_R2 per fold (mean over seeds):")
print(res.pivot_table(index="test_battery", columns="setting", values="test_R2",
                      aggfunc="mean").round(3).to_string())
print("\nanchor offset per fold (true first-cycle SOH - 100):")
print(res.pivot_table(index="test_battery", columns="setting", values="anchor_offset",
                      aggfunc="mean").round(3).to_string())
print(f"\ndegenerate fold-seeds: {int(res.sel_degenerate.sum())} / {len(res)}")
print("\nreference (same 631 rows, absolute-SOH model): Clean-7 0.772 | Clean-8 0.810")
print("saved")