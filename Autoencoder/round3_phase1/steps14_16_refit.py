# Phase 1.1 (+1.2): TD-BPNN with the proper nested refit (advisor R3-C1).

# Inner validation selects the configuration on 2 batteries; the SAME configuration is then re-fitted
# on ALL remaining training batteries (3) for the selected epoch budget and evaluated on the outer
# test battery. Both stages are written out, so the effect of the refit is measured, not assumed.
# Metrics per fold: MAE / RMSE (%SOH and Ah) / R2 / MAPE / nRMSE. Per-sample predictions are dumped
# so phase1_aggregate.py can compute pooled R2 / RMSE / MAPE (advisor reporting standard).
# Device: default cpu (comparable with Round 2). --device cuda|auto is opt-in and is recorded in the
# output filenames and in a `device` column, so a GPU run can never be mistaken for a CPU run.
# Usage: python steps14_16_refit.py --smoke | --full [--device cpu|cuda|auto]
import argparse, itertools, os
import pandas as pd
import r3common as R
from r3common import BATT, FEATS_ALL, load_td, soh_range_and_qref, run_fold, OUT


def run(args):
    smoke = args.smoke
    R.set_device(args.device)
    seeds = [42] if smoke else [42, 7, 123]
    folds = [1] if smoke else [1, 2, 3, 4]
    bp_max, pat = (100, 10) if smoke else (500, 30)

    X, bids, soh, cyc = load_td(FEATS_ALL)
    rng, qref = soh_range_and_qref()
    rows, preds = [], []
    for seed, test_b in itertools.product(seeds, folds):
        r, p = run_fold(X, bids, soh, cyc, test_b, seed, bp_max, pat, qref, rng, "TD-All")
        rows += r
        preds.append(p)
        pre = [x for x in r if x["stage"] == "pre_refit"][0]
        ref = [x for x in r if x["stage"] == "refit_on_3"][0]
        print(f"seed{seed} test={BATT[test_b]} cfg={ref['cfg']} sel_epochs={ref['sel_epochs']} | "
              f"pre_refit R2={pre['test_R2']:+.3f} RMSE={pre['test_RMSE']:.3f} | "
              f"refit_on_3 R2={ref['test_R2']:+.3f} RMSE={ref['test_RMSE']:.3f} "
              f"(MAPE {ref['test_MAPE']:.2f}%, nRMSE {ref['test_nRMSE']:.3f})")

    res = pd.DataFrame(rows)
    res["device"] = R.DEVICE.type
    tag = ("smoke_" if smoke else "") + R.DEVICE.type
    res.to_csv(os.path.join(OUT, f"steps14_16_refit_{tag}_results.csv"), index=False)
    pd.concat(preds, ignore_index=True).to_csv(
        os.path.join(OUT, f"steps14_16_refit_{tag}_preds.csv"), index=False)

    if not smoke:
        cols = ["test_MAE", "test_RMSE", "test_R2", "test_MAPE", "test_RMSE_Ah", "test_nRMSE"]
        agg = res.groupby(["setting", "stage"])[cols].agg(["mean", "std"]).round(3)
        print("\n=== per stage, mean +/- std over 4 folds x 3 seeds ===\n", agg.to_string())
        agg.to_csv(os.path.join(OUT, f"steps14_16_refit_summary_{R.DEVICE.type}.csv"))
        for stage in ("pre_refit", "refit_on_3"):
            print(f"\ntest_R2 by fold ({stage}):")
            print(res[res.stage == stage].pivot_table(index="test_battery", values="test_R2")
                  .round(3).to_string())
        d = (res[res.stage == "refit_on_3"].groupby("test_battery").test_R2.mean()
             - res[res.stage == "pre_refit"].groupby("test_battery").test_R2.mean())
        print("\nrefit - pre_refit, mean test_R2 per fold:\n", d.round(3).to_string())
    else:
        assert not res.isna().any().any(), "SMOKE FAIL: NaN in results"
        assert (res.test_R2 > -5).all(), "SMOKE FAIL: absurd test R2"
        print("SMOKE OK: no NaN, both stages produced metrics")
    print("saved")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--device", default="cpu", choices=["cpu", "cuda", "auto"])
    run(ap.parse_args())
