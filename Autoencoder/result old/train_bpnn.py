import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, MinMaxScaler
import pandas as pd
import numpy as np
import joblib
from ae_model_blueprint import EIS_Autoencoder

# -------------------------------------------------------------------
# BPNN Architecture (Streamlined for highly compressed, pure features)
# -------------------------------------------------------------------
class BPNN_Predictor(nn.Module):
    def __init__(self, input_features=4): # Strictly matched to AE bottleneck
        super(BPNN_Predictor, self).__init__()
        # A simple, shallow MLP is sufficient since the AE already extracted high-quality features.
        self.network = nn.Sequential(
            nn.Linear(input_features, 16),
            nn.ReLU(),
            nn.Linear(16, 8),
            nn.ReLU(),
            nn.Linear(8, 1)
        )
    def forward(self, x):
        return self.network(x)

def train_pure_baseline_scenario_a():
    print("1. Loading Data & Extracting Clean Features (Bottleneck=4)...")
    
    # Initialize AE with the mathematically proven bottleneck size
    ae_model = EIS_Autoencoder(bottleneck_size=4) 
    ae_model.load_state_dict(torch.load('trained_ae_weights.pth', weights_only=True))
    ae_model.eval()

    # Load interpolated EIS features
    eis_data = torch.load('Interpolated_EIS_Data.pt', weights_only=True)
    X_eis_tensor = eis_data['features']
    y_eis_labels = eis_data['labels'].cpu().numpy().copy()
    
    df_eis = pd.DataFrame(y_eis_labels, columns=['Battery_ID', 'Cycle']).astype(int)
    df_eis['Feature_Index'] = df_eis.index 
    df_capacity = pd.read_csv('NASA_Capacity_Data.csv').astype({'Battery_ID': int, 'Cycle': int})
    
    df_eis = df_eis.sort_values('Cycle')
    df_capacity = df_capacity.sort_values('Cycle')
    
    # [ACADEMIC RIGOR]: Merge using empirically proven tolerance=2
    merged_df = pd.merge_asof(
        df_eis, df_capacity, on='Cycle', by='Battery_ID', direction='nearest', tolerance=2
    ).dropna(subset=['Capacity_Ah'])
    
    matched_indices = torch.tensor(merged_df['Feature_Index'].to_numpy(copy=True), dtype=torch.long)
    matched_eis_tensors = X_eis_tensor[matched_indices].clone().detach()
    
    with torch.no_grad():
        latent_features = ae_model.encoder(matched_eis_tensors).numpy()
    actual_capacity = merged_df['Capacity_Ah'].values.reshape(-1, 1)

    print("2. Performing 80/20 Train-Test Split (Scenario A Baseline)...")
    # Using random_state=42 ensures reproducibility for thesis experiments
    X_train_raw, X_test_raw, y_train_raw, y_test_raw = train_test_split(
        latent_features, actual_capacity, test_size=0.20, random_state=42
    )

    print("3. Normalizing Data (Preventing Data Leakage)...")
    # StandardScaler for features preserves variance; MinMaxScaler bounds capacity (0-1)
    feature_scaler = StandardScaler()
    target_scaler = MinMaxScaler()
    
    X_train_scaled = feature_scaler.fit_transform(X_train_raw)
    y_train_scaled = target_scaler.fit_transform(y_train_raw)
    X_test_scaled = feature_scaler.transform(X_test_raw)
    y_test_scaled = target_scaler.transform(y_test_raw)
    
    # Save scalers for future evaluation
    joblib.dump(feature_scaler, 'feature_scaler.pkl')
    joblib.dump(target_scaler, 'target_scaler.pkl')
    
    X_train_tensor = torch.tensor(X_train_scaled, dtype=torch.float32)
    y_train_tensor = torch.tensor(y_train_scaled, dtype=torch.float32)
    X_test_tensor = torch.tensor(X_test_scaled, dtype=torch.float32)
    y_test_tensor = torch.tensor(y_test_scaled, dtype=torch.float32)

    train_dataset = TensorDataset(X_train_tensor, y_train_tensor)
    train_dataloader = DataLoader(train_dataset, batch_size=32, shuffle=True)

    print("4. Training Pure BPNN...")
    bpnn_model = BPNN_Predictor(input_features=4)
    criterion = nn.MSELoss()
    
    # Mild L2 regularization (weight_decay) prevents over-reliance on a single feature
    optimizer = optim.Adam(bpnn_model.parameters(), lr=0.005, weight_decay=1e-5)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=50)
    
    epochs = 1500 
    best_val_loss = float('inf')
    patience = 200 # Allow sufficient time to escape local minima
    epochs_no_improve = 0
    best_model_state = None

    for epoch in range(epochs):
        bpnn_model.train()
        train_loss = 0
        for batch_x, batch_y in train_dataloader:
            optimizer.zero_grad()
            predictions = bpnn_model(batch_x)
            loss = criterion(predictions, batch_y)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
            
        avg_train_loss = train_loss / len(train_dataloader)
        
        # --- Validation Phase ---
        bpnn_model.eval()
        with torch.no_grad():
            val_predictions = bpnn_model(X_test_tensor)
            val_loss = criterion(val_predictions, y_test_tensor).item()
            
        scheduler.step(val_loss)
            
        # Early Stopping Logic
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            epochs_no_improve = 0
            best_model_state = bpnn_model.state_dict()
        else:
            epochs_no_improve += 1
            
        if epochs_no_improve >= patience:
            print(f"Early stopping triggered at epoch {epoch + 1}! Restoring best weights.")
            break
            
        if (epoch + 1) % 100 == 0:
            print(f"Epoch [{epoch + 1}/{epochs}] | Train Loss: {avg_train_loss:.6f} | Val Loss: {val_loss:.6f}")

    torch.save(best_model_state, 'trained_bpnn_weights.pth')
    print(f"\n[SUCCESS] Baseline BPNN trained securely. Best Val Loss: {best_val_loss:.6f}")

if __name__ == "__main__":
    train_pure_baseline_scenario_a()