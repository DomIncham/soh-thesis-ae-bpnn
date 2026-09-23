# Step A1 (Part 1): Inspect raw NASA B0005.mat structure — variable names, shapes, types
import scipy.io as sio
import numpy as np
import sys

MAT = r"C:\Master Degree\Thesis\NASA DataSet\1. BatteryAgingARC-FY08Q4\B0005.mat"

try:
    raw = sio.loadmat(MAT)
    print("[OK] scipy.io.loadmat (MATLAB v7 or earlier)")
except NotImplementedError as e:
    print("[FAIL] v7.3/HDF5 file needs h5py:", e)
    sys.exit(1)

print("\n=== TOP-LEVEL KEYS (non-meta) ===")
for k in raw.keys():
    if k.startswith("__"):
        continue
    v = raw[k]
    print(f"  {k}: type={type(v).__name__}, shape={getattr(v, 'shape', None)}, dtype={getattr(v, 'dtype', None)}")

# Drill into the main cell (usually named B0005 or 'cycles')
for k in raw.keys():
    if k.startswith("__"):
        continue
    print(f"\n=== {k} ===")
    v = raw[k]
    if isinstance(v, np.ndarray) and v.dtype == object:
        print(f"  object ndarray, shape={v.shape}")
        # NASA format: row0 = type labels, rows1..4 = data groups
        types = [str(x[0]) if isinstance(x, np.ndarray) and x.shape==(1,) else str(x) for x in v[0]]
        print(f"  row0 (type labels): {types}")
        for i in range(1, v.shape[0]):
            grp = v[i]
            print(f"  row{i}: shape={grp.shape}, dtype={grp.dtype}")
            # first few entries of each group
            for j in range(min(3, grp.shape[1] if grp.ndim>1 else len(grp))):
                entry = grp[0, j] if grp.ndim > 1 else grp[j]
                if isinstance(entry, np.ndarray) and entry.dtype == object:
                    # descendent of struct-like: show field names via loadmat structured access
                    print(f"    [{j}] object array shape={entry.shape}")
                else:
                    print(f"    [{j}] type={type(entry).__name__}, shape={getattr(entry,'shape',None)}, dtype={getattr(entry,'dtype',None)}")
            break_inner = True
