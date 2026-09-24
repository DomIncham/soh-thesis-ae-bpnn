# Step 18: regenerate summary figures from the actual results CSVs (corrected pipeline)
import os
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figures")
os.makedirs(HERE, exist_ok=True)

s9 = pd.read_csv(os.path.join(os.path.dirname(HERE), "steps9_10_results.csv"))
s14 = pd.read_csv(os.path.join(os.path.dirname(HERE), "steps14_16_results.csv"))
s14 = s14[s14.pipeline.isin(["TD_ridge", "TD_bpnn"])]
df = pd.concat([s9, s14], ignore_index=True)
order = ["B1_mean", "B2_ridge", "P1n_rowminmax_bpnn", "P1_raw_bpnn", "P2_pca_bpnn", "P3_ae_bpnn", "TD_ridge", "TD_bpnn"]
folds = ["B0005", "B0006", "B0007", "B0018"]
colors = {"B1_mean": "0.6", "B2_ridge": "tab:brown", "P1n_rowminmax_bpnn": "tab:gray",
          "P1_raw_bpnn": "tab:orange", "P2_pca_bpnn": "tab:green", "P3_ae_bpnn": "tab:red",
          "TD_ridge": "tab:blue", "TD_bpnn": "tab:purple"}

# Figure R1: per-fold test R2, grouped bars
fig, ax = plt.subplots(figsize=(13, 5))
w, offs = 0.11, np.arange(len(folds))
for i, p in enumerate(order):
    vals = [df[(df.pipeline == p) & (df.test_battery == f)].test_R2.mean() for f in folds]
    ax.bar(offs + i * w, vals, w, label=p, color=colors[p])
ax.axhline(0, color="k", lw=0.8)
ax.set_xticks(offs + 3.5 * w); ax.set_xticklabels(folds)
ax.set_ylabel("test R² (%SOH, mean of 3 seeds)")
ax.set_title("Per-fold test R² under the corrected nested-LOBO protocol (Steps 7–16)")
ax.legend(fontsize=8, ncol=4); ax.grid(axis="y", alpha=0.3)
plt.tight_layout(); plt.savefig(os.path.join(HERE, "R1_per_fold_R2.png"), dpi=150)
print("saved R1_per_fold_R2.png")

# Figure R2: overall RMSE ranking with std error bars
agg = df.groupby("pipeline").test_RMSE.agg(["mean", "std"]).reindex(order)
fig, ax = plt.subplots(figsize=(9, 4.5))
ax.barh(range(len(agg)), agg["mean"], xerr=agg["std"], color=[colors[p] for p in agg.index])
ax.set_yticks(range(len(agg))); ax.set_yticklabels(agg.index)
ax.invert_yaxis(); ax.set_xlabel("test RMSE (%SOH), mean ± std over 12 runs")
ax.set_title("Overall accuracy ranking (lower is better)")
for i, (m, s) in enumerate(zip(agg["mean"], agg["std"])):
    ax.text(m + s + 0.15, i, f"{m:.2f}", va="center", fontsize=8)
ax.grid(axis="x", alpha=0.3)
plt.tight_layout(); plt.savefig(os.path.join(HERE, "R2_rmse_ranking.png"), dpi=150)
print("saved R2_rmse_ranking.png")
print(agg.round(2).to_string())