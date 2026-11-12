# Summary and Chapter Writing Rules

Use this reference when turning a transcript and media evidence into a readable video-summary document.

## Research Basis

The writing rules synthesize three practical content-design findings:

- Video summaries should give viewers short, thoughtful context: what the video is about, who/what matters, the overall flow, and visual features that affect understanding.
- Executive summaries should condense purpose, key findings, implications/recommendations, and caveats for busy readers.
- Scannable long-form content needs descriptive headings, summaries, bullets, and helpful visuals; headings should describe the topic or purpose, not merely label an internal section.

## Replace `一句话结论` With `摘要`

Do not open the document with `一句话结论`. It is too narrow for full-video analysis and often hides the real value.

Use `摘要` instead, and render it as a Feishu callout/highlight block for Feishu delivery. It should usually be 3–6 short paragraphs or bullet groups:

1. **对象** — this video is about what event, workflow, argument, story, product, person, or case.
2. **主线** — how the video develops: setup → conflict/question → evidence/process → conclusion.
3. **关键发现** — 3–5 findings that matter most after watching the whole video.
4. **判断/启发** — what the viewer should understand, do, avoid, or reassess.
5. **证据与限制** — note if analysis depends on ASR, low-resolution public stream, missing official subtitles, unclear visuals, or creator bias.

Good `摘要` is not a teaser. It should let the user decide whether to read the full notes, jump to a chapter, or ignore the video.

## Chapter Title Goal

A chapter title should answer one of these:

- “这一段发生了什么？”
- “这一段解释了什么机制？”
- “这一段证明了什么判断？”
- “这一段让局势/论点发生了什么变化？”
- “这一段教会了什么操作步骤？”

Avoid titles that only expose internal analysis tags, e.g.:

```text
C01｜开播热度与慕兰口径：真正目标不是九国盟
```

Prefer content-facing summaries:

```text
开场先借热度设问，把真正矛盾从九国盟转向慕兰
```

For a tutorial chapter:

```text
先确认环境和权限，避免后面下载到一半才失败
```

For a UI/demo chapter:

```text
在控制台完成密钥绑定，并用一次请求验证配置生效
```

For an argument/commentary chapter:

```text
作者用三处台词说明角色动机不是复仇，而是夺回叙事主动权
```

## Title Design Rules

- Use 12–28 Chinese characters when possible; longer is acceptable if clarity improves.
- Start with the content action or turning point, not `C01` / `阶段一` / `Part 1` in the public heading.
- Keep sequence numbers only in local filenames or optional hidden metadata. If visible numbering is needed, use small natural prefixes like `01 `, not code-like labels.
- Include the specific noun that helps the user scan: the tool, character, conflict, method, risk, or result.
- Avoid cleverness that sacrifices clarity.
- Avoid generic labels: `背景介绍`, `操作流程`, `问题分析`, `总结升华` unless they are immediately made specific.
- If a timestamp list is shown, each title should still make sense when read alone.

## Chapter Body Style

Write in plain, short sentences. Fit the video type:

### Tutorial / UI / workflow videos

Emphasize:

- the user problem;
- prerequisites and permissions;
- exact steps;
- common traps;
- verification signal;
- what to do if it fails.

### Commentary / film / animation / story analysis

Emphasize:

- narrative turn;
- character/object relationship;
- evidence from shots, lines, edits, or timing;
- misunderstanding the video corrects;
- the chapter’s conclusion and how it changes the whole interpretation.

### Lecture / knowledge videos

Emphasize:

- concept hierarchy;
- definitions in plain Chinese;
- examples;
- misconception;
- application or decision rule.

### News / market / report videos

Emphasize:

- event timeline;
- stakeholder positions;
- key data;
- uncertainty;
- practical implication.

## Timestamp and Quote Rules

- Every chapter needs a timestamp range and at least one jump-back timestamp.
- Use key quotes only when phrasing matters; do not quote filler or ASR noise.
- If ASR confidence is low or wording is uncertain, paraphrase and mark it as paraphrase instead of presenting it as a direct quote.
- Visual anchors should mention what appears on screen, not just “见截图”.

## Bad-to-Good Rewrite Patterns

| Weak pattern | Better pattern |
|---|---|
| `C02｜背景铺垫` | `前两分钟交代冲突来源：观众以为在看联盟，实际在看权力换手` |
| `阶段三：工具演示` | `用一次真实请求验证配置，避免只停在界面设置` |
| `问题分析` | `失败原因不是模型不行，而是输入被分成了互相冲突的三层目标` |
| `结论` | `最后把选择收束到成本、可复用性和风险三个判断标准` |

## Final Writing QA

Before delivery, scan the document using only headings and captions:

- Can the user understand the video’s main flow without reading every paragraph?
- Does `摘要` say more than a slogan?
- Does each chapter title communicate a plot/argument/process turn?
- Are timestamps useful jump points, not decorative labels?
- Do diagram captions explain the relationship shown?
- Do frame captions identify what is visible at that timestamp?
