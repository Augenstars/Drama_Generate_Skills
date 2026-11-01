"""Offline regression tests for explicitly selected model service presets."""

import json
import unittest
from pathlib import Path
from unittest.mock import patch

from creator_markdown_check import _check_model_service_preset
from project_tool import project_video_model_profile


LOW = "seedance-2.0-low-cost"


def motion(seconds, refs=""):
    return f"- 时长：{seconds}s\n- 输入参考图：{refs}\n"


def group(seconds, *members):
    return f"- 时长：{seconds}s\n- 成员：{'、'.join(members)}\n"


def picture(n, path=None):
    return (
        f"REF-IMG-{n}（顺序：{n}）· {path or f'image/{n}.png'}《图片{n}》"
        "（用途：身份；控制：人物面貌；不得控制：构图）"
    )


class ServicePresetTests(unittest.TestCase):
    def check(self, *, preset=LOW, target=10, motions=None, groups=None,
              storyboard="", status="accepted", **choices):
        family = {"seedance-2.5-advanced": "seedance-2.5", "wan-3.0": "wan-3.0"}.get(preset, "seedance-2.0")
        profile = {
            "status": status,
            "choices": {
                "target_video_model": family, "video_prompt_dialect": family,
                "video_service_preset": preset, "output_resolution": "720p", **choices,
            },
        }
        project = {
            "creator_authority": {"production_profile": profile},
            "format": {"target_seconds_per_episode": target, "aspect_ratio": "4:3"},
        }
        with patch.object(Path, "read_text", return_value=json.dumps(project)):
            root = Path("test-project")
            errors = []
            _check_model_service_preset(
                root, storyboard=storyboard, motions=motions or {},
                groups=groups or {}, errors=errors,
            )
        return errors

    def test_group_10_allows_shots_4_and_6(self):
        self.assertEqual([], self.check(
            motions={"MOTION-001": motion(4), "MOTION-002": motion(6)},
            groups={"GROUP-01": group(10, "MOTION-001", "MOTION-002")},
            storyboard="## SHOT-001\n- 时长：4s\n## SHOT-002\n- 时长：6s\n",
        ))

    def test_fractional_internal_cuts_are_allowed(self):
        self.assertEqual([], self.check(
            motions={"MOTION-001": motion(3.5), "MOTION-002": motion(6.5)},
            groups={"GROUP-01": group(10, "MOTION-001", "MOTION-002")},
        ))

    def test_legal_standalone_durations(self):
        for duration in (5, 10, 15):
            with self.subTest(duration=duration):
                self.assertEqual([], self.check(target=duration, motions={"MOTION-001": motion(duration)}))

    def test_illegal_group_durations_including_long_group(self):
        for duration in (4, 7, 11, 13, 16, 24):
            with self.subTest(duration=duration):
                errors = self.check(target=30, motions={"MOTION-001": motion(duration)},
                                    groups={"GROUP-01": group(duration, "MOTION-001")})
                self.assertTrue(any("只能为5/10/15秒" in error for error in errors))

    def test_standalone_is_also_a_generation_unit(self):
        self.assertTrue(any("只能为5/10/15秒" in error for error in self.check(
            target=10, motions={"MOTION-001": motion(7)},
        )))

    def test_90_second_budget_not_double_counted(self):
        durations = (15, 15, 15, 15, 15, 15)
        motions = {f"MOTION-{n}": motion(t) for n, t in enumerate(durations)}
        groups = {f"GROUP-{n}": group(t, f"MOTION-{n}") for n, t in enumerate(durations)}
        self.assertEqual([], self.check(target=90, motions=motions, groups=groups))

    def test_105_seconds_cannot_pass_for_90_second_episode(self):
        motions = {f"MOTION-{n}": motion(15) for n in range(7)}
        groups = {f"GROUP-{n}": group(15, f"MOTION-{n}") for n in range(7)}
        self.assertTrue(any("105 秒不等于项目目标集长 90" in error for error in self.check(
            target=90, motions=motions, groups=groups,
        )))

    def test_non_multiple_target_is_reported(self):
        self.assertTrue(any("不是5秒整数倍" in error for error in self.check(target=92)))

    def test_explicit_groups_only_route_needs_formal_coverage(self):
        self.assertTrue(any("未覆盖MOTION" in error for error in self.check(
            motions={"MOTION-001": motion(5), "MOTION-002": motion(5)},
            groups={"GROUP-01": group(5, "MOTION-001")}, delivery_route="groups_only",
        )))

    def test_mini_standard_and_advanced_do_not_get_discrete_rule(self):
        for preset in ("seedance-2.0-mini", "seedance-2.0-standard", "seedance-2.5-advanced"):
            with self.subTest(preset=preset):
                self.assertEqual([], self.check(
                    preset=preset, target=7, motions={"MOTION-001": motion(7)}, output_resolution=None,
                ))

    def test_no_preset_and_unaccepted_preset_leave_original_behavior(self):
        for kwargs in ({"preset": None}, {"status": "unset"}):
            self.assertEqual([], self.check(target=7, motions={"MOTION-001": motion(7)}, **kwargs))

    def test_all_service_presets_reject_10_images(self):
        refs = "；".join(picture(n) for n in range(1, 11))
        for preset in (LOW, "seedance-2.0-mini", "seedance-2.0-standard", "seedance-2.5-advanced", "wan-3.0"):
            self.assertTrue(any("上限 9 张" in error for error in self.check(
                preset=preset, motions={"MOTION-001": motion(10, refs)},
            )))

    def test_group_image_union_is_not_per_member_budget(self):
        refs1 = "；".join(picture(n) for n in range(1, 7))
        refs2 = "；".join(picture(n) for n in range(7, 12))
        self.assertTrue(any("整组参考图片 11 张" in error for error in self.check(
            motions={"MOTION-001": motion(4, refs1), "MOTION-002": motion(6, refs2)},
            groups={"GROUP-01": group(10, "MOTION-001", "MOTION-002")},
        )))

    def test_same_file_for_two_roles_only_uses_one_upload(self):
        refs = "；".join(picture(n, "image/same.png") for n in range(1, 12))
        self.assertEqual([], self.check(motions={"MOTION-001": motion(10, refs)}))

    def test_extra_actual_upload_rows_are_counted(self):
        body = group(10, "MOTION-001") + "\n".join(
            f"| {n} | 图{n} | REF | image/{n}.png |" for n in range(1, 12)
        )
        self.assertTrue(any("整组参考图片 11 张" in error for error in self.check(
            motions={"MOTION-001": motion(10)}, groups={"GROUP-01": body},
        )))

    def test_resolution_is_checked_only_for_low_cost(self):
        self.assertTrue(any("output_resolution" in error for error in self.check(output_resolution="1080p")))

    def test_wan_keeps_7_and_24_second_groups_and_non_720p_output(self):
        for duration in (7, 24):
            with self.subTest(duration=duration):
                self.assertEqual([], self.check(
                    preset="wan-3.0", target=duration,
                    motions={"MOTION-001": motion(duration)},
                    groups={"GROUP-01": group(duration, "MOTION-001")},
                    output_resolution="1080p",
                ))

    def test_wan_uses_universal_9_image_reference_budget(self):
        for count in (9, 10, 11):
            refs = "；".join(picture(n) for n in range(1, count + 1))
            errors = self.check(preset="wan-3.0", motions={"MOTION-001": motion(10, refs)})
            self.assertEqual(count > 9, any("上限 9 张" in error for error in errors))

    def test_status_exposes_the_new_service_choices(self):
        choices = {"video_service_preset": LOW, "reference_limits": {"images": 10},
                   "output_resolution": "720p", "supported_aspect_ratios": ["4:3"]}
        project = {"creator_authority": {"production_profile": {"status": "accepted", "choices": choices}}}
        self.assertEqual(choices, project_video_model_profile(project))


if __name__ == "__main__":
    unittest.main()
