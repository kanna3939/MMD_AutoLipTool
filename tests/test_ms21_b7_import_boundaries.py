from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]


def run_import_smoke(code: str):
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        (str(REPO_ROOT / "src"), str(REPO_ROOT))
    )
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_helper_first_import_order_has_no_cycle():
    result = run_import_smoke(
        "import gui_wx.analysis_rollback; "
        "import gui_wx.ui_sync_context; "
        "import gui_wx.main_frame"
    )
    assert result.returncode == 0, result.stderr


def test_main_frame_first_import_order_has_no_cycle():
    result = run_import_smoke(
        "import gui_wx.main_frame; "
        "import gui_wx.analysis_rollback; "
        "import gui_wx.ui_sync_context"
    )
    assert result.returncode == 0, result.stderr
