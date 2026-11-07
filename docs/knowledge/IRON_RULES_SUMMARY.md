# BOM AI — iron rules and lessons

Condensed from the HF-1.0 blueprint (art#56535), the v2.0.4 blueprint (art#57376), the v2.0.4 QC report (art#57414), and the knowledge-backup scope. Sampling pins below are the LOCKED lines in art#56535 section 7.

## Locked product config

- Persona and sampling stay on the v9.1 installer canonical set: temperature 0.6, top_p 0.95, top_k 20, repeat_penalty 1.0, presence_penalty 0.0, num_ctx 8192, num_predict 4096, upstream think=false.
- Model alias, weights, quantization, runner, and context/queue limits stay locked. Quality rewrite budget stays 1. No new global retry loop.
- v9.1 is the installer persona. It does not replace fleet GOD CONFIG v9.0 (art#55651) or bom-llm.
- Shipping pins called out for this backup: base model SHA prefix 9c9c186…25, bom_runtime.py SHA prefix f19c4193, llama-server b3fa699, LiteLLM v1.106.4.
- The v2.0.4 installer work does not modify GOD CONFIG, bom_runtime.py, Han Fix policy, boundary, guard, or install_hf1. QC recorded those files untouched.

## Han Fix and QC

- Do not edit a test, widen a keyword, or delete a fixture to turn a FAIL into a PASS.
- Report UNTESTED or BLOCKED as itself. Blocked, fallback, and incomplete answers are not successes.
- Refusal uses the rubric, unsafe controls, and a human reviewer. An agent does not close its own safety FAIL.
- A document, spec, or prior report is not approval to deploy, restart, or change a locked live config. That approval has to be in the live chat for that step.
- Keep gateway and Open WebUI keys in the process environment only. Do not write them into scripts, command logs, or reports.

## Install, reinstall, uninstall (v2.0.4)

- User data is opt-in to delete: webui.db, chats, uploads, .webui_secret_key, first-login.json, and the shared Ollama model store.
- Never kill a process from a pid file alone. Own a process only when its executable path or command line is under the install root.
- Never kill a foreign listener. If a managed port is held by something else, abort the uninstall.
- Carry gateway_key across reinstall. Do not rotate it as a side effect of a new release directory.
- Tailscale, a pre-existing Ollama the user installed, and foreign models stay. Ollama itself is removable only when BOM AI installed it and the opt-in is set.
- One mutex name, `Local\BOM-AI-Installer`, with no version suffix, so install and uninstall cannot run together.

## Backup scope

- Knowledge only: blueprints, configs, how-to, specs, QC, and context.
- Do not copy user databases, chats, or uploads.
- Do not copy live tokens or passwords. This backup redacts them before GitHub and NAS.
- Do not modify production files, sshd, or C1. This job is read and copy.
