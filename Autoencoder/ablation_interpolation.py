import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
import pandas as pd
import os
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# -----------------------------------------------------------------------------
# 1. Controlled Model Architectures
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
# 2. Main Interpolation Ablation
# -----------------------------------------------------------------------------
def run_interpolation_ablation():
    print("="*85)
    print("Interpolation & Grid Ablation Study")
    print("Goal: Evaluate whether interpolation choice affects SOH prediction performance.")
    print("Controlled Vars: Bottleneck=17, BPNN=[16,8], Epochs=300, Batch=16, LRs=0.001")
    print("="*85)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    grid_types = ['linear_grid', 'log_grid']
    methods = ['linear', 'cubic', 'pchip']
    
    results_list = []
    
    # Controlled Constants
    b_size = 17
    batch_size = 16
    ae_epochs = 300
    bpnn_epochs = 300
    ae_lr = 0.001
    bpnn_lr = 0.001

    for g_name in grid_types:
        for m_name in methods:
            dataset_file = f'Mapped_EIS_SOH_{g_name}_{m_name}.pt'
            print(f"\n>>> Evaluating: Grid = {g_name.upper()} | Method = {m_name.upper()}")
            
            if not os.path.exists(dataset_file):
                print(f"[WARNING] File {dataset_file} not found. Skipping...")
                continue
                
            # 1. Load Data
            data = torch.load(dataset_file, weights_only=True)
            X_raw = data['features'].numpy()
            y_meta = data['labels'].numpy()

            battery_ids = y_meta[:, 0].astype(int)
            y_capacity = y_meta[:, 2]

            # 2. Strict LOBO Split (Test: 4 / B0018)
            test_battery = 4
            train_mask = (battery_ids != test_battery)
            test_mask = (battery_ids == test_battery)

            X_train_raw = X_raw[train_mask]
            X_test_raw = X_raw[test_mask]
            y_train_raw = y_capacity[train_mask].reshape(-1, 1)
            y_test_raw = y_capacity[test_mask].reshape(-1, 1)

            # 3. Zero-Leakage Scaling
            scaler_X = MinMaxScaler()
            X_train_scaled = scaler_X.fit_transform(X_train_raw)
            X_test_scaled = scaler_X.transform(X_test_raw)

            scaler_Y = MinMaxScaler()
            y_train_scaled = scaler_Y.fit_transform(y_train_raw)
            y_test_scaled = scaler_Y.transform(y_test_raw)

            t_X_train = torch.tensor(X_train_scaled, dtype=torch.float32).to(device)
            t_X_test = torch.tensor(X_test_scaled, dtype=torch.float32).to(device)
            t_y_train = torch.tensor(y_train_scaled, dtype=torch.float32).to(device)

            # 4. Train Autoencoder
            torch.manual_seed(42)
            np.random.seed(42)
            ae = ControlledAutoencoder(input_dim=256, bottleneck_dim=b_size).to(device)
            ae_opt = optim.Adam(ae.parameters(), lr=ae_lr)
            ae_crit = nn.MSELoss()
            ae_loader = DataLoader(TensorDataset(t_X_train, t_X_train), batch_size=batch_size, shuffle=True)

            ae.train()
            for epoch in range(ae_epochs):
                for bx, _ in ae_loader:
                    ae_opt.zero_grad()
                    recon, _ = ae(bx)
                    loss = ae_crit(recon, bx)
                    loss.backward()
                    ae_opt.step()

            # Extract Latent
            ae.eval()
            with torch.no_grad():
                _, train_latent = ae(t_X_train)
                _, test_latent = ae(t_X_test)

            # 5. Train BPNN
            torch.manual_seed(42)
            np.random.seed(42)
            bpnn = ControlledBPNN(input_dim=b_size).to(device)
            bpnn_opt = optim.Adam(bpnn.parameters(), lr=bpnn_lr)
            bpnn_crit = nn.MSELoss()
            bpnn_loader = DataLoader(TensorDataset(train_latent, t_y_train), batch_size=batch_size, shuffle=True)

            bpnn.train()
            for epoch in range(bpnn_epochs):
                for bx, by in bpnn_loader:
                    bpnn_opt.zero_grad()
                    preds = bpnn(bx)
                    loss = bpnn_crit(preds, by)
                    loss.backward()
                    bpnn_opt.step()

            # 6. Evaluate
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

            print(f"    Train RMSE: {tr_rmse:.5f} | Test RMSE: {te_rmse:.5f} | Test R2: {te_r2:.5f}")

            results_list.append({
                'Frequency_Grid': g_name,
                'Interpolation_Method': m_name,
                'Train_RMSE': tr_rmse,
                'Train_R2': tr_r2,
                'Test_MAE': te_mae,
                'Test_RMSE': te_rmse,
                'Test_R2': te_r2
            })

    # Save and Display Results
    df_res = pd.DataFrame(results_list)
    df_res = df_res.sort_values(by='Test_RMSE')
    df_res.to_csv('Interpolation_Ablation_Results.csv', index=False)
    
    print("\n" + "="*85)
    print("--- INTERPOLATION ABLATION RESULTS (Ranked by Test RMSE) ---")
    print(df_res.to_markdown(index=False))
    print("=====================================================================================")

if __name__ == "__main__":
    run_interpolation_ablation()