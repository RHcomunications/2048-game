import wx
import json
import logging
import sys
import os
from sound_manager import SoundManager
from game_logic import Logica2048, coord_nombre
from ui_components import Celda

# Colors/Constants needed for UI
COLOR_FONDO_TABLERO = (187, 173, 160)
COLORES_FONDO = {
    0: (205, 193, 180),  # #cdc1b4
    2: (238, 228, 218),  # #eee4da
    4: (237, 224, 200),  # #ede0c8
    8: (242, 177, 121),  # #f2b179
    16: (245, 149, 99),  # #f59563
    32: (246, 124, 95),  # #f67c5f
    64: (246, 94, 59),   # #f65e3b
    128: (237, 207, 114),# #edcf72
    256: (237, 204, 97), # #edcc61
    512: (237, 200, 80), # #edc850
    1024: (237, 197, 63),# #edc53f
    2048: (237, 194, 46) # #edc22e
}
COLORES_FONDO_HC = {
    0: (0, 0, 0),
    2: (0, 0, 0),
    4: (0, 0, 0),
}
for i in range(1, 17):
    val = 2**i
    COLORES_FONDO_HC[val] = (0, 0, 0)

COLOR_TEXTO_OSCURO = (119, 110, 101)
COLOR_TEXTO_CLARO = (249, 246, 242)
COLORES_TEXTO_HC = {
    2: (0, 255, 255),    # Cyan
    4: (255, 255, 0),    # Yellow
    8: (255, 0, 255),    # Magenta
    16: (0, 255, 0),     # Green
    32: (255, 128, 0),   # Orange
    64: (128, 0, 255),   # Purple
    128: (255, 0, 0),    # Red
    256: (0, 0, 255),    # Blue
    512: (128, 128, 128),# Grey
    1024: (255, 255, 255),# White
    2048: (255, 215, 0), # Gold
}

class VentanaJuego(wx.Frame):
    ARCHIVO_GUARDADO = "savegame.json"

    def __init__(self, parent, title):
        super(VentanaJuego, self).__init__(parent, title=title, size=(700, 800))
        
        # Sonidos
        self.sounds = SoundManager()
        
        # Intentar cargar juego
        self.juego = Logica2048()
        loaded = self.cargar_juego()
        
        if loaded:
            self.tamano = self.juego.tamano
        else:
            self.tamano = self.pedir_tamano()
            self.juego.tamano = self.tamano
            self.juego.iniciar_juego()
        
        self.botones = []
        self.cache_valores = {} # Cache de optimización: (r,c) -> val
        self.foco_actual = [0, 0] # r, c
        self.mensaje_evento_pendiente = "" 
        
        # Accessibility States
        # Accessibility States
        # Sync with Logic
        self.verbosidad = getattr(self.juego, 'verbosidad', 1)
        self.alto_contraste = getattr(self.juego, 'alto_contraste', False)
        print(f"Loaded Config: Verbosity={self.verbosidad}, HighContrast={self.alto_contraste}")
        
        self.historial_anuncios = []
        
        # Logging Setup
        self._setup_logging()
        self.log_event("START", "Juego iniciado")
        
        self.iniciar_ui()
        self.Centre()
        self.Show()
        
        # Foco inicial
        self.botones[0][0].SetFocus()
        self.actualizar_tablero(narrativa_inicial=True)
        
        # Auto-guardado al cerrar
        self.Bind(wx.EVT_CLOSE, self.al_cerrar_ventana)

    def al_cerrar_ventana(self, event):
        self.guardar_juego()
        event.Skip()

    def guardar_juego(self):
        try:
            data = self.juego.to_dict()
            with open(self.ARCHIVO_GUARDADO, "w") as f:
                json.dump(data, f)
            print("Juego guardado.")
        except Exception as e:
            print(f"Error al guardar: {e}")

    def cargar_juego(self):
        if os.path.exists(self.ARCHIVO_GUARDADO):
            try:
                with open(self.ARCHIVO_GUARDADO, "r") as f:
                    data = json.load(f)
                    self.juego.from_dict(data)
                return True
            except Exception as e:
                print(f"Error al cargar: {e}")
        return False

    def _setup_logging(self):
        try:
            # Determinamos la ruta del ejecutable o script
            if getattr(sys, 'frozen', False):
                # Si es el ejecutable (.exe)
                base_pth = os.path.dirname(sys.executable)
            else:
                # Si es el script (.py)
                base_pth = os.path.dirname(os.path.abspath(__file__))
            
            self.log_file = os.path.join(base_pth, "game_events.log")
            
            # Si el directorio actual no es escribible, intentamos en el Escritorio
            if not os.access(base_pth, os.W_OK):
                self.log_file = os.path.join(os.path.expanduser("~"), "Desktop", "game_events.log")

            self.logger = logging.getLogger("2048_Accesible")
            self.logger.setLevel(logging.INFO)
            
            if not self.logger.handlers:
                # Usar encoding utf-8 y asegurar flush
                handler = logging.FileHandler(self.log_file, mode='a', encoding='utf-8')
                formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)
            
            self.logger.info("--- LOG START ---")
            wx.CallAfter(print, f"Log de eventos activo en: {self.log_file}")
            print(f"Logging to: {self.log_file}")
            
        except Exception as e:
            wx.MessageBox(f"No se pudo iniciar el log en {self.log_file if hasattr(self, 'log_file') else 'desconocido'}: {e}", 
                         "Error de Log", wx.ICON_ERROR)

    def log_event(self, category, message):
        # Limpiamos espacios al final (usados para forzar lectura) antes de loguear
        msg_clean = str(message).rstrip()
        msg = f"[{category}] {msg_clean}"
        if hasattr(self, 'logger'):
            self.logger.info(msg)
        print(msg)

    def pedir_tamano(self):
        dlg = wx.TextEntryDialog(None, "Introduce tamaño (4-10):", "Configuración", "4")
        val = 4
        if dlg.ShowModal() == wx.ID_OK:
            try:
                v = int(dlg.GetValue())
                if 4 <= v <= 10: val = v
            except: pass
        dlg.Destroy()
        return val

    def iniciar_ui(self):
        panel = wx.Panel(self)
        self.panel = panel
        panel.SetBackgroundColour(wx.Colour(*COLOR_FONDO_TABLERO))
        
        sizer = wx.GridSizer(self.tamano, self.tamano, 5, 5)
        
        # Pass color maps to Celda
        
        for r in range(self.tamano):
            fila_botones = []
            for c in range(self.tamano):
                celda = Celda(panel, size=80, 
                              r=r, c=c, 
                              colores_fondo=COLORES_FONDO,
                              colores_fondo_hc=COLORES_FONDO_HC,
                              color_texto_oscuro=COLOR_TEXTO_OSCURO,
                              color_texto_claro=COLOR_TEXTO_CLARO,
                              high_contrast_colors=COLORES_TEXTO_HC)
                
                sizer.Add(celda, 1, wx.EXPAND | wx.ALL, 6)
                fila_botones.append(celda)
                
                self.cache_valores[(r,c)] = -1
            self.botones.append(fila_botones)
            
        panel.SetSizer(sizer)
        
        self.Bind(wx.EVT_CHAR_HOOK, self.al_pulsar_tecla)

    def al_pulsar_tecla(self, event):
        code = event.GetKeyCode()
        shift = event.ShiftDown()
        control = event.ControlDown()
        
        self.log_event("INPUT", f"Tecla: {code}, Shift: {shift}, Ctrl: {control}")
        
        if control and code == ord('S'):
            self.guardar_juego()
            if self.verbosidad >= 1:
                self.anunciar("Juego guardado")
            return

        # Reiniciar Juego (Ctrl + R)
        if control and code == ord('R'):
             self.sounds.play('RESTART')
             if os.path.exists(self.ARCHIVO_GUARDADO):
                  try: os.remove(self.ARCHIVO_GUARDADO)
                  except: pass
             
             nueva_tam = self.pedir_tamano()
             if nueva_tam:
                  self.tamano = nueva_tam
                  self.juego = Logica2048()
                  self.juego.tamano = self.tamano
                  self.juego.iniciar_juego()
                  
                  # Re-init UI
                  self.DestroyChildren()
                  self.botones = []
                  self.cache_valores = {}
                  self.iniciar_ui()
                  
                  # Refresh focus
                  self.foco_actual = [0, 0]
                  self.botones[0][0].SetFocus()
                  self.actualizar_tablero(narrativa_inicial=True)
                  self.anunciar("Juego Reiniciado y Reconfigurado")
             return

        # Accessibility Shortcuts
        if control and code == ord('Z'):
            if self.juego.deshacer():
                self.sounds.play('UNDO')
                if self.verbosidad >= 1:
                    self.mensaje_evento_pendiente = "Deshacer"
                self.actualizar_tablero()
            else:
                self.sounds.play('INVALID')
                if self.verbosidad >= 1:
                    self.anunciar("No se puede deshacer")
            return
             
        if code == wx.WXK_F1:
             self.mostrar_ayuda()
             return

        if code == wx.WXK_F5:
             self.toggle_contrast()
             return
             
        if code == ord('V'):
             self.toggle_verbosity()
             return
             
        if code == ord('H'):
             self.anunciar_historial()
             return

        # Mapping definition
        movimiento_map = {
            wx.WXK_UP: 'ARRIBA',
            wx.WXK_NUMPAD_UP: 'ARRIBA',
            wx.WXK_DOWN: 'ABAJO',
            wx.WXK_NUMPAD_DOWN: 'ABAJO',
            wx.WXK_LEFT: 'IZQUIERDA',
            wx.WXK_NUMPAD_LEFT: 'IZQUIERDA',
            wx.WXK_RIGHT: 'DERECHA',
            wx.WXK_NUMPAD_RIGHT: 'DERECHA'
        }

        # Atajos de Información (S / E / Esc)
        if code == ord('S'):
            info = f"Puntaje: {self.juego.puntuacion}"
            self.SetTitle(f"2048 - {info}")
            print(info)
            self.anunciar_en_foco(info, forzar_repeticion=True)
            return
            
        elif code == ord('E'):
            libres_count = len(self.juego.celdas_libres())
            max_f = self.juego.max_ficha
            info = f"{libres_count} casillas libres. Máxima: {max_f}"
            self.SetTitle(f"2048 - {info}")
            print(info)
            self.anunciar_en_foco(info, forzar_repeticion=True)
            return

        elif code == wx.WXK_ESCAPE:
            self.Close()
            return

        # Navegación HOME/END
        elif code == wx.WXK_HOME:
            r, c = self.foco_actual
            if control:
                self.fijar_foco(0, 0) # Ctrl+Home -> Inicio Tablero
            else:
                self.fijar_foco(r, 0) # Home -> Inicio Fila
            return

        elif code == wx.WXK_END:
            r, c = self.foco_actual
            if control:
                self.fijar_foco(self.tamano - 1, self.tamano - 1) # Ctrl+End -> Bottom-Right
            else:
                self.fijar_foco(r, self.tamano - 1) # End -> Row End
            return

        elif code == wx.WXK_PAGEUP:
            r, c = self.foco_actual
            if control:
                self.fijar_foco(0, self.tamano - 1) # Ctrl+PageUp -> Top-Right
            else:
                self.fijar_foco(0, c) # PageUp -> Column Top
            return

        elif code == wx.WXK_PAGEDOWN:
            r, c = self.foco_actual
            if control:
                self.fijar_foco(self.tamano - 1, 0) # Ctrl+PageDown -> Bottom-Left
            else:
                self.fijar_foco(self.tamano - 1, c) # PageDown -> Column Bottom
            return

        # Movimiento
        elif code in movimiento_map:
            if shift:
                # JUEGO
                direccion = movimiento_map[code]
                if self.juego.mover(direccion):
                    self.sounds.play('MOVE')
                    
                    # Narrative Handling
                    prefix = ""
                    if self.verbosidad == 2: # High
                        dirs = {"ARRIBA": "Arriba", "ABAJO": "Abajo", "IZQUIERDA": "Izquierda", "DERECHA": "Derecha"}
                        prefix = f"Movimiento hacia {dirs.get(direccion, direccion)}. "
                    
                    narrativa = ". ".join(self.juego.narrativa)
                    if narrativa:
                        self.mensaje_evento_pendiente = prefix + narrativa
                    elif prefix:
                        self.mensaje_evento_pendiente = prefix
                    
                    # Info in High Verbosity (Score/Free cells)
                    if self.verbosidad == 2:
                        libres = len(self.juego.celdas_libres())
                        info = f"Puntuación: {self.juego.puntuacion}. {libres} casillas libres."
                        if self.mensaje_evento_pendiente:
                             self.mensaje_evento_pendiente += f". {info}"
                        else:
                             self.mensaje_evento_pendiente = info
                    
                    self.actualizar_tablero()
                    
                    if self.juego.juego_terminado():
                        self.sounds.play('GAMEOVER')
                        self.SetTitle("2048 - Juego Terminado")
                        wx.MessageBox(f"Juego Terminado. Puntos: {self.juego.puntuacion}", "Fin")
                        if os.path.exists(self.ARCHIVO_GUARDADO):
                             try: os.remove(self.ARCHIVO_GUARDADO)
                             except: pass
                else:
                    self.sounds.play('INVALID')
            else:
                # NAVEGACION
                dr, dc = 0, 0
                cmd = movimiento_map[code]
                if cmd == 'ARRIBA': dr = -1
                elif cmd == 'ABAJO': dr = 1
                elif cmd == 'IZQUIERDA': dc = -1
                elif cmd == 'DERECHA': dc = 1
                
                self.log_event("NAVIGATE", f"Dir: {dr}, {dc}")
                self.mover_foco(dr, dc)
                
        else:
            event.Skip()

    def fijar_foco(self, r, c):
        if 0 <= r < self.tamano and 0 <= c < self.tamano:
            if [r, c] == self.foco_actual:
                self.anunciar_en_foco()
            else:
                self.log_event("FOCUS_CHANGE", f"Target: {r},{c}")
                self.botones[r][c].SetFocus()
                self.foco_actual = [r, c]
                # Note: No call to anunciar_en_foco here to avoid double-reading 
                # (native focus event already reads the cell)
            self._actualizar_foco_visual()

    def mover_foco(self, dr, dc):
        r, c = self.foco_actual
        nr, nc = r + dr, c + dc
        if 0 <= nr < self.tamano and 0 <= nc < self.tamano:
            self.fijar_foco(nr, nc)
        else:
            # Wall hit: announce current cell again
            self.anunciar_en_foco()

    def _actualizar_foco_visual(self):
         # Iterate all and set focus flag
         # Optimization: only update old and new?
         # But old is lost if we didn't track it.
         # Actually wx handles focus visual? 
         # No, we draw custom ring.
         for r in range(self.tamano):
             for c in range(self.tamano):
                 btn = self.botones[r][c]
                 should_focus = (r == self.foco_actual[0] and c == self.foco_actual[1])
                 if btn.is_focused != should_focus:
                     btn.is_focused = should_focus
                     btn.Refresh()

    def anunciar_en_foco(self, mensaje=None, forzar_repeticion=False):
        """Fuerza la lectura actualizando el nombre del objeto y lanzando evento nativo."""
        r, c = self.foco_actual
        try:
             val = self.juego.tablero[r][c]
             # Si el mensaje ya incluye "casillas libres", pedimos a _get_nombre_accesible que no lo repita
             incluir_libres = "casillas libres" not in (mensaje or "").lower()
             base_name = self._get_nombre_accesible(r, c, val, incluir_libres=incluir_libres)
             
             # Toggle whitespace to force the SR to see a "change" even if text is same
             self.anuncio_toggle = not getattr(self, 'anuncio_toggle', False)
             suffix = " " if self.anuncio_toggle else ""
             
             final_name = base_name + suffix
             if mensaje:
                 # Clean redundant coordinate reading in Low/Normal verbosity
                 if self.verbosidad < 2:
                     final_name = f"{mensaje}{suffix}"
                 else:
                     final_name = f"{mensaje}. {base_name}{suffix}"
             
             # Use force_notify to ensure the screen reader repeats it
             self.botones[r][c].actualizar(val, final_name, force_notify=True)
             
        except Exception as e:
            print(f"Error anunciar foco: {e}")

    def actualizar_tablero(self, narrativa_inicial=False, forzar_silencio_foco=False):
        # Update Window Title
        self.SetTitle(f"2048 - Score: {self.juego.puntuacion} | Best: {self.juego.high_score} | Max: {self.juego.max_ficha}")
        
        # Check High Score Fanfare
        if self.juego.new_high_score:
             self.sounds.play('HIGHSCORE')
             self.juego.new_high_score = False # Reset flag

        # Check Victory
        if getattr(self.juego, 'ganado', False) and not getattr(self.juego, 'victoria_anunciada', False):
            self.juego.victoria_anunciada = True
            self.sounds.play('HIGHSCORE')
            self.anunciar("¡Felicidades! Has alcanzado la ficha 2048. ¡Victoria! Puedes seguir jugando.")
            wx.CallAfter(wx.MessageBox, "¡Has alcanzado la ficha 2048! ¡Victoria!", "2048", wx.OK | wx.ICON_INFORMATION)

        for r in range(self.tamano):
            for c in range(self.tamano):
                val = self.juego.tablero[r][c]
                
                # Check cache
                # Force update if focused cell OR (cache valid AND not focused)
                es_foco = (r==self.foco_actual[0] and c==self.foco_actual[1])
                
                if self.cache_valores.get((r,c)) == val and not es_foco:
                     if not narrativa_inicial: continue
                
                # Update logic
                val_old = self.cache_valores.get((r,c))
                self.cache_valores[(r,c)] = val
                celda = self.botones[r][c]
                
                # Si el mensaje ya incluye "casillas libres", evitamos redundancia
                incluir_libres = "casillas libres" not in (self.mensaje_evento_pendiente or "").lower()
                nombre_accesible = self._get_nombre_accesible(r, c, val, incluir_libres=incluir_libres)
                
                if es_foco and self.mensaje_evento_pendiente:
                    # Aplicamos la misma lógica de limpieza:
                    # Si hay un mensaje de evento (movimiento/fusión), no repetimos la celda en verbosidad reducida.
                    if self.verbosidad < 2:
                        nombre_accesible = self.mensaje_evento_pendiente
                    else:
                        nombre_accesible = f"{self.mensaje_evento_pendiente}. {nombre_accesible}"
                
                if es_foco:
                    self.log_event("CELL_UPDATE_FOCUS", f"Cell {r},{c} with name: {nombre_accesible}")
                
                # Si forzamos silencio, notify es False incluso para el foco
                notify_celda = es_foco and not forzar_silencio_foco
                celda.actualizar(val, nombre_accesible, notify=notify_celda)
        
        # Consume pending message
        if self.mensaje_evento_pendiente:
             self.mensaje_evento_pendiente = ""
             
        if narrativa_inicial:
             r, c = self.foco_actual
             self.botones[r][c].SetFocus()

    def deshacer(self):
        if self.juego.deshacer():
            self.sounds.play('UNDO')
            self.anunciar("Deshacer movimiento")
            self.cache_valores = {}
            self.actualizar_tablero()
        else:
            self.sounds.play('INVALID')
            self.anunciar("No se puede deshacer")

    def toggle_contrast(self):
        self.alto_contraste = not self.alto_contraste
        self.juego.alto_contraste = self.alto_contraste # Sync
        state = "Activado" if self.alto_contraste else "Desactivado"
        
        if self.alto_contraste:
            self.sounds.play('TOGGLE_ON')
        else:
            self.sounds.play('TOGGLE_OFF')
            
        self.anunciar(f"Alto Contraste {state}")
        
        self.cache_valores = {}
        self.Refresh() 
        # Evitamos que actualizar_tablero vuelva a leer la celda tras el anuncio
        self.mensaje_evento_pendiente = "" 
        self.actualizar_tablero(forzar_silencio_foco=True)

    def toggle_verbosity(self):
        self.verbosidad = (self.verbosidad + 1) % 3
        self.juego.verbosidad = self.verbosidad # Sync
        modes = ["Bajo", "Normal", "Alto"]
        mode = modes[self.verbosidad]
        self.anunciar(f"Verbosidad: {mode}")
        # Evitamos que la celda se vuelva a leer justo después del anuncio de verbosidad
        self.mensaje_evento_pendiente = ""
        self.actualizar_tablero(forzar_silencio_foco=True)

    def anunciar_historial(self):
        if not self.historial_anuncios:
             self.anunciar("Historial vacío")
             return
        ultimos = self.historial_anuncios[-3:]
        txt = "Historial: " + ". ".join(ultimos)
        self.anunciar(txt)

    def mostrar_ayuda(self):
        msg = """Atajos de Teclado:
Flechas: Navegar por el tablero
Shift + Flechas: Mover fichas
Inicio / Fin: Inicio / Final de fila
RePág / AvPág: Inicio / Final de columna
Ctrl + Inicio/Fin/RePág/AvPág: Saltar a las 4 esquinas
Ctrl + Z: Deshacer movimiento
F5: Alto Contraste
F1: Ayuda
V: Cambiar Verbosidad
H: Historial de eventos
Ctrl + S: Guardar
Ctrl + R: Reiniciar"""
        wx.MessageBox(msg, "Ayuda 2048", wx.OK | wx.ICON_INFORMATION)

    def anunciar(self, mensaje):
        if not mensaje: return
        self.log_event("ANNOUNCE", mensaje)
        if not self.historial_anuncios or self.historial_anuncios[-1] != mensaje:
            self.historial_anuncios.append(mensaje)
            if len(self.historial_anuncios) > 20:
                self.historial_anuncios.pop(0)

        self.anunciar_en_foco(mensaje, forzar_repeticion=True)

    def _get_nombre_accesible(self, r, c, val, incluir_libres=True):
        coord = coord_nombre(r, c)
        txt_val = str(val) if val != 0 else "Libre"
        
        if self.verbosidad == 0: # Bajo
            return txt_val
            
        elif self.verbosidad == 2: # Alto
            fila = coord[0]
            col = coord[1:]
            base = f"Fila {fila} Columna {col}: {txt_val}"
            # En modo alto, damos el conteo de libres si la celda está vacía y se solicita
            if val == 0 and incluir_libres:
                count = len(self.juego.celdas_libres())
                base += f". {count} casillas libres"
            return base
            
        else: # Normal (1)
            return f"{coord}: {txt_val}"
