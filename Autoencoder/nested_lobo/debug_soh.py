# debug: per-battery SOH stats from tol3 mapped dataset — find SOH<70 and >100 sources
import torch, numpy as np, pandas as pd
d = torch.load(r"C:\Master Degree\Thesis\Autoencoder\nested_lobo\Mapped_EIS_SOH_tol3.pt", weights_only=True)
y = d["labels"].numpy()
df = pd.DataFrame(y, columns=["bid", "cycle", "cap", "soh"])
df["bid"] = df.bid.astype(int); df["cycle"] = df.cycle.astype(int)
for b, g in df.groupby("bid"):
    lo = g.nsmallest(3, "soh")[["cycle", "cap", "soh"]]
    hi = g.nlargest(2, "soh")[["cycle", "cap", "soh"]]
    print(f"B{b:04d}: n={len(g)} soh min={g.soh.min():.2f} max={g.soh.max():.2f} | cycles SOH<70: "
          f"{sorted(g[g.soh < 70].cycle.tolist())[:12]} | lowest3:\n{lo.to_string(index=False)}\n highest2:\n{hi.to_string(index=False)}\n")

# cross-check vs capacity CSV: is cap at the flagged cycles real?
cap = pd.read_csv(r"C:\Master Degree\Thesis\Autoencoder\NASA_Capacity_Data.csv")
cap["Battery_ID"] = cap.Battery_ID.astype(int); cap["Cycle"] = cap.Cycle.astype(int)
for b in [1, 2, 3, 4]:
    g = cap[cap.Battery_ID == b].sort_values("Cycle")
    print(f"B{b:04d} capacity: n={len(g)} first5mean={g.head(5).Capacity_Ah.mean():.4f} "
          f"min={g.Capacity_Ah.min():.4f} @cycle {g.loc[g.Capacity_Ah.idxmin(), 'Cycle']} "
          f"max={g.Capacity_Ah.max():.4f} @cycle {g.loc[g.Capacity_Ah.idxmax(), 'Cycle']}")
