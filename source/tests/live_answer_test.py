#!/usr/bin/env python3
"""F-LIVE: deterministic live-data answer validation; no model-quality claims."""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runtime'))
from bom_runtime import (is_live_query, validate_live_answer, live_data_fallback,
                         ValidationResult, SYSTEM_PROMPT)

NOW = datetime(2026, 11, 1, 13, 45, 0, tzinfo=timezone(timedelta(hours=7)))


class LiveQueryTests(unittest.TestCase):
    def test_kind_detection(self):
        cases = [
            ('ราคาทองวันนี้เท่าไหร่', 'gold'),
            ('ทองคำแพงขึ้นไหม', 'gold'),
            ('หุ้นปตท. ราคาล่าสุด', 'stock'),
            ('ค่าเงินดอลลาร์วันนี้', 'fx'),
            ('อัตราแลกเปลี่ยน usdthb', 'fx'),
            ('ข่าวล่าสุดวันนี้มีอะไรบ้าง', 'news'),
            ('เขียนโค้ด Python หน่อย', None),
            ('สอนทำผัดไทย', None),
        ]
        for question, expected in cases:
            self.assertEqual(is_live_query([{'role': 'user', 'content': question}]),
                             expected, question)

    def test_source_message_not_treated_as_question(self):
        messages = [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': 'ข้อมูลผลค้นหา ราคาทอง 45,000 บาท'},
            {'role': 'user', 'content': 'ช่วยสรุปเรื่องนี้สั้นๆ'},
        ]
        self.assertIsNone(is_live_query(messages))


class ValidationRejectTests(unittest.TestCase):
    def check(self, kind, contexts, answer):
        return validate_live_answer(kind, contexts, answer, NOW)

    def test_stale_2024_wise_fx_rejected(self):
        contexts = ['Wise USD/THB 35.20 อัตรา 2024-05-04 https://wise.com/usd-thb',
                    'อัตราแลกเปลี่ยนล่าสุด 35.25 บาท 2024-05-04 https://www.xe.com/xhr/usd-thb']
        result = self.check('fx', contexts, 'ค่าเงินดอลลาร์วันนี้ 35.20 บาท (Wise 2024-05-04) https://wise.com/usd-thb')
        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'stale_source')

    def test_stale_2024_ptt_rejected(self):
        contexts = ['PTT ราคาหุ้น 33.40 บาท 2024-05-10 https://www.set.or.th/th/market/stock/ptt',
                    'PTT 33.45 บาท 2024-05-10 https://www.finnomena.com/stock/ptt']
        result = self.check('stock', contexts, 'หุ้นปตท. ปิดที่ 33.40 บาท (2024-05-10) อ้างอิง set.or.th')
        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'stale_source')

    def test_undated_homepage_news_rejected(self):
        contexts = ['ข่าวหน้าแรก https://www.bangkokbiznews.com/ ไม่มีวันที่']
        result = self.check('news', contexts, 'ตลาดหุ้นไทยวันนี้บวกแรง ดูข่าวได้ที่ https://www.bangkokbiznews.com/')
        self.assertFalse(result.ok)
        self.assertIn(result.reason, ('no_dated_source', 'homepage_or_single_source'))

    def test_gold_values_labeled_ptt_rejected(self):
        contexts = ['ทองคำ 96.5% ราคา 45,900 บาท 2026-11-01 https://goldtraders.or.th/today',
                    'สมาคมค้าทองคำ 45,950 2026-11-01 https://www.ylg.co.th/gold-price']
        answer = 'ราคาปิดวันนี้อยู่ที่ 45,900 บาท (ทองคำ 96.5%) ตามราคาสมาคมค้าทองคำ'
        result = self.check('stock', contexts, answer)
        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'asset_identity_mismatch')

    def test_all_zero_values_rejected(self):
        contexts = ['gold spot 0.00 USD https://www.kitco.com/price/precious-metals',
                    'USDTHB 0 https://www.investing.com/currencies/usd-thb']
        result = self.check('gold', contexts, 'ราคาทองวันนี้ 0 บาท 0.00 ดอลลาร์ (2026-11-01)')
        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'no_numeric_value')

    def test_ptt_334_vs_334_disagreement_rejected(self):
        contexts = ['PTT ราคาล่าสุด 33.4 บาท 2026-11-01 https://www.set.or.th/th/market/stock/ptt',
                    'บล.กสิกร ประเมิน PTT 33.45 บาท 2026-11-01 https://research.kasikornbank.com/ptt']
        answer = 'หุ้นปตท. วันนี้ราคา 334 บาท (2026-11-01) ตามตลาดหลักทรัพย์'
        result = self.check('stock', contexts, answer)
        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'cross_source_disagreement')

    def test_future_timestamp_rejected(self):
        contexts = ['ทองคำ 45,900 บาท 2026-11-03 https://goldtraders.or.th/today',
                    'ราคาทอง 45,950 บาท 2026-11-03 https://www.ylg.co.th/gold-price']
        result = self.check('gold', contexts, 'ราคาทองวันนี้ 45,900 บาท (2026-11-03)')
        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'future_timestamp')

    def test_single_source_numeric_rejected(self):
        contexts = ['ทองคำ 45,900 บาท 2026-11-01 https://goldtraders.or.th/today']
        result = self.check('gold', contexts, 'ราคาทองวันนี้ 45,900 บาท (2026-11-01) ที่ https://goldtraders.or.th/today')
        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'single_source')

    def test_stale_news_rejected(self):
        contexts = ['ข่าวเศรษฐกิจ 2026-10-01 https://www.bangkokbiznews.com/economy/1234',
                    'วิเคราะห์ตลาด 2026-10-01 https://www.thairath.co.th/money/5678']
        result = self.check('news', contexts, 'ตลาดหุ้นไทยปรับตัวขึ้น (ข่าว 2026-10-01)')
        self.assertFalse(result.ok)
        self.assertEqual(result.reason, 'stale_news')


class ValidationAcceptTests(unittest.TestCase):
    def test_dated_cited_consistent_gold_accepted(self):
        contexts = ['สมาคมค้าทองคำ ทองคำแท่ง 96.5% ราคา 45,900 บาท 2026-11-01 https://goldtraders.or.th/today',
                    'ราคาทองล่าสุด 45,950 บาท 2026-11-01 https://www.ylg.co.th/gold-price']
        answer = ('ราคาทองคำแท่ง 96.5% วันนี้ (2026-11-01) อยู่ที่ประมาณ 45,900 บาท '
                  'อ้างอิง https://goldtraders.or.th/today และ https://www.ylg.co.th/gold-price')
        result = validate_live_answer('gold', contexts, answer, NOW)
        self.assertTrue(result.ok, result.reason)
        self.assertGreaterEqual(len(result.sources), 2)

    def test_dated_cited_consistent_ptt_accepted(self):
        contexts = ['PTT ราคาปิด 33.40 บาท 2026-11-01 https://www.set.or.th/th/market/stock/ptt',
                    'บล.กสิกร PTT 33.45 บาท 2026-11-01 https://research.kasikornbank.com/ptt']
        answer = 'หุ้นปตท. (PTT) ปิดวันนี้ 2026-11-01 ที่ 33.40 บาท ตาม set.or.th และ kasikornbank'
        result = validate_live_answer('stock', contexts, answer, NOW)
        self.assertTrue(result.ok, result.reason)

    def test_honest_fallback_has_no_fabricated_numbers(self):
        text = live_data_fallback('gold', 'stale_source',
                                  ['https://goldtraders.or.th/today'])
        self.assertIn('ขออภัย', text)
        self.assertNotIn('45,900', text)
        self.assertNotIn('2024', text)
        self.assertIn('https://goldtraders.or.th/today', text)


class GatewayLiveTests(unittest.TestCase):
    """One non-stream gateway integration: a live query answer without valid
    citations is replaced by the honest fallback before display."""
    @classmethod
    def setUpClass(cls):
        import threading, tempfile
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
        from bom_runtime import RuntimeServer

        class StaticOllama(BaseHTTPRequestHandler):
            protocol_version = 'HTTP/1.1'
            def log_message(self, *_): pass
            def do_GET(self):
                obj = {'version': '0.40.13'} if self.path == '/api/version' else {'models': [{'name': 'bomai-safe:latest'}]}
                data = json.dumps(obj).encode()
                self.send_response(200); self.send_header('Content-Length', str(len(data))); self.end_headers(); self.wfile.write(data)
            def do_POST(self):
                self.rfile.read(int(self.headers['Content-Length']))
                text = 'ราคาทองวันนี้ 45,900 บาท ตามที่เห็นในเว็บ'
                data = json.dumps({'model': 'bomai-safe', 'message': {'role': 'assistant', 'content': text},
                                   'done': True, 'done_reason': 'stop'}, ensure_ascii=False).encode()
                self.send_response(200); self.send_header('Content-Length', str(len(data))); self.end_headers(); self.wfile.write(data)

        cls.tmp = tempfile.TemporaryDirectory()
        cls.ollama = ThreadingHTTPServer(('127.0.0.1', 0), StaticOllama)
        import threading as _t
        cls.thread = _t.Thread(target=cls.ollama.serve_forever, daemon=True); cls.thread.start()
        cls.key = 'live-test-key-' + 'a' * 24
        cls.gateway = RuntimeServer(('127.0.0.1', 0), f'http://127.0.0.1:{cls.ollama.server_port}',
            catalog=Path(__file__).resolve().parents[1] / 'runtime' / 'models.json',
            log=str(Path(cls.tmp.name) / 'events.jsonl'), gateway_key=cls.key, model_alias='bomai-safe')
        cls.gt = _t.Thread(target=cls.gateway.serve_forever, daemon=True); cls.gt.start()
        cls.url = f'http://127.0.0.1:{cls.gateway.server_port}'
        cls.threading = _t

    @classmethod
    def tearDownClass(cls):
        cls.gateway.shutdown(); cls.gateway.server_close(); cls.ollama.shutdown(); cls.ollama.server_close(); cls.tmp.cleanup()

    def test_uncited_live_answer_replaced_by_fallback(self):
        import urllib.request
        payload = {'model': 'bomai-safe', 'stream': False, 'messages': [
            {'role': 'user', 'content': 'ราคาทองวันนี้เท่าไหร่'}]}
        req = urllib.request.Request(self.url + '/api/chat',
                                     data=json.dumps(payload, ensure_ascii=False).encode(),
                                     headers={'Content-Type': 'application/json',
                                              'Authorization': 'Bearer ' + self.key})
        with urllib.request.urlopen(req, timeout=20) as response:
            result = json.load(response)
        self.assertIn('ขออภัย', result['message']['content'])
        self.assertFalse(result['bomai_live']['validated'])
        self.assertNotIn('45,900', result['message']['content'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
