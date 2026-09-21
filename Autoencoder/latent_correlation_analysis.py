import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import pearsonr, spearmanr
from sklearn.preprocessing import MinMaxScaler

# -----------------------------------------------------------------------------
# 1. Controlled Autoencoder Architecture (Strictly Baseline)
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
# 2. Main Execution: Latent Correlation Analysis
# -----------------------------------------------------------------------------
def run_latent_correlation():
    print("="*85)
    print("Latent Space Correlation Analysis (Rule: Quantitative Evidence)")
    print("Target: Evaluate Pearson/Spearman correlation between Latent Nodes and Capacity")
    print("Controlled Vars: Bottleneck=17 (from PCA 95%), Epochs=300, Batch=16, AE_LR=0.001")
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
    
    # 1. Strict LOBO Split (Zero Future Leakage)
    train_mask = (battery_ids != 4)
    test_mask = (battery_ids == 4) # B0018 Unseen

    X_train_raw = X_raw[train_mask]
    X_test_raw = X_raw[test_mask]
    y_train_raw = y_capacity[train_mask]
    y_test_raw = y_capacity[test_mask]

    # 2. Fit Scaler ONLY on Train Set
    scaler_X = MinMaxScaler()
    X_train_scaled = scaler_X.fit_transform(X_train_raw)
    X_test_scaled = scaler_X.transform(X_test_raw)

    t_X_train = torch.tensor(X_train_scaled, dtype=torch.float32).to(device)
    t_X_test = torch.tensor(X_test_scaled, dtype=torch.float32).to(device)

    # 3. Train Autoencoder
    b_size = 17
    torch.manual_seed(42)
    np.random.seed(42)
    
    print(">>> Training Autoencoder to extract latent representations...")
    ae = ControlledAutoencoder(input_dim=256, bottleneck_dim=b_size).to(device)
    optimizer = optim.Adam(ae.parameters(), lr=0.001)
    criterion = nn.MSELoss()
    train_loader = DataLoader(TensorDataset(t_X_train, t_X_train), batch_size=16, shuffle=True)

    ae.train()
    for epoch in range(300):
        for bx, _ in train_loader:
            optimizer.zero_grad()
            recon, _ = ae(bx)
            loss = criterion(recon, bx)
            loss.backward()
            optimizer.step()

    # 4. Extract Latent Space Features
    ae.eval()
    with torch.no_grad():
        _, latent_train = ae(t_X_train)
        _, latent_test = ae(t_X_test)
        
    latent_train = latent_train.cpu().numpy()
    latent_test = latent_test.cpu().numpy()

    # 5. Calculate Correlations (Pearson and Spearman)
    print(">>> Calculating Pearson and Spearman Correlations vs SOH...")
    correlation_results = []
    
    # We evaluate what the AE LEARNED (Train) and how it GENERALIZES (Test)
    for i in range(b_size):
        node_train = latent_train[:, i]
        node_test = latent_test[:, i]
        
        # Train Set Correlations
        p_corr_tr, p_pval_tr = pearsonr(node_train, y_train_raw)
        s_corr_tr, s_pval_tr = spearmanr(node_train, y_train_raw)
        
        # Test Set Correlations
        p_corr_te, p_pval_te = pearsonr(node_test, y_test_raw)
        s_corr_te, s_pval_te = spearmanr(node_test, y_test_raw)
        
        correlation_results.append({
            'Latent_Node': f'Node_{i+1}',
            'Train_Pearson_R': p_corr_tr,
            'Train_Spearman_R': s_corr_tr,
            'Test_Pearson_R': p_corr_te,
            'Test_Spearman_R': s_corr_te
        })

    df_corr = pd.DataFrame(correlation_results)
    df_corr.to_csv('Latent_Correlation_Metrics.csv', index=False)
    
    print("\n" + "="*85)
    print("--- TOP 5 LATENT NODES CORRELATED WITH SOH (Ranked by Absolute Train Pearson) ---")
    df_corr['Abs_Train_Pearson'] = df_corr['Train_Pearson_R'].abs()
    df_top = df_corr.sort_values(by='Abs_Train_Pearson', ascending=False).head(5)
    print(df_top[['Latent_Node', 'Train_Pearson_R', 'Train_Spearman_R', 'Test_Pearson_R', 'Test_Spearman_R']].to_markdown(index=False))
    print("="*85)

    # 6. Generate Visual Evidence (Correlation Matrix Heatmap among Nodes & Capacity)
    print("\n>>> Generating Visual Evidence (Heatmap of Latent Space)...")
    
    # Create a DataFrame combining Latent Nodes and Capacity for the Train Set
    # (To see how nodes interact with each other and what they learned)
    column_names = [f'N{i+1}' for i in range(b_size)]
    df_heatmap = pd.DataFrame(latent_train, columns=column_names)
    df_heatmap['Capacity'] = y_train_raw
    
    # Calculate Correlation Matrix
    corr_matrix = df_heatmap.corr(method='pearson')
    
    plt.figure(figsize=(14, 10))
    sns.heatmap(corr_matrix, annot=False, cmap='coolwarm', center=0, 
                square=True, linewidths=.5, cbar_kws={"shrink": .75})
    plt.title("Fig: Pearson Correlation Matrix of Latent Nodes & Capacity (Train Set)", fontsize=14)
    plt.tight_layout()
    plt.savefig('Fig_Latent_Correlation_Heatmap.png', dpi=300)
    
    print("Generated: Fig_Latent_Correlation_Heatmap.png")
    print("Generated: Latent_Correlation_Metrics.csv")

if __name__ == "__main__":
    run_latent_correlation()