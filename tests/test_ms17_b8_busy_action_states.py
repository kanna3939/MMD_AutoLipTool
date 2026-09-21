import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import wx

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from gui_wx.app import AutoLipToolApp
from gui_wx.worker_state import AudioWorkerKind, AudioWorkerState, AudioWorkerStatus
from tests.helpers import destroy_wx_app, get_or_create_wx_app


class TestMS17B8BusyActionStates(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch("gui_wx.app.get_resource_path", return_value=Path("missing_splash.png")):
            cls.app, cls.owns_app = get_or_create_wx_app(AutoLipToolApp, False)

    @classmethod
    def tearDownClass(cls):
        destroy_wx_app(cls.app, owns_app=cls.owns_app)

    def setUp(self):
        self.frame = self.app.frame
        self.frame.ui_state = self.frame.ui_state.__class__()

    def tearDown(self):
        self.frame.ui_state = self.frame.ui_state.__class__()
        self.frame.update_action_states()

    def test_busy_audio_worker_enables_only_cancel_for_main_audio_actions(self):
        state = self.frame.ui_state
        state.set_busy(True)
        state.audio_worker_state = AudioWorkerState(
            audio_job_id=1,
            kind=AudioWorkerKind.ANALYSIS_WAV,
            status=AudioWorkerStatus.RUNNING,
        )

        self.frame.update_action_states()

        self.assertFalse(self.frame.btn_open_text.IsEnabled())
        self.assertFalse(self.frame.btn_open_wav.IsEnabled())
        self.assertFalse(self.frame.btn_process.IsEnabled())
        self.assertFalse(self.frame.btn_save_vmd.IsEnabled())
        self.assertFalse(self.frame.btn_export_mmd_wav.IsEnabled())
        self.assertTrue(self.frame.btn_cancel_audio_worker.IsEnabled())


if __name__ == "__main__":
    unittest.main()
