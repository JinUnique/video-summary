# Video Type Summary Strategies

Use this reference after metadata/transcript/frame sampling and before writing the final `video-summary` document. Its purpose is to select a summary strategy by video type so the output extracts the video's real value instead of forcing every video into one generic template.

## Core Rule

Classify first, then write. The same Feishu delivery envelope can stay stable, but the analysis body, chapter focus, diagrams, and reusable-learning fields must change by video type.

Always produce a local or agent-report `video_type_decision` before synthesis:

```yaml
video_type_decision:
  primary_type: <one canonical type>
  secondary_types: [<optional supporting types>]
  confidence: high | medium | low
  evidence: [title/tags/description/transcript/frame/chapter cues]
  selected_strategy: references/video-type-summary-strategies.md#<section>
  fallback_reason: <only when mixed_or_unknown or low confidence>
```

Do not force a category. If the video mixes formats or the evidence is thin, use `mixed_or_unknown` and combine only the strategies that the evidence supports.

## Classification Inputs

Use the smallest sufficient evidence set:

- Title, URL/BV, creator/UP, tags, description, official chapters, playlist part titles.
- Transcript opening, repeated section markers, recurring nouns/verbs, explicit calls to action.
- Sampled frames: charts, talking-head interview, product closeups, gameplay/film clips, travel scenes, editing timeline, AI-generation screenshots.
- Audio style when useful: interview dialogue, narration, music-driven montage, tutorial screen narration, news briefing tone.
- the user's stated goal. If the user says “学习创作者怎么做”, favor creator-learning strategy even when the video also contains knowledge or entertainment content.

## Canonical Type Set

Use these canonical values exactly in manifests, QA notes, or validation scripts:

1. `finance_business_investment`
2. `knowledge_course_tutorial`
3. `politics_social_news`
4. `entertainment_film_variety_microdrama`
5. `ai_video_creation_creative_short_script`
6. `interview_podcast_dialogue`
7. `product_review_consumption_decision`
8. `vlog_life_travel`
9. `mixed_or_unknown`

## Strategy Matrix

### 1. `finance_business_investment`

**Core value:** decision understanding. the user should leave with concepts, argument logic, evidence quality, risk, and practical implications.

**Prioritize extracting:**

- Main thesis and investment/business question.
- Definitions: financial terms, business models, industry mechanisms, valuation logic.
- Assumptions behind the argument.
- Data points, charts, comparisons, unit economics, time horizon.
- Bull/base/bear cases when present.
- Risks, counterarguments, uncertainty, and what would falsify the claim.
- Actionable inspiration: what to watch, what to avoid, what to research next.

**Recommended output structure:**

1. `摘要` — question, main judgment, evidence strength, caveats.
2. `核心判断与适用边界`.
3. `概念解释 / 机制图解`.
4. `论点—证据—假设` table.
5. `风险与反例`.
6. `对 the user / Agent 的可行动启发`.
7. Timestamped chapters focused on argument turns, not equal time slices.

**Do not use:**

- Pure chronological recap unless the video is about a sequence of market events.
- Unsupported investment advice or “buy/sell” conclusions.
- Emotional hype copied from the creator without evidence grading.

**Agent-learning fields:** argument map, decision rule, data-source checklist, risk vocabulary, reusable explanation analogies.

### 2. `knowledge_course_tutorial`

**Core value:** learning transfer. the user should be able to understand the concept or reproduce the process.

**Prioritize extracting:**

- Learning objective and prerequisites.
- Concept hierarchy: definitions → mechanisms → examples → applications.
- Step-by-step procedure when it is a tutorial.
- Common mistakes, debugging signals, verification checks.
- Exercises, follow-up reading, reusable checklist.

**Recommended output structure:**

1. `摘要` — what this teaches, who it is for, what result it enables.
2. `学习路线` — prerequisite → concept map → output.
3. `核心概念` with plain-language definitions.
4. `步骤 / 方法` with verification signal.
5. `常见误区与修正`.
6. `可复用清单 / Agent 操作步骤`.
7. Chapters organized by learning dependency, not by dramatic tension.

**Do not use:**

- News-style stakeholder timeline when the value is conceptual.
- Long direct quotes unless wording is the teaching object.
- A vague “知识点总结” list without prerequisites or verification.

**Agent-learning fields:** concept map, operation checklist, failure-mode table, command/step placeholders, evaluation questions.

### 3. `politics_social_news`

**Core value:** situational awareness. the user should understand what happened, who is involved, what changed, what is disputed, and what may happen next.

**Prioritize extracting:**

- Verified event list and timeline.
- Key people, institutions, countries, companies, communities, or interest groups.
- Positions, incentives, public claims, and observable actions.
- What changed compared with the previous state.
- Disputed points, missing information, propaganda/rhetoric risk, and source caveats.
- Plausible future paths and impact on ordinary people.

**Recommended output structure:**

1. `摘要` — event, change, stakes, uncertainty.
2. `事件时间线`.
3. `关键人物 / 机构 / 利益相关方`.
4. `局势变化与争议点`.
5. `未来走向：情景 A/B/C`.
6. `对普通人的潜在影响`.
7. Chapters aligned to timeline turns or stakeholder shifts.

**Do not use:**

- Moralizing as the main structure.
- Treating creator opinion as verified fact.
- Collapsing disputed claims into one confident conclusion.

**Agent-learning fields:** actor map, timeline, claim-vs-evidence table, uncertainty ledger, scenario map.

### 4. `entertainment_film_variety_microdrama`

**Core value:** story and viewing experience. the user should understand why the video works emotionally and structurally, not just what happens.

**Prioritize extracting:**

- Premise, genre promise, audience expectation.
- Opening hook and first retention beat.
- Character/role relationships, desire, conflict, status shifts.
- Plot beats: setup, pressure, reversal, reveal, payoff, ending memory point.
- Scene-level evidence: shot choice, performance, editing rhythm, visual motif, sound cue.
- What the creator wants the audience to feel at each turn.

**Recommended output structure:**

1. `摘要` — story promise, emotional arc, strongest technique.
2. `故事结构` — hook → setup → escalation → turn → payoff.
3. `人物/关系/冲突`.
4. `关键场面拆解` with timestamp frames.
5. `视听手法` — camera, editing, sound, performance.
6. `可复用创作手法` — what an Agent can imitate abstractly.
7. Chapters built around narrative or emotional turns.

**Do not use:**

- Tutorial-style concept hierarchy.
- Pure plot recap without explaining technique.
- Copying fixed IP names, copyrighted scenes, or exact jokes as reusable templates.

**Agent-learning fields:** beat map, role-function table, conflict/reversal pattern, emotional curve, scene-technique mapping, reusable hook/payoff pattern. When the user wants to learn creator craft, also apply the `Creator-Learning Extraction Sheet` below so entertainment analysis does not collapse into plot recap.

### 5. `ai_video_creation_creative_short_script`

**Core value:** creator learning and production transfer. This is the priority path when the video itself teaches or demonstrates AI video creation, creative short videos, viral scripts, prompt design, editing, or visual storytelling.

**Prioritize extracting:**

- Topic/selling point: what promise makes the video worth watching.
- Target viewer and platform context.
- Opening hook: first 3–8 seconds, visual promise, contradiction, question, or high-stakes image.
- Content outline: sections and each section's job.
- Script structure: voiceover, dialogue, visual beats, CTA or ending memory point.
- Story conflict, reversal, escalation, reveal, payoff.
- Shot and visual language: shot size, composition, camera movement, VFX/physical change, frame evidence.
- Scene blocking: location, foreground/midground/background, props, spatial relationship, action path.
- Character/role design: identity anchors, silhouette, desire/fear, relation tension, performance cues.
- Rhythm and editing: cut density, pattern interrupts, montage, hold, speed ramp, repetition, contrast.
- Sound design: diegetic sound, voiceover, music/BGM placement, silence, impact cues, sound-image synchronization.
- Emotional curve: curiosity → tension → surprise → satisfaction → memory point.
- Reusable script template and prompt-language migration.

**Recommended output structure:**

For summaries delivered under the current Wiki category `视频制作分析`, target **8,000–12,000 Chinese characters** in the reader-facing analysis body, excluding metadata, raw transcript, local agent report, and validation logs. Use the extra length for concrete craft evidence, timestamped chapter reasoning, diagrams, frame observations, reusable production methods, and prompt-transfer language; do not pad with generic praise or duplicate recap.

1. `摘要` — what creative problem this video solves and what technique is most transferable.
2. `创作定位` — topic, selling point, target viewer, platform/format assumption.
3. `开头钩子拆解` — first-frame promise, first line/question, visual contradiction, retention job.
4. `内容大纲 / 台本结构` — beat-by-beat map with each beat's purpose.
5. `剧情与反转机制` — conflict, pressure, reveal, payoff.
6. `镜头与画面表现` — frame evidence, shot size, composition, camera, VFX/physical path.
7. `场景调度与角色设计` — scene container, blocking, props, character anchors.
8. `节奏、剪辑与声音设计` — pacing, transitions, pattern interrupts, voice/music/sfx.
9. `情绪曲线` — audience emotion by segment.
10. `可复用脚本模板` — abstract placeholders, not copied content.
11. `可迁移到 AI 视频提示词的表达方式` — prompt vocabulary and shot grammar.
12. `Agent 复用建议` — how to brief `story_shot_planner`, `video-prompt-writer`, or a future production agent.

**Do not use:**

- A generic content summary that only says “讲了如何做视频”.
- Treating the creator's finished example as something to copy scene-for-scene.
- Flattening production craft into “画面精美、节奏紧凑” without evidence.
- Mixing post-production BGM/subtitle planning into AI-video generation prompts without separating track ownership.

**Agent-learning fields:** creator promise, hook formula, beat map, shot grammar, visual motif, sound cue library, emotion curve, script template, prompt-transfer vocabulary, one-variable retry insight.

#### Creator-Learning Extraction Sheet

Use this sheet for entertainment and AI-video-creation videos when the user wants Agent learning:

```yaml
creator_learning:
  topic_and_selling_point:
    subject:
    target_viewer:
    promise:
    novelty_or_contrast:
  opening_hook:
    first_3_8_seconds:
    first_visual:
    first_line_or_question:
    stakes_or_curiosity_gap:
  outline_and_script:
    beats:
      - timestamp:
        function: hook | setup | pressure | turn | reveal | payoff | CTA | memory_point
        audio_or_text:
        visual_action:
        viewer_question:
  story_engine:
    conflict:
    reversal:
    escalation:
    payoff:
  visuals_and_shots:
    shot_sizes:
    camera_motion:
    composition:
    vfx_or_physical_change:
    frame_evidence:
  scene_blocking:
    scene_container:
    foreground_midground_background:
    props_and_materials:
    subject_movement:
  characters_or_roles:
    identity_anchors:
    desire_or_goal:
    fear_or_obstacle:
    relationship_tension:
  pacing_editing_sound:
    cut_rhythm:
    pattern_interrupts:
    transitions:
    diegetic_sound:
    voiceover_or_dialogue:
    music_or_silence:
  emotion_curve:
    start:
    middle:
    peak:
    ending_aftertaste:
  reusable_template:
    script_template:
    prompt_transfer_language:
    do_not_copy:
```

#### Reusable Script Template Pattern

Keep templates abstract and reusable:

```text
[Hook image/question]：用一个反常识画面或高张力问题让观众立刻知道“为什么要看”。
[Setup]：用一句话建立人物/场景/任务/规则，不讲背景百科。
[Pressure]：让目标遇到一个可见阻碍，最好能被镜头、动作或声音证明。
[Turn]：加入反转、误会解除、能力暴露、规则变化或代价出现。
[Payoff]：让开头承诺得到兑现，形成清晰结果或情绪释放。
[Memory point]：用最后一帧、金句、声音静默、视觉残留或反差画面留下可复述记忆点。
```

#### Prompt-Transfer Language

When converting creator learning into AI-video prompt language, extract phrases at this level:

- **Subject:** visible identity, silhouette, wardrobe/material, relation to other subjects.
- **Scene container:** location, time/weather, foreground/midground/background, props, light, atmosphere.
- **Action chain:** start posture → movement → contact point → result → aftermath.
- **Camera:** shot size, angle, composition, movement, focus path, cut/hold rhythm.
- **VFX/physical effect:** source → path → contact → material response → residue.
- **Sound:** environment sound, body/prop sound, impact cue, silence, voiceover/dialogue ownership.
- **Emotion:** visible evidence, not labels; gaze, breath, hesitation, distance, posture, reaction.
- **Ending frame:** final posture, object state, environment residue, emotional aftertaste.

### 6. `interview_podcast_dialogue`

**Core value:** perspective extraction. the user should understand who said what, where they agree/disagree, and which ideas are worth reusing.

**Prioritize extracting:**

- Speaker map and roles.
- Main questions and answer arcs.
- Each speaker's thesis, evidence, anecdotes, and assumptions.
- Agreement, disagreement, tension, or unanswered questions.
- Quotes when wording matters.
- Practical ideas or creative methods that emerge from the conversation.

**Recommended output structure:**

1. `摘要` — conversation theme, most valuable insight, strongest disagreement or unresolved question.
2. `对谈地图` — speakers, positions, topic sequence.
3. `核心观点分说话人整理`.
4. `共识 / 分歧 / 未回答问题`.
5. `关键金句与上下文`.
6. `可复用启发`.
7. Chapters by topic turns rather than every speaker change.

**Do not use:**

- Single-author argument structure when multiple speakers shape the value.
- A mechanical transcript summary.
- Quote dumping without interpretation.

**Agent-learning fields:** question bank, viewpoint map, quote-with-context, reusable interview prompts, counterargument list.

### 7. `product_review_consumption_decision`

**Core value:** buying/usage decision. the user should understand whether the product or service is suitable, for whom, and under what constraints.

**Prioritize extracting:**

- Product/service identity, target user, price/plan, alternatives.
- Claims being tested and test method quality.
- Real usage scenarios, pros/cons, hidden costs, failure cases.
- Decision criteria and audience fit.
- Sponsor/affiliate/creator-bias risk when visible.

**Recommended output structure:**

1. `摘要` — suitable/not suitable for whom, biggest tradeoff.
2. `产品定位与目标用户`.
3. `测试方法与可信度`.
4. `优点 / 缺点 / 风险`.
5. `竞品或替代方案`.
6. `购买/使用决策树`.
7. `Agent 可复用评测维度`.

**Do not use:**

- Only listing specs.
- Repeating marketing claims without test evidence.
- Giving universal recommendations when the result depends on user profile.

**Agent-learning fields:** evaluation rubric, decision tree, test checklist, bias warning signals, comparison dimensions.

### 8. `vlog_life_travel`

**Core value:** lived experience, atmosphere, route, and creator style. the user should get both practical takeaways and emotional texture.

**Prioritize extracting:**

- Route, places, time, people, activities, costs/logistics when visible.
- Sensory details: light, weather, food, movement, crowd, sound, pacing.
- Emotional arc and creator persona.
- Travel/life tips, avoidable mistakes, memorable scenes.
- Filming/editing choices that create immersion.

**Recommended output structure:**

1. `摘要` — route/life theme, mood, strongest memory point.
2. `行程 / 场景地图`.
3. `体验亮点与踩坑`.
4. `实用信息` — transport, cost, timing, preparation when present.
5. `氛围与拍法` — shots, transitions, music/sound, pacing.
6. `可复用 VLOG 结构`.
7. Chapters by route or mood shift.

**Do not use:**

- Over-analytical business/argument structure.
- Removing personal texture and turning the video into dry logistics.
- Treating every scene as equally important.

**Agent-learning fields:** route map, sensory vocabulary, mood curve, transition pattern, vlog beat template.

### 9. `mixed_or_unknown`

**Core value:** graceful fallback. the user still gets useful structure without false precision.

Use this when:

- Evidence is too thin.
- Title/tags/transcript point to different types with no clear primary.
- The video intentionally combines formats, e.g. interview + product review + investment argument; VLOG + tutorial; AI short + creator commentary.

**Recommended output structure:**

1. `摘要` — what is clear, what is uncertain, why a mixed strategy was used; bold only a few key facts.
2. `按内容价值分区` — facts/events, concepts, creator technique, decisions, story, practical notes as applicable.
3. `章节目录` — natural semantic turns.
4. `章节详解` — every chapter uses `本节总览 → 关键内容与细节 → 阶段小结` before diagrams/frames.
5. `可复用启发` — separated by strategy source.
6. `待确认问题` — only when it affects interpretation.

Keep primary candidates and evidence in the `video_type_decision` artifact or agent report; do not add a reader-facing `类型判定` section to the Feishu document body.

**Do not use:**

- Forcing a confident category for a weak signal.
- Applying every type's full template and bloating the document.
- Hiding uncertainty from the user.

**Agent-learning fields:** strategy blend manifest, confidence notes, missing-evidence list, next-question suggestions.

## Type-Specific Diagram Choices

Choose diagrams by type and chapter content:

| Type | Strong diagram patterns |
|---|---|
| `finance_business_investment` | thesis-evidence-assumption map, risk matrix, scenario tree, causal chain |
| `knowledge_course_tutorial` | concept hierarchy, workflow, troubleshooting decision tree, checklist |
| `politics_social_news` | timeline, stakeholder map, claim-vs-evidence table, scenario map |
| `entertainment_film_variety_microdrama` | story beat arc, character relationship map, conflict/reversal chain, emotion curve |
| `ai_video_creation_creative_short_script` | hook-to-payoff beat map, shot grammar table, prompt-transfer pipeline, emotion/pacing curve |
| `interview_podcast_dialogue` | speaker-topic map, agreement/disagreement matrix, question arc |
| `product_review_consumption_decision` | decision tree, pros/cons matrix, test-method map, user-fit matrix |
| `vlog_life_travel` | route map, scene/mood timeline, sensory map, logistics checklist |
| `mixed_or_unknown` | strategy blend map, evidence-confidence table, section-by-value map |

## Chapter Focus Rules

- Finance/business chapters should turn on argument or evidence changes.
- Knowledge/tutorial chapters should turn on learning dependencies or operations.
- News/social chapters should turn on timeline or stakeholder changes.
- Entertainment chapters should turn on story, conflict, emotional, or technique shifts.
- AI creative chapters should turn on creator technique: hook, beat, shot, edit, sound, prompt language, or reusable template.
- Interview chapters should turn on topic/question shifts.
- Product review chapters should turn on test scenario or decision criterion.
- VLOG chapters should turn on route, scene, mood, or experience changes.
- Mixed chapters should name the value of the section explicitly.

## Minimal Strategy Loading

Do not paste the full matrix into the final Feishu page. Use it to design the output. In the delivered document, show only the type-specific sections that help the user read and reuse the video.

## Smoke Samples

Use these routing examples when checking the assistant’s decision; they are examples, not a bundled automatic classifier:

1. Finance/knowledge hybrid → `finance_business_investment` with knowledge secondary.
2. Social/news event → `politics_social_news`.
3. AI-video creator breakdown → `ai_video_creation_creative_short_script`.
4. Mixed interview/product/business creator format → `mixed_or_unknown`.

Check strategy coverage, type-specific structure, creator-learning fields, and mixed fallback against the actual transcript. The runtime validator checks evidence artifacts; it does not certify the assistant’s semantic classification.
