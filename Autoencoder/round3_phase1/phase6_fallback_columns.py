# P6 pre-report columns: add explicit fallback_rate to every ladder/ridge results CSV so
# every table in the Round 6 report can show "Fallback %" directly (R6-C4).
# - Ladder CSVs (La/Lb/Lc): fallback_rate = sel_degenerate (0.80, source-side selection).
# - Ridge CSVs: fallback_rate = "N/A (deterministic)" (Ridge has no NN selection step).
# No model training; CSV-level column addition only.
import pandas as pd

FB = 0.80
for f in ["phase6_ladder_La.csv", "phase6_ladder_Lb.csv", "phase6_ladder_Lc.csv"]:
    df = pd.read_csv(f)
    if "fallback_rate" not in df.columns:
        df["fallback_rate"] = FB
        df.to_csv(f, index=False)
    print(f, "fallback_rate mean:", df.fallback_rate.mean() if "fallback_rate" in df.columns else "ADDED")

for f in ["phase6_ridge_transfer.csv", "phase6_ridge_within.csv"]:
    df = pd.read_csv(f)
    if "fallback_rate" not in df.columns:
        df["fallback_rate"] = "N/A (deterministic)"
        df.to_csv(f, index=False)
    print(f, "fallback_rate added: N/A (deterministic)")
print("done")
