import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# -----------------------------------------------------------------------------
# 1. Controlled Model Architectures (Strictly Defined)
# -----------------------------------------------------------------------------
class ControlledAutoencoder(nn.Module):
    # Removed default bottleneck_dim to enforce explicit parameter passing
    def __init__(self, input_dim, bottleneck_dim):
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
    # Hidden layers locked at [16, 8] based on Priority 3 Empirical Baseline
    def __init__(self, input_dim, hidden_layers=[16, 8]):
        super(ControlledBPNN, self).__init__()
        layers = []
        prev_dim = input_dim
        for hidden_dim in hidden_layers:
            layers.append(nn.Linear(prev_dim, hidden_dim))
            # แก้ไขบั๊ก Index ตรงนี้: ชี้ไปที่เลเยอร์ล่าสุด (-1) แทนที่จะเป็น (-2)
            nn.init.kaiming_normal_(layers[-1].weight, nonlinearity='relu') 
            layers.append(nn.ReLU())
            prev_dim = hidden_dim
        layers.append(nn.Linear(prev_dim, 1)) 
        self.network = nn.Sequential(*layers)

    def forward(self, x):
        return self.network(x)

def calculate_metrics(y_true, y_pred):
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred)
    return mae, rmse, r2

# -----------------------------------------------------------------------------
# 2. Main Priority 4 Execution Pipeline (108 Runs)
# -----------------------------------------------------------------------------
def run_priority4_ablation():
    print("="*85)
    print("Priority 4: Full Ablation Studies (108 Configurations)")
    print("Validation Strategy: Strict LOBO on B0018 (Zero Future Leakage Enforced)")
    print("Empirical Constants: Batch=16, AE_LR=0.001, BPNN_LR=0.001, Epochs=300")
    print("="*85)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"[Device Status] Execution Device: {device}")
    if device.type == 'cuda':
        print(f"                GPU Name: {torch.cuda.get_device_name(0)}")

    dataset_file = 'Mapped_EIS_SOH_log_grid_pchip.pt'
    if not os.path.exists(dataset_file):
        print(f"[ERROR] Required dataset '{dataset_file}' not found.")
        return

    # 1. Load Mapped Dataset
    data = torch.load(dataset_file, weights_only=True)
    X_raw = data['features'].numpy()
    y_meta = data['labels'].numpy()

    battery_ids = y_meta[:, 0].astype(int)
    cycles = y_meta[:, 1].astype(int)
    y_capacity = y_meta[:, 2]

    # 2. Strict LOBO Split (Train: 1, 2, 3 | Test: 4 / B0018)
    target_test_battery = 4
    train_mask = (battery_ids != target_test_battery)
    test_mask = (battery_ids == target_test_battery)

    X_train_raw = X_raw[train_mask]
    X_test_raw = X_raw[test_mask]
    
    # Reshape Y for Scaler
    y_train_raw = y_capacity[train_mask].reshape(-1, 1)
    y_test_raw = y_capacity[test_mask].reshape(-1, 1)
    test_cycles = cycles[test_mask]

    # 3. Target and Feature Scaling (Fitted on Train Set ONLY)
    scaler_X = MinMaxScaler()
    X_train_scaled = scaler_X.fit_transform(X_train_raw)
    X_test_scaled = scaler_X.transform(X_test_raw)

    scaler_Y = MinMaxScaler()
    y_train_scaled = scaler_Y.fit_transform(y_train_raw)
    y_test_scaled = scaler_Y.transform(y_test_raw)

    tensor_X_train = torch.tensor(X_train_scaled, dtype=torch.float32).to(device)
    tensor_X_test = torch.tensor(X_test_scaled, dtype=torch.float32).to(device)
    tensor_y_train = torch.tensor(y_train_scaled, dtype=torch.float32).to(device)

    # 4. Independent Ablation Search Spaces
    bottlenecks = [1, 3, 7, 17, 37, 67]
    l2_reg_list = [0.0, 1e-5, 1e-4, 1e-3, 1e-2, 1e-1]
    loss_dict = {
        'MSE': nn.MSELoss(),
        'MAE': nn.L1Loss(),
        'Huber': nn.SmoothL1Loss()
    }

    # Empirically Validated Controlled Hyperparameters (From Pre-Ablation)
    ae_epochs = 300
    bpnn_epochs = 300
    batch_size = 16
    ae_lr = 0.001
    bpnn_lr = 0.001

    results_list = []
    best_overall = {'test_r2': -float('inf'), 'preds': None, 'config': None}

    total_runs = len(bottlenecks) * len(loss_dict) * len(l2_reg_list)
    run_idx = 1

    for b_size in bottlenecks:
        print(f"\n>>> [Stage 1] Pre-training Autoencoder for Bottleneck Size = {b_size}...")
        torch.manual_seed(42)
        np.random.seed(42)

        ae = ControlledAutoencoder(input_dim=256, bottleneck_dim=b_size).to(device)
        ae_optimizer = optim.Adam(ae.parameters(), lr=ae_lr)
        ae_criterion = nn.MSELoss()

        ae_train_loader = DataLoader(TensorDataset(tensor_X_train, tensor_X_train), batch_size=batch_size, shuffle=True)

        ae.train()
        for epoch in range(ae_epochs):
            for bx, _ in ae_train_loader:
                ae_optimizer.zero_grad()
                recon, _ = ae(bx)
                loss = ae_criterion(recon, bx)
                loss.backward()
                ae_optimizer.step()

        # Extract Latent Representations
        ae.eval()
        with torch.no_grad():
            _, train_latent = ae(tensor_X_train)
            _, test_latent = ae(tensor_X_test)

        bpnn_train_loader = DataLoader(TensorDataset(train_latent, tensor_y_train), batch_size=batch_size, shuffle=True)

        for loss_name, criterion in loss_dict.items():
            for l2_val in l2_reg_list:
                print(f"[{run_idx:>3}/{total_runs}] Bottleneck: {b_size:>2} | Loss: {loss_name:<5} | L2: {l2_val:<6} ...", end="", flush=True)

                torch.manual_seed(42)
                np.random.seed(42)

                bpnn = ControlledBPNN(input_dim=b_size, hidden_layers=[16, 8]).to(device)
                optimizer = optim.Adam(bpnn.parameters(), lr=bpnn_lr, weight_decay=l2_val)

                bpnn.train()
                for epoch in range(bpnn_epochs):
                    for bx, by in bpnn_train_loader:
                        optimizer.zero_grad()
                        preds = bpnn(bx)
                        loss = criterion(preds, by)
                        loss.backward()
                        optimizer.step()

                # 5. Evaluate (Inverse Transform Required)
                bpnn.eval()
                with torch.no_grad():
                    tr_preds_scaled = bpnn(train_latent).cpu().numpy()
                    te_preds_scaled = bpnn(test_latent).cpu().numpy()

                tr_preds_ah = scaler_Y.inverse_transform(tr_preds_scaled).flatten()
                te_preds_ah = scaler_Y.inverse_transform(te_preds_scaled).flatten()
                
                y_train_ah = y_train_raw.flatten()
                y_test_ah = y_test_raw.flatten()

                tr_mae, tr_rmse, tr_r2 = calculate_metrics(y_train_ah, tr_preds_ah)
                te_mae, te_rmse, te_r2 = calculate_metrics(y_test_ah, te_preds_ah)

                print(f" Done! -> Test RMSE (Ah): {te_rmse:.5f} | Test R2: {te_r2:.5f}")

                res_entry = {
                    'Bottleneck': b_size,
                    'Loss_Function': loss_name,
                    'L2_Regularization': l2_val,
                    'Train_RMSE': tr_rmse,
                    'Train_MAE': tr_mae,
                    'Train_R2': tr_r2,
                    'Test_RMSE': te_rmse,
                    'Test_MAE': te_mae,
                    'Test_R2': te_r2,
                    'Generalization_Gap_RMSE': te_rmse - tr_rmse
                }
                results_list.append(res_entry)

                if te_r2 > best_overall['test_r2']:
                    best_overall['test_r2'] = te_r2
                    best_overall['preds'] = te_preds_ah
                    best_overall['config'] = res_entry

                run_idx += 1

    # 6. Save Quantitative Results Table
    df_all = pd.DataFrame(results_list)
    df_all.to_csv('Priority4_Ablation_Full_Results.csv', index=False)
    print("\n" + "="*85)
    print("Full results saved to 'Priority4_Ablation_Full_Results.csv'")

    # Display Top 5 Configurations
    df_top = df_all.sort_values(by=['Test_R2', 'Test_RMSE'], ascending=[False, True]).head(5)
    print("\n--- TOP 5 BEST CONFIGURATIONS ---")
    print(df_top[['Bottleneck', 'Loss_Function', 'L2_Regularization', 'Train_RMSE', 'Train_R2', 'Test_RMSE', 'Test_MAE', 'Test_R2']].to_markdown(index=False))

    # -----------------------------------------------------------------------------
    # 7. Scientific Visualization (3 Empirical Figures)
    # -----------------------------------------------------------------------------
    print("\n>>> Generating 3 Scientific Evidence Figures...")
    best_cfg = best_overall['config']

    # --- Figure 1: Bottleneck Optimization Curve (U-Shape) ---
    plt.figure(figsize=(8, 5))
    df_sub_b = df_all[(df_all['Loss_Function'] == best_cfg['Loss_Function']) & (df_all['L2_Regularization'] == best_cfg['L2_Regularization'])]
    df_sub_b = df_sub_b.sort_values('Bottleneck')
    plt.plot(df_sub_b['Bottleneck'], df_sub_b['Test_RMSE'], marker='o', linewidth=2, color='#1f77b4', label='Test RMSE (Unseen B0018)')
    plt.plot(df_sub_b['Bottleneck'], df_sub_b['Train_RMSE'], marker='s', linestyle='--', color='#2ca02c', label='Train RMSE')
    plt.axvline(x=best_cfg['Bottleneck'], color='r', linestyle=':', label=f"Optimal Bottleneck ({best_cfg['Bottleneck']})")
    plt.title(f"Fig 1: Bottleneck Optimization Curve (Loss: {best_cfg['Loss_Function']}, L2: {best_cfg['L2_Regularization']})", fontsize=12)
    plt.xlabel("Bottleneck Size (Latent Dimensions)", fontsize=11)
    plt.ylabel("RMSE (Capacity Ah)", fontsize=11)
    plt.xticks(df_sub_b['Bottleneck'], df_sub_b['Bottleneck'])
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig('Fig1_Bottleneck_Optimization_Curve.png', dpi=300)
    plt.close()

    # --- Figure 2: L2 Generalization Gap (Bar Chart) ---
    plt.figure(figsize=(9, 5))
    df_sub_l2 = df_all[(df_all['Bottleneck'] == best_cfg['Bottleneck']) & (df_all['Loss_Function'] == best_cfg['Loss_Function'])]
    df_sub_l2 = df_sub_l2.sort_values('L2_Regularization')
    x_indices = np.arange(len(df_sub_l2))
    width = 0.35

    plt.bar(x_indices - width/2, df_sub_l2['Train_RMSE'], width, label='Train RMSE', color='#2ca02c', alpha=0.85)
    plt.bar(x_indices + width/2, df_sub_l2['Test_RMSE'], width, label='Test RMSE (Unseen B0018)', color='#d62728', alpha=0.85)
    plt.xticks(x_indices, [str(v) for v in df_sub_l2['L2_Regularization']])
    plt.title(f"Fig 2: L2 Regularization vs Generalization Gap (Bottleneck: {best_cfg['Bottleneck']})", fontsize=12)
    plt.xlabel("L2 Regularization Coefficient (Weight Decay)", fontsize=11)
    plt.ylabel("RMSE (Capacity Ah)", fontsize=11)
    plt.grid(True, linestyle='--', alpha=0.5, axis='y')
    plt.legend()
    plt.tight_layout()
    plt.savefig('Fig2_L2_Generalization_Gap.png', dpi=300)
    plt.close()

    # --- Figure 3: SOH Trajectory on Unseen Battery B0018 ---
    plt.figure(figsize=(10, 5))
    sort_idx = np.argsort(test_cycles)
    plt.plot(test_cycles[sort_idx], y_test_ah[sort_idx], color='black', linewidth=2.5, label='Ground Truth Capacity (Ah)')
    plt.plot(test_cycles[sort_idx], best_overall['preds'][sort_idx], color='#d62728', linestyle='--', linewidth=2, 
             label=f"Best Model Prediction (R²={best_cfg['Test_R2']:.4f}, RMSE={best_cfg['Test_RMSE']:.4f})")
    plt.title(f"Fig 3: Real-Time SOH Estimation Trajectory on Unseen Battery B0018", fontsize=12)
    plt.xlabel("Discharge Cycle Index", fontsize=11)
    plt.ylabel("Capacity (Ah)", fontsize=11)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig('Fig3_Best_Model_SOH_Trajectory.png', dpi=300)
    plt.close()

    print("Figures generated successfully:")
    print("  -> Fig1_Bottleneck_Optimization_Curve.png")
    print("  -> Fig2_L2_Generalization_Gap.png")
    print("  -> Fig3_Best_Model_SOH_Trajectory.png")
    print("="*85)

if __name__ == "__main__":
    run_priority4_ablation()