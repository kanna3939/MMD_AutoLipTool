from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from gui_wx.help_about_dialogs import (
    USAGE_GUIDE_LOAD_FAILURE_TEXT,
    USAGE_GUIDE_RESOURCE,
    USAGE_GUIDE_TEXT,
    load_usage_guide_text,
)
from resource_utils import get_resource_path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class TestMS28B5UsageDocument(unittest.TestCase):
    def test_spec_bundles_usage_guide_into_assets(self):
        spec_text = (REPOSITORY_ROOT / "MMD_AutoLipTool.spec").read_text(encoding="utf-8")
        self.assertIn('datas += [("assets/usage_guide.json", "assets")]', spec_text)

    def test_usage_guide_json_is_the_loaded_source(self):
        resource_path = get_resource_path(USAGE_GUIDE_RESOURCE)
        self.assertTrue(resource_path.is_file())
        payload = json.loads(resource_path.read_text(encoding="utf-8"))

        self.assertIsInstance(payload, dict)
        self.assertEqual(USAGE_GUIDE_TEXT, "\n".join(payload["lines"]))
        self.assertEqual(USAGE_GUIDE_TEXT, load_usage_guide_text(resource_path))

    def test_missing_usage_guide_uses_fixed_failure_text(self):
        with TemporaryDirectory() as directory:
            missing_path = Path(directory) / "missing.json"
            self.assertEqual(load_usage_guide_text(missing_path), USAGE_GUIDE_LOAD_FAILURE_TEXT)

    def test_usage_text_contains_required_headings_and_file_types(self):
        content = USAGE_GUIDE_TEXT
        for heading in (
            "## 基本的な使い方",
            "## 開口維持と閉口スムーズ",
            "## 選択イベントの操作",
            "## プリセット",
            "## モデルプロファイル",
            "## Whisperモデル",
            "## 保存とMMDでの確認",
        ):
            self.assertIn(heading, content)
        self.assertIn("UTF-8", content)
        self.assertIn("WAV、MP3、M4A", content)
        self.assertIn("VMD", content)
        self.assertIn("次のような場面", content)
        self.assertIn("https://x.com/kanna3939", content)

    def test_whisper_role_is_described_for_both_analysis_modes(self):
        content = USAGE_GUIDE_TEXT
        self.assertIn("TEXT＋音声・音声のみのどちらの解析でも", content)
        self.assertIn("音声の発話タイミングを取得するために使われます", content)
        self.assertIn("読み込んだTEXTをそのタイミングに対応づけて", content)
        self.assertIn("音声だけを読み込んだ場合は、解析時にWhisperが書き起こしと音声の発話タイミングを取得します", content)
        self.assertNotIn("文章がない音声から書き起こしを作る場合に利用します。", content)


if __name__ == "__main__":
    unittest.main()
