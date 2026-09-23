# Data Manifest

This file documents datasets used by the SOH thesis project. Raw datasets are kept locally; since 2026-09-23 one exception is tracked in Git (see Git Policy).

## Git Policy

The following are intentionally excluded from Git:

```text
NASA DataSet/
*.mat
*.zip
*.pt
*.pth
*.ckpt
*.onnx
```

Exception (tracked since 2026-09-23):

```text
NASA DataSet/1. BatteryAgingARC-FY08Q4/   (~56 MB, public-domain NASA data)
```

Reason for the exception: the Round 2 EIS verification (advisor Part A, Steps 1-4) is defined against these exact files; tracking them makes the verification reproducible from a plain clone. Other NASA folders and all archives remain excluded.

Reason:

- Raw datasets are large external artifacts.
- Binary files do not version well in normal Git.
- The repository should stay lightweight for code, thesis files, and reproducible documentation.
- Generated tensors and model checkpoints can be recreated from code and documented dataset sources.

## Active Dataset: NASA Battery Aging Dataset

Local path:

```text
C:\Master Degree\Thesis\NASA DataSet\1. BatteryAgingARC-FY08Q4
```

Observed local size during workspace audit:

```text
~56 MB
```

Observed file types:

```text
4 .mat files
4 .m files
2 .jpg files
2 .csv files
1 .txt file
```

Cells used in the current SOH workflow:

- B0005
- B0006
- B0007
- B0018

Typical LOBO split used in the project:

```text
Train: B0005 + B0006
Validation: B0007
Test: B0018
```

## Additional Local Dataset Archives

These files exist locally but are excluded from Git:

```text
C:\Master Degree\Thesis\Dataset_1_NCA_battery.zip
C:\Master Degree\Thesis\Dataset_2_NCM_battery.zip
C:\Master Degree\Thesis\Impedance raw data and fitting data.zip
```

Observed during audit:

```text
Dataset_1_NCA_battery.zip: ~553 MB
Dataset_2_NCM_battery.zip: ~703 MB
Impedance raw data and fitting data.zip: ~1.3 MB
```

## Reproducibility Note

To reproduce the project on another machine:

1. Clone the Git repository.
2. The NASA FY08Q4 dataset is included in the repository at:

```text
NASA DataSet/1. BatteryAgingARC-FY08Q4
```

3. Run preprocessing scripts from `Autoencoder/` to regenerate intermediate files such as:

```text
Interpolated_EIS_*.pt
Mapped_EIS_SOH_*.pt
AE_Model_*.pth
Trained_AE_Model.pth
```

These generated files are excluded from Git by design.
