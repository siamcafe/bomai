# BOMAI v2.0.3 critical backup

Date: 2026-11-06
Git tag: v2.0.3-backup
Scope: configs, Open WebUI database, shipping gateway source, GOD blueprints, and v2.0.3 docs.
Excluded: model weights, chat history, API keys, passwords, and tokens.

## Sources
- Windows live install `D:\BOMAI` on this PC (DESKTOP-PE1B0VH, 192.168.1.22). `install.json` release is 2.0.3. The release folder is `releases\2.0.2\b20261106042726`.
- ubuntu-ai 192.168.1.248, mac 192.168.1.254, CAT, hub artifacts, and the `siamcafe/bomai` tag `v2.0.3`.
- SSH account note: spec usernames `bom` on i9 and NAS did not accept a key. Probes used the configured identities (i9 user `bomi9`, NAS user `siamcafe`, CAT per `probes.json`).

## Redaction
- `runtime.json` `gateway_key` and `install.json` `resumeKey` are `REDACTED`.
- `webui.db` password, session stamp, and non-empty API-key settings are `REDACTED`. Chat tables were emptied (they were already empty) and the file was rebuilt so old pages are gone.
- Collected text was scrubbed for those secrets, bearer tokens, `sk-` / GitHub token shapes, and private keys.

## Gateway
- Live `bom_runtime.py` sha256 `f19c4193ec2f0a54bd8cecd75b711973a3322dee17e5a1ebad36117854f299b7` (133774 bytes) is `gateway/bom_runtime.py`.
- The on-disk `.bak_p8` sha256 is `054ed6b1fec1d94b80eebadd9200e08afc452ae74c75346ba977dce856c3e0a3`. That is the older survey hash. It is not the file this backup stored.

## Database
- Source `webui.db` was under 50MB and had 0 chat rows. Backup copy is 786432 bytes after redaction and vacuum.

## Collection notes
- `install-root.txt` is not on the live `D:\BOMAI\state` tree.
- Ubuntu `bomai-owui`, `bomai-searxng`, `bomai-gateway`, and `bomai-ollama` are user systemd units. `systemctl cat` without `--user` reported no system unit. The files here are `systemctl --user cat`.
- Ubuntu system `ollama.service` and `ollama.service.d/restart-limit.conf` are included. LiteLLM env values for keys, passwords, and the database URL are `REDACTED`.
- Mac `~/.ollama/config.json` was not present.
- CAT files were read with the configured SSH host because key login as `siamcar` was refused.
- Open WebUI chat tables were empty. `auth` password and session stamp are `REDACTED`. `openai.api_keys` is `REDACTED`. `automations.auth_token_expires_in` remains the duration setting `1h`.
