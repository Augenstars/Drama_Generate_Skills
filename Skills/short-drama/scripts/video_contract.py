"""Deterministic video constraints shared by drafting checks and production.

Service meanings: ../references/model-service-presets.md. No provider calls.
Only actual generation units are quantized; member shots are not.
"""
from __future__ import annotations

import math
import re
from collections.abc import Mapping


MAX_REFERENCE_IMAGES = 9


def image_limit(profile: Mapping) -> int:
    """Creator-wide ceiling; unknown models do not opt out of the policy."""
    native = profile.get("images")
    return min(MAX_REFERENCE_IMAGES, native) if native is not None else MAX_REFERENCE_IMAGES


# Retain native ceilings to validate historic declarations without rewriting
# project files. Exported profiles and every reference check use the lower
# creator-wide policy, never these native numbers as an execution allowance.
NATIVE_PRESETS = {
    "seedance-2.0-low-cost": {
        "model": "seedance-2.0", "range": (5, 15), "integer": True,
        "allowed_seconds": (5, 10, 15), "images": 10,
        "resolution": "720p", "ratios": ("16:9", "9:16", "4:3", "3:4", "1:1", "21:9"),
        "modes": ("reference",),
    },
    "seedance-2.0-mini": {"model": "seedance-2.0", "range": None, "integer": None,
        "images": 9, "videos": 3, "audios": 3,
        "modes": ("text", "first_frame", "first_last_frame", "reference")},
    "seedance-2.0-standard": {"model": "seedance-2.0", "range": None, "integer": None,
        "images": 9, "videos": 3, "audios": 3,
        "modes": ("text", "first_frame", "first_last_frame", "reference")},
    "seedance-2.5-advanced": {"model": "seedance-2.5", "range": (4, 30), "integer": True,
        "modes": ("text", "reference", "edit", "extend"),
        "declared_mode_extensions": ("first_frame", "first_last_frame")},
    "wan-3.0": {"model": "wan-3.0", "range": (2, 30), "integer": True,
        "images": 10, "videos": 5, "audios": 5,
        "modes": ("text", "first_frame", "first_last_frame", "reference")},
}
NATIVE_BASE_MODELS = {
    "seedance-2.0": {"model": "seedance-2.0", "range": (4, 15), "integer": True, "images": 9},
    "seedance-2.5": {"model": "seedance-2.5", "range": (4, 30), "integer": True,
        "modes": ("text", "reference", "edit", "extend"),
        "declared_mode_extensions": ("first_frame", "first_last_frame")},
    "wan-3.0": NATIVE_PRESETS["wan-3.0"],
    "minimax-h3": {"model": "minimax-h3", "range": (4, 15), "integer": True},
}
PRESETS = {name: {**value, "images": image_limit(value)} for name, value in NATIVE_PRESETS.items()}
BASE_MODELS = {name: {**value, "images": image_limit(value)} for name, value in NATIVE_BASE_MODELS.items()}
MODES = {"text", "first_frame", "first_last_frame", "reference", "edit", "extend"}


def parse_seconds(value: object) -> float | None:
    """A complete, finite, positive scalar, never the first number in prose."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        try:
            result = float(value)
        except (OverflowError, ValueError):
            return None
    elif isinstance(value, str):
        match = re.fullmatch(r"\s*(\d+(?:\.\d+)?|\.\d+)\s*(?:s|秒)?\s*", value, re.I)
        if not match:
            return None
        result = float(match.group(1))
    else:
        return None
    return result if math.isfinite(result) and result > 0 else None


def accepted_choices(project: Mapping) -> dict:
    authority = project.get("creator_authority", {})
    profile = authority.get("production_profile", {}) if isinstance(authority, Mapping) else {}
    if not isinstance(profile, Mapping) or profile.get("status") != "accepted":
        return {}
    value = profile.get("choices", {})
    if not isinstance(value, Mapping):
        raise ValueError("已接受生产档案的choices必须是对象")
    return dict(value)


def resolve_profile(choices: Mapping) -> dict:
    preset = choices.get("video_service_preset")
    model = choices.get("target_video_model")
    if model is not None and (not isinstance(model, str) or not model.strip()):
        raise ValueError("target_video_model 必须是非空字符串或null")
    if preset is not None:
        if not isinstance(preset, str) or preset not in PRESETS:
            raise ValueError("未知 video_service_preset")
        result = dict(NATIVE_PRESETS[preset])
        for key in ("target_video_model", "video_prompt_dialect"):
            if choices.get(key) != result["model"]:
                raise ValueError(f"{preset} 的 {key} 应为 {result['model']}")
    else:
        result = dict(NATIVE_BASE_MODELS.get(model, {"model": model}))
    result["preset"] = preset
    native = choices.get("native_duration_seconds")
    if native is not None:
        if not isinstance(native, Mapping):
            raise ValueError("native_duration_seconds 必须是区间对象或null")
        minimum, maximum = parse_seconds(native.get("min")), parse_seconds(native.get("max"))
        if minimum is None or maximum is None or minimum > maximum:
            raise ValueError("native_duration_seconds 必须为合法正数区间")
        base = result.get("range")
        if base and (minimum < base[0] or maximum > base[1]):
            raise ValueError("原生时长区间超出所选模型/服务已声明范围")
        result["range"] = (minimum, maximum)
    integer = choices.get("duration_integer_seconds")
    if integer is not None:
        if not isinstance(integer, bool):
            raise ValueError("duration_integer_seconds 必须为布尔值或null")
        if result.get("integer") is True and not integer:
            raise ValueError("所选服务要求整数秒，不能关闭整数限制")
        result["integer"] = integer
    limits = choices.get("reference_limits")
    if limits is not None and not isinstance(limits, Mapping):
        raise ValueError("reference_limits 必须为对象或null")
    for kind in ("images", "videos", "audios"):
        declared = limits.get(kind) if isinstance(limits, Mapping) else None
        if declared is not None:
            if not isinstance(declared, int) or isinstance(declared, bool) or declared < 0:
                raise ValueError(f"reference_limits.{kind} 必须为非负整数")
            cap = result.get(kind)
            if cap is not None and declared > cap:
                raise ValueError(f"reference_limits.{kind} 超出已声明服务上限")
            result[kind] = declared
    selected_modes = choices.get("supported_generation_modes")
    if selected_modes is not None:
        if not isinstance(selected_modes, list) or not selected_modes or any(not isinstance(m, str) or m not in MODES for m in selected_modes):
            raise ValueError("supported_generation_modes 含未知模式或为空")
        known = result.get("modes")
        # Frame-position capabilities vary by 2.5 entry point. They are opt-in
        # only through an accepted, explicitly verified capability declaration;
        # choosing the model or requesting a tail image does not enable them.
        allowed = set(known or ()) | set(result.get("declared_mode_extensions", ()))
        if (preset or result.get("declared_mode_extensions")) and known and not set(selected_modes) <= allowed:
            raise ValueError("所声明生成模式超出所选服务已知能力")
        result["modes"] = tuple(selected_modes)
    mode = choices.get("generation_mode")
    if mode is not None and (not isinstance(mode, str) or mode not in MODES):
        raise ValueError("未知 generation_mode")
    if mode is not None and result.get("modes") and mode not in result["modes"]:
        raise ValueError("所选生成模式超出已确认服务能力")
    resolution = choices.get("output_resolution")
    if result.get("resolution") and resolution is not None and str(resolution).lower() != result["resolution"]:
        raise ValueError("output_resolution与服务固定分辨率不一致")
    ratios = choices.get("supported_aspect_ratios")
    if ratios is not None:
        if not isinstance(ratios, list) or not ratios or any(not isinstance(r, str) or not r for r in ratios):
            raise ValueError("supported_aspect_ratios 必须为非空画幅列表或null")
        if result.get("ratios") and not set(ratios) <= set(result["ratios"]):
            raise ValueError("画幅列表超出服务已声明范围")
        result["ratios"] = tuple(ratios)
    route = choices.get("delivery_route", "mixed")
    if route not in ("mixed", "groups_only"):
        raise ValueError("delivery_route 只能为mixed或groups_only")
    result["delivery_route"] = route
    result["images"] = image_limit(result)
    return result


def unit_errors(value: object, profile: Mapping, *, require_known: bool = False) -> list[str]:
    duration = parse_seconds(value)
    if duration is None:
        return ["时长必须是完整、有限且大于0的秒数"]
    errors = []
    allowed = profile.get("allowed_seconds")
    if allowed and duration not in allowed:
        errors.append("2.0低价模型每个GROUP只能为5/10/15秒")
    bounds = profile.get("range")
    if bounds and not bounds[0] <= duration <= bounds[1]:
        errors.append(f"生成时长不在原生范围 {bounds[0]:g}～{bounds[1]:g} 秒内")
    if profile.get("integer") is True and not duration.is_integer():
        errors.append("实际生成单位必须使用整数秒，组内SHOT可使用小数")
    if require_known and (bounds is None or profile.get("integer") is None):
        errors.append("原生时长范围或精度未确认，仅可准备内容草稿，不能提交")
    return errors


def resolve_mode(explicit: object, purposes: list[str], *, video_count: int = 0, audio_count: int = 0) -> str:
    if explicit is not None:
        if not isinstance(explicit, str) or explicit not in MODES:
            raise ValueError("未知 generation_mode")
        return str(explicit)
    if video_count or audio_count:
        return "reference"
    if purposes == ["起始帧"]:
        return "first_frame"
    if len(purposes) == 2 and set(purposes) == {"起始帧", "结束帧"}:
        return "first_last_frame"
    return "reference" if purposes else "text"


def reference_errors(counts: Mapping, profile: Mapping, mode: str) -> list[str]:
    errors = []
    if mode == "first_frame" and (counts.get("images") != 1 or counts.get("videos") or counts.get("audios")):
        errors.append("首帧模式只能使用一张起始图")
    elif mode == "first_last_frame" and (counts.get("images") != 2 or counts.get("videos") or counts.get("audios")):
        errors.append("首尾帧模式只能使用两张图片")
    elif mode == "text" and any(counts.values()):
        errors.append("文生模式不能带参考输入")
    for kind, noun in (("images", "图片"), ("videos", "视频"), ("audios", "音频")):
        cap = image_limit(profile) if kind == "images" else profile.get(kind)
        if cap is not None and counts.get(kind, 0) > cap:
            errors.append(f"整组参考{noun} {counts[kind]} {'张' if kind == 'images' else '段'}，超过上限 {cap} {'张' if kind == 'images' else '段'}")
    return errors
