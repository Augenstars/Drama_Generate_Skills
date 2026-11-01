# Assets And Asset-Image Prompt Rubric

## Occurrence and decision

- Can every production-relevant appearance be traced to a scene ID and a necessary action/dialogue quotation in `剧本.md`?
- Is it production-relevant rather than every noun in the screenplay?
- Is the decision explicit: reuse, new identity, new variant, or unresolved?
- Were pronouns, aliases, groups, memories, portraits, and screen content handled
  without guessing?

## Identity versus variant

### Character / Look

Identity: stable face/body/hair anchors, distinguishing marks, and any explicitly
recorded persistent voice identity. Look: wardrobe, makeup, hair arrangement, injury, dirt/wetness, disguise,
age/weathering state, validity range.

Fail when a costume change creates a new person or incompatible Looks mix in one
prompt without story reason.

Relationship labels may guide current blocking, gaze, and social presentation,
but they do not prove beauty, ugliness, body type, skin tone, or facial morality.
Fail when protagonist/antagonist status silently invents those identity traits;
creator-approved idealization or deliberate counter-casting remains a taste choice.


### Preparation depth for incidental people

Judge preparation depth by identity-recognition needs and visible continuity, not by appearance count alone. A different body, formation position, or temporary duty does not automatically require an independently managed identity or a detailed character sheet.

Incidental people may use group or wardrobe references where individual identity is irrelevant. Do not report an optional individual portrait as a required missing asset. Check necessary wardrobe, count, position, props, physical interactions, and continuity within the shot.

Flag unnecessary preparation when detailed sheets or individual-reference requirements have no stated production need. Also flag under-preparation when a clearly identifiable person or a consequential interaction loses necessary continuity. Do not reward fewer assets by itself or invent a new blocker solely because a sheet could be simplified. Explicit creator choices take precedence.

### Voice direction (optional, `AST-07`–`AST-12`)

Only reviewed when `视觉设定.md` records a voice direction. Timbre is carried by a
named reference recording, not by prose: identity is the reference plus the
creator's current pronunciation choices, and the text alongside it exists to
select or judge a voice, never to stand in for one.

Fail when:

- a project has no reference and a paragraph of adjectives is standing in for
  identity — the voice section must say `待选型` instead;
- a binding omits what it controls and what it must not, or lets the take's
  emotion, the recording space (reverb, mic distance) or background noise into
  identity (`AST-08`);
- a claim about what is audible in a reference has no creator description and no
  authorized listening observation, yet is written as established fact (`AST-09`);
- one proper noun appears with two accepted spellings anywhere in `视觉设定.md`
  (`AST-10`) — this one is structural and blocks;
- two characters designed together are bound to confusable references and no
  distinguishing trait names the nearest neighbour (`AST-11`);
- reference audio bytes, a provider parameter, a model name, a task field or a
  URL appear in `视觉设定.md` or the delivery package.

Selection criteria should be audible, bounded by counter-examples, and limited to what helps choose or judge a
reference (`AST-12`, `craft_default`). Report a weak criterion as a craft note; list length alone is not a failure.

### Location / View

Identity: architecture, layout, entrances, zones, anchors, materials, navigation.
View: camera-facing orientation/zone, time/weather/light state, visible anchors.

Fail when each camera angle becomes a new unrelated location or geography changes
silently between scene and plate.

Views of one Location sharing a time/weather state must also share key-light source,
warm/cool priority, contrast direction, and practical on/off state (`IMG-10`). Compare
the group side by side—each plate reading well alone is not evidence. Fail when an
unrecorded difference would read as two times or two rooms once the plates are
intercut; orientation-driven back/front lighting and occlusion shadows are expected
and need only a stated source.

### Prop / State

Identity: scale, shape, material, function, moving parts, marks, text policy.
State: owner/hand/location, open/closed, clean/damaged/wet/bloodied, contents,
validity.

Fail when a prop teleports, changes scale/material, or readable evidence is erased.

## Era

The era comes from source facts: devices, platforms, slang, stated years. Fail
when the era shown in `视觉设定.md`, `图片提示词.md` or `视频提示词.md` contradicts
them, or when a retro or aged descriptor (旧/老式/复古/褪色/斑驳, old, worn, dusty,
period, CRT) has neither a source basis nor an explicit creator choice (`AST-14`).
This is the visual layer of the source-fidelity check (`STY-07`): cite the source
fact and the conflicting line. A visual direction with
no era anchors, or entries that leave the era-specific form unstated, is a craft
note (`AST-15`).

## Prompt recipe review

All prompt types need purpose, exact binding, identifying facts, current variant,
composition, background, lighting, text policy, constraints, and exclusions. Then
apply type-specific criteria:

- Does each media reference declare one purpose, the facts it may copy,
  the facts it must not import, and a pixel/text admission decision?
- If a reference is composition-, scale-, or effect-only, did the prompt avoid
  borrowing its identity, wardrobe, content, text, count, or story state?

- **Character sheet:** one identity and coherent Look; useful reference views;
  neutral enough background/light to recognize anchors; no story action chain.
- **Location plate:** navigable geography, orientation, fixed anchors, material,
  palette, light direction, atmosphere; normally empty of cast.
- **Prop plate:** scale cue, shape, materials, wear, function/moving parts, current
  state, viewing angle, isolation, text policy.
- **Edit delta:** exact target and region, changes, preserve set, expected
  continuity impact; no unrelated regeneration.

## Prompt quality failures

- quality/style boilerplate appears before or instead of identity/geography/scale;
- prompt copies the whole visual specification instead of the needed identity and current variant;
- character description mixes immutable anchors with accidental pose;
- location prose is rich but cannot orient entrances/zones;
- one character or prop is assigned to mutually exclusive positions, hands, or
  relationship lines in the same frozen instant;
- prop has no scale or text state;
- negative constraints contradict the required visible fact;
- edit request says “make better” without target/change/preserve;
- `图片提示词.md` contradicts the current identity, state or text policy in `视觉设定.md`;
- private URL, source ID, provider task field, or operator complaint leaks in.
- “use the whole reference” does not say what may or may not be copied.

Prompt prose elegance is secondary to recognition, reuse, continuity, and clear
control of the current operation.

## 图像审阅的逐图反馈与更正提示词

适用于用户委托的实际图片审阅，包括参考图、定妆板、场景图、状态图及已生成图片；只检查本轮范围，不因写出修订建议扩成全库审查。复用来源按[具体原图定位](../../short-drama/references/reference-roles.md#复用图片必须可定位)写清，不能让“复用”掩盖未找到或不适用的原图。

### 每张不合格图片的交付

在审阅结果中逐张给出以下内容，同一图片的多个相容问题可合为一项：

- 原图片的准确文件名和项目相对路径，用户可打开的真实文件链接；已有REF、IMG可辅助定位，不能代替文件。多视图／状态板标出具体行列或局部。
- 不合格的是哪些可见事实、与当前哪条设定或分镜冲突、影响哪些实际IMG／SHOT／GROUP及阶段。区分整图不可用、仅某用途不合格和某局部仍可复用，不强行绑定不合格内容。
- 处理方式：优先选区或裁切即可解决的问题，其次局部编辑，必要时才重制。说明哪些内容必须改变、哪些正确内容必须保留；只需裁切时明确无需二次生成，并给出具体裁切／选区修正指令。
- `### 更正提示词`：在同一结果项内给唯一完整、可直接复制的引用块，每个非空正文行以`>`开头，使用项目图片提示词语言。正文明确目标对象和区域、改后的正确可见状态、保持项、必要视角／光线／文字约束；局部编辑的正文足以独立使用。不能只写“修正脸”“门向改一下”、重贴未变原prompt或追加质量形容词，也不能只让用户下一轮再找图片技能。
- 输入及使用说明放在正文外：实际需要上传的原图、身份依据或布局依据及顺序，允许采用的输出区域，以及应替换的旧引用。正文不含文件路径、QA结论或待填占位符；更正尚未执行，修订后文件及裁片不登记为已有REF。

多张图只有在修改目标和保持项确实相同时才能共用一份正文，仍须逐文件标明适用区域及差异；不同人物、造型、状态或空间不能用一条笼统prompt混修。报告可按文件索引合并重复用途，不另建平行素材台账。交付摘要点名不合格原图并链接其结果；数量较多时可指向报告内的逐图索引，不只报“若干图片有问题”。用户只要对话结论时，在回复中直接提供对应更正正文，不为此强制创建额外文件。

### 真实性与阶段边界

没有读到像素、文件缺失或不可读时，写“未核验／无法读取”及具体缺口，不把推测写成已经看见的不合格事实。已有可证实缺陷但修复还依赖原身份图、未定批号或日期时，在正文外列清实际缺失输入；可确定部分仍给有保持边界的更正正文，不自造脸、精确文字或文件路径，不声称已经修好或可自动投产。

更正应服从已确认剧情、人数、造型、门窗布局、左右、持物与文字政策，不为消除图片缺陷暗改分镜边界、时长、生成组或参考生路线。照片／参考输入与生成结果的证据分开，负面提示词不能使错误像素自动消失。报告内给出更正正文属于修订要求；审查本身不修改来源文件、不裁片、不生成媒体，用户另有明确授权的同轮修改按原owner分工执行。准备修订输入时仍按实际上传文件去重和每次最多9图的既定上限，资产库总量不因此受限。
