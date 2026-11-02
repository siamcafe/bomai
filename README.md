# 🤖 BOM AI — ผู้ช่วย AI ภาษาไทย ฟรี 100% ทำงานบนเครื่องคุณเอง

![BOM AI Hero Banner](docs/images/hero_banner_wide.png)

> **"แจกฟรี สำหรับมนุษยชาติ"** — ติดตั้งคลิกเดียว ใช้ได้ทันที ข้อมูลไม่ถูกส่งออกนอกเครื่อง
> ส่วนหนึ่งของภารกิจ *Heal the World* — AI ฟรีเพื่อการศึกษาสำหรับคนไทยทุกคน

[เว็บไซต์ bomai.app](https://bomai.app) · [ดาวน์โหลด](https://bomai.app/download) · [คู่มือฉบับเต็ม](README.th.md) · [English](README.en.md)

[![Download](https://img.shields.io/badge/download-bomai.app-blue)](https://bomai.app/download) [![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE) ![Version](https://img.shields.io/badge/version-v2.0.0-orange)

## ✨ ความสามารถ

- 🇹🇭 **ภาษาไทยเป็นหลัก 100%** — ถาม-ตอบ อ่าน เขียน แปล ภาษาไทยได้เป็นธรรมชาติ ผ่านการทดสอบ Thai gate ≥ 9.0
- 🔒 **ทำงานบนเครื่องคุณ 100%** — ทุกอย่างรันที่ local (127.0.0.1) แชทและรูปภาพไม่ถูกส่งออกนอกเครื่องแม้แต่ไบต์เดียว
- 🖼️ **อ่านข้อความในภาพ (Vision/OCR)** — ถ่ายใบเสร็จ สลิป ป้ายหน้าร้าน เอกสาร แล้วถามได้ทันที
- ⚡ **ติดตั้ง 1 คลิก** — Windows / macOS / Linux ตัวติดตั้งตรวจสเปกเครื่องแล้วเลือกโมเดลที่เหมาะสมให้อัตโนมัติ
- 🚫 **ออฟไลน์ได้เต็มรูปแบบ** — ใช้เน็ตเฉพาะตอนติดตั้งครั้งแรก หลังจากนั้นตัดเน็ตก็คุยได้
- 💚 **ฟรีไม่มีเงื่อนไข** — ไม่ต้องสมัครสมาชิก ไม่มีโฆษณา ไม่จำกัดจำนวนข้อความ ไม่มีการเก็บ/ขายข้อมูล

## 📊 ผลทดสอบจริง (Benchmark)

**ระบบผลิต (Production pipeline) — ตรวจสอบโดย QC20, GOD CONFIG v7.0:**

| ตัวชี้วัด | ค่าที่วัดได้จริง |
|---|---|
| ⚡ TTFT (เวลาตอบตัวอักษรแรก) | **2.29 วินาที** |
| 🔍 Web search แบบ end-to-end | **19.21 วินาที** |
| 📀 Cache hit TTFT | **0.062 วินาที** |
| 🏃 ความเร็วสร้างคำตอบ | **22.4 tokens/วินาที** |
| 🇹🇭 คุณภาพภาษาไทย QC20 | **20/20 PASS** |
| 🎯 การรั่วของอักษรจีน (Han leak) | **0 ตัวอักษร** |

**โมเดล BOM AI v0.3.2 — ผ่านประตูคุณภาพทั้ง 6 ด่าน (Ship Gates 6/6 PASS):**

| ด่านตรวจ | ผลลัพธ์ |
|---|---|
| Zero-Han (อักษรจีนรั่ว) | **250/250 บันทึก = 0 อักษรจีน** |
| คุณภาพภาษาไทย | **≥ 9.0** |
| Vision (อ่านภาพ) | ✅ PASS |
| ตัวตน/Identity | ✅ PASS (ตอบว่าเป็น "BOM") |
| การปฏิเสธงานที่ควรทำได้ (Refusal) | ✅ PASS |
| Regression | ✅ PASS |

## 🚀 ติดตั้ง 1 คลิก

### Windows (PowerShell)
```powershell
# ดาวน์โหลด 86KB แล้วตัวติดตั้งจะดึง component เอง (~3GB)
Invoke-WebRequest -Uri "https://bomai.app/dl/Install-BOM-AI-Online.bat" -OutFile "Install-BOM-AI.bat"
.\Install-BOM-AI.bat
```

### macOS
```bash
curl -fsSL https://bomai.app/dl/install-bom-ai-mac.sh | bash
```

### Linux
```bash
curl -fsSL https://bomai.app/dl/install-bom-ai-linux.sh | bash
```

หรือดาวน์โหลดตัวติดตั้งแบบสมบูรณ์จาก **[bomai.app/download](https://bomai.app/download)** (มี SHA-256 ให้ตรวจสอบทุกไฟล์)

## 🤖 เลือกโมเดลตามสเปกเครื่อง

| ระดับ | RAM | ดาวน์โหลด | เหมาะกับ |
|---|---|---|---|
| **V4B** | 8 GB+ | ~2.5 GB | แชทไทย อ่านภาพ ถาม-ตอบ งานสั้น |
| **V8B** | 16 GB+ | ~5.0 GB | งานเอกสารยาว แปลไทย-อังกฤษเต็มรูปแบบ |
| **V12B** | 24 GB+ | ~7.3 GB | คุณภาพสูงสุด ตาราง แผนภูมิ งาน Vision ซับซ้อน |

ตัวติดตั้งตรวจ RAM + VRAM ให้เอง แล้วแนะนำระดับที่เหมาะกับเครื่อง — แก้ไขเองได้เสมอ

## 🔧 GOD CONFIG v7.0 (LOCKED)

พารามิเตอร์ระดับโปรดักชันที่ผ่านการ QC จนนิ่ง ห้ามเปลี่ยน:

| พารามิเตอร์ | ค่า | เหตุผล |
|---|---|---|
| temperature | **0.6** | เกิน 0.7 = คุณภาพภาษาไทยตก |
| top_p | **0.95** | สมดุลความหลากหลายของคำ |
| top_k | **20** | โฟกัสคลังคำศัพท์ |
| repeat_penalty | **1.0** | ≠1.0 = มีโอกาสรั่วภาษาจีน |
| presence_penalty | **0.0** | ⛔ เหล็กใน — ค่าอื่นที่ไม่ใช่ 0 = อักษรจีนรั่ว |
| num_ctx | **8192** | เหมาะกับภาษาไทย (ตัวติดตั้งปรับตามระดับ RAM: 4096/8192) |
| num_predict | **4096** | คำตอบครบถ้วน |
| think | **false** | กัน code-switch ภาษา |

## 📸 หน้าจอโปรแกรม

| หน้าแรก | แชทภาษาไทย | แชทภาษาอังกฤษ | ตั้งค่า |
|---|---|---|---|
| ![หน้าแรก](docs/images/screenshots/01_home.png) | ![แชทไทย](docs/images/screenshots/02_chat_thai.png) | ![แชทอังกฤษ](docs/images/screenshots/03_chat_english.png) | ![ตั้งค่า](docs/images/screenshots/04_settings.png) |

## 🏆 รายละเอียดโมเดล

- **Base model:** [DavidAU/Qwen3.5-4B-Claude-4.6-HighIQ-THINKING](https://huggingface.co/DavidAU/Qwen3.5-4B-Claude-4.6-HighIQ-THINKING)
- **สถาปัตยกรรม:** Qwen3-VL (vision-language) · ควอนไทซ์ GGUF **Q4_K_M** (~3.4 GB)
- **การเทรน:** QLoRA fine-tune (r=64, alpha=128, bf16) 3 รอบ SFT + repair (PhaseA 465 steps, repair_r2 157, repair_r3 162) บนข้อมูลสอนภาษาไทย + **GBNF zero-Han grammar** ตัดอักษรจีนรั่วได้ 100%
- **Zero-Han:** ✅ 250/250 บันทึกทดสอบ = 0 อักษรจีน
- **ดาวน์โหลดโมเดลจาก Hugging Face:** [siamcafe/bomai-r75-highiq-safety](https://huggingface.co/siamcafe/bomai-r75-highiq-safety)

```bash
ollama pull siamcafe/bomai-r75-highiq-safety:v1
ollama run siamcafe/bomai-r75-highiq-safety:v1
```

## 📖 คู่มือการใช้งาน

- คู่มือฉบับเต็มภาษาไทย: [README.th.md](README.th.md) · [siamcafebook.com/bomai/manual](https://siamcafebook.com/bomai/manual/)
- คำถามที่พบบ่อย วิธีถอนการติดตั้ง และเทคนิคการใช้งาน อยู่ในคู่มือ

## 🗒️ บันทึกการอัปเดต

### v2.0.0 (2026-11-02)
- 🚀 **Fleet Sync Update** — ซิงก์โครงสร้างพื้นฐานกับ BOM LLM v10.0.0
- ⬆️ BOM LLM fleet อัปเกรด Open WebUI v0.12.5
- ✅ GOD CONFIG v7.0 ตรวจสอบผ่าน (40 IRON rules)
- ✅ Fleet 9/9 ผ่านการตรวจสอบ, Pipeline E2E PASS
- 🖼️ อัปเดต Hero banner ใหม่

### v0.3.2 (2026-10-30)
- 🎯 **Official Release** — เลื่อนจาก v0.3.1-rc.1 เป็น stable v0.3.2
- ✅ ผ่าน Ship Gates ทั้ง 6 ด่าน — Vision, Identity, Zero-Han (250/250=0), Thai≥9.0, Refusal, Regression
- 🔒 **Zero-Han Solution** — GBNF grammar allowlist ตัดการรั่วของอักษร CJK ทั้งหมด
- 👁️ Vision (VL) ยืนยันการใช้งานจริง — Qwen3.5-4B multimodal
- ⚙️ **GOD CONFIG v7.0** — พารามิเตอร์ระดับโปรดักชันล็อกแล้ว ใช้ทั่วทั้ง fleet

### v0.3.1-rc.1 (2026-10-28)
- Release candidate แรกของสายโมเดล Thai VL

## 🤝 ร่วมพัฒนา

ยินดีทุกการมีส่วนร่วม:
- ปรับ BOM AI ไปใช้กับภาษา/ประเทศอื่น — แพตเทิร์นนี้ขยายได้
- ชุดข้อมูลสอนภาษาไทย (Thai instruction datasets) เพื่อเทรนโมเดลรุ่นถัดไป
- ปรับปรุงตัวติดตั้ง (Windows / macOS / Linux)

## 🙏 เครดิต

พัฒนาโดย [iCafeFX](https://icafefx.ai) · [SiamCafe](https://siamcafe.net)

- [Ollama](https://ollama.com) — ตัวรันโมเดล
- [Open WebUI](https://openwebui.com) — หน้าจอสนทนา
- [DavidAU](https://huggingface.co/DavidAU) — สถาปัตยกรรม base model
- Free code signing โดย [SignPath.io](https://signpath.io), certificate by SignPath Foundation

## 📜 ลิขสิทธิ์

- โค้ดใน repo นี้: **MIT** — ดู [LICENSE](LICENSE)
- น้ำหนักโมเดล: **Apache 2.0** · Open WebUI: BSD-3-Clause

---

<p align="center"><b>แจกฟรี สำหรับมนุษยชาติ 🇹🇭</b><br>
ถ้าโปรเจกต์นี้มีประโยชน์กับคุณ กด ⭐ Star ไว้หน่อยก็ดีใจมาก<br>
BOM AI · Heal the World · bomai.app</p>

## Model Tiers (v2.0.0)

| Tier | Model | Hardware | Download | Status |
|------|-------|----------|----------|--------|
| **Light** | DavidAU Qwen 4B (Q4_K_M) | 8 GB RAM (16 GB rec.), CPU-only OK | ~3.4 GB | available |
| **Pro** | 12B (Q4_K_M, gemma3) | GPU 12 GB+ VRAM (16 GB rec.) + 16 GB RAM | ~7.9 GB | available |
| **Production** | 709-L 27B | Mac + MLX | ~21 GB | deferred - not public yet |

- Windows installer: `https://bomai.app/dl/Install-BOM-AI-Online.bat` - asks for the tier, detects GPU/VRAM via nvidia-smi, recommends Light or Pro
- Ollama registry: `siamcafe/bom-ai:light-v2.0.0` and `siamcafe/bom-ai:pro-v2.0.0` (`latest` stays Light)
- Both tiers share the identical locked GOD CONFIG (7 parameters + Thai system prompt); only the base model differs
