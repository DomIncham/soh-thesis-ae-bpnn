# debug: inspect raw time field of first cycles
import scipy.io as sio, numpy as np
cyc = sio.loadmat(r"C:\Master Degree\Thesis\NASA DataSet\1. BatteryAgingARC-FY08Q4\B0005.mat",
                  struct_as_record=False, squeeze_me=True)["B0005"].cycle
for i in range(4):
    t = np.asarray(cyc[i].time)
    print(i, cyc[i].type, "| shape:", t.shape, "| dtype:", t.dtype, "| value:", t)
