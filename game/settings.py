# game/settings.py

# --- HD grid -------------------------------------------------------------
# Everything is grid-aligned: WIDTH/HEIGHT are multiples of CELL_SIZE,
# and HUD_HEIGHT is a multiple of CELL_SIZE so the play area lines up.
CELL_SIZE = 40
WIDTH = 1200          # 30 columns
HEIGHT = 800          # 20 rows (incl. HUD)
HUD_HEIGHT = 80       # 2 rows tall

# --- Palette (dark HD theme) --------------------------------------------
BG = (24, 26, 43)         # playfield background
GRID = (34, 37, 58)       # subtle grid lines
HUD_BG = (15, 16, 28)     # HUD bar / panels
INK = (228, 230, 241)     # text, borders, dividers
ACCENT = (95, 208, 104)   # green accent for headings
