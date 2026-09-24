# Phase C: verify all Option-B runs (3 ablations + b7)
import numpy as np, pandas as pd

HERE = r"C:\Master Degree\Thesis\Autoencoder\nested_lobo"

def gate(name, df, expect_rows, expect_cells=None):
    n = len(df)
    nan = int(df.isna().sum().sum())
    g3 = bool(((df.test_R2 >= -2) & (df.test_R2 <= 1)).all())
    r2bad = df[~((df.test_R2 >= -2) & (df.test_R2 <= 1))]
    print(f"[{name}] rows={n}/{expect_rows} NaN={nan} test_R2=[{df.test_R2.min():.3f},{df.test_R2.max():.3f}] in-bounds={g3}")
    if len(r2bad): print("   breaches:", r2bad[["value"] + (["test_battery"] if "test_battery" in r2bad else []) + ["test_R2"]].to_string(index=False))
    if expect_cells:
        per = df.groupby(["value", "test_battery"]).size() if "value" in df else None
        if per is not None:
            ok = bool((per == expect_cells).all())
            print(f"   coverage cells == {expect_cells}: {ok}")
            if not ok: print(per.to_string())
    return df

b = gate("bottleneck", pd.read_csv(f"{HERE}\\abl_bottleneck.csv"), 60, 3)
print("\n=== bottleneck aggregate ===")
print(b.groupby("value")[["test_MAE","test_RMSE","test_R2"]].agg(["mean","std"]).round(3).to_string())

l = gate("loss", pd.read_csv(f"{HERE}\\abl_loss.csv"), 36, 3)
print("\n=== loss aggregate ===")
print(l.groupby("value")[["test_MAE","test_RMSE","test_R2"]].agg(["mean","std"]).round(3).to_string())

i = gate("interp", pd.read_csv(f"{HERE}\\abl_interp.csv"), 72, 3)
print("\n=== interp aggregate (6 configs, tol1) ===")
print(i.groupby("value")[["test_MAE","test_RMSE","test_R2"]].agg(["mean","std"]).round(3).to_string())

r = pd.read_csv(f"{HERE}\\b7_results.csv")
print(f"\n[b7] rows={len(r)}/24 NaN={int(r.isna().sum().sum())}")
print("b7 per-pipeline:")
print(r.groupby("pipeline")[["test_MAE","test_RMSE","test_R2","nRMSE"]].agg(["mean","std"]).round(3).to_string())
print("b7 test_R2 by fold:")
print(r.pivot_table(index="test_battery", columns="pipeline", values="test_R2").round(3).to_string())
print("b7 test_RMSE by fold:")
print(r.pivot_table(index="test_battery", columns="pipeline", values="test_RMSE").round(3).to_string())
print("\nb7 summary csv exists:", pd.read_csv(f"{HERE}\\b7_summary.csv").shape)