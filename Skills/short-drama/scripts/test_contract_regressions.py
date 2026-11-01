"""Regression cases from SK-A02, A03, A07 and A10; no media or provider calls."""
import json
import unittest
from pathlib import Path
from unittest.mock import patch

import creator_markdown_check as c
from video_contract import parse_seconds, resolve_profile, unit_errors, resolve_mode


class ContractRegressionTests(unittest.TestCase):
    def test_invalid_duration_is_not_a_positive_number(self):
        for value in ("-4s", "0s", "约4秒", "4s extra", "4-5s", "nan", float("inf"), True, None):
            with self.subTest(value=value):
                self.assertIsNone(parse_seconds(value))
                self.assertIsNone(c._declared_seconds(value))

    def test_valid_internal_fractional_duration(self):
        for value in (".5s", "0.5 秒", "4s", 4.0):
            self.assertIsNotNone(parse_seconds(value))

    def test_extreme_numbers_and_malformed_profiles_fail_cleanly(self):
        self.assertIsNone(parse_seconds(10 ** 1000))
        for value in ({"target_video_model": []}, {"video_service_preset": False},
                      {"supported_generation_modes": [{}]}, {"generation_mode": {}}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                resolve_profile(value)

    def test_wan_rejects_out_of_range_and_non_integer_units(self):
        profile = resolve_profile({"target_video_model": "wan-3.0"})
        for value in (1, 31, 7.5):
            self.assertTrue(unit_errors(value, profile))
        for value in (2, 7, 24, 30):
            self.assertEqual([], unit_errors(value, profile))

    def test_no_preset_is_needed_to_validate_known_model(self):
        profile = resolve_profile({"target_video_model": "seedance-2.5"})
        self.assertTrue(unit_errors(31, profile))

    def test_known_model_total_is_checked_without_service_preset(self):
        cfg = {"format": {"target_seconds_per_episode": 92}, "creator_authority": {
            "production_profile": {"status": "accepted", "choices": {"target_video_model": "wan-3.0"}}}}
        errors = []
        with patch.object(Path, "read_text", return_value=json.dumps(cfg)):
            c._check_model_service_preset(Path("test"), storyboard="", motions={"MOTION-001": "- 时长：7s\n"}, groups={}, errors=errors)
        self.assertTrue(any("不等于项目目标集长" in e for e in errors))

    def test_broken_project_json_does_not_disable_checks_silently(self):
        errors = []
        with patch.object(Path, "read_text", return_value="{broken"):
            c._check_model_service_preset(Path("test"), storyboard="", motions={}, groups={}, errors=errors)
        self.assertTrue(any("解析" in e for e in errors))

    def test_invalid_accepted_choices_are_reported(self):
        errors = []
        cfg = {"creator_authority": {"production_profile": {"status": "accepted", "choices": []}}}
        with patch.object(Path, "read_text", return_value=json.dumps(cfg)):
            c._check_model_service_preset(Path("test"), storyboard="", motions={}, groups={}, errors=errors)
        self.assertTrue(any("choices" in e for e in errors))

    def test_mini_unknown_capability_allows_draft_not_submission(self):
        profile = resolve_profile({"target_video_model": "seedance-2.0",
            "video_prompt_dialect": "seedance-2.0", "video_service_preset": "seedance-2.0-mini"})
        self.assertEqual([], unit_errors(7, profile))
        self.assertTrue(unit_errors(7, profile, require_known=True))

    def test_low_cost_rule_only_applies_to_actual_unit(self):
        profile = resolve_profile({"target_video_model": "seedance-2.0",
            "video_prompt_dialect": "seedance-2.0", "video_service_preset": "seedance-2.0-low-cost"})
        self.assertEqual([], unit_errors(10, profile))
        self.assertTrue(unit_errors(7, profile))
        self.assertEqual(4, parse_seconds("4s"))

    def test_profile_cannot_expand_known_hard_caps(self):
        with self.assertRaises(ValueError):
            resolve_profile({"target_video_model": "wan-3.0", "reference_limits": {"images": 11}})
        with self.assertRaises(ValueError):
            resolve_profile({"target_video_model": "wan-3.0", "native_duration_seconds": {"min": 1, "max": 40}})

    def test_explicit_mode_has_priority(self):
        self.assertEqual("reference", resolve_mode("reference", ["起始帧"]))
        self.assertEqual("first_frame", resolve_mode(None, ["起始帧"]))
        self.assertEqual("first_last_frame", resolve_mode(None, ["起始帧", "结束帧"]))

    def test_later_entry_does_not_leak_into_opening_lock(self):
        errors = []
        c._check_continuity_locks(
            [c.ContinuityLock("LOCK-CAPE", "红色披风", ["入画"], [], ("造型", "甲的披风"))],
            shots={"SHOT-001": "## SHOT-001 · 门外\n### 冻结关键帧提示词\n> 无人的走廊。\n"},
            motion_by_shot={"SHOT-001": ("MOTION-001", "", "2秒后穿红色披风的甲进入。")},
            image_prompts=None, in_frame={"SHOT-001": {("造型", "甲的披风")}},
            opening_in_frame={"SHOT-001": set()}, errors=errors,
        )
        self.assertEqual([], errors)

    def test_visible_opening_still_requires_its_lock(self):
        errors = []
        entry = ("造型", "甲的披风")
        c._check_continuity_locks(
            [c.ContinuityLock("LOCK-CAPE", "红色披风", ["入画"], [], entry)],
            shots={"SHOT-001": "## SHOT-001 · 甲\n### 冻结关键帧提示词\n> 甲站着。\n"},
            motion_by_shot={}, image_prompts=None,
            in_frame={"SHOT-001": {entry}}, opening_in_frame={"SHOT-001": {entry}}, errors=errors,
        )
        self.assertTrue(any("缺少锁面" in e for e in errors))

    def later_entry_documents(self):
        texts = {
            "剧本.md": "# EP001 门\n## EP001-SC001 外 · 走廊 · 日\n走廊无人。两秒后阿甲推门进入。\n",
            "视觉设定.md": "## 人物 · 阿甲\n- 识别锚点：短发。\n## 造型 · 阿甲披风\n- 连续性锁：LOCK-CAPE《红披风》（镜头：入画）· 锁面：红色披风\n## 地点 · 走廊\n- 识别锚点：木门。\n",
            "图片提示词.md": "# 图片提示词\n本集明确文生，无新增图片。\n",
            "分镜.md": """## SHOT-EP001-001 · 推门
- 来源：EP001-SC001
- 时长：10s
- 目的：先见无人，再见进入。
- 景别/机位：中景，平视。
- 运镜：固定；让门和进入动作可读。
- 起点：走廊无人，门关闭。
- 唯一动作：2秒后阿甲穿红色披风推门进入。
- 终点：阿甲站在门口。
- 视觉依据：《视觉设定.md》·地点「走廊」（控制：地理）；人物「阿甲」（控制：身份）；造型「阿甲披风」（控制：2秒后入画的衣装）
- 开场视觉依据：《视觉设定.md》·地点「走廊」（控制：开场地理）
- 图片提示词项：无
- 输入参考图：无（创作者已明确选择文生视频）
### 冻结关键帧提示词
> 走廊无人，门关闭。
""",
            "视频提示词.md": """## MOTION-EP001-001 · 推门
- 分镜：SHOT-EP001-001
- 时长：10s
- 生成方式：文生视频
- 输入参考图：无（创作者已明确选择文生视频）
- 静态视觉锚点：走廊无人，门关闭。
- 起始帧：走廊无人，门关闭。
- 状态链：2秒后阿甲穿红色披风推门进入。
- 终点：阿甲站在门口。
### 可复制提示词
> 走廊无人，门关闭。2秒后阿甲穿红色披风推门进入，停在门口。机位固定，现场风声，无对白。
""",
        }
        return texts

    def test_full_document_contract_accepts_later_entry(self):
        self.assertEqual([], c.validate_documents(self.later_entry_documents(), None))

    def test_negative_duration_is_rejected_by_full_document_check(self):
        texts = self.later_entry_documents()
        for name in ("分镜.md", "视频提示词.md"):
            texts[name] = texts[name].replace("- 时长：10s", "- 时长：-10s")
        self.assertTrue(any("时长" in e for e in c.validate_documents(texts, None)))

    def test_mixed_grouping_counts_loose_shot_once(self):
        cfg = {"format": {"target_seconds_per_episode": 10}, "creator_authority": {
            "production_profile": {"status": "accepted", "choices": {"target_video_model": "seedance-2.5"}}}}
        errors = []
        with patch.object(Path, "read_text", return_value=json.dumps(cfg)):
            c._check_model_service_preset(Path("test"), storyboard="", motions={
                "MOTION-001": "- 时长：5s\n", "MOTION-002": "- 时长：5s\n"},
                groups={"GROUP-01": "- 成员：MOTION-001\n- 时长：5s\n"}, errors=errors)
        self.assertEqual([], errors)


if __name__ == "__main__":
    unittest.main()
