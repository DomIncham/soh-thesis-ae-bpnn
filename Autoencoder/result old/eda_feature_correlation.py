import torch
import pandas as pd
import numpy as np
from ae_model_blueprint import EIS_Autoencoder

def prove_feature_correlation():
    print("1. Loading Autoencoder and Data...")
    ae_model = EIS_Autoencoder()
    ae_model.load_state_dict(torch.load('trained_ae_weights.pth', weights_only=True))
    ae_model.eval()

    eis_data = torch.load('Interpolated_EIS_Data.pt', weights_only=True)
    X_eis_tensor = eis_data['features']
    y_eis_labels = eis_data['labels'].cpu().numpy().copy()
    
    df_eis = pd.DataFrame(y_eis_labels, columns=['Battery_ID', 'Cycle']).astype(int)
    df_eis['Feature_Index'] = df_eis.index 

    df_capacity = pd.read_csv('NASA_Capacity_Data.csv').astype({'Battery_ID': int, 'Cycle': int})
    df_eis = df_eis.sort_values('Cycle')
    df_capacity = df_capacity.sort_values('Cycle')
    
    # Merge with exact data-driven tolerance
    merged_df = pd.merge_asof(
        df_eis, df_capacity, on='Cycle', by='Battery_ID', 
        direction='nearest', tolerance=2
    ).dropna(subset=['Capacity_Ah'])
    
    matched_indices = torch.tensor(merged_df['Feature_Index'].to_numpy(copy=True), dtype=torch.long)
    matched_eis_tensors = X_eis_tensor[matched_indices].clone().detach()
    
    with torch.no_grad():
        latent_features = ae_model.encoder(matched_eis_tensors).numpy()
        
    actual_capacity = merged_df['Capacity_Ah'].values
    
    print("\n2. Calculating Pearson Correlation Coefficient (r)...")
    results = []
    for i in range(latent_features.shape[1]):
        r = np.corrcoef(latent_features[:, i], actual_capacity)[0, 1]
        results.append({'Feature': f'Latent_Node_{i}', 'Pearson_r': r, 'Abs_r': abs(r)})
        
    df_corr = pd.DataFrame(results).sort_values('Abs_r', ascending=False).reset_index(drop=True)
    
    print("\n=== Feature Correlation Ranking ===")
    print(df_corr.to_string())
    print("===================================")
    
    # [Academic Threshold]: |r| >= 0.40 is considered moderate-to-strong correlation
    threshold = 0.40
    valid_features = df_corr[df_corr['Abs_r'] >= threshold]
    print(f"\n[Conclusion]: Exactly {len(valid_features)} out of 20 features have |r| >= {threshold}.")
    print("This mathematical proof will be used to determine the BPNN input size.")

if __name__ == "__main__":
    prove_feature_correlation()