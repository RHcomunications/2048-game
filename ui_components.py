"""Componentes UI accesibles para el tablero 2048."""
import ctypes
import logging

import wx

from constants import EVENT_OBJECT_NAMECHANGE, OBJID_CLIENT, CHILDID_SELF

user32 = ctypes.windll.user32
# Define signature to avoid unwanted 64-bit expansion of negative args
user32.NotifyWinEvent.argtypes = [ctypes.c_uint, ctypes.c_void_p, ctypes.c_long, ctypes.c_long]
user32.NotifyWinEvent.restype = None

logger = logging.getLogger("2048_Accesible")

class AccessibleCustom(wx.Accessible):
    def __init__(self, win, name=""):
        super().__init__(win)
        self.name = name
        
    def GetName(self, childId):
        if childId == wx.ACC_SELF:
            return wx.ACC_OK, self.name
        return wx.ACC_FALSE, ""

class Celda(wx.Panel):
    def __init__(self, parent, size, r, c, config):
        super().__init__(parent, size=(size, size))
        self.r = r
        self.c = c
        self.value = 0
        self.acc_name = ""
        self.is_focused = False
        self.hc_mode = False
        
        self.COLORS = config['colores_fondo']
        self.COLORS_HC = config['colores_fondo_hc']
        self.TEXT_DARK = config['color_texto_oscuro']
        self.TEXT_LIGHT = config['color_texto_claro']
        self.COLORS_TEXT_HC = config['high_contrast_colors']
        
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.Bind(wx.EVT_PAINT, self.on_paint)
        
        # Accessibility Init
        self.accessible_obj = AccessibleCustom(self, self._get_acc_name())
        self.SetAccessible(self.accessible_obj)

    def _get_acc_name(self):
        # We allow dynamic update of name
        return self.acc_name if self.acc_name else ""

    def actualizar(self, value, nombre_accesible, notify=False, force_notify=False, hc_mode=None):
        self.value = value
        if hc_mode is not None:
            self.hc_mode = hc_mode
        
        # Update Accessible Name
        changed = False
        if nombre_accesible != self.acc_name:
            self.acc_name = nombre_accesible
            self.accessible_obj.name = self.acc_name
            changed = True
            
        if self.GetHandle():
            # Crucial: Solo notificamos a Windows si la celda tiene el FOCO (notify=True)
            # o si forzamos la repetición (force_notify=True).
            # Si 'changed' es True pero no tiene el foco, actualizamos el nombre interno
            # pero NO lanzamos el evento WinAPI para evitar lecturas dobles/no deseadas.
            if (changed and notify) or force_notify:
                 # Clean name for log
                 nombre_log = str(self.acc_name).rstrip()
                 logger.info(f"[WINAPI_NOTIFY] Cell {self.r},{self.c} - Name: {nombre_log} - Force: {force_notify}")
                 user32.NotifyWinEvent(EVENT_OBJECT_NAMECHANGE, self.GetHandle(), OBJID_CLIENT, CHILDID_SELF)
        
        self.Refresh()

    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        
        # Determine Check Parent High Contrast logic?
        # Ideally passed in params or checked from parent.
        # But we don't have direct access to 'parent.alto_contraste' easily without coupling.
        # Let's check a property or method if exists
        
        hc_mode = self.hc_mode

        # Background
        if hc_mode:
            # Black bg, Colored Text
            bg_color = (0,0,0)
            dc.SetBackground(wx.Brush(wx.Colour(*bg_color)))
            
            # Text Color based on value map
            val_idx = self.value
            txt_color = self.COLORS_TEXT_HC.get(val_idx, (255, 255, 255))
            if self.value == 0: txt_color = (0,0,0) # Invisible
            
        else:
            bg_color = self.COLORS.get(self.value, (60, 58, 50))
            dc.SetBackground(wx.Brush(wx.Colour(*bg_color)))
            
            if self.value <= 4:
                txt_color = self.TEXT_DARK
            else:
                txt_color = self.TEXT_LIGHT
        
        dc.Clear()
        
        # Text
        if self.value != 0:
            font_size = 32 if self.value < 100 else 24 if self.value < 1000 else 18
            font = wx.Font(font_size, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
            dc.SetFont(font)
            dc.SetTextForeground(wx.Colour(*txt_color))
            
            txt = str(self.value)
            w, h = dc.GetTextExtent(txt)
            
            sz = self.GetSize()
            x = (sz.width - w) // 2
            y = (sz.height - h) // 2
            dc.DrawText(txt, x, y)
            
        # Focus Ring
        if self.is_focused:
            pen = wx.Pen(wx.Colour(0, 100, 255) if not hc_mode else wx.Colour(255, 255, 0), 4)
            dc.SetPen(pen)
            dc.SetBrush(wx.Brush("TRANSPARENT", wx.TRANSPARENT))
            sz = self.GetSize()
            dc.DrawRectangle(2, 2, sz.width-4, sz.height-4)
        elif hc_mode:
            # White border for grid in HC
            pen = wx.Pen(wx.Colour(255, 255, 255), 2)
            dc.SetPen(pen)
            dc.SetBrush(wx.Brush("TRANSPARENT", wx.TRANSPARENT))
            sz = self.GetSize()
            dc.DrawRectangle(0, 0, sz.width, sz.height)
