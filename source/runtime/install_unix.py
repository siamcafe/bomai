#!/usr/bin/env python3
"""BOM AI macOS/Linux installer and owned-process launcher. Python 3.11/3.12.

An install is successful only after migrations, an offline seed, restart and
authenticated configuration verification. QC is deliberately isolated.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import plistlib
import re
import secrets
import shlex
import shutil
import signal
import socket
import subprocess
import sys
import tarfile
import time
import urllib.request
from urllib.parse import urlsplit
import webbrowser
import zipfile

VERSION = "2.0.0"
OWUI = "0.12.5"
SEARX_REV = "54ca1d9cfb08674f66261d7f351b063558dfcc62"
SEARX_SHA = "030e9e28e6cfa5083dd168771c60bbc109500f5b5f68653a0ebb0117f3364590"
OLLAMA_ASSETS = {
    "Darwin": ("ollama-darwin.tgz", "bae29252232b9e1358cf5801a7d65a07442af18fb5467cb68c7fc3711f59c511"),
    "Linux-x86_64": ("ollama-linux-amd64.tar.zst", "c9490e0f520be21271d969e6703f012268b1d39f8b70dd58854e5bfef7a75bb6"),
    "Linux-aarch64": ("ollama-linux-arm64.tar.zst", "913d9a28da6da86d551ce4ca531457767bb14d511cbc1d5ca93e9b3b8b9a8666"),
}
PARAMS = dict(temperature=0.6, top_p=0.95, top_k=20, repeat_penalty=1.0,
              presence_penalty=0.0, num_ctx=8192, num_predict=4096)
SYSTEM = "คุณคือ BOM AI (บอม เอไอ) ผู้ช่วย AI ภาษาไทย\nตอบเป็นภาษาไทยเสมอ ชัดเจน กระชับ เป็นมิตร\nถ้าถูกถามเรื่องราคาหุ้น ทอง หรือค่าเงิน ให้แนะนำค้นหาจากอินเทอร์เน็ตเพื่อข้อมูลล่าสุด"

def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.chmod(0o600)
    tmp.replace(path)

def request(url, data=None, token=None, timeout=30):
    headers = {"User-Agent": "BOM-AI-installer/" + VERSION}
    if data is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(data, ensure_ascii=False).encode()
    if token:
        headers["Authorization"] = "Bearer " + token
    with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=headers), timeout=timeout) as r:
        return json.load(r)

def run(args, **kwargs):
    print("[run]", " ".join(str(x) for x in args), flush=True)
    subprocess.run([str(x) for x in args], check=True, **kwargs)

def download(url, dest, sha=None):
    dest = Path(dest)
    if dest.exists() and sha and hashlib.sha256(dest.read_bytes()).hexdigest() == sha:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_suffix(dest.suffix + ".part")
    run(["curl", "--fail", "--location", "--proto", "=https", "--connect-timeout", "30", "--retry", "2", "--output", part, url])
    if sha and hashlib.sha256(part.read_bytes()).hexdigest() != sha:
        raise RuntimeError("Checksum mismatch: " + dest.name)
    part.replace(dest)
    return dest

def busy(port):
    with socket.socket() as s:
        s.settimeout(1)
        return s.connect_ex(("127.0.0.1", int(port))) == 0

def ready(url, seconds=300):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        try:
            with urllib.request.urlopen(url, timeout=3) as r:
                if r.status == 200:
                    return
        except Exception:
            time.sleep(2)
    raise RuntimeError("Readiness timeout: " + url)

def owned_pid(root, name):
    f = root / "state" / (name + ".pid")
    if not f.exists():
        return None
    pid = int(f.read_text())
    result = subprocess.run(["ps", "-p", str(pid), "-o", "command="], capture_output=True, text=True)
    cmd = result.stdout.strip()
    if not cmd:
        f.unlink(missing_ok=True)
        return None
    # PID reuse must never permit terminating an unrelated process.
    if str(root) not in cmd:
        raise RuntimeError("PID ownership mismatch for " + name)
    return pid

def stop(root, name, port):
    pid = owned_pid(root, name)
    if pid:
        os.kill(pid, signal.SIGTERM)
        for _ in range(90):
            process = subprocess.run(["ps", "-p", str(pid), "-o", "stat="], capture_output=True, text=True).stdout.strip()
            if not busy(port) and (not process or process.startswith("Z")):
                (root / "state" / (name + ".pid")).unlink(missing_ok=True)
                return
            time.sleep(1)
        raise RuntimeError("Graceful stop timed out for " + name)
    if busy(port):
        raise RuntimeError("Port occupied by unowned service: " + str(port))

def spawn(root, name, args, port, env=None, cwd=None):
    if busy(port):
        if owned_pid(root, name):
            return
        raise RuntimeError("Port occupied by unowned service: " + str(port))
    log = (root / "logs" / (name + ".log")).open("ab", buffering=0)
    proc = subprocess.Popen([str(x) for x in args], stdin=subprocess.DEVNULL, stdout=log,
                            stderr=log, start_new_session=True, env=env, cwd=cwd or root)
    log.close()
    (root / "state" / (name + ".pid")).write_text(str(proc.pid))

def owui_env(root, cfg):
    env = os.environ.copy()
    for k in ("RESET_CONFIG_ON_START", "WEBUI_SECRET_KEY", "WEBUI_BANNERS", "DATABASE_URL", "OPENAI_API_BASE_URLS",
              "OPENAI_API_KEYS", "OLLAMA_BASE_URLS", "DEFAULT_MODELS"):
        env.pop(k, None)
    env.update(DATA_DIR=str(root / "data"), WEBUI_NAME="BOM AI", DEFAULT_LOCALE="th-TH",
               FRONTEND_BUILD_DIR=cfg["frontend_dir"], STATIC_DIR=str(root / "static"),
               WEBUI_AUTH="true", ENABLE_PERSISTENT_CONFIG="true", ENABLE_SIGNUP="false",
               ENABLE_MEMORIES="false", RESET_CONFIG_ON_START="false",
               ENABLE_OLLAMA_API="false", ENABLE_OPENAI_API="true",
               OPENAI_API_BASE_URL=cfg["gateway_url"], OPENAI_API_KEY=cfg["gateway_key"],
               CORS_ALLOW_ORIGIN=f"http://127.0.0.1:{cfg['owui_port']};http://localhost:{cfg['owui_port']}")
    if cfg.get("qc") and cfg.get("qc_browser_origin"):
        env["CORS_ALLOW_ORIGIN"] += ";" + cfg["qc_browser_origin"]
    creds = json.loads((root / "state" / "first-login.json").read_text())
    env.update(WEBUI_ADMIN_EMAIL=creds["email"], WEBUI_ADMIN_PASSWORD=creds["password"], WEBUI_ADMIN_NAME="BOM AI")
    return env

def start_services(root, cfg):
    py = cfg["owui_python"]
    if not busy(cfg["ollama_port"]):
        env = os.environ.copy()
        env.update(OLLAMA_HOST=f"127.0.0.1:{cfg['ollama_port']}", OLLAMA_MAX_LOADED_MODELS="1")
        spawn(root, "ollama", [cfg["ollama_binary"], "serve"], cfg["ollama_port"], env)
        ready(cfg["ollama_url"] + "/api/version", 120)
    spawn(root, "gateway", [py, root / "runtime/bom_runtime.py", "--config", root / "runtime.json",
          "--host", "127.0.0.1", "--port", cfg["gateway_port"], "--upstream", cfg["ollama_url"],
          "--expected-version", cfg["expected_version"], "--catalog", root / "runtime/models.json",
          "--log", root / "logs/gateway.jsonl"], cfg["gateway_port"])
    ready(f"http://127.0.0.1:{cfg['gateway_port']}/healthz", 60)
    env = os.environ.copy()
    env["SEARXNG_SETTINGS_PATH"] = str(root / "searxng-settings.yml")
    spawn(root, "searxng", [cfg["searxng_python"], root / "runtime/install_unix.py", "--root", root, "--serve-searxng"], cfg["search_port"], env, cfg["searxng_source"])
    ready(f"http://127.0.0.1:{cfg['search_port']}/", 90)
    spawn(root, "owui", [py, root / "runtime/install_unix.py", "--root", root, "--serve-owui"],
          cfg["owui_port"], owui_env(root, cfg))
    ready(f"http://127.0.0.1:{cfg['owui_port']}/api/config", 420)

def verify(root, cfg):
    from audit_owui import audit
    base = f"http://127.0.0.1:{cfg['owui_port']}"
    # open_webui.serve creates its key in cwd, which spawn() sets to this root.
    # Inspect an existing admin without changing/relying on its login password.
    audited = audit(root / "data/webui.db", root / ".webui_secret_key", base)
    required = {k: v for k, v in audited["checks"].items() if k != "web_search_default_on"}
    failed = [k for k, passed in required.items() if not passed]
    if failed:
        raise RuntimeError("Post-restart API verification failed: " + ", ".join(failed))
    api = audited["api_config"]
    if api.get("default_models") != cfg["model_alias"]:
        raise RuntimeError("Default model does not match selected tier")
    ids = {b.get("id") for b in audited["banners"]}
    models = request(f"http://127.0.0.1:{cfg['gateway_port']}/v1/models", token=cfg["gateway_key"])
    if not any(x["id"] == cfg["model_alias"] for x in models["data"]):
        raise RuntimeError("Gateway model missing")
    expected_icon = hashlib.sha256((root / "cache/favicon.png").read_bytes()).hexdigest()
    served_icons = {}
    for icon_path in ("/favicon.png", "/static/favicon.png"):
        with urllib.request.urlopen(base + icon_path, timeout=15) as response:
            served_icons[icon_path] = hashlib.sha256(response.read()).hexdigest()
        if served_icons[icon_path] != expected_icon:
            raise RuntimeError("BOM favicon mismatch at " + icon_path)
    search = request(f"http://127.0.0.1:{cfg['search_port']}/search?q=BOM+AI&format=json", timeout=90)
    if not isinstance(search.get("results"), list) or not search["results"]:
        raise RuntimeError("Search returned no JSON results; investigate SearXNG before claiming search works")
    evidence = dict(version=VERSION, timestamp=time.time(), tier=cfg["tier"], alias=cfg["model_alias"],
                    banners=sorted(ids), locale=api.get("default_locale"), signup=False,
                    search_result_count=len(search["results"]), status="CONFIG_VERIFIED",
                    favicon_sha256=expected_icon, served_favicon_sha256=served_icons,
                    api_audit=audited,
                    note="Does not substitute for headed browser or street quality gates. Explicit existing personal search preferences are preserved.")
    write_json(root / "state/install-verification.json", evidence)
    return evidence

def ensure_venv(path, reuse, requirements):
    if reuse:
        py = Path(reuse).expanduser().resolve() / "bin/python"
        if not py.exists():
            raise RuntimeError("QC reuse venv missing: " + str(py))
        return py
    py = path / "bin/python"
    if not py.exists():
        run([sys.executable, "-m", "venv", path])
    run([py, "-m", "pip", "install", "--disable-pip-version-check", *requirements])
    run([py, "-m", "pip", "check"])
    return py

def install_ollama(root, cfg):
    try:
        info = request(cfg["ollama_url"] + "/api/version")
        cfg["expected_version"] = info["version"]
        cfg["ollama_binary"] = shutil.which("ollama") or "ollama"
        return
    except Exception:
        pass
    binary = shutil.which("ollama")
    if not binary:
        key = "Darwin" if platform.system() == "Darwin" else "Linux-" + platform.machine()
        asset, sha = OLLAMA_ASSETS[key]
        archive = download("https://github.com/ollama/ollama/releases/download/v0.40.13/" + asset, root / "cache" / asset, sha)
        target = root / "ollama"
        target.mkdir(exist_ok=True)
        if asset.endswith(".zst"):
            tooling = ensure_venv(root / ".venv-tools", None, ["zstandard==0.23.0"])
            run([tooling, "-c", "import zstandard,sys; zstandard.ZstdDecompressor().copy_stream(open(sys.argv[1],'rb'),open(sys.argv[2],'wb'))", archive, root / "cache/ollama.tar"])
            archive = root / "cache/ollama.tar"
        with tarfile.open(archive) as tf:
            # Filter is available on maintained Python 3.11 patch releases.
            tf.extractall(target, filter="data")
        candidates = [p for p in target.rglob("ollama") if p.is_file() and p.name == "ollama"]
        if not candidates:
            raise RuntimeError("Ollama archive has no executable")
        binary = str(candidates[0])
        Path(binary).chmod(0o755)
    cfg["ollama_binary"] = binary
    env = os.environ.copy()
    env.update(OLLAMA_HOST=f"127.0.0.1:{cfg['ollama_port']}", OLLAMA_MAX_LOADED_MODELS="1")
    spawn(root, "ollama", [binary, "serve"], cfg["ollama_port"], env)
    ready(cfg["ollama_url"] + "/api/version", 120)
    cfg["expected_version"] = request(cfg["ollama_url"] + "/api/version")["version"]

def model_setup(root, cfg):
    ref = "siamcafe/bom-ai:" + cfg["tier"] + "-v2.0.0"
    tags = request(cfg["ollama_url"] + "/api/tags")["models"]
    if not any(m.get("name") == ref for m in tags):
        print("Downloading model:", ref, flush=True)
        request(cfg["ollama_url"] + "/api/pull", {"model": ref, "stream": False}, timeout=7200)
    # Preserve a wrong/legacy alias mapping before overwriting it; blobs are
    # never deleted (contract 4A.2).
    names = {m.get("name", "") for m in tags}
    legacy = cfg["model_alias"] + ":pre2-legacy"
    if any(n == cfg["model_alias"] or n.startswith(cfg["model_alias"] + ":") for n in names) and legacy not in names:
        request(cfg["ollama_url"] + "/api/copy", {"source": cfg["model_alias"], "destination": legacy})
        print("Preserved previous alias mapping as", legacy, flush=True)
    mf = "FROM " + ref + "\n" + "".join(f"PARAMETER {k} {v}\n" for k, v in PARAMS.items()) + 'SYSTEM """' + SYSTEM + '"""\n'
    (root / ("Modelfile." + cfg["tier"])).write_text(mf, encoding="utf-8")
    result = request(cfg["ollama_url"] + "/api/create", dict(model=cfg["model_alias"], **{"from": ref}, parameters=PARAMS, system=SYSTEM, stream=False), timeout=600)
    if result.get("status") != "success":
        raise RuntimeError("Model alias creation failed: " + str(result))
    shown = request(cfg["ollama_url"] + "/api/show", {"model": cfg["model_alias"]})
    actual = dict(line.split(None, 1) for line in shown.get("parameters", "").splitlines() if line.strip())
    for key, value in PARAMS.items():
        assert key in actual and abs(float(actual[key]) - value) < 1e-8, "GOD parameter mismatch: " + key
    assert shown.get("system", "").strip() == SYSTEM, "SYSTEM mismatch"
    write_json(root / "state/model-verification.json", {"model": cfg["model_alias"], "parameters": actual, "system": shown["system"]})

def frontend(root, cfg):
    # Never patch a reused QC environment's production frontend.
    result = subprocess.check_output([cfg["owui_python"], "-c", "import open_webui,pathlib;print(pathlib.Path(open_webui.__file__).parent/'frontend')"], text=True).strip()
    src = Path(result)
    dest = root / "frontend"
    if not dest.exists():
        shutil.copytree(src, dest)
    html = dest / "index.html"
    body = html.read_text()
    if "localStorage.theme = 'system';" in body:
        body = body.replace("localStorage.theme = 'system';", "localStorage.theme = 'dark';")
    elif "localStorage.theme = 'dark';" not in body:
        raise RuntimeError("Pinned frontend dark bootstrap not found")
    # Browsers prefer SVG/ICO candidates over PNG. Keep one explicit BOM icon;
    # replacing only favicon.png leaves the upstream tab icon selected.
    body = re.sub(r'''<link\b[^>]*\brel=["'](?:icon|shortcut icon)["'][^>]*>''', "", body, flags=re.I | re.S)
    body = body.replace("</head>", '<link rel="icon" type="image/png" href="/static/favicon.png?bomai=v3" />\n</head>', 1)
    html.write_text(body)
    favicon = download("https://bomai.app/user/themes/bomai/images/apple-touch-icon.png", root / "cache/favicon.png")
    if not favicon.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
        raise RuntimeError("Favicon is not PNG")
    # Models use /favicon.png, while the browser tab uses /static/favicon.png.
    for path in [dest / "favicon.png", dest / "static/favicon.png",
                 dest / "static/favicon-96x96.png", dest / "static/logo.png",
                 dest / "static/apple-touch-icon.png"]:
        if path.parent.exists():
            shutil.copyfile(favicon, path)
    cfg["frontend_dir"] = str(dest)

def create_launcher(root, cfg):
    launcher = root / ("Start-BOM-AI.command" if platform.system() == "Darwin" else "start-bom-ai.sh")
    launcher.write_text("#!/bin/bash\nset -euo pipefail\nexec " + shlex.join([cfg["owui_python"], str(root / "runtime/install_unix.py"), "--root", str(root), "--start"]) + "\n")
    launcher.chmod(0o755)
    if cfg["qc"]:
        return
    if platform.system() == "Darwin":
        desktop = Path.home() / "Desktop/BOM AI.command"
        shutil.copyfile(launcher, desktop)
        desktop.chmod(0o755)
        # Login agent uses an argument array: spaces in usernames/paths are safe.
        agent = Path.home() / "Library/LaunchAgents/app.bomai.local.plist"
        agent.parent.mkdir(parents=True, exist_ok=True)
        agent.write_bytes(plistlib.dumps(dict(Label="app.bomai.local", RunAtLoad=True,
            ProgramArguments=[cfg["owui_python"], str(root / "runtime/install_unix.py"), "--root", str(root), "--start", "--no-browser"],
            StandardOutPath=str(root / "logs/login.log"), StandardErrorPath=str(root / "logs/login-error.log"))))
    else:
        desktop = Path.home() / ".local/share/applications/bomai.desktop"
        desktop.parent.mkdir(parents=True, exist_ok=True)
        command = '"' + str(launcher).replace('"', '\\"') + '"'
        desktop.write_text("[Desktop Entry]\nType=Application\nName=BOM AI\nExec=" + command + "\nTerminal=false\nIcon=" + str(root / "cache/favicon.png") + "\nCategories=Education;\n")
        autostart = Path.home() / ".config/autostart/bomai.desktop"
        autostart.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(desktop, autostart)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=os.environ.get("BOMAI_ROOT", str(Path.home() / "BOM-AI")))
    parser.add_argument("--tier", choices=["light", "pro"], default=os.environ.get("BOMAI_TIER"))
    parser.add_argument("--qc", action="store_true")
    parser.add_argument("--qc-browser-origin", help="Additional literal loopback origin for SSH-tunnel browser QC only")
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--start", action="store_true")
    parser.add_argument("--stop", action="store_true")
    parser.add_argument("--serve-owui", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--serve-searxng", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--reuse-owui-venv")
    parser.add_argument("--reuse-searxng-venv")
    parser.add_argument("--reuse-searxng-source")
    args = parser.parse_args()
    if args.qc_browser_origin:
        origin = urlsplit(args.qc_browser_origin)
        if not args.qc or origin.scheme != "http" or origin.hostname not in ("127.0.0.1", "localhost", "::1") or origin.path or origin.query or origin.fragment or origin.username or origin.password or origin.port is None:
            parser.error("QC browser origin must be an http literal loopback origin with a port and --qc")
    if platform.system() not in ("Linux", "Darwin"):
        parser.error("Use Windows .bat on Windows")
    root = Path(args.root).expanduser().resolve()
    if root == Path.home() or root == Path("/"):
        parser.error("Choose a dedicated BOM AI folder")
    for folder in ("runtime", "data", "logs", "state", "cache"):
        (root / folder).mkdir(parents=True, exist_ok=True)
    os.chmod(root / "state", 0o700)
    config_path = root / "runtime.json"
    cfg = json.loads(config_path.read_text()) if config_path.exists() else {}
    if args.serve_owui:
        import open_webui
        open_webui.serve(host="127.0.0.1", port=cfg["owui_port"])
        return
    if args.serve_searxng:
        sys.path.insert(0, cfg["searxng_source"])
        from waitress import serve
        from searx.webapp import app
        serve(app, host="127.0.0.1", port=cfg["search_port"])
        return
    if args.start or args.stop:
        if not cfg:
            parser.error("Installation not configured")
        if args.stop:
            for name, key in (("owui", "owui_port"), ("gateway", "gateway_port"), ("searxng", "search_port")):
                stop(root, name, cfg[key])
            return
        start_services(root, cfg)
        if not args.no_browser:
            webbrowser.open(f"http://127.0.0.1:{cfg['owui_port']}")
        return
    if any((args.reuse_owui_venv, args.reuse_searxng_venv, args.reuse_searxng_source)) and not args.qc:
        parser.error("Reuse options are restricted to isolated QC")
    tier = args.tier or cfg.get("tier")
    if not tier:
        try:
            with open("/dev/tty") as terminal:
                print("1) Light  2) Pro  [Production deferred]\nChoose [1]: ", end="", flush=True)
                tier = "pro" if terminal.readline().strip() == "2" else "light"
        except OSError:
            tier = "light"
    if platform.system() == "Darwin":
        subprocess.run(["system_profiler", "SPDisplaysDataType"], check=False)
    elif shutil.which("nvidia-smi"):
        subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"], check=False)
    cfg.update(version=VERSION, tier=tier, qc=args.qc, model_alias=("bomai-qc-" + tier if args.qc else ("bomai-safe" if tier == "light" else "bomai-pro")),
               owui_port=18080 if args.qc else 8080, gateway_port=11436 if args.qc else 11435,
               search_port=18888 if args.qc else 8888, ollama_port=11434, ollama_url="http://127.0.0.1:11434")
    cfg.setdefault("gateway_key", secrets.token_urlsafe(36))
    if args.qc_browser_origin:
        cfg["qc_browser_origin"] = args.qc_browser_origin
    cfg["gateway_url"] = f"http://127.0.0.1:{cfg['gateway_port']}/v1"
    cfg["searxng_url"] = f"http://127.0.0.1:{cfg['search_port']}/search?q=<query>&format=json"
    # Stop only this installation, before replacing its source or seeding.
    for name, key in (("owui", "owui_port"), ("gateway", "gateway_port"), ("searxng", "search_port")):
        stop(root, name, cfg[key])
    source = Path(__file__).resolve().parent
    for name in ("install_unix.py", "bom_runtime.py", "seed_owui.py", "audit_owui.py", "models.json"):
        if source / name != root / "runtime" / name:
            shutil.copyfile(source / name, root / "runtime" / name)
    credentials = root / "state/first-login.json"
    if not credentials.exists():
        write_json(credentials, {"email": "owner@bomai.local", "password": secrets.token_urlsafe(24)})
    install_ollama(root, cfg)
    model_setup(root, cfg)
    cfg["owui_python"] = str(ensure_venv(root / ".venv", args.reuse_owui_venv, ["open-webui==" + OWUI]))
    installed = subprocess.check_output([cfg["owui_python"], "-c", "import importlib.metadata; print(importlib.metadata.version('open-webui'))"], text=True).strip()
    assert installed == OWUI, "Open WebUI version mismatch"
    if args.reuse_searxng_source:
        sx = Path(args.reuse_searxng_source).expanduser().resolve()
    else:
        archive = download("https://codeload.github.com/searxng/searxng/zip/" + SEARX_REV, root / "cache/searxng.zip", SEARX_SHA)
        sx = root / ("searxng-" + SEARX_REV)
        if not sx.exists():
            with zipfile.ZipFile(archive) as z:
                z.extractall(root)
    cfg["searxng_source"] = str(sx)
    cfg["searxng_python"] = str(ensure_venv(root / ".venv-searxng", args.reuse_searxng_venv, ["-r", str(sx / "requirements.txt"), "waitress==3.0.2"]))
    settings = root / "searxng-settings.yml"
    if not settings.exists():
        settings.write_text('use_default_settings: true\nserver:\n  secret_key: "' + secrets.token_hex(32) + '"\n  limiter: false\n  image_proxy: true\nsearch:\n  formats: [html, json]\n')
        settings.chmod(0o600)
    frontend(root, cfg)
    write_json(config_path, cfg)
    start_services(root, cfg)
    stop(root, "owui", cfg["owui_port"])
    run([cfg["owui_python"], root / "runtime/seed_owui.py", "--db", root / "data/webui.db", "--config", config_path,
         "--offline-confirmed", "--owui-port", cfg["owui_port"]])
    start_services(root, cfg)
    evidence = verify(root, cfg)
    create_launcher(root, cfg)
    print("\nBOM AI configured:", tier, cfg["model_alias"], "\n", json.dumps(evidence, ensure_ascii=False))
    creds = json.loads(credentials.read_text())
    print("Initial login:", creds["email"], "\nInitial password:", creds["password"], "\nIf you changed this password, continue using your current password. Keep this file private:", credentials)
    print("URL:", f"http://127.0.0.1:{cfg['owui_port']}")
    if not args.no_browser:
        webbrowser.open(f"http://127.0.0.1:{cfg['owui_port']}")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("INSTALLATION INCOMPLETE:", exc, file=sys.stderr)
        sys.exit(1)
