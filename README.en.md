# BOM AI

![BOM AI](docs/images/banner.png)

> Free, offline AI assistant for Thailand. One-click install. No cloud, no account, no telemetry.

[bomai.app](https://bomai.app) · [Download](https://bomai.app/download) · [ภาษาไทย](README.th.md)

[![Download](https://img.shields.io/badge/download-bomai.app-blue)](https://bomai.app/download) [![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE) ![Version](https://img.shields.io/badge/version-v2.1.7-orange)

## What is BOM AI?

- One-click installer: bundles [Ollama](https://ollama.com) + [Open WebUI](https://openwebui.com) + curated Thai VL (vision-language) models
- Runs 100% offline after install
- Free forever: no signup, no ads, no message limits, no data collection
- Reads Thai text in images: receipts, slips, signs, documents, screenshots
- "Heal the World" mission: free AI education for Thai communities — classes for schools and institutions, no charge

Most AI in Thailand is cloud-only and English-first. Rural and older users on old
hardware and metered connections get locked out. We wanted an AI that just works
on an 8 GB office PC with the internet unplugged.

## Model Tiers

| Tier | Model | Requirements | Download | Capabilities |
|------|-------|--------------|----------|--------------|
| Light | Qwen3.5 4B VL (Q4_K_M) | 8 GB RAM, runs on CPU | ~3.4 GB | Thai chat, image reading, Q&A, short translation |
| Pro | GLM-4.7 12B Q4_K_M | GPU with 12 GB+ VRAM | ~7.9 GB | Everything Light + long documents, translation, highest quality |

The installer detects your RAM + VRAM and recommends the right tier automatically.
You can always override the choice.

## Quick Start

Download from [bomai.app/download](https://bomai.app/download) or the
[GitHub release v2.1.7](https://github.com/siamcafe/bomai/releases/tag/v2.1.7):

### Windows (PowerShell)

```powershell
# Online installer, 2.2 MB (SHA-256: 6c1f9a77) — fetches components when run
Invoke-WebRequest -Uri "https://github.com/siamcafe/bomai/releases/download/v2.1.7/Install-BOM-AI-Online.bat" -OutFile "Install-BOM-AI-Online.bat"
.\Install-BOM-AI-Online.bat
```

### Linux

```bash
# 1.3 MB (SHA-256: 50009487)
curl -fsSL -o install-bom-ai-linux.sh https://github.com/siamcafe/bomai/releases/download/v2.1.7/install-bom-ai-linux.sh
bash install-bom-ai-linux.sh
```

### macOS

```bash
# 1 MB (SHA-256: 830057b4)
curl -fsSL -o install-bom-ai-mac.zip https://github.com/siamcafe/bomai/releases/download/v2.1.7/install-bom-ai-mac.zip
unzip install-bom-ai-mac.zip && bash install-bom-ai.command
```

Then run the installer — it detects your hardware and picks the right model —
and click the **BOM AI** icon: a chat window opens in your browser, in Thai.

Everything binds to `127.0.0.1` only (UI on port 8080, AI gateway on port 11435).
Nothing listens on the network.

## System Requirements

- Windows 10 (1903)+, macOS 12+, or Ubuntu 22.04+
- Minimum 8 GB RAM (Light tier, CPU); GPU with 12 GB+ VRAM for the Pro tier
- ~10 GB free disk space
- No internet needed after install

## How It Works

- **VL models**: curated Thai-capable vision-language models served by
  [Ollama](https://ollama.com). The current Light model (v2.1.7) uses the
  untouched official Qwen3.5-4B weights (`siamcafe/bom-ai:light-v2.1.7`)
- **Vision**: the models read Thai text inside images — receipts, signs,
  screenshots, charts
- **Hardware detection**: the installer probes RAM + VRAM and maps it to
  a model tier before anything downloads
- **Stack**: [Ollama](https://ollama.com) (model serving) + [Open WebUI](https://openwebui.com)
  (chat interface, BSD-3-Clause) + our installer scripts and configs (this repo)

## FAQ

**Is it really free?**
Yes — 100%. No subscription, no ads, no data selling, no credit card, no usage
cap. BOM AI is a free project so every Thai user can have a personal AI.

**Is it safe?**
Everything runs on your own computer. Chats, images, and files never leave the
machine, and there is no account to breach. Windows SmartScreen may warn because
the binary is new — the download page lists SHA-256 hashes so you can verify
what you downloaded.

**Does it need internet?**
Only for the initial download and install. After that, BOM AI works fully offline.

**Does it run on old computers?**
Yes. Any Windows/macOS/Linux machine with 8 GB RAM runs the Light model on CPU;
a GPU with 12 GB+ VRAM unlocks the Pro model.

**Can I use it on mobile?**
Not in this version — BOM AI is designed for desktop computers.

**How is it different from ChatGPT?**
ChatGPT runs on a company's servers and needs an account plus constant internet.
BOM AI runs on your own machine: no signup, works offline, free and unlimited,
and your data never leaves the computer. The trade-off: smaller models that are
not GPT-4 level — but enough for everyday Thai work, and far more private.

**Where does my data go?**
Nowhere. All chats and images are stored only on your computer, and you can
delete them at any time.

## Release Notes

### v2.1.7 (2026-11-13)

- **New Light model** — the untouched official Qwen3.5-4B weights
  (`siamcafe/bom-ai:light-v2.1.7`), which read chart and screenshot images
  clearly better than the previous Light model
- **Streaming fix** — if the model slips into Chinese characters while
  streaming, the BOM AI gateway continues the answer from its last clean
  sentence instead of cutting it
- **Known trade-offs** — answers are slower on CPU-only PCs and the model
  refuses a few more questions; existing installs download the new model once
  (about 3.4 GB)
- Installers: Windows ~2.2 MB (`6c1f9a77`) · Linux ~1.3 MB (`50009487`) ·
  macOS ~1 MB (`830057b4`)

### v0.3.2 (2026-10-30)

- 🎯 **Official Release** — Promoted from v0.3.1-rc.1 to stable v0.3.2
- ✅ **All 6 Ship Gates PASSED** — Vision, Identity, Zero-Han (250/250=0), Thai≥9.0, Refusal, Regression
- 🔒 **Zero-Han Solution** — GBNF grammar allowlist eliminates all CJK character leakage
- 👁️ **Vision (VL) Verified** — Qwen3.5-4B multimodal inference confirmed working
- 🤖 **Identity Correct** — Model responds as "BOM" with proper Thai identity
- ⚙️ **GOD CONFIG v7.0** — Production inference parameters locked and deployed fleet-wide
- 🧹 **Fleet Optimization** — 210 GiB disk reclaimed, 10 orphan models removed, 15 Docker images pruned
- 🖼️ **ComfyUI Fleet v0.43.0** — All 7 instances upgraded and verified

Model details: base `DavidAU/Qwen3.5-4B-Claude-4.6-HighIQ-THINKING`, Q4_K_M GGUF
(~3.4 GB), Qwen3-VL architecture, 3 rounds SFT + repair (PhaseA 465 steps,
repair_r2 157, repair_r3 162). Model weights: Apache 2.0 · Code in this repo: MIT.

### v0.3.1-rc.1 (2026-10-28)

- First release candidate of the Thai VL model line.

## Contributing

We'd love help with:

- Adapting BOM AI for other languages/regions — the pattern generalizes
- Thai instruction datasets for model training
- Installer improvements (Windows / macOS / Linux)

## Credits

Built by [iCafeFX](https://icafefx.ai) · [SiamCafe](https://siamcafe.net) ·
Powered by [Ollama](https://ollama.com) and [Open WebUI](https://openwebui.com)

## License

MIT — see [LICENSE](LICENSE). Open WebUI keeps its own BSD-3-Clause license;
model base licenses apply to their respective weights.

Free code signing provided by SignPath.io, certificate by SignPath Foundation
