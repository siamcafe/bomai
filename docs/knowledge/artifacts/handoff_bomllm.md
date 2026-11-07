# BOMAI v2.0.3 Handoff → Project BOMLLM

## From: Project BOMAI (Claude)
## To: Project BOMLLM
## Date: 2026-11-06
## Priority: MEDIUM

---

## Summary

BOM AI v2.0.3 (Han Fix HF-1.0) SHIPPED and VERIFIED.
GitHub repo siamcafe/bomai และ HuggingFace siamcafe/bomai ได้รับการ update แล้วบางส่วน แต่ยังมีงานที่ต้องทำฝั่ง bomllm:

## What Changed in v2.0.3

1. **Han Fix 3-Layer HF-1.0** — EgressEmitter gateway + OWUI Filter + prompt v9.1
2. **bom_runtime.py** — 565 lines → 2584 lines (shipping version sha256=f19c4193)
3. **GOD CONFIG v9.1** — anti-Han prompt + translation clarification
4. **Installer BAT** — sha256: 88428a59580e02ef0ee3d6f10db2253faadef877b2864cb2e18a0fcdd84f8faa (406263 bytes)
5. **GitHub release v2.0.3** — tagged as Latest, 4 assets uploaded
6. **HuggingFace** — README model card created (commit 0f049c13), files updated

## What BOMLLM Needs to Do

### 1. GitHub repo sync (if bomllm has related repos)
- siamcafe/bomai main branch updated: README v2.0.3, bom_runtime.py synced, backup/ folder added
- Tag v2.0.3-backup created (43 files, config+DB+blueprints)
- Old releases deleted: v0.3.1-rc.1, v4.0.0, v2.0.0
- Remaining releases: v2.0.3 (Latest) + v0.3.1 + v0.3.2 (kept, owner decision)

### 2. HuggingFace model card
- README.md created but may need bomllm branding/links update
- Current: basic v2.0.3 model card
- Needed: link to bomllm fleet docs if applicable

### 3. Version alignment across fleet
Atom survey (art#56602) found version differences:

| Host | Ollama | OWUI | LiteLLM |
|------|--------|------|---------|
| i9 (desktop) | 0.40.13 | 0.12.5 | N/A |
| ubuntu-ai | 0.40.14 | 0.12.4 | 1.106.5 |
| Mac Mini | 0.40.14 | 0.12.0 | N/A |
| C2 | N/A | 0.13.0 | 1.106.5 |

Decision needed: pin to which versions across fleet?
- LiteLLM pin was 1.106.4 but fleet runs 1.106.5
- Ollama desktop pins 0.40.13 but fleet has 0.40.14

### 4. bomllm release artifacts
- bomllm v11.0.0 + bomai v3.0.0 + HF v11 were released (art#55910/55911)
- Need to update if bomllm references bomai version

## Evidence / Artifacts

| Item | Hub Art# |
|------|----------|
| Ship report v2.0.3 | 56626 |
| Atom survey (53 findings) | 56602 |
| Atom fix report | 56648 |
| K3 GOD BLUEPRINT HF-1.0 | 56535 |
| Backup (43 files, GitHub tag) | 56740 |
| Street test browser QC | 56730 + 56796 |
| CSP fix report | 56807 |

## SHAs

| File | SHA256 |
|------|--------|
| BAT v2.0.3 | 88428a59580e02ef0ee3d6f10db2253faadef877b2864cb2e18a0fcdd84f8faa |
| SH v2.0.3 | d27178ce (prefix) |
| ZIP v2.0.3 | 70ff5dfa (prefix) |
| bom_runtime.py (shipping) | f19c4193ec2f0a54bd8cecd75b711973a3322dee17e5a1ebad36117854f299b7 |
| Git commit | cb37600 (installer), 0c89a05d (backup) |

## No Action Required From BOMLLM

- Han Fix is self-contained in BOMAI installer — no bomllm infra change needed
- C2 was READ-ONLY during all operations — zero changes to bomllm prod
- Mac gateway port 11435 untouched (Ollama bind fixed to loopback only)

## Contact

Questions → hub joblog project=bomai or project=bomllm
