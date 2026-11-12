#!/usr/bin/env python3
"""Validate evidence plus a local summary's existence, provenance and timestamps."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

TYPES = {'finance_business_investment', 'knowledge_course_tutorial', 'politics_social_news',
         'entertainment_film_variety_microdrama', 'ai_video_creation_creative_short_script',
         'interview_podcast_dialogue', 'product_review_consumption_decision', 'vlog_life_travel', 'mixed_or_unknown'}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, required=True)
    args = parser.parse_args()
    run = args.run_dir.resolve()
    result = subprocess.run([sys.executable, str(Path(__file__).with_name('validate_video_summary_run.py')),
                             '--run-dir', str(run), '--delivery', 'offline', '--require-frame-evidence'],
                            capture_output=True, text=True)
    if result.returncode:
        print('Evidence validation failed; inspect the run artifacts before accepting the summary.', file=sys.stderr)
        return 2
    try:
        summary = (run / 'doc/summary.md').read_text(encoding='utf-8')
        metadata = json.loads((run / 'metadata/metadata_summary.json').read_text(encoding='utf-8'))
        decision = json.loads((run / 'doc/video_type_decision.json').read_text(encoding='utf-8'))
        times = [(int(m), int(s)) for m, s in re.findall(r'(?<!\d)(\d{1,3}):(\d{2})(?!\d)', summary)]
        checks = {
            'evidence_validation': True,
            'nonempty_summary': len(summary.strip()) >= 80,
            'source_link': metadata['source_url'] in summary,
            'timestamp_navigation': bool(times),
            'timestamps_in_bounds': bool(times) and all(s < 60 and m * 60 + s <= metadata['duration'] for m, s in times),
            'primary_type': decision.get('primary_type') in TYPES,
            'type_evidence': bool(decision.get('evidence')),
        }
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f'Missing or invalid local summary artifact: {type(exc).__name__}', file=sys.stderr)
        return 2
    report = {'ok': all(checks.values()), 'checks': checks,
              'summary_sha256': hashlib.sha256(summary.encode()).hexdigest(),
              'limitation': 'Mechanical checks do not prove factual accuracy or visual interpretation; the assistant must review the source and reopen the final file.'}
    (run / 'doc/summary_readback.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['ok'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
