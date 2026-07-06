# Chat-Only Bilibili Summary Lightweight Path

Use this reference when the user sends a short Bilibili/b23.tv link and asks only for an in-chat summary, not a Feishu/Wiki smart-summary artifact.

## Trigger

- User asks `总结` / `总结这个视频` / `看下这个视频讲什么` with a Bilibili URL.
- No explicit request for Feishu document, screenshots, diagrams, full evidence package, or reusable archive.
- Video is short enough that a concise chat answer is the deliverable.

## Lightweight Workflow

1. Resolve `b23.tv` to the canonical `bilibili.com/video/BV...` URL.
2. Query public Bilibili metadata with `x/web-interface/view` and save or note: title, owner, duration, aid, cid, description, pages.
3. Check public subtitles via `x/player/v2?aid=<aid>&cid=<cid>`.
4. If public subtitles are empty, download only the public audio stream from `x/player/playurl` and transcribe locally with the repo `scripts/transcribe_faster_whisper.py` path when available.
5. Verify ASR coverage before summarizing: compare audio duration and final segment end; accept only when drift is inside the script gates or clearly mark caveats.
6. For tutorial/install videos, sample a few key frames around the instruction segment and use OCR/vision to verify terms that ASR may mishear, especially product-specific words such as `Skill`, `MCP`, `SSE`, `SDK`, `CLI`, `Scale`.
7. If the video displays a public install/readme URL, fetch it read-only to verify command names and feature claims. Do not install third-party skills/packages unless the user asks.
8. Reply in chat with: core conclusion, practical steps, caveats/judgment, and a brief verification note.

## Safety Notes

- Do not request or use Bilibili cookies for default chat summaries.
- Do not print signed media stream URLs; use them inside scripts only.
- Do not install or run third-party skill code while summarizing a video; reading public docs is enough for verification.
- Treat creator claims as promotional unless independently verified by docs or local tests.

## Output Shape

A compact response is preferred:

- `核心结论` — what the video is saying.
- `接入/操作要点` — only if the video includes a tutorial.
- `我的判断` — what is solid vs what needs testing.
- `验证说明` — subtitle/ASR/frame/doc checks, one short line.
