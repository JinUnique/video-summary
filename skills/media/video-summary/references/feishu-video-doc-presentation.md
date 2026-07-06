# Feishu Video Summary Document Presentation Contract

Use this reference when `video-summary` writes the final Feishu Wiki/Doc page. This file controls what belongs in the reader-facing document versus what belongs in the agent's completion report.

When `doc/summary_assets.json` exists, generate and verify the initial reader-facing body with:

```bash
python3 scripts/render_feishu_summary_doc.py \
  --assets runs/<run-id>/doc/summary_assets.json \
  --output runs/<run-id>/doc/feishu_summary.xml

python3 scripts/validate_feishu_presentation_contract.py \
  --input runs/<run-id>/doc/feishu_summary.xml \
  --expected-chapters <chapter-count> \
  --expected-whiteboards <chapter-count+1>
```

Create the document with `lark-cli docs +create --api-version v2 --parent-token <CATEGORY_PARENT_NODE_TOKEN> --content @runs/<run-id>/doc/feishu_summary.xml`. Do not use generated Markdown for the final Feishu page unless the user explicitly asks for Markdown import.

## Scope Split

The Feishu document is the intelligent analysis summary body. It should read like a polished knowledge page for the user.

Keep these out of the document body:

- run QA / quality records;
- command logs;
- retry history;
- raw tool output;
- internal validation checklists;
- implementation caveats that do not help the reader understand the video.

Report quality records in the final agent message instead: metadata duration check, media drift, ASR coverage, Feishu readback, whiteboard/frame counts, and any abnormal condition.

## Top Structure

Use exactly one document title via `<title>...</title>`. Do not repeat the same title as an `h1`/`h2` at the top.

After `<title>`, write the top metadata as separate blockquotes so it scans cleanly:

```xml
<title>视频标题｜智能总结</title>
<blockquote><p>来源：<a href="VIDEO_URL">bilibili</a>｜UP：创作者</p></blockquote>
<blockquote><p>时长：20:55</p></blockquote>
<blockquote><p>标签：标签1、标签2、标签3</p></blockquote>
```

The source link text should be a compact platform/domain label such as `bilibili` or `youtube`; the `href` still points to the original video URL. Do not display the raw URL in the reader-facing metadata line.

Keep tags concise. If the platform has too many noisy tags, preserve them in local metadata JSON and show only useful tags in the document.

## Summary Block

The `摘要` section must use a high-visibility callout block, not plain paragraphs.

Recommended shape:

```xml
<h2>摘要</h2>
<callout emoji="💡" background-color="light-yellow" border-color="yellow">
  <p>第一段：视频对象和<b>主线关键词</b>。</p>
  <p>第二段：关键转折和<b>核心证据</b>。</p>
  <p>第三段：结论、启发或限制。</p>
</callout>
```

Bold only a small number of truly key facts, numbers, named concepts, or titles. Do not bold whole paragraphs or use bold as decoration.

Choose emoji and color semantically:

- `💡 light-yellow` for analytical summaries;
- `📌 light-blue` for neutral briefing;
- `⚠️ light-red` only when the video itself contains risks or the analysis is uncertain.

## Chapter Heading and Metadata

Chapter headings remain timestamped and content-facing:

```xml
<h2>00:00–02:15｜买下整座超市后，规则把自由压缩成一条红线</h2>
```

Immediately after every chapter heading, use a blockquote with exactly these three fixed labels:

```xml
<blockquote>
  <p>原片时间点：<a href="VIDEO_URL?t=0">00:00</a></p>
  <p>本节聚焦：这一节回答的核心问题或判断。</p>
  <p>细节澄清：容易误读、前提边界、ASR/画面不确定性，或本节需要先说明的上下文。</p>
</blockquote>
```

Rules:

- The three labels are fixed: `原片时间点`、`本节聚焦`、`细节澄清`.
- `原片时间点` must be a jump-back link when the platform supports it.
- `本节聚焦` should be a question or sharp statement, not a generic category.
- `细节澄清` should remove ambiguity; if there is no special caveat, state the most important reading boundary.
- Do not fall back to loose `可回跳 / 这一章的问题 / 容易误读` paragraphs in the final document.

## Per-Chapter Body Order

For each chapter, use this reader-facing total-detail-total order:

1. Metadata quote block.
2. `本节总览` — one short paragraph stating what this segment contributes.
3. `关键内容与细节` — bullets or compact paragraphs with concrete events, facts, steps, or evidence.
4. `阶段小结` — one short paragraph explaining the segment's implication or transition value.
5. `图解｜...` native whiteboard.
6. `视频时间戳｜...` real frame when useful/required.

Do not insert quality notes inside chapter bodies unless they change how the chapter should be read.

## Captions

Use labels that make the two visual types instantly distinguishable:

- Diagram caption heading: `图解｜<relationship/process/timeline described>`.
- Frame caption: `视频时间戳｜<visible evidence>｜MM:SS`.

Avoid generic captions like `截图` or `图 1`.

## Final Report Separation

After the document is delivered, the agent report should include a compact `质量记录` section outside the Feishu document, for example:

```text
质量记录：
- 元数据/音视频时长误差：0.01%，低于 5% 阈值。
- ASR 覆盖：末段 20:54，覆盖正常。
- 飞书回读：8 章、8 个画板、8 张视频时间戳帧均命中。
- 异常：无官方字幕，章节基于本地转写语义切分。
```

This is a completion-report artifact, not document content.
