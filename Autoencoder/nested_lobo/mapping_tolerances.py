# Step 8 (Part E): build tolerance 1/2/3 mapped datasets (log_grid + pchip) with %SOH labels
# Decisions (approved 2026-09-23): Q_ref = mean capacity of first 5 discharge cycles per battery (D1);
# config = log_grid + pchip only (isolate tolerance variable); causal backward matching, no future data.
import numpy as np, pandas as pd, torch, os

AUTO = r"C:\Master Degree\Thesis\Autoencoder"
OUT = os.path.join(AUTO, "nested_lobo")
os.makedirs(OUT, exist_ok=True)

df_cap = pd.read_csv(os.path.join(AUTO, "NASA_Capacity_Data.csv"))
df_cap["Battery_ID"] = df_cap["Battery_ID"].astype(int)
df_cap["Cycle"] = df_cap["Cycle"].astype(int)

qref = df_cap.sort_values("Cycle").groupby("Battery_ID").head(5).groupby("Battery_ID")["Capacity_Ah"].mean()
print("Q_ref (mean of first 5 discharge cycles):")
print(qref.to_string())

eis = torch.load(os.path.join(AUTO, "Interpolated_EIS_log_grid_pchip.pt"), weights_only=True)
X = eis["features"].numpy()
lbl = eis["labels"].numpy().astype(int)
df_eis = pd.DataFrame(lbl, columns=["Battery_ID", "Cycle"])
df_eis["Idx"] = np.arange(len(df_eis))
print(f"\nEIS spectra: {len(df_eis)}  (features {X.shape})")

stats_rows, gap_hist = [], []
for tol in [1, 2, 3]:
    keep_idx, keep_bid, keep_cyc, keep_cap, keep_gap = [], [], [], [], []
    per_batt = {}
    for b in [1, 2, 3, 4]:
        be = df_eis[df_eis.Battery_ID == b].sort_values("Cycle")
        bc = df_cap[df_cap.Battery_ID == b].sort_values("Cycle")
        cap_cyc, cap_val = bc.Cycle.values, bc.Capacity_Ah.values
        n_match, gaps = 0, []
        for _, r in be.iterrows():
            j = np.searchsorted(cap_cyc, r.Cycle, side="right") - 1  # largest capacity cycle <= EIS cycle
            if j >= 0 and r.Cycle - cap_cyc[j] <= tol:               # causal backward, within tolerance
                gap = int(r.Cycle - cap_cyc[j])
                keep_idx += [int(r.Idx)]; keep_bid += [b]; keep_cyc += [int(r.Cycle)]
                keep_cap += [float(cap_val[j])]; keep_gap += [gap]
                n_match += 1; gaps.append(gap)
        per_batt[b] = (len(be), n_match)
        for g, n in pd.Series(gaps).value_counts().items():
            gap_hist.append((tol, b, g, n))
    keep_idx = np.array(keep_idx)
    X_m = X[keep_idx]
    soh = np.array(keep_cap) / keep_bid  # placeholder replaced below
    soh = np.array(keep_cap) / np.array([qref[b] for b in keep_bid]) * 100.0
    torch.save({
        "features": torch.tensor(X_m, dtype=torch.float32),
        "labels": torch.tensor(np.column_stack([keep_bid, keep_cyc, keep_cap, soh]), dtype=torch.float32),
    }, os.path.join(OUT, f"Mapped_EIS_SOH_tol{tol}.pt"))
    s = pd.Series(keep_gap)
    stats_rows.append({"tolerance": tol, "total": len(df_eis), "retained": len(keep_idx),
                       "retention_pct": round(len(keep_idx) / len(df_eis) * 100, 2),
                       "dropped": len(df_eis) - len(keep_idx),
                       "mean_gap": round(float(s.mean()), 3),
                       "soh_min": round(soh.min(), 2), "soh_max": round(soh.max(), 2),
                       **{f"B{b}": f"{per_batt[b][1]}/{per_batt[b][0]}" for b in [1,2,3,4]}})

res = pd.DataFrame(stats_rows)
res.to_csv(os.path.join(OUT, "tolerance_mapping_stats.csv"), index=False)
pd.DataFrame(gap_hist, columns=["tolerance", "battery", "gap_cycles", "count"]).to_csv(
    os.path.join(OUT, "tolerance_gap_distribution.csv"), index=False)
print("\n=== retention + gaps per tolerance ===")
print(res.to_string(index=False))
print("\nNaN check:", sum(np.isnan(keep_cap)) + int(np.isnan(soh).sum()), "| SOH range OK:",
      res.soh_min.min() > 50 and res.soh_max.max() <= 100.001)
