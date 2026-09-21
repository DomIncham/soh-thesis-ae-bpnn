import torch
import numpy as np
import pandas as pd
import os
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import MinMaxScaler

def run_stage2_target_scaling():
    print("="*85)
    print("Stage 2: Target Scaling Validation (MinMaxScaler on Y)")
    print("Rule: Fit Scaler strictly on Train Set to prevent Future Leakage")
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
    
    # Reshape Y for Scaler
    y_train_raw = y_capacity[train_mask].reshape(-1, 1)
    y_test_raw = y_capacity[test_mask].reshape(-1, 1)

    # 3. Prevent Data Leakage: Scale X and Y fitted ONLY on Train
    scaler_X = MinMaxScaler()
    X_train_scaled = scaler_X.fit_transform(X_train_raw)
    X_test_scaled = scaler_X.transform(X_test_raw)

    scaler_Y = MinMaxScaler()
    y_train_scaled = scaler_Y.fit_transform(y_train_raw).flatten()
    # Note: We scale Y_test just for reference, but metrics must be evaluated on original scale
    y_test_scaled = scaler_Y.transform(y_test_raw).flatten() 

    # 4. Define Simple Models
    models = {
        "Linear Regression (Scaled Y)": LinearRegression(),
        "Ridge (L2=1.0) (Scaled Y)": Ridge(alpha=1.0),
        "Random Forest (Scaled Y)": RandomForestRegressor(n_estimators=100, random_state=42)
    }

    results = []

    # 5. Train, Predict, and INVERSE TRANSFORM before Evaluation
    for name, model in models.items():
        # Train on scaled features and scaled targets
        model.fit(X_train_scaled, y_train_scaled)
        
        # Predict (Outputs are in 0-1 scale)
        tr_preds_scaled = model.predict(X_train_scaled).reshape(-1, 1)
        te_preds_scaled = model.predict(X_test_scaled).reshape(-1, 1)
        
        # Inverse Transform back to Physical Scale (Ah)
        tr_preds_ah = scaler_Y.inverse_transform(tr_preds_scaled).flatten()
        te_preds_ah = scaler_Y.inverse_transform(te_preds_scaled).flatten()
        
        # Evaluate on Original Scale
        y_train_ah = y_train_raw.flatten()
        y_test_ah = y_test_raw.flatten()
        
        tr_rmse = np.sqrt(mean_squared_error(y_train_ah, tr_preds_ah))
        te_rmse = np.sqrt(mean_squared_error(y_test_ah, te_preds_ah))
        
        tr_r2 = r2_score(y_train_ah, tr_preds_ah)
        te_r2 = r2_score(y_test_ah, te_preds_ah)
        
        results.append({
            "Model": name,
            "Train RMSE (Ah)": tr_rmse,
            "Train R2": tr_r2,
            "Test RMSE (Ah)": te_rmse,
            "Test R2": te_r2,
            "Gap (Test-Train RMSE)": te_rmse - tr_rmse
        })

    # 6. Display Results
    df_results = pd.DataFrame(results)
    print("\n--- STAGE 2: DUMMY BASELINE WITH TARGET SCALING ---")
    print(df_results.to_markdown(index=False))
    print("="*85)

if __name__ == "__main__":
    run_stage2_target_scaling()