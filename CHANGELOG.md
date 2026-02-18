# Changelog — 2048 Accesible

Todos los cambios notables de este proyecto se documentan en este archivo.

## [1.0.0] — 2026-02-17

### ✨ Características
- Juego 2048 completamente accesible con soporte para lectores de pantalla (NVDA, JAWS, Narrator)
- Tablero configurable (3×3 a 8×8) con selección al inicio
- Navegación por coordenadas con nombre de fila y columna (A1, B2, etc.)
- Movimiento de fichas con Shift + Flechas y Numpad 2/4/6/8
- Navegación avanzada: Home/End (fila), RePág/AvPág (columna), Ctrl+esquinas
- Lectura rápida de fila (F) y columna (C) completas
- Sistema de sugerencias inteligente con heurística de esquina
- Hitos de victoria extendidos (2048, 4096, 8192, 16384, 32768, 65536, 131072)
- Historial de anuncios (últimos 20) con tecla L
- Repetir último anuncio con tecla R
- Tres niveles de verbosidad (Bajo / Normal / Alto)

### 🎨 Interfaz
- Modo Alto Contraste (F5) con colores optimizados por ficha
- Indicadores visuales de celdas vacías en modo HC (borde punteado)
- Fuente escalable dinámicamente según tamaño de tablero
- Esquinas redondeadas y sombras en fichas
- Anillo de foco visible para navegación por teclado

### 🔊 Audio
- Efectos de sonido estéreo dinámicos para movimiento, fusión, undo, victoria y game over
- Frecuencia de sonido proporcional al valor de la ficha fusionada
- Caché LRU para sonidos generados dinámicamente
- Auto-limpieza de archivos temporales de audio al salir

### 💾 Persistencia
- Guardado automático después de cada movimiento
- Guardado atómico (escritura temporal + renombrado) para prevenir corrupción
- Carga robusta con saneamiento de tipos y validación de tamaño de tablero
- Separación de configuración (`settings.json`) y estado de juego (`savegame.json`)
- Deshacer hasta 3 movimientos (Ctrl+Z)

### ♿ Accesibilidad
- Notificaciones nativas de Windows (WinAPI) para lectores de pantalla
- Narrativa proactiva: bienvenida, game over, victoria con resumen completo
- Narrativa de fusiones consolidada (ej. "3 fichas 4 fusionadas")
- Atajos de teclado sin modificador para información rápida (S, E, I, H, V)
- Soporte para Numpad (NumLock activo) como alternativa de movimiento
- Atajos case-insensitive (funcionan con CapsLock)

### 🔧 Calidad de Código
- 7 pases de auditoría exhaustivos (56+ hallazgos identificados y corregidos)
- 45 pruebas unitarias cubriendo lógica de juego, serialización y análisis
- Código modular: `game_logic.py`, `game_ui.py`, `ui_components.py`, `sound_manager.py`, `constants.py`
- Limpieza de ~50 líneas de código muerto en el último pase
- Type hints completos y docstrings en español
