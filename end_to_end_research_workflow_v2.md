# E2E Research Workflow & Budget (v3)

> งบ 500 THB/เดือน บน OpenRouter · ใช้จริง ~76-150 THB (15-30%)
> ที่มา: `model_eval/run2/` (debate) + `run3b/` (coding) + `run4/` (reasoning A/B)

---

## 1. Model Stack

| Phase | โมเดล | slug | $/session | reasoning |
| :--- | :--- | :--- | ---: | :--- |
| **P1** Extract | GLM 5.3 | `z-ai/glm-5.3` | ~0.02-0.05 | medium |
| **P2** Debate | GLM 5.3 | `z-ai/glm-5.3` | 0.0832 | **medium** (ปิดไม่ได้ · 0 token) |
| **P3** Coding | DeepSeek V4 Flash 0731 | `deepseek/deepseek-v4-flash-0731` | **0.0024** | **medium — ห้ามปิด** |
| **P3F** Fallback | GPT-5.6 Sol | `openai/gpt-5.6-sol` | 0.0900 | medium |
| **P4** Report | Capi ร่าง report .md + ฝังรูป → Dom review + แปลง Word/PDF | — | ฟรี | — |

P1 ใช้ GLM 5.3 ตัวเดียวกับ P2 — context ต่อเนื่อง ไม่ต้องสลับโมเดล

### ค่าใช้จ่ายต่อเดือน (P2+P3 = $0.0856/session)

| Scenario | Sessions | THB | % งบ |
| :--- | ---: | ---: | ---: |
| Light | 15 | 46 | 9% |
| **Normal** | **25** | **76** | **15%** |
| Heavy | 40 | 122 | 24% |
| + thinking medium (+30-50% output) | 40 | 160-185 | 32-37% |

---

## 2. Flow

```
P1 Extract → P2 Debate → [4-Rule Gate] → /new + active_experiment.md
          → P3 Code → [Validity Gate] → VS Code (Dom) → Git → Run (Dom GPU)
          → ผลย้อนกลับ P2
```

| Phase | ทำอะไร | ใครรัน |
| :--- | :--- | :--- |
| P1 | อ่าน PDF comment อาจารย์ → append `advisor_directives.md` | Capi |
| P2 | ถก methodology ตาม 4 Rules → `active_experiment.md` | Capi |
| P3 | เขียน Python script ตาม state card | Capi |
| P3 ตรวจ | Validity Gate (run จริง + ตรวจตัวเลข) | Capi |
| P3 รัน | copy → VS Code → train บน RTX 3050 | **Dom** |
| P4 | synthesise ผล → Word → PDF ส่งอาจารย์ | Dom (Gemini Plus) |

---

## 3. Gates

### 4-Rule Gate (ก่อนออกจาก P2)

1. Options อะไรบ้างที่พิจารณา? 2. ทำไม option นี้เหมาะ? 3. หลักฐานสถิติอะไร? 4. Leakage / Generalization / Real-time?
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

ไม่ผ่าน → ส่ง error กลับให้โมเดลซ่อม **1 ครั้ง** → ยังพัง → P3F (GPT-5.6 Sol)

### `active_experiment.md` ต้องมี

- [ ] LOBO split ชัด (battery ไหน train/test)
- [ ] MAE, RMSE, R² **แยกต่อ battery** + mean ± std
- [ ] decision rule ก่อนรัน

---

## 4. Hard Rules

| # | กฎ |
| :---: | :--- |
| 1 | **exit code 0 ≠ ถูก** — เพ่งตัวเลขทุกครั้ง |
| 2 | **standardize target ก่อน train BPNN** (failure mode อันดับ 1) |
| 3 | **`list == "str"` ได้ `False` เดี่ยว** ไม่ใช่ mask → `X_all[False]` = array ว่าง → NaN เงียบ |
| 4 | **`max_tokens ≥ 6000`** เมื่อเปิด reasoning — GLM/v4.1-flash ต้อง **≥16000 ตอนซ่อม** |
| 5 | **บังคับ loop ซ่อม 1 ครั้งเสมอ** (ผ่านครั้งแรกแค่ 3/12 โมเดล) |
| 6 | **Leakage probe ทุกครั้ง** — พิสูจน์ ไม่ใช่เชื่อ |
| 7 | **รายงานแยกต่อ battery + mean ± std** (advisor Part C3) |
| 8 | **P3 ห้ามปิด reasoning** — ปิดแล้วได้โค้ด exit 0 แต่ R² = -14.9 (T2) หรือไม่ได้โค้ดเลย (T1) |

---

## 5. Execution Rules

1. **PAEV:** Plan → Approve 1× → Execute batch → Verify
2. **4 Rules** defense ทุกการตัดสินใจ
3. **Context Pruning** `/new` ระหว่าง P2→P3
4. **Git commit** ก่อนรันทุกครั้ง
5. **Ablation Log:** `YYYY-MM-DD | exp_name | key_metric | insight`
6. **Hybrid:** Capi รัน script <50 บรรทัด/ไม่ใช้ GPU · Dom รัน training + sweep
7. **Token hygiene:** ตอบสั้น ไม่ verbose

---

## 6. หลักฐานรายละเอียด

`C:\Master Degree\model_eval\` — `run2/` debate · `run3/` coding pilot · `run3b/` coding เต็ม · `run3c/` v4.1-flash · `shortlist.md` (43 โมเดล)