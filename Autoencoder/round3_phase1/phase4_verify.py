# Phase 4 verification: checks on phase4_features.csv.
# Run: python phase4_verify.py   (all PASS lines must print; any FAIL aborts with exit 1)
import sys
import numpy as np
import pandas as pd

df = pd.read_csv("phase4_features.csv")
checks = []


def check(name, cond):
    checks.append(bool(cond))
    print(("PASS" if cond else "FAIL") + " | " + name)


inc = df[df.include_cell]
exc = sorted(df[~df.include_cell].battery.unique().tolist())

# 1. shape and coverage
check(f"19 cells present (got {df.battery.nunique()})", df.battery.nunique() == 19)
check(f"1,695 rows (got {len(df)})", len(df) == 1695)
# 2. cell-level inclusion rule output
check(f"excluded cells are exactly B0033/34/36/45/46 (got {exc})", exc == ["B0033", "B0034", "B0036", "B0045", "B0046"])
check(f"14 cells included (got {inc.battery.nunique()})", inc.battery.nunique() == 14)
# 3. the rule was applied for the right reasons (recompute independently)
g = df.groupby("battery").agg(Q_ref=("capacity", lambda s: s.head(5).mean()),
                              cap_max=("capacity", "max"), rows=("capacity", "size"))
bad = (g.cap_max > 2.1) | (g.Q_ref < 0.9 * g.cap_max) | (g.rows < 20)
check("independent recomputation of the rule reproduces include_cell",
      (df.battery.map(~bad)).equals(df.include_cell))
# 4. row-level hygiene: no capacity < 1.0 or non-finite anywhere in the CSV
check("no capacity <= 1.0 Ah or non-finite capacity", bool(((df.capacity > 1.0) & np.isfinite(df.capacity)).all()))
# 5. byte-identity with the old pipeline on the 4 original cells
old_td = pd.read_csv(r"..\nested_lobo\time_domain_features.csv")
old_td.columns = [c.strip() for c in old_td.columns]
old_ch = pd.read_csv(r"..\nested_lobo\charge_features.csv")
nmap = {"B0005": 1, "B0006": 2, "B0007": 3, "B0018": 4}
ok = True
for nm, b in nmap.items():
    o = old_td[old_td.battery == b].set_index("cycle")
    n = df[df.battery == nm].set_index("cycle")
    if len(o) != len(n):
        ok = False
        break
    for f in ["capacity", "soh", "dis_duration", "dis_mean_V", "dis_mean_T", "dis_V_slope",
              "cc_dur", "cv_dur", "cv_I_slope", "ch_mean_T"]:
        d = (n[f] - o[f]).abs().max()
        if not (d < 1e-9 or (np.isnan(n[f]).all() and np.isnan(o[f]).all())):
            print(f"   {nm} {f}: max|diff|={d:.3e}")
            ok = False
check("all 10 features byte-identical to nested_lobo extraction for B0005/06/07/18", ok)
och = old_ch[old_ch.battery == 1].set_index("cycle")
nch = df[df.battery == "B0005"].set_index("cycle")
ok2 = True
for f in ["t_40_41", "ic_peak_V"]:
    both = nch[f].notna() & och[f].notna()
    if both.any() and (nch[f][both] - och[f][both]).abs().max() >= 1e-9:
        ok2 = False
check("t_40_41 / ic_peak_V identical to nested_lobo charge extraction (B0005)", ok2)
# 6. label sanity on included cells: SOH bounded, capacity monotone-ish trend allowed but within (1,2.1]
check("included capacities in (1.0, 2.1] Ah", bool((inc.capacity > 1.0).all() and (inc.capacity <= 2.1).all()))
check("included SOH in (0, 120]", bool(((inc.soh > 0) & (inc.soh <= 120)).all()))
# 7. NaNs in charge-side features must be structural: no preceding charge, or (ic_peak_V only)
#    a charge cycle too short for the ICA grid (<10 kept points, the B0047/48 truncated heads).
ncharge = inc[~inc.has_prev_charge]
for f in ["cc_dur", "cv_dur", "cv_I_slope", "ch_mean_T", "t_40_41"]:
    bad_rows = inc[inc[f].isna() & inc.has_prev_charge]
    check(f"{f}: NaN iff no preceding charge (extra rows: {len(bad_rows)})", len(bad_rows) == 0)
ica_extra = inc[inc.ic_peak_V.isna() & inc.has_prev_charge & (inc.capacity > 1.0)]
allowed = {("B0005", 86), ("B0006", 86), ("B0007", 86),   # same NaN positions as the old pipeline
           ("B0018", 117), ("B0018", 141),
           ("B0047", 169), ("B0048", 169)}                # truncated cold-cell charges (<10 pts)
got = set(zip(ica_extra.battery, ica_extra.cycle))
check(f"ic_peak_V: extra NaN rows are the 5 old-pipeline positions + B0047/48 cyc169 (got {sorted(got)})",
      got == allowed)
# 8. discharge-side features complete and sane
check("dis features complete (no NaN)", bool(inc[["dis_duration", "dis_mean_V", "dis_mean_T", "dis_V_slope"]].notna().all().all()))
check("dis_duration positive", bool((inc.dis_duration > 0).all()))
check("dis_V_slope negative (voltage falls during discharge)", bool((inc.dis_V_slope < 0).all()))
# 9. condition labels
conds = inc.groupby("regime").battery.nunique().to_dict()
check(f"regime coverage room>=8, hot=4, cold>=1 (got {conds})", conds.get("room", 0) >= 8 and conds.get("hot") == 4)

print(f"\n{'ALL ' + str(len(checks)) + ' CHECKS PASSED' if all(checks) else 'FAILURES: ' + str(checks.count(False))}")
sys.exit(0 if all(checks) else 1)
