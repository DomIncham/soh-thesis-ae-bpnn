from pypdf import PdfReader
rd = PdfReader(r"C:\Master Degree\Thesis\Autoencoder\nested_lobo\Progress_Report_Steps1-18.pdf")
txt = "\n".join(p.extract_text() for p in rd.pages)
checks = ["34,593", "B6", "PCHIP", "TD-BPNN", "E_fusion", "Q_ref", "Part J", "EarlyStopping",
          "ModelCheckpoint", "tolerance", "B0018", "amplitude domain shift", "3,548"]
for c in checks:
    print(f"{c}: {'OK' if c in txt else 'MISSING'}")
print("pages:", len(rd.pages), "| chars:", len(txt))