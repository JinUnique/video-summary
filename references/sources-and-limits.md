# Sources and limits

## Bilibili

Use metadata/public streams before optional yt-dlp enrichment. The helper supports
a BV id, HTTPS video link, or b23.tv short link. Select a multipart video with its
explicit part index; the helper defaults to part 1, not an entire series. It requests
480p-or-lower evidence and public audio. Metadata, subtitle availability, and signed
stream manifests are local run artifacts. Never copy signed URLs into a summary or
version control. An optional extractor HTTP 412 does not invalidate sufficient
public API evidence. If the public API itself fails, stop or change the source;
do not loop extractors or silently use existing browser credentials.

## Douyin and other extractor-supported public videos

The skill can orchestrate yt-dlp with its `--ignore-config` option for public
metadata and media. Preserve source provenance, inspect public duration, extract
audio, and reuse the ASR/frame scripts. This is a best-effort manual assistant
workflow, not a promise that the Bilibili helper downloads every platform.
Douyin often requires fresh cookies even for public pages; stop and report that
condition. A browser fallback requires the user's explicit authorization and an
available supported browser tool; there is no bundled browser automation or
account binding. Do not assume that local browser playback grants extraction rights.

## Unsupported or conditional

- Paid/member-only/private/DRM videos are outside this public quick start.
- Live streams, deleted videos, region blocks and anti-bot challenges may fail.
- YouTube and other sites depend on extractor support and network access and
  were not exercised by this staging audit. Do not claim they were tested.
- Speechless slide videos need OCR or readable frame inspection. Tesseract and
  language packs are optional and are not bundled.
- Long videos take proportionally more disk, download and ASR time. CPU model
  speed varies. Native GPU setup is not included in the quick start.
- Assistant/model access is the user's own existing setup; Python scripts do not
  include a hosted LLM key or independently write an intelligent summary.
