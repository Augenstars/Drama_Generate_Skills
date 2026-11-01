# Storyboard, Keyframe, And Motion Rubric

## 目录

- [Coverage](#coverage-and-meaning)
- [Shot](#shot-purpose-and-geography)
- [Keyframe](#frozen-keyframe)
- [Motion](#motion)
- [Continuity](#cross-shot-continuity)
- [Rhythm profile](#rhythm-profile-shots)
- [Findings](#common-findings)
- [Production risks and authorized observations](#production-risk-and-authorized-observation-checklist-rev-08)

## Coverage and meaning

- Can every production-relevant action, line, sound, or on-screen text in `剧本.md` be traced to a shot or an explicit omission reason?
- Are omissions/repeats explained?
- Does each shot preserve the source action, dialogue, information, and reaction?
- Has downstream work invented or deleted a story fact?

## Shot purpose and geography

- For a high-value scene with an accepted coverage audition: did the approaches
  genuinely differ — in knowledge timing, audience alignment, performance space,
  strongest image, landing, losses, or production fit?
- Do the final shots in `分镜.md` implement the approach the creator selected?
- When a scene visual plan was used: do its start/end audience positions, spatial
  pressure, camera rhythm, reaction landing, and sound movement carry **one** dramatic turn?
- Does that plan stay clear of owning shot boundaries? (Ordinary scenes need no plan
  merely to satisfy a form.)
- What changes for audience or character by the shot end?
- Why is this a new shot?
- Do framing and camera behavior serve attention, alignment, pressure, reveal, or
  rhythm rather than decorate the prose?
- Does each shot's `运镜` line state a behavior and a reason chosen from the shot's
  purpose (`SHT-04`)? A stated lock-off with its reason passes. An episode locked on
  nearly every shot while its peak gets no movement is a finding; so is a missing line,
  which leaves the choice to the video-prompt stage; a bare 「运镜：固定」 with no reason
  is also a finding.
- Are Location/View, axis, screen direction, eyelines, entrances, positions,
  hands, and props coherent?
- Are exact asset variants bound?
- Does the shot expose every fact it must carry while protecting
  facts the source withholds until a later action or cut?
- Do crop, occlusion, focus, back view, and offscreen space serve that information
  permission rather than accidentally reveal or conceal it?

## Rhythm profile: shots

Under the `REV-12` conditions in the [story rubric](rubric-story-script.md#rhythm-profile-rev-12),
measure two storyboard fields: the average shot length per scene (scene duration divided
by its shot count) against `target_avg_shot_seconds`, and the share of close-range shots
across the episode against `close_shot_share_min`. Close-range shots include 近景、特写、大特写 and 细节镜头;
divide their count by the episode's total shot count. The average is a
scene-level target; one long or short shot is not a finding. Also report durations folded
from screenplay word counts instead of the scene's sound timeline (`SHT-28`).

## Frozen keyframe

- Can all described facts exist in one still instant?
- Does it project the start state written for this shot?
- Are focal hierarchy, composition, camera/lens, geography, pose/gaze/hands/prop,
  expression, and light legible?
- Does it avoid ordered actions, performance arcs, camera moves, or transforming
  environments?
- Read the finished keyframe text, not the shot's intent: is every visible character,
  place, and prop whose identity, Look, or geography must stay recognizable listed in
  this shot's `视觉依据` (`SHT-22`)? A second body that entered the composition while the
  frame was being written is the usual miss.
- Does each declared 控制 scope stay inside what this frame can carry, and is nothing
  bound merely because it was bound in the previous shot (`SHT-24`)?
- When real reference images are bound, does every `REF-...` slot declare a 用途, so the
  shot says which start frame and which identity/geography/prop pictures it sends
  (`SHT-25`, `VID-24`)?
- Is anything the frames need kept consistent across shots — a carried prop, a garment —
  absent from `视觉设定.md` entirely, so it can appear in no shot's basis at all? The
  mechanical check cannot see this: an entry that does not exist cannot be reported missing.

## Motion

- 在“Motion”内增加“GROUP语义覆盖”检查：逐镜事实是否完整；共用段是否扩大范围；图号与累计时间是否正确；GROUP是否独立可用。
- Does it start from the accepted frame/boundary?
- Are subject actions ordered and feasible within the accepted duration while preserving the intended performance?
- Does performance change express the story move rather than stack synonyms?
- In multi-character motion: do the actors who actually change have distinct,
  readable triggers, choices, leaks, or landings — as this shot needs, not one
  identical arc per actor?
- Is attention handed off only where it truly transfers, rather than for
  synchronized reaction?
- Does any text-readiness claim cite the current creator-visible inputs and a real blocking gap?
- Does it avoid any claim about generated media quality or create a second readiness truth?
- Is camera behavior coherent and motivated?
- Are environment motion, dialogue, SFX, and audio included only when relevant?
- Does the described end match the storyboard's written end state without rewriting the next shot?
- When a reference frame carries appearance/composition, does motion prose retain only the visual facts this shot needs?
- Does every claim about text-bearing reference pixels cite a creator/reference-owner
  description or an authorized input-reference observation? Without that evidence,
  is admission still `unverified` instead of pretending a negative prompt solved it?
- For any selective transform, are the accepted trigger, exact target scope,
  end geometry/state, and preserve set explicit? Do non-target people, props,
  text surfaces, and spatial anchors keep their required position, count, and state?
- Does each media reference state its exact purpose, what may be copied, and what
  must not be copied, rather than treating all visible pixels as authority?

For a copyable body (`VID-22`, `VID-23`), check that actions and sound match the
source and that the timeline accounts for the intended ambience or silence.
A summary must not introduce a layer absent from the shot. H3's
`non_diegetic_music: N/A` is a valid empty music layer.

Report a concrete contradiction, omission or ambiguity. A negative clause is
not a defect by itself; do not impose a clause count or assume that negation
causes the model to generate the excluded content. Keep model-specific
observations scoped to their tested model and execution path.

For a pickup or alternate, ask these separately:

- Does the pickup/alternate identify its master? Keep candidate differences in ordinary notes and one formal `MOTION-...` with one copyable body per `SHOT-...`; a separate pickup first needs its own storyboard shot.
- Is every source obligation assigned to the master, this version, another named version or a requested storyboard revision?
- Are the changed items and the items that must remain unchanged explicit?
- Is replacement only requested here? The review Markdown decides whether to adopt the candidate; the owning skill then updates the formal body.

For music, ask these separately (`VID-14`):

- Is intent written as a relative entry/exit/duck against neighbouring shots,
  rather than an independent cue per shot?
- Do adjacent annotations actually join?
- Does the text ask for a per-shot music bed against an accepted timeline-layer plan?
- Whether a rendered clip carries a baked-in track is **not decidable here**. Cite it
  only from an authorized text observation record; otherwise keep it `unverified`
  and never infer a mix result from prose.

Explicit timing that does not sum exactly to its shot's accepted duration—over or
under—is a structural error. Untimed overload is a
reviewed feasibility question: cite which action/performance/story beat would be
lost, not a universal verbs-per-second formula.

Container arithmetic is a separate structural check (`VID-13`). Count the accepted
shots a delivery container carries, then confirm its duration equals the sum of
their accepted durations. For a multi-shot container, confirm the members are
contiguous in source order, share one geography/asset binding chain, do not cross a
scene boundary, and each remains independently reviewable. A space or subject jump
belongs on a member boundary; the same jump inside a member's timed segment is a
hidden cut. Report an arithmetic mismatch and a hidden cut as two findings, not one.

- Is the axis recorded as two named anchors, a stated working side, and a per-character
  screen position — rather than a placeholder?
- In a shot-reverse-shot pair, are the two screen directions complementary?
- Bare left/right always means **screen** left/right. Where a subject's own side is
  meant, does the text name the subject?

## Cross-shot continuity

Trace Look, injury, dirt/wetness, emotion/knowledge, position/facing/gaze, hands,
held prop, prop owner/state, location/time/weather/light, axis, and screen
direction. Distinguish unexplained contradiction from declared montage,
ellipsis, dream, or deliberate disorientation.

### 相邻GROUP的接点与过渡

逐对连读前GROUP末段和后GROUP开场，先判断同场延续、换景、跳时、穿越或有意反差，再定位具体问题：

- 前镜切出动作阶段、后镜接入状态、方向/轴线及左右手持物是否可接；是否人为停住或重演已完成动作。
- 新地点/时间是否在该知道时可辨；若通过空镜、声音或特效揭示，是否有来源与职责，是否泄露源文延迟信息。
- 空镜能否交代地理、时间、后果、情绪或注意；不因无人/无对白/静态就删，也不要求每组都插空镜。
- 穿越等关键转场是否从已确认触发走到可读的变化、到达和人物反应；是否只写特效名称，或擅自新增机制。
- 声音桥的来源、先入/延续与退出是否明确；同一句话或同一音效是否被两份GROUP重复生成，现场声与叙事声桥是否混淆。
- 生成段与后期责任是否分清；独立GROUP是否各自完整，是否误把普通切镜写成需要真实上一段输入的续写。
- 新空镜/切点是否已回填SHOT、MOTION、成员和累计时间；叠化重叠是否重算成片总长；低价规则是否仍只约束GROUP。

硬切可服务冲击和反差，不因未用叠化就报错。相反，风景或特效若遮不住因果、持物与时空理解缺口，指出丢失的事实与修订owner，不以“加一个过渡”替代建议。文字检查只证明计划，未看实际成片就不能声称接缝已平滑。

## Common findings

- beautiful shot with no dramatic purpose;
- dialogue covered but consequential reaction absent;
- anonymous asset or wrong variant;
- cross-location/time action hidden in one ordinary shot;
- keyframe contains “first/then/finally”;
- locked camera also pans or pushes in the same interval;
- motion invents a grab, injury, transfer, relationship change, or line;
- a selective transform removes, copies, or reshapes a non-target person, prop,
  text surface, or spatial anchor because its preserve set was unspecified;
- end pose/prop state disagrees with next start;
- every emotional beat uses the same close-up/push template;
- provider batching is mistaken for editorial shot structure.
- a narrowed pickup silently replaces the master and drops dialogue, reaction,
  reveal, end-state, or creator-directive obligations.

## Production-risk and authorized-observation checklist (REV-08)

按证据路径区分判断：用户已授权只读检查且当前环境能够读取媒体时，可直接观察，并在审查里写清文件/时间段、方法与限制；媒体不可读时，只根据文字风险或用户提供的可核对观察记录判断。直接观察到的事实与提示词中的潜在风险分开写。没有实际观察时保持结果未知，不从任务成功、结果地址或提示词存在推断成片质量。只读检查不等于生成或付费提交授权。

需要项目校准时，先区分输入参考与生成结果。后一种观察须绑定准确的提示词/镜头标题、参考顺序、
制作形态/配置、观察方法和限制；先按 `REV-11` 选择处置，需要改动时再写最小修改项与保持项。
结论只在该项目和版本条件下有效。

短剧生产中需要防范的文字风险或获授权观察包括：

- on-screen text or subtitle residue despite a declared no-text constraint;
- a text-bearing reference admitted under no-text or exact-readable policy
  without an allowed surface or a crop, clean, mask, or replace decision;
- background music implied where the audio boundary allows sound effects only;
- wardrobe or look drift against the bound reference (re-describing clothes the
  reference already fixes invites drift — flag redundant appearance prose);
- 180° axis violation or eyeline mismatch across consecutive shots without a
  declared transition;
- lip-sync mismatch: dialogue bound to the wrong character, inner monologue
  written as mouthed speech, or extra lines the source dialogue never contained;
- explicit segment timings that do not sum exactly to the shot duration, in either direction;
- emotion-intensity mismatch between stated level and described performance
  (a declared 9/10 rage performed as mild irritation, or the reverse).
