# Advisor Round 3 — Literature Gap Audit

- **Received:** 2026-09-26
- **Status:** Resolved
- **Original source:** `Comment Prof and Report/Comment Prof/Round 3 Literature_Gap_Audit_NASA_SOH.pdf`
- **Text extraction:** `Comment Prof and Report/Comment Prof/Round 3 Literature_Gap_Audit_NASA_SOH.txt`
- **Detailed evidence:** `Autoencoder/round3_phase1/PROJECT_STATE.md` and phase summary files
- **Citation verification:** `Autoencoder/round3_phase1/r3c9_citation_verification.md`

## Advisor's Main Direction

The lower scores were attributed to a stricter evaluation protocol and different inputs, not to a confirmed data-processing error. The research direction was to convert this strictness into a measurable contribution by auditing protocol effects and capacity-proxy features.

## Required Items

| ID | Requirement | Final status |
|---|---|---|
| R3-C1 | Evaluation protocol fixes, refit on all training batteries, reporting standard | Complete |
| R3-C2 | Random vs chronological vs nested LOBO protocol-gap experiment | Complete |
| R3-C3 | Safe/proxy feature audit with TD-All, proxy-free, and oracle settings | Complete |
| R3-C4 | Novelty constraint and positioning against the closest published work | Complete |
| R3-C5 | Proxy-free accuracy improvement experiments | Complete |
| R3-C6 | Wider validation and cross-dataset evaluation | Complete, with condition/domain-shift qualifications |
| R3-C7 | Establish the role of EIS and the autoencoder | Complete; AE demoted to documented negative result |
| R3-C8 | Report feature definitions, refit status, sample counts, and fold metrics | Complete |
| R3-C9 | Verify cited literature against full papers | Complete; 13/13 papers verified |

## Final Thesis Direction

The main direction is **proxy-audited, partial-window, unseen-battery SOH estimation**.

- TD-BPNN is the main pipeline.
- The AE is reported in the negative-results or appendix section.
- The thesis title no longer needs to retain “Autoencoder” unless a later advisor directive changes this.
- A partial window is not automatically proxy-free; every feature must still be audited.

## Key Verified Outcomes

- Random and strict unseen-battery protocols produce materially different scores.
- Capacity-proxy features explain a substantial part of the high-score axis.
- Clean-8 is the supported proxy-audited arm from Round 3.
- AE-on-TD was worse than raw TD, and AE did not add measurable value to the EIS/TD direction.
- The cross-dataset result requires domain-shift qualification and a within-dataset control.
- Literature comparisons must state the unit, split protocol, and feature/proxy status.

## Evidence Pointers

- Phase map and verification ledger: `Autoencoder/round3_phase1/PROJECT_STATE.md`
- Citation verification: `Autoencoder/round3_phase1/r3c9_citation_verification.md`
- Chapter drafts: `Autoencoder/round3_phase1/thesis_ch1_introduction_draft.md`, `thesis_ch3_methodology_draft.md`, `thesis_ch4_protocol_draft.md`, `thesis_ch5_discussion_draft.md`, and `thesis_appendix_negative_results.md`
- Report sent or ready for advisor: `Autoencoder/round3_phase1/round4_report_to_advisor.md`

## Items Promoted to Live Directives

- Use nested LOBO for unseen-battery evaluation.
- Audit target proxies explicitly.
- Do not compare metrics across different row sets without identifying the row set.
- Cite from full papers and annotate unit and protocol.
- Treat the AE as a documented negative result unless new evidence or an explicit advisor directive changes the direction.

## Round 4 Boundary

Round 3 is closed. No Round 4 advisor comment has been received in the source-comment folder at the time this record was created. Do not infer new Round 4 requirements from the Round 3 report or from the filename `round4_report_to_advisor.md`; that file is a report prepared for the advisor, not a Round 4 comment source.
