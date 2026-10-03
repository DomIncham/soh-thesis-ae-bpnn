# Device benchmark: same fold-seed at the FULL budget on CPU and (optionally) CUDA.

# Purpose: decide the GPU question with a measurement instead of an assumption. The model is tiny
# (8 -> 16 -> 1, batch 32, ~336 samples), so per-step kernel-launch overhead can easily outrun the
# GPU's advantage. Reports wall time per device and how far the metrics moved.
# Numbers are reported device by device; a CUDA run is NOT interchangeable with a CPU run for
# comparison against Round 2, so the results file records the device used.
# Usage: python bench_device.py [--devices cpu,cuda]
import argparse, copy, time
import numpy as np
import r3common as R
from r3common import FEATS_ALL, load_td, soh_range_and_qref, run_fold, set_device, BATT


def timed(dev, X, bids, soh, cyc, rng, qref):
    set_device(dev)
    t0 = time.time()
    rows, _ = run_fold(X, bids, soh, cyc, 1, 42, 500, 30, qref, rng, "TD-All")
    dt = time.time() - t0
    return dt, {r["stage"]: r for r in rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--devices", default="cpu,cuda")
    args = ap.parse_args()

    X, bids, soh, cyc = load_td(FEATS_ALL)
    rng, qref = soh_range_and_qref()
    out = {}
    for dev in [d.strip() for d in args.devices.split(",") if d.strip()]:
        try:
            dt, res = timed(dev, X, bids, soh, cyc, rng, qref)
        except (SystemExit, RuntimeError) as e:
            print(f"--- {dev}: unavailable ({e})")
            continue
        out[dev] = (dt, res)
        ref = res["refit_on_3"]
        print(f"--- {dev}: {dt:.1f}s | refit R2={ref['test_R2']:+.4f} RMSE={ref['test_RMSE']:.4f} "
              f"| pre_refit R2={res['pre_refit']['test_R2']:+.4f}")

    if len(out) > 1:
        base = out.get("cpu")
        if base:
            t_cpu = base[0]
            print("\n=== speedup vs cpu ===")
            for dev, (dt, _) in out.items():
                print(f"{dev:5s} {dt:7.1f}s  ({t_cpu / dt:.2f}x)")
            print("\n=== metric drift vs cpu (same fold=B0005, seed=42) ===")
            for dev, (_, res) in out.items():
                if dev == "cpu":
                    continue
                for stage in ("pre_refit", "refit_on_3"):
                    d = max(abs(base[1][stage][k] - res[stage][k])
                            for k in ("test_R2", "test_RMSE", "test_MAE"))
                    print(f"{dev:5s} {stage:11s} max|diff| over R2/RMSE/MAE = {d:.4f}")
    print("\ndone")


if __name__ == "__main__":
    main()
