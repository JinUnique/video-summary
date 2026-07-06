#!/usr/bin/env python3
"""Smoke-check the video-summary type-aware strategy layer.

This is not an LLM classifier. It verifies that the repo-backed skill exposes
canonical video types, differentiated output sections, creator-learning fields,
and representative sample routing expectations.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/media/video-summary/SKILL.md"
REFERENCE = ROOT / "skills/media/video-summary/references/video-type-summary-strategies.md"
WIKI_REFERENCE = ROOT / "skills/media/video-summary/references/wiki-category-routing.md"
RUNTIME_REFERENCE = ROOT / "skills/media/video-summary/references/runtime-stability-and-entrypoints.md"
LARK_QUIRKS_REFERENCE = ROOT / "skills/media/video-summary/references/current-lark-cli-writeback-quirks.md"
BILIBILI_INGEST_REFERENCE = ROOT / "skills/media/video-summary/references/bilibili-public-api-first-ingest.md"
FRAME_EVIDENCE_REFERENCE = ROOT / "skills/media/video-summary/references/deterministic-frame-evidence.md"
VISUAL_ROUTING_REFERENCE = ROOT / "skills/media/video-summary/references/visual-understanding-routing.md"
PRESENTATION_REFERENCE = ROOT / "skills/media/video-summary/references/feishu-video-doc-presentation.md"
PREFLIGHT = ROOT / "scripts/video_summary_preflight.py"
FRAME_EVIDENCE_SCRIPT = ROOT / "scripts/select_frame_evidence.py"
VALIDATE_RUN = ROOT / "scripts/validate_video_summary_run.py"
RENDER_FEISHU = ROOT / "scripts/render_feishu_summary_doc.py"
VALIDATE_PRESENTATION = ROOT / "scripts/validate_feishu_presentation_contract.py"

CANONICAL_TYPES = [
    "finance_business_investment",
    "knowledge_course_tutorial",
    "politics_social_news",
    "entertainment_film_variety_microdrama",
    "ai_video_creation_creative_short_script",
    "interview_podcast_dialogue",
    "product_review_consumption_decision",
    "vlog_life_travel",
    "mixed_or_unknown",
]

REQUIRED_CREATOR_FIELDS = [
    "topic_and_selling_point",
    "opening_hook",
    "outline_and_script",
    "story_engine",
    "visuals_and_shots",
    "scene_blocking",
    "characters_or_roles",
    "pacing_editing_sound",
    "emotion_curve",
    "reusable_template",
    "prompt_transfer_language",
]

EXPECTED_STRUCTURE_TERMS = {
    "finance_business_investment": ["核心判断与适用边界", "论点—证据—假设", "风险与反例"],
    "knowledge_course_tutorial": ["学习路线", "核心概念", "常见误区与修正"],
    "politics_social_news": ["事件时间线", "关键人物 / 机构 / 利益相关方", "未来走向"],
    "entertainment_film_variety_microdrama": ["故事结构", "人物/关系/冲突", "视听手法"],
    "ai_video_creation_creative_short_script": ["开头钩子拆解", "内容大纲 / 台本结构", "可迁移到 AI 视频提示词的表达方式"],
    "interview_podcast_dialogue": ["对谈地图", "共识 / 分歧 / 未回答问题", "关键金句与上下文"],
    "product_review_consumption_decision": ["产品定位与目标用户", "测试方法与可信度", "购买/使用决策树"],
    "vlog_life_travel": ["行程 / 场景地图", "体验亮点与踩坑", "可复用 VLOG 结构"],
    "mixed_or_unknown": ["按内容价值分区", "章节详解", "待确认问题"],
}

SAMPLES = [
    {
        "name": "finance_knowledge",
        "text": "美联储降息预期、AI 芯片公司估值、现金流假设、风险情景和投资启发",
        "expected": "finance_business_investment",
    },
    {
        "name": "knowledge_tutorial",
        "text": "Python 自动化教程，先讲环境权限，再演示步骤、常见错误、验证信号和复现练习",
        "expected": "knowledge_course_tutorial",
    },
    {
        "name": "social_news",
        "text": "突发公共事件时间线、政府机构回应、争议点、普通人影响和未来走向",
        "expected": "politics_social_news",
    },
    {
        "name": "entertainment_microdrama",
        "text": "短剧剧情拆解，角色关系、冲突升级、反转 payoff、视听手法和情绪曲线",
        "expected": "entertainment_film_variety_microdrama",
    },
    {
        "name": "ai_creator",
        "text": "AI 视频创作教程，拆解开头钩子、台本结构、镜头画面、剪辑节奏、声音设计、提示词写法",
        "expected": "ai_video_creation_creative_short_script",
    },
    {
        "name": "interview_dialogue",
        "text": "主持人和嘉宾对谈，梳理观点、分歧、金句、问题线索和未回答问题",
        "expected": "interview_podcast_dialogue",
    },
    {
        "name": "product_review",
        "text": "新品手机评测，测试方法、价格、优缺点、竞品对比、适合谁购买和消费决策",
        "expected": "product_review_consumption_decision",
    },
    {
        "name": "vlog_travel",
        "text": "旅行 VLOG，路线景点、生活体验、氛围、实用信息、踩坑和拍法节奏",
        "expected": "vlog_life_travel",
    },
    {
        "name": "mixed_interview_product_business",
        "text": "播客采访创业者，聊新产品评测、商业模式、用户增长和创作者经验，类型混合",
        "expected": "mixed_or_unknown",
    },
]

KEYWORD_RULES = {
    "ai_video_creation_creative_short_script": ["AI 视频", "创作", "开头钩子", "台本", "镜头", "剪辑", "提示词"],
    "entertainment_film_variety_microdrama": ["短剧", "剧情", "角色", "冲突", "反转", "payoff", "视听", "情绪曲线"],
    "politics_social_news": ["突发", "时间线", "机构", "争议", "普通人", "未来走向"],
    "finance_business_investment": ["美联储", "估值", "现金流", "投资", "风险", "情景"],
    "knowledge_course_tutorial": ["教程", "环境", "权限", "步骤", "常见错误", "验证", "练习"],
    "interview_podcast_dialogue": ["主持人", "嘉宾", "对谈", "观点", "分歧", "金句", "未回答问题"],
    "product_review_consumption_decision": ["新品", "评测", "测试方法", "价格", "优缺点", "竞品", "购买", "消费决策"],
    "vlog_life_travel": ["旅行", "VLOG", "路线", "景点", "体验", "氛围", "实用信息", "踩坑", "拍法"],
    "mixed_or_unknown": ["播客", "采访", "产品评测", "商业模式", "创作者", "类型混合"],
}

WIKI_REQUIRED_TERMS = [
    "wiki_category_decision",
    "VIDEO_SUMMARY_WIKI_SPACE_ID",
    "No default space is shipped",
    "Existing finance/business/knowledge parent",
    "configured fallback category",
    "lark-cli wiki nodes list",
    "lark-cli docs +create",
    "--parent-token <CATEGORY_PARENT_NODE_TOKEN>",
    "explicitly authorized category creation",
    "do not append `--format`",
    "No duplicate or near-duplicate category",
]

RUNTIME_REQUIRED_TERMS = [
    "video_summary_preflight.py",
    "transcribe_faster_whisper.py",
    "validate_video_summary_run.py",
    "--entry terminal",
    "--entry feishu",
    "no-VAD",
    "audio_16k_mono.wav",
    "delivery_record.json",
]

LARK_QUIRK_REQUIRED_TERMS = [
    "docs +create --help",
    "lark-cli skills read lark-doc references/lark-doc-create.md",
    "--content @runs/<run-id>/doc/feishu_summary.xml",
    "docs +media-insert --help",
    "docs +whiteboard-update --help",
    "--file ./",
    "--command str_replace",
    "document.new_blocks",
]

PRESENTATION_REQUIRED_TERMS = [
    "scripts/render_feishu_summary_doc.py",
    "scripts/validate_feishu_presentation_contract.py",
    "<callout emoji=\"💡\"",
    "separate blockquotes",
    "原片时间点",
    "本节聚焦",
    "细节澄清",
]

BILIBILI_INGEST_REQUIRED_TERMS = [
    "Public API baseline",
    "Stream adequacy check",
    "Bounded `yt-dlp` enrichment probe",
    "Escalation",
    "metadata/ingest_decision.json",
    "source_order",
    "public_api_baseline -> stream_adequacy -> optional_yt_dlp_enrichment -> escalation_if_needed",
    "not the ingest baseline",
    "Starting default Bilibili runs with `yt-dlp --dump-single-json` as the primary gate",
]

FRAME_EVIDENCE_REQUIRED_TERMS = [
    "deterministic_frame_evidence",
    "remote_vision_used: false",
    "scripts/select_frame_evidence.py",
    "frames/frame_evidence.json",
    "ffmpeg",
    "ffprobe",
    "tesseract",
    "visual-understanding-routing.md",
    "do not choose the evidence frames",
]

VISUAL_ROUTING_REQUIRED_TERMS = [
    "Layered Model",
    "vision_analyze",
    "selected chapter frames",
    "local VLM",
    "visual_understanding_notes",
    "depends_on_frame_evidence",
    "fallback",
    "visible evidence",
]

WIKI_ROUTE_SAMPLES = [
    {
        "name": "existing_finance",
        "primary_type": "finance_business_investment",
        "text": "SpaceX IPO 估值、投行定价、风险和投资启发",
        "expected_parent": "Finance and Business",
        "expected_action": "use_existing",
    },
    {
        "name": "multi_candidate_creator_animation",
        "primary_type": "entertainment_film_variety_microdrama",
        "secondary_types": ["ai_video_creation_creative_short_script"],
        "text": "国产动画逐帧解析，同时拆解镜头、视听手法、节奏和创作者可复用技巧",
        "expected_parent": "Creator Production Analysis",
        "expected_action": "use_existing",
    },
    {
        "name": "new_product_review_category",
        "primary_type": "product_review_consumption_decision",
        "text": "新品手机评测、竞品对比、价格、优缺点和购买决策树",
        "expected_parent": "Product Reviews and Buying Decisions",
        "expected_action": "create_category",
    },
    {
        "name": "new_social_news_category",
        "primary_type": "politics_social_news",
        "text": "公共事件时间线、机构回应、争议点和未来走向",
        "expected_parent": "Current Affairs and Society",
        "expected_action": "create_category",
    },
    {
        "name": "interview_by_finance_topic",
        "primary_type": "interview_podcast_dialogue",
        "secondary_types": ["finance_business_investment"],
        "text": "访谈创业者，核心价值是商业模式、估值假设和市场风险",
        "expected_parent": "Finance and Business",
        "expected_action": "use_existing",
    },
    {
        "name": "new_vlog_category",
        "primary_type": "vlog_life_travel",
        "text": "旅行 VLOG，路线、景点、生活体验、踩坑和拍法节奏",
        "expected_parent": "Travel and Life Vlogs",
        "expected_action": "create_category",
    },
    {
        "name": "unknown_fallback",
        "primary_type": "mixed_or_unknown",
        "text": "素材很少，无法判断主要价值",
        "expected_parent": "Uncategorized",
        "expected_action": "fallback",
    },
]


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def classify_sample(text: str) -> str:
    if "类型混合" in text or "无法判断" in text:
        return "mixed_or_unknown"
    scores = {
        kind: sum(1 for word in words if word in text)
        for kind, words in KEYWORD_RULES.items()
    }
    best, score = max(scores.items(), key=lambda item: item[1])
    if score < 2:
        return "mixed_or_unknown"
    return best


def route_wiki_sample(sample: dict[str, object]) -> tuple[str, str]:
    primary = str(sample.get("primary_type", ""))
    raw_secondary = sample.get("secondary_types", [])
    secondary = set(raw_secondary if isinstance(raw_secondary, list) else [])
    text = str(sample.get("text", ""))

    if primary == "finance_business_investment":
        return "Finance and Business", "use_existing"
    if primary == "ai_video_creation_creative_short_script":
        return "Creator Production Analysis", "use_existing"
    if primary == "entertainment_film_variety_microdrama":
        if "ai_video_creation_creative_short_script" in secondary or any(
            marker in text for marker in ["创作者", "镜头", "视听", "节奏", "可复用"]
        ):
            return "Creator Production Analysis", "use_existing"
        return "Content Analysis", "use_existing"
    if primary == "product_review_consumption_decision":
        return "Product Reviews and Buying Decisions", "create_category"
    if primary == "politics_social_news":
        return "Current Affairs and Society", "create_category"
    if primary == "interview_podcast_dialogue":
        if "finance_business_investment" in secondary:
            return "Finance and Business", "use_existing"
        if "ai_video_creation_creative_short_script" in secondary:
            return "Creator Production Analysis", "use_existing"
        return "Interviews and Podcasts", "create_category"
    if primary == "vlog_life_travel":
        return "Travel and Life Vlogs", "create_category"
    return "Uncategorized", "fallback"


def preflight_ytdlp_is_optional(preflight_text: str) -> bool:
    tree = ast.parse(preflight_text)
    main_defs = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main"]
    if len(main_defs) != 1:
        return False
    ytdlp_calls: list[ast.Call] = []
    for node in ast.walk(main_defs[0]):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Name) or node.func.id != "check_command":
            continue
        if not node.args or not isinstance(node.args[0], ast.Constant) or node.args[0].value != "yt-dlp":
            continue
        ytdlp_calls.append(node)
    if len(ytdlp_calls) != 1:
        return False
    for keyword in ytdlp_calls[0].keywords:
        if keyword.arg == "required" and isinstance(keyword.value, ast.Constant):
            return keyword.value.value is False
    return False


def main() -> None:
    skill_text = SKILL.read_text(encoding="utf-8")
    ref_text = REFERENCE.read_text(encoding="utf-8")
    wiki_ref_text = WIKI_REFERENCE.read_text(encoding="utf-8")
    runtime_ref_text = RUNTIME_REFERENCE.read_text(encoding="utf-8")
    lark_quirks_text = LARK_QUIRKS_REFERENCE.read_text(encoding="utf-8")
    bilibili_ingest_text = BILIBILI_INGEST_REFERENCE.read_text(encoding="utf-8")
    frame_evidence_text = FRAME_EVIDENCE_REFERENCE.read_text(encoding="utf-8")
    visual_routing_text = VISUAL_ROUTING_REFERENCE.read_text(encoding="utf-8")
    presentation_text = PRESENTATION_REFERENCE.read_text(encoding="utf-8")
    preflight_text = PREFLIGHT.read_text(encoding="utf-8")
    frame_evidence_script_text = FRAME_EVIDENCE_SCRIPT.read_text(encoding="utf-8")
    validate_run_text = VALIDATE_RUN.read_text(encoding="utf-8")
    render_feishu_text = RENDER_FEISHU.read_text(encoding="utf-8")
    validate_presentation_text = VALIDATE_PRESENTATION.read_text(encoding="utf-8")

    if "video-type-summary-strategies.md" not in skill_text:
        fail("SKILL.md does not point to video-type-summary-strategies.md")
    if "wiki-category-routing.md" not in skill_text:
        fail("SKILL.md does not point to wiki-category-routing.md")
    if "video_type_decision" not in skill_text:
        fail("SKILL.md does not require video_type_decision")
    if "wiki_category_decision" not in skill_text:
        fail("SKILL.md does not require wiki_category_decision")
    if "runtime-stability-and-entrypoints.md" not in skill_text:
        fail("SKILL.md does not point to runtime-stability-and-entrypoints.md")
    if "current-lark-cli-writeback-quirks.md" not in skill_text:
        fail("SKILL.md does not point to current-lark-cli-writeback-quirks.md")
    if "bilibili-public-api-first-ingest.md" not in skill_text:
        fail("SKILL.md does not point to bilibili-public-api-first-ingest.md")
    if "deterministic-frame-evidence.md" not in skill_text:
        fail("SKILL.md does not point to deterministic-frame-evidence.md")
    if "visual-understanding-routing.md" not in skill_text:
        fail("SKILL.md does not point to visual-understanding-routing.md")
    if "public-API-first" not in skill_text:
        fail("SKILL.md description does not expose public-API-first behavior")
    if "ingest_decision" not in skill_text:
        fail("SKILL.md does not require ingest_decision")
    if "scripts/video_summary_preflight.py" not in skill_text:
        fail("SKILL.md does not require entry preflight")
    if "scripts/transcribe_faster_whisper.py" not in skill_text:
        fail("SKILL.md does not use the stable ASR script")
    if "scripts/select_frame_evidence.py" not in skill_text:
        fail("SKILL.md does not use the deterministic frame evidence script")
    if "Keep frame selection local and deterministic" not in skill_text or "vision_analyze" not in skill_text:
        fail("SKILL.md does not separate deterministic frame evidence from visual understanding")
    if "scripts/validate_video_summary_run.py" not in skill_text:
        fail("SKILL.md does not require final run validation")
    if "scripts/render_feishu_summary_doc.py" not in skill_text:
        fail("SKILL.md does not require Feishu XML rendering")
    if "--require-presentation-contract" not in skill_text:
        fail("SKILL.md does not require Feishu presentation contract validation")

    for kind in CANONICAL_TYPES:
        if kind not in ref_text:
            fail(f"missing canonical type: {kind}")

    for kind, terms in EXPECTED_STRUCTURE_TERMS.items():
        for term in terms:
            if term not in ref_text:
                fail(f"missing output term for {kind}: {term}")

    for field in REQUIRED_CREATOR_FIELDS:
        if field not in ref_text:
            fail(f"missing creator-learning field: {field}")

    sections = re.findall(r"^### \d+\. `([^`]+)`", ref_text, re.MULTILINE)
    missing_sections = set(CANONICAL_TYPES) - set(sections)
    if missing_sections:
        fail(f"missing strategy sections: {sorted(missing_sections)}")

    for sample in SAMPLES:
        actual = classify_sample(sample["text"])
        if actual != sample["expected"]:
            fail(f"sample {sample['name']} classified as {actual}, expected {sample['expected']}")

    for term in WIKI_REQUIRED_TERMS:
        if term not in wiki_ref_text and term not in skill_text:
            fail(f"missing wiki routing term: {term}")
    for term in RUNTIME_REQUIRED_TERMS:
        if term not in runtime_ref_text and term not in skill_text:
            fail(f"missing runtime stability term: {term}")
    for term in LARK_QUIRK_REQUIRED_TERMS:
        if term not in lark_quirks_text and term not in skill_text:
            fail(f"missing lark-cli quirk term: {term}")
    for term in PRESENTATION_REQUIRED_TERMS:
        if term not in presentation_text and term not in skill_text:
            fail(f"missing presentation contract term: {term}")
    for term in BILIBILI_INGEST_REQUIRED_TERMS:
        if term not in bilibili_ingest_text and term not in skill_text:
            fail(f"missing Bilibili ingest architecture term: {term}")
    for term in FRAME_EVIDENCE_REQUIRED_TERMS:
        if term not in frame_evidence_text and term not in skill_text:
            fail(f"missing deterministic frame evidence term: {term}")
    for term in VISUAL_ROUTING_REQUIRED_TERMS:
        if term not in visual_routing_text and term not in skill_text:
            fail(f"missing visual understanding routing term: {term}")
    for term in ["remote_vision_used", "frame_stats", "ffmpeg", "ffprobe"]:
        if term not in frame_evidence_script_text:
            fail(f"select_frame_evidence.py missing implementation term: {term}")
    if "--require-frame-evidence" not in validate_run_text:
        fail("validate_video_summary_run.py does not expose --require-frame-evidence")
    if "--require-presentation-contract" not in validate_run_text:
        fail("validate_video_summary_run.py does not expose --require-presentation-contract")
    if "assert_no_type_decision_section" not in validate_run_text:
        fail("validate_video_summary_run.py does not enforce no reader-facing type decision section")
    for term in ["<title>", "<callout", "<whiteboard", "原片时间点：", "本节聚焦：", "细节澄清：", "本节总览", "关键内容与细节", "阶段小结"]:
        if term not in render_feishu_text:
            fail(f"render_feishu_summary_doc.py missing rich XML term: {term}")
    for forbidden in ["def render_type_decision", "heading(2, \"类型判定\")"]:
        if forbidden in render_feishu_text:
            fail(f"render_feishu_summary_doc.py still emits reader-facing type decision: {forbidden}")
    for term in ["source/duration/tags metadata collapsed", "source link text must be a short platform/domain label", "摘要 section must contain exactly one callout", "摘要 must bold a small number", "reader-facing document leaks", "reader-facing document must not include 类型判定 section", '"ASR"', '"QA"']:
        if term not in validate_presentation_text:
            fail(f"validate_feishu_presentation_contract.py missing guard: {term}")
    if "remote_vision_used" not in validate_run_text:
        fail("validate_video_summary_run.py does not reject remote-vision-dependent frame evidence")
    if not preflight_ytdlp_is_optional(preflight_text):
        fail("preflight still treats yt-dlp as a required baseline command")

    for sample in WIKI_ROUTE_SAMPLES:
        parent, action = route_wiki_sample(sample)
        if parent != sample["expected_parent"] or action != sample["expected_action"]:
            fail(
                f"wiki sample {sample['name']} routed to {parent}/{action}, "
                f"expected {sample['expected_parent']}/{sample['expected_action']}"
            )

    print("PASS video-summary type strategy smoke")
    print("types", len(CANONICAL_TYPES))
    for sample in SAMPLES:
        print(f"sample {sample['name']} -> {classify_sample(sample['text'])}")
    print("wiki_route_samples", len(WIKI_ROUTE_SAMPLES))
    print("runtime_terms", len(RUNTIME_REQUIRED_TERMS))
    print("lark_quirk_terms", len(LARK_QUIRK_REQUIRED_TERMS))
    print("presentation_terms", len(PRESENTATION_REQUIRED_TERMS))
    print("bilibili_ingest_terms", len(BILIBILI_INGEST_REQUIRED_TERMS))
    for sample in WIKI_ROUTE_SAMPLES:
        parent, action = route_wiki_sample(sample)
        print(f"wiki sample {sample['name']} -> {parent} ({action})")


if __name__ == "__main__":
    main()
