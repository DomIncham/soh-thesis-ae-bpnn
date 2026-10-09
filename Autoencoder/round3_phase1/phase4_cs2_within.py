# Phase 4 item 6.3 (R3-C6): CONTROL - leave-one-cell-out WITHIN CS2 (train 7, test 1).
# Purpose: prove the cross-dataset failure is domain shift, not a CS2 data/parser problem.
# Full nested protocol on the CS2 pool itself: per (seed, test cell) - config selection with one
# held-out CS2 val battery, refit on the remaining training cells, score the untouched test cell.
# Feature set: Clean-6T (same as the transfer runs). Comparison targets:
#   frozen NASA->CS2 (median -24/-37), 1-cell warm adapt (~-50), and now within-CS2 LOCO.
# Usage: python phase4_cs2_within.py            # 5 seeds, full (~10-15 min)
#        python phase4_cs2_within.py --smoke    # 1 seed, tiny budget (mechanics only)
import argparse, itertools, os
import numpy as np
import pandas as pd
import r3common as rc
from sklearn.preprocessing import MinMaxScaler

# Clean-6T (Round 4 advisor correction) = Clean-8 minus the two temperature features unavailable
# in CS2 logs; dis_duration and dis_mean_V are proxy/proxy-equivalent and MUST NOT be present.
FEATS = ["dis_V_slope", "cc_dur", "cv_dur", "cv_I_slope", "t_40_41", "ic_peak_V"]
SEEDS = [42, 123, 2024, 7, 99]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--device", default="cpu")
    args = ap.parse_args()
    rc.set_device(args.device)
    seeds = [42] if args.smoke else SEEDS
    bp_max, pat = (60, 10) if args.smoke else (300, 20)
    tag = "smoke" if args.smoke else "full"
    out_name = f"phase4_cs2_within_{tag}.csv"

    cs2 = pd.read_csv("phase4_cs2_features.csv")
    cs2 = cs2[cs2.include_cell & cs2.cap_ok].dropna(subset=FEATS).reset_index(drop=True)
    cs2["bid"] = cs2.battery.astype("category").cat.codes
    X, y, b, cells = cs2[FEATS].values, cs2.soh.values, cs2.bid.values, sorted(set(cs2.battery))
    u = np.unique(b)
    print(f"CS2 within-pool: {len(cs2)} rows, {len(cells)} cells")

    rows = []
    if os.path.exists(out_name):
        rows = pd.read_csv(out_name).to_dict("records")
        print(f"[resume] {len(rows)} rows already in {out_name}")
    done = {(r["seed"], r["test_battery"]) for r in rows}
    for seed in seeds:
        r = np.random.RandomState(seed)
        for test_i in u:
            if (seed, test_i) in done:
                continue
            pool = [b0 for b0 in u if b0 != test_i]
            tr = list(r.choice(pool, size=len(pool), replace=False))
            val_b, fit_b = tr[0], tr
            m_te, m_va = b == test_i, b == val_b
            m_fit = np.isin(b, fit_b)
            m_sel = np.isin(b, [b0 for b0 in fit_b if b0 != val_b])
            sc = MinMaxScaler().fit(X[m_sel])
            mu, sd = y[m_sel].mean(), y[m_sel].std()
            cands = []
            for dims, l2 in itertools.product(rc.ARCHS, rc.L2S):
                try:
                    bp, ep = rc.fit_bpnn_ep([len(FEATS)] + dims, l2, sc.transform(X[m_sel]),
                                            (y[m_sel] - mu) / sd, sc.transform(X[m_va]),
                                            (y[m_va] - mu) / sd, seed, bp_max, pat)
                except (TypeError, RuntimeError):
                    continue
                v = float(np.sqrt(np.mean((rc.predict(bp, sc.transform(X[m_va]), mu, sd) - y[m_va]) ** 2)))
                cands.append((v, dims, l2, ep))
            ok = [c for c in cands if c[3] >= rc.MIN_EP and np.isfinite(c[0])]
            if not ok:
                _, dims, l2, ep = (min(cands, key=lambda c: c[0]) if cands else (0, [8], 0.0, 200))
                ep = 200
            else:
                _, dims, l2, ep = min(ok, key=lambda c: c[0])
            sc2 = MinMaxScaler().fit(X[m_fit])
            mu2, sd2 = y[m_fit].mean(), y[m_fit].std()
            try:
                bp_rf, _ = rc.fit_bpnn_ep([len(FEATS)] + dims, l2, sc2.transform(X[m_fit]),
                                          (y[m_fit] - mu2) / sd2, None, None, seed, bp_max, pat,
                                          epochs=ep)
                p = rc.predict(bp_rf, sc2.transform(X[m_te]), mu2, sd2)
            except (TypeError, RuntimeError) as e:
                print(f"  [guard] diverged ({type(e).__name__}); NaN row recorded")
                p = np.full(int(m_te.sum()), np.nan)
            mae, rmse, r2 = rc.reg_metrics(y[m_te], p)
            rows.append(dict(seed=seed, test_battery=cells[list(u).index(test_i)],
                             val_battery=cells[list(u).index(val_b)],
                             n_cycles=int(m_te.sum()), cfg=f"{dims}/l2={l2}", sel_epochs=ep,
                             MAE=round(float(mae), 3), RMSE=round(float(rmse), 3),
                             R2=round(float(r2), 3)))
            print(f"seed {seed} test {cells[list(u).index(test_i)]}: R2={r2:.3f}")
            pd.DataFrame(rows).to_csv(out_name, index=False)
    out = pd.DataFrame(rows).drop_duplicates(subset=["seed", "test_battery"], keep="last")
    out.to_csv(out_name, index=False)
    print(f"\nsaved {out_name}: {len(out)} rows (deduplicated)")
    if not args.smoke and len(out):
        print("\nWithin-CS2 LOCO per test cell:")
        print(out.groupby("test_battery").agg(R2=("R2", "mean"), R2min=("R2", "min"),
                                              R2max=("R2", "max"), RMSE=("RMSE", "mean")).round(3).to_string())
        print(f"\npooled: mean {out.R2.mean():.3f}, median {out.R2.median():.3f}")


if __name__ == "__main__":
    main()
