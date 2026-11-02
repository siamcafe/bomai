"""SQLite fixture tests, not substitutes for real OWUI/browser installation QC."""
import importlib.util
import json
import os
from pathlib import Path
import socket
import sqlite3
import tempfile
import unittest
from contextlib import closing, contextmanager
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / "runtime" / "seed_owui.py"
SPEC = importlib.util.spec_from_file_location("seed_owui", SOURCE)
seed = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(seed)


class SeedTests(unittest.TestCase):
    def setUp(self):
        scratch = Path(__file__).resolve().parents[3] / "work"
        scratch.mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "webui.db"
        self.config = {"tier": "light", "model_alias": "bomai-safe", "gateway_url": "http://127.0.0.1:11435/v1", "gateway_key": "fixture-secret-" + "x" * 32, "searxng_url": "http://127.0.0.1:8888/search?q=<query>&format=json"}
        with self.db() as db:
            db.executescript("""
                CREATE TABLE config(key TEXT PRIMARY KEY NOT NULL,value JSON NOT NULL,updated_at BIGINT);
                CREATE TABLE model(id TEXT PRIMARY KEY,user_id TEXT,base_model_id TEXT,name TEXT,params TEXT,meta TEXT,version_id TEXT,is_active BOOLEAN,updated_at BIGINT,created_at BIGINT);
                CREATE TABLE user(id TEXT PRIMARY KEY,role TEXT,settings TEXT,updated_at BIGINT,created_at BIGINT);
                CREATE TABLE access_grant(id TEXT PRIMARY KEY,resource_type TEXT,resource_id TEXT,principal_type TEXT,principal_id TEXT,permission TEXT,created_at BIGINT);
                CREATE TABLE alembic_version(version_num TEXT PRIMARY KEY);
                INSERT INTO alembic_version VALUES ('fixture-not-a-real-migration');
                INSERT INTO config VALUES ('ui.banners','[]',1);
                INSERT INTO config VALUES ('user.permissions','{"chat":{"delete":false},"features":{"api_keys":false,"web_search":false,"notes":true}}',1);
                INSERT INTO user VALUES ('admin-1','admin','{"ui":{"version":"0.12.5"},"custom":7}',1,1);
            """)

    @contextmanager
    def db(self):
        with closing(sqlite3.connect(self.path)) as db:
            with db:
                yield db

    def run_seed(self, **kwargs):
        with patch.dict(os.environ, {"ENABLE_PERSISTENT_CONFIG": "true", "RESET_CONFIG_ON_START": "false"}):
            return seed.seed(self.path, self.config, "0.12.5", offline_confirmed=True, **kwargs)

    def value(self, key):
        with self.db() as db:
            return seed.json_value(db.execute("SELECT value FROM config WHERE key=?", (key,)).fetchone()[0])

    def dump(self):
        with self.db() as db:
            return "\n".join(db.iterdump())

    def test_seed_readback_and_second_run_zero_changes(self):
        report = self.run_seed()
        self.assertTrue(report["readback_verified"])
        self.assertEqual(self.value("ui.banners"), seed.BANNERS)
        self.assertEqual(self.value("ui.default_models"), "bomai-safe")
        self.assertFalse(self.value("ui.enable_signup"))
        self.assertTrue(self.value("auth.enable_api_keys"))
        self.assertEqual(self.value("ui.visibility"), {"chat.selected_web_search": True})
        with self.db() as db:
            row = db.execute("SELECT user_id,base_model_id,params FROM model").fetchone()
            self.assertEqual(row[:2], ("admin-1", None))
            self.assertEqual(json.loads(row[2])["function_calling"], "legacy")
        before = self.dump()
        self.assertEqual(self.run_seed()["changed_rows"], 0)
        self.assertEqual(self.dump(), before)

    def test_both_tier_rows_and_grants_seeded(self):
        self.run_seed()
        with self.db() as db:
            rows = {r[0]: r[1] for r in db.execute("SELECT id, name FROM model").fetchall()}
        self.assertEqual(rows.get("bomai-safe"), "BOM AI Light")
        self.assertEqual(rows.get("bomai-pro"), "BOM AI Pro")
        with self.db() as db:
            grants = {r[0] for r in db.execute("SELECT resource_id FROM access_grant WHERE resource_type='model' AND permission='read'").fetchall()}
        self.assertIn("bomai-safe", grants)
        self.assertIn("bomai-pro", grants)
        self.assertEqual(self.value("ui.default_models"), "bomai-safe")

    def test_bypass_flags_false(self):
        self.run_seed()
        self.assertIs(self.value("web.search.bypass_embedding_and_retrieval"), False)
        self.assertIs(self.value("web.search.bypass_web_loader"), False)

    def test_pro_tier_run_also_seeds_light_row(self):
        self.config["tier"] = "pro"
        self.config["model_alias"] = "bomai-pro"
        self.run_seed()
        with self.db() as db:
            rows = {r[0]: r[1] for r in db.execute("SELECT id, name FROM model").fetchall()}
        self.assertEqual(rows.get("bomai-safe"), "BOM AI Light")
        self.assertEqual(rows.get("bomai-pro"), "BOM AI Pro")
        self.assertEqual(self.value("ui.default_models"), "bomai-pro")

    def test_backup_is_preseed_database_with_wal_contents(self):
        with self.db() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("INSERT INTO config VALUES ('custom.test','42',1)")
        report = self.run_seed()
        with closing(sqlite3.connect(report["backup"])) as db:
            self.assertEqual(db.execute("SELECT value FROM config WHERE key='custom.test'").fetchone()[0], 42)
            self.assertEqual(json.loads(db.execute("SELECT value FROM config WHERE key='ui.banners'").fetchone()[0]), [])
            self.assertIsNone(db.execute("SELECT 1 FROM model").fetchone())

    def test_unrelated_preferences_banners_and_permissions_survive(self):
        with self.db() as db:
            db.execute("UPDATE config SET value=? WHERE key='ui.banners'", (json.dumps([{"id": "owner-banner", "content": "keep"}, {"id": "bomai-xm", "content": "outdated"}]),))
            db.execute("UPDATE user SET settings=?", (json.dumps({"ui": {"webSearch": None, "models": ["personal-model"], "theme": "light"}, "custom": 7}),))
        self.run_seed()
        self.assertEqual(self.value("ui.banners")[0], {"id": "owner-banner", "content": "keep"})
        self.assertEqual(len(self.value("ui.banners")), 3)
        permissions = self.value("user.permissions")
        self.assertFalse(permissions["chat"]["delete"])
        self.assertTrue(permissions["features"]["notes"])
        self.assertTrue(permissions["features"]["api_keys"])
        with self.db() as db:
            ui = json.loads(db.execute("SELECT settings FROM user").fetchone()[0])["ui"]
        self.assertIsNone(ui["webSearch"])
        self.assertEqual(ui["theme"], "light")
        self.assertEqual(ui["models"], ["personal-model"])

    def test_unmanaged_model_collision_rolls_back_all_config_writes(self):
        with self.db() as db:
            db.execute("INSERT INTO model(id,user_id,name,params,meta,is_active) VALUES ('bomai-safe','owner','Personal','{}','{}',1)")
        before = self.dump()
        with self.assertRaisesRegex(ValueError, "unmanaged"):
            self.run_seed()
        self.assertEqual(self.dump(), before)

    def test_malformed_user_settings_roll_back(self):
        with self.db() as db:
            db.execute("UPDATE user SET settings='[1,2]'")
        before = self.dump()
        with self.assertRaisesRegex(ValueError, "user.settings"):
            self.run_seed()
        self.assertEqual(self.dump(), before)

    def test_precommit_verification_failure_rolls_back(self):
        before = self.dump()
        with patch.object(seed, "verify_rows", side_effect=RuntimeError("injected verification failure")):
            with self.assertRaisesRegex(RuntimeError, "verification"):
                self.run_seed()
        self.assertEqual(self.dump(), before)

    def test_unmigrated_schema_refused_without_modification(self):
        with self.db() as db:
            db.execute("DROP TABLE config")
            db.execute("CREATE TABLE config(id INTEGER PRIMARY KEY,data JSON)")
        before = self.dump()
        with self.assertRaisesRegex(ValueError, "schema"):
            self.run_seed()
        self.assertEqual(self.dump(), before)

    def test_offline_confirmation_and_version_required(self):
        before = self.dump()
        with self.assertRaisesRegex(ValueError, "stop and join"):
            seed.seed(self.path, self.config, "0.12.5")
        with self.assertRaisesRegex(ValueError, "supports"):
            seed.seed(self.path, self.config, "0.12.6", offline_confirmed=True)
        self.assertEqual(self.dump(), before)

    def test_active_listener_refused_before_writes(self):
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            listener.listen(1)
            before = self.dump()
            with self.assertRaisesRegex(RuntimeError, "still listening"):
                self.run_seed(owui_port=listener.getsockname()[1])
            self.assertEqual(self.dump(), before)

    def test_qc_alias_uses_same_tier_policy(self):
        self.config.update(tier="pro", model_alias="bomai-qc-pro")
        self.run_seed()
        self.assertEqual(self.value("ui.default_models"), "bomai-qc-pro")

    def test_visible_search_default_preserves_other_model_defaults(self):
        with self.db() as db:
            db.execute("INSERT INTO model(id,user_id,name,params,meta,is_active) VALUES (?,?,?,?,?,1)",
                       ("bomai-safe", "admin-1", "BOM AI Light", "{}", json.dumps({"bomai_managed": True, "defaultFeatureIds": ["code_interpreter"], "capabilities": {"vision": False}})))
        self.run_seed()
        with self.db() as db:
            meta = json.loads(db.execute("SELECT meta FROM model WHERE id='bomai-safe'").fetchone()[0])
        self.assertEqual(meta["defaultFeatureIds"], ["code_interpreter", "web_search"])
        self.assertFalse(meta["capabilities"]["vision"])
        self.assertTrue(meta["capabilities"]["web_search"])
        self.assertEqual(self.run_seed()["changed_rows"], 0)

    def test_missing_db_never_created(self):
        missing = self.path.with_name("missing.db")
        with self.assertRaises(FileNotFoundError):
            seed.seed(missing, self.config, "0.12.5", offline_confirmed=True)
        self.assertFalse(missing.exists())

    def test_disabled_persistence_or_reset_refused(self):
        for env in ({"ENABLE_PERSISTENT_CONFIG": "false"}, {"RESET_CONFIG_ON_START": "true"}):
            with patch.dict(os.environ, env):
                with self.assertRaises(ValueError):
                    seed.seed(self.path, self.config, "0.12.5", offline_confirmed=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
