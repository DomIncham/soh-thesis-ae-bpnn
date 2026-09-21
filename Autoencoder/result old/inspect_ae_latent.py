import torch
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
import joblib
from ae_model_blueprint import EIS_Autoencoder

def inspect_latent_space():
    print("1. Loading Models and Data...")
    try:
        ae_scaler = joblib.load('ae_input_scaler.pkl')
    except FileNotFoundError:
        print("[ERROR] 'ae_input_scaler.pkl' not found. Run train_ae.py first.")
        return

    # Update to mathematically proven bottleneck size
    ae_model = EIS_Autoencoder(bottleneck_size=9)
    ae_model.load_state_dict(torch.load('trained_ae_weights.pth', weights_only=True))
    ae_model.eval()

    eis_data = torch.load('Interpolated_EIS_Data.pt', weights_only=True)
    X_eis_tensor = eis_data['features']
    y_eis_labels = eis_data['labels'].cpu().numpy().copy()
    
    df_eis = pd.DataFrame(y_eis_labels, columns=['Battery_ID', 'Cycle']).astype(int)
    df_eis['Feature_Index'] = df_eis.index 
    
    target_battery = 1
    df_b0005 = df_eis[df_eis['Battery_ID'] == target_battery].sort_values('Cycle')
    
    cycles = df_b0005['Cycle'].values
    indices = torch.tensor(df_b0005['Feature_Index'].values, dtype=torch.long)
    tensors_b0005 = X_eis_tensor[indices].clone().detach()
    
    print("2. Normalizing Input and Extracting 9 Latent Features...")
    scaled_inputs = ae_scaler.transform(tensors_b0005.numpy())
    scaled_inputs_tensor = torch.tensor(scaled_inputs, dtype=torch.float32)

    with torch.no_grad():
        latent_features = ae_model.encoder(scaled_inputs_tensor).numpy()
        
    print("3. Plotting Latent Space Trajectories...")
    vis_scaler = MinMaxScaler()
    latent_scaled = vis_scaler.fit_transform(latent_features)
    
    plt.figure(figsize=(14, 8))
    # Generating 9 distinct colors for plotting
    colors = plt.cm.tab10(np.linspace(0, 1, 9))
    
    for i in range(9):
        plt.plot(cycles, latent_scaled[:, i], label=f'Node {i+1}', color=colors[i], alpha=0.8, linewidth=1.5)
        
    plt.title('Diagnostic: Standard AE Latent Features Trajectory (Bottleneck=9)')
    plt.xlabel('Cycle Number')
    plt.ylabel('Normalized Feature Value (0 to 1)')
    # Place legend outside to avoid cluttering the 9 lines
    plt.legend(bbox_to_anchor=(1.04, 1), loc="upper left")
    plt.grid(True)
    plt.tight_layout()
    
    plt.savefig('Diagnostic_AE_Latent_Space_Fixed.png')
    print("[SUCCESS] Saved diagnostic plot as 'Diagnostic_AE_Latent_Space_Fixed.png'")
    plt.show()

if __name__ == "__main__":
    inspect_latent_space()