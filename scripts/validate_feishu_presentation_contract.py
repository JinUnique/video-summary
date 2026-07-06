#!/usr/bin/env python3
"""Validate Feishu video-summary presentation structure.

The checker accepts either rendered DocxXML or a `lark-cli docs +fetch --format json`
artifact. It focuses on reader-facing structure, not run QA.
"""

from __future__ import annotations

import argparse
import json
import re
from html import unescape
from pathlib import Path
from typing import Any, NoReturn

QUALITY_TERMS = (
    "质量记录",
    "Agent report",
    "metadata duration check",
    "media drift",
    "ASR",
    "QA",
    "no-VAD",
    "faster-whisper",
    "运行校验",
    "工具日志",
    "本地 QA",
    "delivery_record",
    "preflight",
    "ASR 覆盖",
    "readback_verification",
)
FIXED_CHAPTER_LABELS = ("原片时间点：", "本节聚焦：", "细节澄清：")
TIMESTAMP_HEADING_RE = re.compile(r"<h2\b[^>]*>\s*\d{2}:\d{2}(?:–\d{2}:\d{2})?｜")
TAG_RE = re.compile(r"<[^>]+>")
LINK_RE = re.compile(r"<a\b[^>]*href=\"([^\"]+)\"[^>]*>(.*?)</a>", re.DOTALL)
SUMMARY_BOLD_RE = re.compile(r"<(?:b|strong)\b[^>]*>(.*?)</(?:b|strong)>", re.DOTALL)


def fail(message: str) -> NoReturn:
    raise SystemExit(f"FAIL: {message}")


def load_content(path: Path) -> str:
    raw = path.read_text(encoding="utf-8")
    stripped = raw.lstrip()
    if stripped.startswith("{"):
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            fail(f"invalid json input: {path}: {exc}")
        content = extract_fetch_content(payload)
        if not content:
            fail(f"json input has no document content: {path}")
        return content
    return raw


def extract_fetch_content(payload: dict[str, Any]) -> str:
    data = payload.get("data")
    if isinstance(data, dict):
        document = data.get("document")
        if isinstance(document, dict) and isinstance(document.get("content"), str):
            return document["content"]
    document = payload.get("document")
    if isinstance(document, dict) and isinstance(document.get("content"), str):
        return document["content"]
    if isinstance(payload.get("content"), str):
        return payload["content"]
    return ""


def text_of(fragment: str) -> str:
    return unescape(TAG_RE.sub("", fragment)).strip()


def blockquotes(content: str) -> list[str]:
    return re.findall(r"<blockquote\b[^>]*>.*?</blockquote>", content, flags=re.DOTALL)


def heading_texts(content: str, tag: str) -> list[str]:
    pattern = rf"<{tag}\b[^>]*>(.*?)</{tag}>"
    return [text_of(item) for item in re.findall(pattern, content, flags=re.DOTALL)]


def assert_source_display(source_quote: str) -> dict[str, Any]:
    if "｜UP：" not in source_quote:
        fail("source metadata must use compact separator: 来源：<platform>｜UP：<creator>")
    if " / UP：" in source_quote:
        fail("source metadata still uses old raw-url / UP separator")
    link_match = LINK_RE.search(source_quote)
    if not link_match:
        fail("source metadata must link the short platform/domain label to the original video URL")
    href, label_fragment = link_match.groups()
    label = text_of(label_fragment)
    if not href.startswith(("http://", "https://")):
        fail("source link href must be the original video URL")
    if not label or label.startswith(("http://", "https://")) or "://" in label:
        fail("source link text must be a short platform/domain label, not the raw URL")
    return {"source_display_label": label}


def assert_top_structure(content: str) -> dict[str, Any]:
    title_matches = re.findall(r"<title\b[^>]*>(.*?)</title>", content, flags=re.DOTALL)
    if len(title_matches) != 1:
        fail(f"expected exactly one <title>, got {len(title_matches)}")
    title = text_of(title_matches[0])
    if "<h1" in content:
        fail("document body must not contain h1 after title")
    for heading in heading_texts(content, "h2")[:1]:
        if heading == title:
            fail("top heading duplicates document title")

    quotes = blockquotes(content)
    source_quotes = [quote for quote in quotes if "来源：" in quote]
    duration_quotes = [quote for quote in quotes if "时长：" in quote]
    tag_quotes = [quote for quote in quotes if "标签：" in quote]
    if len(source_quotes) != 1 or len(duration_quotes) != 1 or len(tag_quotes) != 1:
        fail(
            "top metadata must have separate source/duration/tags blockquotes; "
            f"got source={len(source_quotes)} duration={len(duration_quotes)} tags={len(tag_quotes)}"
        )
    if source_quotes[0] == duration_quotes[0] or source_quotes[0] == tag_quotes[0] or duration_quotes[0] == tag_quotes[0]:
        fail("source/duration/tags metadata collapsed into the same blockquote")
    result = {"title": title, "metadata_blockquotes": 3}
    result.update(assert_source_display(source_quotes[0]))
    return result


def assert_summary_callout(content: str) -> dict[str, Any]:
    summary_heading = re.search(r"<h2\b[^>]*>\s*摘要\s*</h2>", content)
    if not summary_heading:
        fail("missing h2 摘要")
    next_h2 = content.find("<h2", summary_heading.end())
    summary_region = content[summary_heading.end() : next_h2 if next_h2 != -1 else len(content)]
    callouts = re.findall(r"<callout\b[^>]*>", summary_region)
    if len(callouts) != 1:
        fail(f"摘要 section must contain exactly one callout, got {len(callouts)}")
    if "emoji=\"💡\"" not in callouts[0]:
        fail("摘要 callout should use 💡 emoji by default")
    bold_fragments = SUMMARY_BOLD_RE.findall(summary_region)
    if not bold_fragments:
        fail("摘要 must bold a small number of truly key facts")
    plain_len = max(1, len(text_of(summary_region)))
    bold_len = sum(len(text_of(fragment)) for fragment in bold_fragments)
    bold_ratio = bold_len / plain_len
    if bold_ratio > 0.35:
        fail(f"摘要 bold ratio is too high: {bold_ratio:.2%}")
    return {"summary_callouts": 1, "summary_bold_fragments": len(bold_fragments), "summary_bold_ratio": round(bold_ratio, 4)}


def assert_chapter_metadata(content: str, expected_chapters: int | None) -> dict[str, Any]:
    chapter_matches = list(TIMESTAMP_HEADING_RE.finditer(content))
    chapter_count = len(chapter_matches)
    if expected_chapters is not None and chapter_count != expected_chapters:
        fail(f"expected {expected_chapters} timestamp chapter headings, got {chapter_count}")
    if chapter_count == 0:
        fail("missing timestamp chapter headings")

    for index, match in enumerate(chapter_matches, start=1):
        next_h2 = content.find("<h2", match.end())
        chapter_region = content[match.end() : next_h2 if next_h2 != -1 else len(content)]
        quote_match = re.search(r"<blockquote\b[^>]*>.*?</blockquote>", chapter_region, flags=re.DOTALL)
        if not quote_match:
            fail(f"chapter {index} missing metadata blockquote")
        quote = quote_match.group(0)
        missing = [label for label in FIXED_CHAPTER_LABELS if label not in quote]
        if missing:
            fail(f"chapter {index} metadata blockquote missing labels: {', '.join(missing)}")
        chapter_headings = heading_texts(chapter_region, "h3")
        for label in ("本节总览", "关键内容与细节", "阶段小结"):
            if label not in chapter_headings:
                fail(f"chapter {index} missing 总-分-总 body section: {label}")
    return {"chapter_heading_count": chapter_count}


def assert_visual_blocks(content: str, expected_whiteboards: int | None) -> dict[str, Any]:
    whiteboard_count = content.count("<whiteboard")
    if expected_whiteboards is not None and whiteboard_count < expected_whiteboards:
        fail(f"expected at least {expected_whiteboards} whiteboards, got {whiteboard_count}")
    if whiteboard_count == 0:
        fail("missing Feishu-native whiteboard blocks")
    generic_diagram_titles = re.findall(r"图解｜\s*</", content)
    if generic_diagram_titles:
        fail("diagram headings must describe the relationship/process, not be empty generic captions")
    return {"whiteboard_count": whiteboard_count}


def assert_no_quality_leak(content: str) -> dict[str, Any]:
    leaks = [term for term in QUALITY_TERMS if term in content]
    if leaks:
        fail(f"reader-facing document leaks QA/report terms: {', '.join(leaks)}")
    return {"quality_terms_leaked": 0}


def assert_no_type_decision_section(content: str) -> dict[str, Any]:
    headings = heading_texts(content, "h1") + heading_texts(content, "h2") + heading_texts(content, "h3")
    if any(heading == "类型判定" for heading in headings):
        fail("reader-facing document must not include 类型判定 section")
    return {"type_decision_sections": 0}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate video-summary Feishu presentation XML")
    parser.add_argument("--input", required=True, help="Rendered XML or lark-cli docs +fetch JSON")
    parser.add_argument("--expected-chapters", type=int, default=None)
    parser.add_argument("--expected-whiteboards", type=int, default=None)
    parser.add_argument("--output", default="", help="Optional JSON report path")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    path = Path(args.input).expanduser().resolve()
    if not path.exists():
        fail(f"input does not exist: {path}")
    content = load_content(path)
    report: dict[str, Any] = {"ok": True, "input": str(path)}
    report.update(assert_top_structure(content))
    report.update(assert_summary_callout(content))
    report.update(assert_chapter_metadata(content, args.expected_chapters))
    report.update(assert_visual_blocks(content, args.expected_whiteboards))
    report.update(assert_no_quality_leak(content))
    report.update(assert_no_type_decision_section(content))
    output = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(output + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
