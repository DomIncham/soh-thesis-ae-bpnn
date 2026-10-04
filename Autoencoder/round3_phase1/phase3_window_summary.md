# Phase 3, item 5.2 — fixed discharge voltage window (4.0 → 3.6 V): NOT ESTABLISHED

Advisor's plan, item 5.2: *"Fixed voltage window for discharge — 4.0 → 3.6 V (all batteries pass)
instead of whole-cycle min V / total time."* The rationale was that a window with the same two end
points for every cell removes the problem that the discharges end at different voltages
(B0005 2.7 V, B0006 2.5 V, B0007 2.2 V, B0018 2.5 V).

The window exists for all 636 discharge cycles (checked, zero exclusions).

## Part 1 — the window features are mostly proxies, and worse ones

`extract_window_features.py` produces seven features inside the 4.0–3.6 V window and classifies each
with the same rule used throughout (within-battery OLS R² against capacity; PROXY at ≥ 0.90):

| feature | R²(capacity) | per battery | verdict |
|---|---|---|---|
| `win_dur` | **0.995** | .997/.991/.997/.992 | **PROXY** |
| `win_dQ` | **0.995** | .997/.991/.997/.992 | **PROXY** |
| `win_frac` | **0.979** | .977/.988/.964/.986 | **PROXY** |
| `win_V_slope` | **0.968** | .988/.912/.990/.983 | **PROXY** |
| `win_dT` | **0.935** | .946/.951/.901/.943 | **PROXY** |
| `win_mean_V` | 0.659 | .654/.883/.547/.550 | BORDERLINE |
| `win_mean_T` | 0.494 | .374/.670/.309/.621 | SAFE |

**`win_dur` is a stronger capacity proxy than the whole-cycle `dis_duration` (0.972).** The reason is
physical: at roughly constant current the time spent in a fixed voltage window is the charge taken in
that window, so

```
win_dur = win_frac × total_duration ,  win_frac ≈ 0.25–0.35 and roughly constant per cell
        ⇒ win_dur ∝ capacity  by construction
```

Restricting the window to a fixed voltage span therefore *increases* proportionality to capacity
rather than removing it. Measured within-battery correlations of `win_dur` with capacity are
0.9957–0.9987 against 0.976–0.993 for `dis_duration`.

## Part 2 — the comparability rationale also fails

The window was meant to make batteries comparable. It does the opposite:

| quantity | per-battery mean spread |
|---|---|
| `win_frac` | **1.405×** |
| `win_dur` | **1.377×** |
| `win_dQ` | 1.363× |
| `win_dT` | 1.234× |
| *`dis_duration` (whole cycle)* | *1.020×* |
| *`dis_mean_V`* | *1.016×* |

So on both counts — proxy-ness and cross-battery comparability — the fixed window is worse than the
whole-cycle features it was meant to replace.

## Part 3 — the one admissible substitution, measured

Only `win_mean_T` (0.494, SAFE) can legitimately replace anything, and its whole-cycle counterpart is
`dis_mean_T` (0.430, SAFE). `TD-Win-7` is therefore `TD-Clean-7` with exactly one feature swapped.

Paired on identical (fold, seed) cells, same 631 rows, 5 seeds:

| | mean R² | median R² | std | B0005 | B0006 | B0007 | B0018 |
|---|---|---|---|---|---|---|---|
| `TD-Clean-7` | 0.772 | 0.827 | 0.155 | 0.802 | 0.597 | 0.922 | 0.767 |
| `TD-Win-7` | **0.819** | 0.832 | **0.117** | 0.838 | **0.705** | 0.918 | 0.813 |

| metric | value |
|---|---|
| cells improved | **12 / 20** |
| mean ΔR² | +0.047 |
| median ΔR² | +0.021 |
| worst fold-mean Δ | −0.004 |
| B0006 | **+0.108** (better in 4 of 5 seeds) |

**Verdict: NOT established, not adopted.** The aggregate rises and the hardest fold improves, but
the swap is better in only 12 of 20 cells — below the 15/20 consistency bar that `ic_peak_V` cleared
in item 5.1 — and the aggregate gain is smaller than the known instability of the proxy-free regime.
It is reported as suggestive.

## The tension worth recording

`win_mean_T` has a *higher* R²(capacity) (0.494) than the feature it replaces (0.430) and still
performs better. That is consistent, not contradictory: the proxy rule measures **label correlation**,
not usefulness. A feature can be mildly correlated with capacity and still carry
genuine degradation information, and restricting the mean to a fixed voltage window removes the
per-cell cut-off difference that the whole-cycle mean carries. Both features are SAFE (< 0.90), so
the substitution is admissible — it is the only Phase 3 change so far that helped at all.

## Consequence

- **5.2 is closed.** The window idea fails as a proxy-removal strategy (5 of 7 features are proxies,
  and the strongest of them beats the whole-cycle proxy) and fails as a comparability fix.
- The proxy-free result is unchanged: **`TD-Clean-7` = 0.772 (median 0.827)**,
  **`TD-Clean-8` = 0.810 (median 0.825)**.
- Remaining Phase 3 items: **5.4** (ΔSOH target / monotonic prior — the only remaining candidate that
  attacks the per-battery scale problem structurally) and **5.5** (window-length curve).

Evidence: `extract_window_features.py`, `nested_lobo/window_features.csv`, `phase3_window_run.py`,
`phase3_window_cpu_results.csv`, `phase3_window_verify.py` (7/7 checks pass).