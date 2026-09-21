import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error

# -----------------------------------------------------------------------------
# 1. Controlled Autoencoder Architecture
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

# -----------------------------------------------------------------------------
# 2. Evaluation Pipeline (Strictly adhering to Advisor's requests)
# -----------------------------------------------------------------------------
def run_ae_reconstruction_eval():
    print("="*85)
    print("Autoencoder Reconstruction Performance Evaluation")
    print("Target: Assess ability to reconstruct Unseen Data (B0018) in physical units (Ohms)")
    print("Controlled Vars: Bottleneck=17, Epochs=300, Batch=16, AE_LR=0.001")
    print("="*85)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    # We strictly use the Log Grid + PCHIP dataset based on the previous interpolation validation
    dataset_file = 'Mapped_EIS_SOH_log_grid_pchip.pt'
    if not os.path.exists(dataset_file):
        print(f"[ERROR] Required dataset '{dataset_file}' not found.")
        return

    data = torch.load(dataset_file, weights_only=True)
    X_raw = data['features'].numpy()
    y_meta = data['labels'].numpy()

    battery_ids = y_meta[:, 0].astype(int)
    
    # 1. Explicit Train/Val/Test Split (as ordered by advisor)
    mask_train = np.isin(battery_ids, [1, 2]) # B0005, B0006
    mask_val = (battery_ids == 3)             # B0007
    mask_test = (battery_ids == 4)            # B0018 (Unseen)

    X_train_raw = X_raw[mask_train]
    X_val_raw = X_raw[mask_val]
    X_test_raw = X_raw[mask_test]

    # 2. Strict Zero-Leakage Scaling
    scaler_X = MinMaxScaler()
    X_train_scaled = scaler_X.fit_transform(X_train_raw) # FIT ON TRAIN ONLY!
    X_val_scaled = scaler_X.transform(X_val_raw)
    X_test_scaled = scaler_X.transform(X_test_raw)

    t_X_train = torch.tensor(X_train_scaled, dtype=torch.float32).to(device)
    t_X_val = torch.tensor(X_val_scaled, dtype=torch.float32).to(device)
    t_X_test = torch.tensor(X_test_scaled, dtype=torch.float32).to(device)

    # 3. Train Autoencoder with Controlled Parameters
    b_size = 17
    batch_size = 16
    ae_epochs = 300
    ae_lr = 0.001

    torch.manual_seed(42)
    np.random.seed(42)
    
    print(">>> Training Autoencoder...")
    ae = ControlledAutoencoder(input_dim=256, bottleneck_dim=b_size).to(device)
    optimizer = optim.Adam(ae.parameters(), lr=ae_lr)
    criterion = nn.MSELoss()
    train_loader = DataLoader(TensorDataset(t_X_train, t_X_train), batch_size=batch_size, shuffle=True)

    ae.train()
    for epoch in range(ae_epochs):
        for bx, _ in train_loader:
            optimizer.zero_grad()
            recon, _ = ae(bx)
            loss = criterion(recon, bx)
            loss.backward()
            optimizer.step()

    # 4. Extract Reconstructions
    ae.eval()
    with torch.no_grad():
        recon_train_scaled, _ = ae(t_X_train)
        recon_val_scaled, _ = ae(t_X_val)
        recon_test_scaled, _ = ae(t_X_test)
        
    recon_train_scaled = recon_train_scaled.cpu().numpy()
    recon_val_scaled = recon_val_scaled.cpu().numpy()
    recon_test_scaled = recon_test_scaled.cpu().numpy()

    # 5. Inverse Transform to Physical Units (Ohms)
    recon_train_raw = scaler_X.inverse_transform(recon_train_scaled)
    recon_val_raw = scaler_X.inverse_transform(recon_val_scaled)
    recon_test_raw = scaler_X.inverse_transform(recon_test_scaled)

    # 6. Calculate Cycle-wise Errors for Mean & Std Dev
    def calculate_cycle_errors(true_data, recon_data):
        errors = []
        for i in range(len(true_data)):
            rmse = np.sqrt(mean_squared_error(true_data[i], recon_data[i]))
            errors.append(rmse)
        return np.array(errors)

    err_train = calculate_cycle_errors(X_train_raw, recon_train_raw)
    err_val = calculate_cycle_errors(X_val_raw, recon_val_raw)
    err_test = calculate_cycle_errors(X_test_raw, recon_test_raw)

    results = [
        {'Dataset': 'Train (B0005, B0006)', 'Mean_RMSE (Ohms)': np.mean(err_train), 'Std_RMSE': np.std(err_train)},
        {'Dataset': 'Validation (B0007)', 'Mean_RMSE (Ohms)': np.mean(err_val), 'Std_RMSE': np.std(err_val)},
        {'Dataset': 'Unseen Test (B0018)', 'Mean_RMSE (Ohms)': np.mean(err_test), 'Std_RMSE': np.std(err_test)}
    ]
    
    df_res = pd.DataFrame(results)
    df_res.to_csv('AE_Reconstruction_Metrics.csv', index=False)
    
    print("\n" + "="*85)
    print("--- AUTOENCODER RECONSTRUCTION PERFORMANCE (Physical Units: Ohms) ---")
    print(df_res.to_markdown(index=False))
    print("="*85)

    # 7. Generate Visual Evidence (Nyquist Plot)
    print("\n>>> Generating Visual Evidence (Nyquist Plot Comparison)...")
    
    # Pick mid-life cycles for fair representation
    idx_train = len(X_train_raw) // 2
    idx_test = len(X_test_raw) // 2

    def plot_nyquist(ax, true_signal, recon_signal, title):
        # Recall that first 128 points are Re(Z), next 128 points are -Im(Z)
        re_true = true_signal[:128]
        im_true = true_signal[128:]
        re_recon = recon_signal[:128]
        im_recon = recon_signal[128:]
        
        ax.plot(re_true, im_true, 'k-', linewidth=2.5, label='Raw EIS (PCHIP Interpolated)')
        ax.plot(re_recon, im_recon, 'r--', linewidth=2, label='AE Reconstructed')
        ax.set_title(title, fontsize=12)
        ax.set_xlabel('Re_Z (Ohms)', fontsize=10)
        ax.set_ylabel('-Im_Z (Ohms)', fontsize=10)
        ax.grid(True, linestyle='--', alpha=0.6)
        ax.legend()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    plot_nyquist(ax1, X_train_raw[idx_train], recon_train_raw[idx_train], f"Train Set (B0005/06) - RMSE: {err_train[idx_train]:.6f}")
    plot_nyquist(ax2, X_test_raw[idx_test], recon_test_raw[idx_test], f"Unseen Test Set (B0018) - RMSE: {err_test[idx_test]:.6f}")
    
    plt.tight_layout()
    plt.savefig('Fig_AE_Reconstruction_Proof.png', dpi=300)
    print("Generated: Fig_AE_Reconstruction_Proof.png")
    print("Generated: AE_Reconstruction_Metrics.csv")

if __name__ == "__main__":
    run_ae_reconstruction_eval()