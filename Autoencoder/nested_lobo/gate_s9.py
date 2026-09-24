# Phase C Steps 9-10: validity gate + decision tables
import numpy as np, pandas as pd

HERE = r"C:\Master Degree\Thesis\Autoencoder\nested_lobo"
df = pd.read_csv(f"{HERE}\\steps9_10_results.csv")

print("Gate 1 rows:", len(df), "(expect 72 = 6 pipelines x 12)")
print("Gate 2 NaN:", int(df.isna().sum().sum()))
tr_ok = bool((df.train_R2 > 0.5).all()) if "train_R2" in df.columns else "n/a (not recorded per pipeline)"
print("Gate 3 (test R2 bounds):", df.test_R2.min(), "..", df.test_R2.max(),
      "-> in [-2,1]:", bool(((df.test_R2 >= -2) & (df.test_R2 <= 1)).all()))
per = df.groupby(["pipeline", "test_battery"]).size()
print("Gate 4 per pipeline per battery = 12?", bool((per == 12).all()), "| pipelines:", sorted(df.pipeline.unique()))

print("\nGate 5 === mean +/- std per pipeline (12 runs) ===")
agg = df.groupby("pipeline")[["test_MAE", "test_RMSE", "test_R2", "nRMSE"]].agg(["mean", "std"]).round(3)
print(agg.to_string())

print("\n=== test_R2 by fold ===")
print(df.pivot_table(index="test_battery", columns="pipeline", values="test_R2").round(3).to_string())

print("\n=== working folds only (B0005/06/07) ===")
wf = df[df.test_battery != "B0018"]
wagg = wf.groupby("pipeline")[["test_RMSE", "test_R2"]].agg(["mean", "std"]).round(3)
print(wagg.to_string())

print("\n=== decision (pre-declared) ===")
base = agg[("test_RMSE", "mean")]
print("overall lowest mean RMSE:", base.idxmin(), f"({base.min():.3f})")
wbase = wagg[("test_RMSE", "mean")]
print("working-folds lowest mean RMSE:", wbase.idxmin(), f"({wbase.min():.3f})")
p3w = wf[wf.pipeline == "P3_ae_bpnn"].groupby("test_battery").test_RMSE.mean()
p1w = wf[wf.pipeline == "P1_raw_bpnn"].groupby("test_battery").test_RMSE.mean()
p2w = wf[wf.pipeline == "P2_pca_bpnn"].groupby("test_battery").test_RMSE.mean()
cmp3 = pd.DataFrame({"AE": p3w, "Raw": p1w, "PCA": p2w}).round(3)
print("\nworking-fold RMSE AE vs Raw vs PCA per battery:")
print(cmp3.to_string())
print("AE beats BOTH raw and PCA per working fold:",
      {b: bool(p3w[b] < p1w[b] and p3w[b] < p2w[b]) for b in cmp3.index})
print("\nchosen configs:", df[df.pipeline == "P2_pca_bpnn"].cfg.value_counts().to_dict(),
      "|", df[df.pipeline == "B2_ridge"].cfg.value_counts().to_dict())
print("\nB0018 RMSE per pipeline (mean over seeds):")
print(df[df.test_battery == "B0018"].groupby("pipeline").test_RMSE.mean().round(3).to_string())
