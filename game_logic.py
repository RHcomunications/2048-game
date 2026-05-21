"""Motor de juego puro para 2048 Accesible (Modelo)."""
import random
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from constants import VALOR_VICTORIA


@dataclass
class MoveResult:
    """Representa el resultado detallado de un movimiento."""
    tablero: List[List[int]]
    cambio: bool
    puntos: int
    fusiones: List[Tuple[int, int, int, int, int, int, int]]  # val, r1, c1, r2, c2, rf, cf
    ficha_nueva: Optional[Tuple[int, int, int]] = None  # r, c, val


class Logica2048:
    """
    Motor puro para las reglas y el estado de 2048.
    Calcula movimientos, puntuación, historial y sugerencias.
    No maneja ajustes de UI ni narrativa de texto directa.
    """

    def __init__(self, tamano: int = 4, auto_init: bool = True) -> None:
        """
        Inicializa la lógica del juego.

        Args:
            tamano: Tamaño del tablero (NxN).
            auto_init: Si True, autogenera el tablero inicial.
        """
        self.tamano: int = tamano
        self.tablero: List[List[int]] = []
        self.puntuacion: int = 0
        self.max_ficha: int = 0

        # Historial de High Score y Victoria
        self.high_score: int = 0
        self.new_high_score: bool = False
        self.ganado: bool = False
        self.hitos_alcanzados: List[int] = []

        # Historial para deshacer (Undo - máximo 3 estados)
        self.history: List[Dict[str, Any]] = []

        if auto_init:
            self.iniciar_juego()

    def iniciar_juego(self) -> None:
        """Reinicia el tablero de juego con dos fichas iniciales."""
        self.tablero = [[0] * self.tamano for _ in range(self.tamano)]
        self.puntuacion = 0
        self.max_ficha = 0
        self.history = []
        self.ganado = False
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
            'hitos_alcanzados': self.hitos_alcanzados
        }

    def from_dict(self, data: Any) -> bool:
        """Restaura el estado de la partida desde un diccionario."""
        if not isinstance(data, dict):
            return False

        self.high_score = int(data.get('high_score', self.high_score))

        if 'tamano' in data:
            self.tamano = int(data['tamano'])

        if 'tablero' in data:
            tablero = data['tablero']
            if (isinstance(tablero, list)
                    and len(tablero) == self.tamano
                    and all(isinstance(fila, list) and len(fila) == self.tamano for fila in tablero)):
                self.tablero = [[int(cell) for cell in fila] for fila in tablero]
                self.puntuacion = int(data.get('puntuacion', 0))
                self.max_ficha = int(data.get('max_ficha', 0))
                self.history = data.get('history', [])
                self.ganado = bool(data.get('ganado', False))
                self.hitos_alcanzados = list(data.get('hitos_alcanzados', []))
                return True
        return False

    def actualizar_max_ficha(self) -> None:
        """Recalcula la ficha de mayor valor en el tablero."""
        m = max(self.tablero[r][c] for r in range(self.tamano) for c in range(self.tamano))
        self.max_ficha = m
        if self.max_ficha >= VALOR_VICTORIA:
            self.ganado = True

    def agregar_ficha_random(self) -> Optional[Tuple[int, int, int]]:
        """Coloca una ficha (2 o 4) en una celda vacía aleatoria."""
        celdas = self.celdas_libres()
        if celdas:
            r, c = random.choice(celdas)
            val = 4 if random.random() > 0.9 else 2
            self.tablero[r][c] = val
            return (r, c, val)
        return None

    def celdas_libres(self) -> List[Tuple[int, int]]:
        """Retorna una lista de coordenadas (r, c) de celdas libres (valor 0)."""
        return [(r, c) for r in range(self.tamano) for c in range(self.tamano)
                if self.tablero[r][c] == 0]

    def procesar_linea(self, linea: List[int]) -> Tuple[List[int], List[Tuple[int, int, int, int]], int]:
        """
        Compacta y fusiona una sola línea (fila o columna).

        Returns:
            Tuple con:
            - La nueva línea procesada.
            - Detalles de fusiones: [(valor_fusionado, index_org1, index_org2, index_final), ...]
            - Total de puntos ganados por fusión.
        """
        fichas: List[Tuple[int, int]] = []
        for i, val in enumerate(linea):
            if val != 0:
                fichas.append((val, i))

        pts = 0
        fusiones: List[Tuple[int, int, int, int]] = []
        compacta: List[int] = []

        i = 0
        while i < len(fichas):
            val1, idx1 = fichas[i]
            if i + 1 < len(fichas) and val1 == fichas[i + 1][0]:
                val_res = val1 * 2
                idx2 = fichas[i + 1][1]
                idx_final = len(compacta)
                compacta.append(val_res)
                pts += val_res
                fusiones.append((val_res, idx1, idx2, idx_final))
                i += 2
            else:
                compacta.append(val1)
                i += 1

        resultado = compacta + [0] * (len(linea) - len(compacta))
        return resultado, fusiones, pts

    def _aplicar_movimiento(self, tablero: List[List[int]], direccion: str
                            ) -> Tuple[List[List[int]], bool, int, List[Tuple[int, int, int, int, int, int, int]]]:
        """
        Aplica un movimiento a una COPIA del tablero.

        Returns:
            Tuple con:
            - Nuevo tablero.
            - Boolean indicando si hubo cambios.
            - Puntos ganados.
            - Lista detallada de fusiones: [(val, r1, c1, r2, c2, rf, cf), ...]
        """
        nuevo = [list(fila) for fila in tablero]
        cambio = False
        puntos_total = 0
        fusiones_det: List[Tuple[int, int, int, int, int, int, int]] = []

        if direccion == 'IZQUIERDA':
            for r in range(self.tamano):
                linea = nuevo[r]
                procesada, f_list, pts = self.procesar_linea(linea)
                if procesada != linea:
                    cambio = True
                nuevo[r] = procesada
                puntos_total += pts
                for val, idx1, idx2, idx_f in f_list:
                    fusiones_det.append((val, r, idx1, r, idx2, r, idx_f))

        elif direccion == 'DERECHA':
            for r in range(self.tamano):
                linea_rev = list(reversed(nuevo[r]))
                procesada_rev, f_list, pts = self.procesar_linea(linea_rev)
                procesada = list(reversed(procesada_rev))
                if procesada != nuevo[r]:
                    cambio = True
                nuevo[r] = procesada
                puntos_total += pts
                for val, idx1, idx2, idx_f in f_list:
                    c1 = self.tamano - 1 - idx1
                    c2 = self.tamano - 1 - idx2
                    cf = self.tamano - 1 - idx_f
                    fusiones_det.append((val, r, c1, r, c2, r, cf))

        elif direccion == 'ARRIBA':
            for c in range(self.tamano):
                columna = [nuevo[r][c] for r in range(self.tamano)]
                procesada, f_list, pts = self.procesar_linea(columna)
                for r in range(self.tamano):
                    if nuevo[r][c] != procesada[r]:
                        cambio = True
                    nuevo[r][c] = procesada[r]
                puntos_total += pts
                for val, idx1, idx2, idx_f in f_list:
                    fusiones_det.append((val, idx1, c, idx2, c, idx_f, c))

        elif direccion == 'ABAJO':
            for c in range(self.tamano):
                columna = [nuevo[r][c] for r in range(self.tamano)]
                col_rev = list(reversed(columna))
                procesada_rev, f_list, pts = self.procesar_linea(col_rev)
                procesada = list(reversed(procesada_rev))
                for r in range(self.tamano):
                    if nuevo[r][c] != procesada[r]:
                        cambio = True
                    nuevo[r][c] = procesada[r]
                puntos_total += pts
                for val, idx1, idx2, idx_f in f_list:
                    r1 = self.tamano - 1 - idx1
                    r2 = self.tamano - 1 - idx2
                    rf = self.tamano - 1 - idx_f
                    fusiones_det.append((val, r1, c, r2, c, rf, c))

        return nuevo, cambio, puntos_total, fusiones_det

    def mover(self, direccion: str) -> MoveResult:
        """
        Ejecuta un movimiento en la dirección dada.
        Actualiza el estado interno del juego si es válido.
        """
        nuevo_tablero, cambio, pts, fusiones = self._aplicar_movimiento(self.tablero, direccion)

        if not cambio:
            return MoveResult(tablero=self.tablero, cambio=False, puntos=0, fusiones=[])

        # Guardar estado para Undo (máximo 3)
        if len(self.history) >= 3:
            self.history.pop(0)
        self.history.append({
            "tablero": [list(fila) for fila in self.tablero],
            "puntuacion": self.puntuacion,
            "max_ficha": self.max_ficha,
            "ganado": self.ganado,
            "hitos_alcanzados": list(self.hitos_alcanzados)
        })

        # Aplicar el cambio
        self.tablero = nuevo_tablero
        self.puntuacion += pts

        # Agregar ficha aleatoria nueva
        new_tile = self.agregar_ficha_random()

        # Actualizar record
        if self.puntuacion > self.high_score:
            self.high_score = self.puntuacion
            self.new_high_score = True
        else:
            self.new_high_score = False

        self.actualizar_max_ficha()

        return MoveResult(
            tablero=self.tablero,
            cambio=True,
            puntos=pts,
            fusiones=fusiones,
            ficha_nueva=new_tile
        )

    def deshacer(self) -> bool:
        """Deshace el último movimiento, restaurando el estado completo."""
        if not self.history:
            return False

        estado_previo = self.history.pop()
        self.tablero = [list(fila) for fila in estado_previo["tablero"]]
        self.puntuacion = int(estado_previo["puntuacion"])
        self.max_ficha = int(estado_previo["max_ficha"])
        self.ganado = bool(estado_previo["ganado"])
        self.hitos_alcanzados = list(estado_previo["hitos_alcanzados"])
        self.new_high_score = False
        return True

    def obtener_resumen(self) -> str:
        """Devuelve un resumen del estado actual."""
        libres = len(self.celdas_libres())
        return f"Puntaje: {self.puntuacion}. Ficha máxima: {self.max_ficha}. Celdas libres: {libres}."

    def obtener_sugerencia(self) -> str:
        """Sugerencia heurística basada en espacios libres, puntaje y esquinas."""
        direcciones = ['IZQUIERDA', 'DERECHA', 'ARRIBA', 'ABAJO']
        mejor_dir = "Ninguna"
        mejor_valor_heuristico = -1.0

        for d in direcciones:
            temp_tablero, cambio_sim, puntos_mov, _ = self._aplicar_movimiento(self.tablero, d)

            if cambio_sim:
                libres = sum(1 for row in temp_tablero for cell in row if cell == 0)
                valor = float(puntos_mov) + (float(libres) * 10.0)

                # Buscar la posición de la ficha máxima
                max_t = 0
                max_pos = (0, 0)
                for r in range(self.tamano):
                    for c in range(self.tamano):
                        if temp_tablero[r][c] > max_t:
                            max_t = temp_tablero[r][c]
                            max_pos = (r, c)

                # Premiar si la ficha máxima queda en una de las cuatro esquinas
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
