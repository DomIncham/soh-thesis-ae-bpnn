# Steps 9-10: 5-baseline comparison under the approved nested-LOBO protocol (Part F + F2 + G2)
# Pipelines: B1 Mean predictor | B2 Ridge (alpha by inner val) | P1 Raw EIS -> BPNN |
#            P1n Raw -> per-row min-max -> BPNN (B0006 scaler hypothesis, deployable) |
#            P2 PCA(fit train-only, n by inner val) -> BPNN | P3 AE -> BPNN (reused from Steps 7-8 CSV)
# Same splits, EarlyStopping, %SOH metrics, seeds as nested_lobo_harness. nRMSE = RMSE / test-SOH range (D3).
import argparse, itertools, os
import numpy as np, pandas as pd, torch
from sklearn.preprocessing import MinMaxScaler
from sklearn.decomposition import PCA
from sklearn.linear_model import Ridge

from nested_lobo_harness import ControlledAutoencoder, BPNN, train_model, fit_bpnn, reg_metrics

HERE = os.path.dirname(os.path.abspath(__file__))
BATT = {1: "B0005", 2: "B0006", 3: "B0007", 4: "B0018"}
ARCHS, L2S = [[8], [16], [8, 4]], [0.0, 1e-4]
ALPHAS, PCS = [0.1, 1.0, 10.0], [8, 17, 32]

def rmse(a, b): return float(np.sqrt(np.mean((np.asarray(a) - np.asarray(b)) ** 2)))

def eval_bpnn(bp, Ztr, Zte, sd, mu, soh_tr, soh_te):
    with torch.no_grad():
        ptr = bp(torch.tensor(Ztr, dtype=torch.float32)).numpy() * sd + mu
        pte = bp(torch.tensor(Zte, dtype=torch.float32)).numpy() * sd + mu
    return reg_metrics(soh_tr, ptr), reg_metrics(soh_te, pte)

def run(args):
    smoke = args.smoke
    seeds = [42] if smoke else [42, 7, 123]
    folds = [1] if smoke else [1, 2, 3, 4]
    bp_max, pat = 100 if smoke else 500, 10 if smoke else 30
    d = torch.load(os.path.join(HERE, "Mapped_EIS_SOH_tol1.pt"), weights_only=True)
    X, y_all = d["features"].numpy(), d["labels"].numpy()
    bids = y_all[:, 0].astype(int); soh = y_all[:, 3]

    # P3 reuse: tolerance-1 rows from the Steps 7-8 full run
    p3 = pd.read_csv(os.path.join(HERE, "nested_lobo_results.csv"))
    p3 = p3[p3.tolerance.astype(str) == "1"]
    rows = []
    for seed, test_b in itertools.product(seeds, folds):
        remaining = [b for b in [1, 2, 3, 4] if b != test_b]
        val_b, train_b = remaining[0], remaining[1:]
        m_tr, m_va, m_te = np.isin(bids, train_b), (bids == val_b), (bids == test_b)
        scaler = MinMaxScaler().fit(X[m_tr])
        assert np.allclose(scaler.data_min_, X[m_tr].min(0)), "LEAKAGE: scaler != fold-train stats"
        Xs = {k: scaler.transform(X[m]) for k, m in [("tr", m_tr), ("va", m_va), ("te", m_te)]}
        mu, sd = soh[m_tr].mean(), soh[m_tr].std()
        yz = {k: ((soh[m] - mu) / sd).astype(np.float32) for k, m in [("tr", m_tr), ("va", m_va), ("te", m_te)]}
        te_range = float(soh[m_te].max() - soh[m_te].min())

        # B1 Mean predictor
        pred = float(soh[m_tr].mean())
        vmae, vrmse, vr2 = reg_metrics(soh[m_va], np.full(m_va.sum(), pred))
        tmae, trmse_, tr2 = reg_metrics(soh[m_te], np.full(m_te.sum(), pred))
        rows.append(dict(pipeline="B1_mean", seed=seed, test_battery=BATT[test_b], cfg="mean(train)",
                         val_rmse=round(vrmse, 4), test_MAE=round(tmae, 4), test_RMSE=round(trmse_, 4),
                         test_R2=round(tr2, 4), nRMSE=round(trmse_ / te_range, 4)))

        # B2 Ridge on MinMax-scaled features
        best = None
        for a in ALPHAS:
            r = Ridge(alpha=a).fit(Xs["tr"], soh[m_tr])
            v = rmse(r.predict(Xs["va"]), soh[m_va])
            if best is None or v < best[0]:
                best = (v, a, r.predict(Xs["te"]), r.predict(Xs["tr"]))
        v, a, pte, ptr = best
        tmae, trmse_, tr2 = reg_metrics(soh[m_te], pte)
        rows.append(dict(pipeline="B2_ridge", seed=seed, test_battery=BATT[test_b], cfg=f"alpha={a}",
                         val_rmse=round(v, 4), test_MAE=round(tmae, 4), test_RMSE=round(trmse_, 4),
                         test_R2=round(tr2, 4), nRMSE=round(trmse_ / te_range, 4)))

        # P1 Raw EIS -> BPNN (256-dim MinMax-scaled) | P1n per-row min-max (deployable, no train fit)
        Xn = (X - X.min(1, keepdims=True)) / np.maximum(X.max(1, keepdims=True) - X.min(1, keepdims=True), 1e-12)
        Xn = {k: Xn[m] for k, m in [("tr", m_tr), ("va", m_va), ("te", m_te)]}
        for pipeline, feats in [("P1_raw_bpnn", Xs), ("P1n_rowminmax_bpnn", Xn)]:
            n_in = feats["tr"].shape[1]
            best = None
            for dims, l2 in itertools.product(ARCHS, L2S):
                bp = fit_bpnn([n_in] + dims, l2, feats["tr"], yz["tr"], feats["va"], yz["va"], seed, bp_max, pat)
                with torch.no_grad():
                    pv = bp(torch.tensor(feats["va"], dtype=torch.float32)).numpy() * sd + mu
                v = rmse(pv, soh[m_va])
                if best is None or v < best[0]:
                    with torch.no_grad():
                        pte = bp(torch.tensor(feats["te"], dtype=torch.float32)).numpy() * sd + mu
                        ptr = bp(torch.tensor(feats["tr"], dtype=torch.float32)).numpy() * sd + mu
                    best = (v, f"{dims}/l2={l2}", ptr, pte)
            v, cfg, ptr, pte = best
            tmae, trmse_, tr2 = reg_metrics(soh[m_te], pte)
            rows.append(dict(pipeline=pipeline, seed=seed, test_battery=BATT[test_b], cfg=cfg,
                             val_rmse=round(v, 4), test_MAE=round(tmae, 4), test_RMSE=round(trmse_, 4),
                             test_R2=round(tr2, 4), nRMSE=round(trmse_ / te_range, 4)))

        # P2 PCA (fit on fold-train scaled features only) -> BPNN [16]
        best = None
        for n in PCS:
            pca = PCA(n_components=n).fit(Xs["tr"])
            Z = {k: pca.transform(Xs[k]) for k in Xs}
            for l2 in L2S:
                bp = fit_bpnn([n, 16], l2, Z["tr"], yz["tr"], Z["va"], yz["va"], seed, bp_max, pat)
                with torch.no_grad():
                    pv = bp(torch.tensor(Z["va"], dtype=torch.float32)).numpy() * sd + mu
                v = rmse(pv, soh[m_va])
                if best is None or v < best[0]:
                    with torch.no_grad():
                        pte = bp(torch.tensor(Z["te"], dtype=torch.float32)).numpy() * sd + mu
                        ptr = bp(torch.tensor(Z["tr"], dtype=torch.float32)).numpy() * sd + mu
                    best = (v, f"pca{n}/l2={l2}", ptr, pte)
        v, cfg, ptr, pte = best
        tmae, trmse_, tr2 = reg_metrics(soh[m_te], pte)
        rows.append(dict(pipeline="P2_pca_bpnn", seed=seed, test_battery=BATT[test_b], cfg=cfg,
                         val_rmse=round(v, 4), test_MAE=round(tmae, 4), test_RMSE=round(trmse_, 4),
                         test_R2=round(tr2, 4), nRMSE=round(trmse_ / te_range, 4)))
        print(f"seed{seed} test={BATT[test_b]} done")

    # P3 reuse: tolerance-1 rows from Steps 7-8 full run (restrict to current folds/seeds)
    for _, r in p3.iterrows():
        if r["seed"] not in seeds or r["test_battery"] not in [BATT[b] for b in folds]:
            continue
        bid = [k for k, v in BATT.items() if v == r["test_battery"]][0]
        m_te = bids == bid
        te_range = float(soh[m_te].max() - soh[m_te].min())
        rows.append(dict(pipeline="P3_ae_bpnn", seed=int(r["seed"]), test_battery=r["test_battery"],
                         cfg=f"{r['bpnn_arch']}/l2={r['bpnn_l2']}", val_rmse=r["val_rmse_soh"],
                         test_MAE=r["test_MAE"], test_RMSE=r["test_RMSE"], test_R2=r["test_R2"],
                         nRMSE=round(r["test_RMSE"] / te_range, 4)))
    res = pd.DataFrame(rows)
    res.to_csv(os.path.join(HERE, "steps9_10_smoke_results.csv" if smoke else "steps9_10_results.csv"), index=False)
    if not smoke:
        agg = res.groupby("pipeline")[["test_MAE", "test_RMSE", "test_R2", "nRMSE"]].agg(["mean", "std"]).round(4)
        print("\n=== per pipeline (mean +/- std, 12 runs each) ===")
        print(agg.to_string())
        agg.to_csv(os.path.join(HERE, "steps9_10_summary.csv"))
        piv = res.pivot_table(index="test_battery", columns="pipeline", values="test_RMSE").round(3)
        print("\ntest_RMSE by fold:"); print(piv.to_string())
    print("saved results")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true"); ap.add_argument("--full", action="store_true")
    ap.add_argument("--probe", action="store_true")
    run(ap.parse_args())