# Steps 7-8: nested 4-fold LOBO harness + tolerance ablation (advisor Part C + Part E)
# Protocol (approved 2026-09-23): outer test rotates B0005/06/07/18; inner val = first of remaining
# batteries; AE (bottleneck 17) + BPNN candidates selected by inner val; SOH target standardized on
# fold-train only; EarlyStopping on inner-val loss; metrics MAE/RMSE/R2 in %SOH; seeds 42/7/123.
# Usage: python nested_lobo_harness.py --smoke | --full [--probe]
import argparse, itertools, os
import numpy as np, pandas as pd, torch
import torch.nn as nn, torch.optim as optim
from sklearn.preprocessing import MinMaxScaler

HERE = os.path.dirname(os.path.abspath(__file__))
torch.manual_seed(0)
BATT = {1: "B0005", 2: "B0006", 3: "B0007", 4: "B0018"}

class ControlledAutoencoder(nn.Module):
    def __init__(self, input_dim=256, bottleneck_dim=17):
        super().__init__()
        self.encoder = nn.Sequential(nn.Linear(input_dim, 128), nn.ReLU(), nn.Linear(128, bottleneck_dim))
        self.decoder = nn.Sequential(nn.Linear(bottleneck_dim, 128), nn.ReLU(), nn.Linear(128, input_dim))
    def forward(self, x):
        z = self.encoder(x); return self.decoder(z), z

def train_model(model, x_tr, x_va, lr, batch, max_ep, patience, seed):
    torch.manual_seed(seed); np.random.seed(seed)
    opt = optim.Adam(model.parameters(), lr=lr)
    loader = torch.utils.data.DataLoader(torch.utils.data.TensorDataset(x_tr, x_tr),
                                         batch_size=batch, shuffle=True)
    best_v, best_state, best_ep, bad = np.inf, None, 0, 0
    model.train()
    for ep in range(max_ep):
        for bx, _ in loader:
            opt.zero_grad(); out = model(bx)[0]
            loss = nn.functional.mse_loss(out, bx); loss.backward(); opt.step()
        model.eval()
        with torch.no_grad():
            v = nn.functional.mse_loss(model(x_va)[0], x_va).item()
        if v < best_v - 1e-12:
            best_v, best_ep, bad = v, ep, 0
            best_state = {k: t.clone() for k, t in model.state_dict().items()}
        else:
            bad += 1
            if bad >= patience: break
    if best_state is not None: model.load_state_dict(best_state)
    model.eval()
    return best_ep + 1

def reg_metrics(y, yh):
    mae = float(np.mean(np.abs(y - yh)))
    rmse = float(np.sqrt(np.mean((y - yh) ** 2)))
    ss = ((y - y.mean()) ** 2).sum()
    r2 = float(1 - ((y - yh) ** 2).sum() / ss) if ss > 0 else float("nan")
    return mae, rmse, r2

class BPNN(nn.Module):
    def __init__(self, dims, l2):
        super().__init__()
        layers, d = [], dims[0]
        for h in dims[1:]:
            layers += [nn.Linear(d, h), nn.ReLU()]; d = h
        layers += [nn.Linear(d, 1)]
        self.net = nn.Sequential(*layers)
        self.l2 = l2
    def forward(self, x): return self.net(x).squeeze(-1)

def fit_bpnn(dims, l2, Ztr, ytr, Zva, yva, seed, max_ep, patience, lr=1e-3):
    torch.manual_seed(seed); np.random.seed(seed)
    bp = BPNN(dims, l2)
    opt = optim.Adam(bp.parameters(), lr=lr, weight_decay=l2)
    loader = torch.utils.data.DataLoader(
        torch.utils.data.TensorDataset(torch.tensor(Ztr, dtype=torch.float32),
                                       torch.tensor(ytr, dtype=torch.float32)),
        batch_size=32, shuffle=True)
    best_v, best_state, bad = np.inf, None, 0
    for ep in range(max_ep):
        bp.train()
        for zb, tb in loader:
            opt.zero_grad()
            loss = nn.functional.mse_loss(bp(zb), tb)
            loss.backward(); opt.step()
        bp.eval()
        with torch.no_grad():
            v = nn.functional.mse_loss(bp(torch.tensor(Zva, dtype=torch.float32)),
                                       torch.tensor(yva, dtype=torch.float32)).item()
        if v < best_v - 1e-12:
            best_v, bad = v, 0
            best_state = {k: t.clone() for k, t in bp.state_dict().items()}
        else:
            bad += 1
            if bad >= patience: break
    bp.load_state_dict(best_state); bp.eval()
    return bp

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--matched", action="store_true",
                    help="add tolerance '3m': tol3 restricted to the exact sample set tol1 keeps "
                         "(isolates label quality from sample count)")
    args = ap.parse_args()
    tols = [3] if args.smoke else [1, 2, 3]
    seeds = [42] if args.smoke else [42, 7, 123]
    folds = [1, 2, 3, 4] if not args.smoke else [1]
    ae_max = 60 if args.smoke else 500
    bp_max = 100 if args.smoke else 500
    pat = 10 if args.smoke else 30

    data = {t: torch.load(os.path.join(HERE, f"Mapped_EIS_SOH_tol{t}.pt"), weights_only=True)
            for t in [1, 2, 3]}
    tol_list = list(tols)
    if args.matched:
        y1 = data[1]["labels"].numpy()
        keys1 = set(map(tuple, y1[:, :2].astype(int)))
        y3 = data[3]["labels"].numpy(); X3 = data[3]["features"].numpy()
        keep = np.array([tuple(map(int, r[:2])) in keys1 for r in y3])
        data["3m"] = {"features": torch.tensor(X3[keep], dtype=torch.float32),
                      "labels": torch.tensor(y3[keep], dtype=torch.float32)}
        tol_list.append("3m")
        print(f"matched subset: {int(keep.sum())} of {len(y3)} tol3 rows share tol1's sample set")
    tol_list = [t for t in tol_list]
    rows = []
    for tol, seed, test_b in itertools.product(tol_list, seeds, folds):
        y_all = data[tol]["labels"].numpy()
        bids = y_all[:, 0].astype(int)
        soh = y_all[:, 3]
        remaining = [b for b in [1, 2, 3, 4] if b != test_b]
        val_b, train_b = remaining[0], remaining[1:]
        m_tr, m_va, m_te = np.isin(bids, train_b), (bids == val_b), (bids == test_b)
        X, Xtr = data[tol]["features"].numpy(), None
        Xtr = X[m_tr]
        # structural leakage assert: scaler fitted on fold-train ONLY
        scaler = MinMaxScaler().fit(Xtr)
        assert np.allclose(scaler.data_min_, Xtr.min(0)) and np.allclose(scaler.data_max_, Xtr.max(0)), \
            "LEAKAGE: scaler stats != fold-train stats"
        Xs = {k: torch.tensor(scaler.transform(X[m]), dtype=torch.float32)
              for k, m in [("tr", m_tr), ("va", m_va), ("te", m_te)]}
        torch.manual_seed(seed)  # seed BEFORE model init: full run determinism
        ae = ControlledAutoencoder()
        ae_ep = train_model(ae, Xs["tr"], Xs["va"], 1e-3, 16, ae_max, pat, seed)
        with torch.no_grad():
            Z = {k: ae.encoder(v).numpy() for k, v in Xs.items()}
        mu, sd = soh[m_tr].mean(), soh[m_tr].std()
        yz = {k: torch.tensor(((soh[m] - mu) / sd), dtype=torch.float32)
              for k, m in [("tr", m_tr), ("va", m_va), ("te", m_te)]}
        best = None
        for dims, l2 in itertools.product([[8], [16], [8, 4]], [0.0, 1e-4]):
            bp = fit_bpnn([17] + dims, l2, Z["tr"], yz["tr"].numpy(), Z["va"], yz["va"].numpy(), seed, bp_max, pat)
            with torch.no_grad():
                pv = bp(torch.tensor(Z["va"], dtype=torch.float32)).numpy() * sd + mu
            va_rmse = float(np.sqrt(np.mean((pv - soh[m_va]) ** 2)))
            if best is None or va_rmse < best[0]:
                with torch.no_grad():
                    pt = bp(torch.tensor(Z["te"], dtype=torch.float32)).numpy() * sd + mu
                    ptr = bp(torch.tensor(Z["tr"], dtype=torch.float32)).numpy() * sd + mu
                best = (va_rmse, dims, l2, pt, ptr)
        va_rmse, dims, l2, pt, ptr = best
        mae, rmse, r2 = reg_metrics(soh[m_te], pt)
        tmae, trmse, tr2 = reg_metrics(soh[m_tr], ptr)
        rows.append(dict(tolerance=tol, seed=seed, test_battery=BATT[test_b],
                         val_battery=BATT[val_b], train_batteries=str([BATT[b] for b in train_b]),
                         bpnn_arch=str(dims), bpnn_l2=l2, ae_epochs=ae_ep,
                         val_rmse_soh=round(va_rmse, 4),
                         train_MAE=round(tmae, 4), train_RMSE=round(trmse, 4), train_R2=round(tr2, 4),
                         test_MAE=round(mae, 4), test_RMSE=round(rmse, 4), test_R2=round(r2, 4)))
        print(f"tol{tol} seed{seed} test={BATT[test_b]} val={BATT[val_b]} arch={dims} l2={l2} "
              f"ae_ep={ae_ep} | train R2={tr2:.3f} | TEST MAE={mae:.3f} RMSE={rmse:.3f} R2={r2:.3f}")
    out = os.path.join(HERE, "nested_lobo_smoke_results.csv" if args.smoke else "nested_lobo_results.csv")
    pd.DataFrame(rows).to_csv(out, index=False)
    df = pd.DataFrame(rows)
    if not args.smoke:
        agg = df.groupby("tolerance")[["test_MAE", "test_RMSE", "test_R2"]].agg(["mean", "std"]).round(4)
        print("\n=== aggregate per tolerance (mean +/- std across 4 folds x 3 seeds) ===")
        print(agg.to_string())
        agg.to_csv(os.path.join(HERE, "nested_lobo_tolerance_summary.csv"))
    print("saved:", out)

    if args.probe:
        print("\n=== leakage probe: perturb outer-test features x2, re-run fold (test=B0005, tol3, seed42) ===")
        base = df[(df.tolerance == 3) & (df.seed == 42) & (df.test_battery == "B0005")].iloc[0]
        print("baseline row:", base.to_dict())
        import ast
        base_dims = ast.literal_eval(base["bpnn_arch"]); base_l2 = float(base["bpnn_l2"])
        y_all = data[3]["labels"].numpy(); bids = y_all[:, 0].astype(int); soh = y_all[:, 3]
        Xd = data[3]["features"].numpy().copy()
        Xd[bids == 1] *= 2.0
        remaining = [b for b in [1, 2, 3, 4] if b != 1]
        val_b, train_b = remaining[0], remaining[1:]
        m_tr, m_va, m_te = np.isin(bids, train_b), (bids == val_b), (bids == 1)
        scaler = MinMaxScaler().fit(Xd[m_tr])
        Xs = {k: torch.tensor(scaler.transform(Xd[m]), dtype=torch.float32)
              for k, m in [("tr", m_tr), ("va", m_va), ("te", m_te)]}
        torch.manual_seed(42)
        ae = ControlledAutoencoder()
        ae_ep = train_model(ae, Xs["tr"], Xs["va"], 1e-3, 16, ae_max, pat, 42)
        with torch.no_grad():
            Zt = ae.encoder(Xs["tr"]).numpy()
        mu, sd = soh[m_tr].mean(), soh[m_tr].std()
        yz_tr = ((soh[m_tr] - mu) / sd).astype(np.float32)
        yz_va = ((soh[m_va] - mu) / sd).astype(np.float32)
        bp = fit_bpnn([17] + base_dims, base_l2, Zt, yz_tr,
                      ae.encoder(Xs["va"]).detach().numpy(), yz_va, 42, bp_max, pat)
        with torch.no_grad():
            ptr = bp(torch.tensor(Zt, dtype=torch.float32)).numpy() * sd + mu
        tmae, trmse, tr2 = reg_metrics(soh[m_tr], ptr)
        print(f"probe: train metrics with perturbed outer-test -> MAE={tmae:.6f} RMSE={trmse:.6f} R2={tr2:.6f}")
        print(f"probe config: dims={base_dims} l2={base_l2} | probe ae_ep={ae_ep} vs baseline ae_ep={int(base['ae_epochs'])}")
        diff = max(abs(tmae - float(base["train_MAE"])), abs(trmse - float(base["train_RMSE"])),
                   abs(tr2 - float(base["train_R2"])))
        print(f"probe verdict: max |diff| vs baseline = {diff:.2e} -> "
              f"{'PASS: no leakage (train metrics unmoved by perturbed outer test)' if diff < 1e-2 else 'CHECK: diff larger than run noise'}")

if __name__ == "__main__":
    main()
