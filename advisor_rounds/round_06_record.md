# Round 6 — record (active)

Source: `Comment Prof and Report/Comment Prof/Round 6 Advisor Comment.txt` (received 2026-10-20).
Status: ACTIVE — comment transcribed into `advisor_directives.md` §Round 6 (R6-C0…C5);
experiments NOT started; PAEV plan pending Dom's approval.

Items (from `advisor_directives.md` §Round 6):

- R6-C0 — feature-set policy: Clean-5T = primary proxy-audited set for zero-shot cross-dataset
  analysis; Clean-6T stays as an ablation, especially for adaptation arms (t_40_41 helps warm-start).
  NOT STARTED.
- R6-C1 — wording correction: NASA 57–101% vs CALCE 87–113% partially overlap at ~87–101%;
  replace any "ranges do not overlap" phrasing with "substantial range mismatch with partial
  overlap". Fix in `round5_comparison_report.md` (and re-export the PDF via Antigravity). NOT STARTED.
- R6-C2 — diagnosis before adaptation, in order: (1) per-feature NASA/CALCE distribution
  comparison (range overlap, shift, % of CALCE samples outside the NASA training range);
  (2) common-SOH-range diagnostic on ~87–101% (diagnostic only, not a final result);
  (3) inside-vs-outside NASA feature-support error split; (4) Ridge baseline on the same
  Clean-5T features and protocol (no large model comparison); (5) alignment ladder:
  source-only scaling → unsupervised alignment on target training cells only → one-cell output
  calibration, before any further NN fine-tuning. NOT STARTED.
- R6-C3 — rotated battery-wise validation and outer-test isolation unchanged; estimator
  configuration as controlled as possible. Standing constraint on all Round 6 runs.
- R6-C4 — record the selection fallback rate in every Round 6 experiment; do not attribute
  divergence/fallback only to domain shift. New standing reporting requirement.
- R6-C5 — report = compact progression: raw transfer → common-range diagnosis →
  feature-support diagnosis → simple baseline → range/domain alignment. Purpose: identify why
  transfer fails and how much the simplest defensible alignment recovers.

Housekeeping: original comment file untouched.
