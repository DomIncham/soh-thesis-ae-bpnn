# Round 5 advisor item R5-C4: dynamic structural proof that when B0006 is the OUTER test
# battery, B0006 appears in NO inner training or validation fold, and the inner loop is a
# genuine 3-fold rotation over {B0005, B0007, B0018}.
# Method: spy on fit_bpnn_ep during run_fold(test_b=B0006, inner='lobo3'); every inner fit's
# (ytr, yva) targets are the per-inner-fold standardized SOH ((soh-mui)/sdi, r3common.py:198-199),
# so each target vector is matched by multiset identity (round 1e-6, exact counts) against the
# corresponding battery's SOH vector standardized with that fold's own (mui, sdi).
# Exit 1 on any violation. Run: python r5_b0006_leak_probe.py
import sys
import numpy as np
import r3common as rc
from collections import Counter

names = {1: "B0005", 2: "B0006", 3: "B0007", 4: "B0018"}
OUTER = 2  # B0006

X, bids, soh, cyc = rc.load_td(rc.FEATS_ALL)


def std_fingerprint(b_set, v):
    """Multiset fingerprint of the standardized SOH for the inner fold whose train batteries
    are b_set and validation battery is v -- exactly what r3common.run_fold passes to
    fit_bpnn_ep at lines 198-199."""
    itr = np.isin(bids, b_set)
    iva = bids == v
    mui, sdi = soh[itr].mean(), soh[itr].std()
    return (Counter(np.round(((soh[itr] - mui) / sdi), 6).tolist()),
            Counter(np.round(((soh[iva] - mui) / sdi), 6).tolist()))


print("battery sizes:", {names[b]: len(soh[bids == b]) for b in [1, 2, 3, 4]})

cap = []
orig_fit = rc.fit_bpnn_ep


def spy(dims, l2, Ztr, ytr, Zva, yva, seed, max_ep, patience, lr=1e-3, epochs=None):
    if Zva is not None and len(Zva) > 0 and epochs is None:
        cap.append((Counter(np.round(np.asarray(ytr, dtype=float), 6).tolist()),
                    Counter(np.round(np.asarray(yva, dtype=float), 6).tolist())))
    return orig_fit(dims, l2, Ztr, ytr, Zva, yva, seed, max_ep, patience, lr, epochs)


rc.fit_bpnn_ep = spy
old_arch, old_l2 = rc.ARCHS, rc.L2S
rc.ARCHS, rc.L2S = [[8]], [0.0]
qref_r, qref = rc.soh_range_and_qref()
rc.run_fold(X, bids, soh, cyc, test_b=OUTER, seed=42, bp_max=25, pat=5, qref=qref,
            rng=qref_r, setting="S1b-probe", inner="lobo3")
rc.ARCHS, rc.L2S = old_arch, old_l2
rc.fit_bpnn_ep = orig_fit

fails = []
print(f"captured {len(cap)} inner fits")
expected = [([b for b in [1, 2, 3, 4] if b not in (OUTER, v)], v)
            for v in [1, 2, 3, 4] if v != OUTER]
matched = []
for ctr_tr, ctr_va in cap:
    this_ok = False
    for tr_spec, v in expected:
        ftr, fva = std_fingerprint(tr_spec, v)
        if ctr_tr == ftr and ctr_va == fva:
            print(f"  inner fold matched: train={[names[b] for b in tr_spec]} val={names[v]}")
            matched.append(v)
            this_ok = True
            break
    if not this_ok:
        fails.append(f"inner fit matches NO expected fold (tr n={sum(ctr_tr.values())}, "
                     f"va n={sum(ctr_va.values())})")

if len(cap) != 3:
    fails.append(f"expected 3 inner folds, saw {len(cap)}")
if sorted(matched) != sorted(v for _, v in expected):
    fails.append(f"rotation incomplete: matched val batteries = {matched}")

if fails:
    print("FAIL:", fails)
    sys.exit(1)
print("PASS: outer B0006 absent from every inner train/val fold; inner loop is a 3-fold "
      "rotation over B0005/B0007/B0018 (dynamic spy proof)")
