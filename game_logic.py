import json
import logging
import os
import random
from typing import List, Dict, Any, Tuple, Optional
from constants import ARCHIVO_GUARDADO, ARCHIVO_AJUSTES, VALOR_VICTORIA

def coord_nombre(r: int, c: int) -> str:
    """Convierte coordenadas (r, c) a notación humana, e.g., A1, B3."""
    fila = chr(ord('A') + r)
    col = c + 1
    return f"{fila}{col}"


class Logica2048:
    """
    Core engine for the 2048 game logic.
    Handles board state, move calculations, score, and undo history.
    """
    def __init__(self, tamano: int = 4, auto_init: bool = True):
        """Inicializa la lógica del juego.

        Args:
            tamano: Tamaño del tablero (NxN).
            auto_init: Si True, genera tablero inicial. Pasar False cuando
                       se va a cargar estado desde disco inmediatamente después.
        """
        self.tamano: int = tamano
        self.tablero: List[List[int]] = []
        self.puntuacion: int = 0
        self.max_ficha: int = 0
        self.narrativa: List[str] = []

        # High Score
        self.high_score: int = 0
        self.new_high_score: bool = False

        # Victoria
        self.ganado: bool = False
        self.victoria_anunciada: bool = False
        self.hitos_alcanzados: List[int] = []

        self.ARCHIVO_GUARDADO = ARCHIVO_GUARDADO
        self.ARCHIVO_AJUSTES = ARCHIVO_AJUSTES

        # Accessibility Config
        self.verbosidad: int = 1  # 0: Bajo, 1: Normal, 2: Alto
        self.alto_contraste: bool = False

        # Undo History (máximo 3 estados)
        self.history: List[Dict[str, Any]] = []

        self.cargar_ajustes()
        # H2-02: Solo iniciar tablero si no se va a cargar estado después
        if auto_init:
            self.iniciar_juego()

    def iniciar_juego(self) -> None:
        """Reinicia el tablero con dos fichas aleatorias."""
        self.tablero = [[0] * self.tamano for _ in range(self.tamano)]
        self.puntuacion = 0
        self.max_ficha = 0
        self.history = []
        # P4-01: Reset estado de victoria al reiniciar
        self.ganado = False
        self.victoria_anunciada = False
        self.hitos_alcanzados = []
        self.agregar_ficha_random()
        self.agregar_ficha_random()

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el estado esencial de la partida a un diccionario."""
        return {
            'tamano': self.tamano,
            'tablero': self.tablero,
            'puntuacion': self.puntuacion,
            'max_ficha': self.max_ficha,
            'high_score': self.high_score,
            'history': self.history,
            'ganado': self.ganado,
            'victoria_anunciada': self.victoria_anunciada,
            'hitos_alcanzados': self.hitos_alcanzados
        }

    def guardar_ajustes(self) -> None:
        """Persiste los ajustes de accesibilidad de forma atómica."""
        ajustes: Dict[str, Any] = {
            'verbosidad': self.verbosidad,
            'alto_contraste': self.alto_contraste
        }
        self.guardar_json_atomico(self.ARCHIVO_AJUSTES, ajustes)

    def cargar_ajustes(self) -> None:
        """Carga configuraciones de usuario desde settings.json."""
        if os.path.exists(self.ARCHIVO_AJUSTES):
            try:
                with open(self.ARCHIVO_AJUSTES, 'r') as f:
                    data = json.load(f)
                    self.verbosidad = int(data.get('verbosidad', 1))
                    self.alto_contraste = bool(data.get('alto_contraste', False))
            except Exception as e:
                logging.error(f"Error cargando ajustes: {e}")

    def from_dict(self, data: Any) -> bool:
        """Restaura el estado desde un diccionario deserializado de JSON."""
        if not isinstance(data, dict):
            return False
        # Siempre restaurar high_score aunque el tamaño no coincida
        self.high_score = int(data.get('high_score', self.high_score))
        # E3-03: Restaurar tamaño si está disponible en el save
        if 'tamano' in data:
            self.tamano = int(data['tamano'])
        if 'tablero' in data:
            tablero = data['tablero']
            if (isinstance(tablero, list)
                    and len(tablero) == self.tamano
                    and all(isinstance(fila, list) and len(fila) == self.tamano for fila in tablero)):
                # H-03: Sanear cada celda a int para prevenir corrupción
                self.tablero = [[int(cell) for cell in fila] for fila in tablero]
                self.puntuacion = int(data.get('puntuacion', 0))
                self.max_ficha = int(data.get('max_ficha', 0))
                self.history = data.get('history', [])
                self.ganado = bool(data.get('ganado', False))
                self.victoria_anunciada = bool(data.get('victoria_anunciada', False))
                self.hitos_alcanzados = list(data.get('hitos_alcanzados', []))
                return True
        return False

    def cargar_juego(self) -> bool:
        """Carga partida guardada desde savegame.json."""
        if os.path.exists(self.ARCHIVO_GUARDADO):
            try:
                with open(self.ARCHIVO_GUARDADO, 'r') as f:
                    data = json.load(f)
                    if self.from_dict(data):
                        logging.info("Game loaded successfully.")
                        return True
            except Exception as e:
                logging.error(f"Error loading game: {e}")
        return False

    def guardar_json_atomico(self, ruta: str, datos: Dict[str, Any]) -> None:
        """Guarda un diccionario en JSON de forma atómica usando archivo temporal."""
        temp_ruta: str = ruta + ".tmp"
        try:
            with open(temp_ruta, 'w', encoding='utf-8') as f:
                json.dump(datos, f, indent=4)
            # H-04: os.replace() es atómico y funciona siempre
            os.replace(temp_ruta, ruta)
        except Exception as e:
            logging.error(f"Error en guardado atómico de {ruta}: {e}")
            if os.path.exists(temp_ruta):
                try:
                    os.remove(temp_ruta)
                except Exception:
                    pass

    def guardar_juego_estado(self) -> None:
        """Persiste el estado actual de la partida de forma atómica."""
        self.guardar_json_atomico(self.ARCHIVO_GUARDADO, self.to_dict())

    def actualizar_max_ficha(self) -> None:
        """Recalcula la ficha máxima del tablero."""
        m = max(self.tablero[r][c] for r in range(self.tamano) for c in range(self.tamano))
        self.max_ficha = m
        if self.max_ficha >= VALOR_VICTORIA and not self.ganado:
            self.ganado = True

    def agregar_ficha_random(self) -> Optional[Tuple[int, int, int]]:
        """Coloca una ficha (2 o 4) en una celda libre aleatoria."""
        celdas = self.celdas_libres()
        if celdas:
            r, c = random.choice(celdas)
            val = 4 if random.random() > 0.9 else 2
            self.tablero[r][c] = val
            return (r, c, val)
        return None

    def celdas_libres(self) -> List[Tuple[int, int]]:
        """Retorna lista de tuplas (r, c) de celdas con valor 0."""
        return [(r, c) for r in range(self.tamano) for c in range(self.tamano)
                if self.tablero[r][c] == 0]

    def procesar_linea(self, linea: List[int]) -> Tuple[List[int], List[Tuple[int, int, int]], int, int]:
        """
        Procesa una fila o columna para movimiento y fusión.

        Returns:
            Tupla con:
            - La nueva línea (list de ints)
            - Lista de detalles de fusión (valor, índice_destino, índice_origen)
            - Total de puntos ganados
            - Cantidad de fichas que cambiaron de posición
        """
        # Compactar: quitar ceros
        compacta: List[int] = [val for val in linea if val != 0]
        pts: int = 0
        fusiones: List[Tuple[int, int, int]] = []

        # Fusionar pares adyacentes (izquierda primero)
        i = 0
        while i < len(compacta) - 1:
            if compacta[i] == compacta[i + 1]:
                val: int = compacta[i] * 2
                compacta[i] = val
                compacta.pop(i + 1)
                pts += val
                fusiones.append((val, i, i + 1))
                i += 1
            else:
                i += 1

        # Rellenar con ceros
        resultado = compacta + [0] * (len(linea) - len(compacta))

        # H-05: Contar fichas que realmente cambiaron de posición
        fichas_movidas: int = 0
        for idx in range(len(linea)):
            if linea[idx] != resultado[idx]:
                fichas_movidas += 1

        return resultado, fusiones, pts, fichas_movidas

    # ─── E-01: Método unificado para aplicar movimiento a un tablero ───

    def _aplicar_movimiento(self, tablero: List[List[int]], direccion: str
                            ) -> Tuple[List[List[int]], bool, int, List[Tuple[int, int, int, int, int]], int, int]:
        """
        Aplica un movimiento a una COPIA del tablero.

        Returns:
            (nuevo_tablero, cambio, puntos, fusiones_detalladas, moved_count, merge_count)
            fusiones_detalladas: [(val, fila_real, col_real, src_pan_idx, dest_pan_idx), ...]
        """
        nuevo = [fila[:] for fila in tablero]
        cambio = False
        puntos_total = 0
        fusiones_det: List[Tuple[int, int, int, int, int]] = []
        total_moved = 0
        total_merges = 0

        if direccion == 'IZQUIERDA':
            for r in range(self.tamano):
                linea = nuevo[r]
                procesada, f_list, pts, movs = self.procesar_linea(linea)
                if procesada != linea:
                    cambio = True
                nuevo[r] = procesada
                puntos_total += pts
                total_moved += movs
                for val, dest_idx, src_idx in f_list:
                    fusiones_det.append((val, r, dest_idx, src_idx, dest_idx))
                    total_merges += 1

        elif direccion == 'DERECHA':
            for r in range(self.tamano):
                linea_rev = list(reversed(nuevo[r]))
                procesada_rev, f_list, pts, movs = self.procesar_linea(linea_rev)
                procesada = list(reversed(procesada_rev))
                if procesada != nuevo[r]:
                    cambio = True
                nuevo[r] = procesada
                puntos_total += pts
                total_moved += movs
                for val, rev_dest_idx, rev_src_idx in f_list:
                    real_col = self.tamano - 1 - rev_dest_idx
                    fusiones_det.append((val, r, real_col,
                                        self.tamano - 1 - rev_src_idx,
                                        real_col))
                    total_merges += 1

        elif direccion == 'ARRIBA':
            for c in range(self.tamano):
                columna = [nuevo[r][c] for r in range(self.tamano)]
                procesada, f_list, pts, movs = self.procesar_linea(columna)
                for r in range(self.tamano):
                    if nuevo[r][c] != procesada[r]:
                        cambio = True
                    nuevo[r][c] = procesada[r]
                puntos_total += pts
                total_moved += movs
                for val, dest_row, src_row in f_list:
                    fusiones_det.append((val, dest_row, c, c, c))
                    total_merges += 1

        elif direccion == 'ABAJO':
            for c in range(self.tamano):
                columna = [nuevo[r][c] for r in range(self.tamano)]
                col_rev = list(reversed(columna))
                procesada_rev, f_list, pts, movs = self.procesar_linea(col_rev)
                procesada = list(reversed(procesada_rev))
                for r in range(self.tamano):
                    if nuevo[r][c] != procesada[r]:
                        cambio = True
                    nuevo[r][c] = procesada[r]
                puntos_total += pts
                total_moved += movs
                for val, rev_dest_row, rev_src_row in f_list:
                    real_row = self.tamano - 1 - rev_dest_row
                    fusiones_det.append((val, real_row, c, c, c))
                    total_merges += 1

        return nuevo, cambio, puntos_total, fusiones_det, total_moved, total_merges

    def mover(self, direccion: str) -> bool:
        """Ejecuta un movimiento en la dirección dada. Retorna True si hubo cambio."""
        # Guardar estado para Undo
        tablero_ant = [f[:] for f in self.tablero]
        score_ant = self.puntuacion
        max_ant = self.max_ficha
        ganado_ant = self.ganado
        victoria_anunciada_ant = self.victoria_anunciada
        hitos_ant = self.hitos_alcanzados[:]

        nuevo_tablero, cambio, pts, fusiones_det, moved, merges = \
            self._aplicar_movimiento(self.tablero, direccion)

        if cambio:
            self.puntuacion += pts

            # Construir narrativa
            msgs_fusiones: List[str] = []
            for val, row, col, src_pan_idx, dest_pan_idx in fusiones_det:
                coord = coord_nombre(row, col)
                msgs_fusiones.append(f"{val} se fusionó en {coord}")

            # History (máximo 3 estados)
            if len(self.history) >= 3:
                self.history.pop(0)
            self.history.append({
                "tablero": tablero_ant,
                "puntuacion": score_ant,
                "max_ficha": max_ant,
                # H-01: Guardar estado de victoria para undo completo
                "ganado": ganado_ant,
                "victoria_anunciada": victoria_anunciada_ant,
                "hitos_alcanzados": hitos_ant
            })

            # Actualizar High Score
            if self.puntuacion > self.high_score:
                self.high_score = self.puntuacion
                self.new_high_score = True
            else:
                self.new_high_score = False

            self.tablero = nuevo_tablero

            # Agregar ficha nueva
            new_tile = self.agregar_ficha_random()
            if new_tile and self.verbosidad > 0:
                r, c, val = new_tile
                coord = coord_nombre(r, c)
                msgs_fusiones.append(f"Se añadió {val} a {coord}")

            self.actualizar_max_ficha()

            # Construir narrativa final
            if merges > 0:
                counts: Dict[str, int] = {}
                for m in msgs_fusiones:
                    if "fusionó" in m:
                        val_str = m.split(" ")[0]
                        counts[val_str] = counts.get(val_str, 0) + 1

                final_narrative: List[str] = []
                for val_str, count in counts.items():
                    if count > 1:
                        final_narrative.append(f"{count} fichas {val_str} fusionadas")
                    else:
                        for m in msgs_fusiones:
                            if m.startswith(f"{val_str} "):
                                final_narrative.append(m)
                                break

                for m in msgs_fusiones:
                    if "añadió" in m:
                        final_narrative.append(m)

                self.narrativa = final_narrative
            else:
                self.narrativa = msgs_fusiones

            self.guardar_juego_estado()
            return True
        else:
            return False

    def deshacer(self) -> bool:
        """Deshace el último movimiento, restaurando TODO el estado."""
        if not self.history:
            return False

        estado_previo = self.history.pop()
        tablero: List[List[int]] = estado_previo["tablero"]
        self.tablero = [fila[:] for fila in tablero]
        self.puntuacion = int(estado_previo["puntuacion"])
        self.max_ficha = int(estado_previo["max_ficha"])
        # H-01: Restaurar estado de victoria completo
        self.ganado = bool(estado_previo.get("ganado", self.max_ficha >= VALOR_VICTORIA))
        self.victoria_anunciada = bool(estado_previo.get("victoria_anunciada", False))
        self.hitos_alcanzados = list(estado_previo.get("hitos_alcanzados",
                                    [h for h in self.hitos_alcanzados if h <= self.max_ficha]))
        # L4-05: new_high_score se resetea en game_ui.actualizar_tablero()
        return True

    def obtener_resumen(self) -> str:
        """Devuelve un resumen textual del estado del juego."""
        libres = len(self.celdas_libres())
        return f"Puntaje: {self.puntuacion}. Ficha máxima: {self.max_ficha}. Celdas libres: {libres}."

    def obtener_sugerencia(self) -> str:
        """Sugerencia avanzada basada en puntos, espacios y estrategia de esquinas."""
        direcciones = ['IZQUIERDA', 'DERECHA', 'ARRIBA', 'ABAJO']
        mejor_dir = "Ninguna"
        mejor_valor_heuristico = -1.0

        for d in direcciones:
            # E-01 / H-06: Usar el método unificado con copia segura
            temp_tablero, cambio_sim, puntos_mov, _, _, _ = \
                self._aplicar_movimiento(self.tablero, d)

            if cambio_sim:
                libres = sum(1 for row in temp_tablero for cell in row if cell == 0)
                valor = float(puntos_mov) + (float(libres) * 10.0)

                # Estrategia de esquina
                max_t = 0
                max_pos = (0, 0)
                for r in range(self.tamano):
                    for c in range(self.tamano):
                        if temp_tablero[r][c] > max_t:
                            max_t = temp_tablero[r][c]
                            max_pos = (r, c)

                esquinas = [(0, 0), (0, self.tamano - 1),
                            (self.tamano - 1, 0), (self.tamano - 1, self.tamano - 1)]
                if max_pos in esquinas:
                    valor += max_t * 2.0

                if valor > mejor_valor_heuristico:
                    mejor_valor_heuristico = valor
                    mejor_dir = d

        return mejor_dir

    def juego_terminado(self) -> bool:
        """Retorna True si no hay movimientos posibles."""
        if self.celdas_libres():
            return False

        for r in range(self.tamano):
            for c in range(self.tamano):
                val = self.tablero[r][c]
                if c + 1 < self.tamano and self.tablero[r][c + 1] == val:
                    return False
                if r + 1 < self.tamano and self.tablero[r + 1][c] == val:
                    return False
        return True
