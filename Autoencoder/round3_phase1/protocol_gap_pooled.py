# Pooled metrics for the protocol-gap experiment (advisor R3-C1 reporting standard: per-fold mean
# AND pooled, RMSE in %SOH and Ah, MAPE).
# Pooled = the outer-test blocks of a protocol concatenated. For the within-battery and LOBO
# protocols the blocks together cover all 636 cycles. random_pooled has a single 127-row outer test
# set, so its pooled block is smaller by construction - reported as-is, not rescaled.
# Usage: python protocol_gap_pooled.py
import os
import numpy as np
import pandas as pd
import r3common
from r3common import OUT, BATT

REV = {v: k for k, v in BATT.items()}
KEYS = ["pooled_R2", "pooled_RMSE", "pooled_MAE", "pooled_MAPE", "pooled_RMSE_Ah", "pooled_nRMSE"]


def pooled_block(df, qref, rng_span, span_pooled):
    y, yh = df.y_true.values, df.y_pred.values
    rmse = float(np.sqrt(np.mean((y - yh) ** 2)))
    if df.test_battery.iloc[0] == "pooled":
        q, span = float(qref.mean()), span_pooled
    else:
        b = REV[df.test_battery.iloc[0]]
        q, span = float(qref.loc[b]), float(rng_span.loc[b])
    return dict(n=len(y),
                pooled_R2=float(1 - ((y - yh) ** 2).sum() / ((y - y.mean()) ** 2).sum()),
                pooled_RMSE=rmse,
                pooled_MAE=float(np.mean(np.abs(y - yh))),
                pooled_MAPE=float(np.mean(np.abs((y - yh) / y)) * 100),
                pooled_RMSE_Ah=rmse / 100.0 * q,
                pooled_nRMSE=rmse / span)


rng_span, qref = r3common.soh_range_and_qref()
p = pd.read_csv(os.path.join(OUT, "protocol_gap_exp_cpu_preds.csv"))
p.columns = [c.strip() for c in p.columns]
span_pooled = float(p.y_true.max() - p.y_true.min())

rows = []
for (sp, se, st, sd), g in p.groupby(["split", "setting", "stage", "seed"]):
    rows.append(dict(split=sp, setting=se, stage=st, seed=int(sd), scope="per_seed_pooled",
                     **pooled_block(g, qref, rng_span, span_pooled)))
for (sp, se, st), g in p.groupby(["split", "setting", "stage"]):
    rows.append(dict(split=sp, setting=se, stage=st, seed=-1, scope="grand_pooled_all_seeds",
                     **pooled_block(g, qref, rng_span, span_pooled)))
out = pd.DataFrame(rows)
out.to_csv(os.path.join(OUT, "protocol_gap_exp_cpu_pooled.csv"), index=False)

ps = out[out.scope == "per_seed_pooled"]
print("=== pooled (outer-test blocks concatenated), mean / median / std across seeds ===\n")
agg = ps.groupby(["split", "setting", "stage"])[KEYS].agg(["mean", "median", "std"]).round(4)
print(agg[["pooled_R2", "pooled_RMSE", "pooled_MAPE", "pooled_RMSE_Ah"]].to_string())
print("\n=== grand pooled (all seeds) ===")
print(out[out.scope == "grand_pooled_all_seeds"][
    ["split", "setting", "stage", "n", "pooled_R2", "pooled_RMSE", "pooled_MAPE"]]
    .round(4).to_string(index=False))
print("\nsaved: protocol_gap_exp_cpu_pooled.csv")