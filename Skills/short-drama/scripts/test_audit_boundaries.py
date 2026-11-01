"""Offline regressions for the 2026-10-31 skill audit; no provider calls."""
import importlib.util
import json
import unittest
from pathlib import Path
from unittest.mock import patch

import creator_markdown_check as c
from reference_map import build_map
import test_contract_regressions as fixtures
from test_group_review_and_maps import docs, review, group, shot
from video_contract import resolve_profile


def settings(**choices):
    return {'format': {'prompt_language': 'zh-CN', 'target_seconds_per_episode': 10, 'aspect_ratio': '16:9'},
            'creator_authority': {'production_profile': {'status': 'accepted', 'choices': {
                'target_video_model': 'seedance-2.5', **choices}}}}


class AuditBoundaryTests(unittest.TestCase):
    def check_project(self, documents, cfg):
        with patch.object(Path, 'is_file', return_value=True), patch.object(Path, 'read_text', return_value=json.dumps(cfg)):
            return c.validate_documents(documents, Path('isolated-contract-test'))

    def test_groups_only_zero_group_fails_full_check_but_mixed_is_valid(self):
        documents = fixtures.ContractRegressionTests().later_entry_documents()
        self.assertEqual([], self.check_project(documents, settings(delivery_route='mixed')))
        self.assertTrue(any('未覆盖MOTION' in e for e in self.check_project(documents, settings(delivery_route='groups_only'))))

    def test_video_cannot_split_explicit_storyboard_group(self):
        documents = docs(review(1) + review(2).replace('所属GROUP：GROUP-EP001-01', '所属GROUP：GROUP-EP001-02')
                         + group((1,)) + group((2,)).replace('GROUP-EP001-01', 'GROUP-EP001-02'))
        self.assertTrue(any('分镜生成组计划不一致' in e for e in c.validate_documents(documents, None, partial=True)))
        with self.assertRaisesRegex(ValueError, '分镜生成组计划不一致'):
            build_map(documents['分镜.md'], documents['视频提示词.md'])

    def test_old_unplanned_storyboard_still_accepts_video_group(self):
        documents = docs()
        documents['分镜.md'] = '\n'.join(line for line in documents['分镜.md'].splitlines() if not line.startswith('- 生成组：'))
        self.assertEqual([], c.validate_documents(documents, None, partial=True))
        self.assertEqual(1, len(build_map(documents['分镜.md'], documents['视频提示词.md'])['units']))

    def test_source_windows_are_checked_even_when_video_groups_exist(self):
        documents = docs()
        documents['分镜.md'] = documents['分镜.md'].replace('组内2—4s', '组内3—5s')
        self.assertTrue(any('累计秒段' in e for e in c.validate_documents(documents, None, partial=True)))
        with self.assertRaisesRegex(ValueError, '累计秒段'):
            build_map(documents['分镜.md'], documents['视频提示词.md'])

    def test_first_frame_mode_lower_picture_limit_applies(self):
        refs = '；'.join(f'PLAN-{n}（顺序：{i}）· IMG-{n}《人物参考》（用途：身份；控制：面貌；不得控制：构图）'
                        for i, n in enumerate(('A','B'),1))
        errors = []
        with patch.object(Path, 'read_text', return_value=json.dumps(settings(target_video_model='wan-3.0',generation_mode='first_frame'))):
            c._check_model_service_preset(Path('test'), storyboard='', motions={'MOTION-001':'- 时长：10s\n- 输入参考图：'+refs}, groups={}, errors=errors)
        self.assertTrue(any('首帧模式只能' in e for e in errors))

    def test_keyframe_language_does_not_follow_video_language(self):
        documents = fixtures.ContractRegressionTests().later_entry_documents()
        cfg = settings(video_prompt_language='zh-CN')
        cfg['format']['prompt_language'] = 'en'
        self.assertTrue(any('缺少画面代称' in e for e in self.check_project(documents, cfg)))
        self.assertEqual([], self.check_project(documents, settings(video_prompt_language='en')))

    def test_explicit_same_name_designator_counts_as_declared(self):
        documents = fixtures.ContractRegressionTests().later_entry_documents()
        documents['视觉设定.md'] = documents['视觉设定.md'].replace('## 人物 · 阿甲\n', '## 人物 · 阿甲\n- 画面代称：阿甲\n')
        cfg = settings()
        cfg['format']['prompt_language'] = 'en'
        self.assertEqual([], self.check_project(documents,cfg))

    def test_missing_negation_in_declared_source_utterance_fails(self):
        documents = fixtures.ContractRegressionTests().later_entry_documents()
        documents['剧本.md'] += '\n阿甲：不能继续。\n'
        documents['分镜.md'] = documents['分镜.md'].replace('### 冻结关键帧提示词', '- 声音：阿甲说：“不能继续。”\n### 冻结关键帧提示词')
        documents['视频提示词.md'] = documents['视频提示词.md'].replace('现场风声，无对白。', '现场风声，阿甲说：“继续。”')
        self.assertTrue(any('来源声音引文' in e for e in c.validate_documents(documents,None)))
        documents['视频提示词.md'] = documents['视频提示词.md'].replace('说：“继续。”','说：“不能继续。”')
        self.assertEqual([], c.validate_documents(documents,None))

    def test_lossless_ordered_speech_segmentation_is_compatible(self):
        documents = fixtures.ContractRegressionTests().later_entry_documents()
        documents['剧本.md'] += '\n阿甲：不能继续。\n'
        documents['分镜.md'] = documents['分镜.md'].replace('### 冻结关键帧提示词','- 声音：阿甲说：“不能继续。”\n### 冻结关键帧提示词')
        documents['视频提示词.md'] = documents['视频提示词.md'].replace('现场风声，无对白。','现场风声，阿甲说：“不能”随后接着说：“继续。”')
        self.assertEqual([],c.validate_documents(documents,None))

    def test_two_source_events_need_two_occurrences_in_group(self):
        documents = docs()
        documents['剧本.md'] += '\n甲停顿。\n\n甲：你先接稳。\n'
        self.assertTrue(any('逐字出现2次' in e for e in c.validate_documents(documents,None,partial=True)))
        documents['视频提示词.md'] = documents['视频提示词.md'].replace('镜头2对方承稳才松手。', '镜头2对方承稳才松手。甲说：“你先接稳。”')
        self.assertEqual([], c.validate_documents(documents,None,partial=True))

    def test_one_source_event_bridging_two_shots_is_not_duplicated(self):
        self.assertEqual([],c.validate_documents(docs(),None,partial=True))

    def test_distinct_numeric_dialogue_does_not_create_duplicate_event(self):
        documents = docs()
        for name in ('剧本.md','分镜.md','视频提示词.md'):
            documents[name] = documents[name].replace('你先接稳。','口令100。')
        documents['剧本.md'] += '\n甲：口令200。\n'
        self.assertEqual([],c.validate_documents(documents,None,partial=True))

    def test_post_caption_is_not_required_as_generated_speech(self):
        documents = docs()
        for name in ('分镜.md','视频提示词.md'):
            documents[name] = documents[name].replace('；末尾留反应。','；末尾留反应；后期显示“下一天”。')
        self.assertEqual([],c.validate_documents(documents,None,partial=True))

    def test_explicit_post_voice_bridge_does_not_require_regeneration(self):
        self.assertEqual([],c._review_sound_literals('后期声音桥：沿用前组甲说：“不能继续。”'))
        self.assertEqual(['不能继续。'],c._review_sound_literals('甲低声说道“不能继续。”'))

    def test_seedance_frame_modes_are_only_explicitly_enabled(self):
        for preset in (None,'seedance-2.5-advanced'):
            base={'target_video_model':'seedance-2.5','video_prompt_dialect':'seedance-2.5'}
            if preset:base['video_service_preset']=preset
            self.assertNotIn('first_frame',resolve_profile(base)['modes'])
            enabled=resolve_profile({**base,'supported_generation_modes':['text','reference','first_frame','first_last_frame']})
            self.assertIn('first_frame',enabled['modes'])
            self.assertIn('first_last_frame',enabled['modes'])

    def test_explicit_25_frame_capability_passes_production_contract(self):
        path=Path(__file__).resolve().parents[2]/'short-drama-produce/scripts/video_contract_bridge.py'
        spec=importlib.util.spec_from_file_location('audit_video_bridge',path)
        bridge=importlib.util.module_from_spec(spec);spec.loader.exec_module(bridge)
        source='- 时长：10s\n- 任务类型：reference\n- 输入参考图：REF-A（顺序：1）· image/a.png《开场》（用途：起始帧；控制：开场；不得控制：终点）\n'
        job={'modality':'video','parameters':{'duration':10,'ratio':'16:9','omni_reference_task_type':'reference'},
             'reference_bindings':[{'role':'first_frame','path':'image/a.png'}]}
        with patch.object(bridge,'project',return_value=settings()):
            with self.assertRaisesRegex(ValueError,'模式超出'):
                bridge.validate_job(Path('test'),job,section=source)
        with patch.object(bridge,'project',return_value=settings(supported_generation_modes=['text','reference','first_frame'])):
            self.assertEqual(10,bridge.validate_job(Path('test'),job,section=source)['duration'])


if __name__=='__main__':unittest.main()
