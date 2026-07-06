#!/usr/bin/env python3
"""Validate a completed video-summary run artifact directory."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, NoReturn

from validate_feishu_presentation_contract import load_content
from validate_feishu_presentation_contract import assert_chapter_metadata
from validate_feishu_presentation_contract import assert_no_quality_leak
from validate_feishu_presentation_contract import assert_no_type_decision_section
from validate_feishu_presentation_contract import assert_summary_callout
from validate_feishu_presentation_contract import assert_top_structure
from validate_feishu_presentation_contract import assert_visual_blocks

REQUIRED_FEISHU_FILES = (
    "feishu/delivery_record.json",
    "feishu/readback_verification.json",
)


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"missing required artifact: {path}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid json artifact: {path}: {exc}") from exc


def fail(message: str) -> NoReturn:
    raise SystemExit(f"FAIL: {message}")


def validate_preflight(run_dir: Path, delivery: str) -> dict[str, Any]:
    preflight_dir = run_dir / "metadata"
    preflight_paths = sorted(preflight_dir.glob("preflight_*.json"))
    if not preflight_paths:
        fail("missing preflight artifact: metadata/preflight_*.json")

    reports = []
    accepted = []
    for path in preflight_paths:
        report = load_json(path)
        if not isinstance(report, dict):
            fail(f"preflight artifact is not an object: {path.relative_to(run_dir)}")
        item = {
            "path": str(path.relative_to(run_dir)),
            "ok": bool(report.get("ok")),
            "entry": report.get("entry"),
            "delivery": report.get("delivery"),
        }
        reports.append(item)
        if item["ok"] and (delivery == "offline" or report.get("delivery") == delivery):
            accepted.append(item)

    if not accepted:
        fail(f"no ok preflight artifact found for delivery={delivery}")
    return {"ok": True, "accepted": accepted, "reports": reports}


def validate_media(run_dir: Path, threshold_pct: float) -> dict[str, Any]:
    media_path = run_dir / "metadata" / "media_validation.json"
    media = load_json(media_path)
    items = media.get("items")
    if not isinstance(items, dict) or not items:
        fail("media_validation.json has no items")
    selected = []
    for name, item in items.items():
        if not isinstance(item, dict):
            fail(f"media validation item is not an object: {name}")
        drift_ratio = item.get("drift_ratio")
        if drift_ratio is None:
            fail(f"media drift_ratio missing for {name}")
        drift_pct = float(str(drift_ratio)) * 100
        if drift_pct > threshold_pct:
            fail(f"media drift too high for {name}: {drift_pct:.2f}% > {threshold_pct:.2f}%")
        selected.append({"name": name, "drift_pct": drift_pct})
    return {"ok": True, "items": selected}


def validate_transcript(run_dir: Path, threshold_pct: float, threshold_seconds: float) -> dict[str, Any]:
    selection_path = run_dir / "transcript" / "transcript_final_selection.json"
    selected_name: object | None = None
    if selection_path.exists():
        selection = load_json(selection_path)
        if not selection.get("ok"):
            fail("transcript_final_selection.json is not ok")
        attempts = selection.get("attempts")
        if not isinstance(attempts, list) or not attempts:
            fail("transcript_final_selection.json has no attempts")
        selected_name = selection.get("selected_attempt")
        selected = next((item for item in attempts if isinstance(item, dict) and item.get("attempt") == selected_name), None)
        if selected is None and len(attempts) == 1 and isinstance(attempts[0], dict) and attempts[0].get("ok"):
            selected = attempts[0]
        if selected is None:
            fail("selected transcript attempt is not present in attempts")
    else:
        candidates = [
            run_dir / "transcript" / "transcript_no_vad_validation.json",
            run_dir / "transcript" / "transcript_validation.json",
        ]
        selected = None
        for candidate in candidates:
            if candidate.exists():
                qa = load_json(candidate)
                if isinstance(qa, dict) and qa.get("ok"):
                    selected = qa
                    break
        if selected is None:
            fail("no accepted transcript validation artifact found")
    if selected is None:
        fail("no selected transcript validation available")
    assert selected is not None
    if not isinstance(selected, dict):
        fail("selected transcript validation is not an object")
    if not isinstance(selected_name, str):
        selected_name = None

    drift_pct = selected.get("coverage_drift_pct")
    if drift_pct is None:
        fail("accepted transcript validation has no coverage_drift_pct")
    drift_pct_value = float(str(drift_pct))
    if drift_pct_value > threshold_pct:
        fail(f"accepted transcript drift too high: {drift_pct_value:.2f}% > {threshold_pct:.2f}%")
    drift_seconds = selected.get("coverage_drift_seconds")
    if drift_seconds is None:
        fail("accepted transcript validation has no coverage_drift_seconds")
    drift_seconds_value = float(str(drift_seconds))
    if drift_seconds_value > threshold_seconds:
        fail(
            f"accepted transcript drift too high: {drift_seconds_value:.2f}s > {threshold_seconds:.2f}s"
        )
    selected_attempt = selected.get("attempt") or selected_name
    return {
        "ok": True,
        "selected_attempt": selected_attempt,
        "coverage_drift_pct": drift_pct_value,
        "coverage_drift_seconds": drift_seconds_value,
    }


def validate_frame_evidence(run_dir: Path, required: bool) -> dict[str, Any]:
    evidence_path = run_dir / "frames" / "frame_evidence.json"
    if not evidence_path.exists():
        if required:
            fail("missing deterministic frame evidence artifact: frames/frame_evidence.json")
        return {"ok": True, "required": False, "present": False}

    evidence = load_json(evidence_path)
    if not isinstance(evidence, dict):
        fail("frame_evidence.json is not an object")
    if evidence.get("mode") != "deterministic_frame_evidence":
        fail("frame_evidence.json was not produced by deterministic frame evidence workflow")
    if evidence.get("remote_vision_used") is not False:
        fail("frame evidence must not depend on remote vision review by default")
    if not evidence.get("ok"):
        fail("frame_evidence.json is not ok")
    chapters = evidence.get("chapters")
    if not isinstance(chapters, list) or not chapters:
        fail("frame_evidence.json has no chapter frame records")
    selected = []
    for chapter in chapters:
        if not isinstance(chapter, dict):
            fail("frame evidence chapter record is not an object")
        frame = chapter.get("selected_frame")
        if not isinstance(frame, str) or not frame:
            fail("frame evidence chapter missing selected_frame")
        frame_path = run_dir / frame
        if not frame_path.exists() or frame_path.stat().st_size <= 0:
            fail(f"selected frame file missing or empty: {frame}")
        stats = chapter.get("stats")
        if not isinstance(stats, dict):
            fail(f"selected frame has no local stats: {frame}")
        if stats.get("blankish"):
            fail(f"selected frame is blankish by local stats: {frame}")
        selected.append(
            {
                "frame": frame,
                "score": chapter.get("score"),
                "stddev": stats.get("stddev"),
                "edge_score": stats.get("edge_score"),
            }
        )
    return {"ok": True, "required": required, "present": True, "count": len(selected), "frames": selected}


def find_presentation_input(run_dir: Path, explicit_input: str) -> Path | None:
    if explicit_input:
        return Path(explicit_input).expanduser().resolve()
    candidates = [
        run_dir / "feishu" / "fetch_result.json",
        run_dir / "feishu" / "fetch_result.xml",
        run_dir / "doc" / "feishu_summary.xml",
    ]
    return next((path for path in candidates if path.exists()), None)


def validate_presentation_contract(path: Path, readback: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        fail(f"presentation input does not exist: {path}")
    content = load_content(path)
    expected_chapters = readback.get("chapter_heading_count")
    if not isinstance(expected_chapters, int):
        expected_chapters = None
    expected_whiteboards = readback.get("whiteboard_token_count")
    if not isinstance(expected_whiteboards, int):
        expected_whiteboards = None
    report: dict[str, Any] = {"ok": True, "input": str(path)}
    report.update(assert_top_structure(content))
    report.update(assert_summary_callout(content))
    report.update(assert_chapter_metadata(content, expected_chapters))
    report.update(assert_visual_blocks(content, expected_whiteboards))
    report.update(assert_no_quality_leak(content))
    report.update(assert_no_type_decision_section(content))
    return report


def validate_feishu(run_dir: Path, require_presentation_contract: bool, presentation_input: str) -> dict[str, Any]:
    for relative in REQUIRED_FEISHU_FILES:
        if not (run_dir / relative).exists():
            fail(f"missing Feishu artifact: {relative}")
    delivery = load_json(run_dir / "feishu" / "delivery_record.json")
    readback = load_json(run_dir / "feishu" / "readback_verification.json")
    if not readback.get("ok"):
        fail("readback_verification.json is not ok")
    if not delivery.get("doc_url"):
        fail("delivery_record.json has no doc_url")
    if not delivery.get("wiki_category_decision"):
        fail("delivery_record.json has no wiki_category_decision")
    quality = delivery.get("quality_record")
    if not isinstance(quality, dict):
        fail("delivery_record.json has no quality_record object")
    for key, value in quality.items():
        if value is None:
            fail(f"delivery quality_record field is null: {key}")
    result: dict[str, Any] = {"ok": True, "doc_url": delivery.get("doc_url"), "readback": readback}
    presentation_path = find_presentation_input(run_dir, presentation_input)
    if presentation_path is None:
        if require_presentation_contract:
            fail("missing presentation input: expected feishu/fetch_result.json or doc/feishu_summary.xml")
    else:
        result["presentation_contract"] = validate_presentation_contract(presentation_path, readback)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate a video-summary run directory")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--delivery", choices=["offline", "feishu"], default="feishu")
    parser.add_argument("--media-threshold-pct", type=float, default=5.0)
    parser.add_argument("--transcript-threshold-pct", type=float, default=5.0)
    parser.add_argument("--transcript-threshold-seconds", type=float, default=8.0)
    parser.add_argument(
        "--require-frame-evidence",
        action="store_true",
        help="Require frames/frame_evidence.json from scripts/select_frame_evidence.py",
    )
    parser.add_argument(
        "--require-presentation-contract",
        action="store_true",
        help="Require Feishu XML/fetch presentation contract validation",
    )
    parser.add_argument(
        "--presentation-input",
        default="",
        help="Optional rendered XML or lark-cli docs +fetch JSON path for presentation validation",
    )
    parser.add_argument("--output", default="")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    run_dir = Path(args.run_dir).expanduser().resolve()
    if not run_dir.exists():
        fail(f"run dir does not exist: {run_dir}")

    report = {
        "ok": True,
        "run_dir": str(run_dir),
        "delivery": args.delivery,
        "preflight": validate_preflight(run_dir, args.delivery),
        "media": validate_media(run_dir, args.media_threshold_pct),
        "transcript": validate_transcript(
            run_dir,
            args.transcript_threshold_pct,
            args.transcript_threshold_seconds,
        ),
        "frame_evidence": validate_frame_evidence(run_dir, args.require_frame_evidence),
    }
    if args.delivery == "feishu":
        report["feishu"] = validate_feishu(run_dir, args.require_presentation_contract, args.presentation_input)

    output = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(output + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
