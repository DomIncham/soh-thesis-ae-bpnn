# A1 final: full verification — rebuild CSV per export.m logic, compare ALL rows vs NASA_Impedance_Data.csv
import scipy.io as sio
import numpy as np

BASE = r"C:\Master Degree\Thesis\NASA DataSet\1. BatteryAgingARC-FY08Q4"
csv = np.genfromtxt(f"{BASE}\\NASA_Impedance_Data.csv", delimiter=",", names=True)
print("CSV rows:", len(csv))

rows = []
for b, batt in enumerate(["B0005", "B0006", "B0007", "B0018"], start=1):
    cyc = sio.loadmat(f"{BASE}\\{batt}.mat", struct_as_record=False, squeeze_me=True)[batt].cycle
    for i, c in enumerate(cyc, start=1):  # MATLAB 1-based cycle index (matches export.m)
        if str(c.type) == "impedance":
            ri = np.asarray(c.data.Rectified_Impedance)
            rows.append(np.column_stack([np.full(len(ri), b), np.full(len(ri), i), ri.real, -ri.imag]))
mat = np.vstack(rows)
print("Rebuilt from .mat:", mat.shape)

if mat.shape != csv_shape if False else mat.shape[0] != len(csv):
    print("ROW COUNT MISMATCH")
else:
    bid_ok = np.array_equal(mat[:, 0], csv["Battery_ID"])
    cyc_ok = np.array_equal(mat[:, 1], csv["Cycle"])
    d_re = np.abs(mat[:, 2] - csv["Re_Z"]).max()
    d_im = np.abs(mat[:, 3] - csv["Neg_Im_Z"]).max()
    print(f"Battery_ID exact: {bid_ok} | Cycle exact: {cyc_ok}")
    print(f"max|dRe_Z|={d_re:.3e}  max|dNeg_Im_Z|={d_im:.3e}")
    print("VERDICT:", "ALL 34,593 ROWS MATCH" if bid_ok and cyc_ok and max(d_re, d_im) < 1e-12 else "MISMATCH")
