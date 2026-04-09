import wx
from .main_frame import MainFrame

class AutoLipToolApp(wx.App):
    """
    MMD_AutoLipTool の wxPython 側アプリケーションクラス。
    [MS13-B1] 最小の起動骨格として Frame の生成と表示のみを担います。
    """
    def OnInit(self):
        self.frame = MainFrame(None)
        self.frame.Show()
        self.SetTopWindow(self.frame)
        return True
