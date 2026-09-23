# Step A1/A2: Full 39-point match check .mat vs CSV + compare Rectified vs Battery_impedance
import scipy.io as sio
import numpy as np

MAT = r"C:\Master Degree\Thesis\NASA DataSet\1. BatteryAgingARC-FY08Q4\B0005.mat"
CSV = r"C:\Master Degree\Thesis\NASA DataSet\1. BatteryAgingARC-FY08Q4\NASA_Impedance_Data.csv"

raw = sio.loadmat(MAT, struct_as_record=False, squeeze_me=True)
cyc = raw["B0005"].cycle
imp = [c for c in cyc if str(c.type) == "impedance"]
c41 = imp[0]  # MATLAB index 41
ri = np.asarray(c41.data.Rectified_Impedance)          # 39 pts
bi = np.asarray(c41.data.Battery_impedance)            # 48 pts
sc = np.asarray(c41.data.Sense_current)               # 48 pts
bc = np.asarray(c41.data.Battery_current)
cr = np.asarray(c41.data.Current_ratio)

csv = np.genfromtxt(CSV, delimiter=",", names=True)
c_csv = csv[(csv["Battery_ID"] == 1) & (csv["Cycle"] == 41)]
print("CSV rows for B0005 cycle 41:", len(c_csv))
re_csv, negim_csv = c_csv["Re_Z"], c_csv["Neg_Im_Z"]

# exact match check
d_re = np.abs(re_csv - ri.real)
d_im = np.abs(negim_csv - (-ri.imag))
print(f"max|dRe|={d_re.max():.3e}  max|dNegIm|={d_im.max():.3e}  -> {'MATCH' if max(d_re.max(),d_im.max())<1e-12 else 'MISMATCH'}")

print("\n=== 39 pts (Rectified_Impedance), .mat array order ===")
print(" idx |   Re(Z)    |  -Im(Z)    |  |Z|     | phase(deg)")
for i, z in enumerate(ri):
    print(f" {i:3d} | {z.real:10.6f} | {-z.imag:10.6f} | {abs(z):8.5f} | {np.degrees(np.angle(z)):8.2f}")

print("\n=== Battery_impedance (48) first/last 3 ===")
for i in list(range(3)) + list(range(45, 48)):
    print(f" {i:3d} | {bi[i].real:10.6f} | {-bi[i].imag:10.6f}")
print("\nSense_current[0] =", sc[0], " Battery_current[0] =", bc[0], " Current_ratio[0] =", cr[0])

# which of the 48 were dropped to make 39?
in_ri = [complex(z) in set(map(complex, ri)) for z in bi]
print("\nBattery_impedance pts found in Rectified:", sum(in_ri), "/", len(bi))
print("dropped pts (idx: re, -im):")
print([f"{i}: {bi[i].real:.6f},{-bi[i].imag:.6f}" for i, f in enumerate(in_ri) if not f])
