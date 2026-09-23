# Step A4+A5: Quality sweep — all 4 batteries, all impedance cycles
import scipy.io as sio
import numpy as np

BASE = r"C:\Master Degree\Thesis\NASA DataSet\1. BatteryAgingARC-FY08Q4"
rows = []
for batt in ["B0005", "B0006", "B0007", "B0018"]:
    cyc = sio.loadmat(f"{BASE}\\{batt}.mat", struct_as_record=False, squeeze_me=True)[batt].cycle
    imps = [(i, c) for i, c in enumerate(cyc) if str(c.type) == "impedance"]
    pt_counts, nan_c, inf_c, dup_f, nonmono, re_mismatch = {}, 0, 0, 0, 0, 0
    im_max = 0.0
    for mi, c in imps:
        ri = np.asarray(c.data.Rectified_Impedance)
        n = len(ri)
        pt_counts[n] = pt_counts.get(n, 0) + 1
        if np.isnan(ri).any(): nan_c += 1
        if np.isinf(ri).any(): inf_c += 1
        re_ = ri.real; negim = -ri.imag
        if len(set(zip(np.round(re_,12), np.round(negim,12)))) < n: dup_f += 1  # duplicated impedance values
        # expected order: low f first (Re starts high, ends ~Re field); flag if Re(last) far from Re field
        if abs(re_[-1] - c.data.Re) > 0.005 and abs(re_[-2] - c.data.Re) > 0.005: re_mismatch += 1
        im_max = max(im_max, np.abs(ri.imag).max())
    rows.append((batt, len(imps), pt_counts, nan_c, inf_c, dup_f, re_mismatch, im_max))
    print(f"{batt}: imp_cycles={len(imps)} pts/spectrum={pt_counts} NaN={nan_c} Inf={inf_c} "
          f"duplicated_pts={dup_f} ReField!=last2Re:{re_mismatch} max|Im|={im_max:.4f} Ohm")

# cross-measurement mixing check (A4): cycle time strictly increasing + one struct per spectrum
for batt in ["B0005"]:
    cyc = sio.loadmat(f"{BASE}\\{batt}.mat", struct_as_record=False, squeeze_me=True)[batt].cycle
    times = [float(np.asarray(c.time).ravel()[-1]) for c in cyc]  # year field monotonic proxy
    print(f"\n{batt} cycle time field strictly increasing: {all(t2>t1 for t1,t2 in zip(times,times[1:]))}")
