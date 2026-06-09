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

# --- Bonus food ----------------------------------------------------------
BONUS_POINTS = 5       # points awarded for the golden apple
BONUS_CHANCE = 0.25    # chance a bonus appears after eating normal food
BONUS_LIFETIME = 60    # ticks the bonus stays on screen before vanishing

# --- Difficulty presets --------------------------------------------------
# base_speed: starting frames/sec  | speed_cap: fastest it gets
# enemy_interval: ticks between new mines | start_enemies: mines at the start
DIFFICULTIES = {
    "EASY":   {"base_speed": 8,  "speed_cap": 15, "enemy_interval": 150, "start_enemies": 1},
    "NORMAL": {"base_speed": 10, "speed_cap": 22, "enemy_interval": 80,  "start_enemies": 3},
    "HARD":   {"base_speed": 13, "speed_cap": 28, "enemy_interval": 45,  "start_enemies": 5},
}
DIFFICULTY_ORDER = ["EASY", "NORMAL", "HARD"]

# --- Combo multiplier ----------------------------------------------------
COMBO_WINDOW = 50   # ticks allowed between eats to keep the chain alive
COMBO_MAX = 5       # highest multiplier reachable
