# BOM AI — Installation Guide / คู่มือติดตั้ง

Download: [bomai.app/download](https://bomai.app/download) ·
Main doc: [README](../README.md) · [ภาษาไทย](../README.th.md)

> Installers are **unsigned** — Windows SmartScreen / macOS Gatekeeper may warn.
> Verify the SHA-256 of every file on the download page or in `/dl/release.json`.
> Installation downloads components from the internet (~3 GB+ for Light).

---

## Windows

1. Download `Install-BOM-AI-Online.bat` (~0.3 MB) from [bomai.app/download](https://bomai.app/download)
2. Double-click the file — the installer downloads required components (~3 GB+)
3. Pick a tier when asked (Light 4.2B for most PCs / Pro 11.8B for GPU machines)
4. If SmartScreen warns: "More info" → "Run anyway"

## วิธีติดตั้งบน Windows

1. ดาวน์โหลด `Install-BOM-AI-Online.bat` จาก [bomai.app/download](https://bomai.app/download)
2. ดับเบิลคลิกไฟล์ — ตัวติดตั้งจะดึงส่วนประกอบที่จำเป็นเอง (~3 GB+)
3. เลือกรุ่นโมเดล (Light 4.2B สำหรับเครื่องทั่วไป / Pro 11.8B สำหรับเครื่องมี GPU)
4. ถ้า SmartScreen เตือน: "ข้อมูลเพิ่มเติม" → "เรียกใช้ต่อไป"

## macOS

1. Download `install-bom-ai-mac.zip`
2. Unzip in Finder
3. Double-click `install-bom-ai-mac.command`
4. If Gatekeeper warns: right-click the file → Open

## Linux

```bash
curl --fail --location --proto '=https' -o install-bom-ai-linux.sh \
  https://bomai.app/dl/install-bom-ai-linux.sh
bash install-bom-ai-linux.sh
```

## Tiers

| Tier | Download | Requirement |
|---|---|---|
| Light 4.2B ⭐ | ~3.4 GB | 8 GB RAM |
| Pro 11.8B | ~7.9 GB | GPU 12 GB+ VRAM |

Production tier is deferred. Registry: `siamcafe/bom-ai:light-v2.0.0`, `siamcafe/bom-ai:pro-v2.0.0`.
