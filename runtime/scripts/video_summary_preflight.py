#!/usr/bin/env python3
"""Check this interpreter and explicit delivery settings; offline never calls Lark."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess

from video_summary_config import load_config


def check(args: argparse.Namespace) -> dict:
    errors = []
    warnings = []
    commands = {name: shutil.which(name) for name in ['ffmpeg', 'ffprobe']}
    errors += [f'missing command: {name}' for name, path in commands.items() if not path]
    checks = {'commands': {name: bool(path) for name, path in commands.items()}}
    if args.require_asr:
        for module in ['faster_whisper', 'ctranslate2', 'av']:
            if importlib.util.find_spec(module) is None:
                errors.append(f'missing Python dependency in this interpreter: {module}')
    if args.delivery == 'feishu':
        settings = {}
        try:
            configuration, origin = load_config(args.config)
            settings = dict(configuration.get('feishu', {}))
            checks['configuration_source'] = origin
        except (OSError, ValueError) as exc:
            errors.append(f'cannot load user configuration: {type(exc).__name__}')
        for argument, key in [('wiki_space', 'space_id'), ('wiki_parent', 'parent_node_token')]:
            if getattr(args, argument, ''):
                settings[key] = getattr(args, argument)
        for name in ['space_id', 'parent_node_token']:
            if not str(settings.get(name, '')).strip():
                errors.append(f'configure your own feishu.{name} in --config')
        identity = settings.get('identity', 'user')
        if identity not in ['user', 'bot']:
            errors.append('feishu.identity must be user or bot')
        commands['lark-cli'] = shutil.which('lark-cli')
        if not commands['lark-cli']:
            errors.append('install lark-cli and authorize your own identity for Feishu delivery')
        if args.live_feishu_read and not errors:
            parts = ['lark-cli', 'wiki', '+node-get', '--as', identity,
                     '--space-id', str(settings['space_id']), '--node-token', str(settings['parent_node_token'])]
            try:
                result = subprocess.run(parts, capture_output=True, text=True, timeout=45)
                checks['feishu_cli_exit_code'] = result.returncode
                if result.returncode == 77 and 'current requesting user could not be verified' in result.stderr:
                    checks['feishu_identity_error'] = 'current_actor_unverified'
                payload = json.loads(result.stdout) if result.stdout.strip() else {}
                data = payload.get('data') or {}
                valid = (result.returncode == 0 and payload.get('ok') is True
                         and str(data.get('space_id')) == str(settings['space_id'])
                         and data.get('node_token') == settings['parent_node_token'])
            except (OSError, subprocess.TimeoutExpired, ValueError):
                valid = False
            checks['feishu_parent_readback'] = valid
            if not valid:
                errors.append('cannot verify configured parent as the configured identity; inspect CLI output privately')
        elif not args.live_feishu_read:
            warnings.append('Feishu identity and destination have not been verified live')
    elif args.config or args.live_feishu_read:
        warnings.append('offline delivery ignores Feishu configuration and live-read options')
    return {'ok': not errors, 'entry': args.entry, 'delivery': args.delivery,
            'checks': checks, 'warnings': warnings, 'errors': errors}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--entry', choices=['terminal', 'feishu'], default='terminal')
    parser.add_argument('--url', default='')
    parser.add_argument('--delivery', choices=['offline', 'feishu'], default='offline')
    parser.add_argument('--config', default='', help='Feishu config; otherwise VIDEO_SUMMARY_CONFIG or the user config directory')
    parser.add_argument('--wiki-space', default='', help='Override the configured Wiki space for this run')
    parser.add_argument('--wiki-parent', default='', help='Override the configured Wiki collection for this run')
    parser.add_argument('--require-asr', action='store_true')
    parser.add_argument('--live-feishu-read', action='store_true')
    parser.add_argument('--output', default='')
    args = parser.parse_args()
    report = check(args)
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered + '\n', encoding='utf-8')
    print(rendered)
    return 0 if report['ok'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
