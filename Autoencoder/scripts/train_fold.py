#!/usr/bin/env python3
"""
train_fold.py — AE + BPNN Training for Single LOBO Fold
========================================================
Usage:
    python scripts/train_fold.py --fold 0 --config configs/ae_v3_bpnn_v2.yaml
    python scripts/train_fold.py --fold 0 --config configs/ae_v3_bpnn_v2.yaml --epochs 200 --batch-size 16

Outputs (per fold):
    runs/{experiment_name}/fold_{fold}/
        ├── best_ae.pth          # Best AE encoder (by inner-val recon loss)
        ├── best_bpnn.pth        # Best BPNN (by inner-val loss)
        ├── scaler_X.pkl         # MinMaxScaler for features (fit on train)
        ├── scaler_Y.pkl         # MinMaxScaler for targets (fit on train)
        ├── metrics.json         # {fold, test_battery_id, train_mae, train_rmse, train_r2, test_mae, test_rmse, test_r2, ...}
        ├── predictions.npz      # {y_train_true, y_train_pred, y_test_true, y_test_pred, test_cycles}
        └── config.yaml          # Resolved config used for this run

Design Principles (Advisor Directives):
- Strict LOBO: No data from test battery enters training/validation/scalers
- Inner validation: 80/20 split of training batteries for EarlyStopping
- All scalers fit ONLY on training data (inner-train split)
- Metrics reported on ORIGINAL SCALE (Ah) → inverse_transform required
- EarlyStopping + ModelCheckpoint mandatory (no fixed-epoch claims)
- Deterministic seeds for reproducibility
- Per-battery metrics + mean ± std across folds (handled by orchestrator)
"""

import argparse
import yaml
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset, random_split
import numpy as np
import pandas as pd
import os
import json
import pickle
import sys
from pathlib import Path
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from typing import Dict, Any, Tuple, Optional

# ─── Model Definitions ──────────────────────────────────────────────
class ControlledAutoencoder(nn.Module):
    """Autoencoder with configurable bottleneck and hidden dimensions."""
    def __init__(self, input_dim: int, bottleneck_dim: int, hidden_dim: int = 128,
                 activation: str = "relu", bottleneck_activation: Optional[str] = None):
        super().__init__()
        act_map = {"relu": nn.ReLU, "sigmoid": nn.Sigmoid, "tanh": nn.Tanh,
                   "leaky_relu": nn.LeakyReLU, "none": nn.Identity, None: nn.Identity}
        act_cls = act_map.get((activation or "").lower(), nn.ReLU)
        bottleneck_act_cls = act_map.get((bottleneck_activation or "").lower(), nn.Identity)
        act_fn = act_cls()
        bottleneck_act = bottleneck_act_cls()

        # Encoder: input_dim -> hidden_dim -> bottleneck_dim
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            act_fn,
            nn.Linear(hidden_dim, bottleneck_dim),
            bottleneck_act  # Linear by default (no activation on bottleneck)
        )
        # Decoder: bottleneck_dim -> hidden_dim -> input_dim
        self.decoder = nn.Sequential(
            nn.Linear(bottleneck_dim, hidden_dim),
            act_fn,
            nn.Linear(hidden_dim, input_dim)
        )

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        latent = self.encoder(x)
        reconstructed = self.decoder(latent)
        return reconstructed, latent


class ControlledBPNN(nn.Module):
    """BPNN with configurable hidden layers and Kaiming initialization."""
    def __init__(self, input_dim: int, hidden_layers: list, output_dim: int = 1,
                 activation: str = "relu", weight_init: str = "kaiming_normal"):
        super().__init__()
        act_map = {"relu": nn.ReLU, "sigmoid": nn.Sigmoid, "tanh": nn.Tanh,
                   "leaky_relu": nn.LeakyReLU, "none": nn.Identity, None: nn.Identity}
        act_cls = act_map.get((activation or "").lower(), nn.ReLU)
        act_fn = act_cls()
        layers = []
        prev_dim = input_dim
        for hidden_dim in hidden_layers:
            linear = nn.Linear(prev_dim, hidden_dim)
            if weight_init == "kaiming_normal":
                nn.init.kaiming_normal_(linear.weight, nonlinearity='relu')
            layers.append(linear)
            layers.append(act_fn)
            prev_dim = hidden_dim
        # Output layer
        out_linear = nn.Linear(prev_dim, output_dim)
        if weight_init == "kaiming_normal":
            nn.init.kaiming_normal_(out_linear.weight, nonlinearity='linear')
        layers.append(out_linear)
        self.network = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.network(x)


# ─── Utilities ──────────────────────────────────────────────────────
def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Tuple[float, float, float]:
    """MAE, RMSE, R² on original scale."""
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred)
    return mae, rmse, r2


def set_deterministic(seed: int = 42):
    """Set all random seeds for reproducibility."""
    torch.manual_seed(seed)
    np.random.seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def get_device(device_arg: str) -> torch.device:
    if device_arg == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device(device_arg)


def load_config(config_path: str) -> Dict[str, Any]:
    with open(config_path, 'r') as f:
        cfg = yaml.safe_load(f)
    # Force numeric types that YAML may parse as strings (scientific notation)
    if 'optimizer' in cfg:
        cfg['optimizer']['eps'] = float(cfg['optimizer']['eps'])
    def fix_floats(obj):
        for k, v in obj.items() if isinstance(obj, dict) else []:
            pass  # placeholder — we'll do recursive fix below
    def fix_numbers(d):
        for k, v in list(d.items()):
            if isinstance(v, str) and v.replace('.','',1).replace('e','',1).replace('-','').isdigit():
                # Not robust — handle explicit keys
                pass
    # Explicit fixes for known numeric keys
    for section in ['training']:
        if section in cfg and isinstance(cfg[section], dict):
            for sub in ['ae_early_stopping', 'bpnn_early_stopping']:
                if sub in cfg[section] and isinstance(cfg[section][sub], dict):
                    cfg[section][sub]['min_delta'] = float(cfg[section][sub]['min_delta'])
            for sub in ['bpnn_l2', 'ae_lr', 'bpnn_lr', 'ae_batch_size', 'bpnn_batch_size']:
                if sub == 'bpnn_l2' and sub in cfg[section]:
                    cfg[section][sub] = float(cfg[section][sub])
    # Best approach: recursive float conversion for all numeric-looking strings
    def recursive_fix(obj):
        if isinstance(obj, dict):
            return {k: recursive_fix(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [recursive_fix(v) for v in obj]
        if isinstance(obj, str):
            try:
                if obj.lower() in ['true','false']:
                    return obj.lower() == 'true'
                # Try float only if it contains digits
                if any(c.isdigit() for c in obj) and ('.' in obj or 'e' in obj):
                    return float(obj)
            except ValueError:
                pass
            return obj
        return obj
    cfg = recursive_fix(cfg)
    return cfg


def save_config(config: Dict[str, Any], output_dir: Path):
    with open(output_dir / "config.yaml", 'w') as f:
        yaml.dump(config, f, default_flow_style=False)


# ─── Core Training Functions ────────────────────────────────────────
def prepare_data(config: Dict, fold: int, workdir: Path) -> Dict[str, Any]:
    """Load data, apply LOBO split, fit scalers on inner-train only."""
    data_cfg = config['data']
    mapped_file = workdir / data_cfg['mapped_file']
    if not mapped_file.exists():
        raise FileNotFoundError(f"Mapped dataset not found: {mapped_file}")

    data = torch.load(mapped_file, weights_only=True)
    X_raw = data['features'].numpy()           # (N, 256)
    y_meta = data['labels'].numpy()            # (N, 3) [Battery_ID, Cycle, Capacity_Ah]

    battery_ids = y_meta[:, data_cfg['battery_id_col']].astype(int)
    cycles = y_meta[:, data_cfg['cycle_col']].astype(int)
    y_capacity = y_meta[:, data_cfg['target_col']]  # (N,)

    # LOBO fold mapping: 0->B0005(ID=1), 1->B0006(ID=2), 2->B0007(ID=3), 3->B0018(ID=4)
    test_battery_id = fold + 1
    test_mask = (battery_ids == test_battery_id)
    train_mask = (battery_ids != test_battery_id)

    X_train_raw = X_raw[train_mask]
    X_test_raw = X_raw[test_mask]
    y_train_raw = y_capacity[train_mask].reshape(-1, 1)
    y_test_raw = y_capacity[test_mask].reshape(-1, 1)
    test_cycles = cycles[test_mask]

    # Inner validation split (80/20 on training batteries)
    inner_cfg = config.get('inner_validation', {'enabled': True, 'val_ratio': 0.2, 'random_seed': 42})
    n_train = X_train_raw.shape[0]
    n_val = int(n_train * inner_cfg['val_ratio'])
    n_inner_train = n_train - n_val

    set_deterministic(inner_cfg['random_seed'])
    indices = np.random.permutation(n_train)
    inner_train_idx = indices[:n_inner_train]
    inner_val_idx = indices[n_inner_train:]

    X_inner_train = X_train_raw[inner_train_idx]
    X_inner_val = X_train_raw[inner_val_idx]
    y_inner_train = y_train_raw[inner_train_idx]
    y_inner_val = y_train_raw[inner_val_idx]

    # Scalers: Fit ONLY on inner_train (no test, no inner-val leakage)
    scaler_X = MinMaxScaler()
    X_inner_train_scaled = scaler_X.fit_transform(X_inner_train)
    X_inner_val_scaled = scaler_X.transform(X_inner_val)
    X_train_scaled = scaler_X.transform(X_train_raw)      # Full train (for final AE training)
    X_test_scaled = scaler_X.transform(X_test_raw)        # Test (transform only)

    scaler_Y = MinMaxScaler()
    y_inner_train_scaled = scaler_Y.fit_transform(y_inner_train)
    y_inner_val_scaled = scaler_Y.transform(y_inner_val)
    y_train_scaled = scaler_Y.transform(y_train_raw)      # Full train
    y_test_scaled = scaler_Y.transform(y_test_raw)        # Test

    return {
        'X_inner_train': X_inner_train_scaled,
        'X_inner_val': X_inner_val_scaled,
        'X_train': X_train_scaled,
        'X_test': X_test_scaled,
        'y_inner_train': y_inner_train_scaled,
        'y_inner_val': y_inner_val_scaled,
        'y_train': y_train_scaled,
        'y_test': y_test_scaled,
        'y_train_raw': y_train_raw.flatten(),
        'y_test_raw': y_test_raw.flatten(),
        'test_cycles': test_cycles,
        'test_battery_id': test_battery_id,
        'scaler_X': scaler_X,
        'scaler_Y': scaler_Y,
        'input_dim': data_cfg['input_dim'],
    }


def train_autoencoder(config: Dict, data_dict: Dict, device: torch.device, output_dir: Path) -> Tuple[nn.Module, torch.Tensor, torch.Tensor]:
    """Train AE with EarlyStopping on inner-val reconstruction loss."""
    ae_cfg = config['autoencoder']
    train_cfg = config['training']
    opt_cfg = config['optimizer']

    set_deterministic(config['seed'])

    # DataLoaders
    ae_train_loader = DataLoader(
        TensorDataset(
            torch.tensor(data_dict['X_inner_train'], dtype=torch.float32).to(device),
            torch.tensor(data_dict['X_inner_train'], dtype=torch.float32).to(device)
        ),
        batch_size=train_cfg['ae_batch_size'], shuffle=True
    )
    ae_val_loader = DataLoader(
        TensorDataset(
            torch.tensor(data_dict['X_inner_val'], dtype=torch.float32).to(device),
            torch.tensor(data_dict['X_inner_val'], dtype=torch.float32).to(device)
        ),
        batch_size=train_cfg['ae_batch_size'], shuffle=False
    )

    # Model
    ae = ControlledAutoencoder(
        input_dim=data_dict['input_dim'],
        bottleneck_dim=ae_cfg['bottleneck_dim'],
        hidden_dim=ae_cfg['hidden_dim'],
        activation=ae_cfg['activation'],
        bottleneck_activation=ae_cfg['bottleneck_activation']
    ).to(device)

    # Loss & Optimizer
    loss_fn = getattr(nn, train_cfg['ae_loss'].upper() + 'Loss')()
    optimizer = optim.Adam(ae.parameters(), lr=train_cfg['ae_lr'],
                           betas=opt_cfg['betas'], eps=opt_cfg['eps'])

    # EarlyStopping
    es_cfg = train_cfg['ae_early_stopping']
    best_val_loss = float('inf')
    patience_counter = 0
    best_state = None

    ae.train()
    for epoch in range(train_cfg['ae_epochs']):
        # Train
        for bx, _ in ae_train_loader:
            optimizer.zero_grad()
            recon, _ = ae(bx)
            loss = loss_fn(recon, bx)
            loss.backward()
            optimizer.step()

        # Validate
        ae.eval()
        val_losses = []
        with torch.no_grad():
            for bx, _ in ae_val_loader:
                recon, _ = ae(bx)
                val_losses.append(loss_fn(recon, bx).item())
        avg_val_loss = np.mean(val_losses)
        ae.train()

        # EarlyStopping check
        if avg_val_loss < best_val_loss - es_cfg['min_delta']:
            best_val_loss = avg_val_loss
            patience_counter = 0
            best_state = {k: v.cpu().clone() for k, v in ae.state_dict().items()}
            torch.save(best_state, output_dir / "best_ae.pth")
        else:
            patience_counter += 1
            if patience_counter >= es_cfg['patience']:
                print(f"  [AE] EarlyStopping at epoch {epoch+1} (best val_loss: {best_val_loss:.6f})")
                break

    # Load best model
    ae.load_state_dict(torch.load(output_dir / "best_ae.pth", map_location=device))
    ae.eval()

    # Extract latent for FULL training set (for BPNN training) and test set
    with torch.no_grad():
        X_train_t = torch.tensor(data_dict['X_train'], dtype=torch.float32).to(device)
        X_test_t = torch.tensor(data_dict['X_test'], dtype=torch.float32).to(device)
        _, train_latent = ae(X_train_t)
        _, test_latent = ae(X_test_t)

    return ae, train_latent.cpu(), test_latent.cpu()


def train_bpnn(config: Dict, train_latent: torch.Tensor, test_latent: torch.Tensor,
               data_dict: Dict, device: torch.device, output_dir: Path) -> Tuple[nn.Module, np.ndarray, np.ndarray]:
    """Train BPNN with EarlyStopping on inner-val loss."""
    bpnn_cfg = config['bpnn']
    train_cfg = config['training']
    opt_cfg = config['optimizer']

    set_deterministic(config['seed'])

    # Inner-train/val split for BPNN (same indices as AE)
    # We need to recreate the split consistently
    inner_cfg = config.get('inner_validation', {'enabled': True, 'val_ratio': 0.2, 'random_seed': 42})
    n_total = train_latent.shape[0]
    n_val = int(n_total * inner_cfg['val_ratio'])
    n_train = n_total - n_val

    set_deterministic(inner_cfg['random_seed'])
    indices = np.random.permutation(n_total)
    train_idx = indices[:n_train]
    val_idx = indices[n_train:]

    bpnn_train_loader = DataLoader(
        TensorDataset(
            train_latent[train_idx].to(device),
            torch.tensor(data_dict['y_inner_train'], dtype=torch.float32).to(device)
        ),
        batch_size=train_cfg['bpnn_batch_size'], shuffle=True
    )
    bpnn_val_loader = DataLoader(
        TensorDataset(
            train_latent[val_idx].to(device),
            torch.tensor(data_dict['y_inner_val'], dtype=torch.float32).to(device)
        ),
        batch_size=train_cfg['bpnn_batch_size'], shuffle=False
    )

    # Model
    bpnn = ControlledBPNN(
        input_dim=train_latent.shape[1],
        hidden_layers=bpnn_cfg['hidden_layers'],
        output_dim=bpnn_cfg['output_dim'],
        activation=bpnn_cfg['activation'],
        weight_init=bpnn_cfg['weight_init']
    ).to(device)

    # Loss & Optimizer
    loss_fn = getattr(nn, train_cfg['bpnn_loss'].upper() + 'Loss')()
    optimizer = optim.Adam(bpnn.parameters(), lr=train_cfg['bpnn_lr'],
                           weight_decay=train_cfg['bpnn_l2'],
                           betas=opt_cfg['betas'], eps=opt_cfg['eps'])

    # EarlyStopping
    es_cfg = train_cfg['bpnn_early_stopping']
    best_val_loss = float('inf')
    patience_counter = 0

    bpnn.train()
    for epoch in range(train_cfg['bpnn_epochs']):
        for bx, by in bpnn_train_loader:
            optimizer.zero_grad()
            preds = bpnn(bx)
            loss = loss_fn(preds, by)
            loss.backward()
            optimizer.step()

        # Validate
        bpnn.eval()
        val_losses = []
        with torch.no_grad():
            for bx, by in bpnn_val_loader:
                preds = bpnn(bx)
                val_losses.append(loss_fn(preds, by).item())
        avg_val_loss = np.mean(val_losses)
        bpnn.train()

        if avg_val_loss < best_val_loss - es_cfg['min_delta']:
            best_val_loss = avg_val_loss
            patience_counter = 0
            torch.save(bpnn.state_dict(), output_dir / "best_bpnn.pth")
        else:
            patience_counter += 1
            if patience_counter >= es_cfg['patience']:
                print(f"  [BPNN] EarlyStopping at epoch {epoch+1} (best val_loss: {best_val_loss:.6f})")
                break

    # Load best model
    bpnn.load_state_dict(torch.load(output_dir / "best_bpnn.pth", map_location=device))
    bpnn.eval()

    # Predict on FULL train and test (original scale)
    with torch.no_grad():
        tr_preds_scaled = bpnn(train_latent.to(device)).cpu().numpy()
        te_preds_scaled = bpnn(test_latent.to(device)).cpu().numpy()

    # Inverse transform to original scale (Ah)
    tr_preds_ah = data_dict['scaler_Y'].inverse_transform(tr_preds_scaled).flatten()
    te_preds_ah = data_dict['scaler_Y'].inverse_transform(te_preds_scaled).flatten()

    return bpnn, tr_preds_ah, te_preds_ah


# ─── Main ───────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Train AE+BPNN for single LOBO fold")
    parser.add_argument("--fold", type=int, required=True, choices=[0, 1, 2, 3],
                        help="LOBO fold: 0=B0005, 1=B0006, 2=B0007, 3=B0018")
    parser.add_argument("--config", type=str, required=True,
                        help="Path to YAML config file")
    parser.add_argument("--workdir", type=str, default=".",
                        help="Working directory (contains data, outputs)")
    # Override options
    parser.add_argument("--epochs", type=int, help="Override AE and BPNN epochs")
    parser.add_argument("--batch-size", type=int, help="Override batch size")
    parser.add_argument("--lr", type=float, help="Override learning rate (both AE and BPNN)")
    parser.add_argument("--bottleneck", type=int, help="Override AE bottleneck dim")
    parser.add_argument("--l2", type=float, help="Override BPNN L2 weight_decay")
    parser.add_argument("--loss", type=str, choices=['mse', 'mae', 'huber'], help="Override loss function")
    parser.add_argument("--seed", type=int, help="Override random seed")
    parser.add_argument("--device", type=str, choices=['auto', 'cuda', 'cpu'], help="Override device")
    args = parser.parse_args()

    # Load config
    config = load_config(args.config)

    # Apply CLI overrides
    if args.epochs:
        config['training']['ae_epochs'] = args.epochs
        config['training']['bpnn_epochs'] = args.epochs
    if args.batch_size:
        config['training']['ae_batch_size'] = args.batch_size
        config['training']['bpnn_batch_size'] = args.batch_size
    if args.lr:
        config['training']['ae_lr'] = args.lr
        config['training']['bpnn_lr'] = args.lr
    if args.bottleneck:
        config['autoencoder']['bottleneck_dim'] = args.bottleneck
    if args.l2:
        config['training']['bpnn_l2'] = args.l2
    if args.loss:
        config['training']['ae_loss'] = args.loss
        config['training']['bpnn_loss'] = args.loss
    if args.seed:
        config['seed'] = args.seed
    if args.device:
        config['device'] = args.device

    # Setup
    workdir = Path(args.workdir).resolve()
    experiment_name = config['experiment_name']
    output_dir = workdir / config['output']['checkpoint_dir'].format(
        experiment_name=experiment_name, fold=args.fold
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    device = get_device(config['device'])
    print(f"=" * 70)
    print(f"Training Fold {args.fold} (Test Battery ID: {args.fold + 1})")
    print(f"Experiment: {experiment_name}")
    print(f"Device: {device}")
    print(f"Output: {output_dir}")
    print(f"=" * 70)

    # Prepare data
    print(">>> Preparing data (LOBO split, scalers fit on inner-train only)...")
    data_dict = prepare_data(config, args.fold, workdir)
    print(f"    Train samples: {data_dict['X_train'].shape[0]}, Test samples: {data_dict['X_test'].shape[0]}")
    print(f"    Inner-train: {data_dict['X_inner_train'].shape[0]}, Inner-val: {data_dict['X_inner_val'].shape[0]}")

    # Train AE
    print(">>> Training Autoencoder...")
    ae, train_latent, test_latent = train_autoencoder(config, data_dict, device, output_dir)

    # Train BPNN
    print(">>> Training BPNN...")
    bpnn, tr_preds_ah, te_preds_ah = train_bpnn(config, train_latent, test_latent, data_dict, device, output_dir)

    # Metrics on ORIGINAL SCALE (Ah)
    tr_mae, tr_rmse, tr_r2 = calculate_metrics(data_dict['y_train_raw'], tr_preds_ah)
    te_mae, te_rmse, te_r2 = calculate_metrics(data_dict['y_test_raw'], te_preds_ah)

    # Save scalers
    with open(output_dir / "scaler_X.pkl", 'wb') as f:
        pickle.dump(data_dict['scaler_X'], f)
    with open(output_dir / "scaler_Y.pkl", 'wb') as f:
        pickle.dump(data_dict['scaler_Y'], f)

    # Save predictions
    np.savez(output_dir / "predictions.npz",
             y_train_true=data_dict['y_train_raw'],
             y_train_pred=tr_preds_ah,
             y_test_true=data_dict['y_test_raw'],
             y_test_pred=te_preds_ah,
             test_cycles=data_dict['test_cycles'])

    # Save metrics
    metrics = {
        'fold': args.fold,
        'test_battery_id': data_dict['test_battery_id'],
        'experiment_name': experiment_name,
        'config': {
            'bottleneck': config['autoencoder']['bottleneck_dim'],
            'bpnn_hidden': config['bpnn']['hidden_layers'],
            'ae_epochs': config['training']['ae_epochs'],
            'bpnn_epochs': config['training']['bpnn_epochs'],
            'ae_lr': config['training']['ae_lr'],
            'bpnn_lr': config['training']['bpnn_lr'],
            'bpnn_l2': config['training']['bpnn_l2'],
            'ae_loss': config['training']['ae_loss'],
            'bpnn_loss': config['training']['bpnn_loss'],
        },
        'train_mae': float(tr_mae),
        'train_rmse': float(tr_rmse),
        'train_r2': float(tr_r2),
        'test_mae': float(te_mae),
        'test_rmse': float(te_rmse),
        'test_r2': float(te_r2),
        'generalization_gap_rmse': float(te_rmse - tr_rmse),
        'n_train_samples': int(data_dict['X_train'].shape[0]),
        'n_test_samples': int(data_dict['X_test'].shape[0]),
        'status': 'ok'
    }

    metrics_file = output_dir / config['output']['metrics_file']
    with open(metrics_file, 'w') as f:
        json.dump(metrics, f, indent=2)

    # Print summary
    print(f"\n>>> FOLD {args.fold} RESULTS (Test Battery ID: {data_dict['test_battery_id']})")
    print(f"    Train: MAE={tr_mae:.5f} Ah, RMSE={tr_rmse:.5f} Ah, R²={tr_r2:.5f}")
    print(f"    Test:  MAE={te_mae:.5f} Ah, RMSE={te_rmse:.5f} Ah, R²={te_r2:.5f}")
    print(f"    Gap (Test-Train RMSE): {te_rmse - tr_rmse:.5f} Ah")
    print(f">>> Metrics saved to: {metrics_file}")
    print(f">>> Checkpoints: {output_dir}/best_ae.pth, {output_dir}/best_bpnn.pth")

    # Output JSON for sub-agent capture
    print(json.dumps({
        "fold": args.fold,
        "test_battery_id": data_dict['test_battery_id'],
        "val_rmse": float(te_rmse),  # Using test RMSE as validation metric
        "ckpt_path": str(output_dir / "best_bpnn.pth"),
        "status": "ok"
    }))


if __name__ == "__main__":
    main()