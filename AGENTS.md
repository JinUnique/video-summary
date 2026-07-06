# Agent and Contributor Operating Guide

This repository is intended to be public. Keep project instructions generic,
reproducible, and free of personal workspace bindings.

## Scope

- Use this repository for the `video-summary` workflow: video metadata capture,
  transcript QA, deterministic frame evidence, summary rendering, and delivery
  validation.
- Keep reusable logic in scripts or documented reference files. Do not encode
  one person's local path, private chat, private Wiki space, or machine-specific
  runtime state into source-controlled instructions.
- Treat `runs/`, downloaded media, generated frames, local config, and delivery
  logs as local artifacts unless a small sanitized fixture is intentionally
  added for tests.

## Local Configuration

- Store local settings in `.env` or environment variables.
- Use `.env.example` only for placeholder names and documented defaults.
- Do not commit real cookies, tokens, API keys, browser profiles, private Wiki
  identifiers, or local account names.
- Prefer command-line overrides for one-off experiments instead of editing
  checked-in defaults.

## Workflow Rules

- Run `python3 scripts/video_summary_preflight.py --init` before first use to
  create a local `.env` from `.env.example`.
- Run `scripts/video_summary_preflight.py` before non-trivial ASR, frame
  extraction, or delivery work. Save JSON reports under the relevant run
  directory.
- For Bilibili/default ingestion, preserve the public metadata baseline before
  using download or enrichment helpers.
- Use `scripts/transcribe_faster_whisper.py` for ASR so transcript coverage
  checks and fallback behavior stay consistent.
- Use `scripts/select_frame_evidence.py` before any model-assisted visual
  interpretation so selected frames remain reproducible.
- Validate completed runs with `scripts/validate_video_summary_run.py` before
  treating a result as deliverable.

## Editing Rules

- Keep changes focused on the requested behavior or documentation.
- Avoid unrelated refactors, generated artifact churn, and edits to private
  local state.
- Update README/config examples when a public entry point or required
  environment variable changes.
- Add tests or validation commands when changing shared workflow behavior.
- Do not relax secret-ignore rules in `.gitignore`.

## Public Release Hygiene

- Search changed files for personal names, private URLs, private space IDs,
  tokens, cookies, and absolute local paths before handing off work.
- Use placeholders such as `<YOUR_FEISHU_OR_LARK_WIKI_SPACE_ID>` in examples.
- Prefer relative paths from the repository root in public documentation.
