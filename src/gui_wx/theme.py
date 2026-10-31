import wx
from wx.lib.buttons import GenBitmapTextButton

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
            self.attention_text = wx.Colour(255, 170, 64)
            self.pending_edit_text = wx.Colour(255, 215, 0)
            self.error_text = wx.Colour(255, 120, 120)
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
            self.attention_text = wx.Colour(180, 80, 0)
            self.pending_edit_text = wx.Colour(156, 104, 0)
            self.error_text = wx.Colour(180, 0, 0)
            self.border = wx.Colour(200, 200, 200)
            self.waveform_line = wx.Colour(0, 100, 200)
            self.waveform_grid = wx.Colour(220, 220, 220)
            self.playback_cursor = wx.Colour(220, 0, 0)
            self.preview_lane_bg = wx.Colour(245, 245, 245)
            self.preview_segment = wx.Colour(0, 160, 0)

class ThemeManager:
    _current_palette: ThemePalette = ThemePalette(is_dark=True)
    _resolved_theme: str = ResolvedTheme.DARK
    _border_style_attribute = "_ms33c_original_border_style"

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
    def draw_border(cls, dc, rect: wx.Rect, window: wx.Window) -> None:
        """Draw a one-DIP border using the active palette on custom-painted panels."""
        if rect.width <= 1 or rect.height <= 1:
            return

        pen_width = max(1, int(window.FromDIP(1)))
        dc.SetPen(wx.Pen(cls._current_palette.border, pen_width))
        dc.SetBrush(wx.TRANSPARENT_BRUSH)
        dc.DrawRectangle(rect.x, rect.y, rect.width - 1, rect.height - 1)

    @classmethod
    def _apply_native_control_border(
        cls,
        window: wx.Window,
        palette: ThemePalette,
        dark_border_style: int,
        *,
        preserve_borderless: bool = False,
    ) -> None:
        """Apply a control-specific Dark border and restore its original style in Light."""
        original_style = getattr(window, cls._border_style_attribute, None)
        if original_style is None:
            original_style = window.GetWindowStyleFlag()
            setattr(window, cls._border_style_attribute, original_style)

        target_style = original_style
        if palette.is_dark:
            border_style = original_style & wx.BORDER_MASK
            if not preserve_borderless or border_style != wx.BORDER_NONE:
                target_style = (original_style & ~wx.BORDER_MASK) | dark_border_style

        if window.GetWindowStyleFlag() != target_style:
            window.SetWindowStyleFlag(target_style)
            window.Refresh()

    @classmethod
    def _apply_to_window_tree(cls, window: wx.Window, palette: ThemePalette):
        # Apply colors basically. wx on Windows has some quirks with native controls,
        # so we mostly target panels and text.
        if isinstance(window, wx.Panel):
            window.SetBackgroundColour(palette.panel_bg)
            window.SetForegroundColour(palette.text_fg)
        elif isinstance(window, (wx.Frame, wx.Dialog)):
            window.SetBackgroundColour(palette.window_bg)
            window.SetForegroundColour(palette.text_fg)
            
        if isinstance(window, wx.StaticText):
            window.SetForegroundColour(palette.text_fg)
            
        if isinstance(
            window,
            (wx.TextCtrl, wx.SpinCtrl, wx.SpinCtrlDouble, wx.Button, ThemeButton),
        ):
            window.SetBackgroundColour(palette.panel_bg)
            window.SetForegroundColour(palette.text_fg)

        if isinstance(
            window,
            (wx.TextCtrl, wx.SpinCtrl, wx.SpinCtrlDouble),
        ):
            cls._apply_native_control_border(
                window,
                palette,
                wx.BORDER_SIMPLE,
                preserve_borderless=True,
            )
        elif isinstance(window, wx.Button):
            cls._apply_native_control_border(
                window,
                palette,
                wx.BORDER_SIMPLE,
            )
        elif isinstance(window, wx.Notebook):
            cls._apply_native_control_border(
                window,
                palette,
                wx.BORDER_NONE,
            )
        elif isinstance(window, ThemeButton):
            window.focusClr = palette.border
            window.Refresh()

        if getattr(window, "_ms33c_theme_border", False):
            window.Refresh()
            
        for child in window.GetChildren():
            cls._apply_to_window_tree(child, palette)


class ThemeButton(GenBitmapTextButton):
    """Button with native Light rendering and a one-DIP Dark border."""

    def __init__(
        self,
        parent,
        id=wx.ID_ANY,
        label="",
        pos=wx.DefaultPosition,
        size=wx.DefaultSize,
        style=0,
        validator=wx.DefaultValidator,
        name="themeButton",
    ):
        borderless_style = (style & ~wx.BORDER_MASK) | wx.BORDER_NONE
        super().__init__(
            parent,
            id,
            bitmap=wx.NullBitmap,
            label=label,
            pos=pos,
            size=size,
            style=borderless_style,
            validator=validator,
            name=name,
        )
        self.SetBezelWidth(max(1, int(self.FromDIP(2))))
        self.SetUseFocusIndicator(True)
        self.SetInitialSize(size)
        self.Bind(wx.EVT_ENTER_WINDOW, self._on_pointer_change)
        self.Bind(wx.EVT_LEAVE_WINDOW, self._on_pointer_change)

    def SetBitmap(self, bitmap, direction=wx.LEFT) -> None:
        """Keep the wx.Button-style bitmap setter used by the toolbar."""
        self.SetBitmapLabel(bitmap)
        self.InvalidateBestSize()
        min_size = self.GetMinSize()
        if min_size.width < 0 or min_size.height < 0:
            self.SetInitialSize(wx.DefaultSize)
        parent = self.GetParent()
        if parent is not None and parent.GetSizer() is not None:
            parent.Layout()
        self.Refresh()

    def SetBitmapLabel(self, bitmap, createOthers=True) -> None:
        """Allow text-only buttons to start without a valid bitmap."""
        if bitmap is None or not bitmap.IsOk():
            self.bmpLabel = None
            self.bmpDisabled = None
            return
        super().SetBitmapLabel(bitmap, createOthers=createOthers)

    def DrawLabel(self, dc, width, height, dx=0, dy=0):
        """Center the bitmap, its gap, and text as one combined label."""
        if self.bmpLabel is not None and self.GetLabel():
            # GenBitmapTextButton adds a 2px bitmap/text gap after measuring its
            # label; include that gap in the centering width as well.
            width = max(0, width - 2)
        super().DrawLabel(dc, width, height, dx, dy)

    def GetBackgroundBrush(self, dc):
        palette = ThemeManager.get_palette()
        if not palette.is_dark:
            return super().GetBackgroundBrush(dc)

        color = palette.panel_bg
        if self.IsEnabled():
            pointer = self.ScreenToClient(wx.GetMousePosition())
            pointer_inside = self.GetClientRect().Contains(pointer)
            if not self.up:
                adjustment = 12
            elif pointer_inside:
                adjustment = 6
            else:
                adjustment = 0
            if adjustment:
                color = wx.Colour(
                    min(255, color.Red() + adjustment),
                    min(255, color.Green() + adjustment),
                    min(255, color.Blue() + adjustment),
                )
        return wx.Brush(color)

    def DrawBezel(self, dc, x1, y1, x2, y2):
        palette = ThemeManager.get_palette()
        if not palette.is_dark:
            state = 0 if self.up else wx.CONTROL_PRESSED | wx.CONTROL_SELECTED
            if not self.IsEnabled():
                state = wx.CONTROL_DISABLED
            pointer = self.ScreenToClient(wx.GetMousePosition())
            if self.GetClientRect().Contains(pointer):
                state |= wx.CONTROL_CURRENT
            wx.RendererNative.Get().DrawPushButton(
                self,
                dc,
                wx.Rect(x1, y1, x2, y2),
                state,
            )
            return

        pen_width = max(1, int(self.FromDIP(1)))
        dc.SetPen(wx.Pen(palette.border, pen_width))
        dc.SetBrush(wx.TRANSPARENT_BRUSH)
        dc.DrawRectangle(x1, y1, x2 - x1 + 1, y2 - y1 + 1)

    def _on_pointer_change(self, event):
        self.Refresh()
        event.Skip()
