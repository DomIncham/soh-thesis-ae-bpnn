# Round 6, R6-C2 step 3: feature-support split diagnosis.
# Question (advisor): is FEATURE-range extrapolation driving the NASA->CALCE failure?
# Design (approved 2026-10-21, plan A+C):
#   - Primary split: strict per-feature min-max — a CALCE row is INSIDE iff all 5
#     Clean-5T features lie within the NASA training range (min..max of include_cell rows);
#     OUTSIDE if >=1 feature falls outside.
#   - Secondary: fraction-of-features-outside (continuity 0..5).
#   - Metrics per group: MAE, MedAE, P90(|err|) (robust — plan A), plus
#     frac(|err|>50%) and frac(yhat>115) (outlier/exploding-prediction decomposition — plan C).
#   - Per-cell table joins the split fractions with P6-1 shift stats.
# Inputs: phase4_features.csv (NASA), phase4_cs2_features.csv (CALCE), phase6_preds_transfer_full.csv
#         phase6_feature_shift.csv (P6-1 stats for the per-cell join)
# Row set: identical to the P6-2 dump (CALCE include_cell & cap_ok, Clean-5T features; 49,220 rows).
# Outputs: phase6_support_split.csv (per pool/seed x group), phase6_support_split_cells.csv,
#          phase6_support_split_summary.md
# Diagnostic only — no model is trained here (R6-C2.3).
import numpy as np
import pandas as pd
from scipy import stats

FEATS = ["dis_V_slope", "cc_dur", "cv_dur", "cv_I_slope", "ic_peak_V"]

nasa = pd.read_csv("phase4_features.csv")
nasa = nasa[nasa.include_cell].dropna(subset=FEATS).reset_index(drop=True)
cs2 = pd.read_csv("phase4_cs2_features.csv")
cs2 = cs2[cs2.include_cell & cs2.cap_ok].dropna(subset=FEATS).reset_index(drop=True)
dump = pd.read_csv("phase6_preds_transfer_full.csv")

rng = {f: (nasa[f].min(), nasa[f].max()) for f in FEATS}

# per-cycle support flags, keyed by (cell, dump_position) - the dump "cycle" column is the
# 1-based position within the cell in the filtered+reset_index order of phase5.pools(), NOT
# the raw cycle number (verified: per-cell dump counts == filtered per-cell counts, 1..N).
flags = np.zeros((len(cs2), len(FEATS)), dtype=bool)
for j, f in enumerate(FEATS):
    lo, hi = rng[f]
    flags[:, j] = (cs2[f].values < lo) | (cs2[f].values > hi)
sup = pd.DataFrame({"cell": cs2.battery.values,
                    "cycle": cs2.groupby(cs2.battery.values).cumcount() + 1,
                    "n_out": flags.sum(axis=1)})
sup["cell"] = sup.cell.astype(str)
dump["cycle"] = pd.to_numeric(dump.cycle)
d = dump.merge(sup, on=["cell", "cycle"], how="left")
assert d.n_out.notna().all(), "unmatched rows: dump cell/cycle keys vs feature table"
d["group"] = np.where(d.n_out == 0, "inside", "outside")

def metrics(x):
    err = (x.yhat - x.y).abs()
    return pd.Series({
        "n": len(x), "MAE": err.mean(), "MedAE": err.median(),
        "P90err": err.quantile(0.9),
        "frac_err_gt50": (err > 50).mean(),
        "frac_yhat_over115": (x.yhat > 115).mean()})

rows = []
for (pool, seed), g in d.groupby(["pool", "seed"]):
    for grp, gg in g.groupby("group"):
        m = metrics(gg)
        rows.append(dict(pool=pool, seed=seed, group=grp, **{k: round(v, 3) for k, v in m.items()}))
split = pd.DataFrame(rows)
# R6-C4: fallback rate recorded as an explicit column on every row (not just a narrative
# footnote). Rate comes from the underlying P6-2 rerun (sel_degenerate = 0.80), applies to
# both support groups equally since selection is source-side only.
split["fallback_rate"] = 0.80
split["fallback_note"] = "sel_degenerate rate of underlying P6-2 rerun; applies to both groups"
split.to_csv("phase6_support_split.csv", index=False)
print("=== per pool/seed x group ===")
print(split.to_string(index=False))

agg = split.groupby("group")[["n", "MAE", "MedAE", "P90err", "frac_err_gt50",
                              "frac_yhat_over115"]].mean().round(3)
print("\n=== mean across seeds ===")
print(agg.to_string())

# per-cell table: support fraction + error profile + P6-1 join
cell_rows = []
for cell, g in d.groupby("cell"):
    m = metrics(g)
    cell_rows.append(dict(cell=cell,
                          pct_rows_inside=round((g.n_out == 0).mean() * 100, 1),
                          mean_n_out=round(g.n_out.mean(), 2), **{k: round(v, 3) for k, v in m.items()}))
cells = pd.DataFrame(cell_rows)
p61 = pd.read_csv("phase6_feature_shift.csv")
severity = p61.pct_outside_nasa.max()  # max across features (CC/CV dominate ~93-100%)
cells["p61_max_outside"] = severity
cells.to_csv("phase6_support_split_cells.csv", index=False)
print("\n=== per cell ===")
print(cells.to_string(index=False))

corr = stats.spearmanr(cells.MedAE, cells.mean_n_out)
print(f"\nSpearman(MedAE, mean features-outside per row) = {corr.statistic:.3f} (p={corr.pvalue:.4f})")

# one number the report needs: how much of the failure is feature-support related?
overall = metrics(d)
inside = metrics(d[d.group == "inside"])
outside = metrics(d[d.group == "outside"])
lines = [
    "# Phase 6 support-split summary (R6-C2.3, diagnostic only)", "",
    f"Row set: CALCE include_cell & cap_ok, Clean-5T, {len(d):,} dump rows x 10 (pool,seed) runs.",
    "Inside = all 5 features within NASA min-max; Outside = >=1 feature outside (strict per-feature).", "",
    f"- Overall: MAE {overall.MAE:.2f}%, MedAE {overall.MedAE:.2f}%, frac(yhat>115%) {overall.frac_yhat_over115:.2f}",
    f"- INSIDE  ({inside.n:,} rows): MAE {inside.MAE:.2f}, MedAE {inside.MedAE:.2f}, P90 {inside.P90err:.2f}, "
    f"frac(yhat>115) {inside.frac_yhat_over115:.3f}",
    f"- OUTSIDE ({outside.n:,} rows): MAE {outside.MAE:.2f}, MedAE {outside.MedAE:.2f}, P90 {outside.P90err:.2f}, "
    f"frac(yhat>115) {outside.frac_yhat_over115:.3f}",
    f"- Spearman(cell MedAE, mean n-features-outside) = {corr.statistic:.3f}", "",
    "Reading: compare MedAE/P90 between groups — if OUTSIDE is markedly worse, feature-range",
    "extrapolation drives the transfer failure (R6-C2.3). Fallback context (R6-C4): selection",
    "fallback rate 0.80 in the underlying rerun applies to BOTH groups equally."]
with open("phase6_support_split_summary.md", "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines) + "\n")
print("\nWrote phase6_support_split.csv, phase6_support_split_cells.csv, "
      "phase6_support_split_summary.md")
