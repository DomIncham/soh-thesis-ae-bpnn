import torch
import numpy as np
import pandas as pd
import os
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import MinMaxScaler

def run_dummy_baseline():
    print("="*85)
    print("Stage 1: Dummy Baseline Validation (Sanity Check)")
    print("Models: Linear Regression, Ridge (L2), Random Forest")
    print("Validation: Strict LOBO on B0018")
    print("="*85)

    dataset_file = 'Mapped_EIS_SOH_log_grid_pchip.pt'
    if not os.path.exists(dataset_file):
        print(f"[ERROR] Required dataset '{dataset_file}' not found.")
        return

    # 1. Load Data
    data = torch.load(dataset_file, weights_only=True)
    X_raw = data['features'].numpy()
    y_meta = data['labels'].numpy()

    battery_ids = y_meta[:, 0].astype(int)
    y_capacity = y_meta[:, 2]

    # 2. Strict LOBO Split
    target_test_battery = 4
    train_mask = (battery_ids != target_test_battery)
    test_mask = (battery_ids == target_test_battery)

    X_train_raw = X_raw[train_mask]
    X_test_raw = X_raw[test_mask]
    y_train = y_capacity[train_mask]
    y_test = y_capacity[test_mask]

    # 3. Prevent Data Leakage: Scale X fitted only on Train
    scaler_X = MinMaxScaler()
    X_train_scaled = scaler_X.fit_transform(X_train_raw)
    X_test_scaled = scaler_X.transform(X_test_raw)

    # 4. Define Simple Models
    models = {
        "Linear Regression": LinearRegression(),
        "Ridge (L2=1.0)": Ridge(alpha=1.0),
        "Random Forest": RandomForestRegressor(n_estimators=100, random_state=42)
    }

    results = []

    # 5. Train and Evaluate
    for name, model in models.items():
        model.fit(X_train_scaled, y_train)
        
        tr_preds = model.predict(X_train_scaled)
        te_preds = model.predict(X_test_scaled)
        
        tr_rmse = np.sqrt(mean_squared_error(y_train, tr_preds))
        te_rmse = np.sqrt(mean_squared_error(y_test, te_preds))
        
        tr_r2 = r2_score(y_train, tr_preds)
        te_r2 = r2_score(y_test, te_preds)
        
        results.append({
            "Model": name,
            "Train RMSE": tr_rmse,
            "Train R2": tr_r2,
            "Test RMSE": te_rmse,
            "Test R2": te_r2,
            "Gap (Test - Train RMSE)": te_rmse - tr_rmse
        })

    # 6. Display Results
    df_results = pd.DataFrame(results)
    print("\n--- DUMMY BASELINE RESULTS ---")
    print(df_results.to_markdown(index=False))
    print("="*85)

if __name__ == "__main__":
    run_dummy_baseline()