# Part J: BMS Practicality Discussion (advisor Part J) — EIS vs Time-Domain

**Date:** 2026-09-25
**Scope:** Advisor Part J — "When claiming real-time BMS suitability, compare: measurement requirements, computational complexity, required sensors/hardware, online feasibility, sensitivity to operating conditions."
**Evidence base:** Steps 7–16 measured results (this repository).

---

## 1. Measurement requirements

| Aspect | EIS pipeline | Time-domain pipeline |
|---|---|---|
| Excitation | Dedicated small-AC injection swept over 0.1 Hz–5 kHz (39 frequencies per measurement, minutes per sweep) | None — uses the charge/discharge current already applied |
| Measurement condition | Quasi-static; the battery is taken through a dedicated impedance procedure | Normal operation (the logged charge/discharge cycle itself) |
| Data needed | 39 complex impedance points per sweep | V(t), I(t), T(t) of one charge + one discharge cycle |

The time-domain features require no dedicated excitation procedure; they are computed from logs that every BMS already records (advisor Part B1: "V(t), I(t), T(t) are already measured during normal operation").

## 2. Required sensors and hardware

| Aspect | EIS | Time-domain |
|---|---|---|
| Sensors | Precision AC current injection + synchronous voltage sensing (LCR meter / potentiostat-class hardware) | Standard BMS sensing (cell voltage, current shunt/hall, temperature) |
| Added hardware cost | Significant (excitation circuit + isolation + calibration) | None beyond a standard BMS |

## 3. Computational complexity (per prediction)

| Stage | EIS pipeline | Time-domain pipeline |
|---|---|---|
| Preprocessing | Interpolation 39 → 128 points on the nominal grid | 8 scalar features (durations, means, two linear slopes) — O(n) over the logged cycle |
| Feature model | AE: 256→128→17→128→256 (trained offline); encoder at inference | AE-on-TD variant: 8→4 (or none for TD-Ridge) |
| Regressor | BPNN (17 → ≤16 hidden units) | BPNN (8 → ≤16) or closed-form Ridge |

Both inference paths are lightweight by modern standards; the time-domain path is lighter and its preprocessing is simpler and fully causal (each feature uses only the completed/preceding cycle data).

## 4. Online feasibility

- **Time-domain:** cycle-level SOH after each completed charge/discharge cycle — matches how capacity-fade SOH itself is defined (capacity of that cycle). Feasible in any BMS that logs cycles. Features are causal: discharge features come from the cycle being scored; charge features come from the **preceding** charge only (Steps 14–16).
- **EIS:** cycle-level, but requires the dedicated sweep procedure and hardware; NASA's own log contains impedance only every ~2.2 cycles (278 impedance vs 616 cycles for B0005), and Step 8 showed the EIS↔capacity mapping depends on tolerance because the two measurements are not co-timed.
- Neither pipeline estimates SOH mid-discharge; both are cycle-level estimators.

## 5. Sensitivity to operating conditions / cross-battery behavior (measured in Steps 7–16)

- EIS amplitude showed a measured cross-battery domain shift: per-row normalization rescues the B0018 fold (R² −1.19 → +0.22) at the cost of the others (Step 9–10 P1n).
- Time-domain features transferred to all four folds without per-battery adjustment (R² +0.65…+0.97, Steps 14–16).
- EIS retains a potential advantage this study did not test: sensitivity to internal aging mechanisms at fixed SOH (e.g., distinguishing calibration fade from intrinsic fade), which a plain cycle-log feature set does not capture. This remains a hypothesis for future work, not a measured result.

## 6. Conclusion for the thesis discussion

On this dataset, the time-domain pipeline is more practical for a production BMS (no extra hardware, simpler preprocessing, causal features) **and** more accurate cross-battery (Steps 14–16). The EIS pipeline's role, if retained, should be argued on grounds other than cycle-level SOH accuracy (e.g., mechanism diagnostics), and any such claim requires its own experiments.

---

## Ablation log

`2026-09-25 | part_j | discussion (no new runs) | TD deployable on standard BMS; EIS needs added hardware + dedicated sweep`

## Artifacts

`Part_J_BMS_Practicality.md` (this report; written from measured evidence in Steps 7–16, no new runs)