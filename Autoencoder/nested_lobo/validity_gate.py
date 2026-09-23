# Phase C: Validity Gate (6 checks) + tolerance decision table from full run
import numpy as np, pandas as pd

HERE = r"C:\Master Degree\Thesis\Autoencoder\nested_lobo"
df = pd.read_csv(f"{HERE}\\nested_lobo_results.csv")

# Gate 1-2: run completed + no NaN
print("Gate 1 rows:", len(df), "(expect 48 = 4 tol x 3 seeds x 4 folds)")
nan = df.isna().sum().sum()
print("Gate 2 NaN cells:", nan, "->", "PASS" if nan == 0 else "FAIL")

# Gate 3: R2 sanity: train > 0.5 and -2 <= test <= 1
tr_ok = bool((df.train_R2 > 0.5).all())
te_ok = bool(((df.test_R2 >= -2) & (df.test_R2 <= 1)).all())
print(f"Gate 3 train R2 min={df.train_R2.min():.3f} (>0.5: {tr_ok}) | test R2 range "
      f"[{df.test_R2.min():.3f}, {df.test_R2.max():.3f}] (in [-2,1]: {te_ok})")

# Gate 4: metrics complete per battery
per = df.groupby("test_battery").size()
print("Gate 4 rows per test battery:\n", per.to_string(), "\nPASS" if (per == 12).all() else "CHECK")

# Gate 5: mean +/- std per tolerance
agg = df.groupby("tolerance")[["test_MAE", "test_RMSE", "test_R2", "train_R2", "val_rmse_soh"]].agg(["mean", "std"]).round(3)
print("\nGate 5 === aggregate per tolerance (12 runs each: 4 folds x 3 seeds) ===")
print(agg.to_string())

# Decision (pre-declared rules): lowest mean test_RMSE; if within 1 std -> lowest tolerance
base = agg[("test_RMSE", "mean")]
winner = base.idxmin()
rmse_w = base[winner]
within = [t for t in base.index if base[t] - rmse_w <= agg.loc[t, ("test_RMSE", "std")]]
within_num = sorted([t for t in within if isinstance(t, (int, np.integer))])
print(f"\nGate 6 decision: lowest mean RMSE = tol {winner} ({rmse_w:.3f} %SOH)")
print(f"tolerances within 1 std of winner: {within}")
print(f"-> numeric tolerances within 1 std: {within_num} -> rule: prefer lowest =", within_num[0] if within_num else winner)

# fold breakdown for report
piv = df.pivot_table(index="test_battery", columns="tolerance", values="test_RMSE").round(3)
print("\ntest_RMSE by fold (rows=fold's test battery):")
print(piv.to_string())
piv2 = df.pivot_table(index="test_battery", columns="tolerance", values="test_R2").round(3)
print("\ntest_R2 by fold:")
print(piv2.to_string())
# chosen configs
print("\nchosen BPNN arch counts:", df.bpnn_arch.value_counts().to_dict())
print("chosen L2 counts:", df.bpnn_l2.value_counts().to_dict())
print("AE epochs (early stop) mean per tolerance:",
      df.groupby("tolerance").ae_epochs.mean().round(0).to_dict())
