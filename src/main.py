"""
MMD AutoLipTool Entry Point

[MS13-B1] wxPython 移行に伴い、このファイルは wx 主系の起動入口として再構成されました。
"""
import sys
import os
from pathlib import Path

# プロジェクトルートディレクトリを sys.path に追加し、'from src.core...' 等のインポートを解決可能にする
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def main() -> int:
    """
    アプリケーションのメインエントリポイント。
    """
    import traceback

    from src.core.startup_diagnostics import create_startup_diagnostics

    diagnostics = create_startup_diagnostics()
    diagnostics.log_event("entrypoint", "process_entry", "started")

    def global_exception_handler(exctype, value, tb):
        diagnostics.log_event(
            "main_loop",
            "stage_failed",
            "failed",
            failure_code="main_loop_failed",
            exception=value,
        )
        try:
            with open("error.log", "a", encoding="utf-8") as f:
                f.write("".join(traceback.format_exception(exctype, value, tb)))
        except OSError:
            pass
        sys.__excepthook__(exctype, value, tb)
    sys.excepthook = global_exception_handler

    try:
        with diagnostics.stage("wx_import", failure_code="wx_import_failed"):
            from gui_wx.app import AutoLipToolApp
    except Exception as error:
        try:
            with open("error.log", "w", encoding="utf-8") as f:
                f.write(traceback.format_exc())
        except OSError:
            pass
        print(f"Failed to start wx application: {error}", file=sys.stderr)
        return 1

    import ctypes
    if sys.platform == 'win32':
        try:
            myappid = 'kanna3939.MMD_AutoLipTool.app.0.4' # Arbitrary string
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except AttributeError:
            pass

    try:
        with diagnostics.stage("app_construct", failure_code="wx_app_create_failed"):
            app = AutoLipToolApp(False, startup_diagnostics=diagnostics)
        with diagnostics.stage("main_loop", failure_code="main_loop_failed"):
            diagnostics.log_event("main_loop", "main_loop_started", "started")
            app.MainLoop()
            diagnostics.log_event("main_loop", "main_loop_completed", "completed")
        return 0
    except Exception as e:
        diagnostics.log_event(
            "entrypoint",
            "stage_failed",
            "failed",
            failure_code="unknown_failure",
            exception=e,
        )
        try:
            with open("error.log", "w", encoding="utf-8") as f:
                f.write(traceback.format_exc())
        except OSError:
            pass
        print(f"Failed to start wx application: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
