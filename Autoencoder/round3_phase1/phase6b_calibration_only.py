# Round 6B (R7-C0): calibration-only arm — frozen NASA backbone, affine output
# calibration y = a*yhat + b fitted on ONE labeled CALCE cell's L0 predictions,
# applied to the other 7 cells. NO NN training (backbone = P6-2 L0 dump
# phase6_preds_transfer_full.csv, parity-exact vs Round 5 transfer on Clean-5T).
# Matched keys vs Adapt2 (phase5_cs2_adapt2_c5t_full.csv) and Lc (phase6_ladder_Lc.csv):
# pool in {room, all13} x seed in 5 seeds x adapt_cell in 8 cells = 80 runs.
# Degenerate calibration (slope <= 0 or |slope-1| >= 1, Lc criterion) -> identity
# fallback (a=1, b=0), flagged; fallback disclosed per run (R6-C4).
# --smoke writes *_smoke files (1 pool x 2 seeds); full run OVERWRITES the main
# outputs fresh (no append — prevents smoke/full contamination).
# Usage: python phase6b_calibration_only.py [--smoke]
import argparse, os
import numpy as np
import pandas as pd

L0 = "phase6_preds_transfer_full.csv"
OUT_SUM = "phase6b_cal_only{}.csv"
OUT_DUMP = "phase6b_cal_only_preds{}.csv"


def prog(msg):
    print(msg, flush=True)


def reg(y, p):
    err = p - y
    return (np.abs(err).mean(), np.sqrt((err ** 2).mean()),
            1 - (err ** 2).sum() / ((y - y.mean()) ** 2).sum())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()
    sfx = "_smoke" if a.smoke else ""
    out_sum, out_dump = OUT_SUM.format(sfx), OUT_DUMP.format(sfx)
    prog(f"[load] {L0}")
    d = pd.read_csv(L0)
    assert set(d.arm.unique()) == {"transfer"}, "L0 dump must be the zero-shot transfer arm"
    assert d[["pool", "seed", "cell", "cycle"]].notna().all().all()
    n_dup = int(d.duplicated(["pool", "seed", "cell", "cycle"]).sum())
    assert n_dup == 0, f"L0 dump has {n_dup} duplicate keys"
    pools = ["room"] if a.smoke else ["room", "all13"]
    seeds = sorted(d.seed.unique())[:2] if a.smoke else sorted(d.seed.unique())
    cells_all = {p: sorted(d[d.pool == p].cell.unique()) for p in pools}
    n_expect = len(pools) * len(seeds) * len(cells_all[pools[0]])
    prog(f"[plan] pools={pools} seeds={seeds} cells={len(cells_all[pools[0]])} -> {n_expect} runs")
    if not a.smoke:
        for f in (out_sum, out_dump):
            if os.path.exists(f):
                os.remove(f)
                prog(f"[clean] removed stale {f}")
    rows, dump = [], []
    for pool in pools:
        dp = d[d.pool == pool]
        cells = cells_all[pool]
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
                    slope_use, inter_use = 1.0, 0.0  # identity fallback, disclosed
                else:
                    slope_use, inter_use = slope, inter
                p = slope_use * dt.yhat.values + inter_use
                mae, rmse, r2 = reg(dt.y.values, p)
                rows.append(dict(rung="cal_only", pool=pool, seed=seed, adapt_cell=adapt,
                                 n_cycles=len(dt), cal_slope=round(float(slope), 4),
                                 cal_intercept=round(float(inter), 4),
                                 cal_degenerate=deg, fallback_used=deg,
                                 MAE=round(float(mae), 3), RMSE=round(float(rmse), 3),
                                 R2=round(float(r2), 3)))
                dd = dt.copy()
                dd["yhat_cal"] = np.round(p, 4)
                dd["arm"], dd["adapt_cell"], dd["cal_degenerate"] = "cal_only", adapt, deg
                dump.append(dd[["seed", "arm", "pool", "cell", "adapt_cell", "cycle",
                                "y", "yhat", "yhat_cal", "cal_degenerate"]])
            prog(f"[run] {pool} s{seed} done ({len(rows)}/{n_expect})")
    out = pd.DataFrame(rows)
    dmp = pd.concat(dump, ignore_index=True)
    assert len(out) == n_expect, f"expected {n_expect} runs, got {len(out)}"
    assert not dmp.duplicated(["pool", "seed", "adapt_cell", "cell", "cycle"]).any()
    # leak check: every calibrated test row must come from a cell != adapt cell
    assert (dmp.cell != dmp.adapt_cell).all(), "leak: adapt cell rows inside test set"
    bad = (~dmp.apply(lambda r: r.cell in cells_all[r.pool], axis=1)).sum()
    assert bad == 0, f"{bad} test rows outside the pool's cell list"
    out.to_csv(out_sum, index=False)
    dmp.to_csv(out_dump, index=False)
    prog(f"[write] {out_sum} ({len(out)} runs) + {out_dump} ({len(dmp)} rows)")
    prog(f"[result] runs: {len(out)} | degenerate calibrations: {int(out.cal_degenerate.sum())} "
         f"({out.cal_degenerate.mean():.0%})")
    prog(out.groupby("pool")[["MAE", "RMSE", "R2"]].agg(["mean", "median"]).round(3).to_string())


if __name__ == "__main__":
    main()
