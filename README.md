# 2048 Accesible - Edición Final

¡Bienvenido a **2048 Accesible**! Una versión diseñada específicamente para ser jugada con lectores de pantalla y ofrecer una experiencia fluida y gratificante.

## 🚀 Cómo Empezar
1. Ejecuta el archivo `2048_Accesible.exe`.
2. El juego se abrirá con el foco en la primera celda del tablero.

## 🎮 Controles de Juego

### Navegación del Tablero
Usa estas teclas cuando quieras explorar el estado de las celdas sin realizar movimientos:
- **FLECHAS**: Te permiten moverte por las celdas del tablero (A1, A2, B1, etc.). Escucharás la coordenada y el valor de la ficha.
- **INICIO (Home) / FIN (End)**: Salta directamente al inicio o al final de la fila actual.
- **RePág / AvPág**: Salta al inicio o al final de la columna actual.
- **Ctrl + INICIO**: Salta a la primera celda (A1, esquina superior izquierda).
- **Ctrl + FIN**: Salta a la última celda del tablero (esquina inferior derecha).
- **Ctrl + RePág**: Salta a la esquina superior derecha.
- **Ctrl + AvPág**: Salta a la esquina inferior izquierda.

### Jugando (Mover Fichas)
- **SHIFT + FLECHAS**: Desplaza todas las fichas en la dirección elegida para realizar fusiones.
- **Sonidos 2D/Stereo**: Escucharás sonidos que se desplazan de izquierda a derecha (o viceversa) indicando la dirección del movimiento aplicado.

### Teclas Rápidas de Información
- **S**: Escuchar tu **Puntuación** actual.
- **E**: Escuchar el **Estado** general (número de casillas libres y ficha máxima alcanzada).
- **V**: Cambiar el nivel de **Verbosidad** (Bajo, Normal, Alto) para ajustar cuánta información te da el juego.
- **H**: Escuchar el **Historial de anuncios** (los últimos 20 eventos importantes).

### Gestión de Partida
- **F5**: Alternar el modo de **Alto Contraste** visual.
- **Ctrl + Z**: **Deshacer** el último movimiento.
- **Ctrl + R**: **Reiniciar** una partida nueva.
- **Ctrl + S**: **Guardar** la partida manualmente.
- **F1**: Mostrar la **Ayuda** con todos los atajos.
- **ESC**: Salir del juego (se guarda automáticamente).

## 📝 Notas Técnicas
- **Guardado Automático**: Tu progreso se guarda en el archivo `savegame.json`. Si pierdes (Game Over), el archivo se borrará para empezar de cero.
- **Logs de Eventos**: El archivo `game_events.log` registra técnicamente cada acción para depuración.
- **Sin Instalación**: El ejecutable es "portable", puedes llevarlo en un USB y jugarlo en cualquier PC con Windows.

## 🛠️ Requisitos para Desarrollo
- Python 3.8+
- wxPython 4.x (`pip install wxPython`)
- Windows (para `winsound` y `ctypes.windll`)

---
*Desarrollado con pasión por la accesibilidad.*

