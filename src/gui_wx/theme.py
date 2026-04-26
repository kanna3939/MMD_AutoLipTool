import wx

class ThemeMode:
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"
    SUPPORTED = (LIGHT, DARK, SYSTEM)

class ResolvedTheme:
    LIGHT = "light"
    DARK = "dark"

class ThemePalette:
    def __init__(self, is_dark: bool):
        self.is_dark = is_dark
        if is_dark:
            self.window_bg = wx.Colour(45, 45, 45)
            self.panel_bg = wx.Colour(55, 55, 55)
            self.text_fg = wx.Colour(230, 230, 230)
            self.muted_text = wx.Colour(160, 160, 160)
            self.border = wx.Colour(90, 90, 90)
            self.waveform_line = wx.Colour(100, 200, 255)
            self.waveform_grid = wx.Colour(80, 80, 80)
            self.playback_cursor = wx.Colour(255, 80, 80)
            self.preview_lane_bg = wx.Colour(65, 65, 65)
            self.preview_segment = wx.Colour(120, 220, 120)
        else:
            self.window_bg = wx.Colour(240, 240, 240)
            self.panel_bg = wx.Colour(255, 255, 255)
            self.text_fg = wx.Colour(20, 20, 20)
            self.muted_text = wx.Colour(120, 120, 120)
            self.border = wx.Colour(200, 200, 200)
            self.waveform_line = wx.Colour(0, 100, 200)
            self.waveform_grid = wx.Colour(220, 220, 220)
            self.playback_cursor = wx.Colour(220, 0, 0)
            self.preview_lane_bg = wx.Colour(245, 245, 245)
            self.preview_segment = wx.Colour(0, 160, 0)

class ThemeManager:
    _current_palette: ThemePalette = ThemePalette(is_dark=True)
    _resolved_theme: str = ResolvedTheme.DARK

    @classmethod
    def resolve_theme(cls, mode: str) -> str:
        mode = mode.lower()
        if mode in (ThemeMode.LIGHT, ThemeMode.DARK):
            return mode
        
        # System theme fallback based on window background color
        if wx.GetApp():
            sys_bg = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)
            # Approximate brightness
            brightness = (sys_bg.Red() * 299 + sys_bg.Green() * 587 + sys_bg.Blue() * 114) / 1000
            if brightness < 128:
                return ResolvedTheme.DARK
        return ResolvedTheme.LIGHT

    @classmethod
    def apply_theme(cls, mode: str, top_window: wx.Window) -> str:
        resolved = cls.resolve_theme(mode)
        cls._resolved_theme = resolved
        cls._current_palette = ThemePalette(is_dark=(resolved == ResolvedTheme.DARK))
        
        if top_window:
            cls._apply_to_window_tree(top_window, cls._current_palette)
            top_window.Refresh()
            top_window.Update()
            
        return resolved

    @classmethod
    def get_palette(cls) -> ThemePalette:
        return cls._current_palette

    @classmethod
    def _apply_to_window_tree(cls, window: wx.Window, palette: ThemePalette):
        # Apply colors basically. wx on Windows has some quirks with native controls,
        # so we mostly target panels and text.
        if isinstance(window, wx.Panel):
            window.SetBackgroundColour(palette.panel_bg)
            window.SetForegroundColour(palette.text_fg)
        elif isinstance(window, wx.Frame):
            window.SetBackgroundColour(palette.window_bg)
            window.SetForegroundColour(palette.text_fg)
            
        if isinstance(window, wx.StaticText):
            window.SetForegroundColour(palette.text_fg)
            
        for child in window.GetChildren():
            cls._apply_to_window_tree(child, palette)
