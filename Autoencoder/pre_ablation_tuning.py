import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, r2_score

# -----------------------------------------------------------------------------
# 1. Controlled Model Architectures (Standardized for Pre-Tuning)
# -----------------------------------------------------------------------------
class ControlledAutoencoder(nn.Module):
    def __init__(self, input_dim=256, bottleneck_dim=17):
        super(ControlledAutoencoder, self).__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Linear(128, bottleneck_dim)
        )
        self.decoder = nn.Sequential(
            nn.Linear(bottleneck_dim, 128),
            nn.ReLU(),
            nn.Linear(128, input_dim)
        )

    def forward(self, x):
        latent = self.encoder(x)
        reconstructed = self.decoder(latent)
        return reconstructed, latent

class ControlledBPNN(nn.Module):
    def __init__(self, input_dim=17, hidden_layers=[16, 8]):
        super(ControlledBPNN, self).__init__()
        layers = []
        prev_dim = input_dim
        for hidden_dim in hidden_layers:
            layers.append(nn.Linear(prev_dim, hidden_dim))
            layers.append(nn.ReLU())
            prev_dim = hidden_dim
        layers.append(nn.Linear(prev_dim, 1))
        self.network = nn.Sequential(*layers)

    def forward(self, x):
        return self.network(x)

# -----------------------------------------------------------------------------
# 2. Main Pre-Ablation Tuning Pipeline
# -----------------------------------------------------------------------------
def run_pre_ablation_tuning():
    print("="*85)
    print("PRE-ABLATION TUNING: Finding Empirical Evidence for Controlled Variables")
    print("Rule 4 Enforced: B0005+06 (Train), B0007 (Val for Selection), B0018 (Frozen Test)")
    print("="*85)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"[Device Status] Execution Device: {device}")

    dataset_file = 'Mapped_EIS_SOH_log_grid_pchip.pt'
    if not os.path.exists(dataset_file):
        print(f"[ERROR] Required dataset '{dataset_file}' not found.")
        return

    data = torch.load(dataset_file, weights_only=True)
    X_raw = data['features'].numpy()
    y_meta = data['labels'].numpy()

    battery_ids = y_meta[:, 0].astype(int)
    y_capacity = y_meta[:, 2]

    # --- Strict Data Split ---
    train_mask = np.isin(battery_ids, [1, 2]) # B0005, B0006
    val_mask = (battery_ids == 3)             # B0007 (Used for Decision)
    test_mask = (battery_ids == 4)            # B0018 (Frozen Test)

    X_train_raw, y_train_raw = X_raw[train_mask], y_capacity[train_mask].reshape(-1, 1)
    X_val_raw, y_val_raw = X_raw[val_mask], y_capacity[val_mask].reshape(-1, 1)
    X_test_raw, y_test_raw = X_raw[test_mask], y_capacity[test_mask].reshape(-1, 1)

    # --- Zero-Leakage Scaling (Fit on Train ONLY) ---
    scaler_X = MinMaxScaler()
    X_train_scaled = scaler_X.fit_transform(X_train_raw)
    X_val_scaled = scaler_X.transform(X_val_raw)
    X_test_scaled = scaler_X.transform(X_test_raw)

    scaler_Y = MinMaxScaler()
    y_train_scaled = scaler_Y.fit_transform(y_train_raw)
    y_val_scaled = scaler_Y.transform(y_val_raw)
    y_test_scaled = scaler_Y.transform(y_test_raw)

    t_X_train = torch.tensor(X_train_scaled, dtype=torch.float32).to(device)
    t_X_val = torch.tensor(X_val_scaled, dtype=torch.float32).to(device)
    t_X_test = torch.tensor(X_test_scaled, dtype=torch.float32).to(device)
    t_y_train = torch.tensor(y_train_scaled, dtype=torch.float32).to(device)
    t_y_val = torch.tensor(y_val_scaled, dtype=torch.float32).to(device)

    # --- Grid Search Space ---
    batch_sizes = [16, 32]
    ae_lrs = [1e-3, 5e-4]
    bpnn_lrs = [5e-3, 1e-3]
    max_epochs = 500
    
    results = []
    best_val_rmse = float('inf')
    best_config = None
    best_learning_curve = None

    total_runs = len(batch_sizes) * len(ae_lrs) * len(bpnn_lrs)
    run_idx = 1

    print("\n>>> Starting Grid Search (Decision strictly based on B0007 Validation RMSE)")
    
    for bz in batch_sizes:
        for ae_lr in ae_lrs:
            for bpnn_lr in bpnn_lrs:
                print(f"[{run_idx}/{total_runs}] Batch: {bz:2} | AE_LR: {ae_lr} | BPNN_LR: {bpnn_lr} ...", end="", flush=True)
                
                torch.manual_seed(42)
                np.random.seed(42)

                # 1. Train AE
                ae = ControlledAutoencoder(input_dim=256, bottleneck_dim=17).to(device)
                opt_ae = optim.Adam(ae.parameters(), lr=ae_lr)
                crit_ae = nn.MSELoss()
                ae_loader = DataLoader(TensorDataset(t_X_train, t_X_train), batch_size=bz, shuffle=True)

                for epoch in range(max_epochs):
                    ae.train()
                    for bx, _ in ae_loader:
                        opt_ae.zero_grad()
                        recon, _ = ae(bx)
                        loss = crit_ae(recon, bx)
                        loss.backward()
                        opt_ae.step()

                ae.eval()
                with torch.no_grad():
                    _, latent_train = ae(t_X_train)
                    _, latent_val = ae(t_X_val)
                    _, latent_test = ae(t_X_test)

                # 2. Train BPNN & Track Learning Curve
                bpnn = ControlledBPNN(input_dim=17).to(device)
                opt_bpnn = optim.Adam(bpnn.parameters(), lr=bpnn_lr, weight_decay=0.0) # Baseline (No L2 yet)
                crit_bpnn = nn.MSELoss()
                bpnn_loader = DataLoader(TensorDataset(latent_train, t_y_train), batch_size=bz, shuffle=True)

                train_history = []
                val_history = []

                for epoch in range(max_epochs):
                    bpnn.train()
                    for bx, by in bpnn_loader:
                        opt_bpnn.zero_grad()
                        preds = bpnn(bx)
                        loss = crit_bpnn(preds, by)
                        loss.backward()
                        opt_bpnn.step()
                    
                    bpnn.eval()
                    with torch.no_grad():
                        tr_pred = bpnn(latent_train)
                        va_pred = bpnn(latent_val)
                        tr_loss = crit_bpnn(tr_pred, t_y_train).item()
                        va_loss = crit_bpnn(va_pred, t_y_val).item()
                        train_history.append(tr_loss)
                        val_history.append(va_loss)

                # 3. Evaluate (Inverse Transform)
                bpnn.eval()
                with torch.no_grad():
                    val_preds_scaled = bpnn(latent_val).cpu().numpy()
                    test_preds_scaled = bpnn(latent_test).cpu().numpy()

                val_preds_ah = scaler_Y.inverse_transform(val_preds_scaled).flatten()
                test_preds_ah = scaler_Y.inverse_transform(test_preds_scaled).flatten()
                
                y_val_ah = y_val_raw.flatten()
                y_test_ah = y_test_raw.flatten()

                val_rmse = np.sqrt(mean_squared_error(y_val_ah, val_preds_ah))
                test_rmse = np.sqrt(mean_squared_error(y_test_ah, test_preds_ah))
                test_r2 = r2_score(y_test_ah, test_preds_ah)

                print(f" Done! Val RMSE (B0007): {val_rmse:.4f} | Test RMSE (B0018): {test_rmse:.4f}")

                results.append({
                    'Batch_Size': bz,
                    'AE_LR': ae_lr,
                    'BPNN_LR': bpnn_lr,
                    'Val_RMSE': val_rmse,
                    'Test_RMSE': test_rmse,
                    'Test_R2': test_r2
                })

                # Selection strictly based on Validation (B0007)
                if val_rmse < best_val_rmse:
                    best_val_rmse = val_rmse
                    best_config = results[-1]
                    best_learning_curve = (train_history, val_history)

                run_idx += 1

    # --- Save Evidence ---
    df_res = pd.DataFrame(results)
    df_res = df_res.sort_values(by='Val_RMSE')
    print("\n--- PRE-ABLATION HYPERPARAMETER RANKING (Sorted by Validation RMSE) ---")
    print(df_res.to_markdown(index=False))
    df_res.to_csv('PreAblation_Hyperparam_Matrix.csv', index=False)

    # --- Plot Learning Curve Evidence ---
    plt.figure(figsize=(10, 5))
    plt.plot(best_learning_curve[0], label='Train Loss (B0005, B0006)', color='#1f77b4', linewidth=2)
    plt.plot(best_learning_curve[1], label='Validation Loss (B0007)', color='#ff7f0e', linewidth=2, linestyle='--')
    plt.title(f"Empirical Convergence Evidence (Batch: {best_config['Batch_Size']}, AE_LR: {best_config['AE_LR']}, BPNN_LR: {best_config['BPNN_LR']})")
    plt.xlabel("Epochs")
    plt.ylabel("MSE Loss (Scaled)")
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig('Fig_PreAblation_LearningCurve.png', dpi=300)
    plt.close()

    print("\nEvidence Generated:")
    print("1. Table: PreAblation_Hyperparam_Matrix.csv")
    print("2. Graph: Fig_PreAblation_LearningCurve.png (Check this image to find the exact epoch where Validation Loss plateaus)")
    print("="*85)

if __name__ == "__main__":
    run_pre_ablation_tuning()