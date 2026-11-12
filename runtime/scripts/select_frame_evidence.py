#!/usr/bin/env python3
"""Select deterministic video-frame evidence for a video-summary run.

This script implements the reproducible evidence layer. It uses ffmpeg/ffprobe
for frame extraction plus local pixel statistics, with optional local tesseract
OCR. Model-assisted visual understanding belongs after this script has produced
`frames/frame_evidence.json`; it must not choose or validate evidence frames.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, NoReturn

ROOT = Path(__file__).resolve().parents[1]
VIDEO_PATTERNS = (
    "media/video_merged.mp4",
    "media/merged.mp4",
    "media/video.mp4",
    "media/*.mp4",
    "media/*.mkv",
    "media/*.webm",
    "media/video_best.m4s",
)
CHAPTER_KEYS = ("chapters", "sections", "items")
START_KEYS = ("start_seconds", "start_second", "start_s", "start", "start_time", "from")
END_KEYS = ("end_seconds", "end_second", "end_s", "end", "end_time", "to")
TITLE_KEYS = ("title", "heading", "name", "label", "summary")


def fail(message: str) -> NoReturn:
    raise SystemExit(f"FAIL: {message}")


def run_command(args: list[str], timeout: int = 60, input_data: bytes | None = None) -> subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(
            args,
            input=input_data,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        fail(f"missing command: {args[0]}")
    except subprocess.TimeoutExpired as exc:
        fail(f"command timed out after {timeout}s: {' '.join(args)}")
    raise AssertionError("unreachable")


def require_command(name: str) -> str:
    path = shutil.which(name)
    if not path:
        fail(f"missing required command: {name}")
    return path


def compact(value: str, limit: int = 500) -> str:
    value = value.strip()
    return value if len(value) <= limit else value[: limit - 20] + "…[truncated]"


def ffprobe_video(path: Path) -> dict[str, Any]:
    require_command("ffprobe")
    completed = run_command(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration:stream=codec_type,width,height,duration",
            "-of",
            "json",
            str(path),
        ],
        timeout=30,
    )
    if completed.returncode != 0:
        fail(f"ffprobe failed for {path}: {compact(completed.stderr.decode('utf-8', 'replace'))}")
    data = json.loads(completed.stdout.decode("utf-8"))
    duration = float(data.get("format", {}).get("duration") or 0)
    video_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), {})
    width = int(video_stream.get("width") or 0)
    height = int(video_stream.get("height") or 0)
    if duration <= 0:
        fail(f"could not determine video duration for {path}")
    return {"duration": duration, "width": width, "height": height, "raw": data}


def discover_video(run_dir: Path) -> Path:
    for pattern in VIDEO_PATTERNS:
        matches = sorted(run_dir.glob(pattern))
        for match in matches:
            if match.is_file() and match.stat().st_size > 0:
                return match
    fail(f"no usable video file found under {run_dir}/media; pass --video explicitly")


def parse_time(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return None
    if re.fullmatch(r"\d+(\.\d+)?", text):
        return float(text)
    parts = text.split(":")
    if len(parts) in {2, 3}:
        try:
            numbers = [float(part) for part in parts]
        except ValueError:
            return None
        if len(numbers) == 2:
            minutes, seconds = numbers
            return minutes * 60 + seconds
        hours, minutes, seconds = numbers
        return hours * 3600 + minutes * 60 + seconds
    return None


def first_value(mapping: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in mapping:
            return mapping[key]
    return None


def flatten_chapter_source(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if not isinstance(data, dict):
        return []
    for key in CHAPTER_KEYS:
        value = data.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    assets = data.get("assets")
    if isinstance(assets, dict):
        return flatten_chapter_source(assets)
    return []


def normalize_chapters(raw: list[dict[str, Any]], duration: float) -> list[dict[str, Any]]:
    chapters: list[dict[str, Any]] = []
    for index, item in enumerate(raw, start=1):
        start = parse_time(first_value(item, START_KEYS))
        end = parse_time(first_value(item, END_KEYS))
        title_value = first_value(item, TITLE_KEYS)
        if start is None:
            timestamp = item.get("timestamp") or item.get("time")
            start = parse_time(timestamp)
        if start is None:
            continue
        start = max(0.0, min(float(start), duration))
        title = str(title_value or f"chapter-{index:02d}").strip() or f"chapter-{index:02d}"
        chapters.append({"index": index, "title": title, "start": start, "end": end})

    chapters.sort(key=lambda chapter: chapter["start"])
    for offset, chapter in enumerate(chapters):
        next_start = chapters[offset + 1]["start"] if offset + 1 < len(chapters) else duration
        end = chapter.get("end")
        if end is None:
            end = next_start
        end = max(chapter["start"] + 0.25, min(float(end), duration))
        chapter["end"] = end
        chapter["index"] = offset + 1
    return chapters


def fallback_chapters(duration: float, count: int) -> list[dict[str, Any]]:
    count = max(1, count)
    span = duration / count
    chapters = []
    for idx in range(count):
        start = idx * span
        end = duration if idx + 1 == count else (idx + 1) * span
        chapters.append({"index": idx + 1, "title": f"chapter-{idx + 1:02d}", "start": start, "end": end})
    return chapters


def load_chapters(run_dir: Path, explicit_path: str, duration: float, fallback_count: int) -> tuple[list[dict[str, Any]], str]:
    paths: list[Path] = []
    if explicit_path:
        paths.append(Path(explicit_path).expanduser())
    else:
        paths.extend(
            [
                run_dir / "doc" / "summary_assets.json",
                run_dir / "metadata" / "chapters.json",
                run_dir / "doc" / "chapters.json",
            ]
        )
    for path in paths:
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        chapters = normalize_chapters(flatten_chapter_source(data), duration)
        if chapters:
            return chapters, str(path)
    return fallback_chapters(duration, fallback_count), "fallback_even_windows"


def candidate_times(chapter: dict[str, Any], count: int) -> list[float]:
    start = float(chapter["start"])
    end = float(chapter["end"])
    if end <= start:
        return [start]
    span = end - start
    if span <= 4:
        return [start + span / 2]
    usable_start = start + min(2.0, span * 0.15)
    usable_end = end - min(2.0, span * 0.15)
    if usable_end <= usable_start:
        return [start + span / 2]
    count = max(1, count)
    if count == 1:
        return [usable_start + (usable_end - usable_start) / 2]
    return [usable_start + (usable_end - usable_start) * i / (count - 1) for i in range(count)]


def extract_ppm(video: Path, seconds: float, width: int) -> bytes:
    require_command("ffmpeg")
    completed = run_command(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            f"{seconds:.3f}",
            "-i",
            str(video),
            "-frames:v",
            "1",
            "-vf",
            f"scale={width}:-1",
            "-f",
            "image2pipe",
            "-vcodec",
            "ppm",
            "-",
        ],
        timeout=45,
    )
    if completed.returncode != 0 or not completed.stdout:
        raise RuntimeError(compact(completed.stderr.decode("utf-8", "replace")))
    return completed.stdout


def read_token(data: bytes, index: int) -> tuple[bytes, int]:
    while index < len(data):
        char = data[index:index + 1]
        if char == b"#":
            while index < len(data) and data[index:index + 1] not in b"\r\n":
                index += 1
        elif char in b" \t\r\n":
            index += 1
        else:
            break
    start = index
    while index < len(data) and data[index:index + 1] not in b" \t\r\n":
        index += 1
    return data[start:index], index


def parse_ppm(data: bytes) -> tuple[int, int, bytes]:
    index = 0
    magic, index = read_token(data, index)
    if magic != b"P6":
        raise ValueError("expected P6 PPM")
    width_token, index = read_token(data, index)
    height_token, index = read_token(data, index)
    maxval_token, index = read_token(data, index)
    width = int(width_token)
    height = int(height_token)
    maxval = int(maxval_token)
    if maxval != 255:
        raise ValueError(f"unsupported PPM maxval: {maxval}")
    if index < len(data) and data[index:index + 1] in b" \t\r\n":
        index += 1
    pixels = data[index:]
    expected = width * height * 3
    if len(pixels) < expected:
        raise ValueError(f"PPM pixel data too short: {len(pixels)} < {expected}")
    return width, height, pixels[:expected]


def frame_stats(ppm_data: bytes) -> dict[str, Any]:
    width, height, pixels = parse_ppm(ppm_data)
    count = width * height
    luminance = [0] * count
    sum_y = 0
    sum_y2 = 0
    black = 0
    white = 0
    red_sum = 0
    green_sum = 0
    blue_sum = 0
    for pixel_index in range(count):
        offset = pixel_index * 3
        red = pixels[offset]
        green = pixels[offset + 1]
        blue = pixels[offset + 2]
        red_sum += red
        green_sum += green
        blue_sum += blue
        y = (77 * red + 150 * green + 29 * blue) >> 8
        luminance[pixel_index] = y
        sum_y += y
        sum_y2 += y * y
        if y < 16:
            black += 1
        if y > 240:
            white += 1
    mean = sum_y / count
    variance = max(0.0, (sum_y2 / count) - mean * mean)
    stddev = math.sqrt(variance)
    horizontal = 0
    horizontal_count = 0
    vertical = 0
    vertical_count = 0
    for row in range(height):
        row_start = row * width
        for col in range(width - 1):
            horizontal += abs(luminance[row_start + col] - luminance[row_start + col + 1])
            horizontal_count += 1
    for row in range(height - 1):
        row_start = row * width
        next_start = (row + 1) * width
        for col in range(width):
            vertical += abs(luminance[row_start + col] - luminance[next_start + col])
            vertical_count += 1
    edge_score = (horizontal / max(1, horizontal_count) + vertical / max(1, vertical_count)) / 2
    red_mean = red_sum / count
    green_mean = green_sum / count
    blue_mean = blue_sum / count
    color_spread = max(red_mean, green_mean, blue_mean) - min(red_mean, green_mean, blue_mean)
    black_ratio = black / count
    white_ratio = white / count
    blankish = stddev < 8 or black_ratio > 0.90 or white_ratio > 0.96
    score = stddev * 1.15 + edge_score * 1.45 + color_spread * 0.08
    if black_ratio > 0.45:
        score -= (black_ratio - 0.45) * 80
    if white_ratio > 0.70:
        score -= (white_ratio - 0.70) * 80
    if blankish:
        score -= 100
    return {
        "width": width,
        "height": height,
        "stddev": round(stddev, 3),
        "edge_score": round(edge_score, 3),
        "black_ratio": round(black_ratio, 5),
        "white_ratio": round(white_ratio, 5),
        "color_spread": round(color_spread, 3),
        "blankish": blankish,
        "base_score": round(score, 3),
    }


def ocr_score(ppm_data: bytes, tesseract_path: str | None, languages: str) -> dict[str, Any]:
    if not tesseract_path:
        return {"available": False, "chars": 0, "score_bonus": 0.0, "sample": ""}
    with tempfile.NamedTemporaryFile(suffix=".ppm") as temp_file:
        temp_file.write(ppm_data)
        temp_file.flush()
        completed = run_command(
            [tesseract_path, temp_file.name, "stdout", "-l", languages, "--psm", "6"],
            timeout=20,
        )
    if completed.returncode != 0:
        return {
            "available": True,
            "ok": False,
            "chars": 0,
            "score_bonus": 0.0,
            "error": compact(completed.stderr.decode("utf-8", "replace"), 200),
            "sample": "",
        }
    text = completed.stdout.decode("utf-8", "replace")
    normalized = re.sub(r"\s+", "", text)
    chars = len(normalized)
    bonus = min(chars, 120) * 0.12
    return {
        "available": True,
        "ok": True,
        "chars": chars,
        "score_bonus": round(bonus, 3),
        "sample": text.strip()[:120],
    }


def slugify(value: str, fallback: str) -> str:
    ascii_text = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    if not ascii_text:
        ascii_text = fallback
    return ascii_text[:50]


def export_jpeg(video: Path, seconds: float, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    completed = run_command(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-ss",
            f"{seconds:.3f}",
            "-i",
            str(video),
            "-frames:v",
            "1",
            "-q:v",
            "1",
            str(output),
        ],
        timeout=45,
    )
    if completed.returncode != 0 or not output.exists() or output.stat().st_size <= 0:
        fail(f"failed to export frame {output}: {compact(completed.stderr.decode('utf-8', 'replace'))}")


def make_contact_sheet(selected_ppms: list[tuple[str, bytes]], output_jpg: Path, columns: int) -> str | None:
    if not selected_ppms:
        return None
    parsed = []
    for label, ppm_data in selected_ppms:
        width, height, pixels = parse_ppm(ppm_data)
        parsed.append((label, width, height, pixels))
    thumb_width = max(item[1] for item in parsed)
    thumb_height = max(item[2] for item in parsed)
    columns = max(1, min(columns, len(parsed)))
    rows = math.ceil(len(parsed) / columns)
    gap = 12
    sheet_width = columns * thumb_width + (columns + 1) * gap
    sheet_height = rows * thumb_height + (rows + 1) * gap
    background = bytes([245, 242, 235])
    sheet = bytearray(background * (sheet_width * sheet_height))
    for idx, (_label, width, height, pixels) in enumerate(parsed):
        row = idx // columns
        col = idx % columns
        left = gap + col * (thumb_width + gap)
        top = gap + row * (thumb_height + gap)
        for y in range(height):
            src_start = y * width * 3
            src_end = src_start + width * 3
            dest_start = ((top + y) * sheet_width + left) * 3
            sheet[dest_start:dest_start + width * 3] = pixels[src_start:src_end]
    ppm_path = output_jpg.with_suffix(".ppm")
    ppm_path.parent.mkdir(parents=True, exist_ok=True)
    ppm_path.write_bytes(f"P6\n{sheet_width} {sheet_height}\n255\n".encode("ascii") + bytes(sheet))
    completed = run_command(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(ppm_path), "-q:v", "2", str(output_jpg)],
        timeout=45,
    )
    if completed.returncode != 0 or not output_jpg.exists():
        return str(ppm_path)
    ppm_path.unlink(missing_ok=True)
    return str(output_jpg)


def relative_to_run(path: Path, run_dir: Path) -> str:
    try:
        return str(path.relative_to(run_dir))
    except ValueError:
        return str(path)


def select_for_chapter(
    video: Path,
    chapter: dict[str, Any],
    frame_dir: Path,
    run_dir: Path,
    candidates_per_chapter: int,
    thumb_width: int,
    ocr_mode: str,
    tesseract_path: str | None,
    tesseract_languages: str,
) -> tuple[dict[str, Any], bytes | None]:
    candidates = []
    errors = []
    for seconds in candidate_times(chapter, candidates_per_chapter):
        try:
            ppm_data = extract_ppm(video, seconds, thumb_width)
            stats = frame_stats(ppm_data)
            candidates.append(
                {
                    "seconds": round(seconds, 3),
                    "stats": stats,
                    "score": float(stats["base_score"]),
                    "ppm": ppm_data,
                    "ocr": {"available": False, "chars": 0, "score_bonus": 0.0, "sample": ""},
                }
            )
        except Exception as exc:
            errors.append({"seconds": round(seconds, 3), "error": str(exc)})
    if not candidates:
        return {
            "index": chapter["index"],
            "title": chapter["title"],
            "start": chapter["start"],
            "end": chapter["end"],
            "ok": False,
            "error": "no extractable candidates",
            "candidate_errors": errors,
        }, None

    candidates.sort(key=lambda item: item["score"], reverse=True)
    should_ocr = ocr_mode == "always" or (ocr_mode == "auto" and bool(tesseract_path))
    if should_ocr:
        for candidate in candidates[: min(3, len(candidates))]:
            ocr = ocr_score(candidate["ppm"], tesseract_path, tesseract_languages)
            candidate["ocr"] = ocr
            candidate["score"] = round(candidate["score"] + float(ocr.get("score_bonus", 0.0)), 3)
        candidates.sort(key=lambda item: item["score"], reverse=True)

    selected = candidates[0]
    index = int(chapter["index"])
    slug = slugify(str(chapter["title"]), f"chapter-{index:02d}")
    output = frame_dir / f"c{index:02d}_{slug}_{int(round(selected['seconds']))}s.jpg"
    export_jpeg(video, float(selected["seconds"]), output)
    output_stat = output.stat()
    selected_stats = selected["stats"]
    ok = not bool(selected_stats.get("blankish")) and output_stat.st_size > 0
    public_candidates = []
    for candidate in candidates:
        public_candidates.append(
            {
                "seconds": candidate["seconds"],
                "score": candidate["score"],
                "stats": candidate["stats"],
                "ocr": candidate["ocr"],
            }
        )
    report = {
        "index": index,
        "title": chapter["title"],
        "start": round(float(chapter["start"]), 3),
        "end": round(float(chapter["end"]), 3),
        "ok": ok,
        "selected_time_seconds": selected["seconds"],
        "selected_frame": relative_to_run(output, run_dir),
        "selected_size_bytes": output_stat.st_size,
        "score": selected["score"],
        "stats": selected_stats,
        "ocr": selected["ocr"],
        "candidate_errors": errors,
        "candidates": public_candidates,
    }
    return report, selected["ppm"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Select deterministic frame evidence for a video-summary run")
    parser.add_argument("--run-dir", required=True, help="Run directory containing media/ and frames/")
    parser.add_argument("--video", default="", help="Explicit video file; defaults to run media discovery")
    parser.add_argument("--chapters", default="", help="Optional JSON chapter/source file")
    parser.add_argument("--fallback-chapters", type=int, default=7, help="Even windows to use when no chapter JSON exists")
    parser.add_argument("--candidates-per-chapter", type=int, default=5)
    parser.add_argument("--thumb-width", type=int, default=320, help="Width for scoring/contact-sheet thumbnails")
    parser.add_argument("--frame-dir", default="", help="Output directory for selected frame JPGs")
    parser.add_argument("--output", default="", help="Output JSON path; defaults to frames/frame_evidence.json")
    parser.add_argument("--contact-sheet", default="", help="Contact sheet path; defaults to frames/contact_sheet.jpg")
    parser.add_argument("--contact-cols", type=int, default=2)
    parser.add_argument("--ocr", choices=["auto", "always", "never"], default="auto")
    parser.add_argument("--tesseract-languages", default="chi_sim+eng")
    parser.add_argument("--dry-run", action="store_true", help="Check dependencies and source discovery without exporting frames")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    run_dir = Path(args.run_dir).expanduser().resolve()
    if not run_dir.exists():
        fail(f"run directory does not exist: {run_dir}")
    require_command("ffmpeg")
    require_command("ffprobe")
    video = Path(args.video).expanduser().resolve() if args.video else discover_video(run_dir)
    if not video.exists():
        fail(f"video file does not exist: {video}")
    probe = ffprobe_video(video)
    chapters, chapter_source = load_chapters(run_dir, args.chapters, float(probe["duration"]), args.fallback_chapters)
    tesseract_path = shutil.which("tesseract")
    if args.ocr == "always" and not tesseract_path:
        fail("--ocr always requested but tesseract is unavailable")
    frame_dir = Path(args.frame_dir).expanduser().resolve() if args.frame_dir else run_dir / "frames" / "evidence"
    output_path = Path(args.output).expanduser().resolve() if args.output else run_dir / "frames" / "frame_evidence.json"
    contact_sheet = Path(args.contact_sheet).expanduser().resolve() if args.contact_sheet else run_dir / "frames" / "contact_sheet.jpg"

    report: dict[str, Any] = {
        "ok": True,
        "mode": "deterministic_frame_evidence",
        "remote_vision_used": False,
        "video": relative_to_run(video, run_dir),
        "video_duration_seconds": round(float(probe["duration"]), 3),
        "video_width": probe.get("width"),
        "video_height": probe.get("height"),
        "chapter_source": chapter_source,
        "chapter_count": len(chapters),
        "tesseract": {"path": tesseract_path, "languages": args.tesseract_languages, "mode": args.ocr},
        "outputs": {
            "frame_dir": relative_to_run(frame_dir, run_dir),
            "manifest": relative_to_run(output_path, run_dir),
            "contact_sheet": relative_to_run(contact_sheet, run_dir),
        },
        "chapters": [],
        "warnings": [],
    }

    if args.ocr != "never" and not tesseract_path:
        report["warnings"].append("tesseract unavailable; scoring uses pixel statistics only")
    if args.dry_run:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        dry_output = output_path.with_name(output_path.stem + ".dry_run" + output_path.suffix)
        dry_output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    selected_ppms: list[tuple[str, bytes]] = []
    for chapter in chapters:
        chapter_report, selected_ppm = select_for_chapter(
            video=video,
            chapter=chapter,
            frame_dir=frame_dir,
            run_dir=run_dir,
            candidates_per_chapter=args.candidates_per_chapter,
            thumb_width=args.thumb_width,
            ocr_mode=args.ocr,
            tesseract_path=tesseract_path,
            tesseract_languages=args.tesseract_languages,
        )
        if not chapter_report.get("ok"):
            report["ok"] = False
        report["chapters"].append(chapter_report)
        if selected_ppm is not None:
            selected_ppms.append((str(chapter_report.get("index")), selected_ppm))

    sheet_path = make_contact_sheet(selected_ppms, contact_sheet, args.contact_cols)
    if sheet_path:
        report["outputs"]["contact_sheet"] = relative_to_run(Path(sheet_path), run_dir)
    else:
        report["warnings"].append("contact sheet could not be generated")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
