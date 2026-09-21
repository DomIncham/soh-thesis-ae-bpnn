import torch
import numpy as np
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt

def analyze_intrinsic_dimensionality():
    print("1. Loading Raw Interpolated EIS Data...")
    try:
        data = torch.load('Interpolated_EIS_Data.pt', weights_only=True)
        X_raw = data['features'].numpy()
    except FileNotFoundError:
        print("[ERROR] 'Interpolated_EIS_Data.pt' not found. Run Data Interpolation first.")
        return

    print("2. Calculating Intrinsic Dimensionality using PCA...")
    # Initialize PCA without limiting components to see the full variance spectrum
    pca = PCA()
    pca.fit(X_raw)
    
    # Calculate cumulative variance explained by each component
    cumulative_variance = np.cumsum(pca.explained_variance_ratio_)
    
    # Find the exact number of components needed to retain 99% of original information
    target_variance = 0.99
    optimal_components = np.argmax(cumulative_variance >= target_variance) + 1
    
    print("\n=== Data Compression Analysis ===")
    print(f"Original Feature Size: {X_raw.shape[1]}")
    print(f"Components needed for 90% variance: {np.argmax(cumulative_variance >= 0.90) + 1}")
    print(f"Components needed for 95% variance: {np.argmax(cumulative_variance >= 0.95) + 1}")
    print(f"Components needed for 99% variance: {optimal_components}")
    print("=================================")
    print(f"\n[ACADEMIC CONCLUSION]: The optimal AE Bottleneck is {optimal_components}.")
    print("Using more than this captures noise. Using less loses critical DC offset data.")

if __name__ == "__main__":
    analyze_intrinsic_dimensionality()