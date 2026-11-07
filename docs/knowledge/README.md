# BOM AI — Project Knowledge Backup
## v2.0.4 (7 Nov 2026)

### What is BOM AI?
Free 100% local AI installer for Thai users.
Ollama + Open WebUI + SearXNG + gateway bom_runtime.py
3 OS: Windows, macOS, Linux
2 tiers: Light (Qwen 4.2B CPU) + Pro (GLM-4.7 12B GPU)
"แจกฟรี สำหรับมนุษยชาติ" — Heal the World mission

### Architecture
User → OWUI :3000 (C2) → LiteLLM :4000 (C2) → LiteLLM :4100 (UA) → llm-smart :8380 (UA)
Gateway: bom_runtime.py enforces GOD CONFIG + Han Fix HF-1.0

### GOD CONFIG v9.1
temp=0.6, top_p=0.95, top_k=20, repeat_penalty=1.0, num_ctx=8192, num_predict=4096

### Version History
- v2.0.3 (6 Nov): Han Fix 3-Layer, 600+ prompts tested
- v2.0.4 (7 Nov): Reinstall/uninstall fix, 10+9 issues, QC 26/26 PASS

### Key Artifacts
- GOD BLUEPRINT HF-1.0: art#56535 (k3_god_blueprint_hf1.yaml)
- GOD BLUEPRINT v2.0.4: art#57376 (k3_god_blueprint_v204.yaml)
- Hub index: art#56940
- QC report: art#57414

### Fleet
- AM4 (.38): zcode agent + ComfyUI
- i9 (.20): QC + 2x RTX 5060 Ti
- Mac M4 Pro (.254): PROD gateway
- ubuntu-ai (.248): RTX 5080 + 5060 Ti
- CAT (122.155.168.7): bomai.app web
- C2 (109.123.233.171): PROD OWUI + LiteLLM

### LOCKED — Never Modify
- GOD CONFIG v9.1 + base model SHA 9c9c186...25
- bom_runtime.py SHA f19c4193
- llama-server b3fa699, LiteLLM v1.106.4
