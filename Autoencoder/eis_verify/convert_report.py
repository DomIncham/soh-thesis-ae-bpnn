# P4 helper: convert a .md report to Word (.docx) and PDF with embedded images
# Usage: python convert_report.py <report.md> [out_base]
import os
import sys
import pypandoc

src = sys.argv[1] if len(sys.argv) > 1 else r"C:\Master Degree\Thesis\Autoencoder\eis_verify\EIS_Raw_Verification.md"
base = os.path.splitext(src)[0] if len(sys.argv) < 3 else sys.argv[2]
d = os.path.dirname(src)

def which(engine):
    for p in os.environ.get("PATH", "").split(os.pathsep):
        if os.path.isfile(os.path.join(p, engine + ".exe")):
            return os.path.join(p, engine + ".exe")
    return None

# 1) Word: no LaTeX needed
docx = base + ".docx"
pypandoc.convert_file(src, "docx", outputfile=docx, extra_args=["--resource-path", d])
print("OK docx:", docx, os.path.getsize(docx), "bytes")

# 2) PDF: needs a LaTeX engine (MiKTeX)
engine = which("xelatex") or which("pdflatex")
if engine:
    pdf = base + ".pdf"
    pypandoc.convert_file(src, "pdf", outputfile=pdf, extra_args=[
        "--pdf-engine", engine, "--resource-path", d,
        "-V", "geometry:margin=2.5cm", "-V", "fontsize=11pt"])
    print("OK pdf:", pdf, os.path.getsize(pdf), "bytes, engine:", engine)
else:
    print("PDF skipped: no LaTeX engine on PATH (docx was still produced)")