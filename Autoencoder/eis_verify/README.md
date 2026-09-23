# eis_verify — Internal artifact index (NOT part of the advisor report)

Scripts → outputs for the EIS raw verification (Advisor R2, Steps 1–4 / Part A + M).

| File | Purpose |
|---|---|
| `inspect_mat.py`, `inspect_mat2.py` | `.mat` structure discovery |
| `verify_a1_match.py` | B0005 cycle 41 point-level comparison |
| `verify_full_rows.py` | All-rows comparison (A1) — prints "ALL 34,593 ROWS MATCH" |
| `sweep_quality.py` | A4+A5 sweep across all 887 spectra |
| `a4_time_check.py` | Timestamp monotonicity (A4) |
| `debug_time.py` | Time-field format inspection (debugging step before a4_time_check) |
| `a6_rect_vs_battery.py` | Rectified vs raw Battery_impedance comparison (A6) |
| `build_verified_dataset.py` | Regenerated dataset with nominal frequency column (A2) |
| `a3_plots.py` | A3 table + 3-plot diagnostic |
| `a7_redraw.py` | A7 figures (raw Nyquist ×4 spectra; measured vs interpolated) |
| `convert_report.py` | P4 helper: report .md → .docx + .pdf (pandoc via pypandoc-binary) |
| `A3_B0005_cycle41_table.csv` | 39-point table (Freq_nominal_assumed_Hz header) |
| `A3_B0005_cycle41_3plots.png` | 3-plot diagnostic (A3 / M-C) |
| `A7_Raw_Nyquist_4spectra.png` | Raw Nyquist, 4 spectra, 3 batteries (A7) |
| `A7_Measured_vs_Interpolated_B0005c41.png` | Measured vs interpolated (A7) |
| `EIS_Verified_Dataset.csv` | 34,593 rows: Battery, Cycle, Point, Freq (nominal), Re(Z), -Im(Z) |
| `EIS_Raw_Verification.md` | Advisor-facing verification report |
| `README.md` | This index |

Python used for all runs: `C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe` (scipy, numpy, matplotlib, pypandoc).
