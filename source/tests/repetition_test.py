#!/usr/bin/env python3
"""Offline detector and real HTTP gateway contract tests; no model-quality claims."""
import json
import re
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runtime'))
from bom_runtime import RepetitionGate, ResponseFilter, RuntimeServer, CONFIG_G, SYSTEM_PROMPT, SOURCE_GUIDANCE, ensure_system, openai_request, native_request, cap_source_context, context_overflow, is_source_message, has_vision, prepare_context, reduce_source_context, CONTEXT_CAPACITY_NOTICE, MAX_SOURCE_CHARS, MAX_RETRIEVAL_CHARS, CONTEXT_REDUCTIONS, CONTEXT_OVERFLOW_RE, INFERENCE_QUEUE_TIMEOUT, MAX_INFERENCE, MAX_QUEUED, MAX_EMPTY_STREAM_RETRIES, STREAM_INCOMPLETE_NOTICE

PHRASE = 'ดินน้ำมัน หรือดินสอ หรือเทียน หรือสีเทียน หรือ'

class GateTests(unittest.TestCase):
    def run_chunks(self, text, size):
        gate = RepetitionGate()
        output = ''.join(gate.feed(text[i:i+size]) for i in range(0, len(text), size))
        output += gate.feed('', final=True)
        return gate, output

    def test_thai_owner_pattern_all_chunk_sizes(self):
        for size in (1, 2, 3, 7, 13, 41, 4096):
            with self.subTest(size=size):
                gate, output = self.run_chunks('เริ่มต้นรายการ: ' + PHRASE * 30, size)
                self.assertTrue(gate.triggered)
                self.assertIn(RepetitionGate.NOTICE, output)
                self.assertLessEqual(output.count(PHRASE), 2)
                self.assertLess(len(output), 300)

    def test_whitespace_normalization(self):
        text = 'red green blue yellow ' + 'red  green\nblue yellow ' + 'red green\tblue yellow ' + 'red green blue yellow '
        gate, _ = self.run_chunks(text, 1)
        self.assertTrue(gate.triggered)

    def test_two_repetitions_not_a_loop(self):
        text = PHRASE * 2
        gate, output = self.run_chunks(text, 3)
        self.assertFalse(gate.triggered)
        self.assertEqual(output, text)

    def test_non_adjacent_repeated_list_words_preserved(self):
        text = '\n'.join(f'{i}. อุปกรณ์วาดภาพชนิด {i} ใช้สำหรับงานหมายเลข {i*i}' for i in range(1,21))
        gate, output = self.run_chunks(text, 7)
        self.assertFalse(gate.triggered)
        self.assertEqual(output, text)

    def test_real_i9_baseline_numbered_duplicate_rows(self):
        fixture=json.loads((Path(__file__).parent/'fixtures'/'i9-light-owner-list.json').read_text(encoding='utf-8'))
        for size in (1,7,4096):
            gate,output=self.run_chunks(fixture['response'],size)
            self.assertTrue(gate.triggered)
            self.assertEqual(gate.metadata()['reason'],'repeated_list_row')
            # FIX 20261101 guard r2: threshold 3 -> 4, the third duplicate survives
            self.assertIn('7. **ดินสอสีน้ำมัน**',output)
            self.assertNotIn('8. **ดินสอสีน้ำมัน**',output)

    def test_duplicate_list_final_line_without_newline(self):
        row='อุปกรณ์ชนิดเดิมใช้สำหรับฝึกระบายสี'
        text='1. '+row+'\n2. รายการอื่นที่แตกต่างอย่างชัดเจน\n3. '+row+'\n4. '+row
        gate,output=self.run_chunks(text,3)
        # three copies = intentional-repeat control territory, not cut (FIX 20261101)
        self.assertFalse(gate.triggered)
        self.assertEqual(output,text)

    def test_four_duplicate_list_rows_cut(self):
        row='อุปกรณ์ชนิดเดิมใช้สำหรับฝึกระบายสี'
        text='1. '+row+'\n2. รายการอื่นที่แตกต่างอย่างชัดเจน\n3. '+row+'\n4. '+row+'\n5. '+row
        gate,output=self.run_chunks(text,3)
        self.assertTrue(gate.triggered)
        self.assertEqual(gate.reason,'repeated_list_row')
        self.assertIn('3. '+row,output)
        self.assertNotIn('5. '+row,output)

    def test_repeated_rows_in_code_exempt(self):
        row='- ตัวอย่างข้อมูลทดสอบที่จงใจให้ซ้ำกัน\n'
        text='```text\n'+row*4+'```\n'
        gate,output=self.run_chunks(text,2)
        self.assertFalse(gate.triggered)
        self.assertEqual(text,output)

    def test_final_native_chunk_omits_content(self):
        filt=ResponseFilter(True)
        first=filt.clean({'message':{'content':'คำตอบที่ครบถ้วนและมีภาษาไทย'}})
        last=filt.finish(filt.clean({'done':True},final=True))
        self.assertEqual(first['message']['content']+last['message']['content'],'คำตอบที่ครบถ้วนและมีภาษาไทย')

    def test_code_fence_preserves_repeated_source(self):
        text = 'ตัวอย่างโค้ด:\n```python\n' + "print('สวัสดีชาวโลก')\n" * 20 + '```\nจบตัวอย่าง'
        gate, output = self.run_chunks(text, 1)
        self.assertFalse(gate.triggered)
        self.assertEqual(output, text)

    def test_short_laughter_not_a_phrase_loop(self):
        text = 'ฮ่า' * 100
        gate, output = self.run_chunks(text, 3)
        self.assertFalse(gate.triggered)
        self.assertEqual(output, text)

    def test_normal_long_unicode_roundtrip(self):
        text = '\n'.join(f'บรรทัดที่ {i}: ค่า {i*i} 😊 มิตรภาพและความคิดสร้างสรรค์' for i in range(200))
        gate, output = self.run_chunks(text, 11)
        self.assertFalse(gate.triggered)
        self.assertEqual(output, text)

    def test_empty_completion(self):
        gate, output = self.run_chunks('', 1)
        self.assertFalse(gate.triggered)
        self.assertEqual(output, '')

    def test_bounded_response(self):
        gate = RepetitionGate()
        with self.assertRaises(ValueError):
            gate.feed(' ' * (RepetitionGate.MAX_VISIBLE + 1))

    def test_intentional_three_repeat_passes_s041_control(self):
        # FIX 20261101 S041 regression fixture: a user-requested exact 3x
        # phrase repeat is intentional compliance, not a runaway loop.
        text = 'วันนี้อากาศดีและฉันมีความสุข' * 3
        gate, output = self.run_chunks(text, 5)
        self.assertFalse(gate.triggered)
        self.assertEqual(output, text)

    def test_intentional_prose_repeat_disclosed_not_silent(self):
        gate, output = self.run_chunks('วันนี้อากาศดีและฉันมีความสุข' * 4, 5)
        self.assertTrue(gate.triggered)
        self.assertIn('ระบบหยุดคำตอบ', output)

    def test_reasoning_filtered_before_gate(self):
        filt = ResponseFilter(True)
        result = filt.finish(filt.clean({'message': {'content': '<think>' + PHRASE * 4 + '</think>คำตอบปกติ'}}, final=True))
        self.assertEqual(result['message']['content'], 'คำตอบปกติ')
        self.assertIsNone(filt.intervention)

    def test_locked_options_and_persona(self):
        source = {'model': 'bomai-safe', 'messages': [{'role':'system','content':'ข้อมูลจากผลค้นหา'}, {'role':'user','content':'สวัสดี'}],
                  'temperature': 2, 'max_tokens': 99999, 'options': {'repeat_penalty': 2}}
        result = openai_request(source)
        self.assertEqual(result['options'], CONFIG_G)
        self.assertEqual(result['messages'][0], {'role': 'system', 'content': SYSTEM_PROMPT})
        self.assertTrue(any(m['role'] == 'user' and 'ข้อมูลจากผลค้นหา' in m['content']
                            for m in result['messages'][1:]))
        self.assertFalse(result['think'])
        self.assertEqual(native_request({'model':'bomai-safe','prompt':'สวัสดี','options':{'temperature':2}}, '')['system'], SYSTEM_PROMPT)

    def test_retrieval_is_data_message_not_system(self):
        payload = {'model': 'bomai-safe', 'messages': [
            {'role': 'system', 'content': '<context><source id="1">retrieved text</source></context>'},
            {'role': 'user', 'content': 'เขียนโค้ด Python'}]}
        result = openai_request(payload)
        self.assertEqual(result['messages'][0], {'role': 'system', 'content': SYSTEM_PROMPT})
        self.assertTrue(any(m['role'] == 'user' and '<source id="1">' in m['content']
                            for m in result['messages'][1:-1]))
        self.assertEqual(result['messages'][-1]['content'], 'เขียนโค้ด Python')
        self.assertNotIn('<source', result['messages'][0]['content'])

    def test_non_system_messages_and_order_survive(self):
        messages = [
            {'role': 'system', 'content': '<context>search</context>'},
            {'role': 'user', 'content': 'old question'},
            {'role': 'assistant', 'content': 'old answer'},
            {'role': 'user', 'content': 'current question'}]
        result = ensure_system(messages)
        self.assertEqual(result[-1]['content'], 'current question')
        self.assertIn('search', result[-2]['content'])
        self.assertEqual(result[-3]['content'], 'old answer')


class FakeOllama(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    def log_message(self, *_): pass
    def do_GET(self):
        obj = {'version':'0.40.13'} if self.path == '/api/version' else {'models':[{'name':'bomai-safe:latest','model':'bomai-safe:latest'}]}
        data = json.dumps(obj).encode()
        self.send_response(200); self.send_header('Content-Length',str(len(data))); self.end_headers(); self.wfile.write(data)
    def do_POST(self):
        payload = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        self.server.payloads.append(payload)
        text = 'คำตอบเริ่มต้น ' + PHRASE * 100
        prompt=payload.get('prompt') or (payload.get('messages') or [{}])[-1].get('content')
        if prompt=='list_fixture':
            text=json.loads((Path(__file__).parent/'fixtures'/'i9-light-owner-list.json').read_text(encoding='utf-8'))['response']
        if not payload.get('stream'):
            obj = {'model':'bomai-safe','message':{'role':'assistant','content':text},'done':True,'done_reason':'stop'}
            if self.path=='/api/generate':
                obj['response']=text;obj.pop('message')
            data = json.dumps(obj,ensure_ascii=False).encode()
            self.send_response(200); self.send_header('Content-Length',str(len(data))); self.end_headers(); self.wfile.write(data)
            return
        self.send_response(200); self.send_header('Content-Type','application/x-ndjson'); self.send_header('Connection','close'); self.end_headers()
        self.close_connection=True
        try:
            for char in text:
                obj={'model':'bomai-safe','message':{'content':char},'done':False}
                if self.path=='/api/generate':
                    obj['response']=char;obj.pop('message')
                self.wfile.write(json.dumps(obj,ensure_ascii=False).encode()+b'\n'); self.wfile.flush()
                self.server.records_written += 1
                time.sleep(.001)
            self.wfile.write(b'{"model":"bomai-safe","done":true,"done_reason":"stop"}\n'); self.wfile.flush()
        except (OSError, ConnectionError):
            self.server.cancelled.set()

class GatewayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.ollama=ThreadingHTTPServer(('127.0.0.1',0),FakeOllama)
        cls.ollama.payloads=[]; cls.ollama.records_written=0; cls.ollama.cancelled=threading.Event()
        cls.thread=threading.Thread(target=cls.ollama.serve_forever,daemon=True);cls.thread.start()
        cls.key='test-install-key-'+ 'x'*32
        cls.gateway=RuntimeServer(('127.0.0.1',0),f'http://127.0.0.1:{cls.ollama.server_port}',
            catalog=Path(__file__).resolve().parents[1]/'runtime'/'models.json',
            log=str(Path(cls.tmp.name)/'events.jsonl'),gateway_key=cls.key,model_alias='bomai-safe')
        cls.gt=threading.Thread(target=cls.gateway.serve_forever,daemon=True); cls.gt.start()
        cls.url=f'http://127.0.0.1:{cls.gateway.server_port}'
    @classmethod
    def tearDownClass(cls):
        cls.gateway.shutdown(); cls.gateway.server_close(); cls.ollama.shutdown(); cls.ollama.server_close(); cls.tmp.cleanup()
    def request(self,path,data=None,auth=True):
        headers={'Content-Type':'application/json'}
        if auth: headers['Authorization']='Bearer '+self.key
        req=urllib.request.Request(self.url+path,data=json.dumps(data,ensure_ascii=False).encode() if data is not None else None,headers=headers)
        return urllib.request.urlopen(req,timeout=10)
    def test_health_and_ready(self):
        with self.request('/healthz',auth=False) as response: self.assertEqual(json.load(response)['status'],'ok')
        with self.request('/readyz') as response: self.assertEqual(json.load(response)['status'],'ready')
    def test_authorization(self):
        with self.assertRaises(urllib.error.HTTPError) as caught: self.request('/v1/models',auth=False)
        self.assertEqual(caught.exception.code,401)
    def test_models_only_active_alias(self):
        with self.request('/v1/models') as response: self.assertEqual([m['id'] for m in json.load(response)['data']],['bomai-safe'])
    def test_sse_guard_cancels_upstream_and_finishes(self):
        payload={'model':'bomai-safe','messages':[{'role':'user','content':'ทดสอบ'}],'stream':True}
        with self.request('/v1/chat/completions',payload) as response: raw=response.read().decode()
        self.assertTrue(raw.endswith('data: [DONE]\n\n'))
        records=[json.loads(l[6:]) for l in raw.splitlines() if l.startswith('data: ') and l!='data: [DONE]']
        text=''.join(o['choices'][0]['delta'].get('content','') for o in records)
        self.assertIn(RepetitionGate.NOTICE,text)
        self.assertEqual(records[-1]['choices'][0]['finish_reason'],'stop')
        self.assertTrue(records[-1]['bomai_guard']['truncated'])
        self.assertTrue(self.ollama.cancelled.wait(3))
        self.assertEqual(self.ollama.payloads[-1]['options'],CONFIG_G)
    def test_native_nonstream_guard(self):
        with self.request('/api/chat',{'model':'bomai-safe','messages':[{'role':'user','content':'ทดสอบ'}],'stream':False}) as response:
            result=json.load(response)
        self.assertTrue(result['bomai_guard']['truncated'])
        self.assertIn(RepetitionGate.NOTICE,result['message']['content'])
    def test_native_generate_stream_list_guard(self):
        with self.request('/api/generate',{'model':'bomai-safe','prompt':'list_fixture','stream':True}) as response:
            records=[json.loads(line) for line in response.read().splitlines()]
        self.assertTrue(records[-1]['done'])
        self.assertEqual(records[-1]['bomai_guard']['reason'],'repeated_list_row')
        self.assertIn(RepetitionGate.NOTICE,''.join(row.get('response','') for row in records))
    def test_openai_nonstream_list_guard(self):
        with self.request('/v1/chat/completions',{'model':'bomai-safe','messages':[{'role':'user','content':'list_fixture'}],'stream':False}) as response:
            result=json.load(response)
        self.assertEqual(result['bomai_guard']['reason'],'repeated_list_row')
        self.assertIn(RepetitionGate.NOTICE,result['choices'][0]['message']['content'])
    def test_guard_log_no_prompt_or_content(self):
        with self.request('/v1/chat/completions',{'model':'bomai-safe','messages':[{'role':'system','content':'PRIVATE_SYSTEM_MUST_NOT_LOG'},{'role':'user','content':'PRIVATE_PROMPT_MUST_NOT_LOG'}],'stream':False}) as response:
            json.load(response)
        log=(Path(self.tmp.name)/'events.jsonl').read_text(encoding='utf-8')
        self.assertIn('repetition_truncated',log)
        for value in ('PRIVATE_SYSTEM_MUST_NOT_LOG','PRIVATE_PROMPT_MUST_NOT_LOG',PHRASE,self.key): self.assertNotIn(value,log)

class ContextTests(unittest.TestCase):
    def three_source_payload(self):
        sources = ''.join(f'<source id="{i}">{("ข้อมูลผลค้นหาชุดที่ " + str(i) + " ") * 120}</source>' for i in (1, 2, 3))
        system = '<context>' + sources + '</context>'
        return {'model': 'bomai-safe', 'messages': [
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': 'คำถามปกติของผู้ใช้'}], 'stream': False}

    def test_cap_source_context_bounds(self):
        payload = prepare_context(native_request(self.three_source_payload(), ''))
        text = next(m['content'] for m in payload['messages'] if is_source_message(m))
        inner = text.split('<context>', 1)[1].rsplit('</context>', 1)[0]
        bodies = re.findall(r'<source\b[^>]*>(.*?)</source>', inner, re.S)
        self.assertLessEqual(sum(len(b) for b in bodies), MAX_RETRIEVAL_CHARS)
        for body in bodies:
            self.assertLessEqual(len(body), MAX_SOURCE_CHARS)
        self.assertEqual(len(re.findall(r'<source\b', inner)), len(re.findall(r'</source>', inner)))
        user = [m for m in payload['messages'] if m.get('role') == 'user' and not is_source_message(m)]
        self.assertEqual(user[-1]['content'], 'คำถามปกติของผู้ใช้')
        self.assertEqual(payload['messages'][0]['content'], SYSTEM_PROMPT)
        self.assertEqual(payload['options'], CONFIG_G)

    def test_vision_first_attempt_drops_only_source_message(self):
        payload = prepare_context(native_request({'model': 'bomai-safe', 'messages': [
            {'role': 'system', 'content': '<context><source id="9">big retrieval text</source></context>'},
            {'role': 'user', 'content': 'อ่านภาพนี้', 'images': ['aGVsbG8=']}], 'stream': False}, ''))
        roles = [(m.get('role'), m.get('content')) for m in payload['messages']]
        self.assertEqual(payload['messages'][0]['content'], SYSTEM_PROMPT)
        self.assertFalse(any(is_source_message(m) for m in payload['messages']))
        kept = payload['messages'][-1]
        self.assertEqual(kept['content'], 'อ่านภาพนี้')
        self.assertEqual(kept.get('images'), ['aGVsbG8='])

    def test_context_overflow_parsing(self):
        body = json.dumps({'error': 'request (9423 tokens) exceeds the available context size (8192 tokens)'}).encode()
        self.assertEqual(context_overflow(body), (9423, 8192))
        self.assertIsNone(context_overflow(json.dumps({'error': 'model not found'}).encode()))
        self.assertEqual(CONTEXT_REDUCTIONS, (0.5, 0.0))

    def test_reduce_source_context_factors(self):
        payload = native_request(self.three_source_payload(), '')
        halved = reduce_source_context(payload, 0.5)
        text = next(m['content'] for m in halved['messages'] if is_source_message(m))
        inner = text.split('<context>', 1)[1].rsplit('</context>', 1)[0]
        bodies = re.findall(r'<source\b[^>]*>(.*?)</source>', inner, re.S)
        self.assertLessEqual(sum(len(b) for b in bodies), MAX_RETRIEVAL_CHARS // 2)
        removed = reduce_source_context(payload, 0.0)
        self.assertFalse(any(is_source_message(m) for m in removed['messages']))
        self.assertEqual(removed['options']['num_predict'], CONFIG_G['num_predict'])
        users = [m for m in removed['messages'] if m.get('role') == 'user']
        self.assertEqual(users[-1]['content'], 'คำถามปกติของผู้ใช้')


class OverflowFakeOllama(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    def log_message(self, *_): pass
    def do_GET(self):
        obj = {'version': '0.40.13'} if self.path == '/api/version' else {'models': [{'name': 'bomai-safe:latest'}]}
        data = json.dumps(obj).encode()
        self.send_response(200); self.send_header('Content-Length', str(len(data))); self.end_headers(); self.wfile.write(data)
    def do_POST(self):
        payload = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        self.server.payloads.append(payload)
        mode = self.server.mode
        is_overflow = (mode == 'always_overflow') or (mode == 'recover_once' and len(self.server.payloads) == 1)
        if is_overflow:
            data = json.dumps({'error': 'request (9423 tokens) exceeds the available context size (8192 tokens)'}).encode()
            self.send_response(400); self.send_header('Content-Length', str(len(data))); self.end_headers(); self.wfile.write(data)
            return
        text = 'คำตอบปกติที่สมบูรณ์เป็นภาษาไทยชัดเจน'
        data = json.dumps({'model': 'bomai-safe', 'message': {'role': 'assistant', 'content': text}, 'done': True, 'done_reason': 'stop'}, ensure_ascii=False).encode()
        self.send_response(200); self.send_header('Content-Length', str(len(data))); self.end_headers(); self.wfile.write(data)


class OverflowGatewayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.ollama = ThreadingHTTPServer(('127.0.0.1', 0), OverflowFakeOllama)
        cls.ollama.payloads = []; cls.ollama.mode = 'always_ok'
        cls.thread = threading.Thread(target=cls.ollama.serve_forever, daemon=True); cls.thread.start()
        cls.key = 'test-ctx-key-' + 'y' * 32
        cls.gateway = RuntimeServer(('127.0.0.1', 0), f'http://127.0.0.1:{cls.ollama.server_port}',
            catalog=Path(__file__).resolve().parents[1] / 'runtime' / 'models.json',
            log=str(Path(cls.tmp.name) / 'events.jsonl'), gateway_key=cls.key, model_alias='bomai-safe')
        cls.gt = threading.Thread(target=cls.gateway.serve_forever, daemon=True); cls.gt.start()
        cls.url = f'http://127.0.0.1:{cls.gateway.server_port}'
    @classmethod
    def tearDownClass(cls):
        cls.gateway.shutdown(); cls.gateway.server_close(); cls.ollama.shutdown(); cls.ollama.server_close(); cls.tmp.cleanup()
    def setUp(self):
        self.base = len(self.ollama.payloads)
    def request(self, path, data):
        req = urllib.request.Request(self.url + path, data=json.dumps(data, ensure_ascii=False).encode(),
                                     headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + self.key})
        return urllib.request.urlopen(req, timeout=10)
    def big_context_messages(self):
        system = '<context>' + ''.join(f'<source id="{i}">{("ข้อมูลผลค้นหา " * 80)}</source>' for i in (1, 2, 3)) + '</context>'
        return {'model': 'bomai-safe', 'messages': [
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': 'คำถามผู้ใช้'}], 'stream': False}
    def test_one_reduced_retry_recovers(self):
        self.ollama.mode = 'recover_once'
        try:
            with self.request('/api/chat', self.big_context_messages()) as response:
                result = json.load(response)
        finally:
            self.ollama.mode = 'always_ok'
        self.assertEqual(len(self.ollama.payloads) - self.base, 2)
        self.assertIn('คำตอบปกติที่สมบูรณ์', result['message']['content'])
        self.assertNotIn('exceeds the available context', json.dumps(result, ensure_ascii=False))
        self.assertEqual(self.ollama.payloads[self.base]['messages'][0]['content'], SYSTEM_PROMPT)
        self.assertEqual(self.ollama.payloads[self.base + 1]['messages'][-1]['content'], 'คำถามผู้ใช้')
        first = next(m['content'] for m in self.ollama.payloads[self.base]['messages'] if is_source_message(m))
        second = next((m['content'] for m in self.ollama.payloads[self.base + 1]['messages'] if is_source_message(m)), '')
        self.assertLess(len(second), len(first))
        self.assertEqual(self.ollama.payloads[self.base + 1]['options'], CONFIG_G)
    def test_persistent_overflow_returns_thai_notice(self):
        self.ollama.mode = 'always_overflow'
        try:
            with self.request('/api/chat', self.big_context_messages()) as response:
                result = json.load(response)
        finally:
            self.ollama.mode = 'always_ok'
        self.assertEqual(len(self.ollama.payloads) - self.base, 3)
        self.assertEqual(result['message']['content'], CONTEXT_CAPACITY_NOTICE)
        self.assertTrue(result['bomai_context']['exhausted'])
        self.assertNotIn('exceeds the available context', json.dumps(result, ensure_ascii=False))
        self.assertFalse(any(is_source_message(m) for m in self.ollama.payloads[self.base + 2]['messages']))
    def test_persistent_overflow_openai_stream_shape(self):
        self.ollama.mode = 'always_overflow'
        payload = self.big_context_messages(); payload['stream'] = True
        try:
            with self.request('/v1/chat/completions', payload) as response:
                raw = response.read().decode()
        finally:
            self.ollama.mode = 'always_ok'
        self.assertTrue(raw.endswith('data: [DONE]\n\n'))
        records = [json.loads(l[6:]) for l in raw.splitlines() if l.startswith('data: ') and l != 'data: [DONE]']
        text = ''.join(o['choices'][0]['delta'].get('content', '') for o in records)
        self.assertEqual(text, CONTEXT_CAPACITY_NOTICE)
        self.assertTrue(records[-1]['bomai_context']['exhausted'])
        self.assertEqual(records[-1]['choices'][0]['finish_reason'], 'stop')
        self.assertNotIn('exceeds the available context', raw)


class TransportFakeOllama(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    def log_message(self, *_): pass
    def do_GET(self):
        obj = {'version': '0.40.13'} if self.path == '/api/version' else {'models': [{'name': 'bomai-safe:latest'}]}
        data = json.dumps(obj).encode()
        self.send_response(200); self.send_header('Content-Length', str(len(data))); self.end_headers(); self.wfile.write(data)
    def _ndjson_headers(self):
        self.send_response(200); self.send_header('Content-Type', 'application/x-ndjson')
        self.send_header('Connection', 'close'); self.end_headers(); self.close_connection = True
    def do_POST(self):
        payload = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        self.server.payloads.append(payload)
        self.server.stream_count += 1
        mode = self.server.mode
        if mode == 'drop_empty' and self.server.stream_count == 1:
            self._ndjson_headers()
            return  # connection dies before any visible content
        if mode == 'partial':
            self._ndjson_headers()
            for chunk in ('คำตอบบางส่วน', 'ที่ยังไม่จบ'):
                frame = {'model': 'bomai-safe', 'message': {'content': chunk}, 'done': False}
                self.wfile.write(json.dumps(frame, ensure_ascii=False).encode() + b'\n')
            self.wfile.flush()
            return  # no done frame
        self._ndjson_headers()
        for chunk in ('คำตอบสมบูรณ์', 'เป็นภาษาไทย'):
            frame = {'model': 'bomai-safe', 'message': {'content': chunk}, 'done': False}
            self.wfile.write(json.dumps(frame, ensure_ascii=False).encode() + b'\n')
        self.wfile.write(b'{"model":"bomai-safe","done":true,"done_reason":"stop"}\n')
        self.wfile.flush()


class TransportGatewayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.ollama = ThreadingHTTPServer(('127.0.0.1', 0), TransportFakeOllama)
        cls.ollama.payloads = []; cls.ollama.mode = 'ok'; cls.ollama.stream_count = 0
        cls.thread = threading.Thread(target=cls.ollama.serve_forever, daemon=True); cls.thread.start()
        cls.key = 'test-transport-key-' + 'z' * 24
        cls.gateway = RuntimeServer(('127.0.0.1', 0), f'http://127.0.0.1:{cls.ollama.server_port}',
            catalog=Path(__file__).resolve().parents[1] / 'runtime' / 'models.json',
            log=str(Path(cls.tmp.name) / 'events.jsonl'), gateway_key=cls.key, model_alias='bomai-safe')
        cls.gt = threading.Thread(target=cls.gateway.serve_forever, daemon=True); cls.gt.start()
        cls.url = f'http://127.0.0.1:{cls.gateway.server_port}'
    @classmethod
    def tearDownClass(cls):
        cls.gateway.shutdown(); cls.gateway.server_close(); cls.ollama.shutdown(); cls.ollama.server_close(); cls.tmp.cleanup()
    def setUp(self):
        self.base = len(self.ollama.payloads)
    def request(self, path, data):
        req = urllib.request.Request(self.url + path, data=json.dumps(data, ensure_ascii=False).encode(),
                                     headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + self.key})
        return urllib.request.urlopen(req, timeout=60)
    def stream_payload(self):
        return {'model': 'bomai-safe', 'messages': [{'role': 'user', 'content': 'ทดสอบสตรีม'}], 'stream': True}
    def test_queue_contract_constants(self):
        self.assertEqual(INFERENCE_QUEUE_TIMEOUT, 300)
        self.assertEqual(MAX_INFERENCE, 1)
        self.assertEqual(MAX_QUEUED, 8)
        self.assertEqual(MAX_EMPTY_STREAM_RETRIES, 1)
    def test_empty_stream_retry_recovers_single_done(self):
        self.ollama.mode = 'drop_empty'
        try:
            with self.request('/v1/chat/completions', self.stream_payload()) as response:
                raw = response.read().decode()
        finally:
            self.ollama.mode = 'ok'
        self.assertEqual(len(self.ollama.payloads) - self.base, 2)
        self.assertEqual(raw.count('data: [DONE]'), 1)
        self.assertNotIn('upstream_stream_incomplete', raw)
        records = [json.loads(l[6:]) for l in raw.splitlines() if l.startswith('data: ') and l != 'data: [DONE]']
        text = ''.join(o['choices'][0]['delta'].get('content', '') for o in records)
        self.assertEqual(text, 'คำตอบสมบูรณ์เป็นภาษาไทย')
    def test_partial_stream_never_regenerates(self):
        self.ollama.mode = 'partial'
        try:
            with self.request('/api/chat', self.stream_payload()) as response:
                lines = [json.loads(line) for line in response.read().splitlines() if line.strip()]
        finally:
            self.ollama.mode = 'ok'
        self.assertEqual(len(self.ollama.payloads) - self.base, 1)
        self.assertTrue(any('error' in row and row['error'] == 'upstream_stream_incomplete' for row in lines))
        text = ''.join(row.get('message', {}).get('content', '') or '' for row in lines)
        self.assertEqual(text.count('คำตอบบางส่วน'), 1)
        self.assertIn(STREAM_INCOMPLETE_NOTICE, text)


class GuardFixtureTests(unittest.TestCase):
    def run_chunks(self, text, size):
        gate = RepetitionGate()
        output = ''.join(gate.feed(text[i:i+size]) for i in range(0, len(text), size))
        output += gate.feed('', final=True)
        return gate, output

    def test_fguard_real_fixtures_line_and_block(self):
        # fix-121 F-GUARD: real sanitized browser failures.
        fx = Path(__file__).parent / 'fixtures'
        block = json.loads((fx / 'mac-light-s006-block.json').read_text(encoding='utf-8'))['response']
        line = json.loads((fx / 'windows-light-s012-line.json').read_text(encoding='utf-8'))['response']
        for size in (1, 7, 4096):
            gate, output = self.run_chunks(block, size)
            self.assertTrue(gate.triggered, f's006 size={size}')
            self.assertIn(RepetitionGate.NOTICE, output)
            self.assertLessEqual(output.count('หัตถกรรม'), 3)
            gate, output = self.run_chunks(line, size)
            self.assertTrue(gate.triggered, f's012 size={size}')
            self.assertEqual(gate.reason, 'repeated_text_line')
            self.assertIn(RepetitionGate.NOTICE, output)
            self.assertLessEqual(output.count('แมวจามร้องไห้'), 3)

    def test_fguard_synthetic_block_four_copies_cut(self):
        # Short adjacent blocks are usually caught first by the character-level
        # phrase gate; both detectors count as containment.
        block = 'อุปกรณ์อื่น:\nหัตถกรรม 1\nกระเป๋า 1\nเสื้อผ้า 1\nรองเท้า 1'
        text = 'รายการเริ่มต้น:\n' + '\n'.join([block] * 5)
        for size in (1, 7, 4096):
            gate, output = self.run_chunks(text, size)
            self.assertTrue(gate.triggered, f'size={size}')
            self.assertIn(gate.reason, ('repeated_line_block', 'adjacent_phrase_repetition'))
            self.assertLessEqual(output.count('หัตถกรรม'), 3)
            self.assertIn(RepetitionGate.NOTICE, output)
        # Short-line blocks are contained; under the 4-copy rule the
        # character-level phrase gate usually fires first (layered defense —
        # the line-block detector also covers phrase-window roll-off cases).
        short_block = '\n'.join('บอมไป\nโรงเรียน\nกับเพื่อน\nตอนเช้า'.split('\n'))
        for line in short_block.split('\n'):
            self.assertLess(len(line), RepetitionGate.MIN_LINE_CHARS)
        text = 'เริ่มเรื่อง:\n' + '\n'.join([short_block] * 5)
        gate, output = self.run_chunks(text, 7)
        self.assertTrue(gate.triggered)
        self.assertIn(gate.reason, ('repeated_line_block', 'adjacent_phrase_repetition'))
        self.assertLessEqual(output.count('โรงเรียน'), 3)

    def test_fguard_three_block_copies_and_s014_dialogue_pass(self):
        # Blueprint 4-copy threshold: three intentional copies stay untouched,
        # matching the S041 control. The real s014 dialogue fixture contains
        # only three alternating pairs, so it is not contained by the 4-copy
        # rule either (recorded residual gap, not a detector relaxation).
        block = 'อุปกรณ์อื่น:\nหัตถกรรม 1\nกระเป๋า 1\nเสื้อผ้า 1\nรองเท้า 1'
        text = '\n'.join([block] * 3)
        gate, output = self.run_chunks(text, 5)
        self.assertFalse(gate.triggered)
        self.assertEqual(output, text)
        fx = Path(__file__).parent / 'fixtures'
        dialogue = json.loads((fx / 'mac-light-s014-dialogue.json').read_text(encoding='utf-8'))['response']
        gate, output = self.run_chunks(dialogue, 7)
        self.assertFalse(gate.triggered)
        self.assertEqual(output, dialogue)

    def test_fguard_two_ordinary_repeated_lines_pass(self):
        row = 'บรรทัดธรรมดาที่มีเนื้อหายาวพอสมควรและไม่ซ้ำมาก'
        text = row + '\nระหว่างกลางที่แตกต่างอย่างชัดเจน\n' + row + '\nอีกบรรทัดที่ต่างกัน\n' + row
        gate, output = self.run_chunks(text, 3)
        self.assertFalse(gate.triggered)
        self.assertEqual(output, text)


if __name__=='__main__': unittest.main(verbosity=2)
