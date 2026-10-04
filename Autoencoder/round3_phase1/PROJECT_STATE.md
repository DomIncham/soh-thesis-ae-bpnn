# Round 3 — project state, verification ledger, and bug log

Snapshot after Phase 3 items 5.1 and 5.3. Everything below is derived from committed artifacts and
re-checked by script; nothing is quoted from memory.

## Where we are

| Phase | scope | advisor items | status |
|---|---|---|---|
| **Phase 1** | protocol fixes + proxy audit | R3-C1, R3-C3 | ✅ complete |
| **Phase 2** | protocol-gap experiment | R3-C2 | ✅ complete |
| **Phase 3** | proxy-free improvements | R3-C5 | 🔄 in progress — 5.1 done, 5.3 done (rejected) |
| Phase 4 | wider validation | R3-C6 | ⬜ not started (deferred by decision) |
| Phase 5 | EIS/AE role + documentation | R3-C7 | ⬜ not started |
| Phase 6 | citation verification | R3-C9 | ⬜ not started |

### Phase 3 item status

| item | content | status | result |
|---|---|---|---|
| 5.1 | charging-segment / ICA features | ✅ done | `ic_peak_V` supported: Clean-6 0.664 → Clean-7 **0.772** → Clean-8 **0.810** |
| 5.2 | fixed discharge voltage window (4.0→3.6 V) | ⬜ next | — |
| 5.3 | self-referenced normalisation | ✅ done | **REJECTED** — 0.810 → 0.075, B0018 collapses in 5/5 seeds |
| 5.4 | monotonic / ΔSOH prior | ⬜ | — |
| 5.5 | window-length curve | ⬜ | — |

## The results that stand

**Axis 1 — evaluation protocol** (per-fold mean R², TD-All, 5 seeds):

| protocol | R² |
|---|---|
| chronological, same battery | −1.028 (pooled +0.850) |
| nested LOBO, unseen battery (ours) | **0.927** |
| random, same battery | 0.979 |
| random, pooled | 0.989 |

**Axis 2 — capacity proxy** (nested LOBO):

| feature set | features | mean R² | median | note |
|---|---|---|---|---|
| TD-All | 8 | 0.927 | 0.947 | contains both proxies |
| TD-Proxy-Free | 7 | 0.845 | 0.876 | still contains `dis_mean_V`, a 0.948 proxy |
| TD-Clean-6 | 6 | 0.490 | 0.556 | no proxy above 0.90 |
| TD-Clean-7 | 7 | **0.772** | 0.827 | + `ic_peak_V` (0.489) — supported |
| TD-Clean-8 | 8 | **0.810** | 0.825 | + `t_40_41` (0.341) — the extra is within noise |

`TD-Clean-8` has no feature above 0.49 R²(capacity) and reaches ~96 % of the score that
`TD-Proxy-Free` reached with a 0.948 proxy in it.

**Oracle** reaches 0.992 under the same-battery random split and 0.671 under LOBO — the advisor's
"oracle ≈ 1" claim is correct for the protocol the literature uses, and that is the mechanism
behind the published scores.

## Verification ledger

All six scripts were re-run against the current committed artifacts. 134 checks, all passing.

| script | checks | covers |
|---|---|---|
| `phase1_verify.py` | 61 | metrics, formulas, provenance, TD-All identical across scripts, log vs CSV |
| `protocol_gap_verify.py` | 23 | 4 splits, split structure, regression that `lobo_nested` reproduces Phase 1 bit-for-bit |
| `td_clean_verify.py` | 7 | clean sets, paired deltas |
| `data_provenance_audit.py` | 26 | raw `.mat` → label → features; also against the advisor's own numbers |
| `phase3_charge_verify.py` | 8 | paired 5.1 comparison |
| `phase3_selfref_verify.py` | 9 | paired 5.3 comparison, localisation of the damage |

Plus leakage probes at `max|diff| = 0.00e+00` on every protocol and on the clean feature sets.

## Bug log — what was found, and whether anything needed a re-run

| # | bug | impact | re-run needed? |
|---|---|---|---|
| 1 | IC extraction took argmax over the whole 3.0–4.19 V grid, so the peak landed on the grid edge (initial voltage climb, not the ICA peak) | changed a verdict: `ic_peak_h` BORDERLINE 0.681 → **PROXY 0.906** | **no** — fixed at 07:26, before both Phase 3 runs (07:47, 08:18); the committed CSV recomputes to the documented values |
| 2 | degenerate config selection (`sel_epochs=1`) broke TD-Proxy-Free B0005/seed123 | 0.732 → 0.854 | yes, and it was done; regression showed TD-All/Oracle unchanged 0/24 |
| 3 | `\nnested_lobo` typo in an f-string path | crash before writing | n/a |
| 4 | `t_3.9_4.0` used as a dict key (invalid identifier) | syntax error | n/a |
| 5 | verification scripts missing `setting` in a groupby/merge key (3 occurrences) | checker only, never the data | n/a |
| 6 | over-strict assertions: "every fold-seed", "no cell", absolute tolerance | reporting only | n/a |

Bugs 3–6 never touched a result. Bug 1 did change a feature verdict and is fixed with the evidence
above. Bug 2 was a real defect and was fixed with a full regression.

**Nothing outstanding requires a re-run.** The one item that could still change a number is the
known instability of the proxy-free regime: removing 5 of 636 cycles moves TD-Clean-6 between 0.490
and 0.664, so any proxy-free figure must be quoted with its dispersion and never as a stable point
value. That is a property of the problem, not an unfixed defect.

## Artifacts

`round3_phase1/` holds the code, the verification scripts, the run logs and the result/prediction
CSVs for every experiment in this round. The narrative documents are
`phase1_oracle_findings.md`, `phase2_summary_two_axes.md`, `r3c3_feature_classification.md`,
`phase3_charge_features_summary.md`, `phase3_selfref_summary.md` and
`round3_status_for_advisor.md`.