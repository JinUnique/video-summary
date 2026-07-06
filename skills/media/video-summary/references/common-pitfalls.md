# Video Summary Common Pitfalls

Use this reference when the root `SKILL.md` flags a pitfall category but the run needs the full operational detail.

## Scope and Paths

1. **Treating `scripts/*.py` as skill-package files.** Every `scripts/...` path in the video-summary skill is repo-root-relative to `<REPO_ROOT>`. The skill package under `skills/media/video-summary/` intentionally contains only `SKILL.md` and support files such as `references/`; do not report missing `skills/media/video-summary/scripts/*.py` as cleanup drift.
2. **Hard-coding proxy ports or local paths.** Inspect the current environment and keep run-specific paths in artifacts, not the skill.

## Ingest and Credentials

3. **Letting `yt-dlp` define the Bilibili ingest model.** For default/public Bilibili runs, collect the public API baseline and write `metadata/ingest_decision.json` before any extractor probe. `yt-dlp` is an enrichment/downloader helper, not the baseline authority.
4. **Asking for cookies too early.** Try public metadata/default 480p first unless the user explicitly asks for higher quality.
5. **Letting a known Bilibili 412 burn a full step.** For default public 480p runs, public APIs should establish the baseline first; `yt-dlp --dump-single-json` is an enrichment probe. If it returns 412, do not retry the same page extraction unless headers/cookies/quality requirements changed.
6. **Logging secrets.** Redact cookies, signed stream URLs, tokens, and auth material from logs and documents.

## Entry, Queue, and Controller Boundaries

7. **Skipping entry preflight.** Terminal and Feishu entries differ in cwd, task-source trust, lane binding, and Wiki target. Run `scripts/video_summary_preflight.py` first from `<REPO_ROOT>` and save the JSON artifact.
8. **Downgrading a Feishu-lane video summary into a chat-only answer.** In the bound `video-summary` Feishu lane, a direct Bilibili/video link plus `总结` means the full Feishu Wiki delivery contract by default: preflight, public ingest, ASR/coverage checks when needed, type-specific summary assets, deterministic frames, Feishu document creation, media/whiteboard writeback, readback, and final validation. Only provide a chat-only summary when the user explicitly asks for a quick/casual answer or says not to create a document. If you already produced only chat text, treat it as incomplete and immediately finish the document workflow rather than defending the shortcut.
9. **Letting child agents mutate the source queue.** For Feishu/Wiki documents containing multiple video links, the main controller must stay as controller: child agents process exactly one link and return evidence only; the controller verifies final validation and Feishu readback, then deletes the exact source link/block and readbacks the source document. See `references/serial-queue-supervision.md`.
10. **Conflating audit with repair.** When the user asks for an audit of a completed video-summary run, first deliver the evidence-based audit conclusion and responsibility split. If a skill/process gap is found, say it explicitly and then patch the skill; do not silently start repairing before answering the audit question.

## Feishu and Wiki Writeback

11. **Confusing Feishu Wiki space ID with node token.** `/wiki/space/<id>` is a space ID; create a child document under the selected category parent node token after runtime category discovery.
12. **Treating SVG as final Feishu diagram.** For Feishu delivery, use native whiteboards by default; SVG is only a local/offline fallback or intermediate route when whiteboard tooling requires it.
13. **Feishu top-block repair loops.** If `lark-cli docs` creates duplicate top titles, merges metadata into an ugly quote block, or turns the summary callout into plain quotes, do not spend many cycles forcing local block edits after repeated no-op responses. Render clean XML with `scripts/render_feishu_summary_doc.py`, create a replacement document with no duplicate H1, separate metadata blockquotes, and an `摘要` callout, then verify and deliver the clean URL.
14. **Assuming loaded Feishu skill examples match the live CLI.** `lark-cli` evolves. Before creating/updating a Feishu video-summary page, check `lark-cli docs +create --help`, `docs +update --help`, `docs +media-insert --help`, and `docs +whiteboard-update --help`; if help differs from a reference, use live help and record the run-specific command shape.
15. **Using absolute paths for Feishu media insert.** Current `docs +media-insert --file` rejects absolute paths; `cd` into the image directory and pass `./filename`.
16. **Deleting anchor placeholders with legacy update flags.** Current update shortcuts use `--command`; remove anchors with `docs +update --command str_replace --pattern <anchor> --content ""` or exact `block_delete`, not legacy `--mode delete_range` / empty Markdown replacement examples.

## Writing, Type Strategy, and Presentation

17. **Writing a weak `一句话结论`.** Use `摘要` with object, flow, key findings, implications, and confidence/caveats.
18. **Using cryptic chapter labels.** Headings must be scannable and meaningful without reading the body.
19. **Using one template for every video.** Always select a video type before writing; finance, news, tutorial, interview, product, VLOG, entertainment, and AI-creation videos need different value extraction.
20. **Over-classifying mixed videos.** If evidence is thin or multiple formats are equally important, use `mixed_or_unknown` and a compact strategy blend instead of pretending certainty.
21. **Flattening creator-learning videos.** For entertainment or AI-video-creation content, do not stop at plot recap. Extract hook, beat structure, shot grammar, scene blocking, pacing, sound, emotion curve, reusable script template, and prompt-transfer language.
22. **Leaking internal ASR/QA terms into the reader-facing Feishu page.** The presentation validator rejects terms like `ASR`, `QA`, `no-VAD`, `faster-whisper`, `preflight`, and `delivery_record` in the document body. Keep exact transcript route details in local artifacts / final agent report; in the Feishu page use reader-safe wording such as `自动分段转写` or `完整转写结果` only when it helps the reader understand caveats.

## ASR, Frames, and Validation

23. **Blocking on CUDA.** CPU int8 is acceptable for slower but reliable transcription.
24. **Writing run-specific ASR scripts.** Do not hard-code one BV/run path or one guessed audio filename. Use `scripts/transcribe_faster_whisper.py` so audio discovery, CPU int8, coverage QA, and no-VAD fallback are consistent.
25. **Accepting early VAD cutoff as ASR success.** If VAD transcription ends early with >5% coverage drift or >8 seconds absolute drift, rerun no-VAD before accepting the run; accept no-VAD when it reaches the ending and drift is under both thresholds.
26. **Confusing frame evidence with visual interpretation.** Default to `scripts/select_frame_evidence.py` and local stats/OCR for frame selection. Use `vision_analyze` or local VLM only after deterministic evidence exists, and record it as interpretation notes rather than proof that the selected frames are valid.
27. **Blocking on large contact-sheet vision.** Large/tall contact sheets can time out or fail. Do not let that block delivery: produce deterministic `frames/frame_evidence.json` first, then retry on selected frames or the selected-frame contact sheet only as supplemental interpretation, recording any failed remote-vision attempt in `frames/visual_understanding_notes.json`.
28. **Leaving nulls in delivery QA.** If `media_validation.json` has drift data, aggregate it into `delivery_record.json`; final validation should fail on null quality fields.
