# Bilibili → Faster-Whisper → Feishu Wiki Run Findings

Condensed from a completed Bilibili smart-summary delivery session. Keep this as implementation detail; the main skill stays class-level.

## Bilibili Ingest

Normative source-role rules now live in `bilibili-public-api-first-ingest.md`. This section is historical run evidence and implementation detail, not the full architecture.

- `yt-dlp` page extraction may hit Bilibili `HTTP Error 412: Precondition Failed` even for a public video.
- For default public/480p deliveries, public API normalization is the stable first baseline. Run `yt-dlp --dump-single-json` only once as a bounded enrichment probe unless cookies, high quality, playlist fields, subtitles, or extractor-only chapters require it.
- Do not stop at that failure. Public Bilibili APIs can still provide enough data for a deliverable:
  - `x/web-interface/view` for title, owner/UP, cover, description, duration, tags, aid/cid-like metadata.
  - playurl/player endpoints can expose audio and 720P video streams without cookies for some public videos.
- Cookies should be requested only when public paths cannot obtain required streams, high-quality screenshots, or full metadata.
- If cookies are needed, ask for a local Netscape `cookies.txt` file path, not pasted cookie contents.
- A 412 log alone does not prove the exact server-side cause. Treat it as likely Bilibili webpage precondition/risk-control/header-cookie/WBI gating, and record only the observed status unless response bodies or official diagnostics prove more.

## Media QA

- Download best available audio and verify with `ffprobe`.
- Compare `ffprobe` audio duration to platform metadata duration. If drift is over 5%, retry download or mark the run abnormal.
- Keep a JSON status file with metadata duration, probed duration, percent drift, and selected stream URLs redacted where needed.

## Transcription

- Official subtitle APIs can return empty even when chapters exist.
- Bilibili chapter markers are still useful as natural segmentation anchors.
- For Chinese ASR, `faster-whisper` model alias `large-v3-turbo` / `turbo` maps to `mobiuslabsgmbh/faster-whisper-large-v3-turbo` in faster-whisper workflows.
- If CUDA libraries are unavailable, switch to `device="cpu", compute_type="int8"` instead of blocking the run.
- Validate transcript coverage by comparing the final segment end time with audio duration; small tail overrun/underrun under 5% can be accepted with a note.

## Visuals

- For chapter screenshots, run `scripts/select_frame_evidence.py` and use `frames/frame_evidence.json` as the source-of-truth manifest for selected timestamps and frame files.
- Do not make model review of contact sheets part of the frame-selection gate. First create deterministic frame evidence; then use `vision_analyze` or local fallback only for visual interpretation when it materially improves the summary.
- Deterministic checks are mandatory: image dimensions, file size, pixel variance/stddev, edge score, black/white ratio, and `blankish: false`. Local `tesseract` OCR can add a score bonus when available, but absence of OCR is not a blocker.
- For UI/demo videos, every chapter should include both:
  - a content-grounded diagram explaining relationships or process; and
  - a real extracted frame as evidence.

## Feishu Wiki/Doc Writeback

- A URL shaped like `/wiki/space/<id>` is a `space_id`, not a wiki node token.
- Select a top-level category parent before writeback: list the Wiki space's top-level nodes, infer their category profile from child summaries, render `doc/summary_assets.json` to XML, and create the summary under the selected parent with `docs +create --api-version v2 --parent-token <CATEGORY_PARENT_NODE_TOKEN> --content @runs/<run-id>/doc/feishu_summary.xml`. Use root-level creation only for intentional top-level category creation or when the user explicitly wants a root-level document.
- Insert content in stable order per chapter: text body, native whiteboard diagram, video timestamp frame.
- Read back after writing and verify:
  - expected chapter heading count;
  - expected image count;
  - presence of robust keyword groups;
  - final document URL.
- Prefer verification JSON artifacts such as `feishu_verify.json` and `feishu_fetch.json` so the handoff is auditable.

### lark-cli docs/create/update command shape

The reusable rule is: check live shortcut help and read the embedded `lark-doc` references before writeback. Current `docs +create` defaults to XML via `--content`, and current `docs +update` uses `--command`, not older `--mode ... --markdown ...` examples from memory.

Useful confirmed shapes:

- `docs +create --api-version v2 --parent-token <CATEGORY_PARENT_NODE_TOKEN> --content @runs/<run-id>/doc/feishu_summary.xml`
- `docs +update --api-version v2 --command str_replace --pattern "<anchor>" --content ""`
- `docs +media-insert --file ./frame.jpg` after `cd` into the image directory

Do not append `--format` to create/update shortcut dry-runs unless the exact shortcut help shows it. `wiki nodes list` supports `--format json`; create shortcuts may not.

For native whiteboards in current XML create flow, creating XML containing `<whiteboard type="blank"></whiteboard>` returns usable `document.new_blocks` in document order; then `lark-cli docs +whiteboard-update --whiteboard-token ... --source @diagram.mmd --input_format mermaid --overwrite --idempotent-token ...` populates each board.

### Feishu create/writeback presentation quirks

- Creating a generated summary through the old Markdown import path can leave the title duplicated in the body as an H1, collapse consecutive metadata blockquotes, and turn the `摘要` callout into weak plain text. For reader-facing video summaries, render XML with `scripts/render_feishu_summary_doc.py` and validate with `scripts/validate_feishu_presentation_contract.py`.
- Some top-level blocks created during the initial import can become difficult to remove later. Avoid this by getting the top XML structure right before inserting whiteboards/images, because rebuilding after media insertion risks losing ordered resource blocks.
- For verification, do not treat Markdown fetch rendering of `<title>` as a duplicate H1. Use XML outline fetch: if the outline starts at `h2` and contains no `h1`, the document title is not duplicated structurally.
- Whiteboard image previews often export as large mostly-white 2560×2560 canvases. Treat file size plus pixel variance/non-white bounding box as a better non-blank signal than mean brightness alone.
- `validate_video_summary_run.py` may falsely flag quality-term leaks when live Feishu `fetch_result.json` contains generated resource tokens with substrings such as `QA`. Keep live readback verification for title/chapter/whiteboard/wiki checks, but pass `--presentation-input doc/feishu_summary.xml` for presentation-contract validation unless the validator has been updated to ignore XML attributes/tokens.

## the user Presentation Feedback — 2026-06-14

the user edited the delivered Feishu document and clarified the reusable presentation contract:

- Do not write `质量记录` into the Feishu document. The document is the reader-facing intelligent analysis summary; QA belongs in the agent completion report.
- Do not repeat the document title at the top. Use one `<title>` only, then metadata and summary.
- Top metadata should be separate blockquotes: `来源`、`时长`、`标签` each on its own line/block.
- `摘要` should be visually highlighted with a callout block.
- Each chapter should begin with a blockquote using fixed labels: `原片时间点`、`本节聚焦`、`细节澄清`.
- Diagram quality needs to be higher than plain Mermaid boxes. For polished Feishu diagrams, route through `lark-whiteboard` / `@larksuite/whiteboard-cli`, render preview PNGs, and follow its style/layout/typography/connector references.

## v0.2 Policy Updates

- Public API baseline is the Bilibili default ingest architecture. `yt-dlp` is an enrichment/downloader helper and should not be the first blocking gate for public/default runs.
- Default Bilibili video download target is 480p-or-lower for evidence frames. This avoids unnecessary cookie prompts and keeps runs lightweight. Escalate to cookies only when public streams fail or the user explicitly asks for 720p/1080p/highest quality.
- For Feishu Wiki/Doc delivery, prefer editable native Feishu whiteboards over inserted SVG/PNG diagrams. SVG is a local/offline fallback or an intermediate conversion route, not the default final artifact.
- Replace the old `一句话结论` opening with `摘要`: object, main flow, key findings, implications, and caveats.
- Public chapter headings should be narrative/content summaries, not internal codes. Keep `C01`-style identifiers in filenames or local manifests only.

