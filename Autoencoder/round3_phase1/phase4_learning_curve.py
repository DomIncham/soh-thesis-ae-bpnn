# Phase 4 (advisor R3-C6): learning curve vs number of training batteries.
# Data: phase4_features.csv (14 included cells after the committed hygiene rules).
# Protocol = Phase 1 nested protocol, generalized from 4 to n cells:
#   for each (k, seed, test cell): sample k train cells from the other 13; 1 of them becomes the
#   inner-validation battery (config selection, Round 2 single-val behaviour + selection guard);
#   the selected config is refit on all k; the untouched test cell is scored.
#   Scaling and target standardization are fitted on the fitting batteries only (no leakage).
# Settings: TD-All (8 features) and Clean-8 (6 clean + ic_peak_V + t_40_41; no feature above
#   0.49 label-correlation, the supported Phase 3 set). Rows with NaN in the used features are
#   dropped per setting (the same rule Phase 3 used for ic_peak_V: 5 rows).
# Usage:
#   python phase4_learning_curve.py --smoke        # 1 fold, tiny budget, sanity only
#   python phase4_learning_curve.py                # full run (long; CPU ok, GPU via --device cuda)
import argparse, itertools, sys
import numpy as np
import pandas as pd
import r3common as rc

CSV = "phase4_features.csv"
FEATS_TDALL = rc.FEATS_ALL
FEATS_CLEAN8 = rc.FEATS_CLEAN6 + ["ic_peak_V", "t_40_41"]
SETTINGS = {"TD-All": FEATS_TDALL, "Clean-8": FEATS_CLEAN8}
KS = [3, 7, 13]
SEEDS = [42, 123, 2024, 7, 99]
BP_MAX, PAT = 300, 20


def load(feats):
    df = pd.read_csv(CSV)
    df = df[df.include_cell].copy()
    df["bid"] = df.battery.astype("category").cat.codes
    names = sorted(df.battery.unique())
    n0 = len(df)
    df = df.dropna(subset=feats).reset_index(drop=True)
    print(f"[data] {len(df)}/{n0} rows after dropna({len(feats)} feats); cells={len(names)}")
    return (df[feats].values.astype(np.float64), df.bid.values.astype(int),
            df.soh.values.astype(np.float64), df.cycle.values.astype(int), names)


def per_cell_stats(df):
    g = df.groupby("battery").capacity.agg(["max", "min"])
    qref = df.groupby("battery").capacity.apply(lambda s: s.head(5).mean())
    rng = (g["max"] - g["min"]) / qref * 100
    return qref, rng


def fold_once(X, bids, soh, cyc, test_b, train_pool, k, seed, setting, qref, rng, bp_max, pat):
    r = np.random.RandomState(seed)
    tr_sel = list(r.choice(train_pool, size=k, replace=False))
    val_b = tr_sel[0]
    fit_b = tr_sel  # refit set = all k (val battery included, as in Phase 1 refit stage)
    m_te, m_va, m_fit = bids == test_b, bids == val_b, np.isin(bids, fit_b)
    n_in = X.shape[1]
    from sklearn.preprocessing import MinMaxScaler
    # ---- selection: fit on k-1 (all but val), validate on val battery ----
    m_sel = np.isin(bids, [b for b in fit_b if b != val_b])
    sc = MinMaxScaler().fit(X[m_sel])
    assert np.allclose(sc.data_min_, X[m_sel].min(0)), "LEAKAGE: selection scaler != fold-train"
    mu, sd = soh[m_sel].mean(), soh[m_sel].std()
    cands = []
    for dims, l2 in itertools.product(rc.ARCHS, rc.L2S):
        try:
            bp, ep = rc.fit_bpnn_ep([n_in] + dims, l2, sc.transform(X[m_sel]), (soh[m_sel] - mu) / sd,
                                    sc.transform(X[m_va]), (soh[m_va] - mu) / sd, seed, bp_max, pat)
        except (TypeError, RuntimeError) as e:
            # NaN validation loss -> best_state is None (or a torch error); candidate is dead,
            # not a crash: the fold must continue (mixed-condition folds can diverge).
            print(f"  [guard] candidate {dims}/l2={l2} diverged ({type(e).__name__}); skipped")
            continue
        v = float(np.sqrt(np.mean((rc.predict(bp, sc.transform(X[m_va]), mu, sd) - soh[m_va]) ** 2)))
        cands.append((v, dims, l2, ep))
    ok = [c for c in cands if c[3] >= rc.MIN_EP and np.isfinite(c[0])]
    if not cands:  # every candidate diverged: fall back to the default config, fixed budget
        cands = [(np.inf, [8], 0.0, rc.RETRAIN_EP)]
        print("  [guard] all candidates diverged; default [8]/l2=0.0 retrain path")
    degen = len(ok) < len(cands)
    if not ok:
        _, dims, l2, _ = min(cands, key=lambda c: c[0])
        ok = [(min(c[0] for c in cands), dims, l2, rc.RETRAIN_EP)]
        print(f"  [guard] no candidate converged (min sel_epochs={min(c[3] for c in cands)}); "
              f"retrain {dims}/l2={l2} {rc.RETRAIN_EP}ep")
    v, dims, l2, ep = min(ok, key=lambda c: c[0])
    # ---- refit on all k, fixed epoch budget, then score the untouched test cell ----
    sc2 = MinMaxScaler().fit(X[m_fit])
    assert np.allclose(sc2.data_min_, X[m_fit].min(0)), "LEAKAGE: refit scaler != k-battery train"
    mu2, sd2 = soh[m_fit].mean(), soh[m_fit].std()
    bp_rf, _ = rc.fit_bpnn_ep([n_in] + dims, l2, sc2.transform(X[m_fit]), (soh[m_fit] - mu2) / sd2,
                              None, None, seed, bp_max, pat, epochs=ep)
    p = rc.predict(bp_rf, sc2.transform(X[m_te]), mu2, sd2)
    mae, rmse, r2 = rc.reg_metrics(soh[m_te], p)
    return dict(setting=setting, k=k, seed=seed, test_battery=names_all[test_b],
                train_cells=k, cfg=f"{dims}/l2={l2}", sel_epochs=ep, sel_degenerate=degen,
                test_MAE=round(float(mae), 4), test_RMSE=round(float(rmse), 4),
                test_R2=round(float(r2), 4),
                test_nRMSE=round(float(rmse) / float(rng_all[names_all[test_b]]), 4))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--device", default="cpu")
    args = ap.parse_args()
    rc.set_device(args.device)

    raw = pd.read_csv(CSV)
    raw = raw[raw.include_cell]
    qref_all, rng_all = per_cell_stats(raw)
    names_all = sorted(raw.battery.unique())
    idx = {n: i for i, n in enumerate(names_all)}

    ks = [3] if args.smoke else KS
    seeds = [42] if args.smoke else SEEDS
    settings = {"TD-All": FEATS_TDALL} if args.smoke else SETTINGS
    bp_max, pat = (60, 10) if args.smoke else (BP_MAX, PAT)

    rows = []
    for setting, feats in settings.items():
        X, bids, soh, cyc, names = load(feats)
        bidx = {n: i for i, n in enumerate(names)}
        cells = list(range(len(names)))
        n_iter = 0
        for k in ks:
            if k >= len(cells):
                print(f"[skip] k={k} >= {len(cells)} cells")
                continue
            for seed in seeds:
                for test_b in cells:
                    pool = [b for b in cells if b != test_b]
                    rows.append(fold_once(X, bids, soh, cyc, test_b, pool, k, seed,
                                          setting, qref_all, rng_all, bp_max, pat))
                    n_iter += 1
        print(f"[done] {setting}: {n_iter} fold-seed runs")
    out = pd.DataFrame(rows)
    tag = "smoke" if args.smoke else "full"
    out.to_csv(f"phase4_learning_curve_{tag}_results.csv", index=False)
    print(f"\nsaved phase4_learning_curve_{tag}_results.csv: {len(out)} rows")
    if not args.smoke:
        agg = out.groupby(["setting", "k"]).test_R2.agg(["mean", "std", "min", "max", "count"])
        print("\nLearning curve (mean R2 +/- std across fold-seeds):")
        print(agg.round(4).to_string())
        agg2 = out[out.setting == "Clean-8"].groupby("test_battery").test_R2.mean()
        print("\nClean-8 per test battery (k-averaged):")
        print(agg2.round(4).to_string())
