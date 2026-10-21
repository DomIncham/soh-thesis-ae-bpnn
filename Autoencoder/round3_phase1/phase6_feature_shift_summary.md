# Phase 6 feature-shift summary (R6-C2.1, diagnostic only)

Row sets: NASA = phase4_features.csv include_cell dropna (14 cells, 1033 rows); CALCE = phase4_cs2_features.csv include_cell & cap_ok dropna (8 cells, 4922 rows). Unit = each feature's raw unit from the Phase 4 extractors; KS/Wasserstein computed on raw values.

- **dis_V_slope**: NASA [-0.0005623, -4.57e-05] vs CALCE [-0.0002262, -1.761e-05]; 0.0% below / 0.1% above the NASA range (0.1% outside); KS=0.588 (p=4.4e-277), Wasserstein/range=0.216
- **cc_dur**: NASA [113.1, 3535] vs CALCE [657, 6724]; 0.0% below / 93.4% above the NASA range (93.4% outside); KS=0.934 (p=5.4e-323), Wasserstein/range=0.865
- **cv_dur**: NASA [5825, 1.069e+04] vs CALCE [46, 1.152e+04]; 84.5% below / 0.1% above the NASA range (84.6% outside); KS=0.845 (p=5.8e-322), Wasserstein/range=1.234
- **cv_I_slope**: NASA [-0.003038, -0.0003048] vs CALCE [-0.01446, 0]; 37.5% below / 62.3% above the NASA range (99.8% outside); KS=0.623 (p=8.5e-315), Wasserstein/range=0.864
- **ic_peak_V**: NASA [3.91, 4.18] vs CALCE [3.86, 4.18]; 41.6% below / 0.0% above the NASA range (41.6% outside); KS=0.549 (p=2.0e-239), Wasserstein/range=0.243
