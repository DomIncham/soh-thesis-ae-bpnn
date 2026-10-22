# Round 6, P6-5 (R6-C2.5): alignment ladder — increasing levels of target information.
# L0 = P6-2 transfer rerun (already done, parity-exact vs Round 5).
# La = source-only scaling alternatives (Robust / Standard / Quantile), selected by the SAME
#      rotated source-battery rule; no target information at all.
# Lb = unsupervised target-domain feature alignment: per-feature affine match
#      (median + IQR rescale) and PCA-whiten/reconstruct variant — fitted on target TRAINING
#      cells' FEATURES only; the held-out test cell is excluded by assertion.
# Lc = one-cell output calibration: affine correction (slope/intercept) fitted on ONE target
#      cell's predictions vs labels (same LOCO split as adapt2), applied to the other 7 cells.
#      Precedes any NN fine-tuning (advisor's wording).
# Backbone = the SAME phase5 transfer protocol/selection/seeds; only the data transform or
# output correction changes per rung. No AE, no feature changes (R6-C5).
# Every rung CSV carries sel_degenerate (R6-C4) + variant label; per-cycle dumps are written.
#
# Usage: python phase6_alignment_ladder.py --smoke                 # 1 seed, tiny budget
#        python phase6_alignment_ladder.py                         # full (CPU, est ~1-2 h)
#        python phase6_alignment_ladder.py --rungs La,Lc           # subset
import argparse, os
import numpy as np
import pandas as pd
import torch
import r3common as rc
from sklearn.preprocessing import MinMaxScaler, RobustScaler, StandardScaler, QuantileTransformer

FEATS = ["dis_V_slope", "cc_dur", "cv_dur", "cv_I_slope", "ic_peak_V"]
ROOM = ["B0005", "B0006", "B0007", "B0018"]
SEEDS = [42, 123, 2024, 7, 99]
ADAPT2_EP = 30
assert "dis_duration" not in FEATS and "dis_mean_V" not in FEATS, "S4 proxy-ban violated"


def prog(msg):
    import time
    print(msg, flush=True)


def make_scaler(variant):
    return {"robust": RobustScaler, "standard": StandardScaler,
            "quantile": lambda: QuantileTransformer(n_quantiles=min(100, 4 * 4 * 4), output_distribution="uniform")}[variant]


def pools():
    nasa = pd.read_csv("phase4_features.csv")
    nasa = nasa[nasa.include_cell].dropna(subset=FEATS).reset_index(drop=True)
    nasa["bid"] = nasa.battery.astype("category").cat.codes
    cs2 = pd.read_csv("phase4_cs2_features.csv")
    cs2 = cs2[cs2.include_cell & cs2.cap_ok].dropna(subset=FEATS).reset_index(drop=True)
    cs2["bid"] = cs2.battery.astype("category").cat.codes
    return nasa, cs2


def select_config(seed, Xn_, yn_, bn_, bp_max, pat):
    """Identical rotated selection to phase5.transfer (single val battery rotation,
    mean RMSE aggregate, MIN_EP guard, RETRAIN_EP fallback). Returns (dims, l2, ep, deg)."""
    import itertools
    uniq = np.unique(bn_)
    cands = []
    for dims, l2 in itertools.product(rc.ARCHS, rc.L2S):
        vs, eps = [], []
        for v in uniq:
            res = _select_ep(dims, l2, Xn_[bn_ != v], yn_[bn_ != v],
                             Xn_[bn_ == v], yn_[bn_ == v], seed, bp_max, pat)
            if res is None:
                continue
            vs.append(res[0]); eps.append(res[1])
        if vs:
            cands.append((float(np.mean(vs)), dims, l2, int(round(np.mean(eps))), min(eps)))
    ok = [c for c in cands if c[4] >= rc.MIN_EP and np.isfinite(c[0])]
    deg = len(ok) < len(cands)
    if not ok:
        _, dims, l2, _, _ = min(cands, key=lambda c: c[0]) if cands else (0, [8], 0.0, 0, 0)
        ep = rc.RETRAIN_EP
    else:
        _, dims, l2, ep, _ = min(ok, key=lambda c: c[0])
    return dims, l2, ep, deg


def _select_ep(dims, l2, Xf, yf, Xv, yv, seed, bp_max, pat):
    from phase5_cs2_clean5t import select_ep  # reuse EXACT phase5 machinery for parity
    return select_ep(dims, l2, Xf, yf, Xv, yv, seed, bp_max, pat)


def fit_backbone(X_fit, y_fit, dims, l2, ep, seed, bp_max, pat):
    bp, _ = rc.fit_bpnn_ep([X_fit.shape[1]] + dims, l2, X_fit, (y_fit - y_fit.mean()) / y_fit.std(),
                           None, None, seed, bp_max, pat, epochs=ep)
    return bp


def predict_scaled(bp, X, mu, sd):
    return rc.predict(bp, X, mu, sd)


def _dump(path, seed, rung, variant, pool, cell, y, yhat):
    pd.DataFrame(dict(seed=seed, rung=rung, variant=variant, pool=pool, cell=cell,
                      cycle=np.arange(1, len(y) + 1),
                      y=np.round(np.asarray(y, float), 4),
                      yhat=np.round(np.asarray(yhat, float), 4))
                 ).to_csv(path, mode="a", header=not os.path.exists(path), index=False)


def reg(y, p):
    err = p - y
    return (np.abs(err).mean(), np.sqrt((err ** 2).mean()),
            1 - (err ** 2).sum() / ((y - y.mean()) ** 2).sum())


def run_La(nasa, cs2, seeds, bp_max, pat, dump):
    """Source-only scaling alternatives: swap the source scaler; selection over the SOURCE
    batteries as in phase5; zero target information."""
    Xc, yc, bc = cs2[FEATS].values, cs2.soh.values, cs2.bid.values
    cells = sorted(set(cs2.battery))
    rows = []
    out = "phase6_ladder_La.csv"
    for pool in ["room", "all13"]:
        nd = nasa[nasa.battery.isin(ROOM)] if pool == "room" else nasa
        nd = nd.reset_index(drop=True)
        Xn_, yn_, bn_ = nd[FEATS].values, nd.soh.values, nd.bid.values
        for seed in seeds:
            dims, l2, ep, deg = select_config(seed, Xn_, yn_, bn_, bp_max, pat)
            for variant in ["robust", "standard", "quantile"]:
                Sc = make_scaler(variant)()
                Xtr = Sc.fit_transform(Xn_)
                mu, sd = yn_.mean(), yn_.std()
                try:
                    bp = fit_backbone(Xtr, yn_, dims, l2, ep, seed, bp_max, pat)
                    for c_ in cells:
                        m_c = cs2.battery.values == c_
                        p = predict_scaled(bp, Sc.transform(Xc[m_c]), mu, sd)
                        _dump(dump, seed, "La", variant, pool, c_, yc[m_c], p)
                        mae, rmse, r2 = reg(yc[m_c], p)
                        rows.append(dict(rung="La", variant=variant, pool=pool, seed=seed,
                                         test_battery=c_, n_cycles=int(m_c.sum()),
                                         cfg=f"{dims}/l2={l2}", sel_epochs=ep,
                                         sel_degenerate=deg,
                                         MAE=round(float(mae), 3), RMSE=round(float(rmse), 3),
                                         R2=round(float(r2), 3)))
                except (TypeError, RuntimeError):
                    print(f"  [guard] La {pool} s{seed} {variant} diverged — row skipped", flush=True)
            prog(f"[La {pool} s{seed}] scalers done (DEG={deg})")
            pd.DataFrame(rows).to_csv(out, index=False)
    return out, rows


def run_Lb(nasa, cs2, seeds, bp_max, pat, dump, adapt_split):
    """Unsupervised target-feature alignment. Uses adapt_split: {cell -> (fit_mask, test_mask)}
    mirroring the adapt arms — target TRAINING cells = the 7 cells != adapt cell.
    The held-out test cell never contributes to any fit (asserted)."""
    Xc, yc, bc = cs2[FEATS].values, cs2.soh.values, cs2.bid.values
    rows = []
    out = "phase6_ladder_Lb.csv"
    for pool in ["room", "all13"]:
        nd = nasa[nasa.battery.isin(ROOM)] if pool == "room" else nasa
        nd = nd.reset_index(drop=True)
        Xn_, yn_, bn_ = nd[FEATS].values, nd.soh.values, nd.bid.values
        for seed in seeds:
            dims, l2, ep, deg = select_config(seed, Xn_, yn_, bn_, bp_max, pat)
            sc_src = MinMaxScaler().fit(Xn_)
            mu_src, sd_src = yn_.mean(), yn_.std()
            bp = fit_backbone(sc_src.transform(Xn_), yn_, dims, l2, ep, seed, bp_max, pat)
            for adapt_cell in adapt_split:
                fit_mask, te_mask = adapt_split[adapt_cell]
                assert not te_mask.any() == False  # sanity shape
                assert not (fit_mask & te_mask).any()
                train_X = Xc[fit_mask]
                for variant in ["affine", "pca_reconstruct"]:
                    if variant == "affine":
                        # per-feature affine: move target median/IQR to source median/IQR
                        Xtr = train_X.copy()
                        Xte = Xc[te_mask].copy()
                        params = []
                        for j in range(train_X.shape[1]):
                            q75, q50 = np.percentile(train_X[:, j], [75, 50])
                            iqr_t = max(q75 - q50, 1e-12)
                            s75, s50 = np.percentile(Xn_[:, j], [75, 50])
                            iqr_s = max(s75 - s50, 1e-12)
                            a = iqr_s / iqr_t
                            b = s50 - a * q50
                            Xtr[:, j] = a * train_X[:, j] + b
                            Xte[:, j] = a * Xc[te_mask][:, j] + b
                            params.append((a, b))
                        # clamp to source min-max AFTER affine (mild guard against overshoot)
                        for j in range(Xtr.shape[1]):
                            lo, hi = Xn_[:, j].min(), Xn_[:, j].max()
                            Xtr[:, j] = np.clip(Xtr[:, j], lo, hi)
                            Xte[:, j] = np.clip(Xte[:, j], lo, hi)
                        Xte_aligned = Xte
                    else:  # pca_reconstruct: project target train features onto source PCA, rebuild
                        from sklearn.decomposition import PCA
                        Zs = sc_src.transform(Xn_)
                        k = min(5, Zs.shape[1])
                        pca = PCA(n_components=k, svd_solver="full").fit(Zs)
                        Ztr = pca.inverse_transform(pca.transform(sc_src.transform(train_X)))
                        Zte = pca.inverse_transform(pca.transform(sc_src.transform(Xc[te_mask])))
                        Xte_aligned = Zte  # already in source-normalised space
                        Xtr = Ztr
                    mu_al = yn_.mean(); sd_al = yn_.std()
                    # refit backbone on aligned TARGET-FEATURE space mapped through the SOURCE
                    # model? No — alignment is unsupervised: we CORRECT the target inputs, then
                    # evaluate the SAME source-trained model on the aligned test features.
                    if variant == "affine":
                        p = predict_scaled(bp, sc_src.transform(Xte_aligned), mu_src, sd_src)
                    else:
                        p = rc.predict(bp, Xte_aligned, mu_src, sd_src)
                    _dump(dump, seed, "Lb", variant, pool, adapt_cell, yc[te_mask], p)
                    mae, rmse, r2 = reg(yc[te_mask], p)
                    rows.append(dict(rung="Lb", variant=variant, pool=pool, seed=seed,
                                     adapt_cell=adapt_cell, n_cycles=int(te_mask.sum()),
                                     cfg=f"{dims}/l2={l2}", sel_epochs=ep, sel_degenerate=deg,
                                     MAE=round(float(mae), 3), RMSE=round(float(rmse), 3),
                                     R2=round(float(r2), 3)))
            prog(f"[Lb {pool} s{seed}] variants done (DEG={deg})")
            pd.DataFrame(rows).to_csv(out, index=False)
    return out, rows


def run_Lc(nasa, cs2, seeds, bp_max, pat, dump, warm):
    """One-cell output calibration: adapt2 backbone (warm-start on 1 cell, exactly like
    phase5.adapt2), then an affine output correction yhat->y fitted on that ONE cell,
    applied to the remaining 7. No NN fine-tuning beyond adapt2's warm-start."""
    Xc, yc, bc = cs2[FEATS].values, cs2.soh.values, cs2.bid.values
    cells = sorted(set(cs2.battery))
    rows = []
    out = "phase6_ladder_Lc.csv"
    from phase5_cs2_clean5t import warm_fit
    for pool in ["room", "all13"]:
        nd = nasa[nasa.battery.isin(ROOM)] if pool == "room" else nasa
        nd = nd.reset_index(drop=True)
        Xn_, yn_, bn_ = nd[FEATS].values, nd.soh.values, nd.bid.values
        for seed in seeds:
            dims, l2, ep, deg = select_config(seed, Xn_, yn_, bn_, bp_max, pat)
            sc2 = MinMaxScaler().fit(Xn_)
            mu2, sd2 = yn_.mean(), yn_.std()
            try:
                bp_rf, _ = rc.fit_bpnn_ep([Xn_.shape[1]] + dims, l2, sc2.transform(Xn_),
                                          (yn_ - mu2) / sd2, None, None, seed, bp_max, pat,
                                          epochs=ep)
            except (TypeError, RuntimeError):
                print(f"  [guard] Lc {pool} s{seed} pool refit diverged", flush=True)
                continue
            for adapt_cell in cells:
                m_a = cs2.battery.values == adapt_cell
                m_te = ~m_a
                try:
                    bp_ft = warm_fit(bp_rf, dims, l2, sc2.transform(Xc[m_a]), yc[m_a],
                                     mu2, sd2, seed, ADAPT2_EP)
                    p_ad = rc.predict(bp_ft, sc2.transform(Xc[m_a]), mu2, sd2)
                except (TypeError, RuntimeError):
                    print(f"  [guard] Lc {pool} s{seed} warm diverged", flush=True)
                    continue
                # affine output calibration on the ONE adapt cell (least squares slope/intercept)
                A = np.vstack([p_ad, np.ones_like(p_ad)]).T
                slope, intercept = np.linalg.lstsq(A, yc[m_a], rcond=None)[0]
                p_te_raw = rc.predict(bp_ft, sc2.transform(Xc[m_te]), mu2, sd2)
                p_te = slope * p_te_raw + intercept
                _dump(dump, seed, "Lc", f"a={slope:.3f}+b={intercept:.3f}", pool, None,
                      yc[m_te], p_te)
                mae, rmse, r2 = reg(yc[m_te], p_te)
                rows.append(dict(rung="Lc", variant=f"slope={slope:.3f}", pool=pool, seed=seed,
                                 adapt_cell=adapt_cell, n_cycles=int(m_te.sum()),
                                 cfg=f"{dims}/l2={l2}", sel_epochs=ep, sel_degenerate=deg,
                                 MAE=round(float(mae), 3), RMSE=round(float(rmse), 3),
                                 R2=round(float(r2), 3)))
            prog(f"[Lc {pool} s{seed}] calibration done (DEG={deg})")
            pd.DataFrame(rows).to_csv(out, index=False)
    return out, rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--rungs", default="La,Lb,Lc")
    ap.add_argument("--dump-preds", default="phase6_ladder_preds.csv")
    args = ap.parse_args()
    rc.set_device(args.device)
    seeds = [42] if args.smoke else SEEDS
    bp_max, pat = (60, 10) if args.smoke else (300, 20)
    if os.path.exists(args.dump_preds):
        os.remove(args.dump_preds)
    nasa, cs2 = pools()
    Xc, yc = cs2[FEATS].values, cs2.soh.values
    cells = sorted(set(cs2.battery))
    # adapt split mirrors phase5 adapt arms: fit on 1 cell, test the other 7 — but for Lb the
    # "target training cells" are the 7 (features only); the adapt cell is the held-out test.
    adapt_split = {c: (cs2.battery.values != c, cs2.battery.values == c) for c in cells}
    rungs = [r.strip() for r in args.rungs.split(",")]
    all_rows = []
    if "La" in rungs:
        out, rows = run_La(nasa, cs2, seeds, bp_max, pat, args.dump_preds)
        all_rows += rows
    if "Lb" in rungs:
        out, rows = run_Lb(nasa, cs2, seeds, bp_max, pat, args.dump_preds, adapt_split)
        all_rows += rows
    if "Lc" in rungs:
        out, rows = run_Lc(nasa, cs2, seeds, bp_max, pat, args.dump_preds, warm=False)
        all_rows += rows
    df = pd.DataFrame(all_rows)
    df.to_csv("phase6_alignment_summary_rows.csv", index=False)
    print("\n== ladder summary (median across seeds) ==")
    if len(df):
        print(df.groupby(["rung", "variant"])[["MAE", "R2"]].median().round(3).to_string())
    print("\nfallback recorded per row (R6-C4). L0 reference = P6-2 rerun "
          "(median MAE 20.99 / MedAE 19.5).")


if __name__ == "__main__":
    main()
