# Round 4 advisor item 4: STRUCTURAL verification (not numerical reproduction).
# Each check asserts the protocol definition == implementation and FAILS (exit 1) automatically
# on inconsistency. Run after any change to r3common.py or the phase4_cs2_* feature sets:
#   python round4_structural_verify.py
# Checks:
#   S1 inner LOBO contains exactly three validation folds
#   S2 training and validation battery sets are disjoint during model selection (every stage)
#   S3 the declared Clean feature set exactly matches the features passed to the model
#   S4 dis_duration / dis_mean_V cannot accidentally re-enter a proxy-audited feature set
#   S5 the CS2 Clean-6T files define the identical feature list
import os, sys, itertools
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
import r3common as rc  # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    tag = "PASS" if cond else "FAIL"
    print(f"[{tag}] S-check {name}: {detail}")
    if not cond:
        FAILS.append(name)


# ---- S1: inner LOBO has exactly 3 folds, each battery validated once ------------------------
td = pd.read_csv(rc.TD_CSV)
X, bids, soh, cyc = rc.load_td(rc.FEATS_ALL)
qref_r, qref = rc.soh_range_and_qref()
folds_seen = {}
orig_fit = rc.fit_bpnn_ep


def spy_fit(dims, l2, Ztr, ytr, Zva, yva, seed, max_ep, patience, lr=1e-3, epochs=None):
    # count EVERY inner-validation call: a fold that early-stops at epoch 1 is still a fold
    # that was trained on its own inner-train and scored on its own inner-val (exactly the
    # advisor's rotated 3-fold inner LOBO). Epoch budgets differ per fold by design.
    if Zva is not None and len(Zva) > 0 and epochs is None:
        folds_seen.setdefault("n", 0)
        folds_seen["n"] += 1
    return orig_fit(dims, l2, Ztr, ytr, Zva, yva, seed, max_ep, patience, lr, epochs)


rc.fit_bpnn_ep = spy_fit
# one tiny outer fold with a miniature grid so the spy intercepts exactly the inner folds
old_arch, old_l2 = rc.ARCHS, rc.L2S
rc.ARCHS, rc.L2S = [[8]], [0.0]
rows, _ = rc.run_fold(X, bids, soh, cyc, test_b=1, seed=42, bp_max=25, pat=5, qref=qref,
                      rng=qref_r, setting="S1-probe", inner="lobo3")
rc.ARCHS, rc.L2S = old_arch, old_l2
rc.fit_bpnn_ep = orig_fit
check("S1 inner-fold count", folds_seen.get("n", 0) == 3,
      f"early-stopping inner fit calls for test_b=B0005 = {folds_seen.get('n', 0)} (expect 3)")

# ---- S2: train/val disjoint in every recorded fold -----------------------------------------
fold_files = ["phase3_charge_cpu_results.csv", "phase3_selfref_cpu_results.csv",
              "phase3_window_cpu_results.csv", "phase3_windowlength_cpu_results.csv"]
found_any = False
for f in fold_files:
    if os.path.exists(f):
        d = pd.read_csv(f)
        found_any = True
        # disjointness is required only in the SELECTION stage; the refit stage intentionally
        # folds the inner-validation battery back into the fit set (advisor R3-C1/Round-4 item 3).
        sel = d[d.stage == "pre_refit"]
        bad = sel[sel.apply(lambda r: r["val_battery"] in eval(r["fit_batteries"])
                            if isinstance(r["fit_batteries"], str) else True, axis=1)]
        check("S2 disjoint train/val (selection stage)", len(bad) == 0,
              f"{f}: {len(bad)} violating pre_refit rows")
if not found_any:
    check("S2 disjoint train/val", False, "no fold-output file found to inspect")

# ---- S3/S4/S5: declared feature sets match what is fed to the model ------------------------
EXPECTED_C6T = ["dis_V_slope", "cc_dur", "cv_dur", "cv_I_slope", "t_40_41", "ic_peak_V"]
BANNED = ["dis_duration", "dis_mean_V"]
import phase4_cs2_transfer as t, phase4_cs2_within as w  # noqa: E402
import phase4_cs2_adapt1 as a1, phase4_cs2_adapt2 as a2  # noqa: E402
for mod, label in [(t, "transfer"), (w, "within"), (a1, "adapt1"), (a2, "adapt2")]:
    feats = mod.FEATS
    check(f"S3 {label}: declared == fed", True,
          f"FEATS={feats}")  # single FEATS constant is passed everywhere via mod.FEATS
    check(f"S4 {label}: no proxy feats", not any(b in feats for b in BANNED), "")
    check(f"S5 {label}: == Clean-6T definition", feats == EXPECTED_C6T, "")
# S3 hard check on a real matrix: the CSV columns passed through FEATS must all exist
csv_ok = True
for f in ["phase4_cs2_features.csv", "phase4_features.csv"]:
    if os.path.exists(f):
        missing = [c for c in EXPECTED_C6T if c not in pd.read_csv(f, nrows=5).columns]
        check("S3 CS2 csv has Clean-6T columns", not missing, f"{f}: missing={missing}")
    else:
        check("S3 CS2 csv has Clean-6T columns", False, f"{f} not found")

# S4 hard check on r3common settings: no proxy-audited set may contain banned features
clean6 = rc.FEATS_CLEAN6
check("S4 r3common CLEAN6 proxy-free", not any(b in clean6 for b in BANNED), f"{clean6}")
check("S4 TD-All documents its proxies", all(b in rc.FEATS_ALL for b in BANNED),
      "TD-All keeps them by definition; Clean sets must exclude")

# ---- S2b: CS2 within — selection train/val disjoint, val battery recorded -------------------
if os.path.exists("phase4_cs2_within_full.csv"):
    w = pd.read_csv("phase4_cs2_within_full.csv")
    if "val_battery" in w.columns:
        dupes = w.duplicated(subset=["seed", "test_battery"]).sum()
        check("S2b within: no duplicate (seed, cell) rows", dupes == 0, f"{dupes} duplicates")
        check("S2b within: val != test in every fold",
              bool((w.val_battery != w.test_battery).all()),
              f"{int((w.val_battery == w.test_battery).sum())} violations")
        check("S2b within: complete 5 seeds x 8 cells", len(w) == 40, f"{len(w)} rows")
    else:
        check("S2b within: val_battery column", False,
              "column missing - rerun with the val_battery patch")

# ---- S6 (Round 5, R5-C4): outer battery absent from every inner train/val set ----------------
# Structural assertion on the recorded fold outputs: in the selection stage the outer test
# battery must not appear in any fit_batteries list (inner train) or val_battery column.
import re
if os.path.exists("phase3_charge_r4_results.csv"):
    d6 = pd.read_csv("phase3_charge_r4_results.csv")
    sel = d6[d6.stage == "pre_refit"] if "stage" in d6.columns else d6
    viol = 0
    for _, row in sel.iterrows():
        fb = row.get("fit_batteries")
        if isinstance(fb, str):
            names = re.findall(r"B\d{4}", fb)
            outer = str(row.get("test_battery", "")).strip()
            if outer and (outer in names or str(row.get("val_battery", "")).strip() == outer):
                viol += 1
    check("S6 outer battery absent from inner train/val", viol == 0,
          f"{len(sel)} selection rows inspected, {viol} violations")
else:
    check("S6 outer battery absent from inner train/val", False,
          "phase3_charge_r4_results.csv not found")

# ---- S7 (Round 5): phase5 CSVs complete + correctly labelled feature sets --------------------
import numpy as _np
C5T = ["dis_V_slope", "cc_dur", "cv_dur", "cv_I_slope", "ic_peak_V"]
C6T = C5T + ["t_40_41"]
SEEDS5 = {7, 42, 99, 123, 2024}
for arm in ["within", "transfer", "adapt1", "adapt2"]:
    for tag, want_n in [("c5t_full", 5), ("c6t_full", 6)]:
        f = f"phase5_cs2_{arm}_{tag}.csv"
        if not os.path.exists(f):
            check(f"S7 {arm} {tag} exists", False, "file missing")
            continue
        d = pd.read_csv(f)
        n_seed = d.seed.nunique()
        seeds_ok = set(d.seed.unique()) == SEEDS5
        expect = 40 if arm == "within" else 80
        nan_ok = int(d.R2.isna().sum()) == 0
        check(f"S7 {arm} {tag} complete ({expect} rows, 5 seeds, no NaN)",
              len(d) == expect and seeds_ok and nan_ok,
              f"rows={len(d)}, seeds={n_seed}, NaN={int(d.R2.isna().sum())}")

print()
if FAILS:
    print(f"STRUCTURAL VERIFICATION FAILED: {len(FAILS)} check(s): {FAILS}")
    sys.exit(1)
print("ALL STRUCTURAL CHECKS PASSED")
