# Deterministic Frame Evidence

Use this reference for `video-summary` visual evidence selection. The default evidence path is local and deterministic: `ffmpeg`/`ffprobe` plus pixel statistics, with optional local `tesseract` OCR. Model-assisted visual understanding is handled separately in `visual-understanding-routing.md` after evidence exists.

## Decision

Frame evidence and visual interpretation are separate layers. This reference governs the reproducible evidence layer: which video frames are selected, inserted, and validated. assistant image inspection, local VLMs, or manual visual notes may help interpret selected frames later, but they do not choose the evidence frames and do not replace local QA.

Default frame evidence selection MUST use:

1. local media already downloaded for the run;
2. chapter time ranges from `doc/summary_assets.json`, `metadata/chapters.json`, or evenly spaced fallback windows;
3. `runtime/scripts/select_frame_evidence.py` to score candidate frames by local image statistics;
4. optional local `tesseract` OCR when available;
5. `frames/frame_evidence.json` as the source-of-truth QA manifest;
6. `runtime/scripts/validate_video_summary_run.py --require-frame-evidence` before reporting Feishu delivery complete.

Model-assisted visual review is optional only after deterministic evidence exists. If used, review small selected frame files rather than large contact sheets, and record it as supplemental visual understanding, not as the delivery gate. See `visual-understanding-routing.md`.

## Required Command

```bash
.venv/bin/python runtime/scripts/select_frame_evidence.py \
  --run-dir runs/<run-id> \
  --candidates-per-chapter 5 \
  --ocr auto \
  --output runs/<run-id>/frames/frame_evidence.json
```

When chapter metadata is not ready yet, either pass an explicit JSON file:

```bash
.venv/bin/python runtime/scripts/select_frame_evidence.py \
  --run-dir runs/<run-id> \
  --chapters runs/<run-id>/metadata/chapters.json
```

or let the script create even fallback windows using `--fallback-chapters`.

## Output Contract

`frames/frame_evidence.json` must include:

- `mode: deterministic_frame_evidence`;
- `remote_vision_used: false`;
- selected frame path per chapter;
- selected timestamp in seconds;
- local stats: dimensions, standard deviation, edge score, black ratio, white ratio, color spread, and blankish flag;
- optional local OCR character count and sample text;
- candidate scores and any extraction errors;
- contact sheet output path when generated.

Selected frame files are written under `frames/evidence/`. Contact sheets are for human skim and Feishu insertion planning only; they are not a remote-VLM gate.

## Acceptance Rules

A frame evidence run is acceptable when:

- `frame_evidence.json.ok` is `true`;
- every required chapter has a non-empty selected frame file;
- `remote_vision_used` is `false`;
- no selected frame is `blankish` by local pixel stats;
- final validation passes with `--require-frame-evidence`.

If local frame evidence fails, fix the media path, chapter timestamps, sample count, or selected video stream. Do not solve frame-selection failures by asking a VLM to pick or validate frames; use model assistance only after the deterministic manifest is valid.

## Relationship To Feishu Delivery

For UI/demo/operation videos, insert one selected frame per chapter after the native whiteboard diagram.

For commentary, film, animation, lecture, finance, or knowledge videos, insert frames only when they materially anchor the point. Even then, the selected frames should still come from the deterministic manifest.

Feishu captions should use:

```text
视频时间戳｜<visible evidence>｜MM:SS
```

Avoid the generic caption `截图` unless the frame is truly an interface screenshot.

## Non-Default Anti-Pattern

Do not use this as the default:

```text
make large contact sheet -> ask a VLM to choose or validate frames -> fall back to local scoring
```

That path is retired because it mixes evidence selection with visual interpretation. The current default is:

```text
chapter windows -> local candidate scoring -> selected frames -> frame_evidence.json -> validator
```
