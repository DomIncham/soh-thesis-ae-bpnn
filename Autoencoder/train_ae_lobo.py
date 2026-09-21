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
# 1. Define the Standard Autoencoder Architecture
# -----------------------------------------------------------------------------
class StandardAutoencoder(nn.Module):
    def __init__(self, input_dim=256, bottleneck_dim=9):
        super(StandardAutoencoder, self).__init__()
        # Encoder: Compressing spatial features
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, bottleneck_dim)
            # No ReLU on bottleneck to allow latent features to span negative values if needed
        )
        # Decoder: Reconstructing spatial features
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
# 2. Evaluation Metrics Function (Professor's Rule)
# -----------------------------------------------------------------------------
def calculate_metrics(y_true, y_pred):
    """Calculates MAE, RMSE, and R2."""
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred)
    return mae, rmse, r2

# -----------------------------------------------------------------------------
# 3. Main LOBO Training and Evaluation Pipeline
# -----------------------------------------------------------------------------
def run_ae_ablation():
    print("="*60)
    print("Starting Autoencoder LOBO Ablation Study")
    print("="*60)
    
    # Files generated from data_interpolation.py
    grid_types = ['linear_grid', 'log_grid']
    methods = ['linear', 'cubic', 'pchip']
    
    # LOBO Configuration
    target_test_battery = 4 # Battery ID corresponding to B0018
    bottleneck_size = 9     # Fixed bottleneck for this ablation step
    epochs = 200
    batch_size = 32
    learning_rate = 0.001
    
    results_summary = []

    for g_name in grid_types:
        for m_name in methods:
            file_name = f'Interpolated_EIS_{g_name}_{m_name}.pt'
            if not os.path.exists(file_name):
                print(f"[WARNING] Skipping {file_name} (Not found)")
                continue
                
            print(f"\nEvaluating Dataset: {g_name} + {m_name.upper()}")
            
            # Load Data
            data = torch.load(file_name, weights_only=True)
            X_all = data['features'].numpy() # Shape: (Samples, 256)
            y_all = data['labels'].numpy()   # Shape: (Samples, 2) [Battery_ID, Cycle]
            
            # Extract Battery IDs to apply LOBO split
            battery_ids = y_all[:, 0]
            
            # -----------------------------------------------------------------
            # [ACADEMIC RIGOR]: Strict Leave-One-Battery-Out (LOBO) Split
            # -----------------------------------------------------------------
            train_idx = np.where(battery_ids != target_test_battery)[0]
            test_idx = np.where(battery_ids == target_test_battery)[0]
            
            X_train_raw = X_all[train_idx]
            X_test_raw = X_all[test_idx]
            
            # -----------------------------------------------------------------
            # [ACADEMIC RIGOR]: Prevent Data Leakage in Normalization
            # -----------------------------------------------------------------
            scaler = MinMaxScaler()
            # FIT ONLY ON TRAINING DATA!
            X_train_scaled = scaler.fit_transform(X_train_raw) 
            # TRANSFORM TEST DATA using training parameters!
            X_test_scaled = scaler.transform(X_test_raw)
            
            # Convert to PyTorch tensors
            X_train_t = torch.tensor(X_train_scaled, dtype=torch.float32)
            X_test_t = torch.tensor(X_test_scaled, dtype=torch.float32)
            
            train_loader = DataLoader(TensorDataset(X_train_t, X_train_t), batch_size=batch_size, shuffle=True)
            
            # Initialize Model, Loss, and Optimizer
            model = StandardAutoencoder(input_dim=256, bottleneck_dim=bottleneck_size)
            criterion = nn.MSELoss()
            optimizer = optim.Adam(model.parameters(), lr=learning_rate)
            
            # Train the Model
            model.train()
            for epoch in range(epochs):
                for batch_x, _ in train_loader:
                    optimizer.zero_grad()
                    reconstructed, _ = model(batch_x)
                    loss = criterion(reconstructed, batch_x)
                    loss.backward()
                    optimizer.step()
            
            # Evaluate the Model
            model.eval()
            with torch.no_grad():
                # Evaluate on Train Set
                train_recon, _ = model(X_train_t)
                tr_mae, tr_rmse, tr_r2 = calculate_metrics(X_train_t.numpy(), train_recon.numpy())
                
                # Evaluate on Unseen Test Set (LOBO Battery)
                test_recon, _ = model(X_test_t)
                te_mae, te_rmse, te_r2 = calculate_metrics(X_test_t.numpy(), test_recon.numpy())
            
            # Save the trained encoder and scaler for BPNN later
            save_prefix = f"{g_name}_{m_name}"
            torch.save(model.state_dict(), f'AE_Model_{save_prefix}.pth')
            
            # Log results
            print(f"  Train (Seen)   -> RMSE: {tr_rmse:.5f} | MAE: {tr_mae:.5f} | R2: {tr_r2:.5f}")
            print(f"  Test  (Unseen) -> RMSE: {te_rmse:.5f} | MAE: {te_mae:.5f} | R2: {te_r2:.5f}")
            
            results_summary.append({
                'Grid': g_name,
                'Interpolation': m_name,
                'Test_RMSE': te_rmse,
                'Test_MAE': te_mae,
                'Test_R2': te_r2
            })
            
    # -------------------------------------------------------------------------
    # 4. Generate Final Ablation Report Table
    # -------------------------------------------------------------------------
    print("\n" + "="*60)
    print("Ablation Study Summary: AE Reconstruction on Unseen Battery")
    print("="*60)
    df_results = pd.DataFrame(results_summary)
    
    # Sort by best Test R2 (Highest) and Test RMSE (Lowest)
    df_results = df_results.sort_values(by=['Test_R2', 'Test_RMSE'], ascending=[False, True])
    print(df_results.to_markdown(index=False))
    
    # Save to CSV for the thesis report
    df_results.to_csv('AE_Ablation_Results.csv', index=False)
    print("\nResults saved to 'AE_Ablation_Results.csv'")

if __name__ == "__main__":
    run_ae_ablation()