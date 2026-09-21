import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
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
# 2. Stage 3 Pilot Execution
# -----------------------------------------------------------------------------
def run_stage3_pilot():
    print("="*85)
    print("Stage 3: Pilot Test (1 Configuration)")
    print("Config: Bottleneck=17 | Loss=MSE | L2=1e-4 | Epochs=300")
    print("="*85)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    dataset_file = 'Mapped_EIS_SOH_log_grid_pchip.pt'
    
    if not os.path.exists(dataset_file):
        print(f"[ERROR] Required dataset '{dataset_file}' not found.")
        return

    data = torch.load(dataset_file, weights_only=True)
    X_raw = data['features'].numpy()
    y_meta = data['labels'].numpy()

    battery_ids = y_meta[:, 0].astype(int)
    y_capacity = y_meta[:, 2]

    # Strict LOBO Split
    train_mask = (battery_ids != 4)
    test_mask = (battery_ids == 4)

    X_train_raw = X_raw[train_mask]
    X_test_raw = X_raw[test_mask]
    
    y_train_raw = y_capacity[train_mask].reshape(-1, 1)
    y_test_raw = y_capacity[test_mask].reshape(-1, 1)

    # Scaling
    scaler_X = MinMaxScaler()
    X_train_scaled = scaler_X.fit_transform(X_train_raw)
    X_test_scaled = scaler_X.transform(X_test_raw)

    scaler_Y = MinMaxScaler()
    y_train_scaled = scaler_Y.fit_transform(y_train_raw)
    y_test_scaled = scaler_Y.transform(y_test_raw)

    tensor_X_train = torch.tensor(X_train_scaled, dtype=torch.float32).to(device)
    tensor_X_test = torch.tensor(X_test_scaled, dtype=torch.float32).to(device)
    tensor_y_train = torch.tensor(y_train_scaled, dtype=torch.float32).to(device)

    # Pre-train Autoencoder
    b_size = 17
    print(f">>> Training Autoencoder (Bottleneck: {b_size})...")
    torch.manual_seed(42)
    np.random.seed(42)

    ae = ControlledAutoencoder(input_dim=256, bottleneck_dim=b_size).to(device)
    ae_opt = optim.Adam(ae.parameters(), lr=0.001)
    ae_crit = nn.MSELoss()
    ae_loader = DataLoader(TensorDataset(tensor_X_train, tensor_X_train), batch_size=16, shuffle=True)

    ae.train()
    for epoch in range(300):
        for bx, _ in ae_loader:
            ae_opt.zero_grad()
            recon, _ = ae(bx)
            loss = ae_crit(recon, bx)
            loss.backward()
            ae_opt.step()

    ae.eval()
    with torch.no_grad():
        _, train_latent = ae(tensor_X_train)
        _, test_latent = ae(tensor_X_test)

    # Train BPNN
    l2_val = 1e-4
    print(f">>> Training BPNN (L2: {l2_val}, Loss: MSE)...")
    bpnn_loader = DataLoader(TensorDataset(train_latent, tensor_y_train), batch_size=16, shuffle=True)
    
    torch.manual_seed(42)
    np.random.seed(42)
    
    bpnn = ControlledBPNN(input_dim=b_size, hidden_layers=[16, 8]).to(device)
    bpnn_opt = optim.Adam(bpnn.parameters(), lr=0.005, weight_decay=l2_val)
    bpnn_crit = nn.MSELoss()

    bpnn.train()
    for epoch in range(300):
        for bx, by in bpnn_loader:
            bpnn_opt.zero_grad()
            preds = bpnn(bx)
            loss = bpnn_crit(preds, by)
            loss.backward()
            bpnn_opt.step()

    # Evaluate (Inverse Transform back to Physical Scale Ah)
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

    print("\n--- PILOT TEST RESULTS ---")
    print(f"Train RMSE: {tr_rmse:.5f} | Train R2: {tr_r2:.5f}")
    print(f"Test RMSE:  {te_rmse:.5f} | Test R2:  {te_r2:.5f}")
    print(f"Gap (Test - Train RMSE): {te_rmse - tr_rmse:.5f}")
    print("=====================================================================================")

if __name__ == "__main__":
    run_stage3_pilot()