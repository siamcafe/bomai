# BOM AI — Installation Guide / คู่มือติดตั้ง

Download: [bomai.app/download](https://bomai.app/download) ·
Main doc: [README](../README.md) · [ภาษาไทย](../README.th.md)

---

## Windows Installation

1. Download `BOM-AI-Setup.exe` from [bomai.app/download](https://bomai.app/download)
2. Run it → accept the agreement → choose the install drive (C: or D:)
3. The installer detects your RAM/VRAM and recommends a model tier (V4B / V8B / V12B)
4. Wait for the install + model download (internet needed once), then click the
   **BOM AI** desktop icon — the chat opens in your browser automatically

> If Windows SmartScreen warns, it is because the binary is new. The download
> page lists SHA-256 hashes so you can verify the file first.

## วิธีติดตั้งบน Windows

1. ดาวน์โหลด `BOM-AI-Setup.exe` จาก [bomai.app/download](https://bomai.app/download)
2. เปิดไฟล์ → ยอมรับข้อตกลง → เลือกไดรว์ที่ต้องการติดตั้ง (C: หรือ D:)
3. ตัวติดตั้งจะตรวจสอบ RAM/การ์ดจอของเครื่อง แล้วแนะนำโมเดลที่เหมาะสม
   (V4B / V8B / V12B) ให้อัตโนมัติ
4. รอติดตั้ง + ดาวน์โหลดโมเดล (ใช้เน็ตครั้งเดียว) แล้วกดไอคอน **BOM AI**
   บนเดสก์ท็อป — หน้าจอสนทนาจะเปิดขึ้นมาเอง

> ถ้า Windows SmartScreen ขึ้นเตือน เพราะโปรแกรมใหม่ยังไม่เป็นที่รู้จัก
> หน้าดาวน์โหลดแสดงค่า SHA-256 ไว้ให้ตรวจสอบไฟล์ก่อนได้

---

## macOS Installation

1. Download the `.command` file from [bomai.app/download](https://bomai.app/download)
2. Make it executable and run it (Terminal opens automatically on double-click;
   if blocked: right-click → Open):
   ```bash
   chmod +x bomai_launcher.command
   ./bomai_launcher.command
   ```
3. The script auto-detects your hardware → installs → opens the chat in your browser

## วิธีติดตั้งบน macOS

1. ดาวน์โหลดไฟล์ `.command` จาก [bomai.app/download](https://bomai.app/download)
2. เปิดใช้งานไฟล์ (ดับเบิลคลิกเพื่อเปิดผ่าน Terminal หากถูกบล็อก:
   คลิกขวา → เปิด):
   ```bash
   chmod +x bomai_launcher.command
   ./bomai_launcher.command
   ```
3. สคริปต์ตรวจสอบสเปกเครื่อง → ติดตั้ง → เปิดหน้าจอสนทนาในเบราว์เซอร์ให้เลย

---

## Linux Installation

1. Download the `.sh` installer from [bomai.app/download](https://bomai.app/download)
2. Make it executable and run it:
   ```bash
   chmod +x bomai_setup.sh
   ./bomai_setup.sh
   ```
3. The script detects your hardware (RAM, VRAM, GPU) and installs the matching tier

## วิธีติดตั้งบน Linux

1. ดาวน์โหลดตัวติดตั้ง `.sh` จาก [bomai.app/download](https://bomai.app/download)
2. เปิดสิทธิ์รันแล้วรันสคริปต์:
   ```bash
   chmod +x bomai_setup.sh
   ./bomai_setup.sh
   ```
3. สคริปต์จะตรวจสอบสเปกเครื่อง (RAM, VRAM, GPU) แล้วติดตั้งโมเดลที่เหมาะสม

---

## Troubleshooting / แก้ปัญหาที่พบบ่อย

**"Not enough RAM"** — you need at least 8 GB of RAM for the V4B tier.
Check with Task Manager (Windows) / About This Mac / `free -h` (Linux).

**"Model not loading"** — check that the Ollama service is running
(`ollama list` should respond). Restart the BOM AI launcher if needed.

**"Can't read images"** — make sure a VL model (V4B / V8B / V12B) is selected,
not a text-only model.

**"ไม่พบ RAM / Not enough RAM"** — ต้องมี RAM อย่างน้อย 8 GB สำหรับรุ่น V4B
เช็กได้จาก Task Manager (Windows) / About This Mac / `free -h` (Linux)

**"โมเดลไม่โหลด / Model not loading"** — ตรวจว่า Ollama กำลังทำงานอยู่
(พิมพ์ `ollama list` แล้วต้องตอบ) ถ้าไม่ตอบ ลองปิดแล้วเปิด BOM AI ใหม่

**"อ่านรูปไม่ได้ / Can't read images"** — ต้องเลือกโมเดลที่รองรับภาพ
(VL: V4B / V8B / V12B) ไม่ใช่โมเดลแบบข้อความอย่างเดียว

---

## Manual / developer route

The repo contains the building blocks, if you prefer doing it by hand:

- `installer/windows/hardware_detect.ps1`, `installer/macos/hardware_detect.sh`,
  `installer/linux/hardware_detect.sh` — hardware detection (prints JSON)
- `models/Modelfile_v4b|v8b|v12b` — Ollama Modelfiles for the three tiers
- `config/god_config.env` — Open WebUI deployment configuration
  (the installer injects a per-machine random secret at install time)

You will also need [Ollama](https://ollama.com) and
[Open WebUI](https://openwebui.com) installed locally.
