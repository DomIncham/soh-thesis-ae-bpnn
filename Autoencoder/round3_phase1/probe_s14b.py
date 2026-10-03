# Leakage probe for the Phase 1 refit path (Round 2's probe_s14.py covered the 2-battery path).
# Perturb the outer-test battery's features x2 and re-run the ENTIRE fold (config selection + refit).
# Requirement: the model's own fit metrics must not move - if any fit step secretly consumed the test
# battery (e.g. a scaler fitted on all data), doubling its features would shift the fit metrics.
# Deterministic: fold test=B0005, seed 42, reduced epoch budget to keep the probe quick.
# Device: default cpu; run the probe on the SAME device as the run you want to vouch for.
# Usage: python probe_s14b.py [--device cpu|cuda|auto]
import argparse
import numpy as np
from r3common import FEATS_ALL, load_td, soh_range_and_qref, run_fold, set_device, BATT

ap = argparse.ArgumentParser()
ap.add_argument("--device", default="cpu", choices=["cpu", "cuda", "auto"])
args = ap.parse_args()
set_device(args.device)

X, bids, soh, cyc = load_td(FEATS_ALL)
rng, qref = soh_range_and_qref()
TEST_B, SEED, BP_MAX, PAT = 1, 42, 100, 10

Xp = X.copy()
Xp[bids == TEST_B] *= 2.0
print(f"perturbation applied: {int(np.sum(bids == TEST_B))} rows of {BATT[TEST_B]} doubled")

res = {}
for tag, Xd in [("baseline", X), ("perturbed", Xp)]:
    r, _ = run_fold(Xd, bids, soh, cyc, TEST_B, SEED, BP_MAX, PAT, qref, rng, "TD-All")
    res[tag] = {x["stage"]: x for x in r}

worst = 0.0
for stage in ("pre_refit", "refit_on_3"):
    a, b = res["baseline"][stage], res["perturbed"][stage]
    d = max(abs(a[k] - b[k]) for k in ("train_RMSE", "train_R2"))
    worst = max(worst, d)
    print(f"{stage:11s} baseline fit RMSE={a['train_RMSE']:.6f} R2={a['train_R2']:.6f} | "
          f"perturbed fit RMSE={b['train_RMSE']:.6f} R2={b['train_R2']:.6f} | max|diff|={d:.2e}")

print(f"\nprobe verdict: max|diff| = {worst:.2e} -> "
      f"{'PASS: no leakage (fit metrics unmoved by perturbed outer test)' if worst < 1e-6 else 'CHECK: fit metrics moved - investigate'}")
