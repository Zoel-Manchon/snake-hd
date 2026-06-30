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
POWERUP_KINDS = ["slowmo", "double", "magnet", "ghost"]   # available pickup types
POWERUP_COOLDOWN = 220          # ticks between pickups appearing
POWERUP_LIFETIME = 90           # ticks a pickup stays before vanishing
POWERUP_EFFECTS = {
    "slowmo": {"duration": 150, "label": "SLOW-MO", "color": (86, 180, 225)},
    "double": {"duration": 150, "label": "x2 POINTS", "color": (190, 130, 240)},
    "magnet": {"duration": 120, "label": "MAGNET", "color": (235, 130, 100)},
    "ghost":  {"duration": 130, "label": "GHOST", "color": (90, 200, 255)},
}
SLOW_FACTOR = 0.5               # speed multiplier while slow-mo is active
SLOW_MIN = 6                    # never slower than this

# --- Enemy types ---------------------------------------------------------
# Spawn odds for each kind (relative weights). Initial mines are always plain.
ENEMY_WEIGHTS = {"mine": 5, "drifter": 3, "blinker": 2, "chaser": 2}
DRIFTER_INTERVAL = 14   # ticks between a drifter's one-cell moves (lower = faster)
BLINKER_PERIOD = 90     # full solid+faded cycle length, in ticks
BLINKER_SOLID = 58      # ticks of each cycle the blinker is solid (deadly)
CHASER_INTERVAL = 20    # ticks between a chaser's one-cell steps toward your head

# --- Leaderboard ---------------------------------------------------------
PLAYER_NAME = "ZOEL"    # your handle as it appears on the hash-chain leaderboard

# --- Fever mode (signature mechanic) ---------------------------------------
# Chain food up to the max combo and the board ignites: points multiply and
# the whole screen goes electric until the fever cools down.
FEVER_TRIGGER = COMBO_MAX          # combo needed to ignite fever
FEVER_DURATION = 360               # frames of fever (~6s @60fps), refreshed by chaining
FEVER_MULT = 2                     # extra score multiplier while fever is active
FEVER_COLORS = ((255, 64, 160), (64, 200, 255))   # electric magenta <-> cyan pulse

# --- Online leaderboard (optional) ------------------------------------------
# When the Rust/Axum server (see server/) is running, scores sync to a global
# board. When it's not reachable, the game silently falls back to the local
# hash-chain ledger - online play is never required.
ONLINE_ENABLED = True
SERVER_URL = "http://127.0.0.1:8080"

# --- 2-player couch versus --------------------------------------------------
VS_STEP_MS = 110            # ms per step (both snakes move together, fair + synced)
VS_WINS_TARGET = 3         # rounds needed to win the match
VS_P1 = (95, 208, 104)     # player 1 colour (green) - arrow keys
VS_P1_D = (44, 120, 64)
VS_P2 = (240, 150, 70)     # player 2 colour (orange) - WASD
VS_P2_D = (150, 86, 32)

# --- Evolving biomes (single-player journey) --------------------------------
# As the score climbs the board shifts through themed palettes. The first biome
# matches the default look, so a run starts exactly as before.
BIOME_EVERY = 40   # points between biome shifts
BIOMES = [
    {"name": "GARDEN",      "bg": (24, 26, 43), "grid": (34, 37, 58), "tint": (95, 208, 104),
     "weights": {"mine": 5, "drifter": 3, "blinker": 2, "chaser": 2}},   # balanced
    {"name": "EMBER CAVE",  "bg": (40, 22, 24), "grid": (62, 34, 34), "tint": (240, 120, 90),
     "weights": {"mine": 3, "drifter": 2, "blinker": 2, "chaser": 6}},   # hunters
    {"name": "DEEP SEA",    "bg": (14, 28, 46), "grid": (24, 44, 66), "tint": (90, 180, 240),
     "weights": {"mine": 2, "drifter": 7, "blinker": 2, "chaser": 2}},   # drifting currents
    {"name": "TOXIC MARSH", "bg": (24, 34, 20), "grid": (40, 54, 30), "tint": (170, 220, 70),
     "weights": {"mine": 3, "drifter": 2, "blinker": 7, "chaser": 2}},   # pulsing hazards
    {"name": "THE VOID",    "bg": (18, 16, 28), "grid": (32, 28, 46), "tint": (180, 130, 240),
     "weights": {"mine": 4, "drifter": 2, "blinker": 3, "chaser": 5}},   # chaos
]

# --- Game modes (single-player) ---------------------------------------------
GAME_MODES = ["CLASSIC", "TIME ATTACK", "ZEN"]
TIME_ATTACK_SECONDS = 60   # length of a Time Attack run
