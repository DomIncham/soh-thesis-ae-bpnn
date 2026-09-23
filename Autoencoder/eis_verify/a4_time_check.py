# A4 final: proper time-monotonic check across all 4 batteries
import scipy.io as sio, numpy as np
from datetime import datetime

BASE = r"C:\Master Degree\Thesis\NASA DataSet\1. BatteryAgingARC-FY08Q4"
def parse(t):
    t = np.asarray(t, dtype=float).ravel()
    return datetime(int(t[0]), int(t[1]), int(t[2]), int(t[3]), int(t[4]), int(t[5]))

for batt in ["B0005", "B0006", "B0007", "B0018"]:
    cyc = sio.loadmat(f"{BASE}\\{batt}.mat", struct_as_record=False, squeeze_me=True)[batt].cycle
    dts = [parse(c.time) for c in cyc]
    ties = sum(1 for a, b in zip(dts, dts[1:]) if b == a)
    inv = sum(1 for a, b in zip(dts, dts[1:]) if b < a)
    print(f"{batt}: cycles={len(dts)} equal-timestamps={ties} out-of-order(backwards)={inv} "
          f"start={dts[0]} end={dts[-1]}")
