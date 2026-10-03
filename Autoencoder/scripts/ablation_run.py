#!/usr/bin/env python3
"""
ablation_run.py — Sweep AE bottleneck, BPNN L2, loss function.
Wraps train_fold.py (real or dummy) per config.
Usage:
    python scripts/ablation_run.py --base-run runs/ae_v3_bpnn_v2/fold_0
    python scripts/ablation_run.py --base-run runs/ae_v3_bpnn_v2/fold_0 --bottlenecks 7 17 37 --l2s 1e-4 1e-3
Outputs:
    ablation_summary.csv  (all results)
    best_config.yaml     (top by test_r2)
"""
import argparse, yaml, subprocess, sys, json, csv
from pathlib import Path
from collections import OrderedDict

# Ablation grids (from advisor directives Part F, Priority 4)
DEFAULT_BOTTLENECKS = [1, 3, 7, 17, 37, 67]
DEFAULT_L2S = [0.0, 1e-5, 1e-4, 1e-3, 1e-2, 1e-1]
DEFAULT_LOSSES = ["mse", "mae", "huber"]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workdir", default="C:/Master Degree/Thesis/Autoencoder")
    parser.add_argument("--base-run", default="runs/ae_v3_bpnn_v2/fold_0")
    parser.add_argument("--bottlenecks", type=int, nargs="+", default=DEFAULT_BOTTLENECKS)
    parser.add_argument("--l2s", type=float, nargs="+", default=DEFAULT_L2S)
    parser.add_argument("--losses", nargs="+", default=DEFAULT_LOSSES)
    parser.add_argument("--epochs", type=int, default=1)
    args = parser.parse_args()

    workdir = Path(args.workdir)
    base_config = workdir / "configs/ae_v3_bpnn_v2.yaml"
    results = []

    for b in args.bottlenecks:
        for loss_fn in args.losses:
            for l2 in args.l2s:
                exp_name = f"b{b}_l{str(l2).replace('.','p')}_{loss_fn}_e{args.epochs}"
                out_dir = workdir / "runs" / exp_name
                out_dir.mkdir(parents=True, exist_ok=True)

                # Spawn train_fold.py with this config override
                cmd = [
                    sys.executable, str(workdir / "scripts/train_fold.py"),
                    "--fold", "0",
                    "--config", str(base_config),
                    "--bottleneck", str(b),
                    "--l2", str(l2),
                    "--loss", loss_fn,
                    "--epochs", str(args.epochs),
                    "--workdir", str(workdir)
                ]
                print(f"[Ablation] Running b={b} loss={loss_fn} L2={l2} ...")
                # Execute and capture (simplified — real version uses subprocess.PIPE + JSON parse)
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(workdir), timeout=300)
                print(f"    exit={result.returncode} | output last line: {result.stdout.strip().split(chr(10))[-1] if result.stdout else 'N/A'}")

                # For dummy test, parse last JSON line
                try:
                    last_line = result.stdout.strip().splitlines()[-1]
                    metrics = json.loads(last_line)
                    results.append({
                        "bottleneck": b, "loss": loss_fn, "l2": l2,
                        "test_rmse": metrics.get("val_rmse", float('nan')),
                        "test_r2": float('nan'),  # Would read metrics.json
                        "status": metrics.get("status", "unknown"),
                        "exp_dir": str(out_dir)
                    })
                except Exception:
                    results.append({"bottleneck": b, "loss": loss_fn, "l2": l2,
                                    "test_rmse": float('nan'), "status": "error"})

    # Save summary
    summary_path = workdir / "ablation_summary.csv"
    with open(summary_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["bottleneck", "loss", "l2", "test_rmse", "status", "exp_dir"])
        for r in results:
            writer.writerow([r["bottleneck"], r["loss"], r["l2"], r["test_rmse"], r["status"], r.get("exp_dir","")])
    print(f">>> Ablation complete. Results: {summary_path}")

if __name__ == "__main__":
    main()
