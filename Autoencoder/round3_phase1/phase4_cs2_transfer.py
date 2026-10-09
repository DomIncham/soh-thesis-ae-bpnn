# Phase 4 item 6.3 (R3-C6): cross-dataset transfer - NASA-trained Clean-6T tested on CALCE CS2.
# Feature set: Clean-6T (Round 4 advisor correction) = Clean-8 minus the two temperature features
# unavailable in CS2_33-38 xlsx logs. Proxy-audited set: dis_duration and dis_mean_V are EXCLUDED
# (both are proxy / proxy-equivalent per the R3-C3 audit) and MUST NOT re-enter this list.
FEATS = ["dis_V_slope", "cc_dur", "cv_dur", "cv_I_slope", "t_40_41", "ic_peak_V"]
# Freeze protocol: for each seed, select the config on the NASA pool (1 val battery + fit batteries,
# same nested machinery as Phase 1/4), refit on all fit batteries, then score every CS2 cell with
# that frozen model. Two NASA training pools are reported:
#   pool=room : the 4 room-2A cells (B0005/6/7/18) - the homogeneous pool Phase 4 recommends
#   pool=all13: the 13-cell heterogeneous NASA pool - the pooled-claim variant
# CS2 side: only cap_ok rows (>= 0.8 x cell-max capacity) are scored; metrics per cell + pooled.
# Usage:
#   python phase4_cs2_transfer.py --smoke      # 1 seed, tiny budget
#   python phase4_cs2_transfer.py              # 5 seeds, full budget (CPU ok, ~30 min)
import argparse, itertools, os
import numpy as np
import pandas as pd
import r3common as rc
from sklearn.preprocessing import MinMaxScaler

ROOM = ["B0005", "B0006", "B0007", "B0018"]
SEEDS = [42, 123, 2024, 7, 99]


def nasa_pool(pool):
    df = pd.read_csv("phase4_features.csv")
    df = df[df.include_cell]
    if pool == "room":
        df = df[df.battery.isin(ROOM)]
    df = df.dropna(subset=FEATS).reset_index(drop=True)
    df["bid"] = df.battery.astype("category").cat.codes
    return df


def cs2_pool():
    df = pd.read_csv("phase4_cs2_features.csv")
    df = df[df.include_cell & df.cap_ok].dropna(subset=FEATS).reset_index(drop=True)
    return df


def select_and_fit(Xfit, yfit, Xval, yval, seed, bp_max, pat):
    mu, sd = yfit.mean(), yfit.std()
    cands = []
    for dims, l2 in itertools.product(rc.ARCHS, rc.L2S):
        try:
            bp, ep = rc.fit_bpnn_ep([Xfit.shape[1]] + dims, l2, Xfit, (yfit - mu) / sd,
                                    Xval, (yval - mu) / sd, seed, bp_max, pat)
        except (TypeError, RuntimeError):
            continue
        v = float(np.sqrt(np.mean((rc.predict(bp, Xval, mu, sd) - yval) ** 2)))
        cands.append((v, dims, l2, ep))
    ok = [c for c in cands if c[3] >= rc.MIN_EP and np.isfinite(c[0])]
    if not cands:
        cands = [(np.inf, [8], 0.0, rc.RETRAIN_EP)]
    if not ok:
        _, dims, l2, _ = min(cands, key=lambda c: c[0])
        dims, l2, ep = dims, l2, rc.RETRAIN_EP
        try:
            bp_rf, _ = rc.fit_bpnn_ep([Xfit.shape[1]] + dims, l2, Xfit, (yfit - mu) / sd,
                                      None, None, seed, bp_max, pat, epochs=ep)
        except (TypeError, RuntimeError):
            print(f"  [guard] retrain diverged for seed {seed}; default linear-scale fallback")
            return None, mu, sd, dims, l2, ep, True
    else:
        _, dims, l2, ep = min(ok, key=lambda c: c[0])
        try:
            bp_rf, _ = rc.fit_bpnn_ep([Xfit.shape[1]] + dims, l2, Xfit, (yfit - mu) / sd,
                                      None, None, seed, bp_max, pat, epochs=ep)
        except (TypeError, RuntimeError):
            print(f"  [guard] refit diverged for seed {seed}; default linear-scale fallback")
            return None, mu, sd, dims, l2, ep, True
    return bp_rf, mu, sd, dims, l2, ep, False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--device", default="cpu")
    args = ap.parse_args()
    rc.set_device(args.device)
    seeds = [42] if args.smoke else SEEDS
    bp_max, pat = (60, 10) if args.smoke else (300, 20)

    cs2 = cs2_pool()
    tag = "smoke" if args.smoke else "full"
    Xc, yc, cells_c = cs2[FEATS].values, cs2.soh.values, cs2.battery.values
    print(f"CS2 test pool: {len(cs2)} full cycles across {cs2.battery.nunique()} cells")

    rows = []
    out_name = f"phase4_cs2_transfer_{tag}.csv"
    if os.path.exists(out_name):
        rows = pd.read_csv(out_name).to_dict("records")
        done = {(r["pool"], r["seed"]) for r in rows}
        print(f"[resume] {len(rows)} rows already in {out_name}; skipping those (pool, seed) pairs")
    else:
        done = set()
    for pool in ["room", "all13"]:
        nd = nasa_pool(pool)
        Xn, yn, bn = nd[FEATS].values, nd.soh.values, nd.bid.values
        uniq = np.unique(bn)
        for seed in seeds:
            if (pool, seed) in done:
                continue
            r = np.random.RandomState(seed)
            val_b = int(r.choice(uniq))
            val_name = nd.battery[bn == val_b].iloc[0]  # name of the val battery
            # Round 4 advisor correction (item 3): during model selection the training set must
            # exclude the validation battery; the refit then uses the WHOLE pool (incl. val_b).
            m_val = bn == val_b
            m_fit = np.ones_like(bn, dtype=bool)
            m_sel = ~m_val  # selection fitting set = pool minus the validation battery
            sc = MinMaxScaler().fit(Xn[m_sel])
            bp, mu, sd, dims, l2, ep, degraded = select_and_fit(
                sc.transform(Xn[m_sel]), yn[m_sel], sc.transform(Xn[m_val]), yn[m_val],
                seed, bp_max, pat)
            # Advisor sequence (item 3): after selection, REFIT on the WHOLE pool (val battery
            # folded back in) with its own scaler/target stats, then test on CS2 — the same
            # pattern as within.py and r3common.run_fold. mu/sd of the refit scale are reused.
            if bp is not None:
                sc2 = MinMaxScaler().fit(Xn[m_fit])
                mu2, sd2 = yn[m_fit].mean(), yn[m_fit].std()
                try:
                    bp_rf, _ = rc.fit_bpnn_ep([Xn.shape[1]] + dims, l2, sc2.transform(Xn[m_fit]),
                                              (yn[m_fit] - mu2) / sd2, None, None, seed,
                                              bp_max, pat, epochs=ep)
                    bp, mu, sd, sc = bp_rf, mu2, sd2, sc2
                except (TypeError, RuntimeError):
                    print(f"  [guard] pool refit diverged (pool={pool}, seed={seed}); "
                          f"keeping the selection-scale model")
            for cell in sorted(set(cells_c)):
                m_c = cells_c == cell
                if bp is None:  # diverged even on the fallback config: record honestly, keep going
                    rows.append(dict(pool=pool, seed=seed, test_battery=cell,
                                     val_battery=val_name,
                                     n_cycles=int(m_c.sum()), cfg=f"{dims}/l2={l2}",
                                     sel_epochs=ep, MAE=np.nan, RMSE=np.nan, R2=np.nan))
                    continue
                p = rc.predict(bp, sc.transform(Xc[m_c]), mu, sd)
                mae, rmse, r2 = rc.reg_metrics(yc[m_c], p)
                rows.append(dict(pool=pool, seed=seed, test_battery=cell, val_battery=val_name,
                                 n_cycles=int(m_c.sum()),
                                 cfg=f"{dims}/l2={l2}", sel_epochs=ep,
                                 MAE=round(float(mae), 3), RMSE=round(float(rmse), 3),
                                 R2=round(float(r2), 3)))
            print(f"[{pool} seed {seed}] cfg {dims}/l2={l2} sel_ep {ep} "
                  f"{'DEGRADED (fallback)' if degraded else 'ok'}")
            pd.DataFrame(rows).to_csv(out_name, index=False)  # checkpoint after every seed
    out = pd.DataFrame(rows)
    out.to_csv(out_name, index=False)
    print(f"\nsaved {out_name}: {len(out)} rows")
    if not args.smoke:
        print("\nMean R2 / RMSE per (pool, CS2 cell):")
        print(out.groupby(["pool", "test_battery"]).agg(R2=("R2", "mean"), RMSE=("RMSE", "mean"),
                                                        n=("R2", "size")).round(3).to_string())
        print("\nPooled per pool:")
        print(out.groupby("pool").agg(R2_mean=("R2", "mean"), R2_median=("R2", "median"),
                                      RMSE_mean=("RMSE", "mean")).round(3).to_string())


if __name__ == "__main__":
    main()
