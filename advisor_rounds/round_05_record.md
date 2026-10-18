# Round 5 — record (active)

Source: `Comment Prof and Report/Comment Prof/Round 5 Advisor Comment.txt` (received 2026-10-15).
Status: ACTIVE — full run complete, final comparison report drafted, pending commit/push and
advisor delivery.

Items (from `advisor_directives.md` §Round 5):

- R5-C1 — CALCE selection stages use rotated battery-wise validation. DONE: implemented in
  `phase5_cs2_clean5t.py`, all four arms rerun (280 rows, 5 seeds, 0 NaN).
- R5-C2 — Clean-5T (Clean-6T minus t_40_41) vs Clean-6T on cross-dataset transfer. DONE:
  within median 0.573 → 0.581; transfer room per-cell means worsen without t_40_41
  (−7.7…−14.3 → −28.9…−43.5); all-13 and adapt1 improve but stay deeply negative; adapt2
  worsens (−3.5 → −13.1).
- R5-C3 — interpretation wording. DONE: report uses "consistent with, not proven caused by";
  proxy-amplification evidence added (transfer median −37.1 → −2.8 with proxies removed,
  within 0.589 → 0.573).
- R5-C4 — B0006 inner-fold description. DONE: report §1.1 rewritten; structural check S6 added
  to `round4_structural_verify.py` (outer battery absent from every inner train/val set;
  suite passes 26/26).
- R5-C5 — deliverable: `Autoencoder/round3_phase1/round5_comparison_report.md` (updated
  comparison only). If the gap remains → next direction is domain-shift/range-alignment
  analysis (not started; awaiting advisor confirmation).
