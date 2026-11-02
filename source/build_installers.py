#!/usr/bin/env python3
"""Regenerate self-contained installers after changing any runtime source file."""
from pathlib import Path
import base64
import hashlib
import io
import zipfile

ROOT = Path(__file__).resolve().parent
RUNTIME = ("bom_runtime.py", "models.json", "seed_owui.py", "audit_owui.py", "install_unix.py")

SHELL = '''#!/bin/bash
# BOM AI 2.0.0; generated from build_installers.py.
set -euo pipefail
export PATH="/opt/homebrew/bin:/usr/local/bin:$HOME/.local/bin:$PATH"
if [[ "$(uname -s)" != "__OS__" ]]; then echo "This installer requires __OS__."; exit 2; fi
TMP_BOMAI="$(mktemp -d "${TMPDIR:-/tmp}/bomai-bootstrap.XXXXXX")"
trap 'rm -rf -- "$TMP_BOMAI"' EXIT
PY_BOMAI="${BOMAI_PYTHON:-}"
if [[ -z "$PY_BOMAI" ]]; then
  for candidate in python3.12 python3.11 python3; do
    if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys; assert sys.version_info[:2] in ((3,11),(3,12))' 2>/dev/null; then
      PY_BOMAI="$(command -v "$candidate")"; break
    fi
  done
fi
if [[ -z "$PY_BOMAI" ]] && command -v uv >/dev/null 2>&1; then
  PY_BOMAI="$(uv python find 3.12 2>/dev/null || true)"
fi
if [[ -z "$PY_BOMAI" ]]; then
  # Pinned uv installer obtains Python in the user's account; no Homebrew/sudo prerequisite.
  curl --fail --location --proto '=https' --connect-timeout 30 --retry 2 https://astral.sh/uv/0.9.7/install.sh -o "$TMP_BOMAI/uv.sh"
  if command -v sha256sum >/dev/null; then ACTUAL="$(sha256sum "$TMP_BOMAI/uv.sh" | cut -d' ' -f1)"; else ACTUAL="$(shasum -a 256 "$TMP_BOMAI/uv.sh" | cut -d' ' -f1)"; fi
  [[ "$ACTUAL" == "ef72d0c2b8f2d2a0d7c6b2d866339869a3f0cbd31e8f1b6901f2064c16d47b58" ]] || { echo "uv installer checksum mismatch"; exit 3; }
  UV_UNMANAGED_INSTALL="$TMP_BOMAI/uv-bin" sh "$TMP_BOMAI/uv.sh"
  "$TMP_BOMAI/uv-bin/uv" python install 3.12
  PY_BOMAI="$("$TMP_BOMAI/uv-bin/uv" python find 3.12)"
fi
"$PY_BOMAI" - "$TMP_BOMAI" <<'BOMAI_PAYLOAD'
import base64,io,sys,zipfile
data=base64.b64decode("__PAYLOAD__")
with zipfile.ZipFile(io.BytesIO(data)) as z:
    z.extractall(sys.argv[1])
BOMAI_PAYLOAD
"$PY_BOMAI" "$TMP_BOMAI/runtime/install_unix.py" "$@"
'''

def main():
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w", zipfile.ZIP_DEFLATED) as z:
        for name in RUNTIME:
            z.write(ROOT / "runtime" / name, "runtime/" + name)
    payload = base64.b64encode(data.getvalue()).decode()
    for folder, filename, system in (("macos", "install-bom-ai-mac.command", "Darwin"), ("linux", "install-bom-ai-linux.sh", "Linux")):
        dest = ROOT / folder / filename
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(SHELL.replace("__OS__", system).replace("__PAYLOAD__", payload), encoding="utf-8", newline="\n")
        dest.chmod(0o755)
    target = ROOT / "macos/install-bom-ai-mac.zip"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
        info = zipfile.ZipInfo("install-bom-ai-mac.command")
        info.create_system = 3
        info.external_attr = 0o100755 << 16
        z.writestr(info, (ROOT / "macos/install-bom-ai-mac.command").read_bytes())
    template = (ROOT / "windows/installer.template.bat").read_text(encoding="utf-8")
    for tag, filename in (("RUNTIME", "bom_runtime.py"), ("CATALOG", "models.json"), ("SEED", "seed_owui.py"), ("AUDIT", "audit_owui.py")):
        raw = (ROOT / "runtime" / filename).read_bytes()
        template = template.replace("__EMBED_" + tag + "_B64__", base64.b64encode(raw).decode())
        template = template.replace("__" + tag + "_SHA__", hashlib.sha256(raw).hexdigest().upper())
    (ROOT / "windows/Install-BOM-AI-Online.bat").write_text(template, encoding="utf-8", newline="\r\n")
    print("Generated Windows BAT, Linux SH, macOS COMMAND and executable-mode ZIP")

if __name__ == "__main__":
    main()
