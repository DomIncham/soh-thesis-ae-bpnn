# P6B-4 verification: assert every number in round6b_closure.md against source CSVs,
# then run the pre-send grep checklist (Round 5 report convention).
import re
import numpy as np
import pandas as pd

doc = open("round6b_closure.md", encoding="utf-8").read()
cal = pd.read_csv("phase6b_cal_only.csv")
m = pd.read_csv("phase6b_matched_3way.csv")
w = pd.read_csv("phase5_cs2_within_c5t_full.csv")
lc = pd.read_csv("phase6_ladder_Lc.csv")
d = pd.read_csv("phase6_preds_transfer_full.csv", low_memory=False)
dump = pd.read_csv("phase6b_cal_only_preds.csv", low_memory=False)
ok = []

def chk(name, cond):
    assert cond, f"FAILED: {name}"
    ok.append(name)

def r3(x): return round(float(x), 3)
def r2(x): return round(float(x), 2)

chk("cal runs 80", len(cal) == 80)
chk("matched rows 80", len(m) == 80)
chk("Cal mean 17.34", r3(m.MAE_cal.mean()) == 17.338)
chk("Cal median 13.66", r2(m.MAE_cal.median()) == 13.66)
chk("FT mean 13.74", r3(m.MAE_ft.mean()) == 13.742)
chk("FT median 11.95", r2(m.MAE_ft.median()) == 11.95)
chk("FTCal mean 13.20", r3(m.MAE_ftcal.mean()) == 13.197)
chk("FTCal median 12.18", r2(m.MAE_ftcal.median()) == 12.18)
chk("L0 mean 23.54", r3(m.MAE_L0.mean()) == 23.543)
chk("L0 median 23.75", r2(m.MAE_L0.median()) == 23.75)
chk("Cal degenerate 50", int(m.deg_cal.sum()) == 50)
chk("Lc degenerate 45", int(m.deg_lc.sum()) == 45)
chk("FT lower than Cal 53/80", int((m.MAE_ft < m.MAE_cal).sum()) == 53)
chk("Cal lower than FTCal 25/80", int((m.MAE_cal < m.MAE_ftcal).sum()) == 25)
chk("FT lower than FTCal 50/80", int((m.MAE_ft < m.MAE_ftcal).sum()) == 50)
red = lambda c: (m.MAE_L0 - m[c]) / m.MAE_L0
chk("red(a) Cal med 0.0", round(red("MAE_cal").median() * 100, 1) == 0.0)
chk("red(a) Cal mean 17.8", round(red("MAE_cal").mean() * 100, 1) == 17.8)
chk("red(a) FT med 42.8", round(red("MAE_ft").median() * 100, 1) == 42.8)
chk("red(a) FT mean 36.7", round(red("MAE_ft").mean() * 100, 1) == 36.7)
chk("red(a) FTCal med 37.1", round(red("MAE_ftcal").median() * 100, 1) == 37.1)
chk("red(a) FTCal mean 27.0", round(red("MAE_ftcal").mean() * 100, 1) == 27.0)
rec = lambda c: (m.MAE_L0 - m[c]) / (m.MAE_L0 - m.floor_matched)
chk("rec(b) Cal med 0.0", round(rec("MAE_cal").median() * 100, 1) == 0.0)
chk("rec(b) Cal mean 18.3", round(rec("MAE_cal").mean() * 100, 1) == 18.3)
chk("rec(b) FT med 50.1", round(rec("MAE_ft").median() * 100, 1) == 50.1)
chk("rec(b) FT mean 31.3", round(rec("MAE_ft").mean() * 100, 1) == 31.3)
chk("rec(b) FTCal med 42.7", round(rec("MAE_ftcal").median() * 100, 1) == 42.7)
chk("rec(b) FTCal mean 9.7", round(rec("MAE_ftcal").mean() * 100, 1) == 9.7)
chk("floor median 2.809", r3(m.floor_matched.median()) == 2.809)
nd = m[~m.deg_cal & ~m.deg_lc]
chk("joint non-deg 25", len(nd) == 25)
chk("joint Cal 9.00", r2(nd.MAE_cal.median()) == 9.00)
chk("joint FTCal 12.25", r2(nd.MAE_ftcal.median()) == 12.25)
chk("joint L0 38.83", r2(nd.MAE_L0.median()) == 38.83)
chk("joint Cal better 10/25", int((nd.MAE_cal < nd.MAE_ftcal).sum()) == 10)
ndc = m[~m.deg_cal]
chk("Cal own non-deg 30", len(ndc) == 30)
chk("Cal own 10.22", r2(ndc.MAE_cal.median()) == 10.22)
chk("own L0 30.86", r2(ndc.MAE_L0.median()) == 30.86)
idn = m[m.deg_cal]
chk("identity == L0 50/50", int(((idn.MAE_cal - idn.MAE_L0).abs() < 5e-4).sum()) == 50)
uc = d.drop_duplicates(["cell", "cycle"])
chk("unique cycles 4922", len(uc) == 4922)
chk("L0 instances 49220", len(d) == 49220)
chk("cal instances 344540", len(dump) == 344540)
chk("within runs 40", len(w) == 40)
# RMSE/R2 columns added to the matched table (roadmap Stage 1 evidence requirement)
import numpy as np
mm = pd.read_csv("phase6b_matched_3way.csv")
chk("matched has RMSE/R2 cols", all(c in mm for c in
    ["RMSE_cal","R2_cal","RMSE_ft","R2_ft","RMSE_ftcal","R2_ftcal","RMSE_L0","R2_L0"]))
chk("RMSE med Cal 18.80", r2(mm.RMSE_cal.median()) == 18.80)
chk("RMSE med FT 13.08", r2(mm.RMSE_ft.median()) == 13.08)
chk("RMSE med FTCal 17.31", r2(mm.RMSE_ftcal.median()) == 17.31)
chk("RMSE med L0 25.51", r2(mm.RMSE_L0.median()) == 25.51)
chk("R2 med Cal -12.76", r2(mm.R2_cal.median()) == -12.76)
chk("R2 med FT -5.92", r2(mm.R2_ft.median()) == -5.92)
chk("R2 med FTCal -11.22", r2(mm.R2_ftcal.median()) == -11.22)
chk("R2 med L0 -25.76", r2(mm.R2_L0.median()) == -25.76)
chk("RMSE mean Cal 21.07", r2(mm.RMSE_cal.mean()) == 21.07)
chk("RMSE mean FT 16.34", r2(mm.RMSE_ft.mean()) == 16.34)
chk("RMSE mean FTCal 19.22", r2(mm.RMSE_ftcal.mean()) == 19.22)
chk("RMSE mean L0 25.82", r2(mm.RMSE_L0.mean()) == 25.82)
chk("report has RMSE/R2 table", "RMSE median" in doc and "R2 median" in doc)
chk("report has decision point", "simplest defensible adaptation method" in doc)
# slope values used in degenerate criterion
lc["slope"] = lc.variant.str.replace("slope=", "").astype(float)
chk("Lc slope criterion replicates 45",
    int(((lc.slope <= 0) | ((lc.slope - 1).abs() >= 1)).sum()) == 45)
print(f"ALL {len(ok)} REPORT NUMBERS VERIFIED against source CSVs")

# pre-send grep checklist
bad = {
    "prove/confirm/successfully": re.findall(r"\bprove\b|\bconfirm\b|\bsuccessfully\b", doc, re.I),
    "em dash": re.findall("\u2014|\u2013", doc),
    "double asterisk": re.findall(r"\*\*", doc),
    "curly quotes": re.findall("[\u2018\u2019\u201c\u201d]", doc),
}
# whitelist technical identifiers (arm names, file names) like "early-stopping"
allow = re.compile(r"Cal-only|FT-only|cal_only|calibration_only|\w+\.csv|\w+\.py|early-stopping")
ly = [wd for wd in re.findall(r"\b\w+ly\b", doc, re.I)
      if not allow.search(doc[max(0, re.search(r"\b" + re.escape(wd) + r"\b", doc, re.I).start() - 30):
                              re.search(r"\b" + re.escape(wd) + r"\b", doc, re.I).end() + 30])]
bad["-ly adverbs"] = ly
for k, v in bad.items():
    print(f"checklist {k}: {len(v)}", ("-> " + str(v[:5])) if v else "OK")
assert all(len(v) == 0 for v in bad.values()), "checklist failed"
print("GREP CHECKLIST CLEAN")
