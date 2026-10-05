# Shared charge-side feature maths for the Phase 4 pipeline (single source of truth).
# Used by phase4_extract_features.py (NASA .mat) and phase4_cs2_features.py (CALCE logs).
# t_40_41 + ic_peak_V - identical maths to nested_lobo/extract_charge_features.py (lines 30-67).
import numpy as np

CC_V = 4.19  # CC->CV transition threshold (V)


def charge_feats(V, I, T, cc_v=CC_V):
    """V, I, T = charge-segment arrays in (volts, amps, seconds). Returns t_40_41, ic_peak_V."""
    V = np.asarray(V, float).ravel()
    I = np.asarray(I, float).ravel()
    T = np.asarray(T, float).ravel()
    ci = np.where(V >= cc_v)[0]
    end = int(ci[0]) if len(ci) else len(V) - 1
    n = max(end, 2)
    dt = np.diff(T[:n])
    t401 = float(dt[np.logical_and(V[:n - 1] >= 4.0, V[:n - 1] < 4.1)].sum())
    Q = np.concatenate([[0.0], np.cumsum((I[:n - 1] + I[1:n]) / 2 * dt) / 3600.0])
    lo = 3.6
    seg = np.where(V[:n] >= lo)[0]
    if len(seg) > 10:
        s = seg[0]
        Vs, Qs = V[s:n], Q[s:n]
        keep = np.concatenate([[True], np.diff(Vs) > 0])
        Vs, Qs = Vs[keep], Qs[keep]
        grid = np.arange(lo, float(Vs[-1]) + 1e-9, 0.01)
        if len(grid) > 5 and len(Vs) > 5:
            Qg = np.interp(grid, Vs, Qs)
            k = int(np.argmax(np.gradient(Qg, grid)))
            ic_V = float(grid[k])
        else:
            ic_V = np.nan
    else:
        ic_V = np.nan
    return dict(t_40_41=t401, ic_peak_V=ic_V)
