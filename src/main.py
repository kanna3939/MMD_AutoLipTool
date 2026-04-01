import sys
import time
from dataclasses import dataclass

from PySide6.QtCore import QLocale, QRect, QTimer, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QApplication, QSplashScreen

from app_version import format_app_version_display, resolve_app_version
from gui import MainWindow
from gui.i18n_strings import normalize_language
from gui.settings_store import SettingsStore
from resource_utils import get_resource_path

_MIN_SPLASH_DISPLAY_MS = 350
_SPLASH_VERSION_FALLBACK = "Ver. ?"


@dataclass(frozen=True)
class _SplashDisplaySession:
    splash: QSplashScreen
    shown_at_sec: float


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


def _splash_version_rect(pixmap: QPixmap) -> QRect:
    width = pixmap.width()
    height = pixmap.height()
    left = int(width * 0.42)
    top = int(height * 0.64)
    rect_width = int(width * 0.28)
    rect_height = int(height * 0.13)
    return QRect(left, top, rect_width, rect_height)


def _build_splash_version_text() -> str:
    return format_app_version_display(
        resolve_app_version(),
        fallback=_SPLASH_VERSION_FALLBACK,
    )


def _decorate_splash_pixmap(base_pixmap: QPixmap, version_text: str) -> QPixmap:
    splash_pixmap = QPixmap(base_pixmap)
    painter = QPainter(splash_pixmap)
    try:
        font = QFont(painter.font())
        font.setBold(True)
        font.setPointSize(max(int(round(splash_pixmap.height() * 0.06)), 10))
        painter.setFont(font)
        painter.setPen(QPen(QColor("#1b5b61")))
        painter.drawText(
            _splash_version_rect(splash_pixmap),
            int(Qt.AlignCenter | Qt.TextSingleLine),
            version_text,
        )
    finally:
        painter.end()
    return splash_pixmap


def _create_and_show_splash(app: QApplication) -> _SplashDisplaySession | None:
    splash_path = get_resource_path("assets/MMD_AutoLipTool_splash.png")
    if not splash_path.exists():
        return None

    pixmap = QPixmap(str(splash_path))
    if pixmap.isNull():
        return None

    splash = QSplashScreen(
        _decorate_splash_pixmap(pixmap, _build_splash_version_text())
    )
    splash.show()
    app.processEvents()
    return _SplashDisplaySession(splash=splash, shown_at_sec=time.monotonic())


def _remaining_splash_display_ms(
    shown_at_sec: float,
    *,
    minimum_display_ms: int = _MIN_SPLASH_DISPLAY_MS,
) -> int:
    elapsed_ms = max(int((time.monotonic() - shown_at_sec) * 1000.0), 0)
    return max(int(minimum_display_ms) - elapsed_ms, 0)


def _finish_splash_when_ready(
    app: QApplication,
    splash_session: _SplashDisplaySession | None,
    window: MainWindow,
) -> None:
    if splash_session is None:
        return

    app.processEvents()
    remaining_ms = _remaining_splash_display_ms(splash_session.shown_at_sec)
    QTimer.singleShot(
        remaining_ms,
        lambda: splash_session.splash.finish(window),
    )


def main() -> int:
    _set_windows_app_user_model_id()
    app = QApplication(sys.argv)

    icon_path = get_resource_path("assets/icons/MMD_AutoLipTool.ico")

    if icon_path.exists():
        icon = QIcon(str(icon_path))
        app.setWindowIcon(icon)

    splash_session = _create_and_show_splash(app)

    settings_store = SettingsStore()
    startup_settings, startup_language = _resolve_startup_settings(settings_store)

    window = MainWindow(
        startup_settings=startup_settings,
        startup_language=startup_language,
        settings_store=settings_store,
    )
    window.show()

    _finish_splash_when_ready(app, splash_session, window)

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
