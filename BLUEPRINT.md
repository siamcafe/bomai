# BOM AI Blueprint (v3.0.0, 2026-11-04)

Architecture notes for BOM AI on the BOM LLM fleet. Source: GOD BLUEPRINT v5.2
(github.com/siamcafe/bomllm BLUEPRINT.md, C2 performance Phase P).

## Shared Open WebUI instance

BOM AI and BOM LLM are two surfaces of ONE Open WebUI instance on C2
(`webui.siam2r.com`): BOM AI has its own banner, custom buttons and branding
(`/static/bomai/*` assets, `xm-banners.js`, `branding.js`, `bom-ai-theme.css`).
Every UI change or OWUI upgrade affects BOTH surfaces — visual QC must cover both.

- Open WebUI: v0.13.0 (alembic e42c8f710a36), 18 functions, shared database
- LiteLLM: v1.106.4 pinned (v1.107.0 supply-chain compromise blocked)
- Ollama: 0.40.14 (Mac mini + UA servers)
- Public HTTPS: Cloudflare Tunnel -> C2 -> Tailscale -> home fleet

## GOD CONFIG locked parameters (v9.0, unchanged)

| Parameter | Value |
|---|---|
| temperature | 0.6 |
| top_p | 0.95 |
| top_k | 20 |
| repeat_penalty | 1.0 |
| presence_penalty | 0.0 (values > 0 cause Han character leakage) |
| num_predict | 4096 |
| num_ctx | 8192 |

Verified live 2026-11-04: C2 `bom-thai-chat` model params and UA `bomai-safe`
modelfile both expose all seven locked values.

## Tailscale dependency note (from GOD BLUEPRINT v5.2 §O.3)

C2 has no LAN route to the home fleet — every inference path for the shared
instance rides Tailscale 100.x: Mac primary generation (15x LiteLLM api_base),
qdrant relay :6333, rag-lb relay :7998, hub/docs/overlay ingress. `tailscaled`
on C2 is load-bearing; stopping it = public outage of the chat service. SSH
brute-force subnets are blocked at boot by `c2-ssh-guard` (NEVER-BLOCK list
enforced; see bomllm HOWTO v4.2 §3.13).

## Static assets

- Serving path: `/static/bomai/*` from the OWUI container STATIC_DIR
  (`/app/backend/open_webui/static/bomai/`); masters kept in the brand dir
  `bomai_static_v1` on C2
- `hero_banner_v11.png` / `hero_banner_v10.png` (1024x512) served 200 since v3.0.0
- C2 performance numbers (external TTFB median 0.093 s, SSH connect < 1.2 s,
  stress suite) are recorded in the BOM LLM v11.0.0 release
