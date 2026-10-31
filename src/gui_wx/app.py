from contextlib import nullcontext

import wx
import wx.adv
import time
from .main_frame import MainFrame
from src.core.settings_store import SettingsStore
from src.core.generation_presets import GenerationPresetStore
from src.core.model_profiles import ModelProfileStore
from .app_controller import AppController
from resource_utils import get_resource_path
from app_version import resolve_app_version, format_app_version_display
from src.core.transition_evaluation import TransitionEvaluationRequest
from src.core.cleanup_evaluation import CleanupEvaluationRequest

class AutoLipToolApp(wx.App):
    """
    MMD_AutoLipTool の wxPython 側アプリケーションクラス。
    [MS13-B1] 最小の起動骨格として Frame の生成と表示のみを担います。
    [MS13-B4] 起動時に設定から ini を読み込み、メインフレームへ反映します。
    """
    def __init__(
        self,
        *args,
        settings_store: SettingsStore | None = None,
        preset_store: GenerationPresetStore | None = None,
        profile_store: ModelProfileStore | None = None,
        transition_evaluation_request: TransitionEvaluationRequest | None = None,
        cleanup_evaluation_request: CleanupEvaluationRequest | None = None,
        startup_diagnostics=None,
        **kwargs,
    ):
        if transition_evaluation_request is not None and not isinstance(
            transition_evaluation_request, TransitionEvaluationRequest
        ):
            raise TypeError("transition_evaluation_request must be typed or None")
        if cleanup_evaluation_request is not None and not isinstance(
            cleanup_evaluation_request, CleanupEvaluationRequest
        ):
            raise TypeError("cleanup_evaluation_request must be typed or None")
        if cleanup_evaluation_request is not None and transition_evaluation_request is not None:
            raise ValueError("cleanup and explicit transition evaluations cannot be combined")
        self._settings_store = settings_store
        self._preset_store = preset_store
        self._profile_store = profile_store
        self._transition_evaluation_request = transition_evaluation_request
        self._cleanup_evaluation_request = cleanup_evaluation_request
        self._startup_diagnostics = startup_diagnostics
        self._splash = None
        self._startup_ready_scheduled = False
        super().__init__(*args, **kwargs)

    def _diagnostic_stage(self, stage: str, failure_code: str):
        if self._startup_diagnostics is None:
            return nullcontext()
        return self._startup_diagnostics.stage(stage, failure_code=failure_code)

    def _destroy_splash(self) -> None:
        splash = self._splash
        self._splash = None
        if splash is None:
            return
        try:
            splash.Destroy()
        except BaseException as error:
            if self._startup_diagnostics is not None:
                self._startup_diagnostics.log_event(
                    "splash",
                    "splash_cleanup_failed",
                    "warning",
                    failure_code="splash_cleanup_failed",
                    exception=error,
                )
        else:
            if self._startup_diagnostics is not None:
                self._startup_diagnostics.log_event(
                    "splash",
                    "splash_destroyed",
                    "destroyed",
                )

    def _record_startup_ready(self) -> None:
        frame = getattr(self, "frame", None)
        if frame is None:
            return
        try:
            if frame.IsBeingDeleted() or not frame.IsShown():
                return
        except Exception as error:
            if self._startup_diagnostics is not None:
                self._startup_diagnostics.log_event(
                    "diagnostics",
                    "diagnostic_check_failed",
                    "warning",
                    failure_code="unknown_failure",
                    exception=error,
                )
            return
        if self._startup_diagnostics is not None:
            self._startup_diagnostics.record_startup_ready()

    def _schedule_startup_ready(self) -> None:
        if self._startup_diagnostics is None:
            return
        if self._startup_ready_scheduled:
            return
        self._startup_ready_scheduled = True
        try:
            wx.CallAfter(self._record_startup_ready)
        except Exception as error:
            self._startup_diagnostics.log_event(
                "diagnostics",
                "diagnostic_check_failed",
                "warning",
                failure_code="unknown_failure",
                exception=error,
            )
            return
        self._startup_diagnostics.record_startup_ready_callback_scheduled()

    def _layout_and_refresh_frame(self) -> None:
        """Run deferred initial layout only while the main frame is alive."""
        try:
            frame = getattr(self, "frame", None)
            if frame is None or frame.IsBeingDeleted():
                return
            frame.Layout()
            frame.Refresh()
        except RuntimeError:
            # A test or shutdown path may destroy the frame before CallAfter
            # is dispatched.  The deferred refresh is no longer applicable.
            return

    def OnInit(self):
        try:
            with self._diagnostic_stage("app_init", "wx_app_init_failed"):
                return self._initialize_app()
        except BaseException:
            self._destroy_splash()
            raise

    def _initialize_app(self) -> bool:
        start_time = time.monotonic()

        with self._diagnostic_stage("splash_setup", "splash_setup_failed"):
            splash_path = get_resource_path("assets/MMD_AutoLipTool_splash.png")
            if splash_path.is_file():
                with wx.LogNull():
                    bitmap = wx.Bitmap(str(splash_path), wx.BITMAP_TYPE_PNG)

                dc = wx.MemoryDC(bitmap)
                font = wx.Font(
                    14,
                    wx.FONTFAMILY_DEFAULT,
                    wx.FONTSTYLE_NORMAL,
                    wx.FONTWEIGHT_BOLD,
                )
                dc.SetFont(font)
                dc.SetTextForeground(wx.Colour(60, 60, 60))

                version_str = format_app_version_display(resolve_app_version())
                text_size = dc.GetTextExtent(version_str)
                x = (bitmap.GetWidth() - text_size.GetWidth()) // 2
                y = bitmap.GetHeight() - text_size.GetHeight() - 30
                dc.DrawText(version_str, x, y)
                dc.SelectObject(wx.NullBitmap)

                self._splash = wx.adv.SplashScreen(
                    bitmap,
                    wx.adv.SPLASH_CENTRE_ON_SCREEN | wx.adv.SPLASH_NO_TIMEOUT,
                    0,
                    None,
                    -1,
                    style=wx.BORDER_NONE | wx.FRAME_NO_TASKBAR | wx.STAY_ON_TOP,
                )
                self._splash.Show()
                if self._startup_diagnostics is not None:
                    self._startup_diagnostics.log_event(
                        "splash",
                        "splash_shown",
                        "shown",
                    )
                wx.Yield()
            elif self._startup_diagnostics is not None:
                self._startup_diagnostics.log_event(
                    "splash",
                    "splash_missing",
                    "skipped",
                )

        with self._diagnostic_stage("main_frame_create", "main_frame_create_failed"):
            self.frame = MainFrame(
                None,
                transition_evaluation_request=self._transition_evaluation_request,
                cleanup_evaluation_request=self._cleanup_evaluation_request,
            )

        with self._diagnostic_stage("controller_create", "controller_create_failed"):
            self.controller = AppController(
                self.frame,
                settings_store=self._settings_store,
                preset_store=self._preset_store,
                profile_store=self._profile_store,
                startup_diagnostics=self._startup_diagnostics,
            )

        with self._diagnostic_stage("controller_bind", "controller_bind_failed"):
            self.frame.set_controller(self.controller)

        with self._diagnostic_stage(
            "startup_state_load",
            "startup_state_load_failed",
        ):
            startup = self.controller.load_startup_state()
        if self._startup_diagnostics is not None:
            settings_result = startup.get("settings_result")
            if getattr(settings_result, "had_error", False):
                settings_classification = "settings_error"
            elif not getattr(settings_result, "file_exists", False):
                settings_classification = "settings_defaults"
            else:
                settings_classification = "settings_loaded"
            self._startup_diagnostics.log_event(
                "startup_state_load",
                "startup_settings_classified",
                "completed",
                reason_code=settings_classification,
            )

        with self._diagnostic_stage("settings_apply", "settings_apply_failed"):
            self.frame.apply_settings(
                startup["settings"],
                generation_state=startup["generation_state"],
                active_preset_display_name=startup["active_preset_display_name"],
                model_profile_state=startup["model_profile_state"],
                active_model_profile_display_name=(
                    startup["active_model_profile_display_name"]
                ),
                baseline_preset_display_name=startup["baseline_preset_display_name"],
                resolved_morph_upper_limit=startup["resolved_morph_upper_limit"],
                whisper_model_selection_state=startup[
                    "whisper_model_selection_state"
                ],
            )

        self.controller.start_whisper_availability_scan()

        elapsed = (time.monotonic() - start_time) * 1000
        remaining = max(0, 1500 - elapsed)

        if self._splash is not None and remaining > 0:
            def show_main_frame() -> None:
                try:
                    self._show_main_frame()
                except RuntimeError:
                    pass
                finally:
                    self._destroy_splash()

            wx.CallLater(int(remaining), show_main_frame)
        else:
            self._show_main_frame()
            self._destroy_splash()

        return True

    def _show_main_frame(self) -> None:
        with self._diagnostic_stage("main_frame_show", "main_frame_show_failed"):
            frame = getattr(self, "frame", None)
            if frame is None:
                return
            frame.Show()
            self.SetTopWindow(frame)
            frame_visible = True
            if self._startup_diagnostics is not None:
                try:
                    frame_visible = frame.IsShown()
                except Exception as error:
                    frame_visible = False
                    self._startup_diagnostics.log_event(
                        "diagnostics",
                        "diagnostic_check_failed",
                        "warning",
                        failure_code="unknown_failure",
                        exception=error,
                    )
                if frame_visible:
                    self._startup_diagnostics.record_main_frame_shown()
                else:
                    self._startup_diagnostics.log_event(
                        "diagnostics",
                        "diagnostic_check_failed",
                        "warning",
                        failure_code="main_frame_not_visible",
                    )
            wx.CallAfter(self._layout_and_refresh_frame)
            if frame_visible:
                self._schedule_startup_ready()
