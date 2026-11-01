"""Behavioral regressions for compact review records and derived upload data."""
import copy
import tempfile
import unittest
from pathlib import Path

import creator_markdown_check as c
from reference_map import build_map, markdown


NO_IMAGE = "无（创作者已明确选择文生视频）"


def shot(n, *, refs=NO_IMAGE, seconds=2, group=True):
    start = (n - 1) * 2
    return f'''## SHOT-EP001-{n:03d} · 门边交接
- 来源：EP001-SC001（原文：“甲站在门边。”）
- 时长：{seconds}s
- 图片提示词项：无
- 视觉依据：无
- 输入参考图：{refs}
- 生成组：{'GROUP-EP001-01，组内'+str(start)+'—'+str(start+seconds)+'s' if group else '无'}
- 起点：甲右手在门边。
- 唯一动作：右手接物后托稳。
- 动作过程：0—1s伸手接触，1—2s托稳后对方松手。
- 景别/机位：中近景，门左侧。
- 运镜：固定。
- 终点：甲右手托稳。
- 声音：甲说：“你先接稳。”；末尾留反应。
### 冻结关键帧提示词
> 门边两只手尚未接触。
'''


def review(n, *, refs=NO_IMAGE):
    return f'''## MOTION-EP001-{n:03d} · 门边交接
- 审查模式：GROUP成员
- 所属GROUP：GROUP-EP001-01
- 分镜：SHOT-EP001-{n:03d}
- 时长：2s
- 生成方式：{'文生视频' if refs == NO_IMAGE else '图生视频'}
- 输入参考图：{refs}
- 静态视觉锚点：灰色袖口，冷色门框。
- 起始帧：门边两只手尚未接触。
- 状态链：伸手接触后托稳。
- 动作过程：0—1s伸手接触，1—2s托稳后对方松手。
- 景别/机位：中近景，门左侧。
- 运镜：固定。
- 终点：甲右手托稳。
- 声音：甲说：“你先接稳。”；末尾留反应。
'''


def group(members=(1, 2), prompt=None):
    prompt = prompt or '灰色袖口，冷色门框。镜头1右手先接触后承重，甲说：“你先接稳。”。镜头2对方承稳才松手。'
    return ('## GROUP-EP001-01 · 门边交接\n- 成员：' +
            '、'.join(f'MOTION-EP001-{n:03d}' for n in members) +
            f'\n- 时长：{2 * len(members)}s\n### 可复制提示词\n> {prompt}\n')


def docs(video=None):
    return {'剧本.md': '# EP001\n## EP001-SC001 外 · 门边 · 日\n甲站在门边。\n甲：你先接稳。\n',
            '视觉设定.md': '# 视觉设定\n',
            '分镜.md': '# 分镜\n' + shot(1) + shot(2),
            '视频提示词.md': video or (review(1) + review(2) + group())}


def plan(slot='PLAN-HERO', entry='IMG-HERO', purpose='身份', control='同一面貌'):
    return f'{slot}（顺序：1）· {entry}《人物参考》（用途：{purpose}；控制：{control}；不得控制：动作）'


class ReviewRecordTests(unittest.TestCase):
    def check(self, video):
        return c.validate_documents(docs(video), None, partial=True)

    def test_compact_members_pass_without_duplicate_bodies(self):
        self.assertEqual([], self.check(review(1) + review(2) + group()))

    def test_legacy_promptless_motion_still_fails(self):
        errors = self.check(review(1).replace('- 审查模式：GROUP成员\n', '') + review(2) + group())
        self.assertTrue(any('缺少唯一且非空的可复制提示词' in e for e in errors))

    def test_orphan_review_cannot_become_a_singleton(self):
        self.assertTrue(any('必须且只能' in e for e in self.check(review(1) + review(2))))

    def test_claimed_group_must_match_actual_membership(self):
        errors = self.check(review(1).replace('所属GROUP：GROUP-EP001-01', '所属GROUP：GROUP-EP001-02') + review(2) + group())
        self.assertTrue(any('必须且只能' in e for e in errors))

    def test_duplicate_membership_stays_invalid(self):
        errors = self.check(review(1) + review(2) + group() + group().replace('GROUP-EP001-01', 'GROUP-EP001-02'))
        self.assertTrue(any('只能' in e for e in errors))

    def test_malformed_group_body_does_not_exempt_member(self):
        errors = self.check(review(1) + review(2) + group().replace('> 灰色', '灰色'))
        self.assertTrue(any('正式正文' in e or '可复制提示词' in e for e in errors))

    def test_missing_required_review_field_fails(self):
        errors = self.check(review(1).replace('- 动作过程：0—1s伸手接触，1—2s托稳后对方松手。\n', '') + review(2) + group())
        self.assertTrue(any('动作过程' in e for e in errors))

    def test_source_handoff_and_sound_cannot_drift(self):
        for before, after in [('1—2s托稳后对方松手', '1—2s提前松手'), ('你先接稳。', '马上放手。')]:
            with self.subTest(before=before):
                errors = self.check(review(1).replace(before, after) + review(2) + group())
                self.assertTrue(any('原样继承' in e for e in errors))

    def test_group_must_carry_member_literal_and_text_anchor(self):
        for before, after in [('你先接稳。', '换了台词。'), ('灰色袖口，冷色门框。', '门边。')]:
            with self.subTest(before=before):
                errors = self.check(review(1) + review(2) + group().replace(before, after))
                self.assertTrue(any('遗漏或改写' in e or '静态视觉锚点' in e for e in errors))

    def test_post_captions_do_not_become_generated_dialogue(self):
        value = '甲说：“你先接稳。”；后期显示“一个月后。”；字幕：“数月后，大旱。”'
        self.assertEqual(['你先接稳。'], c._review_sound_literals(value))
        self.assertEqual(['你先接稳。'], c._review_sound_literals('甲说“你先接稳。”'))

    def test_review_flag_cannot_hide_an_extra_body(self):
        errors = self.check(review(1) + '\n### 可复制提示词\n> 另一次生成。\n' + review(2) + group())
        self.assertTrue(any('不另写' in e for e in errors))

    def test_locks_are_still_required_in_actual_group(self):
        errors = []
        c._check_continuity_locks(
            [c.ContinuityLock('LOCK-A', '银色口哨', ['全集'], [], None)], shots=None,
            motion_by_shot={'SHOT-001': ('MOTION-001', review(1), None)}, image_prompts=None,
            groups={'GROUP-001': (['SHOT-001'], '普通衣服。')}, errors=errors)
        self.assertTrue(any('GROUP-001' in e and '锁面' in e for e in errors))


class DerivedMapTests(unittest.TestCase):
    def test_same_plan_board_merges_upload_not_roles(self):
        first = plan()
        second = plan('PLAN-LOOK', purpose='造型状态', control='古装袖口')
        data = build_map(shot(1, refs=first) + shot(2, refs=second))
        unit = data['units'][0]
        self.assertEqual(1, len(unit['images']))
        self.assertEqual(['身份', '造型状态'], [r['purpose'] for r in unit['images'][0]['roles']])
        self.assertEqual([1, 1], [m['unit_number'] for m in unit['mapping']])
        self.assertTrue(unit['has_plan'])
        self.assertFalse(data['production_ready'])

    def test_same_character_different_state_entries_do_not_merge(self):
        unit = build_map(shot(1, refs=plan(entry='IMG-DRY')) + shot(2, refs=plan(entry='IMG-WET')))['units'][0]
        self.assertEqual(2, len(unit['images']))

    def test_explicit_slot_order_wins_over_written_order(self):
        first = plan('PLAN-A', entry='IMG-A')
        second = plan('PLAN-B', entry='IMG-B').replace('顺序：1', '顺序：2')
        unit = build_map(shot(1, refs=second + '；' + first))['units'][0]
        self.assertEqual(['IMG-A', 'IMG-B'], [ref['locator'] for ref in unit['images']])
        self.assertEqual([1, 2], [r['source_order'] for r in unit['mapping']])

    def test_timing_is_fractional_and_never_rounded(self):
        board = shot(1, seconds=1.5).replace('0—1.5s', '0—1.5s')
        board += shot(2, seconds=2.5).replace('组内2—4.5s', '组内1.5—4s')
        unit = build_map(board)['units'][0]
        self.assertEqual([(0, 1.5), (1.5, 4)], [(x['start'], x['end']) for x in unit['timeline']])

    def test_bad_source_window_and_duplicate_groups_fail(self):
        with self.assertRaisesRegex(ValueError, '累计秒段'):
            build_map(shot(1) + shot(2).replace('组内2—4s', '组内3—5s'))
        with self.assertRaisesRegex(ValueError, '重复'):
            build_map(shot(1) + shot(2), review(1) + review(2) + group((1, 1)))

    def test_pending_reference_never_turns_into_text_mode(self):
        with self.assertRaises(ValueError):
            build_map(shot(1, refs='无（待补参考图：人物身份）'))

    def test_loose_shot_counted_once_in_mixed_route(self):
        data = build_map(shot(1) + shot(2) + shot(3, group=False))
        self.assertEqual(6, data['seconds'])
        self.assertEqual(['GROUP', 'loose'], [u['type'] for u in data['units']])
        with self.assertRaisesRegex(ValueError, 'groups_only'):
            build_map(shot(1) + shot(2) + shot(3, group=False), profile={'delivery_route': 'groups_only'})

    def test_unknown_video_input_is_not_silently_dropped(self):
        with self.assertRaisesRegex(ValueError, '参考视频'):
            build_map(shot(1) + '- 参考视频：已有片段\n')

    def test_budget_applies_to_whole_group(self):
        with self.assertRaisesRegex(ValueError, '超过上限'):
            build_map(shot(1, refs=plan(entry='IMG-A')) + shot(2, refs=plan(entry='IMG-B')), profile={'images': 1})

    def test_low_cost_and_explicit_mode_are_not_bypassed(self):
        with self.assertRaisesRegex(ValueError, '5/10/15'):
            build_map(shot(1) + shot(2), profile={'allowed_seconds': (5, 10, 15)})
        with self.assertRaisesRegex(ValueError, '文生模式'):
            build_map(shot(1, refs=plan()), explicit_mode='text')

    def test_file_existence_and_no_content_hash_dedup(self):
        # No temporary images are generated: these are byte files solely for
        # testing file identity and existence, not accepted visual references.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ['a.png', 'b.png']:
                (root / name).write_bytes(b'test-path-only')
            def ref(name):
                return f'REF-HERO（顺序：1）· {name}《人物参考》（用途：身份；控制：面貌；不得控制：动作）'
            unit = build_map(shot(1, refs=ref('a.png')) + shot(2, refs=ref('b.png')), root=root)['units'][0]
            self.assertEqual(2, len(unit['images']))
            with self.assertRaises(ValueError):
                build_map(shot(1, refs=ref('missing.png')), root=root)

    def test_audio_numbers_are_separate_and_roles_survive(self):
        audio = 'REF-VOICE（顺序：1）· voice.wav《人物音色》（用途：音色；角色：甲；控制：音色；不得控制：台词、语气、情绪）'
        video = review(1, refs=plan()) + '- 参考音频：' + audio + '\n' + review(2, refs=plan()) + group()
        unit = build_map(shot(1, refs=plan()) + shot(2, refs=plan()), video)['units'][0]
        self.assertEqual(1, unit['images'][0]['number'])
        self.assertEqual(1, unit['audios'][0]['number'])
        self.assertEqual('甲', unit['audios'][0]['roles'][0]['character'])
        self.assertIn('音频1', markdown({'units': [unit], 'notice': '派生测试'}))
        self.assertIn('@图片1', markdown({'units': [unit], 'notice': '派生测试', 'dialect': 'seedance-2.0'}))
        self.assertIn('| 图1 |', markdown({'units': [unit], 'notice': '派生测试', 'dialect': 'wan-3.0'}))


if __name__ == '__main__':
    unittest.main()
