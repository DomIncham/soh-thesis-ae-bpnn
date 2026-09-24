# F3/I3 ablations under the nested-LOBO protocol: --mode bottleneck | loss | interp
# bottleneck: AE sizes {3,7,17,37,67} (tol1, 60 AE+BPNN runs) | loss: {mse,mae,huber} (arch from majority pick) |
# interp: all 6 grid x method configs mapped at tolerance 1 (isolate interpolation variable; tol1 per Step 8 decision)
import argparse, itertools, os
import numpy as np, pandas as pd, torch
import torch.nn as nn, torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sklearn.preprocessing import MinMaxScaler

from nested_lobo_harness import ControlledAutoencoder, BPNN, train_model, reg_metrics

HERE = os.path.dirname(os.path.abspath(__file__))
AUTO = os.path.dirname(HERE)
BATT = {1: "B0005", 2: "B0006", 3: "B0007", 4: "B0018"}
ARCHS, L2S = [[8], [16], [8, 4]], [0.0, 1e-4]
LOSSES = {"mse": nn.MSELoss(), "mae": nn.L1Loss(), "huber": nn.SmoothL1Loss()}

def rmse_(a, b): return float(np.sqrt(np.mean((np.asarray(a) - np.asarray(b)) ** 2)))

def fit_bpnn_loss(dims, l2, loss_name, Ztr, ytr, Zva, yva, seed, max_ep, patience, lr=1e-3):
    torch.manual_seed(seed); np.random.seed(seed)
    bp = BPNN(dims, l2)
    opt = optim.Adam(bp.parameters(), lr=lr, weight_decay=l2)
    loader = DataLoader(TensorDataset(torch.tensor(Ztr, dtype=torch.float32),
                                      torch.tensor(ytr, dtype=torch.float32)), batch_size=32, shuffle=True)
    crit = LOSSES[loss_name]
    best_v, best_state, bad = np.inf, None, 0
    for ep in range(max_ep):
        bp.train()
        for zb, tb in loader:
            opt.zero_grad(); loss = crit(bp(zb), tb); loss.backward(); opt.step()
        bp.eval()
        with torch.no_grad():
            v = nn.functional.mse_loss(bp(torch.tensor(Zva, dtype=torch.float32)),
                                       torch.tensor(yva, dtype=torch.float32)).item()  # select on RMSE-equivalent MSE
        if v < best_v - 1e-12:
            best_v, bad = v, 0; best_state = {k: t.clone() for k, t in bp.state_dict().items()}
        else:
            bad += 1
            if bad >= patience: break
    bp.load_state_dict(best_state); bp.eval()
    return bp

def map_tol1(X, lbl, cap):
    cap = cap.copy(); cap["Battery_ID"] = cap.Battery_ID.astype(int); cap["Cycle"] = cap.Cycle.astype(int)
    qref = cap.sort_values("Cycle").groupby("Battery_ID").head(5).groupby("Battery_ID").Capacity_Ah.mean()
    keep_i, keep_b, keep_c, keep_cap = [], [], [], []
    for b in [1, 2, 3, 4]:
        sel = lbl[:, 0] == b
        cyc = np.sort(lbl[sel, 1])
        cb = cap[cap.Battery_ID == b].sort_values("Cycle")
        cc, cv = cb.Cycle.values, cb.Capacity_Ah.values
        for c in cyc:
            j = np.searchsorted(cc, c, side="right") - 1
            if j >= 0 and c - cc[j] <= 1:
                idx = np.where((lbl[:, 0] == b) & (lbl[:, 1] == c))[0][0]
                keep_i.append(idx); keep_b.append(b); keep_c.append(int(c)); keep_cap.append(float(cv[j]))
    soh = np.array(keep_cap) / np.array([qref[b] for b in keep_b]) * 100.0
    return X[np.array(keep_i)], np.column_stack([keep_b, keep_c, keep_cap, soh])

def run_fold_pipe(X, soh_all, bids_all, test_b, seed, ae_dim, smoke):
    remaining = [b for b in [1, 2, 3, 4] if b != test_b]
    val_b, train_b = remaining[0], remaining[1:]
    m_tr, m_va, m_te = np.isin(bids_all, train_b), (bids_all == val_b), (bids_all == test_b)
    sc = MinMaxScaler().fit(X[m_tr])
    assert np.allclose(sc.data_min_, X[m_tr].min(0)), "LEAKAGE"
    Xs = {k: torch.tensor(sc.transform(X[m]), dtype=torch.float32) for k, m in [("tr", m_tr), ("va", m_va), ("te", m_te)]}
    mu, sd = soh_all[m_tr].mean(), soh_all[m_tr].std()
    yz = {k: ((soh_all[m] - mu) / sd).astype(np.float32) for k, m in [("tr", m_tr), ("va", m_va)]}
    max_ep, pat = (60, 10) if smoke else (500, 30)
    torch.manual_seed(seed)
    ae = ControlledAutoencoder(256, ae_dim)
    ae_ep = train_model(ae, Xs["tr"], Xs["va"], 1e-3, 16, max_ep, pat, seed)
    with torch.no_grad():
        Z = {k: ae.encoder(v).numpy() for k, v in Xs.items()}
    best = None
    for dims, l2 in itertools.product(ARCHS, L2S):
        bp = fit_bpnn_loss([ae_dim] + dims, l2, "mse", Z["tr"], yz["tr"], Z["va"], yz["va"], seed, max_ep, pat)
        with torch.no_grad():
            pv = bp(torch.tensor(Z["va"], dtype=torch.float32)).numpy() * sd + mu
        v = rmse_(pv, soh_all[m_va])
        if best is None or v < best[0]:
            with torch.no_grad():
                pte = bp(torch.tensor(Z["te"], dtype=torch.float32)).numpy() * sd + mu
            best = (v, f"{dims}/l2={l2}", pte)
    v, cfg, pte = best
    mae, t_rmse, r2 = reg_metrics(soh_all[m_te], pte)
    return dict(cfg=cfg, ae_epochs=ae_ep, val_rmse=round(v, 4), test_MAE=round(mae, 4),
                test_RMSE=round(t_rmse, 4), test_R2=round(r2, 4))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["bottleneck", "loss", "interp"], required=True)
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()
    smoke = args.smoke
    seeds = [42] if smoke else [42, 7, 123]
    folds = [1] if smoke else [1, 2, 3, 4]
    cap = pd.read_csv(os.path.join(AUTO, "NASA_Capacity_Data.csv"))
    rows = []
    if args.mode == "bottleneck":
        data = torch.load(os.path.join(HERE, "Mapped_EIS_SOH_tol1.pt"), weights_only=True)
        X, y = data["features"].numpy(), data["labels"].numpy()
        bids, soh = y[:, 0].astype(int), y[:, 3]
        sizes = [17] if smoke else [3, 7, 17, 37, 67]
        for size, seed, test_b in itertools.product(sizes, seeds, folds):
            r = run_fold_pipe(X, soh, bids, test_b, seed, size, smoke)
            r.update(mode="bottleneck", value=size, seed=seed, test_battery=BATT[test_b])
            rows.append(r); print(r)
        out = "abl_bottleneck"
    elif args.mode == "loss":
        data = torch.load(os.path.join(HERE, "Mapped_EIS_SOH_tol1.pt"), weights_only=True)
        X, y = data["features"].numpy(), data["labels"].numpy()
        bids, soh = y[:, 0].astype(int), y[:, 3]
        losses = ["mse"] if smoke else ["mse", "mae", "huber"]
        for seed, test_b in itertools.product(seeds, folds):
            remaining = [b for b in [1, 2, 3, 4] if b != test_b]
            val_b, train_b = remaining[0], remaining[1:]
            m_tr, m_va, m_te = np.isin(bids, train_b), (bids == val_b), (bids == test_b)
            sc = MinMaxScaler().fit(X[m_tr])
            Xs = {k: torch.tensor(sc.transform(X[m]), dtype=torch.float32) for k, m in [("tr", m_tr), ("va", m_va), ("te", m_te)]}
            mu, sd = soh[m_tr].mean(), soh[m_tr].std()
            yz = {k: ((soh[m] - mu) / sd).astype(np.float32) for k, m in [("tr", m_tr), ("va", m_va)]}
            max_ep, pat = (60, 10) if smoke else (500, 30)
            torch.manual_seed(seed)
            ae = ControlledAutoencoder(256, 17)
            ae_ep = train_model(ae, Xs["tr"], Xs["va"], 1e-3, 16, max_ep, pat, seed)
            with torch.no_grad():
                Z = {k: ae.encoder(v).numpy() for k, v in Xs.items()}
            for loss_name in losses:
                best = None
                for dims in ARCHS:  # l2 fixed 1e-4 (majority pick in Steps 7-8) to bound cost
                    bp = fit_bpnn_loss([17] + dims, 1e-4, loss_name, Z["tr"], yz["tr"], Z["va"], yz["va"], seed, max_ep, pat)
                    with torch.no_grad():
                        pv = bp(torch.tensor(Z["va"], dtype=torch.float32)).numpy() * sd + mu
                    v = rmse_(pv, soh[m_va])
                    if best is None or v < best[0]:
                        with torch.no_grad():
                            pte = bp(torch.tensor(Z["te"], dtype=torch.float32)).numpy() * sd + mu
                        best = (v, f"{dims}/l2=1e-4", pte)
                v, cfg, pte = best
                mae, t_rmse, r2 = reg_metrics(soh[m_te], pte)
                rows.append(dict(mode="loss", value=loss_name, seed=seed, test_battery=BATT[test_b],
                                 cfg=cfg, ae_epochs=ae_ep, val_rmse=round(v, 4), test_MAE=round(mae, 4),
                                 test_RMSE=round(t_rmse, 4), test_R2=round(r2, 4))); print(rows[-1])
        out = "abl_loss"
    else:  # interp: 6 configs at tolerance 1
        configs = [("log_grid", "pchip")] if smoke else \
            [(g, m) for g in ["linear_grid", "log_grid"] for m in ["linear", "cubic", "pchip"]]
        for g, m in configs:
            eis = torch.load(os.path.join(AUTO, f"Interpolated_EIS_{g}_{m}.pt"), weights_only=True)
            X, y = eis["features"].numpy(), eis["labels"].numpy()
            X1, y1 = map_tol1(X, y, cap)
            bids, soh = y1[:, 0].astype(int), y1[:, 3]
            print(f"config {g}_{m}: rows={len(X1)}")
            for seed, test_b in itertools.product(seeds, folds):
                r = run_fold_pipe(X1, soh, bids, test_b, seed, 17, smoke)
                r.update(mode="interp", value=f"{g}_{m}", seed=seed, test_battery=BATT[test_b])
                rows.append(r); print(r)
        out = "abl_interp"
    res = pd.DataFrame(rows)
    suffix = "_smoke" if smoke else ""
    res.to_csv(os.path.join(HERE, f"{out}{suffix}.csv"), index=False)
    if not smoke:
        agg = res.groupby("value")[["test_MAE", "test_RMSE", "test_R2"]].agg(["mean", "std"]).round(4)
        print("\n=== aggregate ==="); print(agg.to_string())
        agg.to_csv(os.path.join(HERE, f"{out}_summary.csv"))
    print("saved:", out)

if __name__ == "__main__":
    main()