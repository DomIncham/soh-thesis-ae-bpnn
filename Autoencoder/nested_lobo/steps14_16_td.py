# Steps 14-16: time-domain baseline (TD-Ridge, TD-BPNN) vs EIS pipelines under the same nested-LOBO protocol
# Pipelines: B1 mean | TD_ridge | TD_bpnn | + reuse P1_raw / P3_ae from steps9_10_results.csv (Step 15 comparison)
# nRMSE denominator = fixed per-battery SOH range from the full capacity log (same for all modalities).
import argparse, itertools, os
import numpy as np, pandas as pd, torch
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import Ridge

from nested_lobo_harness import BPNN, fit_bpnn, reg_metrics

HERE = os.path.dirname(os.path.abspath(__file__))
BATT = {1: "B0005", 2: "B0006", 3: "B0007", 4: "B0018"}
ARCHS, L2S, ALPHAS = [[8], [16], [8, 4]], [0.0, 1e-4], [0.1, 1.0, 10.0]

def rmse_(a, b): return float(np.sqrt(np.mean((np.asarray(a) - np.asarray(b)) ** 2)))

def run(args):
    smoke = args.smoke
    seeds = [42] if smoke else [42, 7, 123]
    folds = [1] if smoke else [1, 2, 3, 4]
    bp_max, pat = 100 if smoke else 500, 10 if smoke else 30
    td = pd.read_csv(os.path.join(HERE, "time_domain_features.csv"))
    feats = ["dis_duration", "dis_mean_V", "dis_mean_T", "dis_V_slope", "cc_dur", "cv_dur", "cv_I_slope", "ch_mean_T"]
    X, bids, soh = td[feats].values, td.battery.values.astype(int), td.soh.values
    cap = pd.read_csv(os.path.join(HERE, "..", "NASA_Capacity_Data.csv"), dtype={"Battery_ID": int, "Cycle": int})
    soh_range = cap.groupby("Battery_ID").Capacity_Ah.agg(lambda s: s.max() - s.min()) / \
        cap.sort_values("Cycle").groupby("Battery_ID").head(5).groupby("Battery_ID").Capacity_Ah.mean() * 100
    eis = pd.read_csv(os.path.join(HERE, "steps9_10_results.csv"))
    rows = []
    for seed, test_b in itertools.product(seeds, folds):
        remaining = [b for b in [1, 2, 3, 4] if b != test_b]
        val_b, train_b = remaining[0], remaining[1:]
        m_tr, m_va, m_te = np.isin(bids, train_b), (bids == val_b), (bids == test_b)
        sc = MinMaxScaler().fit(X[m_tr])
        assert np.allclose(sc.data_min_, X[m_tr].min(0)), "LEAKAGE: scaler != fold-train"
        Xs = {k: sc.transform(X[m]) for k, m in [("tr", m_tr), ("va", m_va), ("te", m_te)]}
        mu, sd = soh[m_tr].mean(), soh[m_tr].std()
        yz = {k: ((soh[m] - mu) / sd).astype(np.float32) for k, m in [("tr", m_tr), ("va", m_va)]}
        nr = float(soh_range.loc[test_b])
        # B1 mean
        pred = float(soh[m_tr].mean())
        _, vrmse, _ = reg_metrics(soh[m_va], np.full(m_va.sum(), pred))
        tmae, trmse_, tr2 = reg_metrics(soh[m_te], np.full(m_te.sum(), pred))
        rows.append(dict(pipeline="B1_mean", seed=seed, test_battery=BATT[test_b], cfg="mean(train)",
                         val_rmse=round(vrmse, 4), test_MAE=round(tmae, 4), test_RMSE=round(trmse_, 4),
                         test_R2=round(tr2, 4), nRMSE=round(trmse_ / nr, 4)))
        # TD ridge
        best = None
        for a in ALPHAS:
            r = Ridge(alpha=a).fit(Xs["tr"], soh[m_tr])
            v = rmse_(r.predict(Xs["va"]), soh[m_va])
            if best is None or v < best[0]:
                best = (v, f"alpha={a}", r.predict(Xs["te"]), r.predict(Xs["tr"]))
        v, cfg, pte, ptr = best
        tmae, trmse_, tr2 = reg_metrics(soh[m_te], pte)
        rows.append(dict(pipeline="TD_ridge", seed=seed, test_battery=BATT[test_b], cfg=cfg,
                         val_rmse=round(v, 4), test_MAE=round(tmae, 4), test_RMSE=round(trmse_, 4),
                         test_R2=round(tr2, 4), nRMSE=round(trmse_ / nr, 4)))
        # TD BPNN
        best = None
        for dims, l2 in itertools.product(ARCHS, L2S):
            bp = fit_bpnn([8] + dims, l2, Xs["tr"], yz["tr"], Xs["va"], yz["va"], seed, bp_max, pat)
            with torch.no_grad():
                pv = bp(torch.tensor(Xs["va"], dtype=torch.float32)).numpy() * sd + mu
            v = rmse_(pv, soh[m_va])
            if best is None or v < best[0]:
                with torch.no_grad():
                    pte = bp(torch.tensor(Xs["te"], dtype=torch.float32)).numpy() * sd + mu
                    ptr = bp(torch.tensor(Xs["tr"], dtype=torch.float32)).numpy() * sd + mu
                best = (v, f"{dims}/l2={l2}", pte)
        v, cfg, pte = best
        tmae, trmse_, tr2 = reg_metrics(soh[m_te], pte)
        rows.append(dict(pipeline="TD_bpnn", seed=seed, test_battery=BATT[test_b], cfg=cfg,
                         val_rmse=round(v, 4), test_MAE=round(tmae, 4), test_RMSE=round(trmse_, 4),
                         test_R2=round(tr2, 4), nRMSE=round(trmse_ / nr, 4)))
        print(f"seed{seed} test={BATT[test_b]} done")
    for _, r in eis.iterrows():
        if r["pipeline"] not in ("P1_raw_bpnn", "P3_ae_bpnn"): continue
        if r["seed"] not in seeds or r["test_battery"] not in [BATT[b] for b in folds]: continue
        bid = [k for k, v in BATT.items() if v == r["test_battery"]][0]
        rows.append(dict(pipeline=r["pipeline"], seed=int(r["seed"]), test_battery=r["test_battery"],
                         cfg=r["cfg"], val_rmse=r["val_rmse"], test_MAE=r["test_MAE"],
                         test_RMSE=r["test_RMSE"], test_R2=r["test_R2"],
                         nRMSE=round(r["test_RMSE"] / float(soh_range.loc[bid]), 4)))
    res = pd.DataFrame(rows)
    res.to_csv(os.path.join(HERE, "steps14_16_smoke_results.csv" if smoke else "steps14_16_results.csv"), index=False)
    if not smoke:
        agg = res.groupby("pipeline")[["test_MAE", "test_RMSE", "test_R2", "nRMSE"]].agg(["mean", "std"]).round(3)
        print("\n=== per pipeline (mean +/- std) ==="); print(agg.to_string())
        agg.to_csv(os.path.join(HERE, "steps14_16_summary.csv"))
        print("\ntest_RMSE by fold:"); print(res.pivot_table(index="test_battery", columns="pipeline", values="test_RMSE").round(3).to_string())
        print("\ntest_R2 by fold:"); print(res.pivot_table(index="test_battery", columns="pipeline", values="test_R2").round(3).to_string())
    print("saved")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true"); ap.add_argument("--full", action="store_true")
    run(ap.parse_args())