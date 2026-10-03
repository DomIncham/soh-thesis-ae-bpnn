# Phase 1.2: pooled metrics (advisor R3-C1 reporting standard).

# Advisor requires R2 as per-fold mean AND pooled, RMSE in both %SOH and Ah, plus MAPE.
# Pooled = the 4 outer-test folds concatenated (each fold is a different battery, so the pooled set
# covers all 636 cycles). The pooled R2 denominator therefore contains between-battery variance,
# which is exactly the effect the advisor flagged (factor 5 of the audit).
# Computed per seed, then averaged; "grand pooled" pools every seed as well (identical samples, so it
# is reported for reference only).
# Reads *_preds.csv written by steps14_16_refit.py and td_proxy_audit.py. The device is read back
# from each filename, so a cpu run and a cuda run never blend into one pooled block.
# Usage: python phase1_aggregate.py [--indir DIR] [--allow-partial]
import argparse, glob, os
import numpy as np, pandas as pd
from r3common import OUT, BATT, soh_range_and_qref

REV = {v: k for k, v in BATT.items()}
KEYS = ["pooled_R2", "pooled_RMSE", "pooled_MAE", "pooled_MAPE", "pooled_RMSE_Ah", "pooled_nRMSE"]


def r2(y, yh):
    ss = ((y - y.mean()) ** 2).sum()
    return float(1 - ((y - yh) ** 2).sum() / ss) if ss > 0 else float("nan")


def pooled_block(df, qref, rng):
    y, yh = df.y_true.values, df.y_pred.values
    rmse = float(np.sqrt(np.mean((y - yh) ** 2)))
    bid = REV[df.test_battery.iloc[0]]
    return dict(n=len(y),
                pooled_R2=r2(y, yh),
                pooled_RMSE=rmse,
                pooled_MAE=float(np.mean(np.abs(y - yh))),
                pooled_MAPE=float(np.mean(np.abs((y - yh) / y)) * 100),
                pooled_RMSE_Ah=rmse / 100.0 * float(qref.loc[bid]),
                pooled_nRMSE=rmse / float(rng.loc[bid]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--indir", default=OUT, help="directory holding *_preds.csv (default: this folder)")
    ap.add_argument("--allow-partial", action="store_true",
                    help="allow pooled blocks with fewer than 4 folds (smoke checks only)")
    args = ap.parse_args()
    indir = args.indir if os.path.isabs(args.indir) else os.path.join(OUT, args.indir)

    files = sorted(f for f in glob.glob(os.path.join(indir, "*preds.csv"))
                   if "smoke" not in os.path.basename(f))
    assert files, (f"no prediction dumps found in {indir} - run steps14_16_refit.py / "
                   f"td_proxy_audit.py first")
    rng, qref = soh_range_and_qref()
    print("prediction dumps:", [os.path.basename(f) for f in files])

    rows = []
    for f in files:
        base = os.path.basename(f)
        dev = "cuda" if "_cuda_" in base else "cpu"
        df = pd.read_csv(f)
        for (setting, stage, seed), g in df.groupby(["setting", "stage", "seed"]):
            nf = g.test_battery.nunique()
            if nf != 4:
                msg = f"{dev}/{setting}/{stage}/seed{seed}: expected 4 folds, got {nf}"
                if not args.allow_partial:
                    raise AssertionError(msg + " - pooled metrics need all 4 outer folds")
                print("WARNING (partial):", msg)
            rows.append(dict(source=base, device=dev, setting=setting, stage=stage,
                             seed=int(seed),
                             scope="per_seed_pooled_4_folds" if nf == 4 else "partial_pooled",
                             **pooled_block(g, qref, rng)))
        for (setting, stage), g in df.groupby(["setting", "stage"]):
            rows.append(dict(source=base, device=dev, setting=setting, stage=stage,
                             seed=-1, scope="grand_pooled_all_seeds", **pooled_block(g, qref, rng)))

    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(OUT, "phase1_pooled_metrics.csv"), index=False)
    if out.device.nunique() > 1:
        print("\nNOTE: both cpu and cuda dumps present - blocks are reported separately per device.")

    ps = out[out.scope == "per_seed_pooled_4_folds"]
    print("\n=== pooled (4 folds concatenated) per seed ===\n")
    print(ps.round(4).to_string(index=False))
    print("\n=== pooled mean / median / std across seeds ===\n")
    print(ps.groupby(["device", "setting", "stage"])[KEYS].agg(["mean", "median", "std"])
          .round(4).to_string())
    print("\n=== grand pooled (all seeds) ===\n")
    print(out[out.scope == "grand_pooled_all_seeds"].round(4).to_string(index=False))
    print("\nsaved: phase1_pooled_metrics.csv")


if __name__ == "__main__":
    main()
