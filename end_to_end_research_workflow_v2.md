# E2E Research Workflow & Budget (v4 — Unified GLM 5.3 Flash)

> งบ 500 THB/เดือน บน OpenRouter · ใช้จริง ~50-100 THB (10-20%)
> ที่มา: `model_eval/run2/` (debate) + `run3b/` (coding) + `run4/` (reasoning A/B) + **Dom real usage Sep 2026**

---

## 1. Model Stack — **Unified GLM 5.3 Flash**

| Phase | โมเดล | slug | $/session | reasoning | ใช้ทำอะไร |
| :--- | :--- | :--- | ---: | :--- | :--- |
| **P1** Extract | GLM 5.3 Flash | `z-ai/glm-5.3-flash` | ~0.01-0.03 | medium | อ่าน PDF comment อาจารย์ → append `advisor_directives.md` |
| **P2** Debate | GLM 5.3 Flash | `z-ai/glm-5.3-flash` | ~0.01-0.03 | **medium** (ปิดไม่ได้) | ถก methodology ตาม 4 Rules → `active_experiment.md` |
| **P3** Coding | GLM 5.3 Flash | `z-ai/glm-5.3-flash` | ~0.01-0.03 | **medium — ห้ามปิด** | เขียน Python script AE/BPNN ตาม state card |
| **P4** Report | GLM 5.3 Flash | `z-ai/glm-5.3-flash` | ~0.01-0.03 | medium | เขียน **report.md ครบ** → Dom เปิด **Antigravity → PDF** |
| **P3F** Fallback | DeepSeek V4 Flash 0731 | `deepseek/deepseek-v4-flash-0731` | 0.0024 | medium | Backup coding |
| **P3F** Fallback | GPT-5.6 Sol | `openai/gpt-5.6-sol` | 0.0900 | medium | Backup coding |

**Single model end-to-end**: `z-ai/glm-5.3-flash` ครบทุก Phase — context ต่อเนื่อง ไม่ต้องสลับโมเดล

### ค่าใช้จ่ายต่อเดือน (P1+P2+P3+P4 = ~$0.04/session)

| Scenario | Sessions | THB | % งบ |
| :--- | ---: | ---: | ---: |
| Light | 15 | ~35 | 7% |
| **Normal** | **25** | **~58** | **12%** |
| Heavy | 40 | ~92 | 18% |
| + thinking medium (+30-50% output) | 40 | ~120-140 | 24-28% |

---

## 2. Flow

```
P1 Extract → P2 Debate → [4-Rule Gate] → /new + active_experiment.md
          → P3 Code → [Validity Gate] → VS Code (Dom) → Git → Run (Dom GPU)
          → ผลย้อนกลับ P2
          → P4 Report (report.md) → Antigravity → PDF
```

| Phase | ทำอะไร | ใครรัน | โมเดล |
| :--- | :--- | :--- | :--- |
| P1 | อ่าน PDF comment อาจารย์ → append `advisor_directives.md` | Capi | GLM 5.3 Flash |
| P2 | ถก methodology ตาม 4 Rules → `active_experiment.md` | Capi | GLM 5.3 Flash |
| P3 | เขียน Python script ตาม state card | Capi | GLM 5.3 Flash |
| P3 ตรวจ | Validity Gate (run จริง + ตรวจตัวเลข) | Capi | GLM 5.3 Flash |
| P3 รัน | copy → VS Code → train บน RTX 3050 | **Dom** | — |
| P4 | synthesise ผล → **report.md** → Antigravity → PDF | Dom | GLM 5.3 Flash |

---

## 3. Gates

### 4-Rule Gate (ก่อนออกจาก P2)

1. Options อะไรบ้างที่พิจารณา?
2. ทำไม option นี้เหมาะ?
3. หลักฐานสถิติอะไร?
4. Leakage / Generalization / Real-time?

ไม่ผ่าน → วนกลับ debate

### Validity Gate (ก่อนส่งโค้ดให้ Dom)

**รันโค้ดก่อนตัดสิน — exit code 0 ไม่ได้แปลว่าถูก**

| # | เช็ค | เกณฑ์ |
| :---: | :--- | :--- |
| 1 | รันจบ | exit 0 |
| 2 | ไม่มี NaN | ไม่มีสตริง "nan" ใน output |
| 3 | R² สมเหตุสมผล | train > 0.5 และ -2 ≤ test ≤ 1 |
| 4 | metric ครบ | MAE, RMSE, R² ทุก battery |
| 5 | mean ± std | ถ้า multi-fold |
| 6 | Leakage probe | perturb test ×2 → **train ต้องไม่ขยับ** |

ไม่ผ่าน → ส่ง error กลับให้โมเดลซ่อม **1 ครั้ง** → ยังพัง → P3F (DeepSeek V4 Flash 0731 → GPT-5.6 Sol)

### `active_experiment.md` ต้องมี

- [ ] LOBO split ชัด (battery ไหน train/test)
- [ ] MAE, RMSE, R² **แยกต่อ battery** + mean ± std
- [ ] decision rule ก่อนรัน

---

## 4. Hard Rules (Learned from Run 3 + Run 3b + Dom Real Usage)

| # | กฎ |
| :---: | :--- |
| 1 | **exit code 0 ≠ ถูก** — เพ่งตัวเลขทุกครั้ง |
| 2 | **standardize target ก่อน train BPNN** (failure mode อันดับ 1: SOH ~90, net init ~0) |
| 3 | **`list == "str"` ได้ `False` เดี่ยว** ไม่ใช่ mask → `X_all[False]` = array ว่าง → NaN เงียบ |
| 4 | **`max_tokens ≥ 6000`** เมื่อเปิด reasoning — GLM 5.3 Flash ต้อง **≥16000 ตอนซ่อม** |
| 5 | **บังคับ loop ซ่อม 1 ครั้งเสมอ** (ผ่านครั้งแรกแค่ 3/12 โมเดล) |
| 6 | **Leakage probe ทุกครั้ง** — พิสูจน์ ไม่ใช่เชื่อ |
| 7 | **รายงานแยกต่อ battery + mean ± std** (advisor Part C3) |
| 8 | **P3 ห้ามปิด reasoning** — ปิดแล้วได้โค้ด exit 0 แต่ R² = -14.9 |
| 9 | **Single model stack**: GLM 5.3 Flash ครบทุก Phase — ไม่สลับโมเดล |

---

## 5. Execution Rules

1. **PAEV:** Plan → Approve 1× → Execute batch → Verify
2. **4 Rules** defense ทุกการตัดสินใจ
3. **Context Pruning** `/new` ระหว่าง P2→P3
4. **Git commit** ก่อนรันทุกครั้ง
5. **Ablation Log:** `YYYY-MM-DD | exp_name | key_metric | insight`
6. **Hybrid:** Capi รัน script <50 บรรทัด/ไม่ใช้ GPU · Dom รัน training + sweep
7. **Token hygiene:** ตอบสั้น ไม่ verbose
8. **Antigravity for PDF** — ไม่ใช้ pandoc/MiKTeX

---

## 6. หลักฐานรายละเอียด

`C:\Master Degree\model_eval\` — `run2/` debate · `run3/` coding pilot · `run3b/` coding เต็ม · `run3c/` v4.1-flash · `shortlist.md` (43 โมเดล)

**Dom validated (Sep 2026):** GLM 5.3 Flash works for P1+P2+P3+P4 end-to-end. Report.md → Antigravity → PDF = best quality.