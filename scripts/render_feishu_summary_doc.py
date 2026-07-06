#!/usr/bin/env python3
"""Render a video-summary `summary_assets.json` into Feishu DocxXML.

The renderer intentionally targets rich XML blocks instead of Markdown so Feishu
keeps separate metadata blockquotes, summary callouts, and native whiteboard
placeholders stable across lark-cli versions.
"""

from __future__ import annotations

import argparse
import json
import re
from html import escape
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

MAX_TAGS = 8
PLATFORM_LABELS = {
    "youtube.com": "youtube",
    "youtu.be": "youtube",
    "bilibili.com": "bilibili",
    "b23.tv": "bilibili",
    "douyin.com": "douyin",
    "iesdouyin.com": "douyin",
    "tiktok.com": "tiktok",
    "x.com": "x",
    "twitter.com": "x",
    "xiaohongshu.com": "xiaohongshu",
}
BOLD_MARKUP_RE = re.compile(r"\*\*(.+?)\*\*")
KEY_INFO_RE = re.compile(
    r"(?:[$￥¥]\s?\d[\d,]*(?:\.\d+)?(?:\s?(?:万美元|美元|元))?"
    r"|\d[\d,]*(?:\.\d+)?\s?(?:万|亿|人|天|小时|分钟|秒|%|次|个|组|队|名|年|个月)"
    r"|「[^」]{2,18}」|《[^》]{2,18}》)"
)
SUMMARY_FALLBACK_RE = re.compile(r"[\w\u4e00-\u9fff]{2,18}")
INTERNAL_REPORT_REWRITES = (
    ("AI/ASR 噪声", "音频转写噪声"),
    ("ASR 中", "转写中"),
    ("ASR 把", "转写把"),
    ("ASR 对", "转写对"),
    ("ASR 首句", "转写首句"),
    ("ASR 噪声", "转写噪声"),
    ("ASR 误听", "转写误听"),
    ("ASR 有误听", "转写有误听"),
    ("ASR 有噪声", "转写有噪声"),
    ("ASR 不稳定", "转写不稳定"),
    ("ASR", "转写"),
    ("no-VAD 转写", "完整转写"),
    ("运行 QA", "交付校验"),
    ("本地 QA", "本地校验"),
    ("QA", "校验"),
    ("工具日志", "过程记录"),
)


def text(value: Any) -> str:
    return escape(str(value), quote=False)


def reader_plain(value: Any) -> str:
    rendered = str(value)
    for old, new in INTERNAL_REPORT_REWRITES:
        rendered = rendered.replace(old, new)
    return rendered


def reader_text(value: Any) -> str:
    return escape(reader_plain(value), quote=False)


def add_sparse_summary_emphasis(value: str) -> str:
    """Add limited markdown-bold markers when the summary has none."""

    if "**" in value:
        return value
    spans: list[tuple[int, int]] = []
    max_bold_chars = max(2, min(18, int(len(value) * 0.25)))
    bold_chars = 0
    for match in KEY_INFO_RE.finditer(value):
        start, end = match.span()
        candidate = match.group(0).strip()
        if not candidate or len(candidate) > 24:
            continue
        if any(not (end <= existing_start or start >= existing_end) for existing_start, existing_end in spans):
            continue
        if bold_chars + len(candidate) > max_bold_chars:
            continue
        spans.append((start, end))
        bold_chars += len(candidate)
        if len(spans) >= 2:
            break
    if not spans:
        fallback = SUMMARY_FALLBACK_RE.search(value)
        if fallback:
            start, end = fallback.span()
            spans.append((start, min(end, start + max_bold_chars)))
    for start, end in reversed(spans):
        value = f"{value[:start]}**{value[start:end]}**{value[end:]}"
    return value


def rich_reader_text(value: Any, *, auto_emphasis: bool = False) -> str:
    rendered = reader_plain(value)
    if auto_emphasis:
        rendered = add_sparse_summary_emphasis(rendered)

    pieces: list[str] = []
    cursor = 0
    for match in BOLD_MARKUP_RE.finditer(rendered):
        pieces.append(escape(rendered[cursor : match.start()], quote=False))
        bold_text = match.group(1).strip()
        if bold_text:
            pieces.append(f"<b>{escape(bold_text, quote=False)}</b>")
        cursor = match.end()
    pieces.append(escape(rendered[cursor:], quote=False))
    return "".join(pieces)


def attr(value: Any) -> str:
    return escape(str(value), quote=True)


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def source_url_for_assets(assets: dict[str, Any], metadata: dict[str, Any]) -> str:
    for key in ("source_url", "webpage_url", "original_url", "url"):
        value = assets.get(key) or metadata.get(key)
        if isinstance(value, str) and value.startswith(("http://", "https://")):
            return value
    return ""


def platform_label_for_source(source_url: str, metadata: dict[str, Any]) -> str:
    host = urlparse(source_url).netloc.lower().split(":", 1)[0]
    if host.startswith("www."):
        host = host[4:]
    if host.startswith("m."):
        host = host[2:]
    for domain, label in PLATFORM_LABELS.items():
        if host == domain or host.endswith(f".{domain}"):
            return label

    platform = str(
        metadata.get("platform")
        or metadata.get("extractor_key")
        or metadata.get("extractor")
        or ""
    ).lower()
    normalized = re.sub(r"[^a-z0-9]+", "", platform)
    exact_aliases = {"x": "x"}
    if normalized in exact_aliases:
        return exact_aliases[normalized]
    platform_aliases = {
        "xiaohongshu": "xiaohongshu",
        "rednote": "xiaohongshu",
        "bilibili": "bilibili",
        "bili": "bilibili",
        "youtube": "youtube",
        "youtu": "youtube",
        "douyin": "douyin",
        "iesdouyin": "douyin",
        "tiktok": "tiktok",
        "twitter": "x",
    }
    for alias in sorted(platform_aliases, key=len, reverse=True):
        if alias in normalized:
            return platform_aliases[alias]
    if not host:
        return "原视频"
    parts = host.split(".")
    return parts[-2] if len(parts) >= 2 else host


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"summary assets must be a JSON object: {path}")
    return payload


def dict_value(mapping: dict[str, Any], key: str) -> dict[str, Any]:
    value = mapping.get(key)
    return value if isinstance(value, dict) else {}


def format_duration(seconds: Any) -> str:
    try:
        total = int(round(float(seconds)))
    except (TypeError, ValueError):
        return str(seconds or "未知")
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def timestamp_url(source_url: str, seconds: Any) -> str:
    try:
        value = int(float(seconds))
    except (TypeError, ValueError):
        value = 0
    separator = "&" if "?" in source_url else "?"
    return f"{source_url}{separator}t={value}"


def metadata_tags(metadata: dict[str, Any]) -> list[str]:
    raw_tags = metadata.get("tags") or metadata.get("tag") or []
    tags: list[str] = []
    for item in as_list(raw_tags):
        if isinstance(item, dict):
            candidate = item.get("tag_name") or item.get("name") or item.get("title")
        else:
            candidate = item
        if candidate:
            tags.append(str(candidate))
    return tags[:MAX_TAGS]


def owner_name(metadata: dict[str, Any]) -> str:
    owner = metadata.get("owner")
    if isinstance(owner, dict):
        return str(owner.get("name") or owner.get("uname") or owner.get("mid") or "未知")
    return str(metadata.get("up") or metadata.get("creator") or "未知")


def title_for_assets(assets: dict[str, Any]) -> str:
    metadata = dict_value(assets, "metadata")
    raw_title = metadata.get("title") or assets.get("title") or "视频智能总结"
    title = str(raw_title)
    if not title.endswith("｜智能总结"):
        title = f"{title}｜智能总结"
    return title


def summary_paragraphs(assets: dict[str, Any], title: str) -> list[str]:
    for key in ("summary_paragraphs", "summary", "overview", "abstract"):
        value = assets.get(key)
        if isinstance(value, list) and value:
            return [str(item) for item in value if str(item).strip()]
        if isinstance(value, str) and value.strip():
            parts = [part.strip() for part in re.split(r"\n\s*\n", value) if part.strip()]
            return parts or [value.strip()]

    chapters = [chapter for chapter in as_list(assets.get("chapters")) if isinstance(chapter, dict)]
    chapter_titles = [str(chapter.get("title")) for chapter in chapters if chapter.get("title")]
    first = chapter_titles[0] if chapter_titles else "开场主线"
    last = chapter_titles[-1] if len(chapter_titles) > 1 else "结尾判断"
    return [
        f"这份总结围绕《{title.replace('｜智能总结', '')}》提炼主线，把视频从「{first}」推进到「{last}」的结构拆成可回看的章节。",
        "正文按视频本身的信息价值组织，优先保留关键事实、转折、证据和可复用判断，而不是套用单一模板。",
        "阅读时建议先看摘要和观看导航，再按章节进入图解与视频时间戳帧；交付校验和写回记录保留在本地报告，不写入正文。",
    ]


def paragraph(body: str) -> str:
    return f"<p>{body}</p>"


def heading(level: int, value: str) -> str:
    return f"<h{level}>{text(value)}</h{level}>"


def ul(items: list[str]) -> str:
    if not items:
        return ""
    return "<ul>" + "".join(f"<li>{rich_reader_text(item)}</li>" for item in items) + "</ul>"


def metadata_blocks(assets: dict[str, Any]) -> list[str]:
    metadata = dict_value(assets, "metadata")
    source_url = source_url_for_assets(assets, metadata)
    source_label = platform_label_for_source(source_url, metadata)
    creator = owner_name(metadata)
    duration = format_duration(metadata.get("duration") or assets.get("duration"))
    tags = metadata_tags(metadata)
    tag_text = "、".join(tags) if tags else "未提供"
    source_value = f'<a href="{attr(source_url)}">{text(source_label)}</a>' if source_url else text(source_label)
    return [
        f"<blockquote>{paragraph(f'来源：{source_value}｜UP：{text(creator)}')}</blockquote>",
        f"<blockquote>{paragraph(f'时长：{text(duration)}')}</blockquote>",
        f"<blockquote>{paragraph(f'标签：{text(tag_text)}')}</blockquote>",
    ]


def render_summary(assets: dict[str, Any], title: str) -> list[str]:
    blocks = [heading(2, "摘要")]
    paragraphs = "".join(paragraph(rich_reader_text(item, auto_emphasis=True)) for item in summary_paragraphs(assets, title)[:4])
    blocks.append(
        '<callout emoji="💡" background-color="light-yellow" border-color="yellow">'
        f"{paragraphs}"
        "</callout>"
    )
    return blocks


def render_navigation(assets: dict[str, Any]) -> list[str]:
    metadata = dict_value(assets, "metadata")
    source_url = source_url_for_assets(assets, metadata)
    chapters = [chapter for chapter in as_list(assets.get("chapters")) if isinstance(chapter, dict)]
    if not chapters:
        return []
    rows = []
    for chapter in chapters:
        start = str(chapter.get("start") or "00:00")
        end = str(chapter.get("end") or "")
        title = str(chapter.get("title") or "未命名章节")
        link = timestamp_url(source_url, chapter.get("start_seconds")) if source_url else ""
        time_label = f"{start}–{end}" if end else start
        time_cell = f'<a href="{attr(link)}">{text(time_label)}</a>' if link else text(time_label)
        rows.append(f"<tr><td>{time_cell}</td><td>{text(title)}</td></tr>")
    return [
        heading(2, "观看导航"),
        "<table>"
        "<thead><tr><th background-color=\"light-gray\">时间</th><th background-color=\"light-gray\">这一段看什么</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table>",
    ]


def render_creator_learning(assets: dict[str, Any]) -> list[str]:
    learning = assets.get("creator_learning")
    if not isinstance(learning, dict):
        return []
    blocks = [heading(2, "创作学习提炼")]
    items: list[str] = []
    topic = learning.get("topic_and_selling_point")
    if isinstance(topic, dict):
        promise = topic.get("promise") or topic.get("subject")
        if promise:
            items.append(f"题材与卖点：{promise}")
    labels = {
        "opening_hook": "开头钩子",
        "story_engine": "故事引擎",
        "reusable_template": "可复用模板",
    }
    for key, label in labels.items():
        if learning.get(key):
            items.append(f"{label}：{learning[key]}")
    blocks.append(ul(items))
    prompt_items = [str(item) for item in as_list(learning.get("prompt_transfer_language")) if str(item).strip()]
    if prompt_items:
        blocks.append(heading(3, "Prompt 迁移语言"))
        blocks.append(ul(prompt_items[:8]))
    return blocks


def render_overview_whiteboard(assets: dict[str, Any]) -> list[str]:
    chapters = [chapter for chapter in as_list(assets.get("chapters")) if isinstance(chapter, dict)]
    if not chapters:
        return []
    decision = dict_value(assets, "video_type_decision")
    primary = str(decision.get("primary_type") or "")
    title = "结构图｜从开场到结论的内容主线"
    if "finance" in primary or "business" in primary:
        title = "机制总览｜从现象到判断的因果链"
    elif "ai_video" in primary or "entertainment" in primary:
        title = "结构图｜从规则钩子到情绪收尾"
    return [heading(2, title), '<whiteboard type="blank"></whiteboard>']


def first_text(mapping: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = mapping.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def normalize_text_item(value: Any) -> str:
    if isinstance(value, dict):
        for key in ("summary", "text", "content", "detail", "event", "point"):
            if value.get(key):
                return str(value[key]).strip()
        return ""
    return str(value).strip()


def chapter_detail_items(chapter: dict[str, Any]) -> list[str]:
    items: list[str] = []
    for key in ("points", "details", "evidence", "key_events", "supporting_details", "steps"):
        for item in as_list(chapter.get(key)):
            normalized = normalize_text_item(item)
            if normalized and normalized not in items:
                items.append(normalized)
    return items[:7]


def chapter_overview(chapter: dict[str, Any], title: str) -> str:
    return first_text(chapter, "overview", "summary", "body_intro", "focus") or f"这一段围绕“{title}”展开，先交代该时间段的核心主题，再推进到后续章节需要承接的判断。"


def chapter_conclusion(chapter: dict[str, Any]) -> str:
    return first_text(chapter, "implication", "creator_value", "conclusion", "stage_conclusion") or "这一段的阶段性作用，是把前面的信息收束成可继续观看和复用的判断。"


def render_chapters(assets: dict[str, Any]) -> list[str]:
    metadata = dict_value(assets, "metadata")
    source_url = source_url_for_assets(assets, metadata)
    blocks: list[str] = []
    chapters = [chapter for chapter in as_list(assets.get("chapters")) if isinstance(chapter, dict)]
    for index, chapter in enumerate(chapters, start=1):
        start = str(chapter.get("start") or "00:00")
        end = str(chapter.get("end") or "")
        title = str(chapter.get("title") or f"第 {index} 节")
        time_label = f"{start}–{end}" if end else start
        blocks.append(heading(2, f"{time_label}｜{title}"))
        link = timestamp_url(source_url, chapter.get("start_seconds")) if source_url else ""
        time_value = f'<a href="{attr(link)}">{text(start)}</a>' if link else text(start)
        focus = reader_text(chapter.get("focus") or "本节提炼视频在该时间段的核心信息。")
        clarification = reader_text(chapter.get("clarification") or "本节按视频原始语境解读；不把本地校验或过程记录写入正文。")
        blocks.append(
            "<blockquote>"
            f"{paragraph(f'原片时间点：{time_value}')}"
            f"{paragraph(f'本节聚焦：{focus}')}"
            f"{paragraph(f'细节澄清：{clarification}')}"
            "</blockquote>"
        )
        blocks.append(heading(3, "本节总览"))
        blocks.append(paragraph(rich_reader_text(chapter_overview(chapter, title))))
        detail_items = chapter_detail_items(chapter)
        if not detail_items:
            detail_items = [first_text(chapter, "focus", "summary") or f"围绕“{title}”保留视频在该段提供的主要事实、动作或判断。"]
        blocks.append(heading(3, "关键内容与细节"))
        blocks.append(ul(detail_items))
        blocks.append(heading(3, "阶段小结"))
        blocks.append(paragraph(rich_reader_text(chapter_conclusion(chapter))))
        blocks.append(heading(3, f"图解｜{title}"))
        blocks.append('<whiteboard type="blank"></whiteboard>')
        frame_seconds = chapter.get("frame_seconds") or chapter.get("start_seconds") or 0
        frame_start = format_duration(frame_seconds)
        anchor_id = str(chapter.get("id") or f"c{index:02d}")
        blocks.append(heading(3, f"视频时间戳｜{title}｜{frame_start}"))
        blocks.append(paragraph(text(f"【证据帧锚点：{anchor_id}_frame】")))
    return blocks


def render_document(assets: dict[str, Any]) -> str:
    title = title_for_assets(assets)
    blocks: list[str] = [f"<title>{text(title)}</title>"]
    blocks.extend(metadata_blocks(assets))
    blocks.extend(render_summary(assets, title))
    blocks.extend(render_creator_learning(assets))
    blocks.extend(render_navigation(assets))
    blocks.extend(render_overview_whiteboard(assets))
    blocks.extend(render_chapters(assets))
    return "\n".join(block for block in blocks if block) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render video-summary assets to Feishu DocxXML")
    parser.add_argument("--assets", required=True, help="Path to doc/summary_assets.json")
    parser.add_argument("--output", required=True, help="Output XML path")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    assets_path = Path(args.assets).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    assets = load_json(assets_path)
    xml = render_document(assets)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(xml, encoding="utf-8")
    print(json.dumps({"ok": True, "assets": str(assets_path), "output": str(output_path), "bytes": len(xml.encode("utf-8"))}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
