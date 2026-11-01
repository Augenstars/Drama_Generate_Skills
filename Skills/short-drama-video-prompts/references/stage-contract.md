# 视频提示词阶段契约

本阶段只拥有 `剧集/<EP>/视频提示词.md` 中的 `MOTION-...`、正式 `GROUP-...` 项与按需的时间线音乐章节。它继承镜头
起点、终点、时长、对白和冻结帧，不回写分镜或视觉设定：镜头边界、职责、起终状态和关键帧正文都不在
本阶段手里。

唯一的例外是参考准备。SKILL 的参考发现与绑定流程要求在同一请求内刷新受影响镜头的「输入参考图」
（必要时一并回填「视觉依据」），那是**分镜 owner 在本请求内的动作**，按分镜阶段的字段规则执行，
不是本阶段改写分镜的授权。它只更新这两条依据字段，不动镜头边界、职责、起终状态或关键帧正文。

每项正文只描述从当前冻结起点到终点的变化；多镜打包、补拍或替代关系确有需要时，也写在同一文档
的可读章节中，不建立 motion spec、container、readiness、QA 或接受记录。

## 明确传记的片外例外

上文所有权和下表逐镜规则面向正式剧集。明确传记的演员验证按[共享前置验证](../../short-drama/references/biography-actor-preflight.md)先交片外测试正文，可无正式分镜；按用户要求保存时用既有可选项目开发区。它不冒用SHOT／MOTION／GROUP，也不占成片时长。

## 本阶段规则

### `VID`

| ID | Class | Knowledge |
|---|---|---|
| VID-01 | structural_invariant | A MOTION preserves its SHOT start, end, duration and dialogue. Its duration equals the SHOT duration; a loose singleton submits that duration, while a GROUP submits the sum of its members. Native ranges and integer/discrete constraints govern actual submission units, not every internal member. Stale downstream boundaries are defects even when strings parse. |
| VID-02 | craft_default | Write start anchor, ordered subject motion, camera behavior, timing, and end report; add performance change and environment/audio only when this shot actually carries them. |
| VID-03 | structural_invariant | Reference readiness has three states: verified REF files may enter production preflight; creator-authorized PLAN slots allow complete manual-use text but never automatic submission; unresolved required gaps stop the final text unless the creator selects the PLAN route or explicitly selects text-to-video. Missing references alone never authorize text-to-video. VID-24 defines inherited slots and mode selection. |
| VID-04 | structural_invariant | Explicit segment timing sums exactly to its shot's accepted duration—neither exceeding it nor leaving an unallocated remainder. |
| VID-05 | reviewed_invariant | Untimed action load must be feasible enough to preserve the intended performance and story change. |
| VID-06 | structural_invariant | Locked and moving camera instructions cannot govern the same interval without an explicit transition. |
| VID-07 | taste_option | Camera may be locked or moving; audio/lip-sync detail follows the chosen production profile. |
| VID-08 | reviewed_invariant | Structured motion names this shot's exact subjects, actions, contacts, and results rather than reusable placeholders; when a performance path is present, it names only the actors and visible changes this shot actually carries. |
| VID-09 | structural_invariant | The next start names an existing `SHOT-...` or is explicitly unresolved; never invent a hidden source key, record or hash. |
| VID-10 | craft_default | Resolve one accepted production profile for the current delivery scope; local variants may coexist when their range and precedence are explicit, without overriding source coverage or exact-readable obligations. |
| VID-11 | reviewed_invariant | A selective transform names its trigger, exact target scope, end geometry/state, and preserve set so non-target people, props, text surfaces, and spatial anchors do not change with it. |
| VID-12 | reviewed_invariant | A pickup or alternate names stable `MOTION-...` IDs and maps each source requirement to this version, the master, another pickup, or a requested storyboard revision; it never silently replaces the master. |
| VID-13 | structural_invariant | A multi-shot delivery group contains contiguous shots from one scene with one geography/asset chain. Its duration equals the sum of member shots, and grouping changes neither shot boundaries nor per-shot reviewability. |
| VID-14 | craft_default | Music intent may be annotated per shot as a relative entry/exit/duck against neighbours, but its realization belongs to the timeline layer; no deliverable—single-shot or multi-shot container—carries a baked-in music bed unless the project accepted otherwise or the source is diegetic. Dialogue, off-screen sources, ambience, and event effects stay with the deliverable. |
| VID-15 | structural_invariant | Every visible shot is counted exactly once through its group or as a loose singleton. The default mixed delivery route permits both. Only an explicitly accepted delivery_route of groups_only requires every MOTION to belong to one GROUP. Model choice alone never changes this delivery policy. |
| VID-16 | reviewed_invariant | When performance changes, multi-character motion differentiates the actors who actually carry it and keeps each chosen signal readable in the accepted framing; it does not require an arc for non-performing shots, force every craft field, or duplicate one emotion across the cast. |
| VID-17 | reviewed_invariant | Multiple references use stable visible IDs and an explicit order, so reordering cannot silently change which reference controls which property. |
| VID-18 | reviewed_invariant | Readiness is reported from the current visible inputs and real blocking gaps, not persisted as a motion fact; text readiness never claims generated identity, performance, lip-sync, mix, edit or market quality. |
| VID-19 | reviewed_invariant | When the creator profile declares required literal tokens for a delivery route, that route's delivery text preserves them byte-for-byte and outside the verbatim-dialogue fence. Paraphrase, translation, reordering, or omission is treated as a defect because a literal-matching surface has no reason to reject the rewritten text—the failure is silent rather than reported. The suite asserts no specific surface's behaviour, and whether a given result took the route is returned adherence, provable only by a bound production observation. Tokens declare a route and never substitute for the start state, action, or endpoint. Absent a declared token list the suite invents none; until the profile exposes a machine-readable list at a pinned field path, the reviewer cites the profile against the delivery text rather than claiming mechanical enforcement. |
| VID-20 | reviewed_invariant | Packing routes change delivery granularity only, leaving shot boundaries, shot purpose, and per-shot reviewability intact. A single long-form generation carrying several accepted shots *is* a multi-shot container and is billed under VID-13 and VID-15; it introduces no separate accounting and no exemption from the contiguity, binding-chain, and scene-boundary constraints. A continuation route instead starts from a previously generated result, which is observation evidence and not an accepted artifact: the accepted shot start boundary stays the sole authority, and any claim about the observed state binds a production observation record or remains `unverified`. |
| VID-21 | craft_default | When the project's accepted production profile has generated imagery carry the frame, actions are written as high-frequency, whole-body or single-limb movements common in everyday footage; precise interception, invisible internal states, negative actions, and three-or-more-step two-handed choreography are rewritten into equivalent common-action combinations, with the dramatic information carried by combination and timing. The rule is inactive for live action or an undeclared profile, and a rewrite may never change accepted shot boundaries, terminal states, or screenplay fact. |
| VID-22 | reviewed_invariant | Copyable text describes the intended image and action. IDs, workflow status, hashes and file paths stay outside it. Prefer observable states where they clarify execution; necessary negative constraints are allowed. Unless explicitly authored, prohibit non-diegetic subtitles, captions and dialogue overlays while preserving approved in-scene text and its exact content, carrier and placement. |
| VID-23 | reviewed_invariant | For models generating audio with video, specify the intended dialogue, VO, OS, vocalizations, effects, ambience and silence. Keep source, speaker, language and verbatim dialogue boundaries. Summaries must match the actual sound layers; follow model-specific music syntax without assuming missing layers will always be generated. |
| VID-24 | structural_invariant | Copy REF/PLAN slots and their order, purposes and scopes unchanged from storyboard. An explicit accepted generation_mode has priority; only if absent infer mode from purposes. Check compatibility before mapping provider roles; reference mode uses reference inputs and does not silently become strict first/last-frame conditioning. Resolve conflicting purposes upstream or report the gap; never silently switch route. |
| VID-25 | structural_invariant | Quoted Chinese in a copyable body is delivered, not authored. Every run of four or more Han characters inside a `<d>` tag or quotation marks resolves, ignoring punctuation and spacing, to text that already exists in `剧本.md`, `视觉设定.md` or `分镜.md`. A line the shot wishes the character had said belongs upstream in the screenplay, not in the prompt. Runs of three characters or fewer are in-frame labels and interjections far more often than lines, so they stay with review rather than the mechanical check. |
| VID-26 | craft_default | Absent a director's choice, performance intensity follows form and genre. At motion-comic and wish-fulfilment peaks, key poses and expressions go outward—an expression change readable at a glance, whole-arm gestures, emotion carried by the upper body and the whole face—still written as common whole-body actions, never with the plot resting on a micro-expression. AI live action keeps a subtler realism but still gives each peak one readable performance beat. An inferred inner state is not deleted but translated into a visible expression or movement. |
| VID-27 | structural_invariant | A voice reference is bound on its own `参考音频` line of a `MOTION-...` entry, never inside `输入参考图` and never on a `SHOT-...`. Each slot names a `人物` entry of `视觉设定.md` who speaks in the executable body (this independent MOTION or its actual GROUP) a line the screenplay gives that character, points at a readable project audio file equal to the path that character's `声音参考` records, has 用途 `音色`, and numbers audio 顺序 from 1 separately from pictures. Whether the bound voice actually carried into the take is heard after generation, not asserted here. |

### `CON`

| ID | Class | Knowledge |
|---|---|---|
| CON-01 | structural_invariant | Linked end and next start states match or have an explicit owner revision. |
| CON-02 | reviewed_invariant | Knowledge, injury, ownership, weather, light, or physical state does not teleport/regress without story cause. |
| CON-03 | craft_default | Track downstream-relevant deltas, not the whole 设定集 in every shot. |
| CON-04 | structural_invariant | A continuity change states before, after, cause/source scene, effective range, and affected visible IDs. |
| CON-05 | taste_option | Declared montage, ellipsis, dream, or subjective imagery may intentionally break ordinary continuity. |
| CON-06 | structural_invariant | A continuity change names every existing downstream document it affects; future work is described, not pre-created. |
| CON-07 | structural_invariant | A continuity lock keeps its verbatim surface in each in-scope executable unit (independent MOTION or GROUP) and named image prompt. Explicit GROUP-member review records need not duplicate executable prose; their actual GROUP still carries all member lock surfaces. A frozen start carries it only when the owning entry is visible in 开场视觉依据; legacy documents default that set to 视觉依据. Later entry facts stay in their motion stage, never leak into the opening to satisfy a lock. |

规则分级由高到低：`structural_invariant`（结构缺陷，阻断）、
`reviewed_invariant`（需证据判断）、`craft_default`（常用做法，可覆盖）、
`taste_option`（创作者选择，不作缺陷）。创作者已接受的事实优先于本表。
