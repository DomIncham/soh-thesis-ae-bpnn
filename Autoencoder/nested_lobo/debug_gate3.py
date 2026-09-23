import pandas as pd
df = pd.read_csv(r"C:\Master Degree\Thesis\Autoencoder\nested_lobo\nested_lobo_results.csv")
bad = df[(df.train_R2 <= 0.5) | (df.test_R2 < -2)]
cols = ["tolerance","seed","test_battery","bpnn_arch","bpnn_l2","ae_epochs","train_R2","test_MAE","test_RMSE","test_R2"]
print(bad[cols].to_string(index=False))
print("\nB0018 rows:")
print(df[df.test_battery=="B0018"][["tolerance","seed","test_R2","test_RMSE"]].to_string(index=False))
