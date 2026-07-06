# Contributing

Thanks for helping improve `video-summary`.

## Development Setup

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
python3 scripts/video_summary_preflight.py --init
```

Install system tools as needed for the workflow you are testing:

- `ffmpeg` and `ffprobe` for media validation and frame extraction.
- `yt-dlp` for optional public metadata enrichment or downloads.
- `tesseract` for optional OCR-assisted frame scoring.
- `lark-cli` for Feishu/Lark delivery checks.

## Before Opening a Change

- Keep secrets and private workspace identifiers out of commits.
- Prefer small changes with a clear validation path.
- Update README and `.env.example` when public commands or config variables
  change.
- Add or update tests when workflow behavior changes.
- Do not commit generated run directories, downloaded media, local config, or
  browser session files.

## Suggested Checks

Run the checks that match your change:

```bash
python3 -m unittest discover -s tests
python3 scripts/video_summary_preflight.py --entry terminal --delivery offline
python3 scripts/validate_video_type_strategies.py
```

For end-to-end run changes, also validate a sanitized run directory:

```bash
python3 scripts/validate_video_summary_run.py \
  --run-dir runs/<run-id> \
  --delivery offline \
  --require-frame-evidence
```

## Pull Request Notes

Describe:

- what changed;
- how it was validated;
- any known limitations or follow-up work;
- whether the change affects Feishu/Lark delivery, ASR, frame evidence, or
  public documentation.
