import torch
import torch.nn as nn
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import joblib
from ae_model_blueprint import EIS_Autoencoder

# -------------------------------------------------------------------
# BPNN Architecture (Must precisely match the trained weights)
# -------------------------------------------------------------------
class BPNN_Predictor(nn.Module):
    def __init__(self, input_features=4):
        super(BPNN_Predictor, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(input_features, 16),
            nn.ReLU(),
            nn.Linear(16, 8),
            nn.ReLU(),
            nn.Linear(8, 1)
        )
    def forward(self, x):
        return self.network(x)

def evaluate_and_plot():
    print("1. Loading Models, Scalers, and Data...")
    try:
        feature_scaler = joblib.load('feature_scaler.pkl')
        target_scaler = joblib.load('target_scaler.pkl')
    except FileNotFoundError:
        print("[ERROR] Scalers not found. Run the training script first.")
        return

    # Ensure bottleneck matches the architecture
    ae_model = EIS_Autoencoder(bottleneck_size=4)
    ae_model.load_state_dict(torch.load('trained_ae_weights.pth', weights_only=True))
    ae_model.eval()

    bpnn_model = BPNN_Predictor(input_features=4)
    bpnn_model.load_state_dict(torch.load('trained_bpnn_weights.pth', weights_only=True))
    bpnn_model.eval()

    eis_data = torch.load('Interpolated_EIS_Data.pt', weights_only=True)
    X_eis_tensor = eis_data['features']
    y_eis_labels = eis_data['labels'].cpu().numpy().copy() 
    
    df_eis = pd.DataFrame(y_eis_labels, columns=['Battery_ID', 'Cycle']).astype({'Battery_ID': int, 'Cycle': int})
    df_eis['Feature_Index'] = df_eis.index 
    df_capacity = pd.read_csv('NASA_Capacity_Data.csv').astype({'Battery_ID': int, 'Cycle': int})
    
    df_eis = df_eis.sort_values('Cycle')
    df_capacity = df_capacity.sort_values('Cycle')
    
    merged_df = pd.merge_asof(
        df_eis, df_capacity, on='Cycle', by='Battery_ID', 
        direction='nearest', tolerance=2 
    ).dropna(subset=['Capacity_Ah'])
    
    # 2. Select Battery B0005 for visualization (Scenario A context)
    target_battery = 1
    plot_df = merged_df[merged_df['Battery_ID'] == target_battery].sort_values('Cycle')
    
    actual_cycles = plot_df['Cycle'].values
    actual_capacity = plot_df['Capacity_Ah'].values 
    
    matched_indices = torch.tensor(plot_df['Feature_Index'].to_numpy(copy=True), dtype=torch.long)
    input_tensors = X_eis_tensor[matched_indices].clone().detach()
    
    with torch.no_grad():
        # Step A: Extract the 4 intrinsic features
        latent_features = ae_model.encoder(input_tensors).numpy()
        
        # Step B: Scale features using training distribution
        scaled_features = feature_scaler.transform(latent_features)
        
        # Step C: Predict capacity
        scaled_predictions = bpnn_model(torch.tensor(scaled_features, dtype=torch.float32)).numpy()
        
        # Step D: Inverse transform to original Ah unit
        predicted_capacity_raw = target_scaler.inverse_transform(scaled_predictions).squeeze()
        
    print("Plotting pure actual vs predicted capacity...")
    plt.figure(figsize=(10, 5))
    
    # Plot true values
    plt.plot(actual_cycles, actual_capacity, label='Actual Capacity (NASA)', color='blue', marker='o', markersize=3, linewidth=1.5)
    
    # Plot raw predictions (No smoothing applied - showing true model capability)
    plt.plot(actual_cycles, predicted_capacity_raw, label='Predicted Capacity (Raw AE-BPNN)', color='red', linestyle='dashed', linewidth=2)
    
    plt.title('Scenario A: Baseline SOH Estimation (Battery B0005) - Bottleneck=4')
    plt.xlabel('Cycle Number')
    plt.ylabel('Capacity (Ah)')
    plt.legend()
    plt.grid(True)
    
    plt.savefig('SOH_Scenario_A_True_Baseline.png')
    print("Graph saved successfully as 'SOH_Scenario_A_True_Baseline.png'!")
    plt.show()

if __name__ == "__main__":
    evaluate_and_plot()