import sys
from pathlib import Path

from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QApplication, QSplashScreen

from gui import MainWindow


def get_resource_path(relative_path: str) -> Path:
    try:
        base_path = Path(sys._MEIPASS)
    except AttributeError:
        base_path = Path(__file__).resolve().parent.parent
    return base_path / relative_path


def _set_windows_app_user_model_id() -> None:
    if sys.platform != "win32":
        return
    try:
        import ctypes
        app_id = "kanna.mmd_autoliptool.app.1_0"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    except Exception:
        pass


def main() -> int:
    _set_windows_app_user_model_id()
    app = QApplication(sys.argv)

    icon_path = get_resource_path("assets/icons/MMD_AutoLipTool.ico")

    if icon_path.exists():
        icon = QIcon(str(icon_path))
        app.setWindowIcon(icon)

    splash_path = get_resource_path("assets/MMD_AutoLipTool_splash.png")
    splash = None
    if splash_path.exists():
        pixmap = QPixmap(str(splash_path))
        splash = QSplashScreen(pixmap)
        splash.show()
        app.processEvents()

    window = MainWindow()
    window.show()
    
    if splash is not None:
        splash.finish(window)
        
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
