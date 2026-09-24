# Step 12 evidence collection: quantify the old Figure 10 collapse from existing artifacts
import numpy as np, pandas as pd

BASE = r"C:\Master Degree\Thesis\NASA DataSet\1. BatteryAgingARC-FY08Q4"
AUTO = r"C:\Master Degree\Thesis\Autoencoder"
NL = r"C:\Master Degree\Thesis\Autoencoder\nested_lobo"

# 1) old Figure 10 numbers (advisor Part G1) vs B0018 capacity statistics
cap = pd.read_csv(f"{BASE}\\NASA_Capacity_Data.csv")
cap["Battery_ID"] = cap.Battery_ID.astype(int); cap["Cycle"] = cap.Cycle.astype(int)
b18 = cap[cap.Battery_ID == 4].sort_values("Cycle")
std18, mean18 = b18.Capacity_Ah.std(), b18.Capacity_Ah.mean()
old_rmse, old_r2 = 0.1744, -0.029
print(f"B0018 capacity: n={len(b18)} mean={mean18:.4f} std={std18:.4f} Ah range=[{b18.Capacity_Ah.min():.3f},{b18.Capacity_Ah.max():.3f}]")
print(f"old Fig10: RMSE={old_rmse} R2={old_r2}")
print(f"check: RMSE/std(y) = {old_rmse/std18:.4f}  (== ~1.0 means prediction ~ constant)")
print(f"implied var(pred) from R2: R2 = 1 - MSE/var(y) -> MSE={old_rmse**2:.5f}, var(y)={std18**2:.5f}")
# for a constant predictor c: MSE = var(y) + (c-mean)^2 -> implied |c - mean|
imp_shift = np.sqrt(max(old_rmse**2 - std18**2, 0))
print(f"implied |constant - mean(y)| = {imp_shift:.4f} Ah  (old predictor behaves like a flat line this far from the mean)")

# 2) old BPNN grid search: train vs test gap (single split, Ah target)
gs = pd.read_csv(f"{AUTO}\\BPNN_Baseline_GridSearch_Results.csv")
print(f"\nold grid search (B0018 as fixed test, Ah target, 300 epochs):")
print(f"  Train R2: {gs.Train_R2.min():.3f}..{gs.Train_R2.max():.3f} | Test R2: {gs.Test_R2.min():.3f}..{gs.Test_R2.max():.3f}")
print(f"  Train RMSE: {gs.Train_RMSE.min():.3f}..{gs.Train_RMSE.max():.3f} | Test RMSE: {gs.Test_RMSE.min():.3f}..{gs.Test_RMSE.max():.3f}")

# 3) R1 latent-correlation evidence (correlation flip)
try:
    lc = pd.read_csv(f"{AUTO}\\Latent_Correlation_Metrics.csv")
    print("\nLatent_Correlation_Metrics.csv columns:", list(lc.columns))
    print(lc.head(10).to_string(index=False))
except Exception as e:
    print("latent csv:", e)

# 4) new-protocol contrast numbers (Steps 7-10 full runs)
res78 = pd.read_csv(f"{NL}\\nested_lobo_results.csv")
res78 = res78[res78.tolerance.astype(str) == "1"]
res9 = pd.read_csv(f"{NL}\\steps9_10_results.csv")
p3 = res9[res9.pipeline == "P3_ae_bpnn"]
print("\nnew protocol (tol1): per-fold test R2 (AE->BPNN), mean over seeds:")
print(p3.groupby("test_battery").test_R2.mean().round(3).to_string())
