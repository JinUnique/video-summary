#!/usr/bin/env python3
"""Prepare public Bilibili evidence. An AI assistant writes the actual summary."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

SCRIPTS = Path(__file__).resolve().parent
HEADERS = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.bilibili.com/'}


def save(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def api(endpoint: str, **params):
    url = 'https://api.bilibili.com/' + endpoint + '?' + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=45) as response:
            payload = json.load(response)
    except (urllib.error.URLError, ValueError) as exc:
        raise RuntimeError(f'public metadata request failed: {endpoint} ({type(exc).__name__})') from None
    if payload.get('code') != 0:
        raise RuntimeError(f'public API {endpoint} returned code {payload.get("code")}; no credential fallback was used')
    return payload


def resolve_source(source: str) -> tuple[str, int | None]:
    if re.fullmatch(r'BV[0-9A-Za-z]{10}', source):
        return source, None
    if re.fullmatch(r'av\d+', source, re.I):
        return api('x/web-interface/view', aid=int(source[2:]))['data']['bvid'], None
    parsed = urllib.parse.urlparse(source)
    if parsed.scheme != 'https' or parsed.hostname not in ['www.bilibili.com', 'bilibili.com', 'm.bilibili.com', 'b23.tv']:
        raise RuntimeError('this helper accepts BV/av ids or HTTPS Bilibili/b23.tv links; use the skill reference for other sources')
    if parsed.hostname == 'b23.tv':
        with urllib.request.urlopen(urllib.request.Request(source, headers=HEADERS), timeout=30) as response:
            source = response.url
        if urllib.parse.urlparse(source).hostname not in ['www.bilibili.com', 'bilibili.com', 'm.bilibili.com']:
            raise RuntimeError('short link did not resolve to Bilibili')
    match = re.search(r'BV[0-9A-Za-z]{10}', source)
    aid = re.search(r'/video/av(\d+)', source, re.I)
    bvid = match.group(0) if match else api('x/web-interface/view', aid=int(aid.group(1)))['data']['bvid'] if aid else ''
    if not bvid:
        raise RuntimeError('no BV/av id in link')
    query = urllib.parse.parse_qs(urllib.parse.urlparse(source).query)
    part = int(query['p'][0]) if query.get('p') else None
    if part is not None and part < 1:
        raise RuntimeError('Bilibili p must be at least 1')
    return bvid, part


def download(url: str, destination: Path) -> None:
    if destination.exists() and destination.stat().st_size:
        return
    if urllib.parse.urlparse(url).scheme != 'https':
        raise RuntimeError('media endpoint did not offer HTTPS; stopping before download')
    temporary = destination.with_suffix(destination.suffix + '.part')
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=90) as response:
            with temporary.open('wb') as output:
                while chunk := response.read(1024 * 1024):
                    output.write(chunk)
        temporary.replace(destination)
    except urllib.error.URLError:
        raise RuntimeError('public media download failed; rerun to refresh expiring public stream URLs') from None


def probe(path: Path) -> dict:
    return json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_format', '-show_streams',
                                              '-of', 'json', str(path)], text=True))


def helper(run: Path, script: str, *arguments: str) -> None:
    print(f'Running {script}', flush=True)
    with (run / 'logs' / (script + '.log')).open('w') as log:
        completed = subprocess.run([sys.executable, str(SCRIPTS / script), *arguments], stdout=log, stderr=subprocess.STDOUT)
    if completed.returncode:
        raise RuntimeError(f'{script} failed (exit {completed.returncode}); inspect the local log under runs before retrying')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source')
    parser.add_argument('--run-dir', required=True, type=Path)
    parser.add_argument('--model', default='base', help='faster-whisper model name or your own local model directory')
    parser.add_argument('--language', default='zh')
    parser.add_argument('--part', type=int, default=None, help='Override the p= query or default part 1')
    args = parser.parse_args()
    run = args.run_dir.expanduser().resolve()
    for directory in ['metadata', 'media', 'logs', 'transcript', 'frames', 'doc']:
        (run / directory).mkdir(parents=True, exist_ok=True)
    # This file intentionally contains no generated conclusion. Never label evidence as a finished summary.
    checkpoint = run / 'metadata' / 'checkpoint.json'
    stage = 'preflight'
    try:
        save(checkpoint, {'stage': stage, 'status': 'running'})
        helper(run, 'video_summary_preflight.py', '--delivery', 'offline', '--require-asr',
               '--output', str(run / 'metadata/preflight_terminal.json'))
        bvid, linked_part = resolve_source(args.source)
        part = args.part if args.part is not None else linked_part or 1
        identity = {'bvid': bvid, 'part': part, 'model': args.model, 'language': args.language}
        identity_path = run / 'metadata/input.json'
        if identity_path.exists() and json.loads(identity_path.read_text()) != identity:
            raise RuntimeError('this run directory belongs to a different source or ASR configuration; choose a new directory')
        save(identity_path, identity)
        stage = 'public_api_ingest'
        save(checkpoint, {'stage': stage, 'status': 'running'})
        metadata_path = run / 'metadata/metadata_summary.json'
        video = run / 'media/source.mp4'
        if not (video.exists() and metadata_path.exists() and (run / 'metadata/ingest_decision.json').exists()
                and (run / 'metadata/media_validation.json').exists()):
            view = api('x/web-interface/view', bvid=bvid)
            save(run / 'metadata/view.json', view)
            data = view['data']
            pages = data.get('pages') or [{'cid': data['cid'], 'duration': data['duration']}]
            if part < 1 or part > len(pages):
                raise RuntimeError(f'part must be between 1 and {len(pages)}')
            page = pages[part - 1]
            cid = page['cid']
            duration = float(page['duration'])
            save(run / 'metadata/page_target.json', {'bvid': bvid, 'part': part, 'cid': cid,
                 'part_title': page.get('part', data['title']), 'duration': duration,
                 'requested_source': args.source, 'explicit_part_override': args.part})
            save(run / 'metadata/tags.json', api('x/tag/archive/tags', bvid=bvid))
            # Subtitle/player access can be login-gated; an explicit non-blocking result is kept.
            try:
                player = api('x/player/v2', bvid=bvid, cid=cid)
            except RuntimeError:
                player = {'available': False, 'reason': 'public player metadata unavailable; using local ASR'}
            save(run / 'metadata/player.json', player)
            streams = api('x/player/playurl', bvid=bvid, cid=cid, qn=32, fnval=4048, fourk=0)
            # Signed URLs belong only in this ignored local run, never in a distributable example.
            save(run / 'metadata/playurl.json', streams)
            play = streams['data']
            dash = play.get('dash') or {}
            if dash.get('video') and dash.get('audio'):
                candidates = [item for item in dash['video'] if 0 < item.get('height', 0) <= 480]
                if not candidates:
                    raise RuntimeError('no public video stream at 480p or below; stopping without cookies')
                chosen = max(candidates, key=lambda item: (item.get('height', 0), item.get('bandwidth', 0)))
                audio = max(dash['audio'], key=lambda item: item.get('bandwidth', 0))
                download(chosen.get('baseUrl') or chosen['base_url'], run / 'media/video.m4s')
                download(audio.get('baseUrl') or audio['base_url'], run / 'media/audio_best.m4s')
                subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(run / 'media/video.m4s'),
                                '-i', str(run / 'media/audio_best.m4s'), '-c', 'copy', str(video)], check=True)
            elif len(play.get('durl') or []) == 1 and int(play.get('quality', 0)) <= 32:
                download(play['durl'][0]['url'], run / 'media/combined.flv')
                subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(run / 'media/combined.flv'),
                                '-c', 'copy', str(video)], check=True)
            else:
                raise RuntimeError('public streams are unavailable or multipart legacy streams are unsupported; stopping without cookies')
            inspected = probe(video)
            actual = float(inspected['format']['duration'])
            drift = abs(actual - duration)
            ratio = drift / duration if duration else 1
            has_av = all(any(s.get('codec_type') == kind for s in inspected['streams']) for kind in ['audio', 'video'])
            validation = {'ok': ratio <= 0.05 and has_av, 'items': {'source_mp4': {
                'path': 'media/source.mp4', 'expected_duration': duration, 'actual_duration': actual,
                'drift_seconds': drift, 'drift_ratio': ratio,
                'streams': [{'codec_type': s.get('codec_type'), 'codec_name': s.get('codec_name')} for s in inspected['streams']]}}}
            if not validation['ok']:
                raise RuntimeError('media duration or audio/video streams failed validation')
            save(metadata_path, {'title': data['title'], 'bvid': bvid, 'cid': cid, 'part': part,
                                'duration': duration, 'owner': data['owner']['name'], 'description': data.get('desc', ''),
                                'source_url': f'https://www.bilibili.com/video/{bvid}/?p={part}'})
            save(run / 'metadata/ingest_decision.json', {
                'source_order': 'public_api_baseline -> stream_adequacy -> local_asr',
                'public_streams_sufficient': True, 'yt_dlp': 'skipped', 'cookies': 'not_used'})
            save(run / 'metadata/media_validation.json', validation)
        stage = 'transcription'
        save(checkpoint, {'stage': stage, 'status': 'running'})
        wav = run / 'media/audio_16k_mono.wav'
        if not wav.exists():
            subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(video),
                            '-vn', '-ac', '1', '-ar', '16000', str(wav)], check=True)
        selected = run / 'transcript/transcript_final_selection.json'
        if not (selected.exists() and json.loads(selected.read_text()).get('ok')):
            helper(run, 'transcribe_faster_whisper.py', '--run-dir', str(run), '--model', args.model,
                   '--language', args.language, '--device', 'cpu', '--compute-type', 'int8')
        stage = 'frame_evidence'
        save(checkpoint, {'stage': stage, 'status': 'running'})
        frame_evidence = run / 'frames/frame_evidence.json'
        if not (frame_evidence.exists() and json.loads(frame_evidence.read_text()).get('ok')):
            helper(run, 'select_frame_evidence.py', '--run-dir', str(run), '--fallback-chapters', '4',
                   '--candidates-per-chapter', '3', '--ocr', 'never')
        helper(run, 'validate_video_summary_run.py', '--run-dir', str(run), '--delivery', 'offline',
               '--require-frame-evidence', '--output', str(run / 'metadata/evidence_validation.json'))
        save(checkpoint, {'stage': 'evidence_ready', 'status': 'awaiting_assistant_summary'})
        print(json.dumps({'ok': True, 'stage': 'evidence_ready', 'next': 'Ask your assistant to read the transcript and selected frames, classify the video, then write and verify doc/summary.md.'}, ensure_ascii=False))
        return 0
    except (RuntimeError, OSError, subprocess.CalledProcessError, ValueError, KeyError) as exc:
        save(checkpoint, {'stage': stage, 'status': 'failed', 'error_type': type(exc).__name__})
        # Known RuntimeError messages contain no signed URLs or credentials.
        detail = str(exc) if isinstance(exc, RuntimeError) else type(exc).__name__
        print(f'Stopped at {stage}: {detail}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
