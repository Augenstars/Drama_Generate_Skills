"""Offline production-contract tests; no provider and no media generation."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import production_tool as prod
from provider_adapters import compile_seedance_payload
from video_contract_bridge import validate_adapter, validate_job


class ProductionContractTests(unittest.TestCase):
    def setUp(self):
        parent = Path(os.environ.get("SHORT_DRAMA_TEST_TMP", tempfile.gettempdir())).resolve()
        self.temp = tempfile.TemporaryDirectory(prefix="contract-", dir=parent)
        self.base = Path(self.temp.name).resolve()
        assert self.base.is_relative_to(parent)
        self.root = self.base / "project"
        self.root.mkdir()
        self.cfg = {"format": {"aspect_ratio": "4:3"}, "creator_authority": {
            "production_profile": {"status": "accepted", "choices": {"target_video_model": "wan-3.0"}}}}
        self.write_cfg()
        self.source = "剧集/EP001/视频提示词.md"
        p = self.root / self.source
        p.parent.mkdir(parents=True)
        p.write_text("## MOTION-EP001-001 · 门前\n- 时长：4s\n- 输入参考图：无（创作者已明确选择文生视频）\n### 可复制提示词\n> 无人走廊，保持自然光。\n", encoding="utf-8")
        self.raw = {"job_id": "contract-test", "modality": "video", "adapter": "test",
            "source": self.source, "source_entry": "MOTION-EP001-001",
            "prompt": "无人走廊，保持自然光。", "reference_bindings": [],
            "outputs": ["剧集/EP001/制作成果/test.mp4"], "parameters": {"duration": 4, "ratio": "4:3"}}

    def tearDown(self):
        self.temp.cleanup()

    def write_cfg(self):
        (self.root / "short-drama.json").write_text(json.dumps(self.cfg), encoding="utf-8")

    def test_matching_source_and_parameters_are_accepted(self):
        job = prod._normalize_job(self.root, self.raw)
        self.assertEqual(4, job["parameters"]["duration"])
        self.assertEqual("wan-3.0", prod._preview(job)["parameters"]["target_video_model"])

    def test_group_review_member_cannot_be_submitted_even_as_one_member_group(self):
        p = self.root / self.source
        p.write_text("## MOTION-EP001-001 · 成员\n- 审查模式：GROUP成员\n"
                     "- 所属GROUP：GROUP-EP001-01\n"
                     "## GROUP-EP001-01 · 单成员组\n- 成员：MOTION-EP001-001\n",
                     encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "仅为GROUP成员审查"):
            prod._validate_video_contract(self.root, self.raw)

    def test_source_4_cannot_be_submitted_as_7(self):
        raw = {**self.raw, "parameters": {"duration": 7, "ratio": "4:3"}}
        with self.assertRaisesRegex(ValueError, "来源MOTION"):
            prod._normalize_job(self.root, raw)

    def test_member_cannot_replace_a_multi_shot_group(self):
        path = self.root / self.source
        path.write_text(path.read_text(encoding="utf-8") + "\n## GROUP-EP001-01 · 组\n- 成员：MOTION-EP001-001、MOTION-EP001-002\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "不能以成员"):
            prod._normalize_job(self.root, self.raw)

    def test_automatic_duration_does_not_bypass_fixed_source(self):
        raw = {**self.raw, "parameters": {"duration": -1, "ratio": "4:3"}}
        with self.assertRaises(ValueError):
            prod._normalize_job(self.root, raw)

    def test_ratio_cannot_drift(self):
        raw = {**self.raw, "parameters": {"duration": 4, "ratio": "16:9"}}
        with self.assertRaisesRegex(ValueError, "ratio"):
            prod._normalize_job(self.root, raw)

    def test_project_configuration_is_a_confirmed_input(self):
        job = prod._normalize_job(self.root, self.raw)
        self.assertIn("short-drama.json", job["inputs"])
        self.assertTrue(prod._inputs_current(self.root, job))
        self.cfg["format"]["aspect_ratio"] = "16:9"
        self.write_cfg()
        self.assertFalse(prod._inputs_current(self.root, job))

    def test_low_cost_cannot_use_a_4_second_independent_unit(self):
        self.cfg["creator_authority"]["production_profile"]["choices"] = {
            "target_video_model": "seedance-2.0", "video_prompt_dialect": "seedance-2.0",
            "video_service_preset": "seedance-2.0-low-cost", "output_resolution": "720p"}
        self.write_cfg()
        raw = {**self.raw, "parameters": {"duration": 4, "ratio": "4:3", "resolution": "720p"}}
        with self.assertRaisesRegex(ValueError, "5/10/15"):
            prod._normalize_job(self.root, raw)

    def test_official_compiler_does_not_impersonate_low_cost_service(self):
        raw = {"modality": "video", "prompt": "走廊", "references": [], "outputs": ["a.mp4"],
               "parameters": {"duration": 10, "ratio": "4:3", "video_service_preset": "seedance-2.0-low-cost"}}
        with self.assertRaisesRegex(ValueError, "未接入"):
            compile_seedance_payload(raw, model="configured", allowed_ratios={"4:3"}, duration_range=(5, 15))

    def test_wan_job_cannot_be_sent_to_seedance_compiler(self):
        raw = {"modality": "video", "prompt": "走廊", "references": [], "outputs": ["a.mp4"],
               "parameters": {"duration": 10, "ratio": "4:3", "target_video_model": "wan-3.0"}}
        with self.assertRaisesRegex(ValueError, "编译器不匹配"):
            compile_seedance_payload(raw, model="configured", allowed_ratios={"4:3"}, duration_range=(2, 30))

    def test_unmatched_adapter_is_rejected(self):
        path = self.base / "adapters.json"
        path.write_text(json.dumps({"adapters": {"test": {"command": ["unused"]}}}), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "video_model_profile"):
            validate_adapter(self.root, self.raw, path)

    def test_matching_adapter_declaration_is_accepted(self):
        path = self.base / "adapters.json"
        path.write_text(json.dumps({"adapters": {"test": {"video_model_profile": {"target_video_model": "wan-3.0"}}}}), encoding="utf-8")
        validate_adapter(self.root, self.raw, path)

    def prepare_confirm_and_adapter(self):
        job_path = self.root / "test-job.json"
        job_path.write_text(json.dumps(self.raw), encoding="utf-8")
        preview = prod.prepare_job(self.root, job_path)
        prod.confirm_job(self.root, job_id=self.raw["job_id"], confirmation=preview["confirmation"])
        config = self.base / "adapters.json"
        config.write_text(json.dumps({"adapters": {"test": {"command": ["unused-offline-test"]}}}), encoding="utf-8")
        return config

    def test_adapter_rejection_does_not_launch_or_consume_confirmation(self):
        config = self.prepare_confirm_and_adapter()
        with patch.object(tempfile, "tempdir", str(self.base)), patch.object(prod, "_run_adapter") as runner:
            with self.assertRaisesRegex(ValueError, "video_model_profile"):
                prod.run_job(self.root, job_id=self.raw["job_id"], adapter_config=config)
            runner.assert_not_called()
        receipt = prod._metadata_read_json(self.root, ("confirmations",),
            prod._job_key(self.raw["job_id"]) + ".json", maximum=prod.MAX_RUN_RECORD_BYTES)
        self.assertIsNone(receipt["consumed_at"])

    def test_changed_project_cannot_launch_a_previously_confirmed_video(self):
        config = self.prepare_confirm_and_adapter()
        self.cfg["format"]["aspect_ratio"] = "16:9"
        self.write_cfg()
        with patch.object(tempfile, "tempdir", str(self.base)), patch.object(prod, "_run_adapter") as runner:
            with self.assertRaises(prod.ConfirmationRequiredError):
                prod.run_job(self.root, job_id=self.raw["job_id"], adapter_config=config)
            runner.assert_not_called()

    def test_declared_reference_mode_cannot_become_first_frame(self):
        self.cfg["creator_authority"]["production_profile"]["choices"]["generation_mode"] = "reference"
        self.write_cfg()
        raw = {**self.raw, "reference_bindings": [{"role": "first_frame"}]}
        with self.assertRaisesRegex(ValueError, "参考模式"):
            validate_job(self.root, raw, section="- 时长：4s\n- 输入参考图：用途：起始帧\n")

    def test_video_reference_limits_are_enforced(self):
        raw = {**self.raw, "reference_bindings": [{"role": "reference_image"}] * 11}
        with self.assertRaisesRegex(ValueError, "上限 9 张"):
            validate_job(self.root, raw, section="- 时长：4s\n")

    def test_source_task_type_cannot_drift(self):
        with self.assertRaisesRegex(ValueError, "任务类型"):
            validate_job(self.root, self.raw, section="- 时长：4s\n- 任务类型：extend\n")

    def test_shot_start_frame_job_survives_storage_validation(self):
        source = "剧集/EP001/分镜.md"
        (self.root / source).write_text("## SHOT-EP001-001 · 门前\n- 输入参考图：无\n### 冻结关键帧提示词\n> 门前空景。\n", encoding="utf-8")
        raw = {"job_id": "frame", "modality": "image", "adapter": "test", "source": source,
            "source_entry": "SHOT-EP001-001", "prompt": "门前空景。", "reference_bindings": [],
            "outputs": ["剧集/EP001/制作成果/test.png"], "parameters": {}}
        job = prod._normalize_job(self.root, raw)
        self.assertEqual("SHOT-EP001-001", prod._validate_stored_job(self.root, job)["source_entry"])


if __name__ == "__main__":
    unittest.main()
