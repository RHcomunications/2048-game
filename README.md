# 2048 Accesible — Platinum Edition v1.0.0

¡Bienvenido a **2048 Accesible**! Una versión diseñada específicamente para ser jugada con lectores de pantalla y ofrecer una experiencia fluida y gratificante.

## 🚀 Cómo Empezar
1. Descarga el archivo `.zip` de la [última release](https://github.com/RHcomunications/2048-game/releases/latest).
2. Extrae el contenido en cualquier carpeta.
3. Ejecuta `2048_Accesible_Platinum.exe`.
4. Elige el tamaño de tablero (4×4 por defecto) y ¡a jugar!

## 🎮 Controles de Juego

### Navegación del Tablero
Usa estas teclas para explorar sin realizar movimientos:
- **Flechas**: Moverte celda por celda (A1, A2, B1, etc.)
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
| **L** | Historial (últimos 20 anuncios) |
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
- **Guardado Automático**: Progreso en `savegame.json`. En Game Over se borra para empezar de cero.
- **Configuración**: Verbosidad y alto contraste se guardan en `settings.json`.
- **Portable**: Sin instalación, llévalo en un USB.
- **Logs**: `game_events.log` registra cada acción para depuración.

## 🛠️ Desarrollo
- Python 3.8+ · wxPython 4.x · Windows (winsound + ctypes.windll)
- Tests: `python -m unittest test_game_logic -v` (45 tests)
- Build: `python -m PyInstaller 2048_Accesible_Platinum.spec --clean --noconfirm`

Consulta el [CHANGELOG](CHANGELOG.md) para el historial completo de cambios.

---
*Desarrollado con pasión por la accesibilidad universal.*
