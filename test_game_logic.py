"""Tests unitarios para la lógica pura de 2048 Accesible."""
import json
import os
import tempfile
import unittest
from game_logic import Logica2048, MoveResult
from game_ui import coord_nombre


class TestCoordNombre(unittest.TestCase):
    """Tests para la función utilitaria de conversión de coordenadas a notación humana."""

    def test_esquina_superior_izquierda(self):
        self.assertEqual(coord_nombre(0, 0), "A1")

    def test_fila_uno_columna_dos(self):
        self.assertEqual(coord_nombre(0, 1), "B1")

    def test_fila_dos_columna_uno(self):
        self.assertEqual(coord_nombre(1, 0), "A2")

    def test_esquina_inferior_derecha_4x4(self):
        self.assertEqual(coord_nombre(3, 3), "D4")

    def test_tablero_grande(self):
        self.assertEqual(coord_nombre(9, 9), "J10")


class TestInicializacion(unittest.TestCase):
    """Tests de inicialización y estados iniciales."""

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
        self.assertEqual(game.hitos_alcanzados, [])


class TestProcesarLinea(unittest.TestCase):
    """Tests para procesar_linea (compactación y fusión)."""

    def setUp(self):
        self.game = Logica2048(tamano=4)

    def test_fusion_simple(self):
        merged, f_list, score = self.game.procesar_linea([2, 2, 0, 0])
        self.assertEqual(merged, [4, 0, 0, 0])
        self.assertEqual(score, 4)

    def test_fusion_multiple(self):
        merged, f_list, score = self.game.procesar_linea([2, 2, 4, 4])
        self.assertEqual(merged, [4, 8, 0, 0])
        self.assertEqual(score, 12)

    def test_solo_movimiento(self):
        merged, f_list, score = self.game.procesar_linea([0, 2, 0, 4])
        self.assertEqual(merged, [2, 4, 0, 0])
        self.assertEqual(score, 0)

    def test_linea_sin_cambios(self):
        merged, f_list, score = self.game.procesar_linea([2, 4, 8, 16])
        self.assertEqual(merged, [2, 4, 8, 16])
        self.assertEqual(score, 0)

    def test_triple_no_doble_fusion(self):
        """[2, 2, 2, 0] debe fusionar los dos primeros, no los tres."""
        merged, f_list, score = self.game.procesar_linea([2, 2, 2, 0])
        self.assertEqual(merged, [4, 2, 0, 0])
        self.assertEqual(score, 4)

    def test_cuatro_iguales(self):
        """[4, 4, 4, 4] -> [8, 8, 0, 0] - dos fusiones separadas."""
        merged, f_list, score = self.game.procesar_linea([4, 4, 4, 4])
        self.assertEqual(merged, [8, 8, 0, 0])
        self.assertEqual(score, 16)

    def test_linea_vacia(self):
        merged, f_list, score = self.game.procesar_linea([0, 0, 0, 0])
        self.assertEqual(merged, [0, 0, 0, 0])
        self.assertEqual(score, 0)

    def test_linea_llena_sin_fusion(self):
        merged, f_list, score = self.game.procesar_linea([2, 4, 2, 4])
        self.assertEqual(merged, [2, 4, 2, 4])
        self.assertEqual(score, 0)


class TestMovimiento(unittest.TestCase):
    """Tests para el método mover() y MoveResult."""

    def setUp(self):
        self.game = Logica2048(tamano=4)

    def test_mover_izquierda(self):
        self.game.tablero = [
            [2, 0, 0, 2],
            [0, 0, 0, 0],
            [2, 0, 0, 0],
            [0, 0, 0, 0]
        ]
        res = self.game.mover('IZQUIERDA')
        self.assertTrue(res.cambio)
        self.assertEqual(self.game.tablero[0][0], 4)
        self.assertEqual(self.game.tablero[2][0], 2)

    def test_mover_arriba(self):
        self.game.tablero = [
            [2, 0, 0, 0],
            [2, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0]
        ]
        res = self.game.mover('ARRIBA')
        self.assertTrue(res.cambio)
        self.assertEqual(self.game.tablero[0][0], 4)

    def test_mover_derecha(self):
        self.game.tablero = [
            [2, 2, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0]
        ]
        res = self.game.mover('DERECHA')
        self.assertTrue(res.cambio)
        self.assertEqual(self.game.tablero[0][3], 4)

    def test_mover_abajo(self):
        self.game.tablero = [
            [2, 0, 0, 0],
            [2, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0]
        ]
        res = self.game.mover('ABAJO')
        self.assertTrue(res.cambio)
        self.assertEqual(self.game.tablero[3][0], 4)

    def test_movimiento_invalido_retorna_false(self):
        self.game.tablero = [
            [2, 4, 8, 16],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0]
        ]
        res = self.game.mover('IZQUIERDA')
        self.assertFalse(res.cambio)

    def test_mover_agrega_ficha(self):
        self.game.tablero = [
            [2, 0, 0, 2],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0]
        ]
        res = self.game.mover('IZQUIERDA')
        self.assertTrue(res.cambio)
        self.assertIsNotNone(res.ficha_nueva)
        count = sum(1 for row in self.game.tablero for cell in row if cell != 0)
        self.assertGreaterEqual(count, 2)


class TestDeshacer(unittest.TestCase):
    """Tests para deshacer (Undo)."""

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
        self.game.tablero = [
            [1024, 1024, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0]
        ]
        self.game.ganado = False
        self.game.hitos_alcanzados = []
        self.game.mover('IZQUIERDA')
        self.assertTrue(self.game.ganado)
        self.game.deshacer()
        self.assertFalse(self.game.ganado)

    def test_limite_historial(self):
        """Solo 3 undos disponibles en historial."""
        self.game.tablero = [
            [2, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0]
        ]
        for _ in range(5):
            self.game.tablero[0][1] = 0
            self.game.mover('DERECHA')
        self.assertLessEqual(len(self.game.history), 3)

    def test_deshacer_en_cadena(self):
        """3 undos en cadena."""
        self.game.tablero = [
            [0, 0, 0, 2],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0]
        ]
        self.game.history = []
        for _ in range(3):
            self.game.tablero[0][0] = 2
            self.game.tablero[0][3] = 0
            self.game.mover('DERECHA')
        for i in range(3):
            self.assertTrue(self.game.deshacer())
        self.assertFalse(self.game.deshacer())


class TestSerializacion(unittest.TestCase):
    """Tests de serialización (to_dict y from_dict)."""

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

    def test_high_score_se_preserva(self):
        data = {'tablero': [[0]], 'high_score': 9999}
        self.game.from_dict(data)
        self.assertEqual(self.game.high_score, 9999)


class TestAnalisis(unittest.TestCase):
    """Tests para obtener_resumen y obtener_sugerencia."""

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
        self.game.tablero[0][0] = 4
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
    """Tests para _aplicar_movimiento."""

    def setUp(self):
        self.game = Logica2048(tamano=4)

    def test_no_muta_original(self):
        tablero_orig = [
            [2, 2, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0]
        ]
        tablero_copia = [list(row) for row in tablero_orig]
        self.game._aplicar_movimiento(tablero_orig, 'IZQUIERDA')
        self.assertEqual(tablero_orig, tablero_copia)

    def test_fusion_izquierda(self):
        tablero = [
            [2, 2, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0]
        ]
        nuevo, cambio, pts, fusiones = self.game._aplicar_movimiento(tablero, 'IZQUIERDA')
        self.assertTrue(cambio)
        self.assertEqual(nuevo[0][0], 4)
        self.assertEqual(pts, 4)
        self.assertEqual(len(fusiones), 1)


if __name__ == '__main__':
    unittest.main()
