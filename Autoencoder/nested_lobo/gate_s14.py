# Phase C Steps 14-16: validity gate + B6 decision tables
import numpy as np, pandas as pd

HERE = r"C:\Master Degree\Thesis\Autoencoder\nested_lobo"
df = pd.read_csv(f"{HERE}\\steps14_16_results.csv")

print("Gate 1 rows:", len(df), "(expect 60 = 5 pipelines x 12)")
print("Gate 2 NaN:", int(df.isna().sum().sum()))
g3 = bool(((df.test_R2 >= -2) & (df.test_R2 <= 1)).all())
print("Gate 3 test R2 range:", df.test_R2.min(), "..", df.test_R2.max(), "-> in [-2,1]:", g3)
if not g3:
    bad = df[~((df.test_R2 >= -2) & (df.test_R2 <= 1))]
    print(bad[["pipeline","seed","test_battery","cfg","test_RMSE","test_R2"]].to_string(index=False))
per = df.groupby(["pipeline", "test_battery"]).size()
print("Gate 4 all cells == 3:", bool((per == 3).all()))
if not (per == 3).all(): print(per.to_string())

print("\nGate 5 === mean +/- std per pipeline (12 runs, %SOH) ===")
agg = df.groupby("pipeline")[["test_MAE", "test_RMSE", "test_R2", "nRMSE"]].agg(["mean", "std"]).round(3)
print(agg.to_string())

print("\ntest_RMSE by fold:")
print(df.pivot_table(index="test_battery", columns="pipeline", values="test_RMSE").round(3).to_string())
print("\ntest_R2 by fold:")
print(df.pivot_table(index="test_battery", columns="pipeline", values="test_R2").round(3).to_string())

wf = df[df.test_battery != "B0018"]
print("\n=== B6 verdict inputs ===")
print("working folds (B0005/06/07) mean RMSE / R2:")
print(wf.groupby("pipeline")[["test_RMSE", "test_R2"]].mean().round(3).to_string())
b18 = df[df.test_battery == "B0018"]
print("\nB0018 mean RMSE / R2 per pipeline:")
print(b18.groupby("pipeline")[["test_RMSE", "test_R2", "nRMSE"]].mean().round(3).to_string())
print("\nB0018 per-seed rows (TD vs EIS):")
print(b18[b18.pipeline.isin(["TD_ridge","TD_bpnn","P1_raw_bpnn","P3_ae_bpnn"])][
    ["pipeline","seed","test_MAE","test_RMSE","test_R2","nRMSE"]].to_string(index=False))
print("\noverall lowest mean RMSE:", agg[("test_RMSE","mean")].idxmin(), f"({agg[('test_RMSE','mean')].min():.3f})")
print("working-fold lowest mean RMSE:", wf.groupby("pipeline").test_RMSE.mean().idxmin(),
      f"({wf.groupby('pipeline').test_RMSE.mean().min():.3f})")
print("chosen cfg:", df[df.pipeline=="TD_ridge"].cfg.value_counts().to_dict(), "|",
      df[df.pipeline=="TD_bpnn"].cfg.value_counts().to_dict())