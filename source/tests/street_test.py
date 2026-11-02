#!/usr/bin/env python3
"""Real endpoint street tests. Automated metrics never certify semantic quality.

Examples:
  python street_test.py --ollama http://127.0.0.1:11434 --model siamcafe/bom-ai:light-v1.0.0 --output baseline-light.json
  python street_test.py --gateway http://127.0.0.1:11435 --key-file gateway.key --model bomai-safe --output guarded-light.json
"""
from __future__ import annotations
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import re
import socket
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runtime'))
from bom_runtime import CONFIG_G, SYSTEM_PROMPT, RepetitionGate

HAN = re.compile('[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\U00020000-\U000323af]')
THAI = re.compile('[\u0e01-\u0e5b]')

def utc():
    return datetime.now(timezone.utc).isoformat()

def save(path, document):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(path)

def timed_lines(response, deadline):
    """Bound the total stream, including a peer trickling an unfinished line.

    CPython HTTPResponse.read1 performs at most one underlying buffered read;
    the remaining total budget is applied to its socket before each read.
    """
    pending = b''
    sock = getattr(getattr(getattr(response, 'fp', None), 'raw', None), '_sock', None)
    if sock is None:
        raise OSError('cannot enforce total deadline for this HTTP response transport')
    while True:
        remaining = deadline-time.monotonic()
        if remaining <= 0:
            raise TimeoutError('total prompt deadline exceeded')
        sock.settimeout(remaining)
        chunk = response.read1(65536)
        if time.monotonic() > deadline:
            raise TimeoutError('total prompt deadline exceeded')
        if not chunk:
            if pending:
                yield pending
            return
        pending += chunk
        while b'\n' in pending:
            line, _, pending = pending.partition(b'\n')
            if len(line) > 8*1024*1024:
                raise ValueError('stream record exceeded bound')
            if time.monotonic() > deadline:
                raise TimeoutError('total prompt deadline exceeded')
            yield line
        if len(pending) > 8*1024*1024:
            raise ValueError('stream record exceeded bound')

def call(args, case):
    is_native = bool(args.ollama)
    endpoint = (args.ollama or args.gateway).rstrip('/')
    prompt = case['prompt']
    message = {'role': 'user', 'content': prompt}
    if case.get('requires_image'):
        if not args.image:
            return {'status': 'NOT_RUN', 'reason': 'vision fixture not supplied'}
        encoded = base64.b64encode(args.image.read_bytes()).decode('ascii')
        if is_native:
            message['images'] = [encoded]
        else:
            message['content'] = [{'type': 'text', 'text': prompt},
                {'type': 'image_url', 'image_url': {'url': 'data:image/png;base64,' + encoded}}]
    payload = {'model': args.model, 'messages': [{'role': 'system', 'content': SYSTEM_PROMPT}, message],
               'stream': True}
    if is_native:
        payload.update(options=CONFIG_G, think=False)
    headers = {'Content-Type': 'application/json'}
    if args.key_file:
        headers['Authorization'] = 'Bearer ' + args.key_file.read_text(encoding='utf-8-sig').strip()
    request = urllib.request.Request(endpoint + ('/api/chat' if is_native else '/v1/chat/completions'),
              data=json.dumps(payload, ensure_ascii=False).encode('utf-8'), headers=headers)
    response_text, thinking_chars, done, guard, error = '', 0, False, None, None
    finish_reason, usage = None, None
    start = time.monotonic()
    deadline = start + args.timeout
    http_status = None
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(request, timeout=args.timeout) as response:
            http_status = response.status
            for line in timed_lines(response, deadline):
                if len(line) > 8 * 1024 * 1024:
                    raise ValueError('stream record exceeded bound')
                if not line.strip():
                    continue
                if not is_native:
                    if not line.startswith(b'data: '):
                        continue
                    line = line[6:].strip()
                    if line == b'[DONE]':
                        break
                obj = json.loads(line)
                if obj.get('error'):
                    error = obj['error']
                    break
                if is_native:
                    message = obj.get('message') or {}
                    response_text += message.get('content') or ''
                    thinking_chars += len(message.get('thinking') or '')
                    if obj.get('done'):
                        done = True
                        finish_reason = obj.get('done_reason')
                        usage = {k: v for k, v in obj.items() if k.endswith('_count') or k.endswith('_duration')}
                else:
                    choices = obj.get('choices') or []
                    if choices:
                        response_text += (choices[0].get('delta') or {}).get('content') or ''
                        if choices[0].get('finish_reason'):
                            done, finish_reason = True, choices[0]['finish_reason']
                    usage = obj.get('usage', usage)
                guard = obj.get('bomai_guard', guard)
    except urllib.error.HTTPError as exc:
        http_status = exc.code
        # No credentials or arbitrary upstream bodies enter the report.
        error = 'HTTP_' + str(exc.code)
    except (OSError, ValueError) as exc:
        error = type(exc).__name__ + ': ' + str(exc)
    detector = RepetitionGate()
    try:
        detector.feed(response_text, final=True)
        loop = detector.triggered
    except ValueError:
        loop = None
        error = error or 'visible response exceeded detector bound'
    han, thai = len(HAN.findall(response_text)), len(THAI.findall(response_text))
    maximum = case.get('expected_max_chars', 3000) * 2
    failures = []
    if error or not done: failures.append('transport_or_incomplete')
    if not response_text.strip(): failures.append('empty')
    if han: failures.append('han_characters')
    if not thai: failures.append('no_thai_characters')
    if loop: failures.append('detected_adjacent_repetition')
    if guard: failures.append('guard_intervention_requires_regeneration')
    if len(response_text) > maximum: failures.append('length_above_2x_expected_max')
    if finish_reason == 'length': failures.append('token_limit_reached')
    return {'status': 'FAIL' if failures else 'REVIEW_REQUIRED', 'http_status': http_status,
            'elapsed_seconds': round(time.monotonic()-start, 3), 'response': response_text,
            'response_sha256': hashlib.sha256(response_text.encode()).hexdigest(),
            'chars': len(response_text), 'thai_chars': thai, 'han_chars': han,
            'detected_repetition': loop, 'guard_intervention': guard,
            'done': done, 'finish_reason': finish_reason, 'usage': usage,
            'hidden_thinking_chars': thinking_chars, 'error': error,
            'automatic_failures': failures,
            'manual_review': {'coherent': None, 'answers_question': None, 'clean_ending': None,
                              'thai_quality': None, 'false_positive_review': None},
            'web_search_executed': False if case.get('requires_search') else None}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    endpoints = p.add_mutually_exclusive_group(required=True)
    endpoints.add_argument('--ollama')
    endpoints.add_argument('--gateway')
    p.add_argument('--model', required=True)
    p.add_argument('--key-file', type=Path)
    p.add_argument('--corpus', type=Path, default=Path(__file__).with_name('street_test_50.json'))
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--image', type=Path)
    p.add_argument('--timeout', type=float, default=600, help='total seconds per prompt, including streamed reads')
    p.add_argument('--resume', action='store_true')
    p.add_argument('--limit', type=int)
    args = p.parse_args()
    if args.timeout <= 0:
        p.error('--timeout must be positive')
    corpus_bytes = args.corpus.read_bytes()
    corpus = json.loads(corpus_bytes)
    digest = hashlib.sha256(corpus_bytes).hexdigest()
    endpoint = args.ollama or args.gateway
    report = {'started_utc': utc(), 'machine': socket.gethostname(), 'platform': platform.platform(),
              'python': platform.python_version(), 'model': args.model, 'endpoint': endpoint,
              'mode': 'raw_ollama' if args.ollama else 'guarded_gateway', 'corpus_sha256': digest,
              'locked_options': CONFIG_G, 'system_sha256': hashlib.sha256(SYSTEM_PROMPT.encode()).hexdigest(),
              'semantic_quality_certified': False, 'results': []}
    if args.resume and args.output.exists():
        existing = json.loads(args.output.read_text(encoding='utf-8'))
        for field in ('model', 'endpoint', 'mode', 'corpus_sha256'):
            if existing.get(field) != report[field]:
                p.error('resume metadata mismatch: ' + field)
        report = existing
    revision = {'runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                'timeout_seconds_per_prompt':args.timeout, 'started_utc':utc(),
                'resume_after_results':len(report['results'])}
    report.setdefault('runner_revisions', []).append(revision)
    completed = {row['id'] for row in report['results']}
    cases = corpus['cases'][:args.limit] if args.limit else corpus['cases']
    for case in cases:
        if case['id'] in completed:
            continue
        result = {'id': case['id'], 'category': case['category'], 'prompt': case['prompt'], 'started_utc': utc(),
                  'runner_sha256':revision['runner_sha256'], 'timeout_seconds_per_prompt':args.timeout,
                  'execution_mode':'bounded_total_deadline'}
        result.update(call(args, case))
        report['results'].append(result)
        report['updated_utc'] = utc()
        report['summary'] = {status: sum(row['status'] == status for row in report['results'])
                             for status in ('FAIL', 'REVIEW_REQUIRED', 'NOT_RUN', 'PASS')}
        save(args.output, report)
        print(json.dumps({'id': case['id'], 'status': result['status'], 'elapsed': result.get('elapsed_seconds')}, ensure_ascii=False), flush=True)
    report['finished_utc'] = utc()
    save(args.output, report)
    return 1 if report.get('summary', {}).get('FAIL') else 0

if __name__ == '__main__':
    raise SystemExit(main())
