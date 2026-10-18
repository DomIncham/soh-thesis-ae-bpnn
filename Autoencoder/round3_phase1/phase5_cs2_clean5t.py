# Round 5, item R5-C2: Clean-5T vs Clean-6T on cross-dataset transfer.
# Clean-5T (advisor definition, R5 comment line 5) = Clean-7 minus the two temperature features
# unavailable in CS2 logs = Clean-6T minus t_40_41 = {dis_V_slope, cc_dur, cv_dur, cv_I_slope,
# ic_peak_V}. This script re-runs the four CALCE arms (transfer / within / adapt1 / adapt2)
# with FEATS = Clean-5T, writing new *_c5t_*.csv files; the existing Clean-6T results are NOT
# modified. Same seeds, budgets, protocol, and guards as the Round 4 scripts.
# S4 proxy-ban applies: dis_duration and dis_mean_V must not appear in FEATS.
# Usage: python phase5_cs2_clean5t.py --smoke   # 1 seed, tiny budget (mechanics check)
#        python phase5_cs2_clean5t.py           # 5 seeds, full budget (CPU, est ~60-90 min)
import argparse, itertools, os, sys, time
import numpy as np
import pandas as pd
import torch
import r3common as rc
from sklearn.preprocessing import MinMaxScaler

T_START = time.time()
_FITS_DONE = 0


def prog(msg):
    """Console progress line with elapsed time (printed for every rotation, so the user
    running in CMD can see the process moving and estimate completion)."""
    el = time.time() - T_START
    print(f"[{int(el // 3600):02d}:{int(el % 3600 // 60):02d}:{int(el % 60):02d} elapsed] {msg}",
          flush=True)

import ast as _ast
FEATS = _ast.literal_eval(os.environ.get("CLEAN_FEATS",
    '["dis_V_slope", "cc_dur", "cv_dur", "cv_I_slope", "ic_peak_V"]'))  # default Clean-5T
ROOM = ["B0005", "B0006", "B0007", "B0018"]
SEEDS = [42, 123, 2024, 7, 99]
ADAPT1_EP, ADAPT2_EP = 40, 30

assert "dis_duration" not in FEATS and "dis_mean_V" not in FEATS, "S4 proxy-ban violated"


def warm_fit(bp0, dims, l2, Xfit, yfit, mu, sd, seed, epochs, lr=1e-4):
    """adapt2 warm-start: identical to phase4_cs2_adapt2.warm_fit."""
    torch.manual_seed(seed)
    np.random.seed(seed)
    bp = rc.BPNN([Xfit.shape[1]] + dims, l2).to(rc.DEVICE)
    bp.load_state_dict({k: v.clone() for k, v in bp0.state_dict().items()})
    opt = torch.optim.Adam(bp.parameters(), lr=lr, weight_decay=l2)
    loader = torch.utils.data.DataLoader(
        torch.utils.data.TensorDataset(
            torch.tensor(np.asarray(Xfit), dtype=torch.float32, device=rc.DEVICE),
            torch.tensor(np.asarray((yfit - mu) / sd), dtype=torch.float32, device=rc.DEVICE)),
        batch_size=32, shuffle=True)
    bp.train()
    for _ in range(int(epochs)):
        for zb, tb in loader:
            opt.zero_grad()
            loss = torch.nn.functional.mse_loss(bp(zb), tb)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(bp.parameters(), 1.0)
            opt.step()
    bp.eval()
    return bp


def pools():
    nasa = pd.read_csv("phase4_features.csv")
    nasa = nasa[nasa.include_cell].dropna(subset=FEATS).reset_index(drop=True)
    nasa["bid"] = nasa.battery.astype("category").cat.codes
    cs2 = pd.read_csv("phase4_cs2_features.csv")
    cs2 = cs2[cs2.include_cell & cs2.cap_ok].dropna(subset=FEATS).reset_index(drop=True)
    cs2["bid"] = cs2.battery.astype("category").cat.codes
    return nasa, cs2


def select_ep(dims, l2, Xf, yf, Xv, yv, seed, bp_max, pat):
    """One candidate's early-stopping epoch on the validation fold (None = diverged).
    Emits a progress line every 5 fits so the CMD window shows liveness + elapsed time."""
    global _FITS_DONE
    _FITS_DONE += 1
    if _FITS_DONE % 5 == 0:
        prog(f"fits done: {_FITS_DONE} | {int(_FITS_DONE*3.6/60)} fit-min est")
    mu, sd = yf.mean(), yf.std()
    try:
        bp, ep = rc.fit_bpnn_ep([Xf.shape[1]] + dims, l2, Xf, (yf - mu) / sd, Xv,
                                (yv - mu) / sd, seed, bp_max, pat)
    except (TypeError, RuntimeError):
        return None
    v = float(np.sqrt(np.mean((rc.predict(bp, Xv, mu, sd) - yv) ** 2)))
    return v, ep


def run_arm(arm, nasa, cs2, seeds, bp_max, pat, tag):
    """One CALCE arm under the Clean-5T feature set. Selection protocol per arm:
      transfer: rotate the single-val-battery selection over the source pool (seed draw kept
                per seed), aggregate = mean of the per-battery selection RMSEs (one battery
                here is a degenerate but honest aggregate; recorded per battery).
      within:   LOCO on CS2, val battery rotates over the 7 training cells (aggregated score).
      adapt1:   NASA selection as transfer, then scratch-fit 1 CS2 cell.
      adapt2:   NASA selection as transfer, then warm-start 1 CS2 cell.
    The untouched test battery/cell is never used in selection or refit."""
    Xn, yn, bn = nasa[FEATS].values, nasa.soh.values, nasa.bid.values
    Xc, yc, bc = cs2[FEATS].values, cs2.soh.values, cs2.bid.values  # bc = numeric bids
    cells = sorted(set(cs2.battery))
    out_name = f"phase5_cs2_{arm}_{tag}.csv"
    rows = []
    if os.path.exists(out_name):
        rows = pd.read_csv(out_name).to_dict("records")
        print(f"[resume] {len(rows)} rows in {out_name}")
    if arm in ("transfer", "adapt1", "adapt2"):
        done = {(r["pool"], r["seed"]) for r in rows}
        for pool in ["room", "all13"]:
            nd = nasa[nasa.battery.isin(ROOM)] if pool == "room" else nasa
            nd = nd.reset_index(drop=True)
            Xn_, yn_, bn_ = nd[FEATS].values, nd.soh.values, nd.bid.values
            uniq = np.unique(bn_)
            for seed in seeds:
                if (pool, seed) in done:
                    continue
                r = np.random.RandomState(seed)
                # R5-C1 rotated selection: each source battery takes the validation role once;
                # the candidate score is the MEAN selection RMSE over these rotations
                # (the advisor's "aggregated across the available source-training batteries").
                cands = []
                for dims, l2 in itertools.product(rc.ARCHS, rc.L2S):
                    vs, eps = [], []
                    for v in uniq:
                        res = select_ep(dims, l2, Xn_[bn_ != v], yn_[bn_ != v],
                                        Xn_[bn_ == v], yn_[bn_ == v], seed, bp_max, pat)
                        if res is None:
                            continue
                        vs.append(res[0]); eps.append(res[1])
                    if vs:
                        cands.append((float(np.mean(vs)), dims, l2,
                                      int(round(np.mean(eps))), min(eps)))
                ok = [c for c in cands if c[4] >= rc.MIN_EP and np.isfinite(c[0])]
                sel_degenerate = len(ok) < len(cands)
                if not ok:
                    _, dims, l2, ep, _ = min(cands, key=lambda c: c[0]) if cands else \
                        (0, [8], 0.0, rc.RETRAIN_EP, rc.RETRAIN_EP)
                    ep = rc.RETRAIN_EP
                else:
                    _, dims, l2, ep, _ = min(ok, key=lambda c: c[0])
                # refit on the WHOLE pool (untouched by selection), then score CS2
                sc2 = MinMaxScaler().fit(Xn_)
                mu2, sd2 = yn_.mean(), yn_.std()
                try:
                    bp_rf, _ = rc.fit_bpnn_ep([Xn_.shape[1]] + dims, l2, sc2.transform(Xn_),
                                              (yn_ - mu2) / sd2, None, None, seed,
                                              bp_max, pat, epochs=ep)
                except (TypeError, RuntimeError):
                    print(f"  [guard] pool refit diverged pool={pool} seed={seed}")
                    bp_rf = None
                if arm == "transfer" or bp_rf is None:
                    if bp_rf is not None:
                        for c_ in cells:
                            m_c = cs2.battery.values == c_
                            p = rc.predict(bp_rf, sc2.transform(Xc[m_c]), mu2, sd2)
                            mae, rmse, r2 = rc.reg_metrics(yc[m_c], p)
                            rows.append(dict(arm=arm, pool=pool, seed=seed, test_battery=c_,
                                             n_cycles=int(m_c.sum()), cfg=f"{dims}/l2={l2}",
                                             sel_epochs=ep, sel_degenerate=sel_degenerate,
                                             MAE=round(float(mae), 3),
                                             RMSE=round(float(rmse), 3), R2=round(float(r2), 3)))
                        print(f"[{arm} {pool} s{seed}] cfg {dims}/l2={l2} ep {ep} "
                              f"{'DEG' if sel_degenerate else 'ok'}")
                else:
                    # adapt arms: fine-tune on 1 CS2 cell, test the other 7 (LOCO)
                    for adapt_cell in cells:
                        m_a = cs2.battery.values == adapt_cell
                        m_te = ~m_a
                        if arm == "adapt1":  # scratch on 1 cell (v1 semantics kept)
                            sc_a = MinMaxScaler().fit(Xc[m_a])
                            mu_a, sd_a = yc[m_a].mean(), yc[m_a].std()
                            try:
                                bp_ft, _ = rc.fit_bpnn_ep([Xc.shape[1]] + dims, l2,
                                                          sc_a.transform(Xc[m_a]),
                                                          (yc[m_a] - mu_a) / sd_a, None, None,
                                                          seed, bp_max, pat, epochs=ADAPT1_EP)
                                p = rc.predict(bp_ft, sc_a.transform(Xc[m_te]), mu_a, sd_a)
                            except (TypeError, RuntimeError):
                                print("  [guard] adapt1 diverged"); p = np.full(m_te.sum(), np.nan)
                        else:  # adapt2 warm-start with the source normalisation kept fixed
                            try:
                                bp_ft = warm_fit(bp_rf, dims, l2, sc2.transform(Xc[m_a]), yc[m_a],
                                                 mu2, sd2, seed, ADAPT2_EP)
                                p = rc.predict(bp_ft, sc2.transform(Xc[m_te]), mu2, sd2)
                            except (TypeError, RuntimeError):
                                print("  [guard] adapt2 diverged"); p = np.full(m_te.sum(), np.nan)
                        mae, rmse, r2 = rc.reg_metrics(yc[m_te], p)
                        rows.append(dict(arm=arm, pool=pool, seed=seed, adapt_cell=adapt_cell,
                                         n_cycles=int(m_te.sum()), cfg=f"{dims}/l2={l2}",
                                         sel_epochs=ep, sel_degenerate=sel_degenerate,
                                         MAE=round(float(mae), 3), RMSE=round(float(rmse), 3),
                                         R2=round(float(r2), 3)))
                        print(f"[{arm} {pool} s{seed}] adapt={adapt_cell} R2={r2:.3f}")
                pd.DataFrame(rows).to_csv(out_name, index=False)  # checkpoint per seed
    elif arm == "within":
        done = {(r["seed"], r["test_battery"]) for r in rows}
        cells_u = sorted(set(cs2.battery.values))  # stable cell order for name lookup
        for seed in seeds:
            r = np.random.RandomState(seed)
            for test_name in cells_u:
                if (seed, test_name) in done:
                    continue
                test_i = cs2.bid[cs2.battery == test_name].iloc[0]
                pool_cells = [b0 for b0 in np.unique(cs2.bid[cs2.battery != test_name])
                              if b0 != test_i]
                m_te = cs2.battery.values == test_name
                # R5-C1 rotated selection: every one of the 7 training cells is the validation
                # battery once; the candidate score is the MEAN RMSE across the 7 rotations.
                cands = []
                for dims, l2 in itertools.product(rc.ARCHS, rc.L2S):
                    vs, eps = [], []
                    for v_i in pool_cells:
                        m_sel = np.isin(bc, [c for c in pool_cells if c != v_i])
                        m_va = bc == v_i
                        res = select_ep(dims, l2, Xc[m_sel], yc[m_sel], Xc[m_va], yc[m_va],
                                        seed, bp_max, pat)
                        if res is None:
                            continue
                        vs.append(res[0]); eps.append(res[1])
                    if vs:
                        cands.append((float(np.mean(vs)), dims, l2,
                                      int(round(np.mean(eps))), min(eps)))
                ok = [c for c in cands if c[4] >= rc.MIN_EP and np.isfinite(c[0])]
                sel_degenerate = len(ok) < len(cands)
                if not ok:
                    _, dims, l2, ep, _ = min(cands, key=lambda c: c[0]) if cands else \
                        (0, [8], 0.0, 200, 200)
                    ep = 200
                else:
                    _, dims, l2, ep, _ = min(ok, key=lambda c: c[0])
                m_fit = np.isin(bc, pool_cells)
                m_te = bc == test_i
                prog(f"[within s{seed}] cell {test_name} selection done "
                     f"(cfg {dims}/l2={l2}, ep {ep}) -> refit+eval")
                sc2 = MinMaxScaler().fit(Xc[m_fit])
                mu2, sd2 = yc[m_fit].mean(), yc[m_fit].std()
                try:
                    bp_rf, _ = rc.fit_bpnn_ep([Xc.shape[1]] + dims, l2, sc2.transform(Xc[m_fit]),
                                              (yc[m_fit] - mu2) / sd2, None, None, seed,
                                              bp_max, pat, epochs=ep)
                    p = rc.predict(bp_rf, sc2.transform(Xc[m_te]), mu2, sd2)
                except (TypeError, RuntimeError):
                    print("  [guard] within refit diverged"); p = np.full(m_te.sum(), np.nan)
                mae, rmse, r2 = rc.reg_metrics(yc[m_te], p)
                rows.append(dict(arm="within", seed=seed, test_battery=test_name,
                                 n_cycles=int(m_te.sum()), cfg=f"{dims}/l2={l2}", sel_epochs=ep,
                                 sel_degenerate=sel_degenerate, MAE=round(float(mae), 3),
                                 RMSE=round(float(rmse), 3), R2=round(float(r2), 3)))
                print(f"[within s{seed}] test={test_name} R2={r2:.3f}")
                pd.DataFrame(rows).to_csv(out_name, index=False)
    pd.DataFrame(rows).to_csv(out_name, index=False)
    return out_name


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--arms", default="transfer,within,adapt1,adapt2")
    args = ap.parse_args()
    rc.set_device(args.device)
    seeds = [42] if args.smoke else SEEDS
    bp_max, pat = (60, 10) if args.smoke else (300, 20)
    tag = "smoke" if args.smoke else ("c6t_full" if FEATS != ["dis_V_slope", "cc_dur", "cv_dur", "cv_I_slope", "ic_peak_V"] else "c5t_full")
    nasa, cs2 = pools()
    _label = "Clean-6T" if "t_40_41" in FEATS and len(FEATS) == 6 else (
        "Clean-5T" if len(FEATS) == 5 and "t_40_41" not in FEATS else "CUSTOM feature set")
    print(f"[_label: {_label}] features: {FEATS}")
    print(f"NASA pool {len(nasa)} rows; CS2 pool {len(cs2)} rows, {cs2.battery.nunique()} cells")
    for arm in args.arms.split(","):
        out = run_arm(arm.strip(), nasa, cs2, seeds, bp_max, pat, tag)
        df = pd.read_csv(out)
        print(f"\n== {out}: {len(df)} rows ==")
        if not args.smoke and len(df):
            if "R2" in df and df.R2.notna().any():
                print(df.groupby([c for c in ["pool", "test_battery", "adapt_cell"] if c in df])
                      .R2.agg(["mean", "median"]).round(3).to_string())


if __name__ == "__main__":
    main()
