# Changelog — 2048 Accesible

Todos los cambios notables de este proyecto se documentan en este archivo.

## [3.0.0] — 2026-05-21

### ✨ Características y Mejoras Core
- **Reescritura de Arquitectura Completa**: Reducción de más de un 40% del código fuente original (~1850 a ~1100 líneas). Estricta separación de responsabilidades (Modelo/Vista/Controlador). Eliminados comentarios internos redundantes de depuración.
- **Sonidos 100% en Memoria**: Rediseño del motor de audio (`SoundManager`) que genera y reproduce todas las secuencias directamente desde búferes de memoria mediante WinAPI nativa, eliminando por completo los archivos temporales WAV en disco y mejorando el rendimiento.
- **Almacenamiento Seguro (APPDATA)**: El progreso de la partida (`savegame.json`), configuración de accesibilidad (`settings.json`) y logs (`game_events.log`) se han movido a la carpeta de usuario `%APPDATA%\2048_Accesible`, cumpliendo con las mejores prácticas y estándares de seguridad.
- **Bitácora Rotativa**: Registro rotativo de logs (`game_events.log`) con límite de 1 MB y 3 rotaciones de respaldo, previniendo el crecimiento excesivo de logs en disco.
- **Mapeo de Coordenadas Coherente**: Fila = números (1-indexed), Columna = letras (A-J), resolviendo inconsistencias al consultar e interactuar con el tablero.

### ♿ Accesibilidad y Lector de Pantalla
- **Verbosidad Baja Mejorada**: En verbosidad baja (nivel 0) ahora se anuncia la coordenada simplificada (ej. `A1 4` en lugar de sólo `4`), asegurando que los usuarios invidentes siempre sepan dónde está su foco.
- **Sistema de Anuncio Unificado**: Arquitectura de anuncio de canal único que evita duplicaciones y sincroniza de forma limpia la relectura nativa mediante WinAPI `NotifyWinEvent`.
- **Foco Visual HC**: Los estados de Alto Contraste adaptan dinámicamente los paneles, celdas y anillos visuales de foco de forma inmediata y anuncian cada acción del sistema de forma coherente.

### 🔧 Calidad de Código y Pruebas
- **Type Safety**: Eliminados masivamente todos los comentarios `# type: ignore` silenciados mediante una tipación fuerte y el uso de dataclasses (`MoveResult`).
- **Pruebas de Lógica Actualizadas**: Cobertura completa adaptada a la nueva arquitectura `MoveResult` y validando rigurosamente todos los edge cases de movimiento y deshacer.

---

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
