# Bilibili Public-API-First Ingest

This reference defines the Bilibili ingest architecture for `video-summary`. It is intentionally higher-level than one run's workaround: for default public Bilibili summaries, the public API baseline is the first-class ingest source, and `yt-dlp` is a bounded enrichment/downloader helper.

## Core Principle

For Bilibili default/public runs, do **not** start by treating `yt-dlp` page extraction as the authority.

Use this priority order:

1. **Public API baseline** — required first for public/default Bilibili runs.
2. **Stream adequacy check** — decide whether public streams satisfy the requested deliverable.
3. **Bounded `yt-dlp` enrichment probe** — optional and non-blocking when extractor-only fields add value.
4. **Escalation** — local cookies/high-quality/auth routes only when the public path cannot meet the request.

This makes Bilibili's public API the stable baseline rather than a fallback after `yt-dlp` fails.

## Source Roles

| Layer | Role | Default? | Blocking? | Typical outputs |
|---|---|---:|---:|---|
| Public API baseline | Canonical public metadata and public stream discovery | Yes | Yes for Bilibili default runs | `metadata/view.json`, `metadata/tags.json`, `metadata/playurl.json`, `metadata/ingest_decision.json` |
| `yt-dlp` enrichment probe | Extra extractor-only data: chapters, subtitles, playlists, format labels, webpage-derived hints | Optional | No, unless the user asked for a field only it can supply | `metadata/yt_dlp_enrichment.json` or `logs/yt_dlp_412.stderr` |
| Media acquisition helper | Download selected streams after the source decision | Conditional | Only after public path is insufficient or selected | media files + `metadata/media_validation.json` |
| Cookie/auth escalation | Higher quality, private/VIP, gated subtitles/AI summary, or public stream failure | Explicitly gated | Yes only after the user authorizes local cookie path | redacted local run artifacts |

## Required Public API Baseline

For Bilibili public/default runs, collect and preserve these before any `yt-dlp` probe:

- `x/web-interface/view` — title, owner/UP, cover, description, duration, pages, aid/cid/bvid, stats.
- tags endpoint — tags/categories useful for type routing.
- player/playurl endpoints — public video/audio stream candidates and stream adequacy.

Minimum artifact expectation:

```text
runs/<run-id>/metadata/view.json
runs/<run-id>/metadata/tags.json
runs/<run-id>/metadata/playurl.json        # or equivalent selected stream manifest; local-only when signed URLs are present
runs/<run-id>/metadata/ingest_decision.json
```

`playurl.json` and equivalent stream manifests may contain time-limited signed URLs. Keep them in local ignored run artifacts, redact them in reports, and never copy raw signed URLs into Feishu, memory, committed docs, or chat.

`ingest_decision.json` should record:

- `source_order`: `public_api_baseline -> stream_adequacy -> optional_yt_dlp_enrichment -> escalation_if_needed`
- whether public streams were sufficient for the requested quality;
- whether `yt-dlp` was run, skipped, or failed with a known status such as HTTP 412;
- whether cookies were not needed, requested, or explicitly authorized.

## Stream Adequacy Rule

Default deliverable target:

- evidence video: 480p-or-lower is enough unless the user asks for higher quality;
- audio: best public audio available, converted to 16k mono WAV when useful for ASR;
- validation: `ffprobe` drift under 5% unless explicitly marked abnormal.

If public API/playurl returns adequate 480p evidence video and best audio, proceed without blocking on `yt-dlp` page extraction.

If `yt-dlp` is later used as a downloader helper, keep the same quality policy:

```text
video: bestvideo[height<=480]/best[height<=480]/best
 audio: bestaudio/best
```

The selector is a fallback/helper policy, not the ingest baseline.

## Bounded `yt-dlp` Enrichment Probe

Run `yt-dlp --dump-single-json` at most once in the default path, and only as enrichment when it can add one of:

- official or extractor-discovered subtitles;
- chapter markers or playlist/part structure not already available;
- cleaner format labels or webpage metadata useful for provenance;
- non-Bilibili generic video extraction when the platform API path does not apply.

If the probe returns Bilibili `HTTP Error 412: Precondition Failed`:

1. save stderr once;
2. classify it as webpage extraction/risk-control/gating, not as media failure;
3. continue from the public API baseline if the baseline and streams are sufficient;
4. ask for cookies only if the public path cannot meet the requested deliverable.

Never retry the same `yt-dlp` page extraction loop without a changed condition such as authorized cookies, headers, requested quality, or a different platform.

## Escalation Decision

Ask the user for a local Netscape `cookies.txt` path only when one of these is true:

- public API/playurl cannot obtain a complete audio/video pair for the default deliverable;
- the user explicitly requests 720p/1080p/highest quality;
- official subtitles, official AI summary, VIP/private content, or gated fields are required and public endpoints cannot provide them;
- media validation fails and public retries do not fix it.

Do not ask the user to paste cookies or tokens into chat. Do not store cookie contents in repo, Feishu, logs, memory, or skill notes.

## Failure and Fallback Language

Use these summaries in reports:

- **Public baseline OK, enrichment failed:** “公开视频 API baseline 已满足默认交付；`yt-dlp` enrichment 命中 412，已记录并跳过，不阻塞。”
- **Public streams insufficient:** “公开视频 API 元数据可用，但公开视频流不足以满足交付；需要用户授权本地 cookies.txt 或降低质量目标。”
- **Both public metadata and streams unavailable:** “Bilibili public baseline 不可用，停止在写回前；需要更换来源、稍后重试或授权本地凭据。”

## Anti-Patterns

- Starting default Bilibili runs with `yt-dlp --dump-single-json` as the primary gate.
- Treating `yt-dlp` HTTP 412 as proof the public API path cannot work.
- Asking for cookies before proving the public API baseline/streams are insufficient.
- Letting enrichment output overwrite public API baseline artifacts.
- Hiding source provenance by mixing public API fields and extractor fields into one unlabelled JSON blob.
