"""Ventana de interfaz accesible para el juego 2048 (Vista/Controlador)."""
import json
import logging
import logging.handlers
import os
import sys
from typing import List, Optional, Tuple

import wx

from constants import (
    COLOR_FONDO_TABLERO,
    COLOR_TEXTO_CLARO,
    COLOR_TEXTO_OSCURO,
    COLORES_FONDO,
    COLORES_TEXTO_HC,
    VALOR_VICTORIA,
)
from game_logic import Logica2048, MoveResult
from sound_manager import SoundManager
from ui_components import AccessibleCustom, Celda


# Rutas de almacenamiento persistente en %APPDATA%
def obtener_ruta_appdata() -> str:
    appdata = os.getenv("APPDATA")
    if appdata:
        path = os.path.join(appdata, "2048_Accesible")
    else:
        path = os.path.join(os.path.expanduser("~"), ".2048_Accesible")
    os.makedirs(path, exist_ok=True)
    return path


APPDATA_DIR = obtener_ruta_appdata()
ARCHIVO_GUARDADO = os.path.join(APPDATA_DIR, "savegame.json")
ARCHIVO_AJUSTES = os.path.join(APPDATA_DIR, "settings.json")
ARCHIVO_LOG = os.path.join(APPDATA_DIR, "game_events.log")


def coord_nombre(r: int, c: int) -> str:
    """Convierte coordenadas (r, c) a notación humana (Columna = Letra, Fila = Número)."""
    col_letra = chr(ord("A") + c)
    fila_num = r + 1
    return f"{col_letra}{fila_num}"


class VentanaJuego(wx.Frame):
    """
    Ventana principal del juego 2048 Accesible.
    Maneja teclado, actualizaciones visuales y retroalimentación para lectores de pantalla.
    """

    # Mapa de teclas de movimiento (Flechas y Numpad con NumLock activo)
    _MOVIMIENTO_MAP = {
        wx.WXK_UP: "ARRIBA",
        wx.WXK_NUMPAD_UP: "ARRIBA",
        wx.WXK_DOWN: "ABAJO",
        wx.WXK_NUMPAD_DOWN: "ABAJO",
        wx.WXK_LEFT: "IZQUIERDA",
        wx.WXK_NUMPAD_LEFT: "IZQUIERDA",
        wx.WXK_RIGHT: "DERECHA",
        wx.WXK_NUMPAD_RIGHT: "DERECHA",
        wx.WXK_NUMPAD8: "ARRIBA",
        wx.WXK_NUMPAD2: "ABAJO",
        wx.WXK_NUMPAD4: "IZQUIERDA",
        wx.WXK_NUMPAD6: "DERECHA",
    }

    def __init__(self, parent: Optional[wx.Window], title: str) -> None:
        super().__init__(parent, title=title, size=(700, 800))

        # Configuración de Logging rotativo
        self._setup_logging()
        self.log_event("START", "Inicializando 2048 Accesible v3.0")

        # Inicialización del audio y motor
        self.sounds = SoundManager()
        self.juego = Logica2048(auto_init=False)

        # Ajustes de accesibilidad (UI)
        self.verbosidad = 1  # 0: Bajo, 1: Normal, 2: Alto
        self.alto_contraste = False
        self.cargar_ajustes()

        # Cargar partida previa o pedir tamaño
        loaded = self.cargar_juego_estado()
        if loaded:
            self.tamano = self.juego.tamano
        else:
            self.tamano = self.pedir_tamano() or 4
            self.juego.tamano = self.tamano
            self.juego.iniciar_juego()

        self.botones: List[List[Celda]] = []
        self.foco_actual = [0, 0]
        self.mensaje_evento_pendiente = ""
        self.historial_anuncios: List[str] = []

        # Control de colisión con bordes (Wall Hits)
        self.wall_hit_count = 0
        self.last_wall_hit_key: Optional[int] = None
        self._anuncio_toggle = False

        self.iniciar_ui()
        self.Centre()
        self.Show()

        # Foco inicial
        self.botones[0][0].SetFocus()
        self.actualizar_tablero(narrativa_inicial=True)

        # Eventos globales de ventana
        self.Bind(wx.EVT_CLOSE, self.al_cerrar_ventana)
        self.Bind(wx.EVT_SIZE, self.al_redimensionar)

    def _setup_logging(self) -> None:
        """Configura el RotatingFileHandler en el directorio seguro de AppData."""
        try:
            self.logger = logging.getLogger("2048_Accesible")
            self.logger.setLevel(logging.INFO)

            if not self.logger.handlers:
                handler = logging.handlers.RotatingFileHandler(
                    ARCHIVO_LOG, mode="a", encoding="utf-8", maxBytes=1048576, backupCount=3
                )
                formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)

            self.logger.info("--- LOG INICIADO ---")
        except Exception as e:
            wx.MessageBox(
                f"No se pudo iniciar el log en {ARCHIVO_LOG}: {e}", "Error de Log", wx.ICON_ERROR
            )

    def log_event(self, category: str, message: str) -> None:
        """Escribe un evento limpio en el log rotativo."""
        if hasattr(self, "logger"):
            self.logger.info(f"[{category}] {str(message).rstrip()}")

    def pedir_tamano(self) -> Optional[int]:
        """Solicita el tamaño del tablero al usuario (4 a 10)."""
        dlg = wx.TextEntryDialog(
            None,
            "Introduce el tamaño del tablero.\n"
            "Valores válidos: 4 a 10.\n"
            "Predeterminado: 4.",
            "Configuración de Tablero",
            "4",
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
                        "Aviso",
                        wx.ICON_WARNING,
                    )
                    val = 4
            except ValueError:
                wx.MessageBox("Entrada no válida. Usando defecto 4.", "Aviso", wx.ICON_WARNING)
                val = 4
        dlg.Destroy()
        return val

    def iniciar_ui(self) -> None:
        """Construye los elementos visuales del tablero interactivo."""
        bg_color = wx.Colour(0, 0, 0) if self.alto_contraste else wx.Colour(*COLOR_FONDO_TABLERO)
        self.SetBackgroundColour(bg_color)

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        panel = wx.Panel(self)
        self.panel = panel
        panel.SetBackgroundColour(bg_color)

        # Exponer panel como ROLE_SYSTEM_TABLE para lectores de pantalla
        panel_acc = AccessibleCustom(
            panel, name=f"Tablero {self.tamano} por {self.tamano}", role=wx.ROLE_SYSTEM_TABLE
        )
        panel.SetAccessible(panel_acc)

        sizer = wx.GridSizer(self.tamano, self.tamano, 10, 10)

        celda_config = {
            "colores_fondo": COLORES_FONDO,
            "color_texto_oscuro": COLOR_TEXTO_OSCURO,
            "color_texto_claro": COLOR_TEXTO_CLARO,
            "high_contrast_colors": COLORES_TEXTO_HC,
        }

        for r in range(self.tamano):
            fila_botones = []
            for c in range(self.tamano):
                celda = Celda(panel, size=80, r=r, c=c, config=celda_config)
                sizer.Add(celda, 1, wx.EXPAND | wx.ALL, 2)
                fila_botones.append(celda)
            self.botones.append(fila_botones)

        panel.SetSizer(sizer)
        main_sizer.Add(panel, 1, wx.EXPAND | wx.ALL, 15)
        self.SetSizer(main_sizer)

        self.Bind(wx.EVT_CHAR_HOOK, self.al_pulsar_tecla)

    def al_redimensionar(self, event: wx.SizeEvent) -> None:
        self.Layout()
        for fila in self.botones:
            for celda in fila:
                celda.Refresh()
        event.Skip()

    def al_cerrar_ventana(self, event: wx.CloseEvent) -> None:
        """Guarda ajustes y partida de manera segura antes de salir."""
        self.guardar_ajustes()
        self.guardar_juego_estado()
        self.log_event("SAVE", "Juego y ajustes guardados al cerrar.")
        event.Skip()

    def al_pulsar_tecla(self, event: wx.KeyEvent) -> None:
        """Manejador y despachador de teclas."""
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

        letra = chr(code).upper() if 32 <= code < 127 else None

        # Atajos de una sola letra
        if letra == "V":
            self.toggle_verbosity()
            return
        if letra == "H":
            sug = self.juego.obtener_sugerencia()
            self.anunciar(f"Sugerencia: {sug}")
            return
        if letra == "I":
            self.anunciar(self.juego.obtener_resumen())
            return
        if letra == "L":
            self.anunciar_historial()
            return
        if letra == "R" and not control:
            self._repetir_ultimo_anuncio()
            return
        if letra == "S":
            info = f"Puntaje: {self.juego.puntuacion}"
            self.SetTitle(f"2048 - {info}")
            self.anunciar(info)
            return
        if letra == "E":
            libres = len(self.juego.celdas_libres())
            info = f"{libres} casillas libres. Máxima: {self.juego.max_ficha}"
            self.SetTitle(f"2048 - {info}")
            self.anunciar(info)
            return
        if letra == "F":
            self._leer_fila_actual()
            return
        if letra == "C":
            self._leer_columna_actual()
            return
        if code == wx.WXK_ESCAPE:
            self.Close()
            return

        # Navegación especial
        if self._manejar_navegacion_especial(code, control):
            return

        # Movimiento o Navegación con flechas
        if code in self._MOVIMIENTO_MAP:
            direccion = self._MOVIMIENTO_MAP[code]
            numpad_directo = code in (
                wx.WXK_NUMPAD8,
                wx.WXK_NUMPAD2,
                wx.WXK_NUMPAD4,
                wx.WXK_NUMPAD6,
            )
            if shift or numpad_directo:
                self._ejecutar_movimiento(direccion)
            else:
                self._navegar_con_flechas(direccion, code)
        else:
            event.Skip()

    def _manejar_ctrl_atajo(self, code: int) -> bool:
        """Maneja atajos con Ctrl. Retorna True si consumió el evento."""
        if code == ord("S"):
            self.guardar_juego_estado()
            self.sounds.play("SAVE")
            self.anunciar("Juego guardado")
            return True

        if code == ord("R"):
            self._reiniciar_juego()
            return True

        if code == ord("Z"):
            if self.juego.deshacer():
                self.sounds.play("UNDO")
                self.mensaje_evento_pendiente = "Deshacer"
                self.actualizar_tablero()
            else:
                self.sounds.play("INVALID")
                self.anunciar("No se puede deshacer")
            return True

        return False

    def _reiniciar_juego(self) -> None:
        """Reinicia el tablero y pide nueva configuración si se desea."""
        self.sounds.play("RESTART")
        old_high_score = self.juego.high_score

        nuevo_tam = self.pedir_tamano()
        if nuevo_tam is not None:
            self.tamano = nuevo_tam
            self.guardar_ajustes()

            if os.path.exists(ARCHIVO_GUARDADO):
                try:
                    os.remove(ARCHIVO_GUARDADO)
                except Exception:
                    pass

            self.juego = Logica2048(tamano=self.tamano, auto_init=False)
            self.juego.high_score = old_high_score
            self.juego.iniciar_juego()

            # Re-init UI
            self.DestroyChildren()
            self.botones = []
            self.historial_anuncios = []
            self.wall_hit_count = 0
            self.last_wall_hit_key = None
            self.iniciar_ui()

            self.foco_actual = [0, 0]
            self.botones[0][0].SetFocus()
            self.actualizar_tablero(narrativa_inicial=True)
            self.anunciar("Juego Reiniciado y Reconfigurado")

    def _manejar_navegacion_especial(self, code: int, control: bool) -> bool:
        r, c = self.foco_actual
        if code == wx.WXK_HOME:
            self.fijar_foco(r, 0) if not control else self.fijar_foco(0, 0)
            return True
        if code == wx.WXK_END:
            self.fijar_foco(r, self.tamano - 1) if not control else self.fijar_foco(
                self.tamano - 1, self.tamano - 1
            )
            return True
        if code == wx.WXK_PAGEUP:
            self.fijar_foco(0, c) if not control else self.fijar_foco(0, self.tamano - 1)
            return True
        if code == wx.WXK_PAGEDOWN:
            self.fijar_foco(self.tamano - 1, c) if not control else self.fijar_foco(
                self.tamano - 1, 0
            )
            return True
        return False

    def _ejecutar_movimiento(self, direccion: str) -> None:
        """Ejecuta un movimiento a través del motor y procesa los resultados en la UI."""
        res: MoveResult = self.juego.mover(direccion)

        if res.cambio:
            self.sounds.play("MOVE")

            dir_es = {
                "ARRIBA": "Arriba",
                "ABAJO": "Abajo",
                "IZQUIERDA": "Izquierda",
                "DERECHA": "Derecha",
            }
            anuncio_dir = dir_es.get(direccion, direccion)
            narrativa_raw = self._construir_narrativa(res)

            narrativa = f"{anuncio_dir}: {narrativa_raw}" if narrativa_raw else anuncio_dir
            self.mensaje_evento_pendiente = narrativa
            self._registrar_historial(narrativa)

            if self.verbosidad == 2:
                libres = len(self.juego.celdas_libres())
                info = f"Puntuación: {self.juego.puntuacion}. {libres} casillas libres."
                self.mensaje_evento_pendiente += f". {info}"

            self.actualizar_tablero()

            if self.juego.juego_terminado():
                self._manejar_game_over()
        else:
            self.sounds.play("INVALID")
            if self.verbosidad == 2:
                self.anunciar("Movimiento no posible")

    def _construir_narrativa(self, result: MoveResult) -> str:
        """Genera la narrativa textual correspondiente al nivel de verbosidad."""
        partes = []

        if self.verbosidad == 0:  # Bajo: Resumen
            counts = {}
            for val, _, _, _, _, _, _ in result.fusiones:
                counts[val] = counts.get(val, 0) + 1
            for val, count in counts.items():
                if count > 1:
                    partes.append(f"{count} fichas {val} fusionadas")
                else:
                    partes.append(f"Ficha {val} fusionada")

        elif self.verbosidad == 1:  # Normal: Oriol
            for val, _, _, _, _, rf, cf in result.fusiones:
                coordf = coord_nombre(rf, cf)
                partes.append(f"{val} en {coordf}")

            if result.ficha_nueva:
                r, c, val = result.ficha_nueva
                coord = coord_nombre(r, c)
                partes.append(f"Apareció {val} en {coord}")

        else:  # Alto: Detallado
            for val, r1, c1, r2, c2, rf, cf in result.fusiones:
                coord1 = coord_nombre(r1, c1)
                coord2 = coord_nombre(r2, c2)
                coordf = coord_nombre(rf, cf)
                partes.append(f"{val} en {coordf} ({coord1} + {coord2})")

            if result.ficha_nueva:
                r, c, val = result.ficha_nueva
                coord = coord_nombre(r, c)
                partes.append(f"Apareció {val} en {coord}")

        return ". ".join(partes)

    def _manejar_game_over(self) -> None:
        """Controla el fin de la partida de forma accesible."""
        self.sounds.play("GAMEOVER")
        self.SetTitle("2048 - Juego Terminado")
        txt_fin = f"Juego Terminado. Puntaje final: {self.juego.puntuacion}"
        self.anunciar(txt_fin)

        foco_r, foco_c = self.foco_actual
        wx.CallAfter(self._mostrar_game_over_dialog, foco_r, foco_c)

        if os.path.exists(ARCHIVO_GUARDADO):
            try:
                os.remove(ARCHIVO_GUARDADO)
            except Exception:
                pass

    def _mostrar_game_over_dialog(self, foco_r: int, foco_c: int) -> None:
        wx.MessageBox(f"Juego Terminado. Puntos: {self.juego.puntuacion}", "Fin")
        if 0 <= foco_r < self.tamano and 0 <= foco_c < self.tamano:
            self.botones[foco_r][foco_c].SetFocus()

    def _navegar_con_flechas(self, direccion: str, key_code: int) -> None:
        dr, dc = 0, 0
        if direccion == "ARRIBA":
            dr = -1
        elif direccion == "ABAJO":
            dr = 1
        elif direccion == "IZQUIERDA":
            dc = -1
        elif direccion == "DERECHA":
            dc = 1
        self.mover_foco(dr, dc, key_code=key_code)

    def fijar_foco(self, r: int, c: int) -> None:
        """Aplica foco a una celda específica y limpia buffers de accesibilidad."""
        if 0 <= r < self.tamano and 0 <= c < self.tamano:
            if [r, c] == self.foco_actual:
                self.anunciar_en_foco()
            else:
                self.log_event("FOCUS_CHANGE", f"Destino: {r},{c}")

                # Limpieza de celda anterior (FIX-DUP-01)
                old_r, old_c = self.foco_actual
                if 0 <= old_r < self.tamano and 0 <= old_c < self.tamano:
                    old_val = self.juego.tablero[old_r][old_c]
                    old_nombre = self._get_nombre_accesible(old_r, old_c, old_val)
                    self.botones[old_r][old_c].actualizar(old_val, old_nombre)

                # Preparar celda nueva limpia (FIX-DUP-02)
                val = self.juego.tablero[r][c]
                nombre = self._get_nombre_accesible(r, c, val)
                self.botones[r][c].actualizar(val, nombre)
                self.botones[r][c].SetFocus()
                self.foco_actual = [r, c]

            self._actualizar_foco_visual()

    def mover_foco(self, dr: int, dc: int, key_code: Optional[int] = None) -> None:
        """Desplaza el foco detectando colisión de bordes accesible."""
        r, c = self.foco_actual
        nr, nc = r + dr, c + dc
        if 0 <= nr < self.tamano and 0 <= nc < self.tamano:
            self.wall_hit_count = 0
            self.last_wall_hit_key = None
            self.fijar_foco(nr, nc)
        else:
            if self.last_wall_hit_key == key_code:
                self.wall_hit_count += 1
            else:
                self.wall_hit_count = 1
                self.last_wall_hit_key = key_code

            if self.wall_hit_count >= 2:
                self.anunciar("Borde")
                self.wall_hit_count = 0
            else:
                self.sounds.play("WALL_SOFT")

    def _actualizar_foco_visual(self) -> None:
        for r in range(self.tamano):
            for c in range(self.tamano):
                btn = self.botones[r][c]
                should_focus = r == self.foco_actual[0] and c == self.foco_actual[1]
                if btn.is_focused != should_focus:
                    btn.is_focused = should_focus
                    btn.Refresh()

    def anunciar_en_foco(self, mensaje: Optional[str] = None) -> None:
        """Fuerza la relectura inmediata de un mensaje usando un espacio especial no divisible (toggle)."""
        r, c = self.foco_actual
        try:
            val = self.juego.tablero[r][c]
            incluir_libres = "casillas libres" not in (mensaje or "").lower()
            base_name = self._get_nombre_accesible(r, c, val, incluir_libres=incluir_libres)

            self._anuncio_toggle = not self._anuncio_toggle
            suffix = "\u00A0" if self._anuncio_toggle else ""

            final_name = base_name + suffix
            if mensaje:
                if self.verbosidad < 2:
                    final_name = f"{mensaje}{suffix}"
                else:
                    final_name = f"{mensaje}. {base_name}{suffix}"

            self.botones[r][c].actualizar(val, final_name, force_notify=True)

            if mensaje:
                # FIX-SR-02 / 03: Limpiar el nombre efímero para evitar lecturas residuales al re-enfocar
                wx.CallLater(300, self._limpiar_nombre_celda, r, c, val)

        except Exception as e:
            logging.error(f"Error en anunciar_en_foco: {e}")

    def _limpiar_nombre_celda(self, r: int, c: int, val: int) -> None:
        try:
            if 0 <= r < self.tamano and 0 <= c < self.tamano:
                val_actual = self.juego.tablero[r][c]
                nombre_limpio = self._get_nombre_accesible(r, c, val_actual)
                self.botones[r][c].actualizar(val_actual, nombre_limpio)
        except Exception as e:
            logging.error(f"Error al limpiar celda {r},{c}: {e}")

    def actualizar_tablero(
        self, narrativa_inicial: bool = False, forzar_silencio_foco: bool = False
    ) -> None:
        """Sincroniza visualmente todas las celdas del tablero."""
        hc_tag = " [HC]" if self.alto_contraste else ""
        self.SetTitle(
            f"2048 - Score: {self.juego.puntuacion} | "
            f"Best: {self.juego.high_score} | Max: {self.juego.max_ficha}{hc_tag}"
        )

        if self.juego.new_high_score:
            self.sounds.play("HIGHSCORE")
            self.juego.new_high_score = False

        # Comprobar hitos de victoria
        hitos_objetivo = [2048, 4096, 8192, 16384, 32768, 65536]
        max_f = self.juego.max_ficha
        for h in hitos_objetivo:
            if max_f >= h and h not in self.juego.hitos_alcanzados:
                self.juego.hitos_alcanzados.append(h)
                self.sounds.play("HIGHSCORE")
                if h == 2048:
                    msg_v = (
                        f"¡Increíble! Has alcanzado la ficha {h}. "
                        "¡Has ganado el juego! Puedes seguir superando tus límites."
                    )
                else:
                    msg_v = (
                        f"¡Increíble! Has alcanzado la ficha {h}. "
                        f"Has superado el hito de {h}. ¡Eres una leyenda!"
                    )

                self.anunciar(msg_v)
                foco_r, foco_c = self.foco_actual
                wx.CallAfter(self._mostrar_hito_dialog, msg_v, foco_r, foco_c)

        # Actualizar celdas
        for r in range(self.tamano):
            for c in range(self.tamano):
                val = self.juego.tablero[r][c]
                es_foco = r == self.foco_actual[0] and c == self.foco_actual[1]

                celda = self.botones[r][c]
                incluir_libres = "casillas libres" not in (
                    self.mensaje_evento_pendiente or ""
                ).lower()
                nombre_accesible = self._get_nombre_accesible(
                    r, c, val, incluir_libres=incluir_libres
                )

                if es_foco and self.mensaje_evento_pendiente:
                    if self.verbosidad < 2:
                        nombre_accesible = self.mensaje_evento_pendiente
                    else:
                        nombre_accesible = f"{self.mensaje_evento_pendiente}. {nombre_accesible}"

                notify_celda = es_foco and not forzar_silencio_foco
                celda.actualizar(
                    val, nombre_accesible, notify=notify_celda, hc_mode=self.alto_contraste
                )

        if self.mensaje_evento_pendiente:
            foco_r, foco_c = self.foco_actual
            foco_val = self.juego.tablero[foco_r][foco_c]
            self.mensaje_evento_pendiente = ""
            wx.CallLater(300, self._limpiar_nombre_celda, foco_r, foco_c, foco_val)

        if narrativa_inicial:
            welcome = (
                f"Bienvenido a 2048 Accesible. Tablero de {self.tamano} por {self.tamano} listo."
            )
            self.anunciar(welcome)
            r, c = self.foco_actual
            self.botones[r][c].SetFocus()

    def _mostrar_hito_dialog(self, msg: str, foco_r: int, foco_c: int) -> None:
        wx.MessageBox(msg, "Hito alcanzado", wx.OK | wx.ICON_INFORMATION)
        if 0 <= foco_r < self.tamano and 0 <= foco_c < self.tamano:
            self.botones[foco_r][foco_c].SetFocus()

    def toggle_contrast(self) -> None:
        """Alterna el modo de alto contraste y actualiza la visualización."""
        self.alto_contraste = not self.alto_contraste
        state = "Activado" if self.alto_contraste else "Desactivado"

        self.sounds.play("TOGGLE_ON" if self.alto_contraste else "TOGGLE_OFF")

        bg = wx.Colour(0, 0, 0) if self.alto_contraste else wx.Colour(*COLOR_FONDO_TABLERO)
        self.SetBackgroundColour(bg)
        for child in self.GetChildren():
            if isinstance(child, wx.Panel):
                child.SetBackgroundColour(bg)

        self.guardar_ajustes()
        self.Refresh()

        msg = f"Alto Contraste {state}"
        self.mensaje_evento_pendiente = msg
        self._registrar_historial(msg)
        self.actualizar_tablero()

    def toggle_verbosity(self) -> None:
        """Cicla entre los tres niveles de verbosidad disponibles."""
        self.verbosidad = (self.verbosidad + 1) % 3
        modes = ["Bajo", "Normal", "Alto"]
        mode = modes[self.verbosidad]

        self.sounds.play("VERBOSITY")
        self.guardar_ajustes()

        msg = f"Verbosidad: {mode}"
        self.mensaje_evento_pendiente = msg
        self._registrar_historial(msg)
        self.actualizar_tablero()

    def _registrar_historial(self, mensaje: str) -> None:
        if not mensaje:
            return
        self.log_event("ANNOUNCE", mensaje)
        if not self.historial_anuncios or self.historial_anuncios[-1] != mensaje:
            self.historial_anuncios.append(mensaje)
            if len(self.historial_anuncios) > 20:
                self.historial_anuncios.pop(0)

    def _leer_fila_actual(self) -> None:
        """Lectura rápida de la fila enfocada (1-indexed)."""
        r = self.foco_actual[0]
        fila_num = r + 1
        valores = []
        for c in range(self.tamano):
            val = self.juego.tablero[r][c]
            valores.append(str(val) if val != 0 else "Libre")
        txt = f"Fila {fila_num}: {', '.join(valores)}"
        self.anunciar(txt)

    def _leer_columna_actual(self) -> None:
        """Lectura rápida de la columna enfocada (A-J)."""
        c = self.foco_actual[1]
        col_letra = chr(ord("A") + c)
        valores = []
        for r in range(self.tamano):
            val = self.juego.tablero[r][c]
            valores.append(str(val) if val != 0 else "Libre")
        txt = f"Columna {col_letra}: {', '.join(valores)}"
        self.anunciar(txt)

    def anunciar_historial(self) -> None:
        """Anuncia rápidamente los últimos 5 eventos grabados."""
        if not self.historial_anuncios:
            self.anunciar("Historial vacío")
            return
        ultimos = self.historial_anuncios[-5:]
        self.anunciar("Historial: " + ". ".join(ultimos))

    def _repetir_ultimo_anuncio(self) -> None:
        if self.historial_anuncios:
            self.anunciar_en_foco(self.historial_anuncios[-1])
        else:
            self.anunciar_en_foco("Sin anuncios previos")

    def mostrar_ayuda(self) -> None:
        """Diálogo modal con los atajos e instrucciones completas."""
        msg = """Atajos de Teclado — 2048 Accesible v3.0

═══ MOVIMIENTO DEL JUEGO ═══
Shift + Flecha (simultáneo): Mover fichas en esa dirección
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
L: Historial de los últimos anuncios
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

    def anunciar(self, mensaje: str) -> None:
        if not mensaje:
            return
        self._registrar_historial(mensaje)
        self.anunciar_en_foco(mensaje)

    def _get_nombre_accesible(self, r: int, c: int, val: int, incluir_libres: bool = True) -> str:
        """Construye un nombre accesible con las coordenadas y valores."""
        coord = coord_nombre(r, c)
        txt_val = str(val) if val != 0 else "Libre"

        if self.verbosidad == 0:  # Bajo: "A1 4" o "A1 Libre"
            return f"{coord} {txt_val}"

        elif self.verbosidad == 2:  # Alto: Detallado
            col = coord[0]
            fila = coord[1:]
            base = f"Columna {col} Fila {fila}: {txt_val}"
            if val == 0 and incluir_libres:
                count = len(self.juego.celdas_libres())
                base += f". {count} casillas libres"
            return base

        else:  # Normal (1)
            return f"{coord}: {txt_val}"

    def guardar_ajustes(self) -> None:
        """Persiste los ajustes de accesibilidad de forma atómica."""
        ajustes = {"verbosidad": self.verbosidad, "alto_contraste": self.alto_contraste}
        temp_ruta = ARCHIVO_AJUSTES + ".tmp"
        try:
            with open(temp_ruta, "w", encoding="utf-8") as f:
                json.dump(ajustes, f, indent=4)
            os.replace(temp_ruta, ARCHIVO_AJUSTES)
        except Exception as e:
            logging.error(f"Error guardando ajustes: {e}")
            if os.path.exists(temp_ruta):
                try:
                    os.remove(temp_ruta)
                except Exception:
                    pass

    def cargar_ajustes(self) -> None:
        """Carga configuraciones de accesibilidad de usuario."""
        if os.path.exists(ARCHIVO_AJUSTES):
            try:
                with open(ARCHIVO_AJUSTES, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.verbosidad = int(data.get("verbosidad", 1))
                    self.alto_contraste = bool(data.get("alto_contraste", False))
            except Exception as e:
                logging.error(f"Error cargando ajustes: {e}")

    def guardar_juego_estado(self) -> None:
        """Guarda la partida de forma atómica."""
        temp_ruta = ARCHIVO_GUARDADO + ".tmp"
        try:
            with open(temp_ruta, "w", encoding="utf-8") as f:
                json.dump(self.juego.to_dict(), f, indent=4)
            os.replace(temp_ruta, ARCHIVO_GUARDADO)
        except Exception as e:
            logging.error(f"Error guardando partida: {e}")
            if os.path.exists(temp_ruta):
                try:
                    os.remove(temp_ruta)
                except Exception:
                    pass

    def cargar_juego_estado(self) -> bool:
        """Carga la partida si existe."""
        if os.path.exists(ARCHIVO_GUARDADO):
            try:
                with open(ARCHIVO_GUARDADO, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if self.juego.from_dict(data):
                        return True
            except Exception as e:
                logging.error(f"Error cargando partida: {e}")
        return False
