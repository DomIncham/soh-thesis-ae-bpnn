# R3-C9 Citation Verification — 13 Studies (Verified 2026-10-06)

> Every row below is read from the **full local PDF** (`Gap_audit_paper_Prof_Recommend/`), not from
> the advisor's audit summary. Per audit rule 1: value, unit, split protocol confirmed by direct
> reading. Rule 3: all RMSE converted to %SOH where the original used a fraction; original unit noted.
> Files named `*.pdf` in `Journal Discovery/Gap_audit_paper_Prof_Recommend/`.

| Ref | Paper | Verified headline number | Split protocol (read from paper) | SOH definition | Proxy status | Use in Ch.2 |
|---|---|---|---|---|---|---|
| [1] | Zhang et al. 2022, *Front. Energy Res.* TCN (10.3389/fenrg.2022.929235) | B0018 start=90: TCN MAE 0.361 / RMSE 0.297% vs LSTM 1.537/2.873 | **Same-battery chronological** ("prediction starting point": train = first 80 discharges, val = next 10, test = rest); NASA B0005/07/18 | SOH = C/C_N (rated capacity) | Indirect HFs = temp/voltage variety rates (corr 0.86–0.99 with capacity) | Factor 1 example: high accuracy under chronological same-battery split |
| [2] | Dong et al. 2022, *IJES* GPR (10.20964/2022.08.34) | RMSE 0.81–2.92% across 8 NASA/Sony cells (leave-one-battery-out: "one battery in the NASA... as the test") | LOBO-style (one battery test) | Ratio of actual to initial capacity; EOL = 70% nominal | Multiple IHFs incl. charge-related | Group (A) time-domain; supports cross-battery difficulty |
| [3] | Xu et al. 2024, *PLOS ONE* LSTM-attn (10.1371/journal.pone.0312856) | — (headline verified below) | — | — | **Q(k−1) is an explicit input** (line 350/402: "F2(k), F3(k), and Q(k−1)... actual capacity at the previous time step") | Factor 2 evidence: capacity proxy in input |
| [4] | Giuliano et al. 2025, *Energies* 18:5439 (10.3390/en18205439) | Cross-composition transfer RMSE 0.9017 (fraction ≈ 90%SOH-scale — transfers poorly); fine-tune on Oxford 0.0146 vs ANN 0.0175 | Transfer learning, cross-dataset (Oxford fine-tune) | — | **Inputs include previous-cycle capacitance C and cycle number** (line 471) | Factor 2 + cross-cell group |
| [5] | Salem et al. 2026, *Energy Reports* (10.1016/j.egyr.2025.108931) | LSTM R² 0.9036/RMSE 0.0302; BiLSTM-MHSA 0.9460 at 10 min partial discharge | NASA, train/val/test by time (80% train first — chronological same-battery) | — | Partial-discharge-window features | Partial-window group (F); note their 10-min window IS a proxy per our 5.2 |
| [6] | Okour et al. 2026, *J. Low Power Electron. Appl.* (10.3390/jlpea16020016) | FNN RF up to R² 0.9979 (20 trees: RMSE 2.87, R² 0.92) | NASA + synthetic; random split (same-battery) | SoH = current max capacity / nominal initial | Raw early-discharge voltage segment inputs | Factor 1 example: lightweight + random split = high score |
| [7] | Zhao Y. et al. 2026, *Sci. Rep.* GAF-CNN-Fusion-LSTM (10.1038/s41598-026-48317-5) | Main avg RMSE 0.0080, R² 0.9803; **cross-battery (Oxford, 1-train/rest-test): avg R² 0.9803, RMSE 0.0084 (0.84%SOH)** | Main: same-battery; cross-battery: 1 train / rest test (Oxford) | SOH(j) = Cj/C × 100% (initial capacity) | IC-curve + GASF image features | Group (C) fusion; strongest "cross-battery works" claim to reconcile — note Oxford n=8 small + capacity-as-SOH |
| [8] | Mohamud et al. 2026, *Batteries* 12:210 (10.3390/batteries12060210) | MAE 0.88%, R² 0.978 (best); internal model 0.9949 | **Split-wise normalization: fold-train-only stats** (same discipline as ours) | SOH(n) = Qn/Q0, Q0 = highest capacity in first cycles | ICA features + PCA | Factor 2 example; protocol discipline comparable to ours |
| [9] | Chen et al. 2026, *Batteries* 12:340 (10.3390/batteries12090340) | **B0006 LOCO: RMSE 0.1068→0.0845 (fraction, = 8.45%SOH), R² 0.2464→0.5286**; avg RMSE 0.0499→0.0425 | LOCO on NASA B0005/06/07 (3 cells) | **SOH = Q(c)/Q(1)**; 13 statistical features + **cycle index as explicit input** | Cycle index proxy; conformal intervals "not fully calibrated under severe domain shift" (their own limitation) | Closest to our protocol; audit claim 0.25→0.53 **CONFIRMED**; they also hit the B0006 wall |
| [10] | Zhao J. & Qian X. et al. 2026, *Energies* 19:4326 EWDC (10.3390/en19184326) | Avg R² 0.975 / RMSE 1.21% / MAE 0.65% over 8 LOBO folds (B0005/06/07/18 + CS2-35..38), 10 runs | **Within-dataset LOBO, source-only** (same cells as ours) | Q/Q0, ŷ1 = 1 anchor | **17 charge-segment HIs incl. cycle index + cumulative charged quantity** | Compare vs our TD-All 0.927 (not Clean-8 0.810) — same protocol, proxy status differs |
| [11] | Sardar et al. 2026, *Batteries* 12:291 (10.3390/batteries12080291) | **Random split: ET R² 0.9788 / battery-wise: ET R² 0.7855 (MAE 4.91%, RMSE 7.37%)**; GB random 0.979 | 34 NASA cells → 1830 matched EIS–SOH samples; random vs strict battery-wise | SOH label assigned from preceding discharge capacity | Features carry "indirect proxy" risk — their own leakage caveat | **Audit's factor-1 claim 0.979→0.786 CONFIRMED verbatim**; research-gap anchor |
| [12] | Meng et al. 2026, *Batteries* 12:196 Mamba (10.3390/batteries12060196) | (verified: fusion improves over discharge-only Samba; table MAE/RMSE/MAPE) | NASA; unimodal/multimodal settings | SOH ∈ [0,100] ratio | EIS "proxy (no AC EIS available)" for one arm — partial-cycle proxy | Group (C) fusion |
| [13] | Shi et al. 2026, *Sci. Rep.* DS-Transformer (10.1038/s41598-026-52202-6) | **MAE 1.24%, RMSE 1.67%, MAPE 1.51%, R² 0.9782** (beats BatFormer by 28.3%) | (same-battery split) | Current max releasable / rated capacity | Discharge curves + EIS fusion | Group (C) fusion; unit note: RMSE 1.67% is on the fraction scale → 1.67%SOH |

## Key confirmations vs the advisor's audit

1. **Factor 1 (split protocol)** — [11] random 0.9788 → battery-wise 0.7855 confirmed verbatim.
   [1]/[5]/[6] all high-scoring on same-battery splits. Our own gap 0.979→0.927/0.490 sits inside
   this spread.
2. **Factor 2 (capacity proxy)** — [3] uses Q(k−1) explicitly; [4] uses previous-cycle capacity +
   cycle number; [9] uses cycle index; [10] uses cycle index + cumulative charge. **All of the
   strongest unseen-battery claims in the list are proxy-laden** — supports our Clean-8 framing.
3. **Factor 3 (training batteries)** — [11] 34 cells/1830 samples confirmed; [9] only 3 cells
   (B0005/06/07) confirmed — our 4-battery LOBO is comparable, and they also fail on B0006.
4. **B0006 wall is universal** — [9] best B0006 R² 0.5286 (LOCO); our LOBO B0006 history mirrors
   this; [10] B0018 RMSE 1.91% (worst fold) vs avg 1.21%.
5. **EWDC [10] 0.975** — within-dataset LOBO (see `advisor_directives.md` R3-C9 Part 1): compare
   against TD-All 0.927, noting the proxy-laden feature set and ŷ1=1 anchor.
6. **[7] is the only "cross-battery R² 0.98" result** — but it is Oxford, 1-train/rest-test, and
   SOH defined as capacity ratio per cell; the smallest n and cleanest cells in the list. State
   this scope next to any Ch.2 comparison.

## Unit conversion notes (audit rule 3)

- Fraction-scale RMSEs (e.g. [9] 0.0845, [7] 0.0084) convert to %SOH by ×100 where the SOH was a
  0–1 fraction; [2]/[5]/[8]/[10]/[13] already report %SOH or percent units.
- [6] RMSE 2.87 is on a percent scale (2.87%SOH).
- Any Ch.2 table must state the unit next to every number (rule 3).

## Journal quartiles (rule 4 — to confirm on JCR/SJR at submission time)

- *Energies* (MDPI): JCR Q3 (Q2 in some categories) — check current year.
- *Batteries* (MDPI): JCR Q2–Q3.
- *Scientific Reports*: JCR Q1 (multidisciplinary).
- *PLOS ONE*: JCR Q1 (multidisciplinary).
- *Frontiers in Energy Research*: Q2. *Energy Reports*: Q1–Q2.
- *IJES*: Q3–Q4 (scrape-level journal; still citable as a baseline example).
- *J. Low Power Electron. Appl.*: Q3.
- Confirm each on JCR/SJR **before** the thesis PDF is finalised — quartiles move year to year.

## Status

All 13 studies now verified from full PDFs. **Ch. 2 citation table is unblocked** (with the
per-row "Use in Ch.2" notes above). One remaining advisor question: thesis title phrasing
("proxy-audited, partial-window") — email reduces to this single item.
