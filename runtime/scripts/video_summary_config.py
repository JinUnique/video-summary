#!/usr/bin/env python3
"""Resolve user-owned configuration outside an installed skill or repository."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Mapping


def config_path(explicit: str = '', *, environ: Mapping[str, str] | None = None,
                home: Path | None = None) -> tuple[Path | None, str]:
    env = os.environ if environ is None else environ
    if explicit:
        return Path(explicit).expanduser(), 'explicit'
    if env.get('VIDEO_SUMMARY_CONFIG'):
        return Path(env['VIDEO_SUMMARY_CONFIG']).expanduser(), 'environment'
    user_home = Path.home() if home is None else home
    base = Path(env['XDG_CONFIG_HOME']).expanduser() if env.get('XDG_CONFIG_HOME') else user_home / '.config'
    candidate = base / 'video-summary/config.json'
    return (candidate, 'user_default') if candidate.is_file() else (None, 'missing')


def load_config(explicit: str = '') -> tuple[dict, str]:
    path, origin = config_path(explicit)
    if path is None:
        return {}, origin
    payload = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(payload, dict):
        raise ValueError('configuration must be a JSON object')
    if 'feishu' in payload and not isinstance(payload['feishu'], dict):
        raise ValueError('feishu configuration must be an object')
    return payload, origin
