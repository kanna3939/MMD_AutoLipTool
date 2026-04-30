"""
MMD AutoLipTool Entry Point

[MS13-B1] wxPython 移行に伴い、このファイルは wx 主系の起動入口として再構成されました。
以前の PySide6 (Qt) 側の起動処理はすべて除去・凍結されています。
Qt 版 GUI のロジックは src/gui/ フォルダ内に未加工で残っていますが、今後は呼び出されません。
"""
import sys

from gui_wx.app import AutoLipToolApp

def main() -> int:
    """
    アプリケーションのメインエントリポイント。
    """
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
        print(f"Failed to start wx application: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
