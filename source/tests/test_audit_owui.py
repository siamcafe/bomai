"""Audit policy checks; these do not claim an authenticated server was exercised."""
import importlib.util
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from contextlib import closing
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / "runtime" / "audit_owui.py"
SPEC = importlib.util.spec_from_file_location("audit_owui", SOURCE)
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


class SearchAuditTests(unittest.TestCase):
    def evaluate(self, effective="always", saved=None, default="always", features=None):
        return audit.evaluate_search(
            {"webSearch": default}, {"webSearch": effective}, saved or {},
            {"defaultFeatureIds": ["web_search"] if features is None else features},
        )

    def test_fresh_default_requires_effective_always(self):
        detail, checks = self.evaluate()
        self.assertTrue(all(checks.values()))
        self.assertEqual(detail["source"], "global_default")
        self.assertFalse(detail["explicit_override"])
        _, checks = self.evaluate(effective="never")
        self.assertFalse(checks["effective_search_matches_saved_or_default"])

    def test_intentional_never_is_preserved_and_reported(self):
        detail, checks = self.evaluate(effective="never", saved={"webSearch": "never"})
        self.assertTrue(all(checks.values()))
        self.assertEqual(detail["source"], "saved_user")
        self.assertTrue(detail["explicit_override"])
        self.assertEqual(detail["expected_effective"], "never")

    def test_explicit_nullable_upstream_default_is_preserved(self):
        detail, checks = self.evaluate(effective=None, saved={"webSearch": None})
        self.assertTrue(all(checks.values()))
        self.assertTrue(detail["explicit_override"])

    def test_saved_always_is_not_reported_as_override(self):
        detail, checks = self.evaluate(saved={"webSearch": "always"})
        self.assertTrue(all(checks.values()))
        self.assertFalse(detail["explicit_override"])

    def test_wrong_global_default_fails_even_with_personal_override(self):
        _, checks = self.evaluate(effective="never", saved={"webSearch": "never"}, default="never")
        self.assertTrue(checks["effective_search_matches_saved_or_default"])
        self.assertFalse(checks["global_web_search_default_on"])
        self.assertFalse(all(checks.values()))

    def test_override_does_not_allow_missing_model_default(self):
        _, checks = self.evaluate(effective="never", saved={"webSearch": "never"}, features=[])
        self.assertFalse(checks["visible_search_default_configured"])

    def test_effective_value_must_respect_saved_preference(self):
        _, checks = self.evaluate(effective="always", saved={"webSearch": "never"})
        self.assertFalse(checks["effective_search_matches_saved_or_default"])


class AuditReadTests(unittest.TestCase):
    def read_fixture(self, raw_settings, effective):
        scratch = Path(__file__).resolve().parents[3] / "work"
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as directory:
            folder = Path(directory)
            db_path = folder / "webui.db"
            with closing(sqlite3.connect(db_path)) as db, db:
                db.executescript("""
                    CREATE TABLE user(id TEXT,role TEXT,created_at INTEGER,settings TEXT);
                    CREATE TABLE config(key TEXT,value TEXT);
                    CREATE TABLE model(id TEXT,params TEXT,meta TEXT);
                """)
                db.execute("INSERT INTO user VALUES ('fixture-admin','admin',0,?)", (raw_settings,))
                db.execute("INSERT INTO config VALUES ('ui.default_models',?)", (json.dumps("bomai-safe"),))
                db.execute("INSERT INTO model VALUES (?,?,?)", ("bomai-safe", '{}', '{"defaultFeatureIds":["web_search"]}'))
            secret = folder / "secret"
            secret.write_text("test-fixture-key-not-a-real-server", encoding="utf-8")
            fixture = {
                "/api/config": {"ui": {"default_interface_settings": {"webSearch": "always"}}},
                "/api/v1/configs/banners": [],
                "/api/v1/users/user/settings": {"ui": {"webSearch": effective}},
            }
            def open_request(request, timeout):
                self.assertEqual(request.get_method(), "GET")
                self.assertEqual(request.host, "127.0.0.1:8080")
                return io.BytesIO(json.dumps(fixture[request.selector]).encode())
            with patch.object(audit.urllib.request, "build_opener") as factory:
                factory.return_value.open.side_effect = open_request
                return audit.audit(db_path, secret, "http://127.0.0.1:8080")

    def test_sql_json_null_settings_use_global_default(self):
        result = self.read_fixture("null", "always")
        self.assertEqual(result["search_preference"]["source"], "global_default")
        self.assertTrue(result["checks"]["effective_search_matches_saved_or_default"])

    def test_saved_db_override_is_read_and_retained(self):
        result = self.read_fixture('{"ui":{"webSearch":"never"}}', "never")
        self.assertTrue(result["search_preference"]["explicit_override"])
        self.assertEqual(result["search_preference"]["expected_effective"], "never")
        self.assertTrue(result["checks"]["effective_search_matches_saved_or_default"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
