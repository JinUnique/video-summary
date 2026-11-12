# Visual Understanding Routing

Use this reference when a `video-summary` run needs visual interpretation beyond deterministic frame evidence. The goal is to separate reproducible evidence from model-assisted understanding, so video summaries can be both auditable and visually rich.

## Layered Model

### 1. Evidence Layer — deterministic and mandatory when frames are required

The evidence layer chooses the frames that are allowed to appear in Feishu or in final QA artifacts.

Source of truth:

- downloaded run media;
- chapter time windows;
- `runtime/scripts/select_frame_evidence.py`;
- local `ffmpeg` / `ffprobe` extraction;
- local pixel statistics and optional local OCR;
- `frames/frame_evidence.json`.

This layer must stay reproducible. It should not depend on any remote VLM, current chat model, provider quota, or subjective interpretation. Keep `frame_evidence.json.remote_vision_used` as `false` to mean “frame selection did not depend on remote vision.”

### 2. Understanding Layer — assistant image inspection by default when useful

After deterministic frame evidence exists, use the assistant’s available image-inspection tool as the preferred visual-understanding helper when the video’s value depends on visual details that transcript/OCR cannot fully capture.

Good triggers:

- AIGC concept trailers, visual dossiers, character-card reveals, montage shorts, and music-driven pieces;
- UI/demo videos where hierarchy, screen state, or visual affordances matter;
- film/animation/short-drama analysis where blocking, composition, motif, or reveal timing carries meaning;
- ambiguous OCR where layout or iconography changes the interpretation;
- the user explicitly asks for deeper visual reading.

Default usage:

- send selected chapter frames, not large contact sheets;
- prefer 1–3 representative frames per call, or one focused frame if details matter;
- ask targeted questions tied to the chapter job, not generic “describe this image”;
- write model-assisted observations into a separate local artifact such as `frames/visual_understanding_notes.json` or the synthesis scratchpad;
- cite them in synthesis as visual interpretation, not as frame-selection proof.

Recommended question shape:

```text
Analyze this selected video frame for a video-summary run. Focus only on visible evidence relevant to chapter <title>: scene, text/OCR, character or UI state, composition, action, and what changed from the prior chapter. Do not infer facts not visible in the frame.
```

### 3. Fallback Layer — local OCR / local VLM / manual skim

Use local routes when assistant image inspection is unavailable, too costly for the current task, privacy-sensitive, or not needed.

Fallback order:

1. local OCR from `frames/frame_evidence.json` and contact-sheet skim;
2. local VLM on small individual frames when available and stable;
3. manual frame inspection by the agent from local files/contact sheets;
4. mark the missing visual interpretation as a caveat if it affects confidence.

Local VLM output is supplemental. Prefer it for rough scene confirmation, OCR cross-checks, or privacy-preserving analysis; avoid treating it as authoritative when it is shallow, unstable, or run on large batches.

## Non-Goals

Do not use visual-understanding tools to replace:

- media download validation;
- ASR/subtitle provenance;
- deterministic frame selection;
- Feishu readback verification;
- final artifact validation.

Do not make a remote or local VLM failure block delivery when local evidence and transcript are sufficient. Instead, record the limitation in the agent report or quality record.

## Artifact Contract

When model-assisted visual understanding is used, record at least:

```json
{
  "mode": "visual_understanding_notes",
  "provider_route": "assistant_image_tool | local_vlm | manual",
  "depends_on_frame_evidence": true,
  "frames": [
    {
      "frame": "frames/evidence/chapter_01_012.3s.jpg",
      "question": "...",
      "observations": ["visible evidence only"],
      "confidence": "high | medium | low",
      "caveats": []
    }
  ]
}
```

Keep secrets, signed media URLs, cookies, and unrelated screen contents out of visual prompts and artifacts.

## Acceptance Rules

A visual-understanding supplement is acceptable when:

- deterministic frame evidence already exists and passes local validation;
- the prompt is targeted to visible evidence and chapter goals;
- selected frames are small enough for reliable tool handling;
- observations are separated from hard metadata/transcript facts;
- fallback/caveats are recorded when the model route fails or produces weak output.

The final summary should read naturally: use visual observations to improve chapter explanation, creator-learning fields, shot language, and caveats; do not expose internal provider/debug details in the reader-facing Feishu document.
