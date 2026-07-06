# video-summary

`video-summary` is a repo-backed workflow for turning video links, especially
Bilibili videos, into verified long-form summaries with reproducible metadata,
transcript, frame-evidence, and optional Feishu/Lark delivery artifacts.

The repository contains:

- runnable Python scripts for preflight checks, ASR orchestration, deterministic
  frame selection, Feishu/Lark document rendering, and run validation;
- a reusable media skill under `skills/media/video-summary/`;
- reference notes that document the expected workflow and common pitfalls.

## Features

- Validates local prerequisites before a real run.
- Captures media and transcript quality evidence as JSON artifacts.
- Runs `faster-whisper` with coverage checks and a no-VAD fallback path.
- Selects deterministic video frames with local `ffmpeg`/`ffprobe` statistics.
- Renders summary assets to Feishu/Lark-compatible document XML.
- Validates completed run directories before delivery is treated as complete.

## Requirements

- Python 3.10 or newer.
- `ffmpeg` and `ffprobe` for media inspection and frame extraction.
- `yt-dlp` for optional enrichment or downloads.
- `tesseract` for optional local OCR during frame evidence selection.
- `lark-cli` only when using Feishu/Lark delivery.

For ASR, install the Python dependencies into a local virtual environment:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

The validation-only scripts use the Python standard library unless their command
line options request an external tool check.

## Configuration

Create a local config file from the template:

```bash
python3 scripts/video_summary_preflight.py --init
```

Then edit `.env` with your own Feishu/Lark workspace values:

```dotenv
VIDEO_SUMMARY_WIKI_SPACE_ID=<YOUR_FEISHU_OR_LARK_WIKI_SPACE_ID>
VIDEO_SUMMARY_FEISHU_GROUP_NAME=<OPTIONAL_SOURCE_CHAT_OR_GROUP_NAME>
```

Keep real IDs, tokens, cookies, browser profiles, and generated run artifacts out
of git. `.env.example` is safe to commit; `.env` and other local variants are
ignored.

## Preflight

Run preflight before spending time on ASR or delivery:

```bash
python3 scripts/video_summary_preflight.py \
  --entry terminal \
  --url '<VIDEO_URL_OR_BV>' \
  --delivery offline \
  --output runs/<run-id>/metadata/preflight_terminal.json
```

For Feishu/Lark delivery, provide a Wiki space id through `.env` or
`--wiki-space`, then enable the live read check:

```bash
python3 scripts/video_summary_preflight.py \
  --entry terminal \
  --url '<VIDEO_URL_OR_BV>' \
  --delivery feishu \
  --require-asr \
  --live-feishu-read \
  --output runs/<run-id>/metadata/preflight_feishu.json
```

## Run Workflow

A normal run directory is expected to contain stable subdirectories such as
`metadata/`, `media/`, `transcript/`, `frames/`, `doc/`, and, for Feishu/Lark
delivery, `feishu/`.

Transcribe a prepared run:

```bash
.venv/bin/python scripts/transcribe_faster_whisper.py \
  --run-dir runs/<run-id> \
  --language zh
```

Select deterministic frame evidence:

```bash
python3 scripts/select_frame_evidence.py \
  --run-dir runs/<run-id>
```

Render Feishu/Lark document XML from prepared summary assets:

```bash
python3 scripts/render_feishu_summary_doc.py \
  --assets runs/<run-id>/doc/summary_assets.json \
  --output runs/<run-id>/doc/feishu_summary.xml
```

Validate the completed run:

```bash
python3 scripts/validate_video_summary_run.py \
  --run-dir runs/<run-id> \
  --delivery offline \
  --require-frame-evidence
```

For Feishu/Lark delivery, use `--delivery feishu` and keep the generated
delivery and readback verification artifacts under `runs/<run-id>/feishu/`.

## Optional Skill Installation

If you use a local skill runtime compatible with this repository layout, install
the repo-backed skill from:

```bash
scripts/install_video_summary_skill.sh
```

The installer respects `HERMES_HOME` when it is set. Treat installed runtime
copies as generated local state, not source-of-truth project files.

## Safety

- Never commit cookies, tokens, API keys, browser session files, private Wiki
  identifiers, or local `.env` files.
- Keep raw video/audio and generated heavy media out of git unless a small,
  public fixture is intentionally added for tests.
- Prefer reproducible scripts and JSON artifacts over run-specific notes.
- Redact private URLs and workspace identifiers before sharing logs or examples.
