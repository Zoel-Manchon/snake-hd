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

# --- Power-ups -----------------------------------------------------------
POWERUP_KINDS = ["slowmo", "double", "magnet"]   # available pickup types (more added over time)
POWERUP_COOLDOWN = 220          # ticks between pickups appearing
POWERUP_LIFETIME = 90           # ticks a pickup stays before vanishing
POWERUP_EFFECTS = {
    "slowmo": {"duration": 150, "label": "SLOW-MO", "color": (86, 180, 225)},
    "double": {"duration": 150, "label": "x2 POINTS", "color": (190, 130, 240)},
    "magnet": {"duration": 120, "label": "MAGNET", "color": (235, 130, 100)},
}
SLOW_FACTOR = 0.5               # speed multiplier while slow-mo is active
SLOW_MIN = 6                    # never slower than this
