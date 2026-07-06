from __future__ import annotations

import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
PREFLIGHT_PATH = REPO_ROOT / "scripts" / "video_summary_preflight.py"


def load_preflight_module():
    spec = importlib.util.spec_from_file_location("video_summary_preflight", PREFLIGHT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load video_summary_preflight.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class VideoSummaryPreflightConfigTest(unittest.TestCase):
    def setUp(self) -> None:
        self.preflight = load_preflight_module()

    def test_feishu_delivery_requires_user_wiki_space_configuration(self) -> None:
        parser = self.preflight.build_parser()
        args = parser.parse_args(["--entry", "terminal", "--delivery", "feishu"])
        errors: list[str] = []
        warnings: list[str] = []

        with patch.dict(os.environ, {}, clear=True):
            space_id = self.preflight.resolve_wiki_space(args, errors, warnings)

        self.assertIsNone(space_id)
        self.assertTrue(any("VIDEO_SUMMARY_WIKI_SPACE_ID" in error for error in errors))
        self.assertFalse(any("PRIVATE_WIKI_SPACE_ID" in error for error in errors))

    def test_wiki_space_can_come_from_environment(self) -> None:
        parser = self.preflight.build_parser()
        args = parser.parse_args(["--entry", "terminal", "--delivery", "feishu"])
        errors: list[str] = []
        warnings: list[str] = []

        with patch.dict(os.environ, {"VIDEO_SUMMARY_WIKI_SPACE_ID": "space_123"}, clear=True):
            space_id = self.preflight.resolve_wiki_space(args, errors, warnings)

        self.assertEqual(space_id, "space_123")
        self.assertEqual(errors, [])

    def test_write_initial_env_does_not_overwrite_existing_env(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            example = tmp / ".env.example"
            destination = tmp / ".env"
            example.write_text("VIDEO_SUMMARY_WIKI_SPACE_ID=<YOUR_SPACE_ID>\n", encoding="utf-8")
            destination.write_text("VIDEO_SUMMARY_WIKI_SPACE_ID=keep-me\n", encoding="utf-8")

            created = self.preflight.write_initial_env(example, destination)

            self.assertFalse(created)
            self.assertEqual(destination.read_text(encoding="utf-8"), "VIDEO_SUMMARY_WIKI_SPACE_ID=keep-me\n")

    def test_write_initial_env_creates_env_from_example(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            example = tmp / ".env.example"
            destination = tmp / ".env"
            example.write_text("VIDEO_SUMMARY_WIKI_SPACE_ID=<YOUR_SPACE_ID>\n", encoding="utf-8")

            created = self.preflight.write_initial_env(example, destination)

            self.assertTrue(created)
            self.assertEqual(destination.read_text(encoding="utf-8"), example.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
