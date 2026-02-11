import unittest
from game_logic import Logica2048

class TestGameLogic(unittest.TestCase):
    def setUp(self):
        self.game = Logica2048(tamano=4)

    def test_initialization(self):
        self.assertEqual(self.game.tamano, 4)
        # Check that exactly two tiles are initialized
        count = sum(1 for row in self.game.tablero for cell in row if cell != 0)
        self.assertEqual(count, 2)
        self.assertEqual(self.game.puntuacion, 0)

    def test_procesar_linea_basic(self):
        # Merge identical
        line = [2, 2, 0, 0]
        merged, f_list, score, moved = self.game.procesar_linea(line)
        self.assertEqual(merged, [4, 0, 0, 0])
        self.assertEqual(score, 4)
        self.assertTrue(moved > 0)

        # Multiple merges
        line = [2, 2, 4, 4]
        merged, f_list, score, moved = self.game.procesar_linea(line)
        self.assertEqual(merged, [4, 8, 0, 0])
        self.assertEqual(score, 12)
        self.assertTrue(moved > 0)

        # No merge, just move
        line = [0, 2, 0, 4]
        merged, f_list, score, moved = self.game.procesar_linea(line)
        self.assertEqual(merged, [2, 4, 0, 0])
        self.assertEqual(score, 0)
        self.assertTrue(moved > 0)


    def test_move_logic(self):
        # Force a predictable board
        self.game.tablero = [
            [2, 0, 0, 2],
            [0, 0, 0, 0],
            [2, 0, 0, 0],
            [0, 0, 0, 0]
        ]
        
        # Move Left
        self.game.mover('IZQUIERDA')
        self.assertEqual(self.game.tablero[0][0], 4)
        self.assertEqual(self.game.tablero[2][0], 2)
        
        # Move Up
        self.game.tablero = [
            [2, 0, 0, 0],
            [2, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0]
        ]
        self.game.mover('ARRIBA')
        self.assertEqual(self.game.tablero[0][0], 4)

    def test_serialization(self):
        self.game.puntuacion = 100
        self.game.tablero[0][0] = 64
        data = self.game.to_dict()
        
        new_game = Logica2048(tamano=4)
        new_game.from_dict(data)
        
        self.assertEqual(new_game.puntuacion, 100)
        self.assertEqual(new_game.tablero[0][0], 64)

    def test_undo(self):
        orig_tablero = [row[:] for row in self.game.tablero]
        self.game.mover('DERECHA')
        self.game.deshacer()
        self.assertEqual(self.game.tablero, orig_tablero)

    def test_board_analysis(self):
        # Summary test
        self.game.tablero = [[2, 2, 0, 0] for _ in range(4)]
        self.game.puntuacion = 50
        self.game.max_ficha = 4
        resumen = self.game.obtener_resumen()
        self.assertIn("Puntaje: 50", resumen)
        self.assertIn("Ficha máxima: 4", resumen)
        self.assertIn("Celdas libres: 8", resumen)

        # Hint test
        # With [2, 2, 0, 0] rows, IZQUIERDA should be best (4 fusion points per row)
        sug = self.game.obtener_sugerencia()
        self.assertEqual(sug, 'IZQUIERDA')

        # Complex hint: [4, 4, 2, 2]
        # IZQUIERDA: [8, 4, 0, 0] -> score += 12
        # ARRIBA / ABAJO: No merges if all rows same
        self.game.tablero = [[4, 4, 2, 2] for _ in range(4)]
        sug = self.game.obtener_sugerencia()
        self.assertEqual(sug, 'IZQUIERDA')

if __name__ == '__main__':
    unittest.main()
