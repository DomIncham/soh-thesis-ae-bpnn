# Phase 4 item 6.3 (R3-C6): cross-dataset transfer WITH minimal adaptation (4.5c).
# Question the frozen run left open: how much target-domain data does transfer need?
# Protocol: leave-one-cell-out on the target domain. For each CS2 test cell: start from the NASA
# room-pool frozen model (the pool Phase 4 recommends), fine-tune on ONE different CS2 cell
# (the same config, low LR not needed - we refit with a small epoch budget on 1 cell), then score
# the test cell. k_adapt = 1 full cycle-history is the cheapest possible calibration.
# The frozen (no-adaptation) numbers are in phase4_cs2_transfer_full.csv for comparison.
# Usage:
#   python phase4_cs2_adapt1.py --smoke     # 1 seed, tiny budget
#   python phase4_cs2_adapt1.py             # 5 seeds, full budget (~10-15 min)
import argparse, itertools, os
import numpy as np
import pandas as pd
import r3common as rc
from sklearn.preprocessing import MinMaxScaler

FEATS = ["dis_duration", "dis_mean_V", "dis_V_slope", "cc_dur", "cv_dur", "cv_I_slope",
         "t_40_41", "ic_peak_V"]
ROOM = ["B0005", "B0006", "B0007", "B0018"]
SEEDS = [42, 123, 2024, 7, 99]


def load(feat, path="phase4_features.csv", only=None):
    df = pd.read_csv(path)
    df = df[df.include_cell]
    if only is not None:
        df = df[df.battery.isin(only)]
    df = df.dropna(subset=feat).reset_index(drop=True)
    df["bid"] = df.battery.astype("category").cat.codes
    return df


def fit_pool(Xfit, yfit, Xval, yval, seed, bp_max, pat):
    """Select a config on NASA (val battery) and refit on the whole NASA pool - the frozen start."""
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
        ep = rc.RETRAIN_EP
    else:
        _, dims, l2, ep = min(ok, key=lambda c: c[0])
    bp_rf, _ = rc.fit_bpnn_ep([Xfit.shape[1]] + dims, l2, Xfit, (yfit - mu) / sd,
                              None, None, seed, bp_max, pat, epochs=ep)
    return bp_rf, mu, sd, dims, l2, ep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--device", default="cpu")
    args = ap.parse_args()
    rc.set_device(args.device)
    seeds = [42] if args.smoke else SEEDS
    bp_max, pat = (60, 10) if args.smoke else (300, 20)
    ADAPT_EP = 40 if not args.smoke else 20  # small fine-tune budget on 1 target cell
    tag = "smoke" if args.smoke else "full"
    out_name = f"phase4_cs2_adapt1_{tag}.csv"

    cs2 = cs2df = pd.read_csv("phase4_cs2_features.csv")
    cs2 = cs2[cs2.include_cell & cs2.cap_ok].dropna(subset=FEATS).reset_index(drop=True)
    Xc, yc, cells_c = cs2[FEATS].values, cs2.soh.values, cs2.battery.values
    cells = sorted(set(cells_c))
    print(f"CS2 pool: {len(cs2)} full cycles, {len(cells)} cells")

    nd = load(FEATS, only=ROOM)
    Xn, yn, bn = nd[FEATS].values, nd.soh.values, nd.bid.values
    uniq = np.unique(bn)

    rows = []
    if os.path.exists(out_name):
        rows = pd.read_csv(out_name).to_dict("records")
        print(f"[resume] {len(rows)} rows already in {out_name}")
    done = {(r["seed"], r["adapt_cell"]) for r in rows}
    for seed in seeds:
        r = np.random.RandomState(seed)
        val_b = int(r.choice(uniq))
        m_val, m_fit = bn == val_b, np.ones_like(bn, bool)
        sc_n = MinMaxScaler().fit(Xn[m_fit])
        bp0, mu0, sd0, dims, l2, ep0 = fit_pool(
            sc_n.transform(Xn[m_fit]), yn[m_fit], sc_n.transform(Xn[m_val]), yn[m_val],
            seed, bp_max, pat)
        if bp0 is None:
            print(f"seed {seed}: NASA fit diverged - skipped")
            continue
        for adapt_cell in cells:
            if (seed, adapt_cell) in done:
                continue
            m_a = cells_c == adapt_cell
            m_te = cells_c != adapt_cell
            # fine-tune the frozen model on ONE other CS2 cell (same config, small budget)
            sc_a = MinMaxScaler().fit(Xc[m_a])
            mu_a, sd_a = yc[m_a].mean(), yc[m_a].std()
            try:
                bp_ft, _ = rc.fit_bpnn_ep([len(FEATS)] + dims, l2, sc_a.transform(Xc[m_a]),
                                          (yc[m_a] - mu_a) / sd_a, None, None, seed, bp_max, pat,
                                          epochs=ADAPT_EP)
                p = rc.predict(bp_ft, sc_a.transform(Xc[m_te]), mu_a, sd_a)
            except (TypeError, RuntimeError) as e:
                print(f"  [guard] adapt fit diverged ({type(e).__name__}); NaN row recorded")
                p = np.full(m_te.sum(), np.nan)
            mae, rmse, r2 = rc.reg_metrics(yc[m_te], p)
            rows.append(dict(seed=seed, adapt_cell=adapt_cell, test_cells=sorted(set(cells_c[m_te])),
                             n_cycles=int(m_te.sum()), cfg=f"{dims}/l2={l2}", adapt_epochs=ADAPT_EP,
                             MAE=round(float(mae), 3), RMSE=round(float(rmse), 3),
                             R2=round(float(r2), 3)))
            print(f"seed {seed} adapt={adapt_cell}: R2={r2:.3f} RMSE={rmse:.3f}")
            pd.DataFrame(rows).to_csv(out_name, index=False)
    out = pd.DataFrame(rows)
    print(f"\nsaved {out_name}: {len(out)} rows")
    if not args.smoke and len(out):
        print("\nLeave-one-cell-out adaptation (test = the other 7 cells):")
        print(out.groupby("adapt_cell").agg(R2=("R2", "mean"), R2min=("R2", "min"),
                                            R2max=("R2", "max"), RMSE=("RMSE", "mean")).round(3).to_string())
        print(f"\npooled: mean R2 {out.R2.mean():.3f}, median R2 {out.R2.median():.3f}")


if __name__ == "__main__":
    main()
