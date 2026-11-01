#!/usr/bin/env python3
"""Derive upload maps and timing from accepted Markdown; never create media.

The source documents remain authoritative. Output is a disposable projection,
not a new asset registry, a prompt writer, or a production-ready job.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import OrderedDict
from pathlib import Path

import creator_markdown_check as c
from video_contract import accepted_choices, reference_errors, resolve_mode, resolve_profile, unit_errors


def _fields(body: str, owner: str) -> dict:
    errors: list[str] = []
    result = c._fields(body, owner=owner, errors=errors)
    if errors:
        raise ValueError("；".join(errors))
    return result


def _sections(text: str, kind: str) -> dict:
    ids = re.findall(r"^## (" + kind + r"-[A-Z0-9-]+)\b", text, re.M)
    if len(ids) != len(set(ids)):
        raise ValueError(kind + "标题重复")
    return c._sections(text, kind)


def _identity(kind: str, locator: str, root: Path | None) -> tuple:
    # Equal contents in different files are NOT evidence of the same input.
    # Distinct PLAN entry IDs stay separate even when they depict one person.
    if kind == "REF" and root is not None:
        locator = str((root / locator).resolve())
    return kind, locator.replace("\\", "/").casefold()


def _pictures(value: str, owner: str, root: Path | None) -> list:
    errors: list[str] = []
    c._references(value, owner, root, errors)
    if c._has_pending_references(value):
        errors.append(owner + ": 必要参考仍未解决；先保留缺口，不生成正式上传映射")
    if errors:
        raise ValueError("；".join(errors))
    result = [{"slot": d[0], "source_order": int(d[1]), "kind": kind,
             "locator": d[2], "label": d[3], "purpose": d[4],
             "control": d[5], "exclude": d[6]}
            for _, _, kind, d in c._slot_matches(value)]
    return sorted(result, key=lambda item: item["source_order"])


def _audios(value: str, owner: str, root: Path | None) -> list:
    if not value:
        return []
    matches = list(c.AUDIO_REF_RE.finditer(value))
    if not matches or "；".join(m.group(0) for m in matches) != value:
        raise ValueError(owner + ": 参考音频语法不完整；不能静默丢弃输入")
    result = []
    for m in matches:
        d = m.groups()
        if d[4] != c.AUDIO_PURPOSE:
            raise ValueError(owner + ": 参考音频用途必须为音色")
        errors: list[str] = []
        c._check_project_file(d[2], owner, root, errors)
        if errors:
            raise ValueError("；".join(errors))
        result.append({"slot": d[0], "source_order": int(d[1]), "kind": "REF",
                       "locator": d[2], "label": d[3], "purpose": d[4],
                       "character": d[5], "control": d[6], "exclude": d[7]})
    result.sort(key=lambda item: item["source_order"])
    if [r["source_order"] for r in result] != list(range(1, len(result) + 1)):
        raise ValueError(owner + ": 音频编号须独立从1连续排列")
    if len({r["slot"] for r in result}) != len(result):
        raise ValueError(owner + ": 音频槽位重复")
    return result


def build_map(storyboard: str, video: str = "", *, root: Path | None = None,
              profile: dict | None = None, explicit_mode=None) -> dict:
    shots = _sections(storyboard, "SHOT")
    if not shots:
        raise ValueError("没有已确认SHOT，不能推测镜头或生成组")
    sf = {sid: _fields(body, sid) for sid, body in shots.items()}
    motions = _sections(video, "MOTION")
    mf = {mid: _fields(body, mid) for mid, body in motions.items()}
    by_shot = {}
    for mid, fields in mf.items():
        sid = fields.get("分镜", "")
        if sid not in shots or sid in by_shot:
            raise ValueError(mid + ": SHOT不存在或被重复引用")
        if fields.get("输入参考图", "") != sf[sid].get("输入参考图", ""):
            raise ValueError(mid + ": 参考绑定与分镜不一致，先同步来源")
        if c._declared_seconds(fields.get("时长", "")) != c._declared_seconds(sf[sid].get("时长", "")):
            raise ValueError(mid + ": 时长与分镜不一致")
        by_shot[sid] = mid
    groups = _sections(video, "GROUP")
    selected: OrderedDict = OrderedDict()
    plan_errors = []
    plan_declared, planned, declared_windows = c._storyboard_group_plan(shots, plan_errors)
    if plan_errors:
        raise ValueError("；".join(plan_errors))
    if groups:
        for gid, body in groups.items():
            fields = _fields(body, gid)
            members = c._group_members(fields.get("成员", ""))
            if not members or any(mid not in mf for mid in members):
                raise ValueError(gid + ": 成员不存在或为空")
            selected[gid] = [mf[mid]["分镜"] for mid in members]
    else:
        selected.update(planned)
        if not selected and re.search(r"GROUP-[A-Z0-9-]+", storyboard):
            raise ValueError("分镜提到GROUP但没有可解析成员，不将其擅自改成独立镜头")
    covered = [sid for members in selected.values() for sid in members]
    if len(covered) != len(set(covered)):
        raise ValueError("同一镜头重复进入生成组")
    if groups:
        c._check_storyboard_group_delivery(shots, selected, plan_errors)
        if plan_errors:
            raise ValueError("；".join(plan_errors))
    order = list(shots)
    for gid, members in selected.items():
        positions = [order.index(sid) for sid in members]
        if positions != list(range(positions[0], positions[0] + len(positions))):
            raise ValueError(gid + ": 成员不按分镜相邻顺序排列")
        scenes = set()
        for sid in members:
            errors: list[str] = []
            scenes.update(c._shot_sources(sf[sid].get("来源", ""), sid, None, errors))
            if errors:
                raise ValueError("；".join(errors))
        if len(scenes) > 1:
            raise ValueError(gid + ": 不能跨场次")
    # Include loose shots once, interleaved in source order. An ungrouped shot
    # is reported as loose, never assigned a new group or a rounded duration.
    unit_of = {sid: gid for gid, members in selected.items() for sid in members}
    units = []
    emitted = set()
    for sid in order:
        uid = unit_of.get(sid, by_shot.get(sid, sid.replace("SHOT-", "MOTION-", 1)))
        if uid in emitted:
            continue
        emitted.add(uid)
        members = selected.get(uid, [sid])
        images, audios, mapping, timeline = [], [], [], []
        seen = {"image": {}, "audio": {}}
        elapsed = 0.0
        for member in members:
            fields = sf[member]
            source_errors: list[str] = []
            c._shot_sources(fields.get("来源", ""), member, None, source_errors)
            if source_errors:
                raise ValueError("；".join(source_errors))
            seconds = c._declared_seconds(fields.get("时长", ""))
            if seconds is None:
                raise ValueError(member + ": 时长无效")
            start, end = elapsed, elapsed + seconds
            if member in declared_windows and declared_windows[member] != (start, end):
                raise ValueError(member + ": 生成组累计秒段与镜长不一致")
            mid = by_shot.get(member, member.replace("SHOT-", "MOTION-", 1))
            downstream = mf.get(mid, {})
            if "参考视频" in fields or "参考视频" in downstream:
                raise ValueError(member + ": 当前Markdown未定义参考视频槽位语法，请保留人工清单；工具不猜测视频编号")
            raw_input = fields.get("输入参考图", "")
            pics = _pictures(raw_input, member, root)
            audio = _audios(downstream.get("参考音频", ""), mid, root)
            if not pics and not c._is_explicit_text_to_video(raw_input):
                raise ValueError(member + ": 未明确选择文生视频，不能用空参考继续")
            timeline.append({"shot": member, "motion": mid, "start": start, "end": end,
                             "seconds": seconds, "raw_input": raw_input,
                             "source_fields": {k: fields.get(k, "") for k in
                                               ("起点", "唯一动作", "动作过程", "景别/机位", "运镜", "终点", "声音")}})
            for media, refs, target in (("image", pics, images), ("audio", audio, audios)):
                local = {}
                for ref in refs:
                    key = _identity(ref["kind"], ref["locator"], root)
                    local.setdefault(key, len(local) + 1)
                    if key not in seen[media]:
                        seen[media][key] = len(target) + 1
                        target.append({"number": len(target) + 1, "kind": ref["kind"],
                                       "locator": ref["locator"], "roles": []})
                    number = seen[media][key]
                    role = {**ref, "shot": member, "motion": mid, "start": start, "end": end}
                    target[number - 1]["roles"].append(role)
                    mapping.append({"motion": mid, "media": media, "slot": ref["slot"],
                                    "source_order": ref["source_order"],
                                    "member_number": local[key], "unit_number": number})
            elapsed = end
        if uid in groups and c._declared_seconds(_fields(groups[uid], uid).get("时长", "")) != elapsed:
            raise ValueError(uid + ": GROUP总时长与成员之和不一致")
        counts = {"images": len(images), "videos": 0, "audios": len(audios)}
        purposes = [r["purpose"] for x in images for r in x["roles"]]
        # Purpose inference is meaningful per request; explicit project mode wins.
        mode = resolve_mode(explicit_mode, purposes, audio_count=len(audios))
        errors = unit_errors(elapsed, profile or {}) + reference_errors(counts, profile or {}, mode)
        if (profile or {}).get("modes") and mode not in profile["modes"]:
            errors.append("生成模式超出已确认服务能力")
        if errors:
            raise ValueError(uid + ": " + "；".join(errors))
        units.append({"id": uid, "type": "GROUP" if uid in selected else "loose",
                      "seconds": elapsed, "images": images, "videos": [], "audios": audios,
                      "timeline": timeline, "mapping": mapping,
                      "has_plan": any(x["kind"] == "PLAN" for x in images)})
    if (profile or {}).get("delivery_route") == "groups_only" and any(u["type"] == "loose" for u in units):
        raise ValueError("已接受groups_only路线，不能将未归组镜头当作独立提交单位")
    return {"schema": "derived-reference-map/v1", "production_ready": False,
            "notice": "仅从当前来源派生编号与预算；不替代逐图审阅、声音身份检查、阶段覆盖或正式正文。未创建媒体或裁片。",
            "seconds": sum(u["seconds"] for u in units), "units": units}


def markdown(data: dict) -> str:
    lines = ["# 派生上传映射与累计时间", "", data["notice"], ""]
    escape = lambda x: str(x).replace("|", r"\|").replace("\n", " ")
    def tag(media: str, number: int) -> str:
        dialect = data.get("dialect")
        if dialect == "wan-3.0":
            return ("图" if media == "image" else "音频") + str(number)
        if dialect == "minimax-h3":
            return '`<' + ("Picture" if media == "image" else "Audio") + f' {number}>`'
        prefix = "@" if dialect in ("seedance-2.0", "seedance-2.5") else ""
        return prefix + ("图片" if media == "image" else "音频") + str(number)
    for unit in data["units"]:
        lines += [f'## {unit["id"]}', "", f'- 总时长：{unit["seconds"]:g}s；PLAN：{unit["has_plan"]}', "",
                  "| 类型顺序 | 素材 | 职责、成员与原控制范围 |", "|---|---|---|"]
        for media, noun in (("images", "图片"), ("audios", "音频")):
            for ref in unit[media]:
                roles = "；".join(f'{r["motion"]}（{r["start"]:g}—{r["end"]:g}s）{r["slot"]}：{r["purpose"]}，控制：{r["control"]}，不得控制：{r["exclude"]}' for r in ref["roles"])
                lines.append(f'| {tag("image" if media == "images" else "audio", ref["number"])} | {ref["kind"]} · {escape(ref["locator"])} | {escape(roles)} |')
        lines += ["", "视频输入0；音频与图片分别从1编号。上表保留来源范围，具体入画阶段仍按成员开场、过程和终点核对。", "",
                  "| 成员 | 原槽位顺序 | 成员去重图号/音频号 → 整组号 |", "|---|---|---|"]
        for item in unit["mapping"]:
            noun = "图片" if item["media"] == "image" else "音频"
            lines.append(f'| {item["motion"]} | {item["source_order"]}／{item["slot"]} | {tag(item["media"], item["member_number"])} → {tag(item["media"], item["unit_number"])} |')
        lines += ["", "| 成员 | 组内累计时间 |", "|---|---|"]
        for member in unit["timeline"]:
            lines.append(f'| {member["motion"]} | {member["start"]:g}—{member["end"]:g}s |')
        lines.append("")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("episode", type=Path)
    ap.add_argument("--project-root", type=Path)
    ap.add_argument("--group", help="只返回一个已有GROUP或独立镜头")
    ap.add_argument("--format", choices=("summary", "json", "markdown"), default="summary")
    ap.add_argument("--output", type=Path, help="可选的派生文件；不覆盖五份来源文档")
    args = ap.parse_args(argv)
    try:
        episode = args.episode.resolve()
        root = (args.project_root or episode.parent.parent).resolve()
        board = (episode / "分镜.md").read_text(encoding="utf-8")
        vp = episode / "视频提示词.md"
        video = vp.read_text(encoding="utf-8") if vp.is_file() else ""
        cfg = root / "short-drama.json"
        choices = accepted_choices(json.loads(cfg.read_text(encoding="utf-8"))) if cfg.is_file() else {}
        data = build_map(board, video, root=root, profile=resolve_profile(choices), explicit_mode=choices.get("generation_mode"))
        data["dialect"] = choices.get("video_prompt_dialect") or choices.get("target_video_model")
        if args.group:
            data["units"] = [u for u in data["units"] if u["id"] == args.group]
            if not data["units"]:
                raise ValueError("指定生成单位不存在")
            data["seconds"] = sum(u["seconds"] for u in data["units"])
        if args.format == "summary":
            text = json.dumps({"production_ready": False, "seconds": data["seconds"],
                               "units": [{"id": u["id"], "seconds": u["seconds"],
                                          "images": len(u["images"]), "audios": len(u["audios"]),
                                          "has_plan": u["has_plan"]} for u in data["units"]]}, ensure_ascii=False, indent=2)
        else:
            text = markdown(data) if args.format == "markdown" else json.dumps(data, ensure_ascii=False, indent=2)
        if args.output:
            dest = args.output.resolve()
            if dest.name in c.REQUIRED_DOCUMENTS or dest == cfg.resolve():
                raise ValueError("派生输出不能覆盖来源文档或项目配置")
            if dest.exists():
                raise ValueError("输出文件已存在，选择新的派生文件名")
            with dest.open("x", encoding="utf-8") as stream:
                stream.write(text + "\n")
            print(str(dest))
        else:
            print(text)
        return 0
    except (OSError, ValueError, TypeError) as exc:
        print("无法派生：" + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
