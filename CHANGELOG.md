# Changelog

All notable changes to BOM AI are documented here.
For the full release history see [GitHub Releases](https://github.com/siamcafe/bomai/releases).

## [2.1.9] — 2026-11-24

**Five user-reported fixes**

### Fixed

- **แชทยาวที่มีรูปตอบต่อได้** — เมื่อบทสนทนายาวเกินที่โมเดลอ่านได้ในครั้งเดียว gateway จะเว้นข้อความเก่าที่สุดของแชทนั้น
  แล้วตอบต่อ แทนการตอบด้วยข้อความแจ้งความจุทุกครั้ง (Light และ Pro)
- **num_ctx ในหน้าตั้งค่า Advanced มีผล** — Light ถึง 16384, Pro ถึง 32768, ค่าเริ่มต้น 8192
- **ส่งรูปพร้อมค้นเว็บ** — ส่งคำสั่งระบบให้โมเดลชุดเดียวเสมอ (เดิมบน Windows ส่งสองชุด)
- **คำตอบที่ตั้งใจให้ซ้ำไม่ถูกตัด** — ท่อนฮุคของเพลง บรรทัดเดียวกันคนละหัวข้อ และการขอให้พิมพ์ซ้ำตามจำนวนครั้ง
- **อักษรจีนและญี่ปุ่นเมื่อผู้ใช้ขอ** — คำแปล คำถามเรื่องคำภาษาจีน/ญี่ปุ่น และอักษรจีนในบล็อกโค้ด แสดงผลได้
- **ติดตั้งใหม่บน Linux / macOS จบได้** — ขั้นตรวจสอบสุดท้ายใช้ไอคอนที่มากับตัวติดตั้ง (เดิมหา cache/favicon.png ที่ไม่มีแล้ว)
- **ข้อความแจ้งความจุใหม่** — ขึ้นเฉพาะเมื่อข้อความหรือรูปเดียวใหญ่เกินไป และบอกวิธีแก้

### Added

- **แท็ก Ollama ใหม่** — `siamcafe/bom-ai:light-v2.1.9` ·
  `siamcafe/bom-ai:pro-v2.1.9` (น้ำหนักโมเดลเดิมจาก v2.1.8)

### Unchanged

- default system prompt · sampling · default context size · Open WebUI · SearXNG · model weights

### Installer SHA-256

| File | OS | Size | SHA-256 |
|---|---|---|---|
| `Install-BOM-AI-Online.bat` | Windows | 2,405,335 B | `48ec7c4be6e69eab28933a8439421e59a28622e7c8ed3e80e42bf8510ad98d4a` |
| `install-bom-ai-linux.sh` | Linux | 1,343,772 B | `7ccf639f9c046813e311b8e3d1fb32b54059e8d8881badc414918134f31c41fd` |
| `install-bom-ai-mac.zip` | macOS | 1,013,096 B | `1e25d40ba3d9ae86ba49c3db04e0dd646d34ca8ce985dbf98091544646e6ca40` |

## [2.1.8] — 2026-11-14

**Web Search Default OFF + Pro GGUF on every platform + Stream Resume rc3**

### Changed

- **Web Search ปิดเป็นค่าเริ่มต้น (default OFF)** — แก้ครบ 3 ชั้น: model preset, admin
  default interface (`webSearch: null`), และ builtin tools (`web_search: false`)
  คำตอบ identity ไม่ถูกแทนที่ด้วย web disclaimer อีกต่อไป — ผู้ใช้เปิดใช้เองได้
  (`capabilities.web_search` ยังคงเปิดให้ผู้ใช้เลือก)

- **Pro tier = GGUF Q4_K_M ทุกแพลตฟอร์ม** — 709-L 27B DavidAU Cold Fusion
  (Qwen3.8 base): text 16.5 GB (SHA-256 `5c45be04`) + mmproj 518 MB
  (SHA-256 `d6bb4695`) รันได้ทั้ง Windows / macOS / Linux
  (เดิม v2.1.7 Pro เป็น MLX บน Apple Silicon เท่านั้น)

### Added

- **Stream Resume (gateway rc3)** — ข้อความที่ถูกตัดกลางคำจะถูกต่ออัตโนมัติ
  สูงสุด 3 รอบ (`MAX_STREAM_RESUMES=3`) อัตราตัดกลางคำที่วัดได้จริง **0/272**
  (ลดจาก 13.97% ใน v2.1.6)
- **แท็ก Ollama ใหม่** — `siamcafe/bom-ai:light-v2.1.8` ·
  `siamcafe/bom-ai:pro-v2.1.8` (น้ำหนักโมเดลเดิมจาก v2.1.7)

### Unchanged

- **GOD CONFIG v9.1** — temp 0.6 · top_p 0.95 · top_k 20 · repeat_penalty 1.0 ·
  num_ctx 8192 · num_predict 4096 · think false (ค่าล็อกเดิมทุกตัว)
- Model weights Light (Qwen3.5-4B VL Q4_K_M ~3.4 GB)

### Installer SHA-256

| File | OS | Size | SHA-256 |
|---|---|---|---|
| `Install-BOM-AI-Online.bat` | Windows | 2,359,590 B | `2a2e864ca2c302b655f47c94f1b7fbba6a6627dfebf4e4c5cec224852c3a7729` |
| `install-bom-ai-linux.sh` | Linux | 1,328,272 B | `eef9fc3c42dc2529e1b3d3096e7542059c58c55c4f8aeb06b9fd55d6f9b6cc9b` |
| `install-bom-ai-mac.zip` | macOS | 1,001,301 B | `a1c6d4d4ce2c3e186660e8d13e4dbdf6cbdfed2564ce594aec0662941ce02c97` |

## [2.1.7] — 2026-11-13

- New Light model — untouched official Qwen3.5-4B weights (`light-v2.1.7`),
  clearly better chart/screenshot reading
- Streaming fix — gateway continues from the last clean sentence when Chinese
  characters slip in mid-stream
- Installers: Windows `6c1f9a77` · Linux `50009487` · macOS `830057b4`

## [2.0.8] — 2026-11-08

- Shared infrastructure update with BOM LLM v17: Open WebUI v0.13.2,
  LiteLLM v1.108.3 LTS, Valkey 9.1.3 (heap-overflow fix), Contabo C2
  live-migration (disk latency 133ms → 4ms)
- BOM AI itself and GOD CONFIG parameters unchanged

## [2.0.3] — 2026-11-06

- Han Fix 3-Layer enforcement (HF-1.0) — 0 Han leaks across 550+ test prompts
  (500 API + 50 browser), 10/10 think probes, refusal adjudication 53 cases
  0 UNSAFE 0 UNCERTAIN
- GOD CONFIG v9.1 sampling lock; installer chain SHA-256 match across
  CDN + GitHub + Hugging Face; QC T01–T20 ALL PASS on Windows / Linux / macOS

## [0.3.2] — 2026-10-30

- First official stable release — all 6 ship gates passed (Vision, Identity,
  Zero-Han 250/250, Thai ≥ 9.0, Refusal, Regression)
- GBNF grammar allowlist eliminates CJK leakage; Qwen3.5-4B VL multimodal
  inference verified
