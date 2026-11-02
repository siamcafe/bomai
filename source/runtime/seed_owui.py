#!/usr/bin/env python3
"""Offline BOM AI configuration overlay for migrated Open WebUI 0.12.5.

The installer must start OWUI once, wait for migrations/admin creation, stop
and join that exact process, then call this program and restart. This program
never creates OWUI tables and never stops arbitrary processes. The closed-port
check is an additional guard; it is not proof an idle background writer stopped.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import socket
import sqlite3
import time
import uuid
from contextlib import closing
from pathlib import Path
from urllib.parse import urlsplit

OWUI_VERSION = "0.12.5"
SEED_REVISION = "bomai-v2.0.0-final-1"
SYSTEM_OWNER = "__bomai_seed__"  # Not an authentication account.
MODEL_ALIASES = {
    "light": {"bomai-safe", "bomai-qc-light"},
    "pro": {"bomai-pro", "bomai-qc-pro"},
}
BANNERS = [
    {"id": "bomai-welcome", "type": "info", "title": "", "content": "**BOM AI** — ผู้ช่วย AI ภาษาไทย 100% ฟรี ทำงานบนเครื่องคุณเอง ไม่ส่งข้อมูลออกนอก", "dismissible": True, "timestamp": 0},
    {"id": "xm-partner", "type": "info", "title": "", "content": "[![Open XM Account](https://ads.pipaffiliates.com/i/158598?c=72816)](https://clicks.pipaffiliates.com/c?m=158598&c=72816)", "dismissible": True, "timestamp": 0},
]


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def json_value(raw):
    return json.loads(raw) if isinstance(raw, (str, bytes, bytearray)) else raw


def decode(raw, expected, label):
    value = json_value(raw) if raw is not None else expected()
    if value is None:
        value = expected()
    if not isinstance(value, expected):
        raise ValueError(f"Unexpected JSON type in {label}")
    return value


def validate_config(config):
    if config.get("model_alias") not in MODEL_ALIASES.get(config.get("tier"), set()):
        raise ValueError("tier/model_alias mismatch; only Light and Pro are available")
    key = config.get("gateway_key", "")
    if not isinstance(key, str) or len(key) < 32:
        raise ValueError("gateway_key must be an installation-specific secret (32+ characters)")
    gateway = urlsplit(config.get("gateway_url", ""))
    if gateway.scheme != "http" or gateway.hostname != "127.0.0.1" or gateway.path != "/v1" or not gateway.port:
        raise ValueError("gateway_url must be http://127.0.0.1:PORT/v1")
    search = urlsplit(config.get("searxng_url", ""))
    if search.scheme != "http" or search.hostname != "127.0.0.1" or search.path != "/search" or not search.port:
        raise ValueError("searxng_url must be http://127.0.0.1:PORT/search?q=<query>&format=json")
    if "<query>" not in config["searxng_url"]:
        raise ValueError("searxng_url must include the literal <query> placeholder")


def ensure_stopped(port):
    if not 1 <= port <= 65535:
        raise ValueError("Invalid OWUI port")
    for host in ("127.0.0.1", "::1"):
        try:
            connection = socket.create_connection((host, port), timeout=0.3)
        except OSError:
            continue
        else:
            connection.close()
            raise RuntimeError(f"Port {port} is still listening. Stop and join OWUI before seeding.")


def validate_schema(db):
    required = {
        "config": {"key", "value", "updated_at"},
        "model": {"id", "user_id", "base_model_id", "name", "params", "meta", "version_id", "is_active", "updated_at", "created_at"},
        "user": {"id", "role", "settings", "updated_at", "created_at"},
        "access_grant": {"id", "resource_type", "resource_id", "principal_type", "principal_id", "permission", "created_at"},
        "alembic_version": {"version_num"},
    }
    for table, columns in required.items():
        found = {row[1] for row in db.execute(f'PRAGMA table_info("{table}")')}
        if not columns.issubset(found):
            raise ValueError(f"Unsupported/unmigrated schema: {table}; missing {sorted(columns-found)}")
        if table in ("config", "model", "access_grant") and found != columns:
            raise ValueError(f"Unexpected schema columns: {table}; review the pinned adapter")
    if not db.execute("SELECT version_num FROM alembic_version").fetchone():
        raise ValueError("No recorded Alembic migration revision")
    if db.execute('PRAGMA foreign_key_list("model")').fetchall():
        raise ValueError("Unexpected model foreign keys; reserved seed owner is incompatible")
    if db.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
        raise ValueError("SQLite quick_check failed")


def get_config(db, key, expected):
    row = db.execute("SELECT value FROM config WHERE key=?", (key,)).fetchone()
    return decode(row[0] if row else None, expected, key)


def put_config(db, key, value, now):
    row = db.execute("SELECT value FROM config WHERE key=?", (key,)).fetchone()
    if row and json_value(row[0]) == value:
        return
    db.execute(
        "INSERT INTO config(key,value,updated_at) VALUES (?,?,?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at",
        (key, encode(value), now),
    )


def verify_rows(db, values, alias, owner, params, meta):
    for key, expected in values.items():
        row = db.execute("SELECT value FROM config WHERE key=?", (key,)).fetchone()
        if row is None or json_value(row[0]) != expected:
            raise RuntimeError(f"Seed read-back mismatch: {key}")
    row = db.execute("SELECT user_id,base_model_id,params,meta,is_active FROM model WHERE id=?", (alias,)).fetchone()
    if not row or row[0] != owner or row[1] is not None or json_value(row[2]) != params or json_value(row[3]) != meta or row[4] != 1:
        raise RuntimeError("Seed read-back mismatch: workspace model")
    if not db.execute("SELECT 1 FROM access_grant WHERE resource_type='model' AND resource_id=? AND principal_type='user' AND principal_id='*' AND permission='read'", (alias,)).fetchone():
        raise RuntimeError("Seed read-back mismatch: model read grant")


def seed(db_path, config, observed_version, *, offline_confirmed=False, owui_port=None):
    if not offline_confirmed:
        raise ValueError("Caller must stop and join OWUI, then supply --offline-confirmed")
    if observed_version != OWUI_VERSION:
        raise ValueError(f"Adapter only supports Open WebUI {OWUI_VERSION}; got {observed_version}")
    if os.getenv("ENABLE_PERSISTENT_CONFIG", "true").lower() != "true":
        raise ValueError("ENABLE_PERSISTENT_CONFIG must remain true for this DB overlay")
    if os.getenv("RESET_CONFIG_ON_START", "false").lower() == "true":
        raise ValueError("RESET_CONFIG_ON_START=true would erase the seed on restart")
    validate_config(config)
    if owui_port is not None:
        ensure_stopped(owui_port)
    path = Path(db_path).resolve(strict=True)
    if not path.is_file():
        raise ValueError("db must identify an existing migrated SQLite file")
    backup_path = path.with_name(path.name + f".before-bomai-{time.time_ns()}.bak")
    uri = path.as_uri() + "?mode=rw"
    db = sqlite3.connect(uri, uri=True, timeout=5, isolation_level=None)
    try:
        db.execute("PRAGMA foreign_keys=ON")
        validate_schema(db)
        data_version = db.execute("PRAGMA data_version").fetchone()[0]
        # SQLite backup captures committed WAL contents. Never copy only webui.db.
        backup = sqlite3.connect(backup_path)
        try:
            if os.name != "nt":
                backup_path.chmod(0o600)
            db.backup(backup)
        finally:
            backup.close()
        db.execute("BEGIN EXCLUSIVE")
        if db.execute("PRAGMA data_version").fetchone()[0] != data_version:
            raise RuntimeError("DB changed during backup; stop all OWUI writers")
        now = int(time.time())
        alias = config["model_alias"]
        admin = db.execute("SELECT id FROM user WHERE role='admin' ORDER BY created_at,id LIMIT 1").fetchone()
        owner = admin[0] if admin else SYSTEM_OWNER
        values = {
            "ollama.enable": False,
            "openai.enable": True,
            "openai.api_base_urls": [config["gateway_url"]],
            "openai.api_keys": [config["gateway_key"]],
            "openai.api_configs": {"0": {"enable": True, "model_ids": [alias]}},
            "direct.enable": False,
            "web.search.enable": True,
            "web.search.engine": "searxng",
            "web.search.searxng_query_url": config["searxng_url"],
            "web.search.searxng_language": "th-TH",
            "web.search.result_count": 3,
            "web.search.bypass_embedding_and_retrieval": False,
            "web.search.bypass_web_loader": False,
            "ui.default_models": alias,
            "ui.default_locale": "th-TH",
            "ui.enable_login_form": True,
            "ui.enable_signup": False,
            "auth.enable_api_keys": True,
        }
        interface = get_config(db, "ui.default_interface_settings", dict)
        interface["webSearch"] = "always"
        values["ui.default_interface_settings"] = interface
        visibility = get_config(db, "ui.visibility", dict)
        visibility["chat.selected_web_search"] = True
        values["ui.visibility"] = visibility
        # First boot must seed upstream's complete permission tree. Refuse a
        # partial permission replacement, which would change unrelated access.
        permissions = get_config(db, "user.permissions", dict)
        if not permissions:
            raise ValueError("Missing upstream user.permissions; complete OWUI first boot before seeding")
        features = permissions.setdefault("features", {})
        if not isinstance(features, dict):
            raise ValueError("user.permissions.features must be an object")
        features["web_search"] = True
        features["api_keys"] = True
        values["user.permissions"] = permissions
        existing_banners = get_config(db, "ui.banners", list)
        if any(not isinstance(item, dict) for item in existing_banners):
            raise ValueError("ui.banners contains malformed existing records")
        values["ui.banners"] = [b for b in existing_banners if b.get("id") not in {"bomai-welcome", "xm-partner", "bomai-xm"}] + BANNERS
        for key, value in values.items():
            put_config(db, key, value, now)

        # Both managed tiers get a model row and a read grant on every host
        # (contract 4A.4 / bug M4). The other tier is seeded first so the
        # installing alias's params/meta remain current for verify_rows.
        other_alias = "bomai-pro" if alias == "bomai-safe" else "bomai-safe"
        other_name = "BOM AI Pro" if alias == "bomai-safe" else "BOM AI Light"
        for row_alias, name in ((other_alias, other_name),
                                (alias, "BOM AI Light" if config["tier"] == "light" else "BOM AI Pro")):
            row = db.execute("SELECT user_id,params,meta,name,base_model_id,is_active FROM model WHERE id=?", (row_alias,)).fetchone()
            if row:
                params, meta = decode(row[1], dict, "model.params"), decode(row[2], dict, "model.meta")
                if meta.get("bomai_managed") is not True:
                    raise ValueError(f"Model ID {row_alias} belongs to an unmanaged model; refusing overwrite")
                if row[0] and row[0] != SYSTEM_OWNER:
                    owner = row[0]
            else:
                params, meta = {}, {}
            params["function_calling"] = "legacy"
            meta["bomai_managed"] = True
            capabilities = meta.setdefault("capabilities", {})
            if not isinstance(capabilities, dict):
                raise ValueError("model.meta.capabilities must be an object")
            capabilities["web_search"] = True
            default_features = meta.setdefault("defaultFeatureIds", [])
            if not isinstance(default_features, list) or any(not isinstance(item, str) for item in default_features):
                raise ValueError("model.meta.defaultFeatureIds must be an array of strings")
            if "web_search" not in default_features:
                default_features.append("web_search")
            if row is None:
                db.execute("INSERT INTO model(id,user_id,base_model_id,name,params,meta,version_id,is_active,updated_at,created_at) VALUES (?,?,NULL,?,?,?,NULL,1,?,?)", (row_alias, owner, name, encode(params), encode(meta), now, now))
            elif (row[0], json_value(row[1]), json_value(row[2]), row[3], row[4], row[5]) != (owner, params, meta, name, None, 1):
                db.execute("UPDATE model SET user_id=?,base_model_id=NULL,name=?,params=?,meta=?,is_active=1,updated_at=? WHERE id=?", (owner, name, encode(params), encode(meta), now, row_alias))
            if not db.execute("SELECT 1 FROM access_grant WHERE resource_type='model' AND resource_id=? AND principal_type='user' AND principal_id='*' AND permission='read'", (row_alias,)).fetchone():
                db.execute("INSERT INTO access_grant(id,resource_type,resource_id,principal_type,principal_id,permission,created_at) VALUES (?,'model',?,'user','*','read',?)", (str(uuid.uuid4()), row_alias, now))

        for user_id, raw in db.execute("SELECT id,settings FROM user").fetchall():
            settings = decode(raw, dict, "user.settings")
            ui = settings.setdefault("ui", {})
            if ui is None:
                ui = settings["ui"] = {}
            if not isinstance(ui, dict):
                raise ValueError("user.settings.ui must be an object")
            if "webSearch" not in ui:
                ui["webSearch"] = "always"
                db.execute("UPDATE user SET settings=?,updated_at=? WHERE id=?", (encode(settings), now, user_id))

        digest = hashlib.sha256(encode(config).encode("utf-8")).hexdigest()
        db.execute("CREATE TABLE IF NOT EXISTS bomai_seed_state (id INTEGER PRIMARY KEY CHECK(id=1),revision TEXT NOT NULL,config_sha256 TEXT NOT NULL,updated_at INTEGER NOT NULL)")
        db.execute("INSERT INTO bomai_seed_state(id,revision,config_sha256,updated_at) VALUES (1,?,?,?) ON CONFLICT(id) DO UPDATE SET revision=excluded.revision,config_sha256=excluded.config_sha256,updated_at=excluded.updated_at WHERE revision!=excluded.revision OR config_sha256!=excluded.config_sha256", (SEED_REVISION, digest, now))
        verify_rows(db, values, alias, owner, params, meta)
        changed = db.total_changes
        db.execute("COMMIT")
        # Verify through a new connection, not only this transaction's cache.
        with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as reader:
            verify_rows(reader, values, alias, owner, params, meta)
        return {"seed_revision": SEED_REVISION, "changed_rows": changed, "backup": str(backup_path), "initial_admin_needed": admin is None, "verified_keys": sorted(values), "model_alias": alias, "readback_verified": True}
    except BaseException:
        if db.in_transaction:
            db.execute("ROLLBACK")
        raise
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--owui-version", default=OWUI_VERSION, choices=[OWUI_VERSION])
    parser.add_argument("--owui-port", type=int, default=8080)
    parser.add_argument("--offline-confirmed", action="store_true")
    parser.add_argument("--wait-seconds", type=float, default=120)
    args = parser.parse_args()
    observed_version = importlib.metadata.version("open-webui")
    if observed_version != args.owui_version:
        raise SystemExit("Installed Open WebUI package differs from requested adapter")
    deadline = time.monotonic() + args.wait_seconds
    while not Path(args.db).is_file():
        if time.monotonic() >= deadline:
            raise SystemExit("webui.db not found; installer must finish OWUI first boot, then stop it")
        time.sleep(0.5)
    config = json.loads(Path(args.config).read_text(encoding="utf-8-sig"))
    report = seed(args.db, config, observed_version, offline_confirmed=args.offline_confirmed, owui_port=args.owui_port)
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
