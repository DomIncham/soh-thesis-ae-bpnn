# B7 evidence: Pipeline E (TD + EIS-latent fusion) and AE-on-TD, under the same nested-LOBO protocol
# E_fusion: AE(256->17, EIS) latent + 8 TD features -> BPNN. AE_on_TD: AE(8->4) on TD features -> BPNN.
import argparse, itertools, os
import numpy as np, pandas as pd, torch
from sklearn.preprocessing import MinMaxScaler

from nested_lobo_harness import ControlledAutoencoder, train_model, BPNN, fit_bpnn, reg_metrics

HERE = os.path.dirname(os.path.abspath(__file__))
BATT = {1: "B0005", 2: "B0006", 3: "B0007", 4: "B0018"}
ARCHS, L2S = [[8], [16], [8, 4]], [0.0, 1e-4]

def rmse_(a, b): return float(np.sqrt(np.mean((np.asarray(a) - np.asarray(b)) ** 2)))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true"); ap.add_argument("--full", action="store_true")
    args = ap.parse_args()
    smoke = args.smoke
    seeds = [42] if smoke else [42, 7, 123]
    folds = [1] if smoke else [1, 2, 3, 4]
    max_ep, pat = (60, 10) if smoke else (500, 30)
    cap = pd.read_csv(os.path.join(HERE, "..", "NASA_Capacity_Data.csv"), dtype={"Battery_ID": int, "Cycle": int})
    qref = cap.sort_values("Cycle").groupby("Battery_ID").head(5).groupby("Battery_ID").Capacity_Ah.mean()

    eis = torch.load(os.path.join(HERE, "Mapped_EIS_SOH_tol1.pt"), weights_only=True)
    Xe, ye = eis["features"].numpy(), eis["labels"].numpy()
    be, sohe = ye[:, 0].astype(int), ye[:, 3]
    td = pd.read_csv(os.path.join(HERE, "time_domain_features.csv"))
    feats = ["dis_duration","dis_mean_V","dis_mean_T","dis_V_slope","cc_dur","cv_dur","cv_I_slope","ch_mean_T"]
    Xt, bt, soht = td[feats].values, td.battery.values.astype(int), td.soh.values

    rows = []
    for seed, test_b in itertools.product(seeds, folds):
        remaining = [b for b in [1,2,3,4] if b != test_b]
        val_b, train_b = remaining[0], remaining[1:]
        # --- EIS side (AE trained per fold, same as harness)
        me_tr, me_va, me_te = np.isin(be, train_b), (be == val_b), (be == test_b)
        sce = MinMaxScaler().fit(Xe[me_tr])
        E = {k: torch.tensor(sce.transform(Xe[m]), dtype=torch.float32) for k, m in [("tr", me_tr), ("va", me_va), ("te", me_te)]}
        torch.manual_seed(seed)
        ae_e = ControlledAutoencoder(256, 17)
        train_model(ae_e, E["tr"], E["va"], 1e-3, 16, max_ep, pat, seed)
        with torch.no_grad():
            Ze = {k: ae_e.encoder(v).numpy() for k, v in E.items()}
        # --- TD side
        mt_tr, mt_va, mt_te = np.isin(bt, train_b), (bt == val_b), (bt == test_b)
        sct = MinMaxScaler().fit(Xt[mt_tr])
        T = {k: sct.transform(Xt[m]) for k, m in [("tr", mt_tr), ("va", mt_va), ("te", mt_te)]}
        mu_t, sd_t = soht[mt_tr].mean(), soht[mt_tr].std()
        # --- E_fusion: TD features + EIS latent, aligned CAUSALLY in time:
        # each TD cycle (b, c) takes the latent of the LATEST EIS cycle of battery b with cycle <= c
        # (no future data, no test-set statistics; deployable: use the latest available EIS measurement)
        rows_e = {k: np.where(m)[0] for k, m in [("tr", me_tr), ("va", me_va), ("te", me_te)]}
        e_cycles = {k: ye[ridx, 1].astype(int) for k, ridx in rows_e.items()}
        e_bids = {k: be[ridx] for k, ridx in rows_e.items()}
        def fuse_latent(k, td_b, td_c):
            arr_b, arr_c = e_bids[k], e_cycles[k]
            out = np.zeros((len(td_c), Ze[k].shape[1]))
            for i, (b, c) in enumerate(zip(td_b, td_c)):
                same = np.where(arr_b == b)[0]
                j = np.searchsorted(arr_c[same], c, side="right") - 1
                j = j if j >= 0 else 0  # no earlier EIS yet -> earliest available (declared)
                out[i] = Ze[k][same[j]]
            return out
        # build aligned feature matrices explicitly (readable, no clever tricks)
        def build_aligned(k, mt):
            Xtd = T[k]
            lat = fuse_latent(k, bt[mt], td[mt].cycle.values.astype(int))
            return np.hstack([Xtd, lat])
        A_tr, A_va, A_te = build_aligned("tr", mt_tr), build_aligned("va", mt_va), build_aligned("te", mt_te)
        for pipeline, (Ztr, Zva, Zte, dim, ae_needed) in [
            ("E_fusion_td_eis", (A_tr, A_va, A_te, 25, False)),
            ("AE_on_TD", (T["tr"], T["va"], T["te"], 8, True)),
        ]:
            yz_tr = ((soht[mt_tr] - mu_t) / sd_t).astype(np.float32)
            yz_va = ((soht[mt_va] - mu_t) / sd_t).astype(np.float32)
            if ae_needed:
                torch.manual_seed(seed)
                ae_t = ControlledAutoencoder(8, 4)
                train_model(ae_t, torch.tensor(Ztr, dtype=torch.float32), torch.tensor(Zva, dtype=torch.float32),
                            1e-3, 16, max_ep, pat, seed)
                with torch.no_grad():
                    Ztr = ae_t.encoder(torch.tensor(Ztr, dtype=torch.float32)).numpy()
                    Zva = ae_t.encoder(torch.tensor(Zva, dtype=torch.float32)).numpy()
                    Zte = ae_t.encoder(torch.tensor(Zte, dtype=torch.float32)).numpy()
                dim = 4
            best = None
            for dims, l2 in itertools.product(ARCHS, L2S):
                bp = fit_bpnn([dim] + dims, l2, Ztr, yz_tr, Zva, yz_va, seed, max_ep, pat)
                with torch.no_grad():
                    pv = bp(torch.tensor(Zva, dtype=torch.float32)).numpy() * sd_t + mu_t
                v = rmse_(pv, soht[mt_va])
                if best is None or v < best[0]:
                    with torch.no_grad():
                        pte = bp(torch.tensor(Zte, dtype=torch.float32)).numpy() * sd_t + mu_t
                    best = (v, f"{dims}/l2={l2}", pte)
            v, cfg, pte = best
            mae, t_rmse, r2 = reg_metrics(soht[mt_te], pte)
            capb = cap[cap.Battery_ID == test_b].Capacity_Ah
            nr = float((capb.max() - capb.min()) / qref.loc[test_b] * 100)
            rows.append(dict(pipeline=pipeline, seed=seed, test_battery=BATT[test_b], cfg=cfg,
                             val_rmse=round(v, 4), test_MAE=round(mae, 4), test_RMSE=round(t_rmse, 4),
                             test_R2=round(r2, 4), nRMSE=round(t_rmse / nr, 4)))
        print(f"seed{seed} test={BATT[test_b]} done")
    res = pd.DataFrame(rows)
    res.to_csv(os.path.join(HERE, "b7_smoke_results.csv" if smoke else "b7_results.csv"), index=False)
    if not smoke:
        agg = res.groupby("pipeline")[["test_MAE","test_RMSE","test_R2","nRMSE"]].agg(["mean","std"]).round(3)
        print(agg.to_string()); agg.to_csv(os.path.join(HERE, "b7_summary.csv"))
        print(res.pivot_table(index="test_battery", columns="pipeline", values="test_R2").round(3).to_string())
    print("saved")

if __name__ == "__main__":
    main()