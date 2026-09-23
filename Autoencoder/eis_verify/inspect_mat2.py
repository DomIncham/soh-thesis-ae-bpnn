# Step A1 (Part 2): Drill into B0005 cycle structs — find impedance entries and their fields
import scipy.io as sio
import numpy as np

MAT = r"C:\Master Degree\Thesis\NASA DataSet\1. BatteryAgingARC-FY08Q4\B0005.mat"
raw = sio.loadmat(MAT, struct_as_record=False, squeeze_me=True)
B = raw["B0005"]
print("B fields:", B._fieldnames)
cyc = B.cycle
print("cycle: type =", type(cyc).__name__, ", len =", np.size(cyc))

c0 = cyc[0] if np.size(cyc) > 0 else cyc
print("c0 fields:", c0._fieldnames if hasattr(c0, "_fieldnames") else type(c0))

# scan types
types = {}
imp_example = None
for i in range(np.size(cyc)):
    c = cyc[i]
    t = str(c.type)
    types[t] = types.get(t, 0) + 1
    if t == "impedance" and imp_example is None:
        imp_example = (i, c)
print("cycle types count:", types)

i, c = imp_example
print(f"\n=== first impedance cycle: index {i}, type={c.type} ===")
print("cycle fields:", c._fieldnames)
d = c.data
print("data fields:", d._fieldnames)
for f in d._fieldnames:
    v = getattr(d, f)
    if hasattr(v, "_fieldnames"):
        print(f"  {f}: STRUCT fields={v._fieldnames}")
        for sub in v._fieldnames:
            sv = getattr(v, sub)
            sv_arr = np.asarray(sv)
            print(f"    .{sub}: shape={sv_arr.shape}, dtype={sv_arr.dtype}, first3={np.ravel(sv_arr)[:3]}")
    else:
        v_arr = np.asarray(v)
        print(f"  {f}: shape={v_arr.shape}, dtype={v_arr.dtype}, first3={np.ravel(v_arr)[:3]}")
