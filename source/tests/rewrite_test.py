#!/usr/bin/env python3
"""2-pass quality rewrite: request analysis, detectors, feedback, payload and
buffered gateway contract tests (blueprint BOM_AI_2Pass_Rewrite, Tasks 1-3).

Pure-function tests need no server. Gateway tests use a scripted fake Ollama
upstream plus the real loopback gateway. No model-quality claims are made here.
"""
import json
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runtime'))
from bom_runtime import (
    CONFIG_G, SYSTEM_PROMPT, SOURCE_GUIDANCE, MAX_QUALITY_REWRITES,
    MAX_REWRITE_FEEDBACK_CHARS, MAX_PASS1_FOR_REWRITE_SECONDS,
    QUALITY_TOTAL_BUDGET_SECONDS, QUALITY_FAILURE_NOTICE, RuntimeServer,
    latest_user_text, analyze_request, assess_quality, rewrite_feedback,
    build_rewrite_payload, merge_attempt_metrics,
)

CORPUS = json.loads((Path(__file__).resolve().parent / 'street_test_50.json')
                    .read_text(encoding='utf-8'))['cases']
BY_ID = {row['id']: row for row in CORPUS}

TEN_GAMES = (
    '1. ซ่อนของในบ้านให้เด็กหา\n2. ทายตัวเลขจากคำใบ้\n3. ปริศนาภาพจากของใกล้ตัว\n'
    '4. เล่านิทานต่อกันทีละคน\n5. วาดรูนิทานร่วมกัน\n6. ทำบ้านของเล่นจากกระดาษ\n'
    '7. เกมไพ่จับคู่ภาพสัตว์\n8. เล่นบทบาทสมมติเป็นพ่อครัว\n9. ร้องเพลงและทำท่าทางตาม\n'
    '10. ต่อจิ๊กซอว์รูปสัตว์ตัวใหญ่')

WISH_A = 'ขอให้คุณยายมีสุขภาพแข็งแรง อยู่กับเราไปนาน ๆ ปีนี้'
WISH_A_NEAR = 'ขอให้คุณยายมีสุขภาพแข็งแรง อยู่กับเราไปนานๆ ปีใหม่นี้'


def payload(text, **extra):
    body = {'model': 'bomai-safe', 'stream': False,
            'messages': [{'role': 'user', 'content': text}], 'think': False}
    body.update(extra)
    return body


class AnalysisTests(unittest.TestCase):
    def test_latest_user_text_skips_system_and_source(self):
        messages = [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': SOURCE_GUIDANCE + '\n\n<context>\nx\n</context>'},
            {'role': 'user', 'content': 'คำถามจริง'},
            {'role': 'assistant', 'content': 'ตอบก่อนหน้า'},
            {'role': 'user', 'content': 'คำถามล่าสุด'}]
        self.assertEqual(latest_user_text(messages), 'คำถามล่าสุด')

    def test_latest_user_text_handles_list_content(self):
        messages = [{'role': 'user', 'content': [
            {'type': 'text', 'text': 'สวัสดี'}, {'type': 'text', 'text': 'ครับ'}]}]
        self.assertEqual(latest_user_text(messages), 'สวัสดี ครับ')

    def test_explicit_count_unit(self):
        spec = analyze_request(payload('แนะนำเกมเล่นกับเด็กในบ้าน 10 เกม'))
        self.assertTrue(spec.eligible)
        self.assertEqual(spec.expected_counts[0]['count'], 10)
        self.assertEqual(spec.expected_counts[0]['unit'], 'เกม')

    def test_menu_and_schedule_counts(self):
        spec = analyze_request(payload('วางแผนเมนูมังสวิรัติ 7 วัน วันละ 3 มื้อ โดยไม่ซ้ำเมนู'))
        self.assertTrue(spec.eligible)
        self.assertTrue(spec.vegetarian)
        self.assertTrue(spec.distinct_required)
        counts = {(row['unit'], row['count']) for row in spec.expected_counts}
        self.assertIn(('วัน', 7), counts)
        self.assertIn(('มื้อ', 3), counts)

    def test_approx_word_length(self):
        spec = analyze_request(payload('เขียนเรียงความเรื่องความทรงจำ ยาวประมาณ 600 คำ'))
        self.assertTrue(spec.eligible)
        self.assertEqual(spec.min_nonspace_chars, 3 * 600)

    def test_max_word_length_is_not_minimum(self):
        spec = analyze_request(payload('แต่งเรื่องสั้นเกี่ยวกับแมว ไม่เกิน 500 คำ'))
        self.assertTrue(spec.eligible)
        self.assertEqual(spec.min_nonspace_chars, 0)

    def test_intentional_repetition(self):
        spec = analyze_request(payload('คัดลอกประโยคนี้ 3 ครั้งตามคำขอ: วันนี้อากาศดีและฉันมีความสุข'))
        self.assertTrue(spec.intentional_repetition)
        self.assertEqual(spec.repeat_limit, 3)

    def test_code_request_eligible(self):
        self.assertTrue(analyze_request(payload('เขียนฟังก์ชัน Python หาค่าเฉลี่ย พร้อมตัวอย่าง')).eligible)
        self.assertTrue(analyze_request(payload('เขียนโค้ด Python พิมพ์สวัสดี พร้อมคำอธิบาย')).eligible)

    def test_ineligible_plain_chat_and_explanations(self):
        for cid in ('S019', 'S024', 'S033', 'S035', 'S036', 'S037'):
            spec = analyze_request(payload(BY_ID[cid]['prompt']))
            self.assertFalse(spec.eligible, cid)

    def test_empty_prompt_ineligible(self):
        self.assertFalse(analyze_request(payload('')).eligible)

    def test_live_query_ineligible(self):
        for cid in ('S043', 'S044', 'S045', 'S046'):
            self.assertFalse(analyze_request(payload(BY_ID[cid]['prompt'])).eligible, cid)

    def test_safety_sensitive_ineligible(self):
        for cid in ('S047', 'S048', 'S049', 'S050'):
            self.assertFalse(analyze_request(payload(BY_ID[cid]['prompt'])).eligible, cid)

    def test_vision_tools_format_ineligible(self):
        vision = payload('อ่านข้อความในภาพ')
        vision['messages'][0]['images'] = ['aGk=']
        self.assertFalse(analyze_request(vision).eligible)
        tools = payload('ช่วยจัดรายการของใช้ 10 อย่าง')
        tools['tools'] = [{'type': 'function', 'function': {'name': 'x'}}]
        self.assertFalse(analyze_request(tools).eligible)
        fmt = payload('จัดรายการ 10 อย่าง')
        fmt['format'] = 'json'
        self.assertFalse(analyze_request(fmt).eligible)

    def test_code_numbers_are_not_counts(self):
        spec = analyze_request(payload('ช่วยดูโค้ดนี้: for i in range(5) print(i) และอธิบาย'))
        self.assertEqual(spec.expected_counts, [])
        spec2 = analyze_request(payload('เขียนโค้ด Python พิมพ์คำว่าสวัสดี 3 ครั้ง พร้อมคำอธิบาย'))
        self.assertEqual(spec2.expected_counts, [])

    def test_han_allowed_when_chinese_requested(self):
        spec = analyze_request(payload('แปลประโยคนี้เป็นภาษาจีน: สวัสดีครับ'))
        self.assertTrue(spec.allow_han)

    def test_generate_prompt_payload(self):
        spec = analyze_request({'model': 'bomai-safe', 'prompt': 'เสนอวิธีประหยัดไฟ 10 ข้อ'})
        self.assertTrue(spec.eligible)
        self.assertEqual(spec.expected_counts[0]['count'], 10)


class DetectorTests(unittest.TestCase):
    def test_prose_answer_without_list_rows_not_count_mismatch(self):
        # A complete prose answer (baseline-PASS shape) has no deterministic
        # unit structure; count_mismatch must not fire on rows==0 prose.
        spec = analyze_request(payload('แนะนำเกมเล่นกับเด็กในบ้าน 10 เกม'))
        prose = ('ควรเลือกเกมตามวัยของเด็ก เกมจำคู่ภาพช่วยพัฒนาความจำ '
                 'เกมปริศนาภาพกระตุ้นการคิดวิเคราะห์ เกมบทบาทสมมติฝึกจินตนาการ '
                 'เกมโยนห่วงฝึกกล้ามเนื้อมัดใหญ่ และควรเล่นด้วยกันทุกวันเพื่อสร้างความสัมพันธ์')
        report = assess_quality(spec, prose, 'stop', None)
        self.assertNotIn('count_mismatch', report.issues)
        self.assertNotIn('เกม', report.observed)
        # A partial LIST is still deterministically short and must fire.
        self.assertIn('count_mismatch',
                      assess_quality(spec, '1. ซ่อนของ' + chr(10) + '2. ทายตัว', 'stop', None).issues)

    def test_count_mismatch(self):
        spec = analyze_request(payload('แนะนำเกมเล่นกับเด็กในบ้าน 10 เกม'))
        report = assess_quality(spec, '1. ซ่อนของ\n2. ทายตัว', 'stop', None)
        self.assertIn('count_mismatch', report.issues)
        self.assertEqual(report.expected.get('เกม'), 10)
        self.assertEqual(report.observed.get('เกม'), 2)
        self.assertNotIn('count_mismatch',
                         assess_quality(spec, TEN_GAMES, 'stop', None).issues)

    def test_too_short_only_for_approx_words(self):
        short_spec = analyze_request(payload('เขียนเรียงความเรื่องความทรงจำ ยาวประมาณ 600 คำ'))
        self.assertIn('too_short', assess_quality(short_spec, 'สั้นมาก', 'stop', None).issues)
        one_word = analyze_request(payload('แปลคำว่า apple เป็นภาษาไทย และตอบแค่คำเดียว'))
        self.assertTrue(assess_quality(one_word, 'แอปเปิ้ล', 'stop', None).ok)

    def test_empty_and_length_and_guard(self):
        spec = analyze_request(payload('เสนอวิธีประหยัดไฟ 10 ข้อ'))
        self.assertIn('empty', assess_quality(spec, '  \n ', 'stop', None).issues)
        self.assertIn('length', assess_quality(spec, 'ตอบยาวแต่ถูกตัด', 'length', None).issues)
        self.assertIn('guard_intervention',
                      assess_quality(spec, 'ข้อความ', 'stop', {'reason': 'repeated_list_row'}).issues)

    def test_intentional_repetition_bounds(self):
        phrase = 'วันนี้อากาศดีและฉันมีความสุข'
        intentional = analyze_request(payload('คัดลอกประโยคนี้ 3 ครั้งตามคำขอ: ' + phrase))
        self.assertTrue(assess_quality(intentional, phrase * 3, 'stop', None).ok)
        self.assertFalse(assess_quality(intentional, phrase * 4, 'stop', None).ok)

    def test_adjacent_repetition_detection(self):
        spec = analyze_request(payload('แต่งเรื่องสั้นเกี่ยวกับแมวที่กลัวฝน ไม่เกิน 500 คำ'))
        unit = 'แมวตัวน้อยเดินเล่นในสวนด้วยความสุข'
        self.assertIn('adjacent_repetition', assess_quality(spec, unit * 3, 'stop', None).issues)
        two = 'ขอบคุณครับ\nขอบคุณครับ'
        self.assertNotIn('adjacent_repetition', assess_quality(spec, two, 'stop', None).issues)

    def test_token_stutter(self):
        spec = analyze_request(payload('แต่งเรื่องสั้นเกี่ยวกับแมว ไม่เกิน 500 คำ'))
        self.assertIn('token_stutter', assess_quality(spec, 'ฉันอยากไปไปไปไปตลาดด้วยกัน', 'stop', None).issues)
        self.assertNotIn('token_stutter', assess_quality(spec, 'ฉันอยากไปตลาดด้วยกันสักครั้ง', 'stop', None).issues)

    def test_code_fence_exempt(self):
        code_spec = analyze_request(payload('เขียนฟังก์ชัน Python หาค่าเฉลี่ย พร้อมตัวอย่าง'))
        text = '```python\n' + 'print("x")\n' * 4 + '```'
        self.assertTrue(assess_quality(code_spec, text, 'stop', None).ok)

    def test_refusal_with_counts_and_no_rows_is_false_refusal(self):
        # A refusal-shaped answer (no list rows) to a counted request is a
        # detectable false refusal even when the refusal prose exceeds 120
        # non-space characters.
        spec = analyze_request(payload('แนะนำหนังสือนิทานสำหรับเด็ก 5 แนว พร้อมกิจกรรมหลังอ่าน'))
        refusal = ('ผมไม่สามารถตอบคำถามนี้ได้เนื่องจากบริบทที่ให้มาไม่มีข้อมูลเกี่ยวกับหนังสือนิทาน'
                   'สำหรับเด็กที่ระบุชื่อหรือรายละเอียดเพียงพอ จึงไม่สามารถแนะนำได้ในขณะนี้ครับ')
        self.assertIn('false_refusal', assess_quality(spec, refusal, 'stop', None).issues)

    def test_paragraph_unit_single_newline_style(self):
        # Thai models often separate ย่อหน้า with single newlines; when the
        # blank-line count degenerates to 1, fall back to non-empty lines so a
        # compliant 6-paragraph story is not falsely flagged.
        spec = analyze_request(payload('เขียนเรื่องสั้นสืบสวนที่เฉลยตอนท้ายใน 6 ย่อหน้า'))
        six_single_newline = chr(10).join(
            f'ย่อหน้าที่ {n} นักสืบตามรอยเบาะแสและพบว่าคดีเชื่อมโยงถึงกันเองอย่างน่าประหลาด' for n in range(1, 7))
        self.assertNotIn('count_mismatch',
                         assess_quality(spec, six_single_newline, 'stop', None).issues)
        self.assertIn('count_mismatch',
                      assess_quality(spec, six_single_newline.split(chr(10))[0], 'stop', None).issues)

    def test_false_refusal(self):
        code_spec = analyze_request(payload('เขียนฟังก์ชัน Python หาค่าเฉลี่ย พร้อมตัวอย่าง'))
        self.assertIn('false_refusal',
                      assess_quality(code_spec, 'ผมไม่สามารถเขียนโค้ดให้ได้ครับ', 'stop', None).issues)
        spec10 = analyze_request(payload('แนะนำเกม 10 เกม'))
        self.assertIn('false_refusal',
                      assess_quality(spec10, 'ไม่มีข้อมูลสำหรับคำถามนี้ในบริบทนี้ครับ', 'stop', None).issues)
        normal = ('คำตอบทั่วไปที่มีคำว่า ในบริบทนี้ อยู่ในประโยคปกติ พร้อมคำอธิบายยาวพอสมควร และมีเนื้อหาจริงทั้งหมด')
        self.assertNotIn('false_refusal', assess_quality(spec10, normal, 'stop', None).issues)

    def test_han_leak(self):
        summary_spec = analyze_request(payload('เขียนเรียงความเรื่องความทรงจำ ยาวประมาณ 600 คำ'))
        self.assertIn('han_leak',
                      assess_quality(summary_spec, 'เพิ่มความ专注และลดเครียด', 'stop', None).issues)
        chinese = analyze_request(payload('แปลประโยคนี้เป็นภาษาจีน: สวัสดีครับ'))
        self.assertNotIn('han_leak', assess_quality(chinese, '你好世界', 'stop', None).issues)

    def test_vegetarian_violation(self):
        veg_spec = analyze_request(payload('วางแผนเมนูมังสวิรัติ 7 วัน วันละ 3 มื้อ โดยไม่ซ้ำเมนู'))
        self.assertIn('vegetarian_violation',
                      assess_quality(veg_spec, 'วันที่ 1\nเช้า ข้าวต้ม\nเย็น แกงส้มปลา', 'stop', None).issues)
        negated = 'วันที่ 1\nเช้า ข้าวต้มผัก\nเย็น ผัดผักไม่ใส่น้ำปลา'
        self.assertNotIn('vegetarian_violation',
                         assess_quality(veg_spec, negated, 'stop', None).issues)

    def test_duplicate_unit(self):
        wish_spec = analyze_request(payload('แต่งคำอวยพรวันเกิดให้คุณยาย 5 แบบที่ไม่ซ้ำกัน'))
        self.assertIn('duplicate_unit',
                      assess_quality(wish_spec, WISH_A + '\n' + WISH_A_NEAR, 'stop', None).issues)
        distinct = WISH_A + '\n' + 'ขอให้คุณยายหายจากอาการป่วยเร็ว ๆ และมีรอยยิ้มทุกวัน'
        self.assertNotIn('duplicate_unit',
                         assess_quality(wish_spec, distinct, 'stop', None).issues)

    def test_incomplete_schedule(self):
        spec = analyze_request(payload('วางแผนเมนูมังสวิรัติ 7 วัน วันละ 3 มื้อ โดยไม่ซ้ำเมนู'))
        six_days = '\n'.join(
            f'วันที่ {d}\nเช้า ข้าวต้มผัก {d}\nกลางวัน ผัดผัก {d}\nเย็น แกงเห็ด {d}'
            for d in range(1, 7))
        self.assertIn('incomplete_schedule', assess_quality(spec, six_days, 'stop', None).issues)
        seven_days = '\n'.join(
            f'วันที่ {d}\nเช้า ข้าวต้มผัก {d}\nกลางวัน ผัดผัก {d}\nเย็น แกงเห็ด {d}'
            for d in range(1, 8))
        self.assertNotIn('incomplete_schedule',
                         assess_quality(spec, seven_days, 'stop', None).issues)

    def test_raw_markup(self):
        spec = analyze_request(payload('เสนอวิธีประหยัดไฟ 10 ข้อ'))
        self.assertIn('raw_markup',
                      assess_quality(spec, '<context>ข้อมูลดิบ</context> คำตอบ', 'stop', None).issues)
        self.assertIn('raw_markup',
                      assess_quality(spec, 'connection refused ตอบไม่ได้', 'stop', None).issues)

    def test_config_g_and_system_locked(self):
        self.assertEqual(CONFIG_G['temperature'], 0.6)
        self.assertEqual(CONFIG_G['num_ctx'], 8192)
        self.assertEqual(CONFIG_G['think'] if 'think' in CONFIG_G else None, None)
        self.assertEqual(len(SYSTEM_PROMPT.strip().splitlines()), 3)
        self.assertEqual(MAX_QUALITY_REWRITES, 1)
        self.assertEqual(MAX_PASS1_FOR_REWRITE_SECONDS, 240.0)
        self.assertEqual(QUALITY_TOTAL_BUDGET_SECONDS, 540.0)


class CorpusControlTests(unittest.TestCase):
    """All 52 corpus prompts run through analyze_request without errors and
    classification follows the blueprint eligibility rules."""

    def test_all_52_analyze_without_error(self):
        for row in CORPUS:
            spec = analyze_request(payload(row['prompt']))
            self.assertIsInstance(spec.eligible, bool, row['id'])
            self.assertIsInstance(spec.expected_counts, list, row['id'])

    def test_primary_candidates_eligible(self):
        eligible_ids = {
            'S002', 'S003', 'S005', 'S006', 'S007', 'S008', 'S009', 'S010',
            'S011', 'S012', 'S013', 'S014', 'S015', 'S016', 'S017', 'S018',
            'S022', 'S026', 'S030', 'S031', 'S039', 'S040', 'S004', 'S001'}
        for cid in sorted(eligible_ids):
            self.assertTrue(analyze_request(payload(BY_ID[cid]['prompt'])).eligible, cid)

    def test_history_and_gravity_not_structured(self):
        for cid in ('S019', 'S024'):
            spec = analyze_request(payload(BY_ID[cid]['prompt']))
            self.assertFalse(spec.eligible, cid)
            self.assertEqual(spec.expected_counts, [], cid)

    def test_owui_rag_template_context_does_not_pollute_analysis(self):
        template = (
            '### Task:\nRespond to the user query using the provided context.\n'
            '### Guidelines:\n- If you don\'t know the answer, clearly state that.\n'
            '<context>\n<source id="1">บทความแนะนำ 5 วิธีจัดการความโกรธ และ 10 อย่างที่ควรทำ</source>\n'
            '</context>\n')
        safety = analyze_request(payload(
            template + 'ฉันโกรธเพื่อนมาก อยากทำร้ายเขา ช่วยหาวิธีจัดการอารมณ์อย่างสร้างสรรค์'))
        self.assertFalse(safety.eligible)
        self.assertEqual(safety.expected_counts, [])
        news = analyze_request(payload(
            template + 'สรุปข่าวสำคัญของประเทศไทยวันนี้ พร้อมแหล่งอ้างอิง'))
        self.assertFalse(news.eligible)
        self.assertEqual(news.expected_counts, [])
        structured = analyze_request(payload(
            template + 'แนะนำเกมเล่นกับเด็กในบ้าน 10 เกม'))
        self.assertTrue(structured.eligible)
        self.assertEqual(structured.expected_counts[0]['count'], 10)


class FeedbackAndPayloadTests(unittest.TestCase):
    def setUp(self):
        self.spec = analyze_request(payload('แนะนำเกมเล่นกับเด็กในบ้าน 10 เกม'))
        self.report = assess_quality(self.spec, '1. ซ่อนของ\n2. ทายตัว', 'stop', None)
        self.original = payload('แนะนำเกมเล่นกับเด็กในบ้าน 10 เกม')
        self.original['messages'] = [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': 'แนะนำเกมเล่นกับเด็กในบ้าน 10 เกม'}]
        self.original['options'] = dict(CONFIG_G)
        self.original['stream'] = True

    def test_feedback_bounded_and_no_draft(self):
        text = rewrite_feedback(self.report)
        self.assertLessEqual(len(text), MAX_REWRITE_FEEDBACK_CHARS)
        self.assertTrue(text.endswith('ตอบคำถามเดิมใหม่ทั้งหมด ไม่ต้องอธิบายการแก้ไข'))
        self.assertNotIn('ซ่อนของ', text)
        self.assertNotIn('ทายตัว', text)
        self.assertIn('10', text)

    def test_feedback_has_no_host_or_case_ids(self):
        text = rewrite_feedback(self.report)
        for token in ('windows', 'macos', 'linux', 'ubuntu', 'S0', 'host', 'tier'):
            self.assertNotIn(token, text)

    def test_build_rewrite_payload_chat_contract(self):
        result = build_rewrite_payload(self.original, self.report)
        system = [m for m in result['messages'] if m.get('role') == 'system']
        self.assertEqual(len(system), 1)
        self.assertEqual(system[0]['content'], SYSTEM_PROMPT)
        users = [m for m in result['messages']
                 if m.get('role') == 'user' and not str(m.get('content', '')).startswith(SOURCE_GUIDANCE)]
        original_users = [m for m in self.original['messages'] if m.get('role') == 'user']
        original_text = original_users[0]['content']
        self.assertTrue(users[0]['content'].startswith(original_text))
        self.assertIn(rewrite_feedback(self.report), users[0]['content'])
        self.assertEqual(result['options'], dict(CONFIG_G))
        self.assertIs(result['think'], False)
        self.assertIs(result['stream'], False)
        # Original payload is not mutated.
        self.assertEqual(self.original['stream'], True)
        self.assertNotIn(rewrite_feedback(self.report), original_text)

    def test_build_rewrite_payload_no_recursive_append(self):
        once = build_rewrite_payload(self.original, self.report)
        twice = build_rewrite_payload(self.original, self.report)
        feedback = rewrite_feedback(self.report)
        self.assertEqual(once['messages'][-1]['content'].count(feedback), 1)
        self.assertEqual(once['messages'][-1]['content'], twice['messages'][-1]['content'])

    def test_build_rewrite_payload_preserves_retrieval_order(self):
        with_source = payload('แนะนำเกม 10 เกม')
        with_source['messages'] = [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': SOURCE_GUIDANCE + '\n\n<context>\nข้อมูล\n</context>'},
            {'role': 'user', 'content': 'แนะนำเกม 10 เกม'}]
        with_source['options'] = dict(CONFIG_G)
        result = build_rewrite_payload(with_source, self.report)
        self.assertEqual(result['messages'][0]['role'], 'system')
        self.assertTrue(result['messages'][1]['content'].startswith(SOURCE_GUIDANCE))
        self.assertNotIn(rewrite_feedback(self.report), result['messages'][1]['content'])
        self.assertTrue(result['messages'][2]['content'].endswith(rewrite_feedback(self.report)))

    def test_build_rewrite_payload_generate_contract(self):
        native = {'model': 'bomai-safe', 'prompt': 'เสนอวิธีประหยัดไฟ 10 ข้อ',
                  'stream': True, 'options': dict(CONFIG_G), 'think': False}
        result = build_rewrite_payload(native, self.report)
        self.assertTrue(result['prompt'].startswith('เสนอวิธีประหยัดไฟ 10 ข้อ'))
        self.assertTrue(result['prompt'].endswith(rewrite_feedback(self.report)))
        self.assertIs(result['stream'], False)

    def test_merge_attempt_metrics_sums(self):
        first = {'model': 'bomai-safe', 'prompt_eval_count': 120, 'eval_count': 340,
                 'load_duration': 1000000, 'total_duration': 9000000000,
                 'done': True, 'message': {'role': 'assistant', 'content': 'a'}}
        second = {'model': 'bomai-safe', 'prompt_eval_count': 140, 'eval_count': 280,
                  'load_duration': 200000, 'total_duration': 7000000000,
                  'done': True, 'done_reason': 'stop',
                  'message': {'role': 'assistant', 'content': 'b'}}
        merged = merge_attempt_metrics([first, second])
        self.assertEqual(merged['prompt_eval_count'], 260)
        self.assertEqual(merged['eval_count'], 620)
        self.assertEqual(merged['load_duration'], 1200000)
        self.assertEqual(merged['total_duration'], 16000000000)
        self.assertEqual(merged['done_reason'], 'stop')
        self.assertEqual(merged['message']['content'], 'b')


CLEAN_NATIVE = {'model': 'bomai-safe',
                'message': {'role': 'assistant', 'content': TEN_GAMES},
                'done': True, 'done_reason': 'stop',
                'prompt_eval_count': 100, 'eval_count': 50,
                'load_duration': 45, 'total_duration': 123456}
BAD_REPEAT_NATIVE = {'model': 'bomai-safe',
                     'message': {'role': 'assistant',
                                 'content': 'แมวตัวน้อยเดินเล่นในสวนด้วยความสุข' * 3},
                     'done': True, 'done_reason': 'stop',
                     'prompt_eval_count': 100, 'eval_count': 50}
EMPTY_NATIVE = {'model': 'bomai-safe', 'message': {'role': 'assistant', 'content': ''},
                'done': True, 'done_reason': 'stop',
                'prompt_eval_count': 100, 'eval_count': 50}
OVERFLOW_BODY = {'error': 'request (9423 tokens) exceeds the available context size (8192 tokens)'}


class QualityFakeOllama(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, *_):
        pass

    def _send(self, status, obj):
        data = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == '/api/version':
            self._send(200, {'version': '0.40.13'})
        else:
            self._send(200, {'models': [{'name': 'bomai-safe:latest'}]})

    def do_POST(self):
        server = self.server
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        with server.lock:
            server.calls.append(body)
            index = len(server.calls) - 1
            server.active += 1
            server.max_active = max(server.max_active, server.active)
        try:
            time.sleep(server.delay)
            script = server.script[index] if index < len(server.script) else server.default
            if isinstance(script, tuple):
                self._send(script[0], script[1])
            else:
                self._send(200, script)
        finally:
            with server.lock:
                server.active -= 1


class QualityGatewayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.ollama = ThreadingHTTPServer(('127.0.0.1', 0), QualityFakeOllama)
        cls.ollama.calls, cls.ollama.script, cls.ollama.default = [], [], dict(CLEAN_NATIVE)
        cls.ollama.delay, cls.ollama.active, cls.ollama.max_active = 0.0, 0, 0
        cls.ollama.lock = threading.Lock()
        cls.thread = threading.Thread(target=cls.ollama.serve_forever, daemon=True)
        cls.thread.start()
        cls.key = 'test-quality-key-' + 'z' * 32
        cls.log_path = Path(cls.tmp.name) / 'events.jsonl'
        cls.gateway = RuntimeServer(
            ('127.0.0.1', 0), f'http://127.0.0.1:{cls.ollama.server_port}',
            catalog=Path(__file__).resolve().parents[1] / 'runtime' / 'models.json',
            log=str(cls.log_path), gateway_key=cls.key, model_alias='bomai-safe')
        cls.gt = threading.Thread(target=cls.gateway.serve_forever, daemon=True)
        cls.gt.start()
        cls.url = f'http://127.0.0.1:{cls.gateway.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.gateway.shutdown(); cls.gateway.server_close()
        cls.ollama.shutdown(); cls.ollama.server_close()
        cls.tmp.cleanup()

    def setUp(self):
        self.ollama.calls.clear()
        self.ollama.script = []
        self.ollama.default = dict(CLEAN_NATIVE)
        self.ollama.delay = 0.0

    def post(self, path, body):
        req = urllib.request.Request(
            self.url + path, data=json.dumps(body, ensure_ascii=False).encode(),
            headers={'Content-Type': 'application/json',
                     'Authorization': 'Bearer ' + self.key})
        return urllib.request.urlopen(req, timeout=30)

    def chat(self, text, **extra):
        body = {'model': 'bomai-safe', 'stream': False,
                'messages': [{'role': 'user', 'content': text}]}
        body.update(extra)
        return body

    def chat_on(self, text, **extra):
        body = self.chat(text, **extra)
        body['think'] = True
        return body

    def test_clean_pass1_single_generation(self):
        with self.post('/api/chat', self.chat_on('แนะนำเกมเล่นกับเด็กในบ้าน 10 เกม')) as response:
            result = json.load(response)
        self.assertEqual(len(self.ollama.calls), 1)
        self.assertEqual(result['message']['content'], TEN_GAMES)
        quality = result['bomai_quality']
        self.assertEqual(quality['attempts'], 1)
        self.assertFalse(quality['rewritten'])
        self.assertFalse(quality['exhausted'])

    def test_repetitive_pass1_recovered_stream(self):
        self.ollama.script = [dict(BAD_REPEAT_NATIVE), dict(CLEAN_NATIVE)]
        body = self.chat_on('แนะนำเกมเล่นกับเด็กในบ้าน 10 เกม', stream=True)
        with self.post('/api/chat', body) as response:
            raw = response.read().decode('utf-8')
        self.assertEqual(len(self.ollama.calls), 2)
        records = [json.loads(line) for line in raw.splitlines() if line.strip()]
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['message']['content'], TEN_GAMES)
        self.assertNotIn('แมวตัวน้อย', raw)
        quality = records[0]['bomai_quality']
        self.assertEqual(quality['attempts'], 2)
        self.assertTrue(quality['rewritten'])
        self.assertTrue(quality['recovered'])
        self.assertIn('adjacent_repetition', quality['issues'])
        self.assertTrue(records[0]['done'])
        second_user = [m for m in self.ollama.calls[1]['messages']
                       if m.get('role') == 'user'][-1]['content']
        self.assertNotIn('แมวตัวน้อย', second_user)
        self.assertNotIn(TEN_GAMES, second_user)
        self.assertTrue(second_user.startswith('แนะนำเกมเล่นกับเด็กในบ้าน 10 เกม'))
        self.assertEqual(self.ollama.calls[1]['options'], CONFIG_G)
        self.assertIs(self.ollama.calls[1]['think'], False)

    def test_incomplete_count_recovered_openai_usage_summed(self):
        partial = dict(CLEAN_NATIVE)
        partial['message'] = {'role': 'assistant', 'content': '1. ซ่อนของ\n2. ทายตัว'}
        self.ollama.script = [partial, dict(CLEAN_NATIVE)]
        body = self.chat_on('แนะนำเกมเล่นกับเด็กในบ้าน 10 เกม')
        with self.post('/v1/chat/completions', body) as response:
            result = json.load(response)
        self.assertEqual(len(self.ollama.calls), 2)
        self.assertEqual(result['choices'][0]['message']['content'], TEN_GAMES)
        self.assertTrue(result['bomai_quality']['recovered'])
        self.assertEqual(result['usage']['prompt_tokens'], 200)
        self.assertEqual(result['usage']['completion_tokens'], 100)
        self.assertEqual(result['usage']['total_tokens'], 300)

    def test_bad_both_passes_exhausted_notice(self):
        self.ollama.script = [dict(BAD_REPEAT_NATIVE), dict(BAD_REPEAT_NATIVE)]
        with self.post('/api/chat', self.chat_on('แนะนำเกมเล่นกับเด็กในบ้าน 10 เกม')) as response:
            result = json.load(response)
        self.assertEqual(len(self.ollama.calls), 2)
        self.assertEqual(result['message']['content'], QUALITY_FAILURE_NOTICE)
        self.assertEqual(result['done_reason'], 'stop')
        self.assertTrue(result['bomai_quality']['exhausted'])
        self.assertEqual(result['bomai_quality']['attempts'], 2)
        self.assertNotIn('แมวตัวน้อย', json.dumps(result, ensure_ascii=False))

    def test_slow_pass1_skips_pass2(self):
        import bom_runtime
        old = bom_runtime.MAX_PASS1_FOR_REWRITE_SECONDS
        bom_runtime.MAX_PASS1_FOR_REWRITE_SECONDS = -1.0
        try:
            self.ollama.script = [dict(BAD_REPEAT_NATIVE)]
            with self.post('/api/chat', self.chat_on('แนะนำเกมเล่นกับเด็กในบ้าน 10 เกม')) as response:
                result = json.load(response)
        finally:
            bom_runtime.MAX_PASS1_FOR_REWRITE_SECONDS = old
        self.assertEqual(len(self.ollama.calls), 1)
        self.assertEqual(result['message']['content'], QUALITY_FAILURE_NOTICE)
        self.assertTrue(result['bomai_quality']['exhausted'])
        self.assertEqual(result['bomai_quality']['attempts'], 1)

    def test_pass2_transport_failure_no_bad_fallback(self):
        self.ollama.script = [dict(BAD_REPEAT_NATIVE), (500, {'error': 'upstream boom'})]
        with self.post('/api/chat', self.chat_on('แนะนำเกมเล่นกับเด็กในบ้าน 10 เกม')) as response:
            result = json.load(response)
        self.assertEqual(len(self.ollama.calls), 2)
        self.assertEqual(result['message']['content'], QUALITY_FAILURE_NOTICE)
        self.assertTrue(result['bomai_quality']['exhausted'])
        self.assertNotIn('แมวตัวน้อย', json.dumps(result, ensure_ascii=False))

    def test_context_overflow_bounded_two_drafts(self):
        big = self.chat_on('แนะนำเกมเล่นกับเด็กในบ้าน 10 เกม')
        big['messages'] = [
            {'role': 'system', 'content': '<context>' + '<source id="1">' + ('ข้อมูลผลค้นหา ' * 80)
             + '</source>' + '<source id="2">' + ('ข้อมูลเพิ่มเติม ' * 80) + '</source></context>'},
            {'role': 'user', 'content': 'แนะนำเกมเล่นกับเด็กในบ้าน 10 เกม'}]
        self.ollama.script = [(400, OVERFLOW_BODY), (400, OVERFLOW_BODY), dict(BAD_REPEAT_NATIVE),
                              (400, OVERFLOW_BODY), (400, OVERFLOW_BODY), dict(CLEAN_NATIVE)]
        with self.post('/api/chat', big) as response:
            result = json.load(response)
        self.assertEqual(len(self.ollama.calls), 6)
        self.assertEqual(result['message']['content'], TEN_GAMES)
        self.assertTrue(result['bomai_quality']['recovered'])
        self.assertEqual(result['bomai_quality']['attempts'], 2)

    def test_empty_pass1_uses_quality_rewrite_not_502(self):
        self.ollama.script = [dict(EMPTY_NATIVE), dict(CLEAN_NATIVE)]
        with self.post('/api/chat', self.chat_on('แนะนำเกมเล่นกับเด็กในบ้าน 10 เกม')) as response:
            result = json.load(response)
        self.assertEqual(len(self.ollama.calls), 2)
        self.assertEqual(result['message']['content'], TEN_GAMES)
        self.assertTrue(result['bomai_quality']['recovered'])
        self.assertIn('empty', result['bomai_quality']['issues'])

    def test_live_request_not_quality_path(self):
        body = self.chat('ราคาทองวันนี้เท่าไหร่ ขอแหล่งข้อมูลและเวลาที่อัปเดต')
        body['messages'].insert(0, {'role': 'system', 'content':
                                    '<source id="1">https://gold.example.com/api ราคาทอง 41,000 บาท 2026-11-01</source>'})
        good_live = dict(CLEAN_NATIVE)
        good_live['message'] = {'role': 'assistant',
                                'content': 'ราคาทองวันนี้ 41,000 บาท อัปเดต 2026-11-01 อ้างอิง https://gold.example.com/api และ https://gold2.example.com/price'}
        self.ollama.default = good_live
        with self.post('/api/chat', body) as response:
            result = json.load(response)
        self.assertEqual(len(self.ollama.calls), 1)
        self.assertNotIn('bomai_quality', result)

    def test_vision_request_not_quality_path(self):
        body = self.chat('อ่านข้อความในภาพ')
        body['messages'][0]['images'] = ['aGk=']
        with self.post('/api/chat', body) as response:
            result = json.load(response)
        self.assertEqual(len(self.ollama.calls), 1)
        self.assertNotIn('bomai_quality', result)

    def test_openai_sse_single_done(self):
        self.ollama.script = [dict(BAD_REPEAT_NATIVE), dict(CLEAN_NATIVE)]
        body = self.chat_on('แนะนำเกมเล่นกับเด็กในบ้าน 10 เกม', stream=True)
        with self.post('/v1/chat/completions', body) as response:
            raw = response.read().decode('utf-8')
        self.assertEqual(raw.count('data: [DONE]'), 1)
        records = [json.loads(l[6:]) for l in raw.splitlines()
                   if l.startswith('data: ') and l != 'data: [DONE]']
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['choices'][0]['finish_reason'], 'stop')
        self.assertEqual(records[0]['model'], 'bomai-safe')
        self.assertTrue(records[0]['bomai_quality']['recovered'])

    def test_concurrency_single_inference_slot(self):
        self.ollama.delay = 0.2
        results = []

        def worker():
            with self.post('/api/chat', self.chat_on('แนะนำเกมเล่นกับเด็กในบ้าน 10 เกม')) as response:
                results.append(json.load(response))

        threads = [threading.Thread(target=worker) for _ in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(len(results), 2)
        self.assertEqual(self.ollama.max_active, 1)
        for result in results:
            self.assertEqual(result['message']['content'], TEN_GAMES)

    def test_logs_contain_no_content(self):
        self.ollama.script = [dict(BAD_REPEAT_NATIVE), dict(CLEAN_NATIVE)]
        with self.post('/api/chat', self.chat_on('แนะนำเกมเล่นกับเด็กในบ้าน 10 เกม')) as response:
            json.load(response)
        log_text = self.log_path.read_text(encoding='utf-8')
        self.assertIn('quality_rewrite_started', log_text)
        self.assertNotIn('แมวตัวน้อย', log_text)
        self.assertNotIn('แนะนำเกมเล่นกับเด็ก', log_text)
        self.assertNotIn(self.key, log_text)


class ThinkingGateTests(QualityGatewayTests):
    """Phase 5 contract: OFF (default) = one pass; ON = bounded two-pass."""

    def test_off_defective_answer_single_pass(self):
        self.ollama.script = [dict(BAD_REPEAT_NATIVE)]
        with self.post('/api/chat', self.chat('แนะนำเกมเล่นกับเครื่องในบ้าน 10 เกม')) as response:
            result = json.load(response)
        self.assertEqual(len(self.ollama.calls), 1)
        self.assertNotIn('bomai_quality', result)

    def test_reasoning_effort_high_enables_rewrite(self):
        self.ollama.script = [dict(BAD_REPEAT_NATIVE), dict(CLEAN_NATIVE)]
        body = self.chat('แนะนำเกมเล่นกับเด็กในบ้าน 10 เกม')
        body['reasoning_effort'] = 'high'
        with self.post('/api/chat', body) as response:
            result = json.load(response)
        self.assertEqual(len(self.ollama.calls), 2)
        self.assertTrue(result['bomai_quality']['recovered'])
        self.assertEqual(result['bomai_quality']['trigger'], 'thinking_button')

    def test_reasoning_dict_effort_enables_rewrite(self):
        self.ollama.script = [dict(BAD_REPEAT_NATIVE), dict(CLEAN_NATIVE)]
        body = self.chat('แนะนำเกมเล่นกับเด็กในบ้าน 10 เกม')
        body['reasoning'] = {'effort': 'max'}
        with self.post('/api/chat', body) as response:
            result = json.load(response)
        self.assertEqual(len(self.ollama.calls), 2)
        self.assertTrue(result['bomai_quality']['recovered'])

    def test_options_think_enables_rewrite(self):
        self.ollama.script = [dict(BAD_REPEAT_NATIVE), dict(CLEAN_NATIVE)]
        body = self.chat('แนะนำเกมเล่นกับเด็กในบ้าน 10 เกม')
        body['options'] = {'think': True}
        with self.post('/api/chat', body) as response:
            result = json.load(response)
        self.assertEqual(len(self.ollama.calls), 2)
        self.assertTrue(result['bomai_quality']['recovered'])

    def test_explicit_false_overrides_effort(self):
        self.ollama.script = [dict(BAD_REPEAT_NATIVE)]
        body = self.chat('แนะนำเกมเล่นกับเด็กในบ้าน 10 เกม')
        body['reasoning_effort'] = 'high'
        body['think'] = False
        with self.post('/api/chat', body) as response:
            result = json.load(response)
        self.assertEqual(len(self.ollama.calls), 1)
        self.assertNotIn('bomai_quality', result)

    def test_invalid_think_string_400(self):
        body = self.chat('สวัสดี')
        body['think'] = 'yes'
        req = urllib.request.Request(
            self.url + '/api/chat', data=json.dumps(body).encode(),
            headers={'Content-Type': 'application/json',
                     'Authorization': 'Bearer ' + self.key})
        with self.assertRaises(urllib.error.HTTPError) as raised:
            urllib.request.urlopen(req, timeout=30)
        self.assertEqual(raised.exception.code, 400)

    def test_invalid_effort_400(self):
        body = self.chat('สวัสดี')
        body['reasoning_effort'] = 'warp'
        req = urllib.request.Request(
            self.url + '/api/chat', data=json.dumps(body).encode(),
            headers={'Content-Type': 'application/json',
                     'Authorization': 'Bearer ' + self.key})
        with self.assertRaises(urllib.error.HTTPError) as raised:
            urllib.request.urlopen(req, timeout=30)
        self.assertEqual(raised.exception.code, 400)

    def test_upstream_think_false_and_locked_options_every_call(self):
        self.ollama.script = [dict(BAD_REPEAT_NATIVE), dict(CLEAN_NATIVE)]
        with self.post('/api/chat', self.chat_on('แนะนำเกมเล่นกับเด็กในบ้าน 10 เกม')) as response:
            json.load(response)
        self.assertEqual(len(self.ollama.calls), 2)
        for call in self.ollama.calls:
            self.assertIs(call.get('think'), False)
            self.assertEqual(call.get('options'), CONFIG_G)

    def test_no_reasoning_fields_exposed_on(self):
        self.ollama.script = [dict(BAD_REPEAT_NATIVE), dict(CLEAN_NATIVE)]
        with self.post('/api/chat', self.chat_on('แนะนำเกมเล่นกับเด็กในบ้าน 10 เกม')) as response:
            result = json.load(response)
        dumped = json.dumps(result, ensure_ascii=False)
        for key in ('reasoning', 'reasoning_content', 'thinking'):
            self.assertNotIn("'" + key + "'", dumped.replace('"', "'"))


if __name__ == '__main__':
    unittest.main(verbosity=2)
