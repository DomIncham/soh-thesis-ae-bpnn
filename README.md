# SOH Thesis Research Repository

Research workspace for Dom's master's thesis at NTUST:

**State of Health (SOH) Estimation of Lithium-ion Batteries using Two-Stage Autoencoder + BPNN**

## Project Root

Local workspace:

```text
C:\Master Degree\Thesis
```

## Repository Policy

This repository is intended to back up and version-control research work, code, methodology notes, thesis materials, and selected Dom-authored literature review files.

Raw datasets, large external archives, generated tensors, and model checkpoints are intentionally excluded from Git to keep the repository lightweight and reproducible.

## Main Folders

```text
Autoencoder/                       # Stage-1 AE, BPNN, preprocessing, metrics, figures
Comment Prof and Report/           # Advisor/professor comments and reports
Journal Discovery/literature review by dom/ # Dom-authored literature review materials to keep in Git
examples/                          # LaTeX practice examples, ignored by Git for now
NASA DataSet/                      # Raw datasets, ignored by Git
```

## Important Files

```text
advisor_directives.md              # Advisor directives and methodology constraints
end_to_end_research_workflow_v2.md # End-to-end research workflow
E2E Research Workflow.html         # HTML version of workflow
README.md                          # Repository overview
.gitignore                         # Git inclusion/exclusion policy
data_manifest.md                   # Dataset source/path documentation
```

## What Should Be Committed

Recommended Git contents:

- Research code: `*.py`
- Small result tables: `*.csv`
- Thesis/research figures: `*.png`, `*.jpg` when relevant
- Methodology/workflow notes: `*.md`, `*.html`
- Advisor/professor reports and Dom-authored review documents
- LaTeX source files: `*.tex`, `*.bib`

## What Should Not Be Committed

Excluded from Git:

- Raw datasets: `NASA DataSet/`, `*.mat`
- Large compressed external datasets: `*.zip`
- Generated tensors: `*.pt`
- Model checkpoints: `*.pth`, `*.ckpt`, `*.onnx`
- Python cache: `__pycache__/`, `*.pyc`
- LaTeX build artifacts: `*.aux`, `*.bbl`, `*.fls`, etc.

## Active Dataset

The active NASA dataset is stored locally and documented in `data_manifest.md`.

Current active subset:

```text
C:\Master Degree\Thesis\NASA DataSet\1. BatteryAgingARC-FY08Q4
```

Cells currently used:

- B0005
- B0006
- B0007
- B0018

## Daily Git Workflow

After Git is initialized and connected to GitHub:

```bash
git status
git add .
git commit -m "Describe the research update"
git push
```

Use short commit messages such as:

```text
Add NASA EIS preprocessing script
Update LOBO validation results
Document AE-BPNN methodology
Add advisor report notes
```
