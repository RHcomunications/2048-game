import json
import logging
import os
import random
from typing import List, Dict, Any, Tuple
from constants import ARCHIVO_GUARDADO, ARCHIVO_AJUSTES

def coord_nombre(r, c):
    # e.g., A1, B3
    # r=0 -> A
    fila = chr(ord('A') + r)
    col = c + 1
    return f"{fila}{col}"

class Logica2048:
    def __init__(self, tamano: int = 4):
        self.tamano: int = tamano
        self.tablero: List[List[int]] = []
        self.puntuacion: int = 0
        self.max_ficha: int = 0
        self.narrativa: List[str] = []
        self.ultimo_evento: str = "" # 'MOVE', 'MERGE', ""
        self.merge_info: Tuple[float, float, int] = (0.0, 0.0, 0) # (start_pan, end_pan, val)
        self.moved_count: int = 0
        self.merge_count: int = 0 
        self._temp_merge_val: int = 0
        self._temp_merge_dist: float = 0.0
        
        # High Score Handling
        self.high_score = 0
        self.new_high_score = False # Flag for current turn event
        self.new_record = False # Flag for new max tile
        self.ganado = False # Si llegó a 2048
        self.victoria_anunciada = False # Para no repetir el mensaje
        self.ARCHIVO_GUARDADO = ARCHIVO_GUARDADO
        self.ARCHIVO_AJUSTES = ARCHIVO_AJUSTES
        
        # Accessibility Config
        self.verbosidad = 1 # 0: Brief, 1: Normal, 2: Verbose
        self.alto_contraste = False
        
        # Undo History
        self.history: List[Dict[str, Any]] = []
        
        self.cargar_ajustes() # Load user preferences before starting logic
        self.iniciar_juego()

    def iniciar_juego(self):
        self.tablero = [[0] * self.tamano for _ in range(self.tamano)]
        self.puntuacion = 0
        self.max_ficha = 0
        self.history = []
        self.agregar_ficha_random()
        self.agregar_ficha_random()

    def to_dict(self):
        """Convierte el estado esencial de la partida a un diccionario."""
        return {
            'tablero': self.tablero,
            'puntuacion': self.puntuacion,
            'max_ficha': self.max_ficha,
            'high_score': self.high_score,
            'history': self.history,
            'ganado': self.ganado,
            'victoria_anunciada': self.victoria_anunciada
        }

    def guardar_ajustes(self):
        """Guarda configuraciones de usuario de forma independiente."""
        data = {
            'verbosidad': self.verbosidad,
            'alto_contraste': self.alto_contraste
        }
        try:
            with open(self.ARCHIVO_AJUSTES, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            logging.error(f"Error guardando ajustes: {e}")

    def cargar_ajustes(self):
        """Carga configuraciones de usuario desde settings.json."""
        if os.path.exists(self.ARCHIVO_AJUSTES):
            try:
                with open(self.ARCHIVO_AJUSTES, 'r') as f:
                    data = json.load(f)
                    self.verbosidad = int(data.get('verbosidad', 1))
                    self.alto_contraste = bool(data.get('alto_contraste', False))
            except Exception as e:
                logging.error(f"Error cargando ajustes: {e}")

    def from_dict(self, data):
        """Restaura el estado desde un diccionario deserializado de JSON."""
        if not isinstance(data, dict):
            return False
        # Siempre restaurar high_score aunque el tamaño no coincida
        self.high_score = int(data.get('high_score', self.high_score))
        if 'tablero' in data:
             tablero = data['tablero']
             if (isinstance(tablero, list)
                     and len(tablero) == self.tamano
                     and all(isinstance(fila, list) and len(fila) == self.tamano for fila in tablero)):
                  self.tablero = tablero
                  self.puntuacion = int(data.get('puntuacion', 0))
                  self.max_ficha = int(data.get('max_ficha', 0))
                  self.history = data.get('history', [])
                  self.ganado = bool(data.get('ganado', False))
                  self.victoria_anunciada = bool(data.get('victoria_anunciada', False))
                  return True
        return False

    def cargar_juego(self):

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

    def guardar_juego_estado(self):

        data = self.to_dict()
        try:
            with open(self.ARCHIVO_GUARDADO, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            logging.error(f"Error saving game: {e}")

    def actualizar_max_ficha(self):
        """Recalcula la ficha máxima del tablero y marca eventos de récord."""
        m = max(self.tablero[r][c] for r in range(self.tamano) for c in range(self.tamano))
        
        if m > self.max_ficha:
            self.max_ficha = m
            self.new_record = True
            if self.max_ficha >= 2048 and not self.ganado:
                self.ganado = True
        else:
            self.new_record = False

    def agregar_ficha_random(self):
        celdas = self.celdas_libres()
        if celdas:
            r, c = random.choice(celdas)
            val = 4 if random.random() > 0.9 else 2
            self.tablero[r][c] = val
            return (r, c, val)
        return None

    def celdas_libres(self):
        """Retorna lista de tuplas (r, c) de celdas con valor 0."""
        return [(r, c) for r in range(self.tamano) for c in range(self.tamano)
                if self.tablero[r][c] == 0]

    def procesar_linea(self, linea):
        nueva_linea = [val for val in linea if val != 0]
        pts = 0
        fusiones = [] # List of tuples: (value, dest_idx, src_idx_relative_to_compressed_but_we_need_absolute)
        
        # Mapping logic is complex inside loop. 
        # Standard 2048: Leftmost merge first.
        
        i = 0
        while i < len(nueva_linea) - 1:
            if nueva_linea[i] == nueva_linea[i+1]:
                val = nueva_linea[i] * 2
                nueva_linea[i] = val
                nueva_linea.pop(i+1)
                pts += val
                fusiones.append((val, i, i+1)) # Simplified indices
                i += 1
            else:
                i += 1
                
        moves_made = 0
        for i, val in enumerate(linea):
            if val != 0:
                # Find its new index in nueva_linea (rough estimate for intensity)
                # For simplicity, we just count non-zero tiles as "intensity contributors"
                moves_made += 1
        
        # If the line stayed the same, moves_made should be 0 for sound purposes
        if linea == nueva_linea + [0] * (len(linea) - len(nueva_linea)) and not fusiones:
            moves_made = 0

        return nueva_linea + [0] * (len(linea) - len(nueva_linea)), fusiones, pts, moves_made

    def _map_pan(self, idx):
        """Mapea un índice de celda a un valor de paneo estéreo (-0.8 a 0.8)."""
        if self.tamano <= 1:
            return 0.0
        return -0.8 + (1.6 * (idx / (self.tamano - 1)))

    def _update_merge_info(self, start, end, val):
        """Selecciona el merge más relevante para retroalimentación de audio."""
        
        dist = abs(end - start)
        
        if self.merge_info == (0.0, 0.0, 0):
            self.merge_info = (start, end, val)
            self._temp_merge_val = val
        else:
            if val > self._temp_merge_val:
                self.merge_info = (start, end, val)
                self._temp_merge_val = val
            elif val == self._temp_merge_val:
                 # Tie breaker: Distance
                 curr_dist = 0
                 if isinstance(self.merge_info, tuple) and len(self.merge_info) >= 2:
                      curr_dist = abs(self.merge_info[1] - self.merge_info[0])
                     
                 if dist > curr_dist:
                      self.merge_info = (start, end, val)

    def mover(self, direccion):
        # Save state for Undo
        tablero_ant = [f[:] for f in self.tablero]
        score_ant = self.puntuacion
        max_ant = self.max_ficha
        
        nuevo_tablero = [fila[:] for fila in self.tablero]
        cambio = False
        msgs_fusiones = []
        
        self.merge_count = 0
        self.moved_count = 0 
        self.merge_info = (0.0, 0.0, 0)
        self._temp_merge_val = 0
        self._temp_merge_dist = 0.0
        
        # Lógica EXPLÍCITA por dirección (Simplificada para brevity en extracción)
        # Assuming original logic structure...
        # To avoid massive copy-paste error, I will try to preserve the logic 
        # exactly as it was or close to it.
        
        if direccion == 'IZQUIERDA':
            for r in range(self.tamano):
                linea = nuevo_tablero[r]
                procesada, f_list, pts, movs = self.procesar_linea(linea)
                if procesada != linea: cambio = True
                nuevo_tablero[r] = procesada
                self.puntuacion += pts
                self.moved_count += movs
                for val, dest_idx, src_idx in f_list:
                    coord = coord_nombre(r, dest_idx)
                    msgs_fusiones.append(f"{val} se fusionó en {coord}")
                    p_start = self._map_pan(src_idx)
                    p_end = self._map_pan(dest_idx)
                    self._update_merge_info(p_start, p_end, val)
                    self.merge_count += 1
                
        elif direccion == 'DERECHA':
            for r in range(self.tamano):
                linea_rev = list(reversed(nuevo_tablero[r]))
                procesada_rev, f_list, pts, movs = self.procesar_linea(linea_rev)
                procesada = list(reversed(procesada_rev))
                if procesada != nuevo_tablero[r]: cambio = True
                nuevo_tablero[r] = procesada
                self.puntuacion += int(pts)
                self.moved_count += int(movs)
                for val, rev_dest_idx, rev_src_idx in f_list:
                    coord = coord_nombre(r, self.tamano - 1 - rev_dest_idx)
                    msgs_fusiones.append(f"{val} se fusionó en {coord}")
                    p_start = self._map_pan(self.tamano - 1 - rev_src_idx) # Fix logic?
                    p_end = self._map_pan(self.tamano - 1 - rev_dest_idx)
                    self._update_merge_info(p_start, p_end, val)
                    self.merge_count += 1
                
        elif direccion == 'ARRIBA':
            for c in range(self.tamano):
                columna = [nuevo_tablero[r][c] for r in range(self.tamano)]
                procesada, f_list, pts, movs = self.procesar_linea(columna)
                for r in range(self.tamano):
                    if nuevo_tablero[r][c] != procesada[r]: cambio = True
                    nuevo_tablero[r][c] = procesada[r]
                self.puntuacion += pts
                self.moved_count += movs
                for val, dest_row, src_row in f_list:
                    coord = coord_nombre(dest_row, c)
                    msgs_fusiones.append(f"{val} se fusionó en {coord}")
                    pan = self._map_pan(c)
                    self._update_merge_info(pan, pan, val)
                    self.merge_count += 1
                    
        elif direccion == 'ABAJO':
            for c in range(self.tamano):
                columna = [nuevo_tablero[r][c] for r in range(self.tamano)]
                col_rev = list(reversed(columna))
                procesada_rev, f_list, pts, movs = self.procesar_linea(col_rev)
                procesada = list(reversed(procesada_rev))
                for r in range(self.tamano):
                    if nuevo_tablero[r][c] != procesada[r]: cambio = True
                    nuevo_tablero[r][c] = procesada[r]
                self.puntuacion += int(pts)
                self.moved_count += int(movs)
                for val, rev_dest_row, rev_src_row in f_list:
                    coord = coord_nombre(self.tamano - 1 - rev_dest_row, c)
                    msgs_fusiones.append(f"{val} se fusionó en {coord}")
                    pan = self._map_pan(c)
                    self._update_merge_info(pan, pan, val)
                    self.merge_count += 1

        if cambio:
            # History
            if len(self.history) >= 3:
                self.history.pop(0)
            self.history.append({
                "tablero": tablero_ant,
                "puntuacion": score_ant,
                "max_ficha": max_ant
            })
            
            # Update High Score
            if self.puntuacion > self.high_score:
                self.high_score = self.puntuacion
                self.new_high_score = True
                self.new_record = False # Only fanfare for score if it's new
            else:
                self.new_high_score = False

            self.tablero = nuevo_tablero
            # Add new tile and narrative
            new_tile = self.agregar_ficha_random()
            if new_tile and self.verbosidad > 0:
                r, c, val = new_tile
                coord = coord_nombre(r, c)
                msgs_fusiones.append(f"Se añadió {val} a {coord}")
                
            self.actualizar_max_ficha()
            
            # Events
            if self.merge_count > 0:
                self.ultimo_evento = 'MERGE'
                # Consolidate narratives: "3 fusionados en 4", etc.
                # Actually, simpler: count by value
                counts = {}
                for m in msgs_fusiones:
                    if "fusionó" in m:
                        val = m.split(" ")[0]
                        counts[val] = counts.get(val, 0) + 1
                
                final_narrative = []
                for val, count in counts.items():
                    if count > 1:
                        final_narrative.append(f"{count} fichas {val} fusionadas")
                    else:
                        # Find the original coordinate message for the single merge
                        for m in msgs_fusiones:
                            if m.startswith(f"{val} "):
                                final_narrative.append(m)
                                break
                
                # Add spawn info
                for m in msgs_fusiones:
                    if "añadió" in m:
                        final_narrative.append(m)
                
                self.narrativa = final_narrative
            else:
                self.ultimo_evento = 'MOVE'
                self.narrativa = msgs_fusiones # Usually just spawn info or empty
            self.guardar_juego_estado()
            return True
        else:
            self.ultimo_evento = ""
            return False

    def deshacer(self):
        if not self.history:
            return False
            
        estado_previo = self.history.pop()
        tablero: List[List[int]] = estado_previo["tablero"]
        self.tablero = [fila[:] for fila in tablero]
        self.puntuacion = int(estado_previo["puntuacion"])
        self.max_ficha = int(estado_previo["max_ficha"])
        self.new_record = False 
        self.new_high_score = False
        return True

    def obtener_resumen(self):
        """Devuelve un resumen textual del estado del juego."""
        libres = len(self.celdas_libres())
        return f"Puntaje: {self.puntuacion}. Ficha máxima: {self.max_ficha}. Celdas libres: {libres}."

    def obtener_sugerencia(self):
        """Analiza el tablero y sugiere el mejor movimiento próximo."""
        direcciones = ['IZQUIERDA', 'DERECHA', 'ARRIBA', 'ABAJO']
        mejor_dir = "Ninguna"
        mejor_puntaje = -1
        max_libres = -1
        
        # Simulamos cada movimiento
        for d in direcciones:
            temp_tablero = [fila[:] for fila in self.tablero]
            cambio = False
            puntos_mov = 0
            
            # Lógica simplificada de simulación
            if d == 'IZQUIERDA':
                for r in range(self.tamano):
                    linea = temp_tablero[r]
                    procesada, f_list, pts, movs = self.procesar_linea(linea)
                    if procesada != linea: cambio = True
                    temp_tablero[r] = procesada
                    puntos_mov += pts
            elif d == 'DERECHA':
                for r in range(self.tamano):
                    linea = list(reversed(temp_tablero[r]))
                    procesada, f_list, pts, movs = self.procesar_linea(linea)
                    if list(reversed(procesada)) != temp_tablero[r]: cambio = True
                    temp_tablero[r] = list(reversed(procesada))
                    puntos_mov += pts
            elif d == 'ARRIBA':
                for c in range(self.tamano):
                    col = [temp_tablero[r][c] for r in range(self.tamano)]
                    procesada, f_list, pts, movs = self.procesar_linea(col)
                    for r in range(self.tamano):
                        if temp_tablero[r][c] != procesada[r]: cambio = True
                        temp_tablero[r][c] = procesada[r]
                    puntos_mov += pts
            elif d == 'ABAJO':
                for c in range(self.tamano):
                    col = list(reversed([temp_tablero[r][c] for r in range(self.tamano)]))
                    procesada, f_list, pts, movs = self.procesar_linea(col)
                    procesada_final = list(reversed(procesada))
                    for r in range(self.tamano):
                        if temp_tablero[r][c] != procesada_final[r]: cambio = True
                        temp_tablero[r][c] = procesada_final[r]
                    puntos_mov += pts
            
            if cambio:
                libres = sum(1 for row in temp_tablero for cell in row if cell == 0)
                # Prioridad 1: Más puntos por fusión
                # Prioridad 2: Más espacios libres (si empatan puntos)
                if puntos_mov > mejor_puntaje:
                    mejor_puntaje = puntos_mov
                    max_libres = libres
                    mejor_dir = d
                elif puntos_mov == mejor_puntaje and libres > max_libres:
                    max_libres = libres
                    mejor_dir = d
                    
        return mejor_dir

    def juego_terminado(self):
        if self.celdas_libres():
            return False
        
        # Check adjacent
        for r in range(self.tamano):
            for c in range(self.tamano):
                val = self.tablero[r][c]
                if c + 1 < self.tamano and self.tablero[r][c+1] == val:
                    return False
                if r + 1 < self.tamano and self.tablero[r+1][c] == val:
                    return False
        return True
