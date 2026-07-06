#!/usr/bin/env python3
"""Preflight checks for the repo-backed video-summary workflow.

The script is intentionally read-only by default. It checks the active entry
context, local tools, ASR environment, and Feishu Wiki/lark-cli command shape so
an agent can fail early with a readable reason instead of discovering gaps mid-run.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ENV_EXAMPLE = ROOT / ".env.example"
DEFAULT_ENV_FILE = ROOT / ".env"
BILIBILI_RE = re.compile(r"(bilibili\.com/video/|b23\.tv/|\bBV[0-9A-Za-z]+\b|\bav\d+\b)")
CONFIG_HELP = (
    "Run `python3 scripts/video_summary_preflight.py --init` to create .env from .env.example, "
    "or pass the value explicitly on the command line."
)


def run_command(args: list[str], timeout: int = 20, cwd: Path | None = None) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            args,
            cwd=str(cwd) if cwd else None,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        return {
            "cmd": args,
            "ok": completed.returncode == 0,
            "exit_code": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
    except FileNotFoundError:
        return {"cmd": args, "ok": False, "exit_code": 127, "stdout": "", "stderr": "command not found"}
    except subprocess.TimeoutExpired as exc:
        return {
            "cmd": args,
            "ok": False,
            "exit_code": 124,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or f"timeout after {timeout}s",
        }


def compact_text(value: str, limit: int = 900) -> str:
    value = value.strip()
    if len(value) <= limit:
        return value
    return value[: limit - 20] + "…[truncated]"


def parse_jsonish(stdout: str) -> Any:
    text = stdout.strip()
    for start_char in ("{", "["):
        idx = text.find(start_char)
        if idx >= 0:
            try:
                return json.loads(text[idx:])
            except json.JSONDecodeError:
                continue
    return None


def read_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'\"")
        if key:
            values[key] = value
    return values


def config_value(args: argparse.Namespace, name: str) -> str:
    env_value = os.environ.get(name, "").strip()
    if env_value:
        return env_value
    env_values = getattr(args, "env_values", None)
    if env_values is None:
        env_values = read_env_file(Path(getattr(args, "env_file", DEFAULT_ENV_FILE)))
    return str(env_values.get(name, "")).strip()


def write_initial_env(example_path: Path = ENV_EXAMPLE, destination_path: Path = DEFAULT_ENV_FILE) -> bool:
    if destination_path.exists():
        return False
    if not example_path.exists():
        raise FileNotFoundError(f"missing config template: {example_path}")
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    destination_path.write_text(example_path.read_text(encoding="utf-8"), encoding="utf-8")
    return True


def resolve_wiki_space(
    args: argparse.Namespace,
    errors: list[str],
    warnings: list[str],
) -> str | None:
    space_id = (args.wiki_space or config_value(args, "VIDEO_SUMMARY_WIKI_SPACE_ID")).strip()
    if space_id:
        return space_id
    if args.delivery == "feishu":
        errors.append(
            "Feishu delivery requires a Wiki space id. Set VIDEO_SUMMARY_WIKI_SPACE_ID in .env "
            "or pass --wiki-space <SPACE_ID>. " + CONFIG_HELP
        )
    elif getattr(args, "live_feishu_read", False):
        warnings.append("--live-feishu-read was requested without VIDEO_SUMMARY_WIKI_SPACE_ID or --wiki-space")
    return None


def check_command(name: str, errors: list[str], warnings: list[str], required: bool = True) -> dict[str, Any]:
    path = shutil.which(name)
    result = {"name": name, "path": path, "ok": bool(path)}
    if required and not path:
        errors.append(f"missing required command: {name}")
    elif not required and not path:
        warnings.append(f"optional command unavailable: {name}")
    return result


def check_asr_environment(errors: list[str], warnings: list[str]) -> dict[str, Any]:
    candidates: list[Path] = []
    repo_python = ROOT / ".venv" / "bin" / "python"
    if repo_python.exists():
        candidates.append(repo_python)
    candidates.append(Path(sys.executable))

    probe_code = "import faster_whisper, ctranslate2; print('ok')"
    probes = []
    for candidate in dict.fromkeys(candidates):
        probe = run_command([str(candidate), "-c", probe_code], timeout=20)
        probes.append(
            {
                "python": str(candidate),
                "ok": probe["ok"],
                "stderr": compact_text(probe["stderr"], 400),
            }
        )
        if probe["ok"]:
            return {"ok": True, "python": str(candidate), "probes": probes}

    errors.append(
        "ASR dependency missing: faster_whisper/ctranslate2 not importable from .venv or current Python. "
        "Create a repo-local env before running ASR: python3 -m venv .venv && "
        ".venv/bin/python -m pip install faster-whisper==1.2.1"
    )
    warnings.append("Do not install ASR packages into system Python when a repo-local .venv can be used.")
    return {"ok": False, "python": None, "probes": probes}


def check_lark_cli(args: argparse.Namespace, errors: list[str], warnings: list[str]) -> dict[str, Any]:
    result: dict[str, Any] = {"required": args.delivery == "feishu", "checks": {}}
    command_info = check_command("lark-cli", errors, warnings, required=args.delivery == "feishu")
    result["command"] = command_info
    if not command_info["ok"]:
        return result

    env = os.environ.copy()
    env.setdefault("LARK_CLI_NO_PROXY", "1")

    def run_lark(parts: list[str], timeout: int = 25) -> dict[str, Any]:
        try:
            completed = subprocess.run(
                ["lark-cli", *parts],
                cwd=str(ROOT),
                env=env,
                text=True,
                capture_output=True,
                timeout=timeout,
                check=False,
            )
            return {
                "ok": completed.returncode == 0,
                "exit_code": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
            }
        except subprocess.TimeoutExpired as exc:
            return {"ok": False, "exit_code": 124, "stdout": exc.stdout or "", "stderr": exc.stderr or "timeout"}

    version = run_lark(["--version"])
    result["version"] = compact_text(version["stdout"] or version["stderr"], 300)

    help_specs = {
        "docs_create": ["docs", "+create", "--help"],
        "docs_update": ["docs", "+update", "--help"],
        "docs_media_insert": ["docs", "+media-insert", "--help"],
        "docs_whiteboard_update": ["docs", "+whiteboard-update", "--help"],
        "wiki_nodes_list": ["wiki", "nodes", "list", "--help"],
        "wiki_node_create": ["wiki", "+node-create", "--help"],
    }
    for key, parts in help_specs.items():
        help_result = run_lark(parts)
        text = help_result["stdout"] + help_result["stderr"]
        result["checks"][key] = {
            "ok": help_result["ok"],
            "has_markdown": "--markdown" in text,
            "has_mode": "--mode" in text,
            "has_content": "--content" in text,
            "has_command": "--command" in text,
            "has_parent_token": "--parent-token" in text,
            "has_file": "--file" in text,
            "has_format": "--format" in text,
            "sample": compact_text(text, 500),
        }
        if args.delivery == "feishu" and not help_result["ok"]:
            errors.append(f"lark-cli help failed for {' '.join(parts)}")

    if args.live_feishu_read:
        space_id = getattr(args, "resolved_wiki_space", None)
        if not space_id:
            errors.append("live Feishu read requires VIDEO_SUMMARY_WIKI_SPACE_ID or --wiki-space")
            return result
        params = json.dumps({"space_id": space_id, "page_size": 50}, ensure_ascii=False)
        list_result = run_lark(["wiki", "nodes", "list", "--as", "user", "--params", params, "--format", "json"], timeout=40)
        parsed = parse_jsonish(list_result["stdout"])
        item_count = None
        if isinstance(parsed, dict):
            data = parsed.get("data") if isinstance(parsed.get("data"), dict) else parsed
            items = data.get("items") if isinstance(data, dict) else None
            if isinstance(items, list):
                item_count = len(items)
        result["wiki_read"] = {
            "ok": list_result["ok"] and item_count is not None,
            "space_id": space_id,
            "item_count": item_count,
            "stderr": compact_text(list_result["stderr"], 500),
        }
        if args.delivery == "feishu" and not result["wiki_read"]["ok"]:
            errors.append("cannot read target Feishu Wiki top-level nodes with lark-cli as user")

    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Preflight checks for video-summary runs")
    parser.add_argument("--init", action="store_true", help="Create .env from .env.example and exit")
    parser.add_argument("--init-output", default=str(DEFAULT_ENV_FILE), help="Where --init writes the config file")
    parser.add_argument("--env-file", default=str(DEFAULT_ENV_FILE), help="Optional .env file to read")
    parser.add_argument("--entry", choices=["terminal", "feishu"], default="")
    parser.add_argument("--url", default="", help="Video URL or BV/av id for trigger validation")
    parser.add_argument("--delivery", choices=["offline", "feishu"], default="feishu")
    parser.add_argument("--wiki-space", default="", help="Feishu/Lark Wiki space id; overrides VIDEO_SUMMARY_WIKI_SPACE_ID")
    parser.add_argument("--require-asr", action="store_true", help="Require faster-whisper availability")
    parser.add_argument("--live-feishu-read", action="store_true", help="Read-only check of current Wiki top-level nodes")
    parser.add_argument("--output", default="", help="Optional path for JSON report")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.init:
        destination = Path(args.init_output)
        created = write_initial_env(ENV_EXAMPLE, destination)
        print(
            json.dumps(
                {
                    "ok": True,
                    "created": created,
                    "path": str(destination),
                    "message": "created config file" if created else "config file already exists; left unchanged",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    if not args.entry:
        parser.error("--entry is required unless --init is used")

    args.env_values = read_env_file(Path(args.env_file))
    errors: list[str] = []
    warnings: list[str] = []
    args.resolved_wiki_space = resolve_wiki_space(args, errors, warnings)

    report: dict[str, Any] = {
        "ok": False,
        "entry": args.entry,
        "delivery": args.delivery,
        "repo_root": str(ROOT),
        "cwd": os.getcwd(),
        "config": {
            "env_file": args.env_file,
            "wiki_space_configured": bool(args.resolved_wiki_space),
            "feishu_group_configured": bool(config_value(args, "VIDEO_SUMMARY_FEISHU_GROUP_NAME")),
        },
        "warnings": warnings,
        "errors": errors,
        "checks": {},
    }

    if args.url and not BILIBILI_RE.search(args.url):
        warnings.append("video trigger does not look like a Bilibili URL/BV/av id; generic video handling may need manual metadata rules")

    if args.entry == "terminal" and Path.cwd().resolve() != ROOT:
        warnings.append(f"terminal entry is not running from repo root; use absolute repo paths or cd {ROOT}")
    if args.entry == "feishu":
        agents = ROOT / "AGENTS.md"
        if not agents.exists():
            warnings.append("AGENTS.md is missing; skipping optional Feishu entry guidance check")
        else:
            group_name = config_value(args, "VIDEO_SUMMARY_FEISHU_GROUP_NAME")
            text = agents.read_text(encoding="utf-8")
            if group_name and group_name not in text:
                warnings.append("configured VIDEO_SUMMARY_FEISHU_GROUP_NAME was not found in AGENTS.md; verify current lane before writing")
            elif not group_name:
                warnings.append("VIDEO_SUMMARY_FEISHU_GROUP_NAME is unset; skipping optional Feishu group-name check")

    report["checks"]["commands"] = [
        check_command("ffmpeg", errors, warnings),
        check_command("ffprobe", errors, warnings),
        check_command("yt-dlp", errors, warnings, required=False),
        check_command("tesseract", errors, warnings, required=False),
    ]

    if args.require_asr:
        report["checks"]["asr"] = check_asr_environment(errors, warnings)

    if args.delivery == "feishu":
        report["checks"]["lark_cli"] = check_lark_cli(args, errors, warnings)

    report["ok"] = not errors
    output = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output + "\n", encoding="utf-8")
    print(output)
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
