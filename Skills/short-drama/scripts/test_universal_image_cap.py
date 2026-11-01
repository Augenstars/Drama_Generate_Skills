"""Universal nine-picture ceiling; no media or provider calls."""
import copy
import unittest

import creator_markdown_check as c
from reference_map import build_map
from video_contract import BASE_MODELS, PRESETS, reference_errors, resolve_profile
from test_group_review_and_maps import shot


def pictures(n, start=1):
    return '；'.join(f'PLAN-R-{i}（顺序：{order}）· IMG-R-{i}《参考图片》（用途：身份；控制：面貌；不得控制：动作）'
                    for order, i in enumerate(range(start, start+n), 1))


class UniversalImageCapTests(unittest.TestCase):
    def test_every_exported_model_and_service_has_nine_or_lower(self):
        for table in (BASE_MODELS, PRESETS):
            for name, profile in table.items():
                with self.subTest(name=name):
                    self.assertLessEqual(profile['images'], 9)

    def test_all_models_including_unknown_and_unselected_enforce_boundary(self):
        choices = [{'target_video_model': model} for model in
                   ['seedance-2.0', 'seedance-2.5', 'wan-3.0', 'minimax-h3', 'custom-video-model']]
        choices += [{}, {'target_video_model': None}]
        choices += [{'video_service_preset': name, 'target_video_model': value['model'],
                     'video_prompt_dialect': value['model']} for name, value in PRESETS.items()]
        for choice in choices:
            with self.subTest(choice=choice):
                profile = resolve_profile(choice)
                self.assertEqual([], reference_errors({'images': 9}, profile, 'reference'))
                self.assertTrue(reference_errors({'images': 10}, profile, 'reference'))

    def test_empty_or_forged_profile_cannot_bypass_universal_policy(self):
        for profile in ({}, {'images': None}, {'images': 100}):
            self.assertTrue(reference_errors({'images': 10}, profile, 'reference'))

    def test_legacy_native_ten_is_clamped_without_mutating_project_choice(self):
        for choice in [{'target_video_model': 'wan-3.0', 'reference_limits': {'images': 10}},
                       {'target_video_model': 'seedance-2.0', 'video_prompt_dialect': 'seedance-2.0',
                        'video_service_preset': 'seedance-2.0-low-cost', 'reference_limits': {'images': 10}},
                       {'target_video_model': 'custom', 'reference_limits': {'images': 100}}]:
            before = copy.deepcopy(choice)
            self.assertEqual(9, resolve_profile(choice)['images'])
            self.assertEqual(before, choice)

    def test_lower_caps_and_frame_modes_remain_stricter(self):
        profile = resolve_profile({'target_video_model': 'wan-3.0', 'reference_limits': {'images': 3}})
        self.assertTrue(reference_errors({'images': 4}, profile, 'reference'))
        self.assertEqual([], reference_errors({'images': 1}, {}, 'first_frame'))
        self.assertTrue(reference_errors({'images': 2}, {}, 'first_frame'))
        self.assertEqual([], reference_errors({'images': 2}, {}, 'first_last_frame'))
        self.assertTrue(reference_errors({'images': 3}, {}, 'first_last_frame'))

    def test_audio_and_video_budgets_are_unchanged(self):
        profile = resolve_profile({'target_video_model': 'wan-3.0'})
        self.assertEqual([], reference_errors({'images': 9, 'videos': 5, 'audios': 5}, profile, 'reference'))
        self.assertTrue(reference_errors({'images': 0, 'videos': 6, 'audios': 0}, profile, 'reference'))

    def test_checker_without_project_cannot_accept_ten(self):
        errors = []
        c._check_model_service_preset(None, storyboard='', motions={'MOTION-001':
            '- 时长：5s\n- 输入参考图：'+pictures(10)+'\n'}, groups={}, errors=errors)
        self.assertTrue(any('上限 9 张' in e for e in errors))

    def test_storyboard_only_group_union_is_limited_not_each_member(self):
        errors = []
        board = shot(1, refs=pictures(5)) + shot(2, refs=pictures(5, start=6))
        c._check_model_service_preset(None, storyboard=board, motions={}, groups={}, errors=errors)
        self.assertTrue(any('GROUP-EP001-01' in e and '10 张' in e for e in errors))

    def test_image_prompt_inputs_also_have_the_global_limit(self):
        for n in [9, 10]:
            refs = '；'.join(f'REF-R-{i}（顺序：{i}）· images/{i}.png《参考图片》（用途：身份；控制：面貌；不得控制：动作）' for i in range(1, n+1))
            errors = c.validate_documents({'图片提示词.md': '# 图片提示词\n## IMG-A · 人物图\n- 参考：'+refs+'\n### 可复制提示词\n> 灰衣人物。\n'}, None, partial=True)
            self.assertEqual(n > 9, any('上限 9 张' in e for e in errors))

    def test_mapping_tool_cannot_ignore_limit_for_unknown_model(self):
        self.assertEqual(9, len(build_map(shot(1, refs=pictures(9)))['units'][0]['images']))
        with self.assertRaisesRegex(ValueError, '上限 9 张'):
            build_map(shot(1, refs=pictures(10)))


if __name__ == '__main__':
    unittest.main()
