# P6-6 figures: support gradient (Fig 2) and alignment-ladder progression (Fig 3).
# Both drawn from existing dumps; no model training.
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ---- Fig 2: MedAE vs number of features outside NASA range (L0 rerun) ----
d = pd.read_csv("phase6_dump_with_support.csv")
d["err"] = (d.yhat - d.y).abs()
g = d.groupby(d.n_out.clip(0, 5)).apply(
    lambda x: pd.Series({"n": len(x), "MedAE": x.err.median(), "MAE": x.err.mean()}),
    include_groups=False)
fig, ax = plt.subplots(figsize=(7, 4))
ax.bar(g.index.astype(str), g.MedAE, color="#4a76a8", width=0.6)
for i, (n, m) in enumerate(zip(g.n, g.MedAE)):
    ax.text(i, m + 0.4, f"n={n:,}", ha="center", fontsize=8)
ax.axhline(19.51, color="gray", ls="--", lw=1, label="overall MedAE 19.5")
ax.set_xlabel("number of Clean-5T features outside the NASA range (per cycle)")
ax.set_ylabel("MedAE (SOH % points)")
ax.set_title("Prediction error vs feature-support violation (BPNN transfer rerun)")
ax.legend(fontsize=8)
fig.tight_layout()
fig.savefig("phase6_support_gradient.png", dpi=150)

# ---- Fig 3: ladder progression ----
labels = ["L0\nno target\ninfo", "La\nrobust", "La\nstandard", "La\nquantile\n(degenerate)",
          "Lb\naffine", "Lc\ncalib\n(non-deg)"]
mae = [20.99, 20.17, 20.51, 6.76, 11.53, 9.24]
colors = ["#888888", "#4a76a8", "#4a76a8", "#b04a4a", "#4a8a5a", "#4a8a5a"]
fig, ax = plt.subplots(figsize=(8, 4.2))
bars = ax.bar(labels, mae, color=colors, width=0.65)
ax.axhline(4.06, color="#b04a4a", ls=":", lw=1.2, label="constant-predictor MAE 4.06")
ax.axhline(2.54, color="#333333", ls="--", lw=1.2, label="within-CALCE ceiling 2.54")
for b, v in zip(bars, mae):
    ax.text(b.get_x() + b.get_width() / 2, v + 0.4, f"{v:.1f}", ha="center", fontsize=9)
ax.set_ylabel("median MAE (SOH % points)")
ax.set_title("Alignment ladder: median MAE by rung (BPNN, 5 seeds)")
ax.legend(fontsize=8)
ax.set_ylim(0, 24)
fig.tight_layout()
fig.savefig("phase6_ladder_progress.png", dpi=150)
print("figures written: phase6_support_gradient.png, phase6_ladder_progress.png")
