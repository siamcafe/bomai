#!/usr/bin/env python3
"""BOM AI real-browser QC runner (Playwright Chromium).

Qualifies the 52-case street corpus through the actual Open WebUI browser UI:
login form, fresh empty chat, visible model alias, composer submission, and
DOM-level completion detection. Never calls /api/chat, /v1/chat/completions,
Ollama, or the gateway to produce an answer.

Usage:
  python tests/browser_qc.py \
    --base-url http://127.0.0.1:18080 \
    --credentials /abs/path/state/first-login.json \
    --corpus tests/street_test_50.json \
    --image tests/vision_fixture.png \
    --output evidence/browser/<host>-<tier>.json \
    --screenshot-dir evidence/browser/<host>-<tier> \
    --timeout 600 --resume [--headed]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

CORPUS_SHA256 = '88073d112350982a4965a74a4d834abd1053d9aa36406d000f2618b0136bde93'
CORPUS_COUNT = 52
GUARD_NOTICE_MARKERS = ('[ระบบหยุดคำตอบ', 'ระบบหยุดคำตอบที่เริ่มวนซ้ำ')
# r2: leading search-status lines share the .chat-assistant node with the
# real answer (verified against live OWUI 0.12.5 on macOS via dom_probe).
# r3: OWUI injects '[ERROR: No results found from web search]' as a leading
# line when SearXNG returns nothing; the model answer below it is still a
# real generated answer, so strip it and flag instead of failing transport.
STATUS_LINE_PATTERNS = (
    re.compile(r'^ค้นหา \d+ เว็บไซต์\s*$'),
    re.compile(r'^ไม่มีการสร้างคำค้นหา\s*$'),
    re.compile(r'^กำลังค้นหาบนเว็บ\s*$'),
    re.compile(r'^\[ERROR: No results found from web search\]\s*$'),
)
SEARCH_ERROR_MARKER = '[ERROR: No results found from web search]'
# 2-pass quality rewrite: the exhausted notice is an honest synthetic
# terminal answer. It is always a CONTENT FAIL for QC purposes, never a
# transport error and never a successful fallback.
QUALITY_FAILURE_MARKERS = (
    'ขออภัย ระบบยังไม่สามารถสร้างคำตอบที่ครบถ้วนและไม่ซ้ำซ้อนได้',
    'กรุณาลองแบ่งคำถามหรือระบุรูปแบบคำตอบอีกครั้ง',
)
HAN = re.compile('[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\U00020000-\U000323af]')
THAI = re.compile('[\u0e00-\u0e7f]')
LIST_ROW = re.compile(r'^\s*(?:[-*+•]\s+|\d{1,4}[.)]\s+)(.*)$')
MAX_PERIOD = 240


def strip_status_lines(text: str) -> str:
    """Remove leading OWUI search-status lines from an assistant node text."""
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        if any(pattern.match(lines[index]) for pattern in STATUS_LINE_PATTERNS):
            index += 1
        else:
            break
    return '\n'.join(lines[index:]).strip()


def is_pure_status(text: str) -> bool:
    return len(text.strip()) > 0 and len(strip_status_lines(text)) == 0


def atomic_write_json(path: Path, payload: dict) -> None:
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    os.replace(tmp, path)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def detect_han(text: str) -> int:
    return len(HAN.findall(text))


def detect_thai(text: str) -> int:
    return len(THAI.findall(text))


def detect_repeated_rows(text: str):
    """Rows repeated verbatim 3+ times (same rule family as the gateway guard)."""
    rows = {}
    order = []
    for line in text.splitlines():
        match = LIST_ROW.match(line)
        if not match:
            continue
        row = re.sub(r'\s+', ' ', match.group(1)).strip()
        if len(row) < 4:
            continue
        if row not in rows:
            rows[row] = 0
            order.append(row)
        rows[row] += 1
    repeated = [row for row in order if rows[row] >= 3]
    return repeated, {row: rows[row] for row in repeated}


def detect_adjacent_repetition(text: str):
    """Exact adjacent phrase loop of >= 3 identical repeats (gateway rule family)."""
    normalized = re.sub(r'\s+', '', text)
    limit = min(MAX_PERIOD, max(4, len(normalized) // 3))
    for period in range(4, limit + 1):
        if len(normalized) < period * 3:
            break
        phrase = normalized[-period:]
        if (len({c for c in phrase if c.isalnum()}) >= 4
                and phrase == normalized[-2 * period:-period]
                and phrase == normalized[-3 * period:-2 * period]):
            return phrase
    return None


def detect_raw_markup(text: str) -> bool:
    """Search-context echo heuristics: raw JSON/HTML results in the answer."""
    signals = [
        '"results"', '"unresponsive_engines"', '"url":', '"title":',
        'DOCTYPE', '<html', 'curl -', 'searxng', '"answer_format"',
    ]
    hits = [s for s in signals if s in text]
    lowered = str(text or '').lower()
    # fix-121 r4: raw retrieval markup and site chrome never belong in an
    # answer; case-insensitive so <SOURCE/</Context variants cannot slip out.
    for marker in ('<context', '</context', '<source', '</source',
                   'all rights reserved'):
        if marker in lowered:
            hits.append(marker)
    if lowered.count('cookie policy') >= 1 and lowered.count('skip to content') >= 1:
        hits.append('site_chrome')
    return bool(hits), hits


TRANSPORT_ERROR_MARKERS = (
    'คิว AI เต็ม',
    'กำลังค้นหาบนเว็บ',
    'รอคิว AI เกินกำหนด',
    'upstream_stream_incomplete',
    'reasoning_only_or_empty_response',
    # r5: OWUI's own connection-failure bubble text is a transport failure.
    'การเชื่อมต่อเซิร์ฟเวอร์ล้มเหลว',
)
CONTEXT_OVERFLOW_MARKER_RE = re.compile(
    r'request \(\d+ tokens\) exceeds the available context size \(\d+ tokens\)')


def detect_quality_failure(text: str) -> bool:
    """True when the answer is the 2-pass quality-exhausted notice: both
    distinctive notice sentences must be present in the visible text."""
    body = str(text or '')
    return all(marker in body for marker in QUALITY_FAILURE_MARKERS)


def detect_transport_error(text):
    """True transport failure only: queue-full/timeout notice, upstream
    incomplete/empty markers, context overflow, or a leftover
    searching-status line with no real answer after stripping."""
    body = str(text or '')
    if any(marker in body for marker in TRANSPORT_ERROR_MARKERS):
        return True
    if CONTEXT_OVERFLOW_MARKER_RE.search(body):
        return True
    return len(body.strip()) > 0 and len(strip_status_lines(body)) == 0


def classify_answer(text: str, prompt_meta: dict):
    han = detect_han(text)
    thai = detect_thai(text)
    empty = len(text.strip()) == 0
    repeated_rows, row_counts = detect_repeated_rows(text)
    adjacent = detect_adjacent_repetition(text)
    guard = any(marker in text for marker in GUARD_NOTICE_MARKERS)
    markup, markup_hits = detect_raw_markup(text)
    truncated = bool(re.search(r'\[ระบบหยุด|finish_reason.*length', text))
    return {
        'chars': len(text),
        'han_chars': han,
        'thai_chars': thai,
        'empty': empty,
        'repeated_rows': [{'row': r, 'count': row_counts[r]} for r in repeated_rows[:5]],
        'adjacent_repetition': bool(adjacent),
        'adjacent_period': len(adjacent) if adjacent else 0,
        'guard_intervention': guard,
        'raw_markup_echo': markup,
        'raw_markup_hits': markup_hits[:5],
        'truncation_suspect': truncated,
        'quality_failure': detect_quality_failure(text),
        'expected_max_chars': prompt_meta.get('expected_max_chars'),
    }


class OWUI:
    """Thin selector-tolerant driver for the Open WebUI chat page.

    r2 selectors verified against live OWUI 0.12.5 (macOS dom_probe
    2026-10-31): the assistant payload renders inside a single
    `.chat-assistant` node prefixed by search-status lines; the stop
    control is a Thai aria-label button that is REMOVED from the DOM
    when generation finishes. Fixture-based mechanics tests stay green
    because stop detection uses visibility, not node count.
    """

    NEW_CHAT_SELECTORS = [
        '[data-testid="new-chat-button"]',
        'button[aria-label="New Chat"]',
        'button[aria-label="แชทใหม่"]',
        '#new-chat-button',
    ]
    COMPOSER_SELECTORS = ['#chat-input', 'div[contenteditable="true"]', 'textarea[placeholder]']
    STOP_SELECTORS = [
        'button[aria-label*="หยุด"]',
        'button[aria-label*="Stop"]',
        '[data-testid="stop-response-button"]',
        '#stop-response-button',
    ]
    MODEL_SELECTORS = [
        '[data-testid="model-selector-button"]',
        'button[aria-label*="model" i]',
        '#model-selector-button',
    ]
    ASSISTANT_SELECTORS = ['.chat-assistant', '[data-testid="assistant-message"]']
    SOURCE_SELECTORS = (
        '.source-button',
        '[data-testid*="source"]',
        '[class*="citation"]',
        'button.source-spotlight-button',
        'a.source',
    )

    def __init__(self, page, base_url):
        self.page = page
        self.base_url = base_url

    def first_by(self, selectors, timeout=4000):
        for selector in selectors:
            try:
                loc = self.page.locator(selector).first
                loc.wait_for(state='visible', timeout=timeout)
                return loc
            except Exception:
                continue
        return None

    def login(self, email, password):
        self.page.goto(self.base_url, wait_until='domcontentloaded', timeout=60000)
        self.page.wait_for_timeout(2500)
        email_loc = self.page.locator('input#email, input[name="email"], input[type="email"]').first
        try:
            email_loc.wait_for(state='visible', timeout=8000)
        except Exception:
            email_loc = None
        if email_loc is None:
            # No visible login form: treat an existing session as authenticated.
            composer = self.page.locator('#chat-input, textarea, [data-testid="chat-input"]').first
            try:
                composer.wait_for(state='visible', timeout=8000)
                return 'already_authenticated'
            except Exception:
                raise RuntimeError('neither login form nor chat workspace visible')
        email_loc.fill(email)
        self.page.locator('input#password, input[name="password"], input[type="password"]').first.fill(password)
        self.page.locator('button[type="submit"], button:has-text("เข้าสู่ระบบ"), button:has-text("Sign in")').first.click()
        self.page.wait_for_timeout(4000)
        self.page.wait_for_load_state('domcontentloaded', timeout=60000)
        if '/auth' in self.page.url:
            raise RuntimeError('login did not leave the auth page')
        return 'logged_in'

    def open_new_chat(self):
        self.page.goto(self.base_url + '/', wait_until='domcontentloaded', timeout=60000)
        self.page.wait_for_timeout(2000)
        button = self.first_by(self.NEW_CHAT_SELECTORS, timeout=3000)
        if button:
            try:
                button.click()
                self.page.wait_for_timeout(1200)
            except Exception:
                pass
        return self.page.url

    def current_model_label(self):
        for selector in self.MODEL_SELECTORS:
            loc = self.page.locator(selector)
            if loc.count():
                text = loc.first.inner_text()
                if text and text.strip():
                    return text.strip()
        body = self.page.locator('body').inner_text()
        match = re.search(r'bomai[-a-z0-9]*', body)
        return match.group(0) if match else ''

    def submit_prompt(self, prompt, image_path=None):
        composer = self.first_by(self.COMPOSER_SELECTORS, timeout=20000)
        if composer is None:
            raise RuntimeError('composer not found')
        if image_path:
            file_input = self.page.locator('input[type="file"]').first
            file_input.set_input_files(str(image_path))
            self.page.wait_for_timeout(2500)
        if prompt:
            composer.fill(prompt)
        composer.press('Enter')

    def assistant_nodes(self):
        return self.page.locator(', '.join(self.ASSISTANT_SELECTORS))

    def assistant_count(self):
        return self.assistant_nodes().count()

    def stop_visible(self):
        for selector in self.STOP_SELECTORS:
            try:
                if self.page.locator(selector).first.is_visible():
                    return True
            except Exception:
                continue
        return False

    def raw_assistant_text(self):
        nodes = self.assistant_nodes()
        count = nodes.count()
        if count == 0:
            return ''
        try:
            return nodes.nth(count - 1).inner_text()
        except Exception:
            return ''

    def assistant_text(self):
        return strip_status_lines(self.raw_assistant_text())

    def wait_completion(self, deadline_s, stable_polls=4, poll_interval=0.6):
        """Wait until the stop control disappears and the answer text is
        stable and no longer a bare search-status line."""
        started = time.monotonic()
        last_text = None
        stable = 0
        generation_started = False
        while time.monotonic() - started < deadline_s:
            text = self.assistant_text()
            if text and not is_pure_status(text):
                generation_started = True
            if (text == last_text and text and not self.stop_visible()
                    and generation_started and not is_pure_status(text)):
                stable += 1
                if stable >= stable_polls:
                    return {'completed': True, 'timeout': False, 'elapsed': round(time.monotonic() - started, 1)}
            else:
                stable = 0
                last_text = text
            time.sleep(poll_interval)
        return {'completed': False, 'timeout': True, 'elapsed': round(time.monotonic() - started, 1)}

    def source_urls(self):
        found = []
        locs = self.page.locator(', '.join(self.SOURCE_SELECTORS))
        for index in range(min(locs.count(), 30)):
            try:
                text = locs.nth(index).inner_text()
                if text and text.strip() and text.strip() not in found:
                    found.append(text.strip())
            except Exception:
                continue
        return found

    def search_activity_seen(self):
        for selector in self.SOURCE_SELECTORS:
            try:
                if self.page.locator(selector).count() > 0:
                    return True
            except Exception:
                continue
        return False


def load_output(path: Path):
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    return {}


def main():
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
    parser.add_argument('--cases', default='',
                        help='Comma-separated subset of case IDs for focused runs '
                             '(e.g. S007,S011); empty runs the full corpus')
    parser.add_argument('--model-alias', required=True,
                        choices=('bomai-qc-light', 'bomai-qc-pro'))
    parser.add_argument('--host', required=True, choices=('windows', 'macos', 'linux'))
    parser.add_argument('--tier', required=True, choices=('light', 'pro'))
    parser.add_argument('--runtime-path', required=True)
    args = parser.parse_args()

    if not args.tier in args.model_alias:
        raise SystemExit('tier/model-alias mismatch')

    runtime_path = Path(args.runtime_path)
    if not runtime_path.is_file():
        raise SystemExit('runtime-path must be the candidate bom_runtime.py')
    runtime_sha = sha256_file(runtime_path)
    image_sha = sha256_file(Path(args.image))

    corpus_path = Path(args.corpus)
    corpus_sha = sha256_file(corpus_path)
    if corpus_sha != CORPUS_SHA256:
        raise SystemExit('corpus sha256 mismatch: ' + corpus_sha)
    corpus = json.loads(corpus_path.read_text(encoding='utf-8'))
    ids = [case['id'] for case in corpus['cases']]
    if corpus.get('count') != CORPUS_COUNT or len(ids) != CORPUS_COUNT or len(set(ids)) != CORPUS_COUNT:
        raise SystemExit('corpus must contain 52 unique case ids')
    selected = [token.strip() for token in args.cases.split(',') if token.strip()]
    unknown = [case_id for case_id in selected if case_id not in ids]
    if unknown:
        raise SystemExit('unknown case id(s) in --cases: ' + ','.join(unknown))
    run_cases = [case for case in corpus['cases'] if not selected or case['id'] in set(selected)]

    creds = json.loads(Path(args.credentials).read_text(encoding='utf-8-sig'))
    email = creds['email']
    password = creds['password']

    output_path = Path(args.output)
    shot_dir = Path(args.screenshot_dir)
    shot_dir.mkdir(parents=True, exist_ok=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    runner_sha = sha256_file(Path(__file__).resolve())
    resume_keys = ('corpus_sha256', 'runtime_sha256', 'runner_sha256',
                   'model_alias', 'base_url', 'image_sha256')
    resume_values = {'corpus_sha256': corpus_sha, 'runtime_sha256': runtime_sha,
                     'runner_sha256': runner_sha, 'model_alias': args.model_alias,
                     'base_url': args.base_url, 'image_sha256': image_sha}
    record = load_output(output_path)
    if args.resume:
        stored = record.get('metadata', {})
        for key in resume_keys:
            if stored.get(key) not in (None, resume_values[key]):
                raise SystemExit(
                    f'resume refused: {key} differs from this candidate '
                    f'({stored.get(key)!r} != {resume_values[key]!r})')
    cases_done = {k: v for k, v in (record.get('cases') or {}).items()
                  if isinstance(v, dict) and v.get('status') in ('completed', 'timeout')}
    if not args.resume:
        record = {}

    from playwright.sync_api import sync_playwright

    started_at = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=(not args.headed))
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            locale='th-TH',
            timezone_id='Asia/Bangkok',
        )
        page = context.new_page()
        ui = OWUI(page, args.base_url)
        login_mode = ui.login(email, password)

        record.setdefault('metadata', {})
        record['metadata'].update({
            'base_url': args.base_url,
            'corpus_sha256': corpus_sha,
            'started_at': started_at,
            'login_mode': login_mode,
            'model_alias_expected': args.model_alias,
            'host': args.host,
            'tier': args.tier,
            'runtime_path': str(runtime_path),
            'runtime_sha256': runtime_sha,
            'runner_sha256': runner_sha,
            'image_sha256': image_sha,
            'runner_sha_note': 'browser_qc.py r5 (2-pass quality-failure detector)',
            'selected_cases': selected,
        })
        record.setdefault('cases', {})

        # Default-state capture before any prompt.
        try:
            ui.open_new_chat()
            page.wait_for_timeout(1500)
            page.screenshot(path=str(shot_dir / '00-new-chat-default.png'), full_page=False)
            record['metadata']['default_state_screenshot'] = str(shot_dir / '00-new-chat-default.png')
            record['metadata']['model_label_seen'] = ui.current_model_label()
        except Exception as exc:
            record['metadata']['default_state_error'] = repr(exc)

        for case in run_cases:
            case_id = case['id']
            if args.resume and case_id in cases_done:
                continue
            attempt = {
                'id': case_id,
                'category': case.get('category'),
                'started_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                'model_label': ui.current_model_label(),
            }
            submit_t0 = time.monotonic()
            try:
                ui.open_new_chat()
                page.wait_for_timeout(800)
                image = str(Path(args.image).resolve()) if case.get('requires_image') else None
                ui.submit_prompt(case.get('prompt', ''), image_path=image)
                if not case.get('prompt'):
                    page.wait_for_timeout(4000)
                    attempt['empty_prompt_behavior'] = {
                        'assistant_present': ui.assistant_count() > 0,
                        'body_contains_generation': bool(ui.assistant_text().strip()),
                    }
                    attempt['status'] = 'completed'
                    attempt['answer'] = ''
                    page.screenshot(path=str(shot_dir / (case_id + '.png')), full_page=False)
                else:
                    outcome = ui.wait_completion(args.timeout)
                    text = ui.assistant_text()
                    raw = ui.raw_assistant_text()
                    attempt.update(outcome)
                    attempt['wall_ms'] = round((time.monotonic() - submit_t0) * 1000)
                    attempt['answer'] = text
                    attempt['raw_prefix'] = raw[:160]
                    attempt['search_web_error'] = SEARCH_ERROR_MARKER in raw
                    attempt['sources'] = ui.source_urls()
                    attempt['search_activity'] = ui.search_activity_seen()
                    attempt.update(classify_answer(text, case))
                    if detect_transport_error(text):
                        attempt['status'] = 'transport_error'
                        attempt['transport_error'] = True
                    else:
                        attempt['status'] = 'completed' if outcome['completed'] else 'timeout'
                    page.screenshot(path=str(shot_dir / (case_id + '.png')), full_page=False)
                    if case.get('requires_search'):
                        page.screenshot(path=str(shot_dir / (case_id + '-full.png')), full_page=True)
            except Exception as exc:
                attempt['status'] = 'error'
                attempt['error'] = repr(exc)
                try:
                    page.screenshot(path=str(shot_dir / (case_id + '-error.png')), full_page=False)
                except Exception:
                    pass
            attempt['finished_at'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
            record['cases'][case_id] = attempt
            atomic_write_json(output_path, record)

        # Settings -> Account capture with secret values masked in pixels.
        try:
            page.goto(args.base_url + '/settings/account', wait_until='domcontentloaded', timeout=60000)
            page.wait_for_timeout(2500)
            page.evaluate(
                "document.querySelectorAll('input').forEach(el => {"
                "  const t = el.getAttribute('type') || '';"
                "  if (['text','email','password',''].includes(t.toLowerCase()) && el.value) {"
                "    el.setAttribute('value','********'); el.value = '********'; } })"
            )
            page.screenshot(path=str(shot_dir / 'settings-account-masked.png'), full_page=True)
            record['metadata']['settings_account_screenshot'] = str(shot_dir / 'settings-account-masked.png')
        except Exception as exc:
            record['metadata']['settings_account_error'] = repr(exc)

        record['metadata']['finished_at'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        counts = {}
        for entry in record['cases'].values():
            counts[entry.get('status', 'unknown')] = counts.get(entry.get('status', 'unknown'), 0) + 1
        record['summary'] = {'counts': counts, 'total': len(record['cases'])}
        atomic_write_json(output_path, record)
        browser.close()

    print(json.dumps(record.get('summary', {}), indent=2))
    incomplete = [cid for cid, c in record['cases'].items() if c.get('status') not in ('completed',)]
    if incomplete:
        print('INCOMPLETE:', ', '.join(sorted(incomplete)))
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
