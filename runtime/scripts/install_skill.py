#!/usr/bin/env python3
"""Install a self-contained skill copy without changing assistant settings."""
from __future__ import annotations

import argparse
from pathlib import Path
import shutil


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assistant', required=True, choices=['codex', 'claude'])
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument('--project', type=Path,
                        help='Project to receive a project-scoped skill; existing installs are preserved')
    target.add_argument('--target', type=Path,
                        help='Explicit skill directory for an existing assistant setup; must not already exist')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    container = '.agents' if args.assistant == 'codex' else '.claude'
    destination = (args.target.expanduser().resolve() if args.target else
                   args.project.expanduser().resolve() / container / 'skills' / 'video-summary')
    if destination.exists():
        parser.error(f'already exists; review or move it before installing: {destination}')
    destination.mkdir(parents=True)
    for name in ['SKILL.md', 'LICENSE', 'requirements.txt', 'config.example.json']:
        shutil.copyfile(root / name, destination / name)
    for name in ['runtime', 'references']:
        shutil.copytree(root / name, destination / name,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.venv'))
    print(f'Installed {args.assistant} skill: {destination}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
