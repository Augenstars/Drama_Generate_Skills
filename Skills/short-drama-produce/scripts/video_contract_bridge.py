"""Video contracts and the universal reference-image policy; no provider calls."""
from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path
from collections.abc import Mapping

_path = Path(__file__).resolve().parents[2] / "short-drama/scripts/video_contract.py"
POLICY = None
if _path.is_file():
    _spec = importlib.util.spec_from_file_location("short_drama_shared_video_contract", _path)
    if _spec is not None and _spec.loader is not None:
        POLICY = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(POLICY)


def policy():
    if POLICY is None:
        raise ValueError("视频及参考图片上限校验需要同级short-drama技能的video_contract.py")
    return POLICY


def project(root):
    value = json.loads((root / "short-drama.json").read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("项目配置必须是对象")
    return value


def validate_reference_images(job):
    """Enforce the same image ceiling for every model and modality.

    Counts the supplied upload entries, not both representations added together.
    It neither opens files nor conflates audio/video entries with pictures.
    """
    suffixes = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff", ".avif", ".heic", ".jxl", ".jfif"}
    image_roles = {"reference_image", "first_frame", "last_frame"}
    other_suffixes = {".mp4", ".mov", ".webm", ".mkv", ".avi", ".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg",
                      ".txt", ".md", ".json", ".jsonl", ".csv", ".tsv", ".srt", ".vtt", ".pdf", ".docx"}
    def is_image(value):
        if not isinstance(value, str):
            return False
        return value.casefold().startswith("data:image/") or Path(value.split("?", 1)[0].split("#", 1)[0]).suffix.casefold() in suffixes
    refs = job.get("references", [])
    bindings = job.get("reference_bindings", [])
    typed_other = {x.get("path") for x in bindings if isinstance(x, Mapping)
                   and x.get("role") in ("reference_video", "reference_audio")
                   and isinstance(x.get("path"), str)} if isinstance(bindings, list) else set()
    def raw_picture(value):
        if is_image(value):
            return True
        if not isinstance(value, str) or value in typed_other:
            return False
        if value.casefold().startswith(("data:audio/", "data:video/")):
            return False
        # Untyped/extensionless references cannot bypass the picture ceiling;
        # an explicit audio/video binding supplies the missing media identity.
        return Path(value.split("?", 1)[0].split("#", 1)[0]).suffix.casefold() not in other_suffixes
    raw_count = sum(raw_picture(x) for x in refs) if isinstance(refs, list) else 0
    bound_count = sum(isinstance(x, Mapping) and (x.get("role") in image_roles or is_image(x.get("path")))
                      for x in bindings) if isinstance(bindings, list) else 0
    count = max(raw_count, bound_count)
    if count and count > policy().MAX_REFERENCE_IMAGES:
        raise ValueError(f"参考图片 {count} 张，超过全模型统一上限 {policy().MAX_REFERENCE_IMAGES} 张")


def validate_job(root, job, *, section=None):
    """Return canonical parameters; source and accepted project stay authoritative."""
    validate_reference_images(job)
    if job.get("modality") != "video":
        return dict(job.get("parameters", {}))
    p = policy()
    cfg = project(root)
    choices = p.accepted_choices(cfg)
    profile = p.resolve_profile(choices)
    parameters = dict(job.get("parameters", {}))
    preset = choices.get("video_service_preset")
    target = choices.get("target_video_model")
    if "target_video_model" in parameters and parameters["target_video_model"] != target:
        raise ValueError("工作单目标模型与项目选择不一致")
    if target:
        parameters["target_video_model"] = target
    if "video_service_preset" in parameters and parameters["video_service_preset"] != preset:
        raise ValueError("工作单服务档位与项目选择不一致")
    if preset:
        parameters["video_service_preset"] = preset
    fields = dict(re.findall(r"^- ([^：\n]+)：(.+)$", section or "", re.MULTILINE))
    source_duration = p.parse_seconds(fields.get("时长")) if section is not None else None
    if section is not None and source_duration is None:
        raise ValueError("来源MOTION必须声明合法正时长")
    task = fields.get("任务类型")
    if task is not None:
        if task not in ("reference", "edit", "extend"):
            raise ValueError("来源任务类型无效")
        if parameters.get("omni_reference_task_type") != task:
            raise ValueError("工作单任务类型必须与来源一致")
    if source_duration is not None:
        if task == "edit":
            if parameters.get("duration") != -1:
                raise ValueError("编辑任务要求duration=-1，源片时长另按来源记录")
        elif p.parse_seconds(parameters.get("duration")) != source_duration:
            raise ValueError("提交duration必须与来源MOTION时长一致")
    if task != "edit" and (source_duration is not None or choices.get("target_video_model") or "duration" in parameters):
        messages = p.unit_errors(parameters.get("duration"), profile,
                                 require_known=bool(choices.get("target_video_model")))
        if messages:
            raise ValueError("；".join(messages))
    fmt = cfg.get("format", {})
    ratio = fmt.get("aspect_ratio") if isinstance(fmt, Mapping) else None
    if task in ("edit", "extend"):
        if parameters.get("ratio") != "adaptive":
            raise ValueError("编辑/延长任务要求adaptive画幅")
    elif ratio and parameters.get("ratio") != ratio:
        raise ValueError("提交ratio必须与项目画幅一致")
    if task not in ("edit", "extend") and profile.get("ratios") and parameters.get("ratio") not in profile["ratios"]:
        raise ValueError("提交画幅不在所选服务支持列表中")
    expected_resolution = profile.get("resolution") or choices.get("output_resolution")
    if expected_resolution and str(parameters.get("resolution", "")).casefold() != str(expected_resolution).casefold():
        raise ValueError("提交resolution必须与项目/服务已确认分辨率一致")
    bindings = job.get("reference_bindings", [])
    counts = {"images": 0, "videos": 0, "audios": 0}
    roles = []
    for binding in bindings:
        role = binding["role"]
        roles.append(role)
        kind = "videos" if role == "reference_video" else "audios" if role == "reference_audio" else "images"
        counts[kind] += 1
    purposes = re.findall(r"用途：([^；）]+)", fields.get("输入参考图", ""))
    mode = p.resolve_mode(choices.get("generation_mode"), purposes,
                          video_count=counts["videos"], audio_count=counts["audios"])
    if task in ("edit", "extend"):
        if not counts["videos"]:
            raise ValueError("编辑/延长缺少实际参考视频；当前creator-first选择器不支持此输入")
        mode = task
    if choices.get("target_video_model") and profile.get("modes") and mode not in profile["modes"]:
        raise ValueError("当前模式超出已确认服务能力")
    messages = p.reference_errors(counts, profile, mode)
    if messages:
        raise ValueError("；".join(messages))
    if mode == "reference" and ("first_frame" in roles or "last_frame" in roles):
        raise ValueError("已选参考模式，不能把图片角色改为严格首尾帧")
    if mode == "first_frame" and roles != ["first_frame"]:
        raise ValueError("首帧输入角色必须为first_frame")
    if mode == "first_last_frame" and roles != ["first_frame", "last_frame"]:
        raise ValueError("首尾帧输入角色必须依次为first_frame、last_frame")
    if mode == "reference" and choices.get("target_video_model") and not (counts["images"] or counts["videos"]):
        raise ValueError("参考生视频缺少实际图像或视频输入")
    return parameters


def validate_adapter(root, job, config_path):
    """Match an operator-declared adapter contract before consuming confirmation."""
    if job.get("modality") != "video":
        return
    choices = policy().accepted_choices(project(root))
    if not choices.get("target_video_model"):
        return
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    selected = cfg.get("adapters", {}).get(job["adapter"], {})
    declared = selected.get("video_model_profile")
    if not isinstance(declared, Mapping):
        raise ValueError("视频adapter未声明video_model_profile；仅可保留文本/手动路线，未提交")
    for key in ("target_video_model", "video_service_preset"):
        if declared.get(key) != choices.get(key):
            raise ValueError("adapter的" + key + "与项目不匹配，未提交")
    if job["parameters"].get("resolution"):
        resolutions = declared.get("resolutions", [])
        if str(job["parameters"]["resolution"]).lower() not in [str(x).lower() for x in resolutions]:
            raise ValueError("adapter未声明接受目标分辨率，未提交")


def seedance_service_guard(parameters):
    """Pure guard for the official compiler; service aliases are not API models."""
    provider_model_guard(parameters, ("seedance-2.0", "seedance-2.5"))
    preset = parameters.pop("video_service_preset", None)
    if preset is None:
        return
    p = policy()
    if preset in ("seedance-2.0-low-cost", "seedance-2.0-mini", "seedance-2.0-standard"):
        raise ValueError("该服务档位未接入内置官方Seedance编译器；使用手动工具或已匹配的专用adapter")
    if preset != "seedance-2.5-advanced":
        raise ValueError("服务档位不属于此Seedance编译器")
    if parameters.get("omni_reference_task_type") != "edit":
        messages = p.unit_errors(parameters.get("duration"), p.PRESETS[preset])
        if messages:
            raise ValueError("；".join(messages))


def provider_model_guard(parameters, allowed):
    target = parameters.pop("target_video_model", None)
    if target is not None and target not in allowed:
        raise ValueError("target_video_model与当前编译器不匹配")
