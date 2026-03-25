import sys
from pathlib import Path

from PySide6.QtCore import QLocale
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QApplication, QSplashScreen

from gui import MainWindow
from gui.i18n_strings import normalize_language
from gui.settings_store import SettingsStore


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


def _detect_os_language() -> str:
    try:
        locale_name = QLocale.system().name()
    except Exception:
        return "en"
    normalized = normalize_language(locale_name.split("_", 1)[0])
    if normalized == "ja":
        return "ja"
    return "en"


def _resolve_startup_settings(store: SettingsStore) -> tuple[dict[str, object], str]:
    load_result = store.load()
    startup_settings = dict(load_result.settings)
    language_is_usable = (
        "language" not in load_result.invalid_keys
        and "language" not in load_result.used_default_keys
    )
    startup_language = (
        normalize_language(str(startup_settings.get("language")))
        if language_is_usable
        else _detect_os_language()
    )
    startup_settings["language"] = startup_language
    return (startup_settings, startup_language)


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

    settings_store = SettingsStore()
    startup_settings, startup_language = _resolve_startup_settings(settings_store)

    window = MainWindow(
        startup_settings=startup_settings,
        startup_language=startup_language,
        settings_store=settings_store,
    )
    window.show()
    
    if splash is not None:
        splash.finish(window)
        
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
