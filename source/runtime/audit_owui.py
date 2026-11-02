#!/usr/bin/env python3
"""Local owner-only read audit of an existing OWUI account, without password reset.

Reads a pre-existing admin ID and session revocation stamp from SQLite, and uses
the server's existing signing key for a two-minute in-memory token. Requires
local owner access to both files. Sends only GET requests to loopback. Neither
the key, token, account ID, email nor password is included in output. Refuses
this method when MFA is enabled; use a normal authenticated session instead.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import sqlite3
import time
import urllib.error
import urllib.request
import uuid
from contextlib import closing
from pathlib import Path
from urllib.parse import urlsplit


def b64(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def evaluate_search(default_ui, effective_ui, saved_ui, model_meta):
    """Verify release defaults while respecting an explicitly saved preference."""
    saved = "webSearch" in saved_ui
    expected = saved_ui["webSearch"] if saved else default_ui.get("webSearch")
    details = {
        "source": "saved_user" if saved else "global_default",
        "explicit_override": saved and saved_ui["webSearch"] != default_ui.get("webSearch"),
        "saved_value": saved_ui.get("webSearch"),
        "expected_effective": expected,
        "release_default": "always",
    }
    checks = {
        "effective_search_matches_saved_or_default": effective_ui.get("webSearch") == expected,
        "global_web_search_default_on": default_ui.get("webSearch") == "always",
        "visible_search_default_configured": "web_search" in (model_meta.get("defaultFeatureIds") or []),
    }
    return details, checks


def audit(db_path, secret_file, base_url):
    url = urlsplit(base_url)
    if url.scheme != "http" or url.hostname not in {"127.0.0.1", "localhost", "::1"} or url.username or url.password or url.query or url.fragment:
        raise ValueError("Audit requires a local http loopback OWUI URL")
    with closing(sqlite3.connect(Path(db_path).resolve(strict=True).as_uri() + "?mode=ro", uri=True)) as db:
        row = db.execute("SELECT value FROM config WHERE key='auth.mfa.enable'").fetchone()
        if row and (json.loads(row[0]) if isinstance(row[0], str) else row[0]):
            raise ValueError("MFA is enabled; this owner audit does not bypass MFA")
        columns = {r[1] for r in db.execute('PRAGMA table_info("auth")')}
        if "session_stamp" in columns:
            admin = db.execute("SELECT u.id,a.session_stamp FROM user u JOIN auth a ON a.id=u.id WHERE u.role='admin' ORDER BY u.created_at,u.id LIMIT 1").fetchone()
        else:
            admin = db.execute("SELECT id,NULL FROM user WHERE role='admin' ORDER BY created_at,id LIMIT 1").fetchone()
        settings_row = db.execute("SELECT settings FROM user WHERE id=?", (admin[0],)).fetchone() if admin else None
        saved_settings = json.loads(settings_row[0] or "{}") if settings_row else {}
        if saved_settings is None:
            saved_settings = {}
        if not isinstance(saved_settings, dict) or not isinstance(saved_settings.get("ui") or {}, dict):
            raise ValueError("Existing user settings must be JSON objects")
        saved_ui = saved_settings.get("ui") or {}
        default_row = db.execute("SELECT value FROM config WHERE key='ui.default_models'").fetchone()
        default_alias = json.loads(default_row[0]) if default_row and isinstance(default_row[0], str) else None
        model_row = db.execute("SELECT params,meta FROM model WHERE id=?", (default_alias,)).fetchone() if isinstance(default_alias, str) else None
        model_params = json.loads(model_row[0] or "{}") if model_row else {}
        model_meta = json.loads(model_row[1] or "{}") if model_row else {}
    if not admin:
        raise ValueError("No existing admin account; finish first-run bootstrap")
    now = int(time.time())
    payload = {"id": admin[0], "typ": "session", "auth_method": "password", "auth_time": now, "session_stamp": admin[1], "mfa_verified": False, "iat": now, "exp": now + 120, "jti": str(uuid.uuid4())}
    unsigned = b64(b'{"alg":"HS256","typ":"JWT"}') + "." + b64(json.dumps(payload, separators=(",", ":")).encode())
    # Match open_webui.serve(): KEY_FILE.read_text(), without stripping a key.
    secret = Path(secret_file).read_text(encoding="utf-8").encode()
    if not secret:
        raise ValueError("Empty server secret file")
    token = unsigned + "." + b64(hmac.new(secret, unsigned.encode(), hashlib.sha256).digest())
    # No environment proxy and no redirects: do not forward an admin token.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    def get(path):
        request = urllib.request.Request(base_url.rstrip("/") + path, headers={"Authorization": "Bearer " + token})
        with opener.open(request, timeout=30) as response:
            return json.load(response)
    config = get("/api/config")
    banners = get("/api/v1/configs/banners")
    settings = get("/api/v1/users/user/settings") or {}
    ui = settings.get("ui") or {}
    feature_names = ("auth", "enable_signup", "enable_login_form", "enable_api_keys", "enable_web_search", "enable_web_search_confirmation")
    public = {k: config.get(k) for k in ("status", "version", "name", "default_locale", "default_models")}
    public["features"] = {k: config.get("features", {}).get(k) for k in feature_names}
    default_ui = config.get("ui", {}).get("default_interface_settings") or {}
    search_preference, search_checks = evaluate_search(default_ui, ui, saved_ui, model_meta)
    banner_ids = {b.get("id") for b in banners}
    expected_content = {
        "bomai-welcome": "**BOM AI** — ผู้ช่วย AI ภาษาไทย 100% ฟรี ทำงานบนเครื่องคุณเอง ไม่ส่งข้อมูลออกนอก",
        "xm-partner": "[![Open XM Account](https://ads.pipaffiliates.com/i/158598?c=72816)](https://clicks.pipaffiliates.com/c?m=158598&c=72816)",
    }
    banner_by_id = {b.get("id"): b for b in banners}
    return {
        "time_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "api_config": public,
        "banners": banners,
        "effective_ui": {k: ui[k] for k in ("webSearch", "models", "theme", "language", "version") if k in ui},
        "default_ui": {"webSearch": default_ui.get("webSearch")},
        "search_preference": search_preference,
        "workspace_model_defaults": {
            "id": default_alias,
            "function_calling": model_params.get("function_calling"),
            "defaultFeatureIds": model_meta.get("defaultFeatureIds", []),
        },
        "checks": {
            "both_banner_ids_returned": {"bomai-welcome", "xm-partner"}.issubset(banner_ids),
            "banner_payloads_match": all(
                banner_by_id.get(key, {}).get("content") == content
                and banner_by_id[key].get("type") == "info"
                and banner_by_id[key].get("dismissible") is True
                for key, content in expected_content.items()
            ),
            "web_search_enabled": public["features"]["enable_web_search"] is True,
            "api_keys_enabled": public["features"]["enable_api_keys"] is True,
            "signup_disabled": public["features"]["enable_signup"] is False,
            "thai_locale": public["default_locale"] == "th-TH",
            **search_checks,
        },
        "limitations": "API checks do not prove visible banners, search results, theme or favicon; headed browser QC is still required.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True)
    parser.add_argument("--secret-file", required=True)
    parser.add_argument("--base-url", default="http://127.0.0.1:8080")
    parser.add_argument("--verify", action="store_true", help="exit nonzero if any API check fails")
    args = parser.parse_args()
    try:
        result = audit(args.db, args.secret_file, args.base_url)
    except urllib.error.HTTPError as error:
        raise SystemExit(f"Authenticated audit request failed: HTTP {error.code}")
    # ASCII JSON survives Windows PowerShell 5.1's native-output code page.
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if args.verify and not all(result["checks"].values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
