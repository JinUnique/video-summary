# Feishu Native Diagram Workflow

Use this reference when `video-summary` needs editable diagrams inside a Feishu Doc/Wiki document.

## Why Native Whiteboards

For Feishu delivery, prefer native editable whiteboards over inserted SVG/PNG diagrams because:

- the user can edit the diagram later in Feishu.
- The document remains a living knowledge artifact instead of a static screenshot bundle.
- Lark/Feishu can export/query the whiteboard as image or code for QA.

Use SVG/PNG only as a local/offline fallback or an intermediate source for `whiteboard-cli` conversion.

## Tool setup

Use the user's installed official lark-cli and current help. If the official
lark-doc/lark-whiteboard/lark-shared skills are installed, follow their relevant
guides. They are optional external documentation, not bundled dependencies.
Without them, use the official CLI docs/help and inspect the generated board
before writing. The examples below are upstream workflow references, not commands
validated by the offline installation exercise; adapt flags to the installed CLI.

## Per-Chapter Workflow

### 1. Decide the diagram semantic type

Choose from the chapter’s real content, not from a fixed template:

| Content pattern | Diagram route |
|---|---|
| Sequence, operation, workflow | Flow/path |
| Concept, roles, layers | Relation/layer diagram |
| Time evolution, version, story arc | Timeline/milestone |
| Comparison, alternatives | Matrix/comparison |
| Risk, mistakes, causes | Checklist/decision tree/fishbone |
| Quantitative trend or counts | Chart |
| Cause and effect | Causal chain |
| Loop, growth, reinforcement | Flywheel |

### 2. Insert a blank whiteboard block

When writing a Feishu Doc/Wiki document, place a blank whiteboard immediately after the chapter body and before the video frame evidence:

```xml
<whiteboard type="blank"></whiteboard>
```

Use `lark-cli docs +update` or `docs +create` through the `lark-doc` workflow. Capture the returned `board_token` / whiteboard block token from the command response.

### 3. Generate the source diagram

For each chapter, produce a small diagram spec with:

- chapter title and timestamp range;
- diagram intent in one sentence;
- nodes/entities from the chapter only;
- arrows/relationships/labels;
- constraints: no decorative shapes, no repeated template shells, no claims not supported by transcript/frame evidence.

Preferred source formats:

- Mermaid only for simple mind maps, sequence diagrams, class-like relations, pie charts, or Gantt-style diagrams where Mermaid is the native best fit.
- For polished Feishu chapter diagrams, especially process/path, comparison, timeline, fishbone, flywheel, pyramid, funnel, architecture/layer, and dense relation visuals, use the official whiteboard tools and their current guide.
- When the official whiteboard skill is installed, read its scene/layout guides; otherwise follow the current whiteboard CLI documentation. Generate and inspect a preview before writing to Feishu.
- `whiteboard-cli` DSL/OpenAPI is the preferred route for richer layouts such as matrix, fishbone, flywheel, layered architecture, milestone/timeline, or dense cheat-sheet style visuals.

Minimum visual bar for video chapter diagrams:

- one clear chart title inside the whiteboard;
- 2–4 semantic groups with consistent colors from the `lark-whiteboard` palette;
- outer light containers and inner white cards when grouping is needed;
- readable typography, usually no more than three font sizes;
- grey relationship lines/arrows with labels only where they add meaning;
- no generic repeated flowchart shell across chapters;
- no node text copied as long paragraphs.

If a diagram looks like plain text boxes connected by arrows and does not materially improve comprehension, redesign it through the `lark-whiteboard` DSL route before delivery.

### 4. Write into the whiteboard

Simple Mermaid example:

```bash
cat chapter_03.mmd | lark-cli whiteboard +update \
  --whiteboard-token <board_token> \
  --input_format mermaid \
  --source - \
  --overwrite --yes --as user
```

DSL/OpenAPI example:

```bash
npx -y @larksuite/whiteboard-cli@^0.2.10 -i chapter_03.json --to openapi --format json \
  | lark-cli whiteboard +update \
    --whiteboard-token <board_token> \
    --source - --input_format raw \
    --idempotent-token <10+char-run-id> \
    --overwrite --yes --as user
```

If updating an existing non-empty board, first dry-run with `--overwrite --dry-run`. If the output says nodes will be deleted, ask the user before overwriting unless this board was just created by the current run.

### 5. Verify no blank diagrams remain

After writing:

- `docs +fetch` the document and count whiteboard blocks.
- Use `lark-cli whiteboard +query --output_as code` to confirm each board contains chapter-specific source, not just a blank block.
- Generate or export at least representative PNG previews via `@larksuite/whiteboard-cli` / `whiteboard +query --output_as image` and inspect for text truncation, overlap, unreadable contrast, excessive whitespace, and empty shells.
- Feishu whiteboard PNG previews often render on a very large white canvas. Do not judge blankness by mean brightness alone; use file size, non-white pixel ratio, and non-white bounding box, plus code readback, to avoid false `blank` failures.
- Verify the diagram contains chapter-specific terms and visible relationships.
- Treat an empty whiteboard block, an unreadable preview, or a generic repeated template as failed delivery even if the document text was written successfully.

## Chapter Delivery Order

Keep this order for every chapter:

1. `正文` — timestamp, plain-language explanation, evidence, conclusion.
2. `图解` — native Feishu whiteboard, editable.
3. `视频时间戳` — real extracted video frame when required/useful.

The diagram explains structure; the frame proves what was on screen.

## QA Rules

- A diagram must answer “what does this chapter’s structure look like?”
- If two adjacent chapters produce nearly identical diagrams, merge, specialize, or change the visual type.
- If a chapter has no meaningful diagram candidate, write a short note in the run log and skip the diagram only when the user did not require one per chapter.
- Never invent diagram nodes to make the drawing look full.
- Keep labels short enough for Feishu rendering; long claims belong in the chapter body.

## Failure Fallbacks

1. Mermaid fails: simplify labels and syntax, retry once.
2. SVG route fails or has text overflow: switch to DSL/OpenAPI route instead of repeatedly patching SVG.
3. Whiteboard update fails due to auth/scope: finish text and frames locally, report the exact CLI error, and leave the diagram source files for retry.
4. Feishu native diagrams are unavailable: fall back to rendered image insertion and mark the document as non-editable-diagram fallback.
