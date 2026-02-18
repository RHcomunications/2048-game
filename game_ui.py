import wx
import logging
import logging.handlers
import sys
import os
from sound_manager import SoundManager
from game_logic import Logica2048, coord_nombre
from ui_components import Celda, AccessibleCustom
from constants import (
    COLOR_FONDO_TABLERO, COLORES_FONDO,
    COLOR_TEXTO_OSCURO, COLOR_TEXTO_CLARO, COLORES_TEXTO_HC,
    VALOR_VICTORIA
)


class VentanaJuego(wx.Frame):
    """
    Ventana principal de la aplicación 2048.
    Gestiona la interfaz, eventos de teclado y retroalimentación accesible.
    """
    # E2-06: Mapa de movimiento como constante de clase, no se recrea en cada keypress
    _MOVIMIENTO_MAP = {
        wx.WXK_UP: 'ARRIBA', wx.WXK_NUMPAD_UP: 'ARRIBA',
        wx.WXK_DOWN: 'ABAJO', wx.WXK_NUMPAD_DOWN: 'ABAJO',
        wx.WXK_LEFT: 'IZQUIERDA', wx.WXK_NUMPAD_LEFT: 'IZQUIERDA',
        wx.WXK_RIGHT: 'DERECHA', wx.WXK_NUMPAD_RIGHT: 'DERECHA',
        # A2-01: Teclas numpad (NumLock activo) para movimiento
        wx.WXK_NUMPAD8: 'ARRIBA',
        wx.WXK_NUMPAD2: 'ABAJO',
        wx.WXK_NUMPAD4: 'IZQUIERDA',
        wx.WXK_NUMPAD6: 'DERECHA',
    }
    def __init__(self, parent, title):
        """Inicializa la ventana del juego y componentes principales."""
        super(VentanaJuego, self).__init__(parent, title=title, size=(700, 800))

        # Sonidos
        self.sounds = SoundManager()

        # H2-02: auto_init=False para no generar tablero descartable
        self.juego = Logica2048(auto_init=False)
        loaded = self.juego.cargar_juego()

        if loaded:
            self.tamano = self.juego.tamano
        else:
            self.tamano = self.pedir_tamano()
            if self.tamano is None:
                self.tamano = 4
            self.juego.tamano = self.tamano
            self.juego.iniciar_juego()

        self.botones = []
        self.cache_valores = {}
        self.foco_actual = [0, 0]
        self.mensaje_evento_pendiente = ""

        # Accessibility — Sync con Logic
        self.verbosidad = getattr(self.juego, 'verbosidad', 1)
        self.alto_contraste = getattr(self.juego, 'alto_contraste', False)

        self.historial_anuncios = []
        self.wall_hit_count = 0
        self.last_wall_hit_key = None

        # A-05: Toggle con zero-width space para forzar relectura del SR
        self._anuncio_toggle = False

        # E-09: Setup logging con rotación
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
        self.Bind(wx.EVT_SIZE, self.al_redimensionar)

    def al_redimensionar(self, event):
        """Refresca celdas al redimensionar la ventana."""
        self.Layout()
        if hasattr(self, 'botones'):
            for fila in self.botones:
                for celda in fila:
                    celda.Refresh()
        event.Skip()

    def al_cerrar_ventana(self, event):
        """Guarda estado y limpia recursos al cerrar."""
        self.juego.guardar_ajustes()
        self.juego.guardar_juego_estado()
        self.log_event("SAVE", "Juego y ajustes guardados al cerrar.")
        if hasattr(self, 'sounds'):
            self.sounds.cleanup()
        event.Skip()

    def _setup_logging(self):
        """Configura logging con RotatingFileHandler (E-09)."""
        try:
            if getattr(sys, 'frozen', False):
                base_pth = os.path.dirname(sys.executable)
            else:
                base_pth = os.path.dirname(os.path.abspath(__file__))

            self.log_file = os.path.join(base_pth, "game_events.log")

            if not os.access(base_pth, os.W_OK):
                self.log_file = os.path.join(os.path.expanduser("~"), "Desktop", "game_events.log")

            self.logger = logging.getLogger("2048_Accesible")
            self.logger.setLevel(logging.INFO)

            if not self.logger.handlers:
                # E-09: RotatingFileHandler — max 1 MB, 3 backups
                handler = logging.handlers.RotatingFileHandler(
                    self.log_file, mode='a', encoding='utf-8',
                    maxBytes=1_048_576, backupCount=3
                )
                formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)

            self.logger.info("--- LOG START ---")
            self.logger.info(f"Log de eventos activo en: {self.log_file}")

        except Exception as e:
            wx.MessageBox(
                f"No se pudo iniciar el log en "
                f"{self.log_file if hasattr(self, 'log_file') else 'desconocido'}: {e}",
                "Error de Log", wx.ICON_ERROR
            )

    def log_event(self, category, message):
        """Registra un evento en el log del juego."""
        msg_clean = str(message).rstrip()
        msg = f"[{category}] {msg_clean}"
        if hasattr(self, 'logger'):
            self.logger.info(msg)

    # H-08: Manejar cancelación del diálogo retornando None
    def pedir_tamano(self):
        """Pide tamaño de tablero al usuario. Retorna None si cancela."""
        dlg = wx.TextEntryDialog(
            None,
            "Introduce el tamaño del tablero.\n"
            "Valores válidos: 4 a 10.\n"
            "Predeterminado: 4.",
            "Configuración de Tablero", "4"
        )
        val = None
        if dlg.ShowModal() == wx.ID_OK:
            try:
                v = int(dlg.GetValue())
                if 4 <= v <= 10:
                    val = v
                else:
                    wx.MessageBox(
                        f"Tamaño {v} fuera de rango (4-10). Usando defecto 4.",
                        "Aviso", wx.ICON_WARNING
                    )
                    val = 4
            except ValueError:
                wx.MessageBox(
                    "Entrada no válida. Usando defecto 4.",
                    "Aviso", wx.ICON_WARNING
                )
                val = 4
        dlg.Destroy()
        return val

    def iniciar_ui(self):
        """Construye la interfaz gráfica del tablero."""
        # H3-03: Aplicar fondo según modo HC al iniciar
        if self.alto_contraste:
            bg_color = wx.Colour(0, 0, 0)
        else:
            bg_color = wx.Colour(*COLOR_FONDO_TABLERO)
        self.SetBackgroundColour(bg_color)

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        panel = wx.Panel(self)
        self.panel = panel
        panel.SetBackgroundColour(bg_color)

        # A-02: Exponer panel como ROLE_SYSTEM_TABLE para lectores de pantalla
        panel_acc = AccessibleCustom(
            panel,
            name=f"Tablero {self.tamano} por {self.tamano}",
            role=wx.ROLE_SYSTEM_TABLE
        )
        panel.SetAccessible(panel_acc)

        sizer = wx.GridSizer(self.tamano, self.tamano, 10, 10)

        celda_config = {
            'colores_fondo': COLORES_FONDO,
            'color_texto_oscuro': COLOR_TEXTO_OSCURO,
            'color_texto_claro': COLOR_TEXTO_CLARO,
            'high_contrast_colors': COLORES_TEXTO_HC
        }

        for r in range(self.tamano):
            fila_botones = []
            for c in range(self.tamano):
                celda = Celda(panel, size=80, r=r, c=c, config=celda_config)
                sizer.Add(celda, 1, wx.EXPAND | wx.ALL, 2)
                fila_botones.append(celda)
                self.cache_valores[(r, c)] = -1
            self.botones.append(fila_botones)

        panel.SetSizer(sizer)
        main_sizer.Add(panel, 1, wx.EXPAND | wx.ALL, 15)
        self.SetSizer(main_sizer)

        self.Bind(wx.EVT_CHAR_HOOK, self.al_pulsar_tecla)

    # ─── Manejo de Teclado (E-03: separado en métodos) ───

    def al_pulsar_tecla(self, event):
        """Dispatcher principal de teclas."""
        code = event.GetKeyCode()
        shift = event.ShiftDown()
        control = event.ControlDown()

        self.log_event("INPUT", f"Tecla: {code}, Shift: {shift}, Ctrl: {control}")

        # Atajos con Ctrl
        if control:
            if self._manejar_ctrl_atajo(code):
                return

        # Teclas de función
        if code == wx.WXK_F1:
            self.mostrar_ayuda()
            return
        if code == wx.WXK_F5:
            self.toggle_contrast()
            return

        # E2-01: Normalizar letra a mayúscula para que funcione con/sin CapsLock
        letra = chr(code).upper() if 32 <= code < 127 else None

        # Atajos de una letra (A-03: documentados en ayuda)
        if letra == 'V':
            self.toggle_verbosity()
            return
        if letra == 'H':
            sug = self.juego.obtener_sugerencia()
            self.anunciar(f"Sugerencia: {sug}")
            return
        if letra == 'I':
            resumen = self.juego.obtener_resumen()
            self.anunciar(resumen)
            return
        if letra == 'L':
            self.anunciar_historial()
            return
        # A-10: Repetir último anuncio
        if letra == 'R' and not control:
            self._repetir_ultimo_anuncio()
            return
        if letra == 'S':
            info = f"Puntaje: {self.juego.puntuacion}"
            self.SetTitle(f"2048 - {info}")
            self.log_event("INFO", info)
            self.anunciar_en_foco(info)
            return
        if letra == 'E':
            libres_count = len(self.juego.celdas_libres())
            max_f = self.juego.max_ficha
            info = f"{libres_count} casillas libres. Máxima: {max_f}"
            self.SetTitle(f"2048 - {info}")
            self.log_event("INFO", info)
            self.anunciar_en_foco(info)
            return
        # A3-01: Lectura rápida de fila/columna
        if letra == 'F':
            self._leer_fila_actual()
            return
        if letra == 'C':
            self._leer_columna_actual()
            return
        if code == wx.WXK_ESCAPE:
            self.Close()
            return

        # Navegación Home/End/PageUp/PageDown
        if self._manejar_navegacion_especial(code, control):
            return

        # Movimiento / Navegación con flechas y numpad (A2-01)
        if code in self._MOVIMIENTO_MAP:
            direccion = self._MOVIMIENTO_MAP[code]
            # Numpad numéricos (2/4/6/8) ejecutan movimiento directamente
            numpad_directo = code in (
                wx.WXK_NUMPAD8, wx.WXK_NUMPAD2,
                wx.WXK_NUMPAD4, wx.WXK_NUMPAD6
            )
            if shift or numpad_directo:
                self._ejecutar_movimiento(direccion)
            else:
                self._navegar_con_flechas(direccion, code)
        else:
            event.Skip()

    def _manejar_ctrl_atajo(self, code):
        """Maneja atajos Ctrl+tecla. Retorna True si consumió el evento."""
        if code == ord('S'):
            self.juego.guardar_juego_estado()
            self.log_event("SAVE", "Juego guardado manualmente.")
            # A2-05: Siempre dar feedback de guardado (sonido + anuncio)
            self.sounds.play('TOGGLE_ON')
            if self.verbosidad >= 1:
                self.anunciar("Juego guardado")
            return True

        if code == ord('R'):
            self._reiniciar_juego()
            return True

        if code == ord('Z'):
            if self.juego.deshacer():
                self.sounds.play('UNDO')
                if self.verbosidad >= 1:
                    self.mensaje_evento_pendiente = "Deshacer"
                self.actualizar_tablero()
            else:
                self.sounds.play('INVALID')
                if self.verbosidad >= 1:
                    self.anunciar("No se puede deshacer")
            return True

        return False

    # H-02: Preservar high_score al reiniciar
    def _reiniciar_juego(self):
        """Reinicia el juego preservando high_score."""
        self.sounds.play('RESTART')
        old_high_score = self.juego.high_score

        nueva_tam = self.pedir_tamano()
        if nueva_tam is not None:
            self.tamano = nueva_tam

            # H4-01: Persistir ajustes antes de crear nuevo objeto
            self.juego.guardar_ajustes()

            # H2-01: Borrar savegame SOLO después de confirmar reinicio
            if os.path.exists(self.juego.ARCHIVO_GUARDADO):
                try:
                    os.remove(self.juego.ARCHIVO_GUARDADO)
                except Exception:
                    pass

            # H2-03: Usar auto_init=False + pasar tamaño directamente
            self.juego = Logica2048(tamano=self.tamano, auto_init=False)
            self.juego.high_score = old_high_score  # H-02
            self.juego.iniciar_juego()

            # H3-02: Sincronizar config de accesibilidad al nuevo objeto
            self.juego.verbosidad = self.verbosidad
            self.juego.alto_contraste = self.alto_contraste

            # Re-init UI
            self.DestroyChildren()
            self.botones = []
            self.cache_valores = {}
            # E3-04: Limpiar historial de anuncios de la partida anterior
            self.historial_anuncios = []
            self.iniciar_ui()

            self.foco_actual = [0, 0]
            self.botones[0][0].SetFocus()
            self.actualizar_tablero(narrativa_inicial=True)
            self.anunciar("Juego Reiniciado y Reconfigurado")

    def _manejar_navegacion_especial(self, code, control):
        """Maneja Home/End/PageUp/PageDown. Retorna True si consumió el evento."""
        r, c = self.foco_actual

        if code == wx.WXK_HOME:
            if control:
                self.fijar_foco(0, 0)
            else:
                self.fijar_foco(r, 0)
            return True

        if code == wx.WXK_END:
            if control:
                self.fijar_foco(self.tamano - 1, self.tamano - 1)
            else:
                self.fijar_foco(r, self.tamano - 1)
            return True

        if code == wx.WXK_PAGEUP:
            if control:
                self.fijar_foco(0, self.tamano - 1)
            else:
                self.fijar_foco(0, c)
            return True

        if code == wx.WXK_PAGEDOWN:
            if control:
                self.fijar_foco(self.tamano - 1, 0)
            else:
                self.fijar_foco(self.tamano - 1, c)
            return True

        return False

    def _ejecutar_movimiento(self, direccion):
        """Ejecuta un movimiento de fichas y maneja resultado."""
        if self.juego.mover(direccion):
            self.sounds.play('MOVE')

            narrativa = ". ".join(self.juego.narrativa)
            self.mensaje_evento_pendiente = narrativa

            if self.verbosidad == 2 and narrativa:
                libres = len(self.juego.celdas_libres())
                info = f"Puntuación: {self.juego.puntuacion}. {libres} casillas libres."
                self.mensaje_evento_pendiente += f". {info}"

            self.actualizar_tablero()

            if self.juego.juego_terminado():
                self._manejar_game_over()
        else:
            self.sounds.play('INVALID')
            if self.verbosidad == 2:
                self.anunciar("Movimiento no posible")

    # A-08: Restaurar foco tras game over
    def _manejar_game_over(self):
        """Maneja el fin del juego con anuncio accesible y restauración de foco."""
        self.sounds.play('GAMEOVER')
        self.SetTitle("2048 - Juego Terminado")
        txt_fin = f"Juego Terminado. Puntaje final: {self.juego.puntuacion}"
        self.anunciar(txt_fin)

        # A-08: Guardar foco actual antes del modal
        foco_r, foco_c = self.foco_actual

        wx.CallAfter(self._mostrar_game_over_dialog, foco_r, foco_c)

        if os.path.exists(self.juego.ARCHIVO_GUARDADO):
            try:
                os.remove(self.juego.ARCHIVO_GUARDADO)
            except Exception:
                pass

    def _mostrar_game_over_dialog(self, foco_r, foco_c):
        """Muestra diálogo de game over y restaura foco después."""
        wx.MessageBox(
            f"Juego Terminado. Puntos: {self.juego.puntuacion}", "Fin"
        )
        # A-08: Restaurar foco tras cerrar el modal
        if 0 <= foco_r < self.tamano and 0 <= foco_c < self.tamano:
            self.botones[foco_r][foco_c].SetFocus()

    def _navegar_con_flechas(self, direccion, key_code):
        """Navega por el tablero con flechas."""
        dr, dc = 0, 0
        if direccion == 'ARRIBA':
            dr = -1
        elif direccion == 'ABAJO':
            dr = 1
        elif direccion == 'IZQUIERDA':
            dc = -1
        elif direccion == 'DERECHA':
            dc = 1

        self.log_event("NAVIGATE", f"Dir: {dr}, {dc}")
        self.mover_foco(dr, dc, key_code=key_code)

    # ─── Gestión de Foco ───

    def fijar_foco(self, r, c):
        """Fija el foco en la celda (r, c)."""
        if 0 <= r < self.tamano and 0 <= c < self.tamano:
            if [r, c] == self.foco_actual:
                self.anunciar_en_foco()
            else:
                self.log_event("FOCUS_CHANGE", f"Target: {r},{c}")
                self.botones[r][c].SetFocus()
                self.foco_actual = [r, c]
            self._actualizar_foco_visual()

    def mover_foco(self, dr, dc, key_code=None):
        """Mueve el foco en la dirección dada con detección de bordes."""
        r, c = self.foco_actual
        nr, nc = r + dr, c + dc
        if 0 <= nr < self.tamano and 0 <= nc < self.tamano:
            self.wall_hit_count = 0
            self.last_wall_hit_key = None
            self.fijar_foco(nr, nc)
        else:
            # A-04: Sonido en primer wall hit, anuncio verbal en segundo
            if self.last_wall_hit_key == key_code:
                self.wall_hit_count += 1
            else:
                self.wall_hit_count = 1
                self.last_wall_hit_key = key_code

            if self.wall_hit_count >= 2:
                self.anunciar("Borde")
                self.wall_hit_count = 0
            else:
                # A-04: Sonido sutil en primer intento
                self.sounds.play('WALL_SOFT')

    def _actualizar_foco_visual(self):
        """Actualiza el anillo visual de foco en todas las celdas."""
        for r in range(self.tamano):
            for c in range(self.tamano):
                btn = self.botones[r][c]
                should_focus = (r == self.foco_actual[0] and c == self.foco_actual[1])
                if btn.is_focused != should_focus:
                    btn.is_focused = should_focus
                    btn.Refresh()

    # ─── Anuncios Accesibles ───

    def anunciar_en_foco(self, mensaje=None):
        """Fuerza relectura actualizando el nombre del objeto con evento nativo."""
        r, c = self.foco_actual
        try:
            val = self.juego.tablero[r][c]
            incluir_libres = "casillas libres" not in (mensaje or "").lower()
            base_name = self._get_nombre_accesible(r, c, val, incluir_libres=incluir_libres)

            # A-05: Zero-width space para forzar detección de cambio
            self._anuncio_toggle = not self._anuncio_toggle
            suffix = "\u200B" if self._anuncio_toggle else ""

            final_name = base_name + suffix
            if mensaje:
                if self.verbosidad < 2:
                    final_name = f"{mensaje}{suffix}"
                else:
                    final_name = f"{mensaje}. {base_name}{suffix}"

            self.botones[r][c].actualizar(val, final_name, force_notify=True)

        except Exception as e:
            logging.error(f"Error anunciar foco: {e}")

    def actualizar_tablero(self, narrativa_inicial=False, forzar_silencio_foco=False):
        """Actualiza todas las celdas del tablero y maneja eventos."""
        # A2-04: Título con indicador HC si activo
        hc_tag = " [HC]" if self.alto_contraste else ""
        self.SetTitle(
            f"2048 - Score: {self.juego.puntuacion} | "
            f"Best: {self.juego.high_score} | Max: {self.juego.max_ficha}{hc_tag}"
        )

        # High Score Fanfare
        if self.juego.new_high_score:
            self.sounds.play('HIGHSCORE')
            self.juego.new_high_score = False

        # Hitos de Victoria
        hitos_objetivo = [2048, 4096, 8192, 16384, 32768, 65536]
        max_f = self.juego.max_ficha
        for h in hitos_objetivo:
            if max_f >= h and h not in self.juego.hitos_alcanzados:
                self.juego.hitos_alcanzados.append(h)
                self.sounds.play('HIGHSCORE')
                if h == 2048:
                    msg_v = f"¡Increíble! Has alcanzado la ficha {h}. ¡Has ganado el juego! Puedes seguir superando tus límites."
                else:
                    msg_v = f"¡Increíble! Has alcanzado la ficha {h}. Has superado el hito de {h}. ¡Eres una leyenda!"

                self.anunciar(msg_v)
                # A-08: Guardar foco antes del modal
                foco_r, foco_c = self.foco_actual
                wx.CallAfter(self._mostrar_hito_dialog, msg_v, foco_r, foco_c)

        if max_f >= VALOR_VICTORIA:
            self.juego.ganado = True

        # Actualizar celdas
        for r in range(self.tamano):
            for c in range(self.tamano):
                val = self.juego.tablero[r][c]
                es_foco = (r == self.foco_actual[0] and c == self.foco_actual[1])

                if self.cache_valores.get((r, c)) == val and not es_foco:
                    if not narrativa_inicial:
                        continue

                self.cache_valores[(r, c)] = val
                celda = self.botones[r][c]

                incluir_libres = "casillas libres" not in (self.mensaje_evento_pendiente or "").lower()
                nombre_accesible = self._get_nombre_accesible(r, c, val, incluir_libres=incluir_libres)

                if es_foco and self.mensaje_evento_pendiente:
                    if self.verbosidad < 2:
                        nombre_accesible = self.mensaje_evento_pendiente
                    else:
                        nombre_accesible = f"{self.mensaje_evento_pendiente}. {nombre_accesible}"

                if es_foco:
                    self.log_event("CELL_UPDATE_FOCUS", f"Cell {r},{c} with name: {nombre_accesible}")

                notify_celda = es_foco and not forzar_silencio_foco
                celda.actualizar(val, nombre_accesible, notify=notify_celda, hc_mode=self.alto_contraste)

        # Consumir mensaje pendiente
        if self.mensaje_evento_pendiente:
            self.mensaje_evento_pendiente = ""

        if narrativa_inicial:
            welcome = f"Bienvenido a 2048 Accesible. Tablero de {self.tamano} por {self.tamano} listo."
            self.anunciar(welcome)
            r, c = self.foco_actual
            self.botones[r][c].SetFocus()

    # A-08: Restaurar foco después de diálogos de hitos
    def _mostrar_hito_dialog(self, msg, foco_r, foco_c):
        """Muestra diálogo de hito y restaura foco."""
        wx.MessageBox(msg, "Hito alcanzado", wx.OK | wx.ICON_INFORMATION)
        if 0 <= foco_r < self.tamano and 0 <= foco_c < self.tamano:
            self.botones[foco_r][foco_c].SetFocus()

    # ─── Toggles de Accesibilidad ───

    def toggle_contrast(self):
        """Alterna modo de alto contraste."""
        self.alto_contraste = not self.alto_contraste
        self.juego.alto_contraste = self.alto_contraste
        state = "Activado" if self.alto_contraste else "Desactivado"

        if self.alto_contraste:
            self.sounds.play('TOGGLE_ON')
        else:
            self.sounds.play('TOGGLE_OFF')

        # A2-02: Cambiar fondo del frame y panel según modo HC
        if self.alto_contraste:
            bg = wx.Colour(0, 0, 0)
        else:
            bg = wx.Colour(*COLOR_FONDO_TABLERO)
        self.SetBackgroundColour(bg)
        for child in self.GetChildren():
            if isinstance(child, wx.Panel):
                child.SetBackgroundColour(bg)

        self.anunciar(f"Alto Contraste {state}")
        self.juego.guardar_ajustes()

        self.cache_valores = {}
        self.Refresh()
        self.mensaje_evento_pendiente = ""
        self.actualizar_tablero(forzar_silencio_foco=True)

    def toggle_verbosity(self):
        """Cicla entre los tres niveles de verbosidad."""
        self.verbosidad = (self.verbosidad + 1) % 3
        self.juego.verbosidad = self.verbosidad
        modes = ["Bajo", "Normal", "Alto"]
        mode = modes[self.verbosidad]
        self.anunciar(f"Verbosidad: {mode}")
        self.juego.guardar_ajustes()
        self.mensaje_evento_pendiente = ""
        self.actualizar_tablero(forzar_silencio_foco=True)

    # ─── Historial, Lectura Rápida y Anuncios ───

    # A3-01: Lectura rápida de fila completa
    def _leer_fila_actual(self):
        """Lee todos los valores de la fila donde está el foco."""
        r = self.foco_actual[0]
        fila_letter = chr(ord('A') + r)
        valores = []
        for c in range(self.tamano):
            val = self.juego.tablero[r][c]
            valores.append(str(val) if val != 0 else "Libre")
        txt = f"Fila {fila_letter}: {', '.join(valores)}"
        self.anunciar(txt)

    # A3-01: Lectura rápida de columna completa
    def _leer_columna_actual(self):
        """Lee todos los valores de la columna donde está el foco."""
        c = self.foco_actual[1]
        col_num = c + 1
        valores = []
        for r in range(self.tamano):
            val = self.juego.tablero[r][c]
            valores.append(str(val) if val != 0 else "Libre")
        txt = f"Columna {col_num}: {', '.join(valores)}"
        self.anunciar(txt)

    def anunciar_historial(self):
        """Lee los últimos 20 anuncios del historial."""
        if not self.historial_anuncios:
            self.anunciar("Historial vacío")
            return
        ultimos = self.historial_anuncios[-20:]
        txt = "Historial: " + ". ".join(ultimos)
        self.anunciar(txt)

    # A-10: Repetir último anuncio con tecla R
    def _repetir_ultimo_anuncio(self):
        """Repite el último anuncio del historial."""
        if self.historial_anuncios:
            ultimo = self.historial_anuncios[-1]
            self.anunciar_en_foco(ultimo)
        else:
            self.anunciar_en_foco("Sin anuncios previos")

    # A-07 / E-10: Ayuda mejorada con documentación completa
    def mostrar_ayuda(self):
        """Muestra diálogo de ayuda con atajos de teclado documentados."""
        msg = """Atajos de Teclado — 2048 Accesible

═══ MOVIMIENTO DEL JUEGO ═══
Shift + Flechas: Mover fichas en esa dirección
  (¡Importante! Sin Shift solo navegas, no mueves fichas)

═══ NAVEGACIÓN POR EL TABLERO ═══
Flechas (sin Shift): Navegar celda por celda
Inicio / Fin: Ir al inicio o final de la fila actual
RePág / AvPág: Ir al inicio o final de la columna actual
Ctrl + Inicio: Esquina superior izquierda
Ctrl + Fin: Esquina inferior derecha
Ctrl + RePág: Esquina superior derecha
Ctrl + AvPág: Esquina inferior izquierda

═══ ACCIONES ═══
Ctrl + Z: Deshacer movimiento (máximo 3 veces)
Ctrl + S: Guardar partida
Ctrl + R: Reiniciar / Nueva partida
Escape: Salir del juego

═══ INFORMACIÓN (teclas sin modificador) ═══
S: Consultar puntaje actual
E: Consultar casillas libres y ficha máxima
I: Resumen completo del estado
H: Sugerencia de mejor movimiento
L: Historial de los últimos 20 anuncios
R: Repetir el último anuncio
V: Cambiar nivel de verbosidad (Bajo / Normal / Alto)

═══ ACCESIBILIDAD ═══
F1: Esta ayuda
F5: Activar/Desactivar modo Alto Contraste

═══ LECTURA RÁPIDA ═══
F: Leer todos los valores de la fila actual
C: Leer todos los valores de la columna actual

Nota: Las teclas de una sola letra (S, E, I, H, L, R, V, F, C)
son atajos rápidos que solo funcionan cuando el foco
está en el tablero de juego.
Numpad 2/4/6/8 (NumLock activo): Mover fichas directamente."""
        wx.MessageBox(msg, "Ayuda 2048 Accesible", wx.OK | wx.ICON_INFORMATION)

    def anunciar(self, mensaje):
        """Anuncia un mensaje vía lector de pantalla y lo registra en historial."""
        if not mensaje:
            return
        self.log_event("ANNOUNCE", mensaje)
        if not self.historial_anuncios or self.historial_anuncios[-1] != mensaje:
            self.historial_anuncios.append(mensaje)
            if len(self.historial_anuncios) > 20:
                self.historial_anuncios.pop(0)

        self.anunciar_en_foco(mensaje)

    def _get_nombre_accesible(self, r, c, val, incluir_libres=True):
        """Genera el nombre accesible de una celda según nivel de verbosidad."""
        coord = coord_nombre(r, c)
        txt_val = str(val) if val != 0 else "Libre"

        if self.verbosidad == 0:  # Bajo
            return txt_val

        elif self.verbosidad == 2:  # Alto
            fila = coord[0]
            col = coord[1:]
            base = f"Fila {fila} Columna {col}: {txt_val}"
            if val == 0 and incluir_libres:
                count = len(self.juego.celdas_libres())
                base += f". {count} casillas libres"
            return base

        else:  # Normal (1)
            return f"{coord}: {txt_val}"
