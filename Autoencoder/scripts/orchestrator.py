#!/usr/bin/env python3
"""
orchestrator.py — Master CLI for Thesis Pipeline (A, B, C, E phases)
Usage:
    python scripts/orchestrator.py --phase cv --config configs/ae_v3_bpnn_v2.yaml
    python scripts/orchestrator.py --phase ablation --base-run runs/ae_v3_bpnn_v2/fold_0
    python scripts/orchestrator.py --phase eval --run-dir runs/ae_v3_bpnn_v2/fold_0
    python scripts/orchestrator.py --phase report --results ablation_summary.csv

Phases:
    cv         : 4-fold LOBO (train_fold.py ×4, parallel via sub-agent or sequential)
    ablation   : Ablation sweep via ablation_run.py
    eval       : Evaluate saved checkpoints + generate plots
    report     : Aggregate CSV results → markdown table + best config YAML
"""
import argparse, subprocess, sys, json, yaml
from pathlib import Path
from collections import OrderedDict

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", required=True, choices=["cv", "ablation", "eval", "report"])
    parser.add_argument("--workdir", default="C:/Master Degree/Thesis/Autoencoder")
    parser.add_argument("--config", default="configs/ae_v3_bpnn_v2.yaml")
    parser.add_argument("--base-run", default="runs/ae_v3_bpnn_v2/fold_0")
    args = parser.parse_args()

    workdir = Path(args.workdir)
    print(f"=== Orchestrator Phase: {args.phase} ===")
    print(f"Workdir: {workdir}")
    print(f"Config:  {workdir / args.config}")

    if args.phase == "cv":
        # Sequential 4-fold CV execution (parallel version uses delegate_task)
        for fold in range(4):
            print(f"\n[Orchestrator CV] Running fold {fold} ...")
            cmd = [
                sys.executable, str(workdir / "scripts/train_fold.py"),
                "--fold", str(fold),
                "--config", str(workdir / args.config),
                "--workdir", str(workdir)
            ]
            result = subprocess.run(cmd, timeout=1800)
            print(f"  Fold {fold}: exit={result.returncode}")
        print("[Orchestrator CV] Complete. Aggregate results manually or via sub-agent.")

    elif args.phase == "ablation":
        print("[Orchestrator Ablation] Delegating to ablation_run.py ...")
        cmd = [sys.executable, str(workdir / "scripts/ablation_run.py"),
               "--workdir", str(workdir), "--base-run", args.base_run]
        result = subprocess.run(cmd, timeout=3600)
        print(f"  Exit: {result.returncode}")

    elif args.phase == "eval":
        run_dir = workdir / args.base_run
        metrics_file = run_dir / "metrics.json"
        if not metrics_file.exists():
            print(f"[ERROR] Metrics file not found: {metrics_file}")
            return
        with open(metrics_file) as f:
            metrics = json.load(f)
        print(f"[Orchestrator Eval] Fold {metrics['fold']} (Battery ID: {metrics['test_battery_id']})")
        print(f"  Train RMSE: {metrics['train_rmse']:.5f} Ah  |  R²: {metrics['train_r2']:.4f}")
        print(f"  Test  RMSE: {metrics['test_rmse']:.5f} Ah  |  R²: {metrics['test_r2']:.4f}")
        print(f"  Gap:        {metrics['generalization_gap_rmse']:.5f} Ah")

    elif args.phase == "report":
        results_file = workdir / "ablation_summary.csv"
        if not results_file.exists():
            # Try relative path
            results_file = Path("ablation_summary.csv")
        if not results_file.exists():
            print(f"[ERROR] Results file not found: {results_file}")
            return
        import csv
        best = None
        with open(results_file) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            for r in rows:
                try:
                    rmse = float(r.get("test_rmse", float('inf')))
                    if best is None or rmse < best["test_rmse"]:
                        best = {"test_rmse": rmse, **r}
                except ValueError:
                    pass
        print(f"[Orchestrator Report] Read {len(rows)} results from {results_file}")
        if best:
            print(f"  Best config: bottleneck={best.get('bottleneck')}, loss={best.get('loss')}, L2={best.get('l2')}, RMSE={best['test_rmse']:.5f}")
        # Save best config YAML (simplified)
        best_config = {
            "experiment_name": "best_ablation_config",
            "autoencoder": {"bottleneck_dim": int(best.get("bottleneck", 17)) if best.get("bottleneck") else 17},
            "bpnn": {"hidden_layers": [16, 8]},
            "training": {"bpnn_l2": float(best.get("l2", 1e-4)) if best.get("l2") else 1e-4,
                        "bpnn_loss": best.get("loss", "mse") if best.get("loss") else "mse"}
        }
        with open(workdir / "best_config.yaml", "w") as f:
            yaml.dump(best_config, f, default_flow_style=False)
        print(f"  Best config saved to: {workdir / 'best_config.yaml'}")

    print(f"=== Phase {args.phase} Complete ===")

if __name__ == "__main__":
    main()
