"""Componentes UI accesibles para el tablero 2048."""
import ctypes
import logging
from typing import Optional
import wx

from constants import CHILDID_SELF, EVENT_OBJECT_NAMECHANGE, OBJID_CLIENT

# Guard de plataforma para Windows-specific API
try:
    user32 = ctypes.windll.user32  # type: ignore[attr-defined]
    user32.NotifyWinEvent.argtypes = [
        ctypes.c_uint, ctypes.c_void_p, ctypes.c_long, ctypes.c_long
    ]
    user32.NotifyWinEvent.restype = None
except (ImportError, AttributeError):
    user32 = None

logger = logging.getLogger("2048_Accesible")


class AccessibleCustom(wx.Accessible):
    """Objeto accesible que expone nombre, rol y estado a lectores de pantalla."""

    def __init__(self, win: wx.Window, name: str = "", role: wx.AccRole = wx.ROLE_SYSTEM_CELL) -> None:
        super().__init__(win)
        self.name = name
        self.role = role

    def GetName(self, childId: int) -> tuple:
        if childId == wx.ACC_SELF:
            return wx.ACC_OK, self.name
        return wx.ACC_FALSE, ""

    def GetRole(self, childId: int) -> tuple:
        if childId == wx.ACC_SELF:
            return wx.ACC_OK, self.role
        return wx.ACC_FALSE, 0

    def GetDescription(self, childId: int) -> tuple:
        # Canal redundante necesario para JAWS/Narrator que consultan Description además de Name.
        if childId == wx.ACC_SELF:
            return wx.ACC_OK, self.name
        return wx.ACC_FALSE, ""

    def GetState(self, childId: int) -> tuple:
        """Expone estado de foco para lectores de pantalla."""
        if childId == wx.ACC_SELF:
            states = wx.ACC_STATE_SYSTEM_FOCUSABLE | wx.ACC_STATE_SYSTEM_SELECTABLE
            win = self.GetWindow()
            if win and win.FindFocus() == win:
                states |= wx.ACC_STATE_SYSTEM_FOCUSED
            return wx.ACC_OK, states
        return wx.ACC_FALSE, 0


class Celda(wx.Panel):
    """
    Representa una celda del tablero 2048.
    Maneja pintado personalizado, anillo de foco y notificaciones WinAPI nativas.
    """

    def __init__(self, parent: wx.Window, size: int, r: int, c: int, config: dict) -> None:
        super().__init__(parent, size=(size, size))
        self.r = r
        self.c = c
        self.value = 0
        self.acc_name = ""
        self.is_focused = False
        self.hc_mode = False

        self.COLORS = config['colores_fondo']
        self.TEXT_DARK = config['color_texto_oscuro']
        self.TEXT_LIGHT = config['color_texto_claro']
        self.COLORS_TEXT_HC = config['high_contrast_colors']

        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.Bind(wx.EVT_PAINT, self.on_paint)

        # Configuración de accesibilidad nativa
        self.accessible_obj = AccessibleCustom(self, self.acc_name)
        self.SetAccessible(self.accessible_obj)

    def _notify_screen_reader(self) -> None:
        """Lanza evento WinAPI para notificar cambio de nombre al lector de pantalla de forma nativa."""
        if user32 is not None and self.GetHandle():
            user32.NotifyWinEvent(
                EVENT_OBJECT_NAMECHANGE,
                self.GetHandle(),
                OBJID_CLIENT,
                CHILDID_SELF
            )

    def actualizar(self, value: int, nombre_accesible: str, notify: bool = False,
                   force_notify: bool = False, hc_mode: Optional[bool] = None) -> None:
        """Actualiza valor, nombre accesible de la celda y fuerza redibujado."""
        self.value = value
        if hc_mode is not None:
            self.hc_mode = hc_mode

        changed = False
        if nombre_accesible != self.acc_name:
            self.acc_name = nombre_accesible
            self.accessible_obj.name = self.acc_name
            changed = True

        if (changed and notify) or force_notify:
            self._notify_screen_reader()

        self.Refresh()

    def on_paint(self, event: wx.PaintEvent) -> None:
        """Dibuja la celda con estilo premium y alto contraste según corresponda."""
        dc = wx.AutoBufferedPaintDC(self)
        hc_mode = self.hc_mode

        # Determinar colores de fondo y texto
        if hc_mode:
            bg_color = (0, 0, 0)
            dc.SetBackground(wx.Brush(wx.Colour(*bg_color)))
            txt_color = self.COLORS_TEXT_HC.get(self.value, (255, 255, 255))
            if self.value == 0:
                txt_color = (0, 0, 0)
        else:
            bg_color = self.COLORS.get(self.value, (60, 58, 50))
            dc.SetBackground(wx.Brush(wx.Colour(*bg_color)))
            txt_color = self.TEXT_DARK if self.value <= 4 else self.TEXT_LIGHT

        dc.Clear()

        sz = self.GetSize()
        w, h = sz.width, sz.height
        radius = 8

        if not hc_mode:
            # Sombra suave
            dc.SetPen(wx.TRANSPARENT_PEN)
            dc.SetBrush(wx.Brush(wx.Colour(0, 0, 0, 40)))
            dc.DrawRoundedRectangle(3, 3, w - 4, h - 4, radius)
            # Fondo principal
            dc.SetBrush(wx.Brush(wx.Colour(*bg_color)))
            dc.DrawRoundedRectangle(0, 0, w - 2, h - 2, radius)
        else:
            # Modo Alto Contraste
            dc.SetBackground(wx.Brush(wx.BLACK))
            dc.Clear()
            dc.SetPen(wx.Pen(wx.WHITE, 2))
            dc.SetBrush(wx.TRANSPARENT_BRUSH)
            dc.DrawRoundedRectangle(1, 1, w - 2, h - 2, radius)

        # Dibujar Texto o Punto indicador
        if self.value != 0:
            base_size = h // 3
            if self.value < 100:
                font_size = base_size
            elif self.value < 1000:
                font_size = int(base_size * 0.8)
            else:
                font_size = int(base_size * 0.6)

            font_size = max(8, font_size)

            font = wx.Font(font_size, wx.FONTFAMILY_DEFAULT,
                           wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD,
                           faceName="Segoe UI")
            if not font.IsOk():
                font = wx.Font(font_size, wx.FONTFAMILY_SWISS,
                               wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)

            dc.SetFont(font)
            dc.SetTextForeground(wx.Colour(*txt_color))

            txt = str(self.value)
            tw, th = dc.GetTextExtent(txt)
            dc.DrawText(txt, (w - tw) // 2, (h - th) // 2)
        elif hc_mode:
            # Indicador tenue para celdas vacías en modo Alto Contraste
            dot_font = wx.Font(h // 4, wx.FONTFAMILY_DEFAULT,
                               wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
            dc.SetFont(dot_font)
            dc.SetTextForeground(wx.Colour(60, 60, 60))
            dot_txt = "·"
            dtw, dth = dc.GetTextExtent(dot_txt)
            dc.DrawText(dot_txt, (w - dtw) // 2, (h - dth) // 2)

        # Anillo de Foco Accesible
        if self.is_focused:
            focus_color = wx.Colour(0, 120, 255) if not hc_mode else wx.Colour(255, 255, 0)
            dc.SetPen(wx.Pen(focus_color, 4))
            dc.SetBrush(wx.TRANSPARENT_BRUSH)
            dc.DrawRoundedRectangle(2, 2, w - 4, h - 4, radius)
