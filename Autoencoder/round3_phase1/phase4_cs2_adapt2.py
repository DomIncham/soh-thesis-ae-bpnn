# Phase 4 item 6.3 (R3-C6): cross-dataset transfer with minimal adaptation (4.5c, v2).
# v1 (phase4_cs2_adapt1.py) accidentally trained FROM SCRATCH on the 1 target cell - its numbers
# are the "no-transfer, 1-cell-only training" reference (phase4_cs2_adapt1_full.csv).
# v2 adds the real adaptation arm:
#   warm  : load the NASA room-pool frozen model's weights, fine-tune with the NASA normalisation
#           (source scaler + label scale kept fixed - only the weights adapt), 30 epochs.
# Both arms are leave-one-cell-out on CS2: fine-tune on 1 cell, test the other 7.
# The frozen (no-adaptation) numbers are phase4_cs2_transfer_full.csv.
# Usage: python phase4_cs2_adapt2.py            # 5 seeds, full budget (~15-20 min)
#        python phase4_cs2_adapt2.py --smoke    # 1 seed, tiny budget (mechanics only)
import argparse, itertools, os
import numpy as np
import pandas as pd
import torch
import r3common as rc
from sklearn.preprocessing import MinMaxScaler

# Clean-6T (Round 4 advisor correction) = Clean-8 minus the two temperature features unavailable
# in CS2 logs; dis_duration and dis_mean_V are proxy/proxy-equivalent and MUST NOT be present.
FEATS = ["dis_V_slope", "cc_dur", "cv_dur", "cv_I_slope", "t_40_41", "ic_peak_V"]
ROOM = ["B0005", "B0006", "B0007", "B0018"]
SEEDS = [42, 123, 2024, 7, 99]


def warm_fit(bp0, dims, l2, Xfit, yfit, mu, sd, seed, epochs, lr=1e-4):
    """Continue training bp0's weights on (Xfit, yfit) already normalised with mu/sd.
    Low LR + gradient clipping: CS2 features fall partly OUTSIDE the NASA min-max range, so the
    source-scale loss can spike; 1e-3 diverges, 1e-4 with clipping is stable (tested)."""
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


def nasa_frozen(seed, bp_max, pat):
    """Frozen NASA model: config selection on a held-out NASA cell (same protocol as 4.5b),
    refit on the whole room pool. Returns model + the fixed source normalisation."""
    nd = pd.read_csv("phase4_features.csv")
    nd = nd[nd.include_cell & nd.battery.isin(ROOM)].dropna(subset=FEATS).reset_index(drop=True)
    nd["bid"] = nd.battery.astype("category").cat.codes
    Xn, yn, bn = nd[FEATS].values, nd.soh.values, nd.bid.values
    uniq = np.unique(bn)
    r = np.random.RandomState(seed)
    val_b = int(r.choice(uniq))
    val_name = nd.battery[bn == val_b].iloc[0]  # name of the val battery (recorded in the CSV)
    sc = MinMaxScaler().fit(Xn)  # refit-stage scaler: the whole room pool
    mu, sd = yn.mean(), yn.std()
    m_val, m_fit = bn == val_b, np.ones_like(bn, bool)
    m_sel = bn != val_b
    sc_sel = MinMaxScaler().fit(Xn[m_sel])
    mu_s, sd_s = yn[m_sel].mean(), yn[m_sel].std()
    cands = []
    for dims, l2 in itertools.product(rc.ARCHS, rc.L2S):
        try:
            bp, ep = rc.fit_bpnn_ep([len(FEATS)] + dims, l2, sc_sel.transform(Xn[m_sel]),
                                    (yn[m_sel] - mu_s) / sd_s, sc_sel.transform(Xn[m_val]),
                                    (yn[m_val] - mu_s) / sd_s, seed, bp_max, pat)
        except (TypeError, RuntimeError):
            continue
        v = float(np.sqrt(np.mean((rc.predict(bp, sc_sel.transform(Xn[m_val]), mu_s, sd_s) - yn[m_val]) ** 2)))
        cands.append((v, dims, l2, ep))
    ok = [c for c in cands if c[3] >= rc.MIN_EP and np.isfinite(c[0])]
    if not ok:
        _, dims, l2, ep = (min(cands, key=lambda c: c[0]) if cands else (0, [8], 0.0, rc.RETRAIN_EP))
        ep = rc.RETRAIN_EP
    else:
        _, dims, l2, ep = min(ok, key=lambda c: c[0])
    bp0, _ = rc.fit_bpnn_ep([len(FEATS)] + dims, l2, sc.transform(Xn[m_fit]), (yn - mu) / sd,
                            None, None, seed, bp_max, pat, epochs=ep)
    return bp0, sc, mu, sd, dims, l2, val_name


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--device", default="cpu")
    args = ap.parse_args()
    rc.set_device(args.device)
    seeds = [42] if args.smoke else SEEDS
    bp_max, pat = (60, 10) if args.smoke else (300, 20)
    ADAPT_EP = 30
    tag = "smoke" if args.smoke else "full"
    out_name = f"phase4_cs2_adapt2_{tag}.csv"

    cs2 = pd.read_csv("phase4_cs2_features.csv")
    cs2 = cs2[cs2.include_cell & cs2.cap_ok].dropna(subset=FEATS).reset_index(drop=True)
    Xc, yc, cells_c = cs2[FEATS].values, cs2.soh.values, cs2.battery.values
    cells = sorted(set(cells_c))
    print(f"CS2 pool: {len(cs2)} full cycles, {len(cells)} cells")

    rows = []
    if os.path.exists(out_name):
        rows = pd.read_csv(out_name).to_dict("records")
        print(f"[resume] {len(rows)} rows already in {out_name}")
    done = {(r["seed"], r["adapt_cell"]) for r in rows}
    for seed in seeds:
        if all((seed, c) in done for c in cells):
            continue
        bp0, sc_n, mu_n, sd_n, dims, l2, val_name = nasa_frozen(seed, bp_max, pat)
        if bp0 is None:
            print(f"seed {seed}: NASA fit diverged - skipped")
            continue
        for adapt_cell in cells:
            if (seed, adapt_cell) in done:
                continue
            m_a = cells_c == adapt_cell
            m_te = cells_c != adapt_cell
            try:
                bp = warm_fit(bp0, dims, l2, sc_n.transform(Xc[m_a]), yc[m_a],
                              mu_n, sd_n, seed, ADAPT_EP)
                p = rc.predict(bp, sc_n.transform(Xc[m_te]), mu_n, sd_n)
            except (TypeError, RuntimeError) as e:
                print(f"  [guard] warm diverged ({type(e).__name__}); NaN row recorded")
                p = np.full(int(m_te.sum()), np.nan)
            mae, rmse, r2 = rc.reg_metrics(yc[m_te], p)
            rows.append(dict(seed=seed, adapt_cell=adapt_cell, val_battery=val_name,
                             n_cycles=int(m_te.sum()),
                             cfg=f"{dims}/l2={l2}", adapt_epochs=ADAPT_EP,
                             MAE=round(float(mae), 3), RMSE=round(float(rmse), 3),
                             R2=round(float(r2), 3)))
            print(f"seed {seed} adapt={adapt_cell}: R2={r2:.3f}")
            pd.DataFrame(rows).to_csv(out_name, index=False)
    out = pd.DataFrame(rows)
    print(f"\nsaved {out_name}: {len(out)} rows")
    if not args.smoke and len(out):
        print("\nWarm-start, per adapt cell (test = other 7 CS2 cells):")
        print(out.groupby("adapt_cell").agg(R2=("R2", "mean"), R2min=("R2", "min"),
                                            R2max=("R2", "max"), RMSE=("RMSE", "mean")).round(3).to_string())
        print(f"\npooled: mean R2 {out.R2.mean():.3f}, median R2 {out.R2.median():.3f}")


if __name__ == "__main__":
    main()
