from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / 'runtime/scripts'
sys.path.insert(0, str(SCRIPTS))


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


PREFLIGHT = load('video_summary_preflight')
ASR = load('transcribe_faster_whisper')
RENDERER = load('render_feishu_summary_doc')
PRESENTATION = load('validate_feishu_presentation_contract')
CONFIG = load('video_summary_config')
PREPARE = load('prepare_video')


class PortableDeliveryTests(unittest.TestCase):
    def args(self, **changes):
        values = dict(entry='terminal', delivery='offline', config='missing-config.json',
                      require_asr=False, live_feishu_read=True)
        values.update(changes)
        return argparse.Namespace(**values)

    def test_offline_does_not_read_config_or_call_lark(self):
        with mock.patch.object(Path, 'read_text', side_effect=AssertionError('unexpected config read')), \
             mock.patch.object(PREFLIGHT.shutil, 'which', return_value='/example/tool'), \
             mock.patch.object(PREFLIGHT.subprocess, 'run', side_effect=AssertionError('unexpected process')):
            self.assertTrue(PREFLIGHT.check(self.args())['ok'])

    def test_blank_feishu_config_stops_before_live_access(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'config.json'
            path.write_text(json.dumps({'feishu': {'space_id': '', 'parent_node_token': ''}}))
            with mock.patch.object(PREFLIGHT.shutil, 'which', return_value='/example/tool'), \
                 mock.patch.object(PREFLIGHT.subprocess, 'run', side_effect=AssertionError('unexpected network access')):
                report = PREFLIGHT.check(self.args(delivery='feishu', config=str(path)))
            self.assertFalse(report['ok'])
            self.assertEqual(len(report['errors']), 2)

    def test_wrong_live_parent_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'config.json'
            path.write_text(json.dumps({'feishu': {'space_id': 'example-space', 'parent_node_token': 'example-parent'}}))
            response = argparse.Namespace(returncode=0, stdout=json.dumps({'ok': True, 'data': {
                'space_id': 'other-space', 'node_token': 'example-parent'}}))
            with mock.patch.object(PREFLIGHT.shutil, 'which', return_value='/example/tool'), \
                 mock.patch.object(PREFLIGHT.subprocess, 'run', return_value=response):
                self.assertFalse(PREFLIGHT.check(self.args(delivery='feishu', config=str(path)))['ok'])

    def test_external_config_precedence_and_no_default_binding(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            self.assertEqual(CONFIG.config_path(environ={}, home=home), (None, 'missing'))
            default = home / '.config/video-summary/config.json'
            default.parent.mkdir(parents=True)
            default.write_text('{}')
            self.assertEqual(CONFIG.config_path(environ={}, home=home), (default, 'user_default'))
            custom = home / 'external.json'
            self.assertEqual(CONFIG.config_path(environ={'VIDEO_SUMMARY_CONFIG': str(custom)}, home=home),
                             (custom, 'environment'))
            explicit = home / 'explicit.json'
            self.assertEqual(CONFIG.config_path(str(explicit), environ={'VIDEO_SUMMARY_CONFIG': str(custom)}, home=home),
                             (explicit, 'explicit'))

    def test_multipart_query_is_preserved(self):
        self.assertEqual(PREPARE.resolve_source('https://www.bilibili.com/video/BV1a3W76wETa/?p=2'),
                         ('BV1a3W76wETa', 2))

    def test_av_source_resolves_through_public_metadata(self):
        with mock.patch.object(PREPARE, 'api', return_value={'data': {'bvid': 'BV1a3W76wETa'}}) as api:
            self.assertEqual(PREPARE.resolve_source('av123'), ('BV1a3W76wETa', None))
            api.assert_called_once_with('x/web-interface/view', aid=123)

    def test_asr_tail_hallucinations_do_not_mask_missing_audio(self):
        segments = [{'start': 0, 'end': 80, 'text': '正文'}, {'start': 101, 'end': 110, 'text': '尾部幻觉'}]
        normalized, stats = ASR.normalize_segments_to_audio_duration(segments, 100)
        self.assertEqual([s['text'] for s in normalized], ['正文'])
        self.assertEqual(stats['normalized_last_segment_end'], 80)
        self.assertEqual(stats['discarded_after_audio_segments'], 1)

    def test_qa_series_has_separate_question_and_answer_blocks(self):
        assets = {'presentation_profile': 'qa_list', 'document_title': '示例合集',
                  'source_url': 'https://example.org/video/series', 'qa_groups': [
            {'title': '第 1 期', 'source_url': 'https://example.org/video/1', 'published_date': '2026-01-01',
             'qa_items': [{'question': '示例问题？', 'answer': '示例答案。'}]},
            {'title': '第 2 期', 'source_url': 'https://example.org/video/2', 'published_date': '2026-01-02',
             'qa_items': [{'question': '另一个问题？', 'answer': '另一个答案。'}]}]}
        xml = RENDERER.render_document(assets)
        self.assertIn('01.01', xml)
        self.assertIn('02.01', xml)
        self.assertIn('</b></p>\n<p><b>A：</b>', xml)
        self.assertNotIn('<whiteboard', xml)
        report = PRESENTATION.assert_qa_list(xml, 2, 2)
        self.assertEqual(report['qa_item_count'], 2)


if __name__ == '__main__':
    unittest.main()
