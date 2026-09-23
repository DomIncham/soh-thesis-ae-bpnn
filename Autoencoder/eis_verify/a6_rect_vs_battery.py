# A6 quantitative: Rectified_Impedance vs Battery_impedance (raw) across all spectra
import scipy.io as sio
import numpy as np

BASE = r"C:\Master Degree\Thesis\NASA DataSet\1. BatteryAgingARC-FY08Q4"
summary = {}
marker_count = 0
for batt in ["B0005", "B0006", "B0007", "B0018"]:
    cyc = sio.loadmat(f"{BASE}\\{batt}.mat", struct_as_record=False, squeeze_me=True)[batt].cycle
    imps = [c for c in cyc if str(c.type) == "impedance"]
    ri_immax, bi_immax, neg_re, bi_zmax = [], [], [], 0
    n48 = 0
    for c in imps:
        ri = np.asarray(c.data.Rectified_Impedance)
        bi = np.asarray(c.data.Battery_impedance)
        if len(bi) == 48:
            n48 += 1
            bi = bi[1:]  # drop marker row
        ri_immax.append(np.abs(ri.imag).max())
        bi_immax.append(np.abs(bi.imag).max())
        neg_re.append(int((bi.real < 0).sum()))
        bi_zmax = max(bi_zmax, np.abs(bi).max())
    summary[batt] = dict(
        n=len(imps), n48=n48,
        ri_immax=(np.mean(ri_immax), np.std(ri_immax)),
        bi_immax=(np.mean(bi_immax), np.std(bi_immax)),
        bi_reneg=np.mean(neg_re), bi_zmax=bi_zmax,
    )
    print(f"{batt}: spectra={len(imps)} 48pt-arrays={n48} | max|Im| Rectified={summary[batt]['ri_immax'][0]:.4f}"
          f"+-{summary[batt]['ri_immax'][1]:.4f} Ohm | Battery={summary[batt]['bi_immax'][0]:.4f}"
          f"+-{summary[batt]['bi_immax'][1]:.4f} Ohm | neg-Re pts/spectrum={summary[batt]['bi_reneg']:.1f}"
          f" | max|Z| Battery={bi_zmax:.3f} Ohm")

print("\nRatio mean(max|Im|) Battery/Rectified per battery:")
for b, s in summary.items():
    print(f"  {b}: {s['bi_immax'][0]/s['ri_immax'][0]:.1f}x")