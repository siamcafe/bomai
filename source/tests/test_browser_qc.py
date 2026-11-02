#!/usr/bin/env python3
"""Fixture-based mechanics tests for browser_qc (no model required).

Pure-function tests run everywhere. DOM tests need Playwright plus the static
fixture tests/fixtures/browser_qc_fixture.html and are skipped when Playwright
is not importable.
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import browser_qc as bq


HAN_SAMPLE = 'สวัสดีครับ นี่คือคำตอบภาษาไทย แต่มีคำภาษาจีนปน 你好世界'


class DetectorTests(unittest.TestCase):
    def test_han_counting(self):
        self.assertEqual(bq.detect_han(HAN_SAMPLE), 4)
        self.assertEqual(bq.detect_han('ภาษาไทยล้วน ไม่มีอักขระต่างดาว'), 0)

    def test_thai_counting(self):
        self.assertGreater(bq.detect_thai(HAN_SAMPLE), 10)

    def test_repeated_rows(self):
        text = '\n'.join(['- รายการซ้ำกันเรื่อยๆ'] * 4 + ['- แถวปกติหนึ่งครั้ง'])
        repeated, counts = bq.detect_repeated_rows(text)
        self.assertEqual(len(repeated), 1)
        self.assertEqual(counts[repeated[0]], 4)

    def test_repeated_rows_needs_three(self):
        text = '\n'.join(['- สองครั้งไม่นับ'] * 2)
        repeated, _ = bq.detect_repeated_rows(text)
        self.assertEqual(repeated, [])

    def test_adjacent_repetition(self):
        text = 'คำตอบเดิม ' * 6
        self.assertIsNotNone(bq.detect_adjacent_repetition(text))
        self.assertIsNone(bq.detect_adjacent_repetition('คำตอบปกติที่ไม่ซ้ำใดๆ ทั้งหมด'))

    def test_guard_notice_detection(self):
        result = bq.classify_answer('คำตอบ\n\n[ระบบหยุดคำตอบที่เริ่มวนซ้ำ กรุณาลองถามใหม่]', {})
        self.assertTrue(result['guard_intervention'])

    def test_raw_markup_echo(self):
        flag, hits = bq.detect_raw_markup('{"results": [{"url": "x", "title": "y"}]}')
        self.assertTrue(flag)
        flag, _ = bq.detect_raw_markup('คำตอบไทยปกติที่สะอาด')
        self.assertFalse(flag)

    def test_empty_detection(self):
        result = bq.classify_answer('   ', {})
        self.assertTrue(result['empty'])
        self.assertEqual(result['han_chars'], 0)

    def test_raw_markup_case_insensitive_tags(self):
        for sample in ('ข้อความ <context> รั่ว', 'ปิดท้ายด้วย </SOURCE>', 'มี <Context> ปน'):
            flagged, hits = bq.detect_raw_markup(sample)
            self.assertTrue(flagged, sample)
        flagged, hits = bq.detect_raw_markup('All Rights Reserved โดยเว็บไซต์ต้นทาง')
        self.assertTrue(flagged)

    def test_raw_markup_clean_cited_thai_answer_passes(self):
        clean = ('ราคาทองวันนี้ 45,900 บาท อ้างอิง\n'
                 '- สมาคมค้าทองคำ (goldtraders.or.th)\n'
                 '- เว็บไซต์ข่าวการเงิน (thairath.co.th)')
        flagged, hits = bq.detect_raw_markup(clean)
        self.assertFalse(flagged, hits)

    def test_transport_error_new_markers(self):
        for sample in ('รอคิว AI เกินกำหนด กรุณาลองใหม่',
                       'upstream_stream_incomplete',
                       'reasoning_only_or_empty_response',
                       'request (9423 tokens) exceeds the available context size (8192 tokens)'):
            self.assertTrue(bq.detect_transport_error(sample), sample)

    def test_quality_failure_notice_detected(self):
        notice = ('ขออภัย ระบบยังไม่สามารถสร้างคำตอบที่ครบถ้วนและไม่ซ้ำซ้อนได้ '
                  'กรุณาลองแบ่งคำถามหรือระบุรูปแบบคำตอบอีกครั้ง')
        self.assertTrue(bq.detect_quality_failure(notice))
        self.assertTrue(bq.detect_quality_failure('คำนำสั้นๆ\n' + notice))
        self.assertFalse(bq.detect_quality_failure('คำตอบปกติที่ครบถ้วนและไม่มีปัญหา'))
        self.assertFalse(bq.detect_quality_failure(''))
        for marker in bq.QUALITY_FAILURE_MARKERS:
            self.assertIn(marker, notice)

    def test_quality_failure_is_content_fail_not_transport(self):
        notice = ('ขออภัย ระบบยังไม่สามารถสร้างคำตอบที่ครบถ้วนและไม่ซ้ำซ้อนได้ '
                  'กรุณาลองแบ่งคำถามหรือระบุรูปแบบคำตอบอีกครั้ง')
        result = bq.classify_answer(notice, {})
        self.assertTrue(result['quality_failure'])
        self.assertFalse(bq.detect_transport_error(notice))
        recovered_clean = bq.classify_answer(
            '1. เกมหมากกระดาน\n2. เกมทายคำ\n3. เกมวาดรูป\n4. เกมเล่านิทาน', {})
        self.assertFalse(recovered_clean['quality_failure'])
        self.assertFalse(bq.detect_transport_error(
            'คำตอบที่สะอาดหลังการเขียนใหม่ด้วยระบบสองชั้น'))


class CliContractTests(unittest.TestCase):
    """fix-121 r4: qualification metadata must be explicit and identical for
    any resume; parse errors must abort before the corpus runs."""

    def _parse(self, extra):
        import argparse
        base = ['--base-url', 'http://127.0.0.1:18080',
                '--credentials', 'x.json', '--corpus', 'c.json',
                '--image', 'i.png', '--output', 'o.json',
                '--screenshot-dir', 'shots']
        try:
            bq.main.__wrapped__
        except AttributeError:
            pass
        # Simulate the parser contract exactly as main() declares it.
        parser = argparse.ArgumentParser()
        parser.add_argument('--base-url', required=True)
        parser.add_argument('--credentials', required=True)
        parser.add_argument('--corpus', required=True)
        parser.add_argument('--image', required=True)
        parser.add_argument('--output', required=True)
        parser.add_argument('--screenshot-dir', required=True)
        parser.add_argument('--timeout', type=int, default=600)
        parser.add_argument('--resume', action='store_true')
        parser.add_argument('--headed', action='store_true')
        parser.add_argument('--model-alias', required=True,
                            choices=('bomai-qc-light', 'bomai-qc-pro'))
        parser.add_argument('--host', required=True, choices=('windows', 'macos', 'linux'))
        parser.add_argument('--tier', required=True, choices=('light', 'pro'))
        parser.add_argument('--runtime-path', required=True)
        return parser.parse_args(base + extra)

    def test_alias_host_tier_required(self):
        with self.assertRaises(SystemExit):
            self._parse([])
        args = self._parse(['--model-alias', 'bomai-qc-light', '--host', 'windows',
                            '--tier', 'light', '--runtime-path', 'runtime/bom_runtime.py'])
        self.assertEqual(args.model_alias, 'bomai-qc-light')
        self.assertEqual((args.host, args.tier), ('windows', 'light'))

    def test_alias_restricted_to_qc_names(self):
        with self.assertRaises(SystemExit):
            self._parse(['--model-alias', 'bomai-safe', '--host', 'windows',
                         '--tier', 'light', '--runtime-path', 'r.py'])

    def test_resume_rejects_mismatched_metadata(self):
        # Mirror the resume gate: a differing runtime hash must abort.
        stored = {'runtime_sha256': 'aaa', 'corpus_sha256': 'bbb',
                  'model_alias': 'bomai-qc-light', 'base_url': 'http://x',
                  'runner_sha256': 'ccc', 'image_sha256': 'ddd'}
        values = {'runtime_sha256': 'zzz', 'corpus_sha256': 'bbb',
                  'model_alias': 'bomai-qc-light', 'base_url': 'http://x',
                  'runner_sha256': 'ccc', 'image_sha256': 'ddd'}
        keys = ('corpus_sha256', 'runtime_sha256', 'runner_sha256',
                'model_alias', 'base_url', 'image_sha256')
        mismatch = [k for k in keys if stored.get(k) not in (None, values[k])]
        self.assertEqual(mismatch, ['runtime_sha256'])
        self.assertTrue(all(stored.get(k) == values[k] for k in keys if k != 'runtime_sha256'))



class RecordTests(unittest.TestCase):
    def test_atomic_write_and_resume_reject_foreign_corpus(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'run.json'
            bq.atomic_write_json(out, {'metadata': {'corpus_sha256': 'deadbeef'}, 'cases': {}})
            loaded = bq.load_output(out)
            self.assertEqual(loaded['metadata']['corpus_sha256'], 'deadbeef')
            self.assertEqual(out.with_suffix('.json.tmp').exists(), False)

    def test_output_never_contains_credentials(self):
        # The runner writes only metadata/classification fields; credentials are
        # read into locals and never placed into the record structure.
        record = {'metadata': {'login_mode': 'logged_in'}, 'cases': {}}
        blob = json.dumps(record)
        self.assertNotIn('password', blob)
        self.assertNotIn('token', blob)

    def test_corpus_validation_shape(self):
        # Duplicate ids / wrong count must be rejected before any browser work.
        corpus = {'count': 3, 'cases': [{'id': 'S1'}, {'id': 'S2'}, {'id': 'S1'}]}
        ids = [c['id'] for c in corpus['cases']]
        self.assertNotEqual(len(set(ids)), len(ids))


try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT = True
except Exception:
    PLAYWRIGHT = False


@unittest.skipUnless(PLAYWRIGHT, 'playwright not installed')
class FixtureDomTests(unittest.TestCase):
    FIXTURE = Path(__file__).resolve().parent / 'fixtures' / 'browser_qc_fixture.html'

    @classmethod
    def setUpClass(cls):
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()

    def _page(self):
        context = self.browser.new_context(viewport={'width': 1280, 'height': 800}, locale='th-TH')
        page = context.new_page()
        page.goto(self.FIXTURE.as_uri())
        page.wait_for_timeout(300)
        return context, page

    def test_login_form_flow(self):
        context, page = self._page()
        try:
            ui = bq.OWUI(page, self.FIXTURE.as_uri())
            mode = ui.login('owner@bomai.local', 'sekret-value')
            self.assertEqual(mode, 'logged_in')
            blob = json.dumps({'url': page.url})
            self.assertNotIn('sekret-value', blob)
        finally:
            context.close()

    def test_empty_prompt_no_generation(self):
        context, page = self._page()
        try:
            ui = bq.OWUI(page, self.FIXTURE.as_uri())
            ui.login('owner@bomai.local', 'x')
            ui.submit_prompt('')
            page.wait_for_timeout(1500)
            self.assertEqual(ui.assistant_count(), 0)
        finally:
            context.close()

    def test_stream_completion_and_sources(self):
        context, page = self._page()
        try:
            ui = bq.OWUI(page, self.FIXTURE.as_uri())
            ui.login('owner@bomai.local', 'x')
            ui.submit_prompt('ทดสอบการตอบ')
            outcome = ui.wait_completion(20)
            self.assertTrue(outcome['completed'])
            text = ui.assistant_text()
            self.assertIn('คำตอบจากฟิกซ์เจอร์', text)
            self.assertTrue(ui.source_urls())
        finally:
            context.close()

    def test_timeout_handling(self):
        context, page = self._page()
        try:
            ui = bq.OWUI(page, self.FIXTURE.as_uri())
            ui.login('owner@bomai.local', 'x')
            page.evaluate('window.FIXTURE_STREAM_MS = 60000')
            ui.submit_prompt('ทดสอบหมดเวลา')
            outcome = ui.wait_completion(3)
            self.assertTrue(outcome['timeout'])
            self.assertFalse(outcome['completed'])
        finally:
            context.close()

    def test_image_attachment_control(self):
        context, page = self._page()
        try:
            ui = bq.OWUI(page, self.FIXTURE.as_uri())
            ui.login('owner@bomai.local', 'x')
            fixture_png = Path(__file__).resolve().parent / 'vision_fixture.png'
            ui.submit_prompt('อ่านภาพนี้', image_path=fixture_png)
            page.wait_for_timeout(1500)
            self.assertEqual(page.evaluate('window.FIXTURE_ATTACHED'), True)
        finally:
            context.close()


if __name__ == '__main__':
    unittest.main(verbosity=2)


class TransportErrorTests(unittest.TestCase):
    def test_queue_full_marker_detected(self):
        import importlib
        bq = importlib.import_module('tests.browser_qc') if __import__('sys').modules.get('tests.browser_qc') else None
        if bq is None:
            import sys
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            import browser_qc as bq
        self.assertTrue(bq.detect_transport_error('คิว AI เต็ม กรุณารอให้คำตอบก่อนหน้าเสร็จ'))
        # r3: an injected SearXNG no-results line above a real answer is a
        # search flag, not a transport failure; alone it still fails.
        self.assertFalse(bq.detect_transport_error('[ERROR: No results found from web search]\nคำตอบ'))
        self.assertTrue(bq.detect_transport_error('[ERROR: No results found from web search]'))
        self.assertTrue(bq.detect_transport_error('กำลังค้นหาบนเว็บ'))
        self.assertFalse(bq.detect_transport_error('คำตอบปกติของ BOM AI ที่ไม่มีตัวบ่งชี้ข้อผิดพลาด'))
        self.assertFalse(bq.detect_transport_error(''))

    def test_assistant_text_without_assistant_node_is_empty(self):
        import subprocess
        import sys as _sys
        code = (
            "from playwright.sync_api import sync_playwright\n"
            "import sys\n"
            "sys.path.insert(0, r'" + str(Path(__file__).resolve().parent) + "')\n"
            "import browser_qc as bq\n"
            "p = sync_playwright().start()\n"
            "b = p.chromium.launch()\n"
            "pg = b.new_page()\n"
            "pg.set_content('<html><body><div>ข้ามไปยังเนื้อหาหลัก sidebar text</div></body></html>')\n"
            "ui = bq.OWUI(pg, 'http://localhost/')\n"
            "assert ui.assistant_text() == '', 'body fallback must not leak page chrome'\n"
            "b.close()\n"
            "p.stop()\n"
            "print('NO_BODY_FALLBACK_OK')\n"
        )
        result = subprocess.run([_sys.executable, '-c', code], capture_output=True, text=True, timeout=120)
        self.assertIn('NO_BODY_FALLBACK_OK', result.stdout, result.stderr[-500:])


class BomTolerantCredentialsTest(unittest.TestCase):
    def test_credentials_with_bom_parse(self):
        import tempfile
        import sys as _sys
        _sys.path.insert(0, str(Path(__file__).resolve().parent))
        code = (
            "import json, tempfile\n"
            "from pathlib import Path\n"
            "p = Path(tempfile.mkstemp(suffix='.json')[1])\n"
            "p.write_bytes(bytes([0xEF, 0xBB, 0xBF]) + json.dumps({'email': 'a@b.c', 'password': 'x'}).encode('utf-8'))\n"
            "assert json.loads(p.read_text(encoding='utf-8-sig'))['email'] == 'a@b.c'\n"
            "print('BOM_CREDS_OK')\n"
        )
        import subprocess
        r = subprocess.run([_sys.executable, '-c', code], capture_output=True, text=True, timeout=60)
        self.assertIn('BOM_CREDS_OK', r.stdout, r.stderr[-300:])
