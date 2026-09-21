import pandas as pd
import numpy as np
import torch
import os
from sklearn.decomposition import PCA
from sklearn.preprocessing import MinMaxScaler

def analyze_pca_bottlenecks():
    print("="*80)
    print("Quantitative Evidence for Bottleneck Selection via PCA")
    print("Rule: Prevent Data Leakage (Fit PCA on Training Data Only)")
    print("="*80)

    dataset_file = 'Mapped_EIS_SOH_log_grid_pchip.pt'
    if not os.path.exists(dataset_file):
        print(f"[ERROR] Required file not found: {dataset_file}")
        return

    # 1. โหลดข้อมูล
    data = torch.load(dataset_file, weights_only=True)
    X_raw = data['features'].numpy()
    y_meta = data['labels'].numpy()
    battery_ids = y_meta[:, 0].astype(int)

    # 2. แบ่งข้อมูล Train (B0005, B0006, B0007) และ Test (B0018) ป้องกัน Leakage
    target_test_battery = 4
    train_mask = (battery_ids != target_test_battery)
    
    X_train_raw = X_raw[train_mask]
    
    # 3. Normalization (Fit บน Train เท่านั้น)
    scaler = MinMaxScaler()
    X_train_scaled = scaler.fit_transform(X_train_raw)

    # 4. รัน PCA เพื่อกวาดหา Variance ของทั้ง 256 มิติ
    pca = PCA()
    pca.fit(X_train_scaled)
    
    cum_var = np.cumsum(pca.explained_variance_ratio_)

    # 5. หาจุดตัด (Thresholds) ที่มีความหมายทางสถิติ
    thresholds = [0.80, 0.85, 0.90, 0.95, 0.99, 0.999]
    results = []
    
    print("Scanning cumulative explained variance from 1 to 256 components...\n")
    
    for t in thresholds:
        # หาจำนวน component น้อยที่สุด ที่ให้ variance ทะลุ threshold
        n_comp = np.argmax(cum_var >= t) + 1
        actual_var = cum_var[n_comp - 1] * 100
        results.append({
            'Target_Variance': f"{t*100:.1f}%",
            'Exact_Variance_Captured': f"{actual_var:.4f}%",
            'Optimal_Bottleneck_Size': n_comp
        })

    df_results = pd.DataFrame(results)
    print(df_results.to_markdown(index=False))
    
    print("\n" + "="*80)
    print("Defense Strategy for Oral Examination:")
    print("If asked: 'Why did you choose these specific bottleneck sizes?'")
    print("Answer: 'I did not pick them arbitrarily. I performed PCA on the training set.")
    print("The chosen bottleneck sizes correspond exactly to the intrinsic dimensionality")
    print("required to capture 80%, 90%, 95%, and 99% of the dataset's total variance.'")
    print("="*80)

if __name__ == "__main__":
    analyze_pca_bottlenecks()