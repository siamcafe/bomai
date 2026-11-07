# HANDOFF — BOMAI Manual Full Rewrite (9 pages)
# From: Project BOMAI (QC + owner review)
# To: Project VDO (yt-tutorial-kit) + Project DOC (grav-siamcafebook)
# Date: 2026-11-06
# Priority: CRITICAL — manual misleads users on every OS

---

## Problem Summary

คู่มือ BOM AI ทั้ง 9 หน้าบน siamcafebook.com/bomai/manual
เขียนสำหรับ **v0.3.1-r2** (ยุคเก่า) ไม่ตรงกับ **v2.0.2** ที่ LIVE อยู่
ผู้ใช้ทำตามคู่มือจะงง/ทำไม่ได้/หาไฟล์ไม่เจอ

## Pages to Rewrite

### 1. /bomai/manual/windows — CRITICAL
URL: https://siamcafebook.com/bomai/manual/windows

WRONG (v0.3.1):
- "Download ZIP bomai-windows-installer-r2.zip (1.2GB)"
- "Extract ZIP, BAT + payload/ must sit side by side"
- "SHA of ZIP file"

CORRECT (v2.0.2):
- Download BAT directly: Install-BOM-AI-Online.bat (338KB)
- No ZIP for Windows, no payload/ folder
- BAT is online installer — downloads everything itself
- BAT SHA: 2d19bad72a85814e5d868a4c4eb042ea236aa36075fb024dba588757ee7b1288
- BAT size: 338,303 bytes
- Install location: %LOCALAPPDATA%\Programs\BOM-AI (not %LOCALAPPDATA%\BOMAI)
- OWUI: http://127.0.0.1:8080

### 2. /bomai/manual/macos — NEEDS UPDATE
URL: https://siamcafebook.com/bomai/manual/macos

Issues:
- No installer filename mentioned at all
- v2.0.2 uses install-bom-ai-mac.zip containing .command file
- ZIP SHA: c5c1273291a92a0675cbc90dddf32effa8fe821bc34a55be989adcf95b3da017
- Port says localhost:3000 — v2.0.2 uses 8080
- "Port 11435" mentioned — should be 11434
- No SHA verification steps
- Video clips M1.mp4, M2.mp4 may be outdated

### 3. /bomai/manual/linux — NEEDS UPDATE
URL: https://siamcafebook.com/bomai/manual/linux

Issues:
- No installer filename (v2.0.2 = install-bom-ai-linux.sh)
- SH SHA: 3ab24b69deeb827f5835a67728f1cfafaf1663bee02fd24bb318475f6a22c1ee
- No package format specified
- No SHA verification steps
- References "package's tools" without naming them

### 4. /bomai/manual/faq — NEEDS UPDATE
URL: https://siamcafebook.com/bomai/manual/faq

Issues:
- Version says v0.3.1-r2 — should be v2.0.2
- Subtitle: "แก้ปัญหาเองได้ ก่อนติดต่อทีมงาน" — ไม่มีทีมงาน (free software)
- Subtitle: "สวัสดีครับ · FAQ แก้ปัญหา BOM AI" — ดู bot-like
- Q3 specs: "30 GB" — verify for v2.0.2
- Q3: "ดาวน์โหลดรวม 5.1 GB" — verify for v2.0.2
- Q7: only mentions Safe + Light — v2.0.2 also has Pro tier
- Q9: install location %LOCALAPPDATA%\BOMAI — should be %LOCALAPPDATA%\Programs\BOM-AI
- Q18: "ติดต่อผ่านช่องทางที่ระบุ" — what channel? ไม่มี support team

### 5. /bomai/manual (หน้าแรก) — CHECK
URL: https://siamcafebook.com/bomai/manual

Issues:
- Likely references v0.3.1-r2
- Version number + download instructions probably stale

### 6. /bomai/manual/usage — NEEDS UPDATE
URL: https://siamcafebook.com/bomai/manual/usage

Issues:
- Version: v0.3.1-r2 — stale
- "model set 3.4 GB" — verify for v2.0.2
- Only mentions Safe + Light — missing Pro tier
- "Downloading other models is not supported" — verify for v2.0.2

### 7. /bomai/manual/models — NEEDS UPDATE
URL: https://siamcafebook.com/bomai/manual/models

Issues:
- Only lists Safe + Light — missing Pro tier (GLM-4.7 12B Q4_K_M GPU 12GB+)
- "3.4 GB" — verify
- No mention of GPU requirements for Pro

### 8. /bomai/manual/mobile — CHECK
URL: https://siamcafebook.com/bomai/manual/mobile
- Tailscale setup may be stale
- Port numbers may be wrong

### 9. /bomai/manual/apikey — CHECK
URL: https://siamcafebook.com/bomai/manual/apikey
- API key creation steps may differ in v2.0.2

## Correct v2.0.2 Reference

product: BOM AI v2.0.2
distribution:
  windows: Install-BOM-AI-Online.bat (338,303 bytes, online installer)
  macos: install-bom-ai-mac.zip (contains .command)
  linux: install-bom-ai-linux.sh
download_url: https://bomai.app/download
github: https://github.com/siamcafe/bomai/releases/tag/v2.0.0
huggingface: https://huggingface.co/siamcafe/bomai

sha256:
  bat: 2d19bad72a85814e5d868a4c4eb042ea236aa36075fb024dba588757ee7b1288
  sh: 3ab24b69deeb827f5835a67728f1cfafaf1663bee02fd24bb318475f6a22c1ee
  zip: c5c1273291a92a0675cbc90dddf32effa8fe821bc34a55be989adcf95b3da017

tiers:
  - name: BOM AI Safe
    model: Qwen 4.2B Q4_K_M
    req: CPU, RAM 8GB min
    note: default, safety system prompt
  - name: BOM AI Light
    model: Qwen 4.2B Q4_K_M
    req: CPU, RAM 8GB min
    note: standard, no extra system prompt
  - name: BOM AI Pro
    model: GLM-4.7 12B Q4_K_M
    req: GPU 12GB+ VRAM
    note: advanced tasks

ports:
  owui: 8080
  ollama: 11434
  searxng: 8888

install_location:
  windows: "%LOCALAPPDATA%\\Programs\\BOM-AI"

god_config: v9.0 (art#55651) — temp=0.6, top_p=0.95, top_k=20

## Scope for VDO Project

1. Rewrite all 9 manual pages on siamcafebook Grav CMS
2. Update all screenshots/videos to v2.0.2 UI
3. Fix FAQ subtitle (remove "ทีมงาน" reference)
4. Add Pro tier to models page
5. Fix all SHA/size/filename references
6. Fix port numbers (3000 -> 8080, 11435 -> 11434)
7. Fix install paths
8. Verify EN translation pages match TH
9. Record new how-to videos if M1.mp4/M2.mp4 are stale

## IRON Rules

- Grav CMS on CAT (122.155.168.7:99, user bom)
- IRON 37: SSH LOCK
- IRON 44: DNS FORBIDDEN
- BAN-branding-assets: NEVER modify han-monitor/xm-banners.js/bom-ai-theme.css
- Content changes only — no server/config changes

## Reference Artifacts

- art#56397: QC Live Full report (installer flow, ports, paths)
- art#56419: Stress test context (product specs)
- art#56457: Previous handoff (Windows-only, superseded by this)
- art#55651: GOD CONFIG v9.0
