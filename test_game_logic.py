"""Tests exhaustivos para game_logic.py — Cubre E-06 (edge cases extensivos)."""
import unittest
import json
import os
import tempfile
from game_logic import Logica2048, coord_nombre


class TestCoordNombre(unittest.TestCase):
    """Tests para la función utilitaria coord_nombre."""

    def test_esquina_superior_izquierda(self):
        self.assertEqual(coord_nombre(0, 0), "A1")

    def test_esquina_inferior_derecha_4x4(self):
        self.assertEqual(coord_nombre(3, 3), "D4")

    def test_tablero_grande(self):
        self.assertEqual(coord_nombre(9, 9), "J10")


class TestInicializacion(unittest.TestCase):
    """Tests de inicialización del juego."""

    def test_tamano_default(self):
        game = Logica2048(tamano=4)
        self.assertEqual(game.tamano, 4)

    def test_dos_fichas_iniciales(self):
        game = Logica2048(tamano=4)
        count = sum(1 for row in game.tablero for cell in row if cell != 0)
        self.assertEqual(count, 2)

    def test_puntuacion_inicial_cero(self):
        game = Logica2048(tamano=4)
        self.assertEqual(game.puntuacion, 0)

    def test_tamano_grande(self):
        game = Logica2048(tamano=8)
        self.assertEqual(len(game.tablero), 8)
        self.assertEqual(len(game.tablero[0]), 8)

    def test_estado_victoria_inicial(self):
        game = Logica2048(tamano=4)
        self.assertFalse(game.ganado)
        self.assertFalse(game.victoria_anunciada)
        self.assertEqual(game.hitos_alcanzados, [])


class TestProcesarLinea(unittest.TestCase):
    """Tests para procesar_linea — fusión y movimiento."""

    def setUp(self):
        self.game = Logica2048(tamano=4)

    def test_fusion_simple(self):
        merged, f_list, score, moved = self.game.procesar_linea([2, 2, 0, 0])
        self.assertEqual(merged, [4, 0, 0, 0])
        self.assertEqual(score, 4)

    def test_fusion_multiple(self):
        merged, f_list, score, moved = self.game.procesar_linea([2, 2, 4, 4])
        self.assertEqual(merged, [4, 8, 0, 0])
        self.assertEqual(score, 12)

    def test_solo_movimiento(self):
        merged, f_list, score, moved = self.game.procesar_linea([0, 2, 0, 4])
        self.assertEqual(merged, [2, 4, 0, 0])
        self.assertEqual(score, 0)
        self.assertGreater(moved, 0)

    def test_linea_sin_cambios(self):
        merged, f_list, score, moved = self.game.procesar_linea([2, 4, 8, 16])
        self.assertEqual(merged, [2, 4, 8, 16])
        self.assertEqual(score, 0)
        self.assertEqual(moved, 0)

    def test_triple_no_doble_fusion(self):
        """[2, 2, 2, 0] debe fusionar los dos primeros, no los tres."""
        merged, f_list, score, moved = self.game.procesar_linea([2, 2, 2, 0])
        self.assertEqual(merged, [4, 2, 0, 0])
        self.assertEqual(score, 4)

    def test_cuatro_iguales(self):
        """[4, 4, 4, 4] → [8, 8, 0, 0] — dos fusiones separadas."""
        merged, f_list, score, moved = self.game.procesar_linea([4, 4, 4, 4])
        self.assertEqual(merged, [8, 8, 0, 0])
        self.assertEqual(score, 16)

    def test_linea_vacia(self):
        merged, f_list, score, moved = self.game.procesar_linea([0, 0, 0, 0])
        self.assertEqual(merged, [0, 0, 0, 0])
        self.assertEqual(score, 0)
        self.assertEqual(moved, 0)

    def test_linea_llena_sin_fusion(self):
        merged, f_list, score, moved = self.game.procesar_linea([2, 4, 2, 4])
        self.assertEqual(merged, [2, 4, 2, 4])
        self.assertEqual(score, 0)
        self.assertEqual(moved, 0)

    def test_fichas_movidas_correcto(self):
        """H-05: Verificar que moved_count refleja fichas realmente desplazadas."""
        merged, f_list, score, moved = self.game.procesar_linea([0, 0, 0, 2])
        self.assertEqual(merged, [2, 0, 0, 0])
        self.assertGreater(moved, 0)


class TestMovimiento(unittest.TestCase):
    """Tests para el método mover() con tableros controlados."""

    def setUp(self):
        self.game = Logica2048(tamano=4)

    def test_mover_izquierda(self):
        self.game.tablero = [
            [2, 0, 0, 2],
            [0, 0, 0, 0],
            [2, 0, 0, 0],
            [0, 0, 0, 0]
        ]
        self.game.mover('IZQUIERDA')
        self.assertEqual(self.game.tablero[0][0], 4)
        self.assertEqual(self.game.tablero[2][0], 2)

    def test_mover_arriba(self):
        self.game.tablero = [
            [2, 0, 0, 0],
            [2, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0]
        ]
        self.game.mover('ARRIBA')
        self.assertEqual(self.game.tablero[0][0], 4)

    def test_mover_derecha(self):
        self.game.tablero = [
            [2, 2, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0]
        ]
        self.game.mover('DERECHA')
        self.assertEqual(self.game.tablero[0][3], 4)

    def test_mover_abajo(self):
        self.game.tablero = [
            [2, 0, 0, 0],
            [2, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0]
        ]
        self.game.mover('ABAJO')
        self.assertEqual(self.game.tablero[3][0], 4)

    def test_movimiento_invalido_retorna_false(self):
        self.game.tablero = [
            [2, 4, 8, 16],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0]
        ]
        result = self.game.mover('IZQUIERDA')
        self.assertFalse(result)

    def test_mover_agrega_ficha(self):
        self.game.tablero = [
            [2, 0, 0, 2],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0]
        ]
        self.game.mover('IZQUIERDA')
        # Debe haber al menos 1 ficha nueva (total mínimo 2)
        count = sum(1 for row in self.game.tablero for cell in row if cell != 0)
        self.assertGreaterEqual(count, 2)


class TestDeshacer(unittest.TestCase):
    """Tests para undo — incluyendo H-01 (restaurar estado de victoria)."""

    def setUp(self):
        self.game = Logica2048(tamano=4)

    def test_deshacer_basico(self):
        orig = [row[:] for row in self.game.tablero]
        self.game.mover('DERECHA')
        self.game.deshacer()
        self.assertEqual(self.game.tablero, orig)

    def test_deshacer_sin_historial(self):
        self.assertFalse(self.game.deshacer())

    def test_deshacer_restaura_puntuacion(self):
        self.game.tablero = [
            [2, 2, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0]
        ]
        score_antes = self.game.puntuacion
        self.game.mover('IZQUIERDA')
        self.game.deshacer()
        self.assertEqual(self.game.puntuacion, score_antes)

    def test_deshacer_restaura_victoria(self):
        """H-01: Undo debe restaurar estado ganado/hitos."""
        self.game.tablero = [
            [1024, 1024, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0]
        ]
        self.game.ganado = False
        self.game.hitos_alcanzados = []
        self.game.mover('IZQUIERDA')
        # Después del merge: 2048 presente, ganado = True
        self.assertTrue(self.game.ganado)
        # Deshacer
        self.game.deshacer()
        self.assertFalse(self.game.ganado)

    def test_limite_historial(self):
        """E-10: Solo 3 undos disponibles."""
        self.game.tablero = [
            [2, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0]
        ]
        for _ in range(5):
            self.game.tablero[0][1] = 0  # Forzar espacio libre
            self.game.mover('DERECHA')
        self.assertLessEqual(len(self.game.history), 3)

    def test_deshacer_en_cadena(self):
        """3 deshacimientos consecutivos."""
        # Establecer tablero base determinista
        self.game.tablero = [
            [0, 0, 0, 2],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0]
        ]
        self.game.history = []
        # Realizar 3 movimientos válidos
        for _ in range(3):
            # Forzar que siempre haya una ficha que se pueda mover
            self.game.tablero[0][0] = 2
            self.game.tablero[0][3] = 0
            self.game.mover('DERECHA')
        # Deshacer 3 veces
        for i in range(3):
            self.assertTrue(self.game.deshacer())
        # 4ta vez debe fallar
        self.assertFalse(self.game.deshacer())


class TestSerializacion(unittest.TestCase):
    """Tests de guardado/carga — incluyendo H-03 (sanitización)."""

    def setUp(self):
        self.game = Logica2048(tamano=4)

    def test_to_dict_y_from_dict(self):
        self.game.puntuacion = 100
        self.game.tablero[0][0] = 64
        data = self.game.to_dict()

        new_game = Logica2048(tamano=4)
        result = new_game.from_dict(data)

        self.assertTrue(result)
        self.assertEqual(new_game.puntuacion, 100)
        self.assertEqual(new_game.tablero[0][0], 64)

    def test_from_dict_invalido(self):
        self.assertFalse(self.game.from_dict("not a dict"))
        self.assertFalse(self.game.from_dict(42))
        self.assertFalse(self.game.from_dict(None))

    def test_from_dict_tamano_incorrecto(self):
        data = {'tablero': [[0, 0], [0, 0]], 'puntuacion': 50}
        result = self.game.from_dict(data)
        self.assertFalse(result)

    def test_from_dict_sanea_tipos(self):
        """H-03: Celdas float en JSON deben convertirse a int."""
        data = {
            'tablero': [[2.0, 4.0, 0, 0],
                         [0, 0, 0, 0],
                         [0, 0, 0, 0],
                         [0, 0, 0, 0]],
            'puntuacion': 10,
            'max_ficha': 4,
            'high_score': 100
        }
        result = self.game.from_dict(data)
        self.assertTrue(result)
        self.assertIsInstance(self.game.tablero[0][0], int)
        self.assertEqual(self.game.tablero[0][0], 2)

    def test_guardar_y_cargar_atomico(self):
        """H-04: Test de guardado atómico."""
        temp_file = os.path.join(tempfile.gettempdir(), "test_2048_save.json")
        try:
            datos = {'test': True, 'valor': 42}
            self.game.guardar_json_atomico(temp_file, datos)
            with open(temp_file, 'r') as f:
                loaded = json.load(f)
            self.assertEqual(loaded['test'], True)
            self.assertEqual(loaded['valor'], 42)
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)

    def test_high_score_se_preserva(self):
        """High score debe persistir incluso con tablero inválido."""
        data = {'tablero': [[0]], 'high_score': 9999}
        self.game.from_dict(data)
        self.assertEqual(self.game.high_score, 9999)


class TestAnalisis(unittest.TestCase):
    """Tests para resumen y sugerencia."""

    def setUp(self):
        self.game = Logica2048(tamano=4)

    def test_resumen(self):
        self.game.tablero = [[2, 2, 0, 0] for _ in range(4)]
        self.game.puntuacion = 50
        self.game.max_ficha = 4
        resumen = self.game.obtener_resumen()
        self.assertIn("Puntaje: 50", resumen)
        self.assertIn("Ficha máxima: 4", resumen)
        self.assertIn("Celdas libres: 8", resumen)

    def test_sugerencia_izquierda(self):
        self.game.tablero = [[2, 2, 0, 0] for _ in range(4)]
        sug = self.game.obtener_sugerencia()
        self.assertEqual(sug, 'IZQUIERDA')

    def test_sugerencia_compleja(self):
        self.game.tablero = [[4, 4, 2, 2] for _ in range(4)]
        sug = self.game.obtener_sugerencia()
        self.assertEqual(sug, 'IZQUIERDA')

    def test_sugerencia_tablero_lleno_sin_movimiento(self):
        self.game.tablero = [
            [2, 4, 8, 16],
            [16, 8, 4, 2],
            [2, 4, 8, 16],
            [16, 8, 4, 2]
        ]
        sug = self.game.obtener_sugerencia()
        self.assertEqual(sug, "Ninguna")


class TestJuegoTerminado(unittest.TestCase):
    """Tests para detección de game over."""

    def setUp(self):
        self.game = Logica2048(tamano=4)

    def test_no_terminado_con_libres(self):
        self.assertFalse(self.game.juego_terminado())

    def test_no_terminado_con_adyacentes(self):
        self.game.tablero = [
            [2, 4, 8, 16],
            [16, 8, 4, 2],
            [2, 4, 8, 16],
            [16, 8, 4, 2]
        ]
        # Cambiar una celda para crear un par adyacente
        self.game.tablero[0][0] = 4  # Ahora [0][0]==4 y [0][1]==4
        self.assertFalse(self.game.juego_terminado())

    def test_terminado_sin_movimientos(self):
        self.game.tablero = [
            [2, 4, 8, 16],
            [16, 8, 4, 2],
            [2, 4, 8, 16],
            [16, 8, 4, 2]
        ]
        self.assertTrue(self.game.juego_terminado())


class TestAplicarMovimiento(unittest.TestCase):
    """Tests para el método unificado E-01 _aplicar_movimiento."""

    def setUp(self):
        self.game = Logica2048(tamano=4)

    def test_no_muta_original(self):
        """H-06: _aplicar_movimiento no debe mutar el tablero original."""
        tablero_orig = [
            [2, 2, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0]
        ]
        tablero_copia = [row[:] for row in tablero_orig]
        self.game._aplicar_movimiento(tablero_orig, 'IZQUIERDA')
        self.assertEqual(tablero_orig, tablero_copia)

    def test_fusion_izquierda(self):
        tablero = [
            [2, 2, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0]
        ]
        nuevo, cambio, pts, fusiones, moved, merges = \
            self.game._aplicar_movimiento(tablero, 'IZQUIERDA')
        self.assertTrue(cambio)
        self.assertEqual(nuevo[0][0], 4)
        self.assertEqual(pts, 4)
        self.assertEqual(merges, 1)

    def test_sin_cambio_retorna_false(self):
        tablero = [
            [2, 4, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0]
        ]
        _, cambio, _, _, _, _ = self.game._aplicar_movimiento(tablero, 'IZQUIERDA')
        self.assertFalse(cambio)


if __name__ == '__main__':
    unittest.main()
