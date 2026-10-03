# Round 3 / Phase 1 shared utilities.

# Single source of truth for the BPNN stays Round 2's nested_lobo/nested_lobo_harness.py (imported via
# sys.path, NOT copied). The only local variant is fit_bpnn_ep(), which mirrors harness.fit_bpnn
# line-for-line but also returns the early-stopping best epoch, so the refit stage can reuse the
# epoch budget that inner validation selected.
import os, sys, itertools
import numpy as np, pandas as pd, torch
from sklearn.preprocessing import MinMaxScaler

HERE = os.path.dirname(os.path.abspath(__file__))
R2 = os.path.abspath(os.path.join(HERE, "..", "nested_lobo"))
AUTOENC = os.path.abspath(os.path.join(R2, ".."))
if R2 not in sys.path:
    sys.path.insert(0, R2)
from nested_lobo_harness import BPNN, reg_metrics  # noqa: E402

BATT = {1: "B0005", 2: "B0006", 3: "B0007", 4: "B0018"}
TD_CSV = os.path.join(R2, "time_domain_features.csv")
CAP_CSV = os.path.join(AUTOENC, "NASA_Capacity_Data.csv")
OUT = HERE

FEATS_ALL = ["dis_duration", "dis_mean_V", "dis_mean_T", "dis_V_slope",
             "cc_dur", "cv_dur", "cv_I_slope", "ch_mean_T"]
PROXY_FEATS = ["dis_duration"]  # CC discharge at constant current: Capacity = I x t
FEATS_PROXY_FREE = [f for f in FEATS_ALL if f not in PROXY_FEATS]
ARCHS, L2S = [[8], [16], [8, 4]], [0.0, 1e-4]  # same grid as Round 2 (comparability)

SETTINGS = {"TD-All": FEATS_ALL,
            "TD-Proxy-Free": FEATS_PROXY_FREE,
            "Oracle-proxy": PROXY_FEATS}

# ---- device handling -------------------------------------------------------------------------
# Default stays CPU: every Round 2 number was produced on CPU and the refit comparison is only
# meaningful on the same device. GPU is opt-in via --device cuda / --device auto.
# TF32 is forced off so GPU arithmetic stays fp32 (matmul.allow_tf32 is already False here, but
# cudnn.allow_tf32 defaults to True and would silently change numbers if convolution ever appears).
DEVICE = torch.device("cpu")


def set_device(name="cpu"):
    global DEVICE
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    if name == "auto":
        name = "cuda" if torch.cuda.is_available() else "cpu"
    if name == "cuda" and not torch.cuda.is_available():
        raise SystemExit("--device cuda requested but torch.cuda.is_available() is False")
    DEVICE = torch.device(name, 0) if name == "cuda" else torch.device(name)
    if DEVICE.type == "cuda":
        torch.cuda.set_device(DEVICE)  # torch.device("cuda") carries no index; set_device needs cuda:0
        torch.cuda.manual_seed_all(0)
        print(f"[device] {torch.cuda.get_device_name(DEVICE)} | "
              f"{torch.cuda.get_device_properties(DEVICE).total_memory / 1e9:.1f} GB | "
              f"tf32 matmul={torch.backends.cuda.matmul.allow_tf32} cudnn={torch.backends.cudnn.allow_tf32}")
    else:
        print(f"[device] cpu | threads={torch.get_num_threads()}")
    return DEVICE


def load_td(feats):
    td = pd.read_csv(TD_CSV)
    missing = [f for f in feats if f not in td.columns]
    assert not missing, f"missing feature columns: {missing}"
    return (td[feats].values.astype(np.float64), td["battery"].values.astype(int),
            td["soh"].values.astype(np.float64), td["cycle"].values.astype(int))


def soh_range_and_qref():
    """Per-battery SOH span (nRMSE denominator) and Q_ref Ah, same formulas as Round 2."""
    cap = pd.read_csv(CAP_CSV, dtype={"Battery_ID": int, "Cycle": int})
    qref = cap.sort_values("Cycle").groupby("Battery_ID").head(5).groupby("Battery_ID").Capacity_Ah.mean()
    rng = (cap.groupby("Battery_ID").Capacity_Ah.max()
           - cap.groupby("Battery_ID").Capacity_Ah.min()) / qref * 100
    return rng, qref


def fit_bpnn_ep(dims, l2, Ztr, ytr, Zva, yva, seed, max_ep, patience, lr=1e-3, epochs=None):
    """harness.fit_bpnn + best_epoch. If `epochs` is given, trains exactly that many epochs on
    (Ztr, ytr) with no early stopping and returns the final model (used for the refit stage)."""
    torch.manual_seed(seed); np.random.seed(seed)
    if DEVICE.type == "cuda":
        torch.cuda.manual_seed_all(seed)
    bp = BPNN(dims, l2).to(DEVICE)
    opt = torch.optim.Adam(bp.parameters(), lr=lr, weight_decay=l2)
    loader = torch.utils.data.DataLoader(
        torch.utils.data.TensorDataset(torch.tensor(np.asarray(Ztr), dtype=torch.float32, device=DEVICE),
                                       torch.tensor(np.asarray(ytr), dtype=torch.float32, device=DEVICE)),
        batch_size=32, shuffle=True)
    if epochs is not None:
        bp.train()
        for _ in range(int(epochs)):
            for zb, tb in loader:
                opt.zero_grad()
                loss = torch.nn.functional.mse_loss(bp(zb), tb)
                loss.backward(); opt.step()
        bp.eval()
        return bp, int(epochs)
    best_v, best_state, best_ep, bad = float("inf"), None, 0, 0
    for ep in range(max_ep):
        bp.train()
        for zb, tb in loader:
            opt.zero_grad()
            loss = torch.nn.functional.mse_loss(bp(zb), tb)
            loss.backward(); opt.step()
        bp.eval()
        with torch.no_grad():
            v = torch.nn.functional.mse_loss(
                bp(torch.tensor(np.asarray(Zva), dtype=torch.float32, device=DEVICE)),
                torch.tensor(np.asarray(yva), dtype=torch.float32, device=DEVICE)).item()
        if v < best_v - 1e-12:
            best_v, bad, best_ep = v, 0, ep
            best_state = {k: t.clone() for k, t in bp.state_dict().items()}
        else:
            bad += 1
            if bad >= patience:
                break
    bp.load_state_dict(best_state); bp.eval()
    return bp, best_ep + 1


def predict(model, Z, mu, sd):
    with torch.no_grad():
        out = model(torch.tensor(np.asarray(Z), dtype=torch.float32, device=DEVICE))
    return out.detach().cpu().numpy() * sd + mu


def extras(y, yh, qref_ah):
    """MAE / RMSE / R2 (%SOH) + MAPE + RMSE,MAE in Ah (advisor R3-C1)."""
    mae, rmse, r2 = reg_metrics(y, yh)
    return dict(test_MAE=float(mae), test_RMSE=float(rmse), test_R2=float(r2),
                test_MAPE=float(np.mean(np.abs((y - yh) / y)) * 100),
                test_MAE_Ah=float(mae) / 100.0 * float(qref_ah),
                test_RMSE_Ah=float(rmse) / 100.0 * float(qref_ah))


def run_fold(X, bids, soh, cyc, test_b, seed, bp_max, pat, qref, rng, setting):
    """One outer fold, both stages.
    Stage A (pre_refit): inner validation on 1 battery selects the config - Round 2 protocol.
    Stage B (refit_on_3): the selected config is re-fitted on ALL 3 remaining batteries for the
    selected epoch budget (advisor R3-C1), then evaluated on the untouched outer test battery.
    Scaling and target standardization are fitted on the fitting batteries only; the test battery
    never enters any fit.
    """
    n_in = X.shape[1]
    remaining = [b for b in [1, 2, 3, 4] if b != test_b]
    val_b, train_b = remaining[0], remaining[1:]
    m_tr, m_va, m_te = np.isin(bids, train_b), (bids == val_b), (bids == test_b)
    m_all = np.isin(bids, remaining)

    # ---- Stage A: select config by inner validation (fold-train scaling only) ----
    sc = MinMaxScaler().fit(X[m_tr])
    assert np.allclose(sc.data_min_, X[m_tr].min(0)), "LEAKAGE: selection scaler != fold-train"
    tr_s, va_s = sc.transform(X[m_tr]), sc.transform(X[m_va])
    mu, sd = soh[m_tr].mean(), soh[m_tr].std()
    best = None
    for dims, l2 in itertools.product(ARCHS, L2S):
        bp, ep = fit_bpnn_ep([n_in] + dims, l2, tr_s, (soh[m_tr] - mu) / sd,
                             va_s, (soh[m_va] - mu) / sd, seed, bp_max, pat)
        v = float(np.sqrt(np.mean((predict(bp, va_s, mu, sd) - soh[m_va]) ** 2)))
        if best is None or v < best[0]:
            best = (v, dims, l2, ep, bp)
    v, dims, l2, ep, bp_sel = best

    # ---- Stage B: refit on all 3 remaining batteries, same epoch budget ----
    sc2 = MinMaxScaler().fit(X[m_all])
    assert np.allclose(sc2.data_min_, X[m_all].min(0)), "LEAKAGE: refit scaler != 3-battery train"
    # the refit set must be exactly the 3 remaining batteries (2-battery train + the val battery).
    # Structural, not statistical: min/max stats of two sets can coincide by accident, so comparing
    # scaler statistics cannot prove which batteries were used. Mask identity can.
    assert set(np.unique(bids[m_all])) == set(remaining) and set(np.unique(bids[m_tr])) == set(train_b), \
        "CHECK: refit mask is not the 3 remaining batteries"
    assert m_all.sum() == m_tr.sum() + m_va.sum(), "CHECK: refit mask != train + val rows"
    mu2, sd2 = soh[m_all].mean(), soh[m_all].std()
    bp_rf, _ = fit_bpnn_ep([n_in] + dims, l2, sc2.transform(X[m_all]), (soh[m_all] - mu2) / sd2,
                           None, None, seed, bp_max, pat, epochs=ep)

    rows, preds = [], []
    for stage, model, sce, mu_, sd_, fit_mask, fit_batteries in [
            ("pre_refit", bp_sel, sc, mu, sd, m_tr, train_b),
            ("refit_on_3", bp_rf, sc2, mu2, sd2, m_all, remaining)]:
        p_te = predict(model, sce.transform(X[m_te]), mu_, sd_)
        p_fit = predict(model, sce.transform(X[fit_mask]), mu_, sd_)
        _, trmse, tr2 = reg_metrics(soh[fit_mask], p_fit)
        ex = extras(soh[m_te], p_te, qref.loc[test_b])
        rows.append(dict(setting=setting, stage=stage, seed=seed, test_battery=BATT[test_b],
                         val_battery=BATT[val_b],
                         fit_batteries=str([BATT[b] for b in fit_batteries]),
                         cfg=f"{dims}/l2={l2}", sel_epochs=ep, sel_val_rmse=round(v, 4),
                         train_RMSE=round(float(trmse), 4), train_R2=round(float(tr2), 4),
                         test_nRMSE=round(ex["test_RMSE"] / float(rng.loc[test_b]), 4),
                         **{k: round(float(x), 4) for k, x in ex.items()}))
        preds.append(pd.DataFrame(dict(setting=setting, stage=stage, seed=seed,
                                       test_battery=BATT[test_b], cycle=cyc[m_te],
                                       y_true=soh[m_te], y_pred=p_te)))
    return rows, pd.concat(preds, ignore_index=True)
