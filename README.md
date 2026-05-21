# 2048 Accesible — Edición Profesional v3.0.0

¡Bienvenido a **2048 Accesible**! Una versión diseñada específicamente para ser jugada con lectores de pantalla y ofrecer una experiencia fluida y gratificante.

## 🚀 Cómo Empezar
1. Descarga el archivo de la [última release](https://github.com/RHcomunications/2048-game/releases/latest).
2. Ejecuta `2048_Accesible.exe`.
3. Elige el tamaño de tablero (4×4 por defecto) y ¡a jugar!

## 🎮 Controles de Juego

### Navegación del Tablero
Usa estas teclas para explorar sin realizar movimientos:
- **Flechas**: Moverte celda por celda (A1, B1, C1, etc. son la primera fila)
- **Inicio / Fin**: Inicio o final de la fila actual
- **RePág / AvPág**: Inicio o final de la columna actual
- **Ctrl + Inicio**: Esquina superior izquierda (A1)
- **Ctrl + Fin**: Esquina inferior derecha
- **Ctrl + RePág**: Esquina superior derecha
- **Ctrl + AvPág**: Esquina inferior izquierda

### Mover Fichas
- **Shift + Flechas**: Desplaza fichas en esa dirección
- **Numpad 2/4/6/8** (NumLock activo): Movimiento directo sin Shift

### Información y Lectura
| Tecla | Acción |
|-------|--------|
| **S** | Puntaje actual |
| **E** | Casillas libres + ficha máxima |
| **I** | Resumen completo del estado |
| **H** | Sugerencia de mejor movimiento |
| **L** | Historial (últimos 5 anuncios) |
| **R** | Repetir último anuncio |
| **V** | Cambiar verbosidad (Bajo/Normal/Alto) |
| **F** | Leer todos los valores de la fila actual |
| **C** | Leer todos los valores de la columna actual |

### Gestión de Partida
| Atajo | Acción |
|-------|--------|
| **F5** | Activar/desactivar Alto Contraste |
| **Ctrl+Z** | Deshacer movimiento (máx. 3) |
| **Ctrl+R** | Reiniciar partida |
| **Ctrl+S** | Guardar manualmente |
| **F1** | Ayuda completa |
| **Esc** | Salir (guardado automático) |

## 📝 Notas Técnicas
- **Almacenamiento Seguro**: El progreso (`savegame.json`), configuración (`settings.json`) y bitácora (`game_events.log`) se guardan en el directorio del usuario `%APPDATA%\2048_Accesible` cumpliendo con las pautas de Windows.
- **Audio en Memoria**: Todos los sonidos se sintetizan dinámicamente y se reproducen directamente desde memoria sin crear archivos WAV temporales en disco.
- **Logs**: `game_events.log` registra cada acción para depuración de forma rotatoria para evitar que consuma espacio innecesario.

## 🛠️ Desarrollo
- Python 3.8+ · wxPython 4.x · Windows (winsound + ctypes.windll)
- Tests: `python -m unittest test_game_logic -v`
- Build: `python -m PyInstaller 2048_Accesible.spec --clean --noconfirm`

Consulta el [CHANGELOG](CHANGELOG.md) para el historial completo de cambios.

---
*Desarrollado con pasión por la accesibilidad universal.*
