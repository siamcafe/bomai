# BOM AI

![BOM AI](docs/images/banner.png)

> Free, offline AI assistant for Thailand. One-click install. No cloud, no account, no telemetry.

[bomai.app](https://bomai.app) · [Download](https://bomai.app/download) · [ภาษาไทย](README.th.md)

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

| Tier | RAM | Download | Capabilities |
|------|-----|----------|--------------|
| V4B | 8 GB | ~2.5 GB | Thai chat, image reading, Q&A, short translation |
| V8B | 16 GB | ~5 GB | Everything V4B + document translation, longer documents |
| V12B | 24 GB+ | ~7.3 GB | Full capability: charts, tables, complex vision tasks |

The installer detects your RAM + VRAM and recommends the right tier automatically.
You can always override the choice.

## Quick Start

1. Download from [bomai.app/download](https://bomai.app/download)
2. Run the installer — it detects your hardware and picks the right model
3. Click the **BOM AI** icon — a chat window opens in your browser, in Thai

Everything binds to `127.0.0.1` only (UI on port 8787, Ollama on port 11434).
Nothing listens on the network.

## System Requirements

- Windows 10 (1903)+, macOS 12+, or Ubuntu 22.04+
- Minimum 8 GB RAM (V4B); 16 GB recommended (V8B)
- ~10 GB free disk space
- No internet needed after install

## How It Works

- **VL models**: QLoRA fine-tunes (r64 / alpha 128, bf16) of open vision-language
  base models on Thai instruction data, exported to GGUF and served by Ollama
- **Vision**: the models read Thai text inside images — receipts, signs,
  screenshots, charts
- **Hardware detection**: a small per-OS script probes RAM + VRAM and maps it to
  a model tier before anything downloads (see `installer/`)
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
Yes. Any Windows/macOS/Linux machine with 8 GB RAM runs the V4B model; 16 GB
suits V8B; 24 GB+ gets V12B.

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
