
import pandas as pd
df = pd.read_csv(r"C:\Master Degree\Thesis\Autoencoder\nested_lobo\steps9_10_results.csv")
per = df.groupby(["pipeline","test_battery"]).size()
print(per.to_string())
print("all cells == 3:", bool((per == 3).all()))
bad = df[(df.test_R2 < -2)]
print("Gate3 breach rows:"); print(bad[["pipeline","seed","test_battery","cfg","test_RMSE","test_R2"]].to_string(index=False))
