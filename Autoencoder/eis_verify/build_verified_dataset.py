# A2 deliverable: regenerate dataset with declared nominal frequency column (all 4 batteries)
import scipy.io as sio
import numpy as np

BASE = r"C:\Master Degree\Thesis\NASA DataSet\1. BatteryAgingARC-FY08Q4"
OUT = r"C:\Master Degree\Thesis\Autoencoder\eis_verify"
F_NOM = np.logspace(np.log10(0.1), np.log10(5000), 39)  # nominal assumption, not measured

rows = []
for b, batt in enumerate(["B0005", "B0006", "B0007", "B0018"], start=1):
    cyc = sio.loadmat(f"{BASE}\\{batt}.mat", struct_as_record=False, squeeze_me=True)[batt].cycle
    for i, c in enumerate(cyc, start=1):
        if str(c.type) == "impedance":
            ri = np.asarray(c.data.Rectified_Impedance)
            n = len(ri)
            rows.append(np.column_stack([
                np.full(n, b), np.full(n, i), np.arange(1, n + 1),
                F_NOM[:n], ri.real, -ri.imag]))
mat = np.vstack(rows)
hdr = "Battery_ID,Cycle,Point,Freq_nominal_assumed_Hz,Re_Z,Neg_Im_Z"
with open(f"{OUT}\\EIS_Verified_Dataset.csv", "w") as f:
    f.write(hdr + "\n")
    np.savetxt(f, mat, fmt=["%d", "%d", "%d", "%.6g", "%.12g", "%.12g"], delimiter=",")
print("rows written:", len(mat), "-> EIS_Verified_Dataset.csv")

# rewrite A3 cycle-41 table with assumption-explicit header
import csv as _csv
old = f"{OUT}\\A3_B0005_cycle41_table.csv"
with open(old) as f:
    lines = f.readlines()
lines[0] = "Point,Freq_nominal_assumed_Hz,Re_Z_Ohm,NegIm_Z_Ohm\n"
with open(old, "w") as f:
    f.writelines(lines)
print("A3 table header renamed (assumption explicit)")

# spot-check vs original CSV (first/last row of each battery block)
orig = np.genfromtxt(f"{BASE}\\NASA_Impedance_Data.csv", delimiter=",", names=True)
ok = True
for b in [1, 2, 3, 4]:
    m = np.argwhere(mat[:, 0] == b).ravel()
    for j in [m[0], m[-1]]:
        if abs(mat[j, 4] - orig["Re_Z"][j]) > 1e-12 or abs(mat[j, 5] - orig["Neg_Im_Z"][j]) > 1e-12:
            ok = False
print("spot-check vs original CSV:", "PASS" if ok else "FAIL")