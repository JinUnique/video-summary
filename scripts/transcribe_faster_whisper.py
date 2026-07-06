#!/usr/bin/env python3
"""Run faster-whisper transcription with coverage QA and no-VAD fallback.

This script is run-scoped: pass a run directory containing media files. It writes
transcript artifacts under <run>/transcript and never hard-codes a single BV/run.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

AUDIO_CANDIDATE_NAMES = (
    "audio_16k_mono.wav",
    "audio_best.m4s",
    "audio_best.m4a",
    "audio.m4a",
    "audio.wav",
)


@dataclass(frozen=True)
class TranscriptionAttempt:
    name: str
    vad_filter: bool
    condition_on_previous_text: bool | None = None
    no_speech_threshold: float | None = None
    log_prob_threshold: float | None = None
    compression_ratio_threshold: float | None = None


def ffprobe_duration(path: Path) -> float:
    if not shutil.which("ffprobe"):
        raise SystemExit("ffprobe is required for ASR coverage QA")
    raw = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        text=True,
    ).strip()
    return float(raw)


def select_audio(run_dir: Path, explicit_audio: str | None) -> Path:
    if explicit_audio:
        path = Path(explicit_audio).expanduser()
        if not path.is_absolute():
            path = (Path.cwd() / path).resolve()
        if not path.exists():
            raise SystemExit(f"audio file not found: {path}")
        return path

    media_dir = run_dir / "media"
    candidates = [media_dir / name for name in AUDIO_CANDIDATE_NAMES]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    searched = ", ".join(str(path.relative_to(run_dir)) for path in candidates)
    raise SystemExit(f"no audio candidate found under {media_dir}; searched: {searched}")


def try_import_faster_whisper() -> Any:
    try:
        from faster_whisper import WhisperModel  # type: ignore[import-not-found]
    except ImportError as exc:
        raise SystemExit(
            "faster_whisper is not installed in this Python. Use the repo preflight first, then create a repo-local env: "
            "python3 -m venv .venv && .venv/bin/python -m pip install faster-whisper==1.2.1"
        ) from exc
    return WhisperModel


def transcribe_attempt(
    *,
    WhisperModel: Any,
    attempt: TranscriptionAttempt,
    audio: Path,
    out_dir: Path,
    model_name: str,
    language: str,
    beam_size: int,
    device: str,
    compute_type: str,
    threshold_pct: float,
    threshold_seconds: float,
    dry_run: bool,
) -> dict[str, Any]:
    suffix = "no-vad" if not attempt.vad_filter else "vad"
    dry_prefix = "dry_run." if dry_run else ""
    out_json = out_dir / f"transcript.{dry_prefix}{suffix}.faster-whisper.json"
    out_txt = out_dir / f"transcript.{dry_prefix}{suffix}.faster-whisper.txt"
    qa_json = out_dir / f"transcript_{dry_prefix}{suffix.replace('-', '_')}_validation.json"

    audio_duration = ffprobe_duration(audio)
    if dry_run:
        qa = {
            "ok": True,
            "dry_run": True,
            "attempt": attempt.name,
            "model": model_name,
            "audio": str(audio),
            "audio_duration": audio_duration,
            "vad_filter": attempt.vad_filter,
            "threshold_pct": threshold_pct,
            "threshold_seconds": threshold_seconds,
        }
        qa_json.write_text(json.dumps(qa, ensure_ascii=False, indent=2), encoding="utf-8")
        return qa

    model = WhisperModel(model_name, device=device, compute_type=compute_type)
    kwargs: dict[str, Any] = {
        "language": language,
        "vad_filter": attempt.vad_filter,
        "beam_size": beam_size,
        "word_timestamps": False,
    }
    for key in (
        "condition_on_previous_text",
        "no_speech_threshold",
        "log_prob_threshold",
        "compression_ratio_threshold",
    ):
        value = getattr(attempt, key)
        if value is not None:
            kwargs[key] = value

    segments_iter, info = model.transcribe(str(audio), **kwargs)
    segments: list[dict[str, Any]] = []
    for segment in segments_iter:
        text = " ".join(segment.text.split())
        if not text:
            continue
        segments.append(
            {
                "id": segment.id,
                "start": float(segment.start),
                "end": float(segment.end),
                "text": text,
            }
        )

    last_end = segments[-1]["end"] if segments else 0.0
    drift = abs(audio_duration - last_end)
    drift_pct = drift / audio_duration * 100 if audio_duration else None
    qa = {
        "ok": bool(segments)
        and drift_pct is not None
        and drift_pct <= threshold_pct
        and drift <= threshold_seconds,
        "attempt": attempt.name,
        "model": model_name,
        "language": getattr(info, "language", None),
        "language_probability": getattr(info, "language_probability", None),
        "audio": str(audio),
        "audio_duration": audio_duration,
        "segment_count": len(segments),
        "last_segment_end": last_end,
        "coverage_drift_seconds": drift,
        "coverage_drift_pct": drift_pct,
        "threshold_pct": threshold_pct,
        "threshold_seconds": threshold_seconds,
        "vad_filter": attempt.vad_filter,
        "device": device,
        "compute_type": compute_type,
    }
    out_json.write_text(json.dumps({"info": qa, "segments": segments}, ensure_ascii=False, indent=2), encoding="utf-8")
    out_txt.write_text(
        "\n".join(f"[{s['start']:07.2f}-{s['end']:07.2f}] {s['text']}" for s in segments),
        encoding="utf-8",
    )
    qa_json.write_text(json.dumps(qa, ensure_ascii=False, indent=2), encoding="utf-8")
    return qa


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Transcribe a video-summary run with faster-whisper and QA")
    parser.add_argument("--run-dir", required=True, help="Run directory containing media/ and transcript/")
    parser.add_argument("--audio", default="", help="Optional explicit audio file")
    parser.add_argument("--model", default="large-v3-turbo")
    parser.add_argument("--language", default="zh")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--compute-type", default="int8")
    parser.add_argument("--beam-size", type=int, default=5)
    parser.add_argument("--threshold-pct", type=float, default=5.0)
    parser.add_argument(
        "--threshold-seconds",
        type=float,
        default=8.0,
        help="Maximum accepted end-coverage drift in seconds; prevents short videos from passing with a missing tail",
    )
    parser.add_argument("--no-vad-first", action="store_true", help="Skip the VAD-first attempt")
    parser.add_argument("--dry-run", action="store_true", help="Validate paths/imports/ffprobe without loading the model")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    run_dir = Path(args.run_dir).expanduser().resolve()
    if not run_dir.exists():
        raise SystemExit(f"run directory not found: {run_dir}")
    out_dir = run_dir / "transcript"
    out_dir.mkdir(parents=True, exist_ok=True)
    audio = select_audio(run_dir, args.audio or None)
    WhisperModel = try_import_faster_whisper()

    attempts = []
    if not args.no_vad_first:
        attempts.append(TranscriptionAttempt(name="vad", vad_filter=True))
    attempts.append(
        TranscriptionAttempt(
            name="no_vad_fallback",
            vad_filter=False,
            condition_on_previous_text=False,
            no_speech_threshold=0.8,
            log_prob_threshold=-1.0,
            compression_ratio_threshold=2.4,
        )
    )

    results = []
    selected: dict[str, Any] | None = None
    for attempt in attempts:
        qa = transcribe_attempt(
            WhisperModel=WhisperModel,
            attempt=attempt,
            audio=audio,
            out_dir=out_dir,
            model_name=args.model,
            language=args.language,
            beam_size=args.beam_size,
            device=args.device,
            compute_type=args.compute_type,
            threshold_pct=args.threshold_pct,
            threshold_seconds=args.threshold_seconds,
            dry_run=args.dry_run,
        )
        results.append(qa)
        if qa.get("ok"):
            selected = qa
            break

    summary = {
        "ok": selected is not None,
        "run_dir": str(run_dir),
        "audio": str(audio),
        "selected_attempt": selected.get("attempt") if selected else None,
        "attempts": results,
    }
    selection_name = "transcript_final_selection.dry_run.json" if args.dry_run else "transcript_final_selection.json"
    (out_dir / selection_name).write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
