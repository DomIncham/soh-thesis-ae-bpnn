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
# 1. Pre-trained Autoencoder Definition (Feature Extractor)
# -----------------------------------------------------------------------------
class StandardAutoencoder(nn.Module):
    def __init__(self, input_dim=256, bottleneck_dim=9):
        super(StandardAutoencoder, self).__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, bottleneck_dim)
        )
        self.decoder = nn.Sequential(
            nn.Linear(bottleneck_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 128),
            nn.ReLU(),
            nn.Linear(128, input_dim)
        )

    def forward(self, x):
        latent = self.encoder(x)
        reconstructed = self.decoder(latent)
        return reconstructed, latent

# -----------------------------------------------------------------------------
# 2. Flexible BPNN Architecture Builder
# -----------------------------------------------------------------------------
class DynamicBPNN(nn.Module):
    def __init__(self, input_dim, hidden_layers):
        super(DynamicBPNN, self).__init__()
        layers = []
        prev_dim = input_dim
        for hidden_dim in hidden_layers:
            layers.append(nn.Linear(prev_dim, hidden_dim))
            layers.append(nn.ReLU())
            prev_dim = hidden_dim
        layers.append(nn.Linear(prev_dim, 1)) # Output: Capacity (Ah)
        self.network = nn.Sequential(*layers)

    def forward(self, x):
        return self.network(x)

def calculate_metrics(y_true, y_pred):
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred)
    return mae, rmse, r2

# -----------------------------------------------------------------------------
# 3. Main Grid Search Execution Pipeline
# -----------------------------------------------------------------------------
def search_bpnn_baseline():
    print("="*80)
    print("Executing Systematic Grid Search for BPNN Baseline (Priority 3)")
    print("Validation Strategy: Strict Leave-One-Battery-Out (LOBO on B0018)")
    print("="*80)

    dataset_file = 'Mapped_EIS_SOH_log_grid_pchip.pt'
    ae_model_file = 'AE_Model_log_grid_pchip.pth'

    if not os.path.exists(dataset_file) or not os.path.exists(ae_model_file):
        print(f"[ERROR] Required files not found: {dataset_file} or {ae_model_file}")
        return

    # 1. Load Mapped Dataset
    data = torch.load(dataset_file, weights_only=True)
    X_raw = data['features'].numpy()
    y_meta = data['labels'].numpy() # [Battery_ID, Cycle, Capacity_Ah]

    battery_ids = y_meta[:, 0].astype(int)
    y_capacity = y_meta[:, 2]

    # 2. LOBO Split Setup
    target_test_battery = 4 # B0018
    train_mask = (battery_ids != target_test_battery)
    test_mask = (battery_ids == target_test_battery)

    X_train_raw = X_raw[train_mask]
    X_test_raw = X_raw[test_mask]
    y_train = y_capacity[train_mask]
    y_test = y_capacity[test_mask]

    # Preprocessing strictly on Train Set
    scaler_X = MinMaxScaler()
    X_train_scaled = scaler_X.fit_transform(X_train_raw)
    X_test_scaled = scaler_X.transform(X_test_raw)

    # 3. Extract Latent Features via Pre-trained AE
    bottleneck_size = 9
    ae = StandardAutoencoder(input_dim=256, bottleneck_dim=bottleneck_size)
    ae.load_state_dict(torch.load(ae_model_file, weights_only=True))
    ae.eval()

    with torch.no_grad():
        _, train_latent = ae(torch.tensor(X_train_scaled, dtype=torch.float32))
        _, test_latent = ae(torch.tensor(X_test_scaled, dtype=torch.float32))

    # 4. Search Spaces
    architectures = [
        [8],
        [12],
        [16],
        [16, 8],
        [12, 6],
        [8, 4]
    ]

    loss_functions = {
        'MSE': nn.MSELoss(),
        'MAE': nn.L1Loss(),
        'Huber': nn.SmoothL1Loss()
    }

    epochs = 300
    batch_size = 16
    learning_rate = 0.005

    train_loader = DataLoader(
        TensorDataset(train_latent, torch.tensor(y_train, dtype=torch.float32).unsqueeze(1)),
        batch_size=batch_size,
        shuffle=True
    )

    grid_results = []
    
    total_configs = len(architectures) * len(loss_functions)
    cfg_counter = 1

    for arch in architectures:
        arch_str = str(arch)
        for loss_name, criterion in loss_functions.items():
            print(f"[{cfg_counter:>2}/{total_configs}] Testing Architecture: {arch_str:<10} | Loss: {loss_name:<6} ...", end="", flush=True)
            
            # Fix random seed for fair comparison
            torch.manual_seed(42)
            np.random.seed(42)

            bpnn = DynamicBPNN(input_dim=bottleneck_size, hidden_layers=arch)
            optimizer = optim.Adam(bpnn.parameters(), lr=learning_rate, weight_decay=0.0) # Baseline without L2

            bpnn.train()
            for epoch in range(epochs):
                for batch_x, batch_y in train_loader:
                    optimizer.zero_grad()
                    preds = bpnn(batch_x)
                    loss = criterion(preds, batch_y)
                    loss.backward()
                    optimizer.step()

            bpnn.eval()
            with torch.no_grad():
                train_preds = bpnn(train_latent).numpy().flatten()
                test_preds = bpnn(test_latent).numpy().flatten()

            tr_mae, tr_rmse, tr_r2 = calculate_metrics(y_train, train_preds)
            te_mae, te_rmse, te_r2 = calculate_metrics(y_test, test_preds)

            print(f" Done! -> Test RMSE: {te_rmse:.5f} | Test R2: {te_r2:.5f}")

            grid_results.append({
                'Hidden_Layers': arch_str,
                'Num_Layers': len(arch),
                'Loss_Function': loss_name,
                'Train_RMSE': tr_rmse,
                'Train_R2': tr_r2,
                'Test_RMSE': te_rmse,
                'Test_MAE': te_mae,
                'Test_R2': te_r2
            })
            cfg_counter += 1

    # 5. Output Summary Table
    print("\n" + "="*80)
    print("BPNN Baseline Grid Search Results (Sorted by Test R2)")
    print("="*80)
    df_results = pd.DataFrame(grid_results)
    df_results = df_results.sort_values(by=['Test_R2', 'Test_RMSE'], ascending=[False, True])
    print(df_results.to_markdown(index=False))

    df_results.to_csv('BPNN_Baseline_GridSearch_Results.csv', index=False)
    print("\nResults saved to 'BPNN_Baseline_GridSearch_Results.csv'")

if __name__ == "__main__":
    search_bpnn_baseline()