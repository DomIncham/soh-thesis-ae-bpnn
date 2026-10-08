# Autoencoder Research Workspace

This folder contains the SOH-estimation research pipeline, evidence, and thesis-supporting material. The layout separates historical research rounds from reusable infrastructure without duplicating code or results.

## Structure

```text
Autoencoder/
├─ round2_nested_lobo/   # Round 2 AE/BPNN and nested-LOBO evidence
├─ round3_phase1/        # Current Round 3 evidence, verification, and thesis drafts
├─ scripts/               # Reusable/general-purpose scripts
├─ configs/               # Shared configuration files
├─ eis_verify/            # Raw EIS verification workflow and evidence
├─ assets/                # Shared figures and supporting assets
├─ runs/                  # Local run outputs; generally excluded from Git
├─ archive/               # Obsolete local material
└─ <legacy root files>    # Earlier shared pipeline files pending classification
```

## Round map

| Area | Scope | Status |
|---|---|---|
| `round2_nested_lobo/` | Autoencoder reconstruction, BPNN baseline, nested LOBO, Steps 1–18 | Historical evidence; preserve as the Round 2 source of truth |
| `round3_phase1/` | Proxy audit, protocol comparisons, wider validation, cross-dataset analysis, thesis drafts | Current Round 3 working package |
| `scripts/` | Reusable scripts not tied to one historical round | Shared infrastructure |
| `configs/` | Shared experiment/configuration files | Shared infrastructure |
| `eis_verify/` | Verification of the raw NASA EIS representation | Shared verification workflow |
| `assets/` | Figures and support assets used across reports | Shared assets |
| `archive/` | Obsolete local material | Not part of the active pipeline |

## Important path policy

- Do not duplicate scripts, result tables, checkpoints, or reports between rounds.
- Round 3 may reuse Round 2 code and evidence; this dependency is intentional.
- Keep original Round 2 paths stable until the rename to `round2_nested_lobo/` is completed and all references are verified.
- Keep `round3_phase1/` as one working package for now. Do not split it into many subfolders before checking relative paths and report links.
- `Journal Discovery/` is outside this organization plan and remains under Dom's personal working structure.

## Planned rename

The existing `Autoencoder/nested_lobo/` directory represents Round 2. It is planned to become:

```text
Autoencoder/round2_nested_lobo/
```

That rename must be done as a separate, path-aware change. Before committing it, search the repository for `nested_lobo`, update source paths and links, run targeted verification, check GitHub links, and confirm that the working tree contains only the intended rename and reference changes.

## File classification rule

When adding a new file, classify it by function:

1. Round-specific evidence or report → the relevant round directory.
2. Reusable code or configuration → `scripts/` or `configs/`.
3. Raw EIS verification → `eis_verify/`.
4. Shared figures/assets → `assets/`.
5. Temporary logs, caches, checkpoints, and generated run outputs → keep local and follow `.gitignore`.

Do not create `Round 1`, `Round 2`, or `Round 3` duplicate copies merely for visual organization. The directory and this map are the source of truth.
