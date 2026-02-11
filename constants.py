"""Constants and configuration for the 2048 project."""

# Game Configuration
ARCHIVO_GUARDADO = "savegame.json"
ARCHIVO_AJUSTES = "settings.json"
VALOR_VICTORIA = 2048

# UI Colors - Standard
COLOR_FONDO_TABLERO = (187, 173, 160)
COLORES_FONDO = {
    0: (205, 193, 180),   # #cdc1b4
    2: (238, 228, 218),   # #eee4da
    4: (237, 224, 200),   # #ede0c8
    8: (242, 177, 121),   # #f2b179
    16: (245, 149, 99),   # #f59563
    32: (246, 124, 95),   # #f67c5f
    64: (246, 94, 59),    # #f65e3b
    128: (237, 207, 114), # #edcf72
    256: (237, 204, 97),  # #edcc61
    512: (237, 200, 80),  # #edc850
    1024: (237, 197, 63), # #edc53f
    2048: (237, 194, 46)  # #edc22e
}

COLOR_TEXTO_OSCURO = (119, 110, 101)
COLOR_TEXTO_CLARO = (249, 246, 242)

# UI Colors - High Contrast
COLORES_FONDO_HC = {2**i: (0, 0, 0) for i in range(17)}
COLORES_FONDO_HC[0] = (0, 0, 0)

COLORES_TEXTO_HC = {
    2: (0, 255, 255),     # Cyan
    4: (255, 255, 0),     # Yellow
    8: (255, 0, 255),     # Magenta
    16: (0, 255, 0),      # Green
    32: (255, 128, 0),    # Orange
    64: (128, 0, 255),    # Purple
    128: (255, 0, 0),     # Red
    256: (0, 0, 255),     # Blue
    512: (128, 128, 128), # Grey
    1024: (255, 255, 255),# White
    2048: (255, 215, 0),  # Gold
}

# Windows Accessibility Constants
EVENT_OBJECT_NAMECHANGE = 0x800C
OBJID_CLIENT = -4
CHILDID_SELF = 0
