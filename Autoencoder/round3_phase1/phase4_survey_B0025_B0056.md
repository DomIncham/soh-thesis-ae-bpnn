# Phase 4 (R3-C6) pre-check: what B0025–B0056 actually contain

Measured from the `.mat` files directly (`NASA DataSet/3–6. BatteryAgingARC_*`), 2026-10-05.
Columns: dis = labelled discharge cycles; cap0-5/caplast = mean of the first 5 / last discharge
capacity (Ah); Iptp = mean peak-to-peak discharge current of the first 50 cycles (≈0 means a
constant-current load); capptp = capacity span.

| cells | dis cyc | ambient | load | label quality |
|---|---|---|---|---|
| B0005/06/07 (our train) | 168 each | 24 °C | 2 A constant (Iptp ≈ 2.0) | clean, 1.84→1.33 Ah |
| B0018 (our test) | 132 | 24 °C | 2 A constant | clean |
| B0025/26/27 | 28 each | 24 °C | **4 A pulsed square wave** (Iptp ≈ 4.0) | clean but tiny; cap 1.80–1.85 Ah, fade ≤ 0.43 Ah |
| B0028 | 28 | 24 °C | 2 A (Iptp 2.0; README says pulsed — README wrong or data differs) | clean but tiny |
| B0029–32 | 40 each | **43 °C** | 4 A constant | clean-ish |
| B0033/34 | 197 each | 24 °C | 4 A constant | **corrupt early cycles** (cap0-5 = 0.895 / 1.454 Ah, capptp up to 1.8) |
| B0036 | 197 | 24 °C | 2 A constant | corrupt early cycles (capptp 1.44) |
| B0038–40 | 47 each | 24 & 44 °C mixed | 1/2/4 A mixed | **corrupt** (cap0-5 0.34–1.04 Ah) |
| B0041–48 | 67–112 | **4 °C** | 1–4 A | README itself warns: "several discharge runs where the capacity was very low. Reasons … not fully analyzed" |
| B0049–52 | 25 | 4 °C | 2 A | anomalous (capptp up to 2.4); B0050/B0052 have **inhomogeneous (ragged) arrays** that fail to load |
| B0053–56 | 56–103 | 4 °C | 2 A | several capacity = 0.000 cycles |

## What this changes

The advisor's premise "add B0025–B0056 (similar conditions)" **does not hold**:

1. Only B0025–28 share our 24 °C ambient — but they use a **4 A pulsed** load (B0028 looks 2 A),
   and give only **28 discharge cycles each** (vs 168). The pulsed load changes `dis_duration`'s
   meaning entirely (time is no longer a fixed fraction of charge per cycle — it is per-pulse).
2. Everything else is 43 °C, 4 °C, mixed-temperature, or has documented corrupt/zero-capacity
   cycles. Only B0029–32 (43 °C) and B0033–36 (24 °C, 4 A/2 A, corrupt early cycles) even have
   ≥ 40 usable-looking cycles.

Charging is identical everywhere (CC 1.5 A → 4.2 V, CV to 20 mA), so **charge-side features
(`cc_dur`, `cv_dur`, `cv_I_slope`, `ch_mean_T`, `ic_peak_V`) transfer across all cells**; the
discharge-side proxies (`dis_duration`, `dis_mean_V`) do not compare across load profiles.

## Options for the learning curve (decision needed)

| option | training-pool additions | pro | con |
|---|---|---|---|
| **A. room-temp only** | B0025–28 (pulsed, 28 cyc) + B0033/34/36 (corrupt head) | honest same-conditions curve | max k ≈ 4 train cells; corrupt heads need an explicit exclusion rule |
| **B. temperature-heterogeneous** | B0025–28 + B0029–32 (43 °C) + B0045–48 (4 °C) | k up to 10–11; stress-test of the proxy-free claim | conditions differ → curve mixes "more data" with "harder data"; must be reported as such |
| **C. go straight to CALCE CS2** | external dataset, same chemistry/model family | cleanest generalisation statement; cross-dataset was the advisor's second half of C6 anyway | more engineering (different file format); no NASA learning curve |

Recommended: **B first, disclosed as a heterogeneous curve, with A as the subset analysis** (same
run: group folds by condition so the curve can be reported per-condition), then C. Rationale: one
extraction pass over all cells serves both; per-condition grouping keeps the "similar conditions"
honest version without a second experiment.

Data-hygiene rules needed regardless: drop discharge cycles with Capacity ≤ 0 or < 1.2 Ah unless
the cell's whole history is that low; drop cells B0050/B0052 (ragged arrays) or repair them
explicitly; document every exclusion with a committed rule, not a hand-pick.
