# Phase 1.3 (advisor R3-C3): target-proxy audit - the most important scientific question of Round 3.

# TD-All (8 features, includes the capacity proxy dis_duration) vs TD-Proxy-Free (7, proxy removed)
# vs Oracle-proxy (dis_duration alone: on a constant-current discharge Capacity = I x t, so the model
# is effectively handed the answer). Same nested-LOBO + refit-on-3 protocol as Phase 1.1,
# 4 folds x 3 seeds, per-fold metrics + prediction dumps for pooled metrics.
# TD-All is computed here AND in steps14_16_refit.py on purpose: identical numbers across the two
# scripts double as an internal consistency check of the shared code path.
# Device: default cpu, --device cuda|auto opt-in; recorded in filenames and in a `device` column.
# Usage: python td_proxy_audit.py --smoke | --full [--device cpu|cuda|auto]
import argparse, itertools, os
import pandas as pd
import r3common as R
from r3common import (BATT, SETTINGS, PROXY_FEATS, FEATS_PROXY_FREE,
                      load_td, soh_range_and_qref, run_fold, OUT)


def run(args):
    smoke = args.smoke
    R.set_device(args.device)
    seeds = [42] if smoke else [42, 7, 123]
    folds = [1] if smoke else [1, 2, 3, 4]
    bp_max, pat = (100, 10) if smoke else (500, 30)

    rng, qref = soh_range_and_qref()
    settings = {"TD-Proxy-Free": FEATS_PROXY_FREE, "Oracle-proxy": PROXY_FEATS} if smoke else SETTINGS
    rows, preds = [], []
    for name, feats in settings.items():
        X, bids, soh, cyc = load_td(feats)
        for seed, test_b in itertools.product(seeds, folds):
            r, p = run_fold(X, bids, soh, cyc, test_b, seed, bp_max, pat, qref, rng, name)
            rows += r
            preds.append(p)
            ref = [x for x in r if x["stage"] == "refit_on_3"][0]
            print(f"{name:14s} seed{seed} test={BATT[test_b]} n_feat={len(feats)} | "
                  f"R2={ref['test_R2']:+.3f} RMSE={ref['test_RMSE']:.3f}% "
                  f"MAPE={ref['test_MAPE']:.2f}%")

    res = pd.DataFrame(rows)
    res["device"] = R.DEVICE.type
    tag = ("smoke_" if smoke else "") + R.DEVICE.type
    res.to_csv(os.path.join(OUT, f"td_proxy_audit_{tag}_results.csv"), index=False)
    pd.concat(preds, ignore_index=True).to_csv(
        os.path.join(OUT, f"td_proxy_audit_{tag}_preds.csv"), index=False)

    if not smoke:
        ref = res[res.stage == "refit_on_3"]
        cols = ["test_MAE", "test_RMSE", "test_R2", "test_MAPE", "test_RMSE_Ah"]
        agg = ref.groupby("setting")[cols].agg(["mean", "std"]).round(3)
        print("\n=== refit_on_3, mean +/- std over 4 folds x 3 seeds ===\n", agg.to_string())
        agg.to_csv(os.path.join(OUT, f"td_proxy_audit_summary_{R.DEVICE.type}.csv"))
        print("\ntest_R2 per fold:")
        print(ref.pivot_table(index="test_battery", columns="setting", values="test_R2")
              .round(3).to_string())
        print("\ntest_RMSE %SOH per fold:")
        print(ref.pivot_table(index="test_battery", columns="setting", values="test_RMSE")
              .round(3).to_string())
    else:
        assert not res.isna().any().any(), "SMOKE FAIL: NaN in results"
        print("SMOKE OK: no NaN")
    print("saved")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--device", default="cpu", choices=["cpu", "cuda", "auto"])
    run(ap.parse_args())
