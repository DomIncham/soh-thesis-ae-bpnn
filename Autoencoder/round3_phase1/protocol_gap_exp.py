# Round 3 Phase 2: the protocol-gap experiment (advisor R3-C2 / R3-C3).

# One model, one feature set, one selection grid, one leakage discipline. Only the SPLIT changes:
#
#   lobo_nested           our protocol: outer test = an unseen battery, inner validation = a second
#                         battery, config re-fitted on all 3 remaining batteries. Delegates to
#                         r3common.run_fold, so with the default seeds it must reproduce Phase 1
#                         bit-for-bit - that is the regression check for this script.
#   random_within         per battery, cycles shuffled, 70/10/20 train/val/test. This is the split
#                         that most NASA papers use: the test cycles come from the SAME battery the
#                         model was trained on.
#   chronological_within  per battery, cycles in time order, first 70% train / next 10% val /
#                         last 20% test. The other half of the audit's factor (a).
#   random_pooled         all 636 cycles shuffled together, 70/10/20. The 34-cell style of the audit:
#                         the training set contains other cycles of the test battery.
#
# Why: the advisor's audit says published R2 > 0.95 comes from (a) same-battery splits and/or
# (b) indirect capacity proxies. This measures (a) on a fixed representation, and pushes the
# Oracle-proxy through every protocol so (b) can be compared under each of them. The Oracle is the
# bridge: if it reaches R2 ~ 1 under random/chronological but not under LOBO, the two audit factors
# are separated by measurement rather than argued.
#
# Every stage is leakage-guarded the same way as Phase 1: masks asserted disjoint, the scaler is
# fitted on the training rows only and asserted against them, and the outer test rows never enter
# any fit. A cross-check mode (--probe) doubles the outer test features and requires the fit
# metrics to stay bit-identical.
#
# Device: default cpu; --device cuda|auto is opt-in and recorded in the filenames and a `device`
# column, so a GPU run can never be mistaken for a CPU run.
# Usage:
#   python protocol_gap_exp.py --smoke
#   python protocol_gap_exp.py --full [--seeds 42,7,123,2024,11] [--splits ...] [--tag NAME]
#   python protocol_gap_exp.py --probe [--device cpu]
import argparse, itertools, os, time
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

import r3common as R
from r3common import (BATT, SETTINGS, ARCHS, L2S, MIN_EP, RETRAIN_EP,
                      load_td, soh_range_and_qref, run_fold, fit_bpnn_ep, predict,
                      extras, reg_metrics, OUT)

REV = {v: k for k, v in BATT.items()}
ALL_B = [1, 2, 3, 4]
SPLITS = ("lobo_nested", "random_within", "chronological_within", "random_pooled")
FRAC = (0.70, 0.10, 0.20)
PRED_COLS = ["split", "setting", "stage", "seed", "test_battery", "test_scope",
             "cycle", "y_true", "y_pred"]


# ---------------------------------------------------------------- split construction
def split_blocks(split, bids, cyc, seed):
    """(tag, train_mask, val_mask, test_mask) per outer block.

    Chronological ordering always uses the `cycle` column, never row order. `random_within` sorts by
    cycle first so the permutation is applied to a deterministic ordering regardless of file order.
    """
    n = len(bids)
    if split in ("random_within", "chronological_within"):
        blocks = []
        for b in ALL_B:
            idx = np.where(bids == b)[0]
            idx = idx[np.argsort(cyc[idx])]
            if split == "random_within":
                idx = np.random.default_rng(seed).permutation(idx)
            a = int(round(FRAC[0] * len(idx)))
            z = int(round((FRAC[0] + FRAC[1]) * len(idx)))
            m_tr, m_va, m_te = (np.zeros(n, bool) for _ in range(3))
            m_tr[idx[:a]] = True
            m_va[idx[a:z]] = True
            m_te[idx[z:]] = True
            blocks.append((BATT[b], m_tr, m_va, m_te))
        return blocks
    if split == "random_pooled":
        idx = np.random.default_rng(seed).permutation(np.arange(n))
        a = int(round(FRAC[0] * n))
        z = int(round((FRAC[0] + FRAC[1]) * n))
        m_tr, m_va, m_te = (np.zeros(n, bool) for _ in range(3))
        m_tr[idx[:a]] = True
        m_va[idx[a:z]] = True
        m_te[idx[z:]] = True
        return [("pooled", m_tr, m_va, m_te)]
    raise ValueError(f"unknown split: {split}")


# ---------------------------------------------------------------- one block
def run_block(X, bids, soh, cyc, qref, rng_span, setting, split, seed, tag,
              m_tr, m_va, m_te, bp_max, pat, span_pooled):
    """Select a config on the inner validation rows, fit it once, evaluate on the outer test rows.

    Mirrors r3common.run_fold Stage A (same grid, same guard, same scaler discipline) so the only
    difference between this and the LOBO protocol is which rows the split puts where.
    """
    assert not (m_tr & m_va).any(), "LEAKAGE: train/val masks overlap"
    assert not (m_tr & m_te).any(), "LEAKAGE: train/test masks overlap"
    assert not (m_va & m_te).any(), "LEAKAGE: val/test masks overlap"
    assert m_te.sum() > 0, "empty outer test mask"

    n_in = X.shape[1]
    sc = MinMaxScaler().fit(X[m_tr])
    assert np.allclose(sc.data_min_, X[m_tr].min(0)), "LEAKAGE: scaler != block-train"
    tr_s, va_s, te_s = sc.transform(X[m_tr]), sc.transform(X[m_va]), sc.transform(X[m_te])
    mu, sd = soh[m_tr].mean(), soh[m_tr].std()

    cands = []
    for dims, l2 in itertools.product(ARCHS, L2S):
        bp, ep = fit_bpnn_ep([n_in] + dims, l2, tr_s, (soh[m_tr] - mu) / sd,
                             va_s, (soh[m_va] - mu) / sd, seed, bp_max, pat)
        v = float(np.sqrt(np.mean((predict(bp, va_s, mu, sd) - soh[m_va]) ** 2)))
        cands.append((v, dims, l2, ep, bp))
    ok = [c for c in cands if c[3] >= MIN_EP]
    sel_degenerate = len(ok) < len(cands)
    if not ok:
        _, dims, l2, _, _ = min(cands, key=lambda c: c[0])
        bp2, _ = fit_bpnn_ep([n_in] + dims, l2, tr_s, (soh[m_tr] - mu) / sd,
                             None, None, seed, bp_max, pat, epochs=RETRAIN_EP)
        v = float(np.sqrt(np.mean((predict(bp2, va_s, mu, sd) - soh[m_va]) ** 2)))
        ok = [(v, dims, l2, RETRAIN_EP, bp2)]
        print(f"  [guard] no candidate converged; retrained {dims}/l2={l2} "
              f"{RETRAIN_EP}ep -> val RMSE={v:.4f}")
    v, dims, l2, ep, bp = min(ok, key=lambda c: c[0])

    p_te = predict(bp, te_s, mu, sd)
    p_fit = predict(bp, tr_s, mu, sd)
    _, trmse, tr2 = reg_metrics(soh[m_tr], p_fit)

    if tag == "pooled":
        # no single battery: use the mean Q_ref of the 4 cells and the pooled SOH span
        scope, qref_ah, span = "pooled", float(qref.loc[ALL_B].mean()), span_pooled
    else:
        scope, qref_ah, span = "per_battery", float(qref.loc[REV[tag]]), float(rng_span.loc[REV[tag]])
    ex = extras(soh[m_te], p_te, qref_ah)

    row = dict(split=split, setting=setting, stage="fit", seed=seed, test_battery=tag,
               test_scope=scope, val_battery=tag, fit_batteries=("pooled-all" if tag == "pooled"
                                                                 else "same-battery"),
               cfg=f"{dims}/l2={l2}", sel_epochs=ep, sel_degenerate=sel_degenerate,
               sel_val_rmse=round(v, 4),
               train_RMSE=round(float(trmse), 4), train_R2=round(float(tr2), 4),
               test_nRMSE=round(ex["test_RMSE"] / span, 4),
               n_train=int(m_tr.sum()), n_val=int(m_va.sum()), n_test=int(m_te.sum()),
               **{k: round(float(x), 4) for k, x in ex.items()})
    pred = pd.DataFrame(dict(split=split, setting=setting, stage="fit", seed=seed,
                             test_battery=tag, test_scope=scope, cycle=cyc[m_te],
                             y_true=soh[m_te], y_pred=p_te))
    return row, pred


# ---------------------------------------------------------------- driver
def run(args):
    R.set_device(args.device)
    seeds = args.seed_list
    splits = args.split_list
    settings = {k: v for k, v in SETTINGS.items() if k in (args.setting_list or list(SETTINGS))}
    folds = [1, 2, 3, 4]
    bp_max, pat = (100, 10) if args.smoke else (500, 30)

    rng_span, qref = soh_range_and_qref()
    span_pooled = None
    rows, preds, t0 = [], [], time.time()

    for name, feats in settings.items():
        X, bids, soh, cyc = load_td(feats)
        if span_pooled is None:
            span_pooled = float(soh.max() - soh.min())
        for split in splits:
            for seed in seeds:
                if split == "lobo_nested":
                    for b in folds:
                        r, p = run_fold(X, bids, soh, cyc, b, seed, bp_max, pat, qref, rng_span, name)
                        for x in r:
                            x.update(split=split, test_scope="per_battery",
                                     n_train=np.nan, n_val=np.nan, n_test=int((bids == b).sum()))
                        rows += r
                        preds.append(p.assign(split=split, test_scope="per_battery"))
                        ref = [x for x in r if x["stage"] == "refit_on_3"][0]
                        print(f"{name:14s} {split:20s} seed{seed:<5d} {BATT[b]} | "
                              f"R2={ref['test_R2']:+.3f} RMSE={ref['test_RMSE']:.3f}%")
                else:
                    for tag, m_tr, m_va, m_te in split_blocks(split, bids, cyc, seed):
                        row, pred = run_block(X, bids, soh, cyc, qref, rng_span, name, split, seed,
                                              tag, m_tr, m_va, m_te, bp_max, pat, span_pooled)
                        rows.append(row)
                        preds.append(pred)
                        print(f"{name:14s} {split:20s} seed{seed:<5d} {tag:6s} | "
                              f"R2={row['test_R2']:+.3f} RMSE={row['test_RMSE']:.3f}% "
                              f"(n_tr={row['n_train']} n_te={row['n_test']})")
        print(f"    ... {name} done, {time.time() - t0:.0f}s elapsed")

    res = pd.DataFrame(rows)
    res["device"] = R.DEVICE.type
    tag = args.tag if args.tag else R.DEVICE.type
    res.to_csv(os.path.join(OUT, f"protocol_gap_exp_{tag}_results.csv"), index=False)
    pd.concat(preds, ignore_index=True)[PRED_COLS].to_csv(
        os.path.join(OUT, f"protocol_gap_exp_{tag}_preds.csv"), index=False)

    cols = ["test_MAE", "test_RMSE", "test_R2", "test_MAPE", "test_RMSE_Ah"]
    print("\n=== per split x setting, mean / median / std over blocks x seeds ===\n")
    agg = res.groupby(["split", "setting"])[cols].agg(["mean", "median", "std"]).round(3)
    print(agg.to_string())
    agg.to_csv(os.path.join(OUT, f"protocol_gap_exp_{tag}_summary.csv"))
    print("\n=== test_R2 per split (setting = TD-All, stage = the one that matters) ===")
    key = res[(res.setting == "TD-All") & (res.stage.isin(["refit_on_3", "fit"]))]
    print(key.pivot_table(index="split", values="test_R2", aggfunc=["mean", "median", "std"])
          .round(3).to_string())
    print("\n=== degenerate blocks flagged ===")
    print(res.groupby("split").sel_degenerate.agg(["sum", "count"]).to_string())
    print(f"\ntotal {len(res)} blocks, {time.time() - t0:.0f}s")
    print("saved")


def probe(args):
    """Leakage cross-check for every non-LOBO split: double the outer test features and re-run the
    whole block. The fit metrics (and the selection) must not move."""
    R.set_device(args.device)
    rng_span, qref = soh_range_and_qref()
    X, bids, soh, cyc = load_td(R.FEATS_ALL)
    span_pooled = float(soh.max() - soh.min())
    SEED, BP, PAT = 42, 500, 30
    worst = 0.0
    for split in [s for s in SPLITS if s != "lobo_nested"]:
        tag, m_tr, m_va, m_te = split_blocks(split, bids, cyc, SEED)[0]
        Xp = X.copy()
        Xp[m_te] *= 2.0
        print(f"\n{split}: {tag}, {int(m_te.sum())} outer test rows doubled")
        got = {}
        for lbl, Xd in (("baseline", X), ("perturbed", Xp)):
            got[lbl] = run_block(Xd, bids, soh, cyc, qref, rng_span, "TD-All", split, SEED, tag,
                                 m_tr, m_va, m_te, BP, PAT, span_pooled)[0]
        d = max(abs(got["baseline"][k] - got["perturbed"][k]) for k in ("train_RMSE", "train_R2"))
        same_cfg = got["baseline"]["cfg"] == got["perturbed"]["cfg"]
        same_ep = got["baseline"]["sel_epochs"] == got["perturbed"]["sel_epochs"]
        worst = max(worst, d)
        print(f"  fit RMSE={got['baseline']['train_RMSE']:.6f} R2={got['baseline']['train_R2']:.6f}"
              f" | max|diff|={d:.2e} | same cfg={same_cfg} same sel_epochs={same_ep}")
        if not (same_cfg and same_ep):
            print("  CHECK: selection moved - investigate")
    print(f"\nprobe verdict: max|diff| = {worst:.2e} -> "
          f"{'PASS: no leakage (fit metrics unmoved by perturbed outer test)' if worst < 1e-6 else 'CHECK: fit metrics moved'}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--device", default="cpu", choices=["cpu", "cuda", "auto"])
    ap.add_argument("--tag", default=None, help="output filename tag (default: device type)")
    ap.add_argument("--seeds", default=None, help="comma list; default 42,7,123,2024,11 (smoke: 42)")
    ap.add_argument("--splits", default=None, help="comma list; default all four")
    ap.add_argument("--settings", default=None, help="comma list; default all three")
    a = ap.parse_args()
    if a.smoke:
        a.seeds, a.splits, a.settings = "42", "random_within,chronological_within", None
    a.seed_list = [int(s) for s in (a.seeds or "42,7,123,2024,11").split(",")]
    a.split_list = (a.splits or ",".join(SPLITS)).split(",")
    a.setting_list = a.settings.split(",") if a.settings else None
    if a.probe:
        probe(a)
    else:
        run(a)
