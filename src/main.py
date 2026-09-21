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

from gui_wx.app import AutoLipToolApp

def main() -> int:
    """
    アプリケーションのメインエントリポイント。
    """
    import traceback
    def global_exception_handler(exctype, value, tb):
        with open("error.log", "a", encoding="utf-8") as f:
            f.write("".join(traceback.format_exception(exctype, value, tb)))
        sys.__excepthook__(exctype, value, tb)
    sys.excepthook = global_exception_handler

    import ctypes
    if sys.platform == 'win32':
        try:
            myappid = 'kanna3939.MMD_AutoLipTool.app.0.4' # Arbitrary string
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except AttributeError:
            pass

    try:
        app = AutoLipToolApp(False)
        app.MainLoop()
        return 0
    except Exception as e:
        import traceback
        with open("error.log", "w", encoding="utf-8") as f:
            f.write(traceback.format_exc())
        print(f"Failed to start wx application: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
