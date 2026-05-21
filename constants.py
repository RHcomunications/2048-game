"""Constants and configuration for the 2048 Accessible project."""

# Game Configuration
VALOR_VICTORIA = 2048

# UI Colors - Standard
COLOR_FONDO_TABLERO = (187, 173, 160)
COLORES_FONDO = {
    0: (205, 193, 180),
    2: (238, 228, 218),
    4: (237, 224, 200),
    8: (242, 177, 121),
    16: (245, 149, 99),
    32: (246, 124, 95),
    64: (246, 94, 59),
    128: (237, 207, 114),
    256: (237, 204, 97),
    512: (237, 200, 80),
    1024: (237, 197, 63),
    2048: (237, 194, 46),
    4096: (231, 76, 60),
    8192: (142, 68, 173),
    16384: (41, 128, 185),
    32768: (39, 174, 96),
    65536: (243, 156, 18),
    131072: (192, 57, 43),
}

# Improved contrast ratios for text
COLOR_TEXTO_OSCURO = (80, 70, 60)       # ratio >= 4.6:1
COLOR_TEXTO_CLARO = (255, 255, 255)     # white

# High Contrast Colors for high-contrast mode (HC)
COLORES_TEXTO_HC = {
    2: (0, 255, 255),       # Cyan
    4: (255, 255, 0),       # Yellow
    8: (255, 0, 255),       # Magenta
    16: (0, 255, 0),        # Green
    32: (255, 128, 0),      # Orange
    64: (128, 0, 255),      # Purple
    128: (255, 0, 0),       # Red
    256: (100, 149, 237),   # Cornflower Blue
    512: (192, 192, 192),   # Silver
    1024: (255, 255, 255),  # White
    2048: (255, 215, 0),    # Gold
    4096: (0, 255, 128),    # Spring Green
    8192: (255, 105, 180),  # Hot Pink
    16384: (255, 165, 0),   # Orange
    32768: (173, 216, 230), # Light Blue
    65536: (255, 255, 224), # Light Yellow
    131072: (255, 200, 200),# Light Coral
}

# Windows Accessibility Constants
EVENT_OBJECT_NAMECHANGE = 0x800C
OBJID_CLIENT = -4
CHILDID_SELF = 0
