# Round 6B (R7-C0): calibration-only arm — frozen NASA backbone, affine output
# calibration y = a*yhat + b fitted on ONE labeled CALCE cell's L0 predictions,
# applied to the other 7 cells. NO NN training (backbone = P6-2 L0 dump
# phase6_preds_transfer_full.csv, parity-exact vs Round 5 transfer on Clean-5T).
# Matched keys vs Adapt2 (phase5_cs2_adapt2_c5t_full.csv) and Lc (phase6_ladder_Lc.csv):
# pool in {room, all13} x seed in 5 seeds x adapt_cell in 8 cells = 80 runs.
# Degenerate calibration (slope <= 0 or |slope-1| >= 1, Lc criterion) -> identity
# fallback (a=1, b=0), flagged; fallback disclosed per run (R6-C4).
# Usage: python phase6b_calibration_only.py [--smoke]
import argparse, os
import numpy as np
import pandas as pd

L0 = "phase6_preds_transfer_full.csv"
OUT_SUM = "phase6b_cal_only.csv"
OUT_DUMP = "phase6b_cal_only_preds.csv"


def reg(y, p):
    err = p - y
    return (np.abs(err).mean(), np.sqrt((err ** 2).mean()),
            1 - (err ** 2).sum() / ((y - y.mean()) ** 2).sum())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()
    d = pd.read_csv(L0)
    assert set(d.arm.unique()) == {"transfer"}, "L0 dump must be the zero-shot transfer arm"
    assert d[["pool", "seed", "cell", "cycle"]].notna().all().all()
    pools = ["room"] if a.smoke else ["room", "all13"]
    seeds = sorted(d.seed.unique())[:2] if a.smoke else sorted(d.seed.unique())
    rows, dump = [], []
    for pool in pools:
        dp = d[d.pool == pool]
        cells = sorted(dp.cell.unique())
        for seed in seeds:
            ds = dp[dp.seed == seed]
            for adapt in cells:
                da = ds[ds.cell == adapt]
                dt = ds[ds.cell != adapt]
                # affine fit on the ONE adapt cell's frozen-backbone predictions only
                A = np.vstack([da.yhat.values, np.ones(len(da))]).T
                slope, inter = np.linalg.lstsq(A, da.y.values, rcond=None)[0]
                deg = (slope <= 0) or (abs(slope - 1) >= 1)
                if deg:
                    slope, inter = 1.0, 0.0  # identity fallback, disclosed below
                p = slope * dt.yhat.values + inter
                mae, rmse, r2 = reg(dt.y.values, p)
                rows.append(dict(rung="cal_only", pool=pool, seed=seed, adapt_cell=adapt,
                                 n_cycles=len(dt), cal_slope=round(float(slope), 4), cal_intercept=round(float(inter), 4),
                                 cal_degenerate=deg, fallback_used=deg,
                                 MAE=round(float(mae), 3), RMSE=round(float(rmse), 3),
                                 R2=round(float(r2), 3)))
                dd = dt.copy()
                dd["yhat_cal"] = np.round(p, 4)
                dd["arm"], dd["adapt_cell"], dd["cal_degenerate"] = "cal_only", adapt, deg
                dump.append(dd[["seed", "arm", "pool", "cell", "adapt_cell", "cycle",
                                "y", "yhat", "yhat_cal", "cal_degenerate"]])
    out = pd.DataFrame(rows)
    dmp = pd.concat(dump, ignore_index=True)
    # leak check: the adapt cell's own rows must not appear as calibrated test rows
    assert not dmp.duplicated(["pool", "seed", "adapt_cell", "cell", "cycle"]).any()
    # per-cell identity: every test row's cell != its adapt_cell
    assert (dmp.cell != dmp.adapt_cell).all(), "leak: adapt cell rows inside test set"
    out.to_csv(OUT_SUM, index=False)
    dmp.to_csv(OUT_DUMP, mode="a", header=not os.path.exists(OUT_DUMP), index=False)
    print(f"runs: {len(out)} | degenerate calibrations: {int(out.cal_degenerate.sum())} "
          f"({out.cal_degenerate.mean():.0%})")
    print(out.groupby("pool")[["MAE", "RMSE", "R2"]].agg(["mean", "median"]).round(3).to_string())


if __name__ == "__main__":
    main()
