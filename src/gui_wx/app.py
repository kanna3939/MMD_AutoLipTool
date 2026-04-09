import wx
from .main_frame import MainFrame
from gui.settings_store import SettingsStore
from .app_controller import AppController

class AutoLipToolApp(wx.App):
    """
    MMD_AutoLipTool の wxPython 側アプリケーションクラス。
    [MS13-B1] 最小の起動骨格として Frame の生成と表示のみを担います。
    [MS13-B4] 起動時に設定から ini を読み込み、メインフレームへ反映します。
    """
    def OnInit(self):
        self.frame = MainFrame(None)
        
        # [MS13-B5] Controllerの結合
        self.controller = AppController(self.frame)
        self.frame.set_controller(self.controller)
        
        # [MS13-B4] 設定をロードし、構築済みのFrameへ適用する
        store = SettingsStore()
        load_result = store.load()
        self.frame.apply_settings(load_result.settings)
        
        self.frame.Show()
        self.SetTopWindow(self.frame)
        return True
