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
        **kwargs,
    ):
        self._settings_store = settings_store
        self._preset_store = preset_store
        self._profile_store = profile_store
        super().__init__(*args, **kwargs)

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
        # スプラッシュスクリーンの生成
        splash_path = get_resource_path("assets/MMD_AutoLipTool_splash.png")
        splash = None
        start_time = time.time()
        
        if splash_path.is_file():
            with wx.LogNull():
                bitmap = wx.Bitmap(str(splash_path), wx.BITMAP_TYPE_PNG)
            
            # バージョン情報の描画
            dc = wx.MemoryDC(bitmap)
            font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
            dc.SetFont(font)
            dc.SetTextForeground(wx.Colour(60, 60, 60)) # ダークグレイ
            
            version_str = format_app_version_display(resolve_app_version())
            text_size = dc.GetTextExtent(version_str)
            # 画像の中央下付近に配置
            x = (bitmap.GetWidth() - text_size.GetWidth()) // 2
            y = bitmap.GetHeight() - text_size.GetHeight() - 30
            dc.DrawText(version_str, x, y)
            dc.SelectObject(wx.NullBitmap)
            
            splash = wx.adv.SplashScreen(
                bitmap,
                wx.adv.SPLASH_CENTRE_ON_SCREEN | wx.adv.SPLASH_NO_TIMEOUT,
                0,
                None,
                -1,
                style=wx.BORDER_NONE | wx.FRAME_NO_TASKBAR | wx.STAY_ON_TOP
            )
            splash.Show()
            wx.Yield()
            
        self.frame = MainFrame(None)
        
        # [MS13-B5] Controllerの結合
        self.controller = AppController(
            self.frame,
            settings_store=self._settings_store,
            preset_store=self._preset_store,
            profile_store=self._profile_store,
        )
        self.frame.set_controller(self.controller)
        
        # [MS13-B4/B4] SettingsStore / preset storeを一つのstartup flowで解決する
        startup = self.controller.load_startup_state()
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
            whisper_model_selection_state=startup["whisper_model_selection_state"],
        )
        self.controller.start_whisper_availability_scan()
        
        # 1500msの最小表示時間を担保
        elapsed = (time.time() - start_time) * 1000
        remaining = max(0, 1500 - elapsed)
        
        if splash and remaining > 0:
            def show_main_frame():
                try:
                    if self.frame:
                        self.frame.Show()
                        self.SetTopWindow(self.frame)
                        wx.CallAfter(self._layout_and_refresh_frame)
                except RuntimeError:
                    pass
                if splash:
                    try:
                        splash.Destroy()
                    except RuntimeError:
                        pass
            wx.CallLater(int(remaining), show_main_frame)
        else:
            self.frame.Show()
            self.SetTopWindow(self.frame)
            wx.CallAfter(self._layout_and_refresh_frame)
            if splash:
                splash.Destroy()
                
        return True
