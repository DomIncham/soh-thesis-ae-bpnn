import torch
import numpy as np
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA

def generate_pca_proof():
    data = torch.load('Interpolated_EIS_Data.pt', weights_only=True)
    X_raw = data['features'].numpy()
    
    pca = PCA()
    pca.fit(X_raw)
    
    cumulative_variance = np.cumsum(pca.explained_variance_ratio_)
    target_variance = 0.99
    optimal_components = np.argmax(cumulative_variance >= target_variance) + 1
    
    plt.figure(figsize=(10, 6))
    plt.plot(range(1, len(cumulative_variance) + 1), cumulative_variance, 'b-', linewidth=2)
    plt.axhline(y=target_variance, color='r', linestyle='--', label=f'99% Information Retained')
    plt.axvline(x=optimal_components, color='g', linestyle='--', label=f'Optimal Bottleneck = {optimal_components}')
    
    plt.title('Proof of Feature Selection: Intrinsic Dimensionality of NASA EIS Data')
    plt.xlabel('Number of Principal Components (Latent Nodes)')
    plt.ylabel('Cumulative Explained Variance')
    plt.xlim(0, 30) # ซูมดูแค่ 30 ตัวแรก
    plt.ylim(0.8, 1.01)
    plt.legend(loc='lower right')
    plt.grid(True)
    plt.savefig('Proof_PCA_Variance.png')
    print(f"Optimal components for 99% variance: {optimal_components}")
    print("Saved 'Proof_PCA_Variance.png'")

if __name__ == "__main__":
    generate_pca_proof()