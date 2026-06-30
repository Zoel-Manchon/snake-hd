import math
import pygame
import random

from helpers.helper_function import (
    draw_text_center,
    draw_background,
    draw_border,
    draw_overlay,
    draw_hud,
    draw_game_over_panel,
    draw_food,
    draw_bonus,
    draw_powerup,
    draw_effect,
    draw_combo,
    draw_enemies,
    draw_snake,
    draw_fps,
    load_sprites,
    lerp_color,
    draw_fever_tint,
    draw_fever_glow,
    draw_fever_vignette,
    draw_fever_banner,
    draw_fever_meter,
    draw_flash,
    draw_wave_text,
    draw_versus_snake,
    draw_boss,
    draw_boss_hp,
    draw_achievement_card,
)

from helpers.storage import load_high_score, save_high_score
from helpers.audio import init_audio, play_sound, play_eat, start_music, toggle_mute, is_muted
from helpers.fx import ParticleSystem, FloatingTextSystem
from helpers.ledger import record_score, top_scores
from helpers import online
from helpers import achievements
from helpers import daily

from game.settings import *
from game.snake_logic import move_snake_head
from game.collision_logic import hit_self, hit_enemy, hit_wall
from game.spawn_logic import random_position, random_safe_position, spawn_enemy
from game.enemies import Enemy
from game.boss import Boss

pygame.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Snake HD")

clock = pygame.time.Clock()

init_audio()
start_music()

font = pygame.font.Font("assets/PressStart2P.ttf", 22)
big_font = pygame.font.Font("assets/PressStart2P.ttf", 44)
small_font = pygame.font.Font("assets/PressStart2P.ttf", 14)

# Load the sprite set once (needs the display to exist for convert_alpha).
sprites = load_sprites(CELL_SIZE)
# Player-2 sprite set for versus: same art, orange recolour for head/body/tail.
sprites_p2 = {**sprites,
              "head": sprites["head_p2"], "body": sprites["body_p2"], "tail": sprites["tail_p2"]}

high_score = load_high_score()

# Visual FX: particle bursts and floating score popups (created once, cleared per run).
fx = ParticleSystem(BG)
popups = FloatingTextSystem(font)


def fade_out_current(speed=24):
    """Fade whatever is on screen out to black."""
    frame = screen.copy()
    black = pygame.Surface((WIDTH, HEIGHT)); black.fill((0, 0, 0))
    for a in range(0, 256, speed):
        screen.blit(frame, (0, 0)); black.set_alpha(a); screen.blit(black, (0, 0))
        pygame.display.update(); clock.tick(60)


def fade_in_current(speed=24):
    """Fade the freshly drawn frame in from black."""
    frame = screen.copy()
    black = pygame.Surface((WIDTH, HEIGHT)); black.fill((0, 0, 0))
    for a in range(255, -1, -speed):
        screen.blit(frame, (0, 0)); black.set_alpha(a); screen.blit(black, (0, 0))
        pygame.display.update(); clock.tick(60)
    screen.blit(frame, (0, 0)); pygame.display.update()


_DIR_NAME = {(CELL_SIZE, 0): "RIGHT", (-CELL_SIZE, 0): "LEFT",
             (0, CELL_SIZE): "DOWN", (0, -CELL_SIZE): "UP"}


class DemoSnake:
    """A snake that drives itself around the menu, chasing a roaming apple."""

    def __init__(self):
        self.cols = WIDTH // CELL_SIZE
        self.rows = HEIGHT // CELL_SIZE
        cx, cy = self.cols // 2, self.rows // 2
        self.cells = [[(cx - i) * CELL_SIZE, cy * CELL_SIZE] for i in range(6)]
        self.prev = [c[:] for c in self.cells]
        self.dir = (CELL_SIZE, 0)
        self.dir_name = "RIGHT"
        self.length = 9
        self.max_length = 14
        self.target = self._rand_cell()
        self.acc = 0.0
        self.step_ms = 95.0

    def _rand_cell(self):
        return [random.randrange(self.cols) * CELL_SIZE,
                random.randrange(self.rows) * CELL_SIZE]

    def _choose_dir(self):
        head = self.cells[0]
        back = (-self.dir[0], -self.dir[1])
        opts = [d for d in ((CELL_SIZE, 0), (-CELL_SIZE, 0), (0, CELL_SIZE), (0, -CELL_SIZE))
                if d != back]
        body = {tuple(c) for c in self.cells[:-1]}

        def ok(d):
            nx = (head[0] + d[0]) % WIDTH
            ny = (head[1] + d[1]) % HEIGHT
            return (nx, ny) not in body

        safe = [d for d in opts if ok(d)] or opts
        if random.random() < 0.78:                      # mostly chase the apple
            safe.sort(key=lambda d: abs(head[0] + d[0] - self.target[0])
                                    + abs(head[1] + d[1] - self.target[1]))
            return safe[0]
        return random.choice(safe)                      # sometimes wander

    def update(self, dt):
        self.acc += dt
        while self.acc >= self.step_ms:
            self.acc -= self.step_ms
            self.prev = [c[:] for c in self.cells]
            self.dir = self._choose_dir()
            self.dir_name = _DIR_NAME[self.dir]
            head = self.cells[0]
            nx = (head[0] + self.dir[0]) % WIDTH
            ny = (head[1] + self.dir[1]) % HEIGHT
            self.cells.insert(0, [nx, ny])
            if [nx, ny] == self.target:
                self.target = self._rand_cell()
                if self.length < self.max_length:
                    self.length += 1
            if len(self.cells) > self.length:
                self.cells.pop()

    def positions(self):
        t = min(1.0, self.acc / self.step_ms)
        out = []
        for i, cur in enumerate(self.cells):
            prv = self.prev[i] if i < len(self.prev) else cur
            dx, dy = cur[0] - prv[0], cur[1] - prv[1]
            if abs(dx) > CELL_SIZE or abs(dy) > CELL_SIZE:
                out.append([cur[0], cur[1]])
            else:
                out.append([prv[0] + dx * t, prv[1] + dy * t])
        return out


def achievements_screen():
    """A browsable gallery of all achievements: unlocked ones lit green with a
    check, locked ones dimmed with a padlock. ESC / A / ENTER returns to menu.
    Returns "quit" if the window was closed."""
    items = achievements.all_list()          # (id, name, desc, unlocked)
    margin_x, gap_x, gap_y = 60, 40, 15
    card_w = (WIDTH - 2 * margin_x - gap_x) // 2
    card_h, y0 = 100, 150
    shown = False

    while True:
        screen.fill(BG)
        u, t = achievements.unlocked_count(), achievements.total()
        draw_text_center(screen, "ACHIEVEMENTS", 44, big_font, ACCENT)
        draw_text_center(screen, f"{u} / {t} UNLOCKED", 110, font, INK)

        for i, (_aid, name, desc, unlocked) in enumerate(items):
            col, rowi = i % 2, i // 2
            x = margin_x + col * (card_w + gap_x)
            y = y0 + rowi * (card_h + gap_y)
            draw_achievement_card(screen, x, y, card_w, card_h,
                                  name, desc, unlocked, font, small_font)

        draw_text_center(screen, "ESC / A   BACK", 758, small_font, (120, 124, 150))
        draw_border(screen, WIDTH, HEIGHT, INK)

        if not shown:
            fade_in_current()
            shown = True
        else:
            pygame.display.update()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN and event.key in (
                    pygame.K_ESCAPE, pygame.K_a, pygame.K_RETURN, pygame.K_q):
                fade_out_current()
                return None


def start_menu():
    modes = [("SCREEN WRAP", True), ("WALLS", False)]
    mode_idx = 0
    diff_idx = DIFFICULTY_ORDER.index("NORMAL")
    gm_idx = 0
    players = [("1 PLAYER", 1), ("2 PLAYERS", 2)]
    pl_idx = 0
    row = 0  # 0 = mode, 1 = difficulty, 2 = game mode, 3 = players

    demo = DemoSnake()
    phase = 0.0
    faded_in = False
    online.fetch_board_async(5)   # pull the global board for display (non-blocking)

    while True:
        dt = clock.tick(60)
        phase += dt / 1000.0
        demo.update(dt)

        draw_background(screen, WIDTH, HEIGHT, CELL_SIZE, HUD_HEIGHT, BG, GRID, HUD_BG, INK)

        # The menu is alive: a self-driving snake chases a roaming apple.
        draw_food(screen, demo.target, CELL_SIZE, sprites)
        draw_snake(screen, demo.cells, CELL_SIZE, sprites, demo.dir_name, demo.positions())

        # Dim panel so the text stays readable over the moving snake.
        panel = pygame.Surface((780, 372), pygame.SRCALPHA)
        panel.fill((10, 12, 22, 185))
        pygame.draw.rect(panel, (*ACCENT, 70), panel.get_rect(), 2, border_radius=14)
        screen.blit(panel, ((WIDTH - 780) // 2, 244))

        # Animated logo: a travelling wave + a gentle green shimmer.
        title_color = lerp_color(ACCENT, (170, 245, 180), 0.5 + 0.5 * math.sin(phase * 2.2))
        draw_wave_text(screen, "SNAKE", WIDTH // 2, 140, big_font, title_color, phase * 3.5, amp=12)

        # Global leaderboard (top-left) when the server is reachable.
        board = online.BOARD
        if board["status"] == "online" and board["scores"]:
            bx, by, bw = 36, 96, 290
            rows = board["scores"][:5]
            bp = pygame.Surface((bw, 40 + len(rows) * 22), pygame.SRCALPHA)
            bp.fill((10, 12, 22, 180))
            pygame.draw.rect(bp, (*ACCENT, 70), bp.get_rect(), 2, border_radius=10)
            screen.blit(bp, (bx, by))
            screen.blit(small_font.render("GLOBAL TOP 5", True, ACCENT), (bx + 16, by + 12))
            for i, (nm, sc) in enumerate(rows):
                line = small_font.render(f"{i + 1}. {sc:>5}  {str(nm)[:8]}", True, INK)
                screen.blit(line, (bx + 16, by + 36 + i * 22))

        ach = f"ACHIEVEMENTS  {achievements.unlocked_count()}/{achievements.total()}  (A)"
        aimg = small_font.render(ach, True, ACCENT)
        screen.blit(aimg, (WIDTH - aimg.get_width() - 36, 104))

        mode_color = ACCENT if row == 0 else INK
        diff_color = ACCENT if row == 1 else INK
        gm_color = ACCENT if row == 2 else INK
        play_color = ACCENT if row == 3 else INK
        draw_text_center(screen, f"MODE:   < {modes[mode_idx][0]} >", 292, font, mode_color)
        draw_text_center(screen, f"DIFFICULTY:   < {DIFFICULTY_ORDER[diff_idx]} >", 334, font, diff_color)
        draw_text_center(screen, f"GAME MODE:   < {GAME_MODES[gm_idx]} >", 376, font, gm_color)
        draw_text_center(screen, f"PLAYERS:   < {players[pl_idx][0]} >", 418, font, play_color)

        if players[pl_idx][1] == 2:
            draw_text_center(screen, "P1 ARROWS    P2 WASD", 456, small_font, (150, 200, 255))

        draw_text_center(screen, "UP/DOWN SELECT     LEFT/RIGHT CHANGE", 494, small_font, INK)
        draw_text_center(screen, "ENTER START     P PAUSE     ESC END RUN", 522, small_font, INK)
        sound_label = "M: SOUND OFF" if is_muted() else "M: SOUND ON"
        draw_text_center(screen, sound_label, 550, small_font, INK)

        draw_border(screen, WIDTH, HEIGHT, INK)
        if not faded_in:
            fade_in_current()
            faded_in = True
        else:
            pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    row = (row - 1) % 4
                elif event.key == pygame.K_DOWN:
                    row = (row + 1) % 4
                elif event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                    step = 1 if event.key == pygame.K_RIGHT else -1
                    if row == 0:
                        mode_idx = (mode_idx + step) % len(modes)
                    elif row == 1:
                        diff_idx = (diff_idx + step) % len(DIFFICULTY_ORDER)
                    elif row == 2:
                        gm_idx = (gm_idx + step) % len(GAME_MODES)
                    else:
                        pl_idx = (pl_idx + step) % len(players)
                elif event.key == pygame.K_m:
                    toggle_mute()
                elif event.key == pygame.K_a:
                    fade_out_current()
                    if achievements_screen() == "quit":
                        return None
                    faded_in = False        # fade the menu back in on return
                elif event.key == pygame.K_RETURN:
                    fade_out_current()
                    return (modes[mode_idx][1], DIFFICULTY_ORDER[diff_idx],
                            GAME_MODES[gm_idx], players[pl_idx][1])


def game(wrap, difficulty, mode="CLASSIC"):
    global high_score

    daily_mode = mode == "DAILY"         # date-seeded run, own best/streak board
    if daily_mode:                       # everyone plays the same fixed config
        difficulty = DAILY_DIFFICULTY
        wrap = DAILY_WRAP

    cfg = DIFFICULTIES[difficulty]
    base_speed = cfg["base_speed"]
    speed_cap = cfg["speed_cap"]
    enemy_interval = cfg["enemy_interval"]
    start_enemies = cfg["start_enemies"]

    zen = mode == "ZEN"                  # no enemies, no death - just grow
    time_attack = mode == "TIME ATTACK"  # race a fixed clock
    if zen:
        wrap = True                      # nothing to crash into; always wrap
        start_enemies = 0

    did_fade_in = False   # fade the first frame in from black once per entry

    # Outer loop lets us restart cleanly without recursion.
    while True:
        # Grid-aligned starting state (all multiples of CELL_SIZE, below the HUD).
        snake = [[CELL_SIZE * 7, HUD_HEIGHT + CELL_SIZE * 5]]
        prev_snake = [list(seg) for seg in snake]   # pre-step positions, for smooth rendering
        direction = "RIGHT"
        next_direction = "RIGHT"

        # Daily Challenge: seed by date so the run is reproducible; otherwise
        # reseed from OS entropy so a prior daily run doesn't fix later runs.
        if daily_mode:
            random.seed(daily.today_seed())
        else:
            random.seed()

        food = random_position()
        bonus = None          # golden apple position, or None when inactive
        bonus_timer = 0       # steps remaining before it vanishes
        combo = 1             # current score multiplier
        combo_timer = 0       # steps left to keep the combo alive
        fever = False         # signature mechanic: electric high-combo state
        fever_timer = 0       # frames of fever remaining (refreshed by chaining)
        fever_phase = 0.0     # advances each frame to drive the pulsing visuals
        fever_flash = 0       # frames of the white ignite flash remaining
        shake_timer = 0       # frames of screen-shake remaining
        shake_mag = 0.0       # current shake magnitude in pixels
        biome_idx = 0         # current biome; advances as the score climbs
        biome_bg = BIOMES[0]["bg"]
        biome_grid = BIOMES[0]["grid"]
        biome_tint = BIOMES[0]["tint"]
        biome_weights = BIOMES[0].get("weights")   # per-biome enemy mix
        biome_name = ""       # name to flash when entering a new biome
        biome_flash = 0       # frames of the biome-entry colour flash
        biome_banner = 0      # frames the biome name stays on screen
        time_left = TIME_ATTACK_SECONDS * 1000 if time_attack else 0   # ms, Time Attack
        end_run = False       # set by ESC / time-up to finish the run
        toasts = []           # achievement toast queue: [name, frames_left]

        def award(aid):
            if achievements.unlock(aid):
                toasts.append([achievements.NAME[aid], 210])
                play_sound("bonus")

        # --- The Void Warden boss state ---
        boss = None              # Boss instance while the fight is on, else None
        boss_active = False      # True during the encounter
        boss_done = False        # True once defeated this run (no re-trigger)
        boss_banner = 0          # frames the boss banner stays up
        boss_banner_text = ""

        def kill():
            """Run the full death sequence (used by both normal deaths and a
            boss projectile hit). Finalizes the score and plays the animation."""
            nonlocal game_over, fever, accumulator, leaderboard
            game_over = True
            fever = False
            accumulator = 0.0
            if daily_mode:                    # Daily records to its own board
                daily.record(score)
            elif not zen:                     # Zen runs are unranked
                record_score(score, PLAYER_NAME)
                online.submit_async(PLAYER_NAME, score, 5)
            leaderboard = top_scores(5)
            play_sound("death")
            hx = snake[0][0] + CELL_SIZE // 2
            hy = snake[0][1] + CELL_SIZE // 2
            fx.burst(hx, hy, (235, 70, 84), count=34, speed=4.5, size=6, life=46)
            for alpha in (200, 150, 105, 65, 30, 0):
                buf = pygame.Surface((WIDTH, HEIGHT))
                draw_background(buf, WIDTH, HEIGHT, CELL_SIZE, HUD_HEIGHT, biome_bg, biome_grid, HUD_BG, INK)
                draw_food(buf, food, CELL_SIZE, sprites)
                if bonus is not None:
                    draw_bonus(buf, bonus, CELL_SIZE, sprites)
                draw_enemies(buf, enemies, CELL_SIZE, sprites)
                draw_snake(buf, snake, CELL_SIZE, sprites, direction)
                if boss_active and boss is not None:
                    draw_boss(buf, boss, CELL_SIZE)
                fx.update()
                fx.draw(buf)
                draw_hud(buf, score, high_score, enemies, font, big_font, INK)
                draw_overlay(buf, (220, 60, 60), alpha)
                draw_border(buf, WIDTH, HEIGHT, INK)
                mag = int(14 * (alpha / 200))
                dx = random.randint(-mag, mag) if mag else 0
                dy = random.randint(-mag, mag) if mag else 0
                screen.fill(biome_bg)
                screen.blit(buf, (dx, dy))
                pygame.display.update()
                clock.tick(40)

        powerup = None        # pickup position on the board, or None
        powerup_kind = None   # which power-up the current pickup grants
        powerup_life = 0      # steps before the pickup vanishes
        spawn_cooldown = POWERUP_COOLDOWN  # steps until the next pickup
        effects = {}          # active timed effects -> steps remaining

        # Initial mines placed below the snake's starting row, scaled by difficulty.
        enemies = [
            Enemy([CELL_SIZE * (8 + 3 * i), HUD_HEIGHT + CELL_SIZE * 9], "mine")
            for i in range(start_enemies)
        ]

        enemy_timer = 0
        score = 0

        fx.clear()
        popups.clear()
        leaderboard = []   # filled in from the ledger when the run ends
        online.reset()     # clear any global-board state from the previous run
        go_sel = 0         # game-over menu selection: 0 restart, 1 menu, 2 quit

        running = True
        game_over = False
        paused = False
        restart = False

        def draw_active_bonus():
            # Blink during the final ~15 steps to signal it's about to vanish.
            if bonus is not None and (bonus_timer > 15 or bonus_timer % 2 == 0):
                draw_bonus(screen, bonus, CELL_SIZE, sprites)

        # Time accumulator: the render loop runs at a steady 60 FPS, while the
        # snake advances one logical "step" every (1000 / speed) milliseconds.
        accumulator = 0.0

        while running:
            frame_ms = clock.tick(60)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP and direction != "DOWN":
                        next_direction = "UP"
                    elif event.key == pygame.K_DOWN and direction != "UP":
                        next_direction = "DOWN"
                    elif event.key == pygame.K_LEFT and direction != "RIGHT":
                        next_direction = "LEFT"
                    elif event.key == pygame.K_RIGHT and direction != "LEFT":
                        next_direction = "RIGHT"

                    if event.key == pygame.K_p:
                        paused = not paused

                    if event.key == pygame.K_ESCAPE and not game_over:
                        end_run = True   # finish the run -> game-over panel

                    if event.key == pygame.K_m:
                        toggle_mute()

                    if game_over:
                        if event.key in (pygame.K_UP, pygame.K_DOWN):
                            go_sel = (go_sel + (1 if event.key == pygame.K_DOWN else -1)) % 3
                        elif event.key == pygame.K_SPACE:
                            restart = True          # quick restart
                            running = False
                        elif event.key == pygame.K_RETURN:
                            if go_sel == 0:          # RESTART
                                restart = True
                                running = False
                            elif go_sel == 1:        # MAIN MENU
                                fade_out_current()
                                return "menu"
                            else:                    # QUIT
                                return "quit"

            if restart:
                break

            # ---- simulation: advance whole steps based on elapsed time ----
            render_positions = None   # smooth (interpolated) snake coords for rendering
            if not paused and not game_over:
                speed = min(base_speed + score, speed_cap)
                if "slowmo" in effects:
                    speed = max(SLOW_MIN, int(speed * SLOW_FACTOR))
                step_interval = 1000.0 / speed

                accumulator += frame_ms
                if accumulator > 250:        # avoid a burst of catch-up steps after a hitch
                    accumulator = 250.0

                while accumulator >= step_interval and not game_over:
                    accumulator -= step_interval
                    prev_snake = [list(seg) for seg in snake]   # state before this step

                    enemy_timer += 1
                    if not zen and not boss_active and enemy_timer >= enemy_interval:
                        spawn_enemy(enemies, snake, food, biome_weights)
                        enemy_timer = 0

                    # Drifters slide, blinkers phase on/off.
                    occupied = {tuple(e.pos) for e in enemies}
                    for e in enemies:
                        e.update(snake, food, occupied)

                    # The Warden aims at the head and fires on its cooldown.
                    if boss_active and boss is not None:
                        boss.on_step(snake[0])

                    if bonus is not None:
                        bonus_timer -= 1
                        if bonus_timer <= 0:
                            bonus = None

                    if combo_timer > 0:
                        combo_timer -= 1
                        if combo_timer == 0:
                            combo = 1

                    # Power-up pickup: appears on a cooldown, then vanishes if ignored.
                    if powerup is None:
                        spawn_cooldown -= 1
                        if spawn_cooldown <= 0:
                            powerup = random_safe_position(snake, food, enemies)
                            powerup_kind = random.choice(POWERUP_KINDS)
                            powerup_life = POWERUP_LIFETIME
                    else:
                        powerup_life -= 1
                        if powerup_life <= 0:
                            powerup = None
                            spawn_cooldown = POWERUP_COOLDOWN

                    # Tick down any active effects.
                    for name in list(effects):
                        effects[name] -= 1
                        if effects[name] <= 0:
                            del effects[name]

                    # Magnet: nudge the apple one cell toward the head (every other step).
                    if "magnet" in effects and effects["magnet"] % 2 == 0:
                        hx, hy = snake[0]
                        food_x, food_y = food
                        if abs(hx - food_x) >= abs(hy - food_y) and hx != food_x:
                            target = [food_x + (CELL_SIZE if hx > food_x else -CELL_SIZE), food_y]
                        elif hy != food_y:
                            target = [food_x, food_y + (CELL_SIZE if hy > food_y else -CELL_SIZE)]
                        else:
                            target = food
                        if target != food and target not in snake and tuple(target) not in {tuple(e.pos) for e in enemies}:
                            food = target

                    direction = next_direction
                    new_head = move_snake_head(snake, direction, wrap)

                    ate_food = new_head == food
                    ate_bonus = bonus is not None and new_head == bonus
                    will_grow = ate_food or ate_bonus
                    body_to_check = snake if will_grow else snake[:-1]

                    wall_death = (not wrap) and hit_wall(new_head)
                    ghost = "ghost" in effects   # phase through tail + enemies while active
                    boss_hazard = (boss.solid_cells() | boss.projectile_cells()) if boss_active and boss is not None else set()
                    lethal = (not zen) and (wall_death
                        or (tuple(new_head) in boss_hazard)
                        or (not ghost and (
                            hit_self(new_head, body_to_check) or hit_enemy(new_head, enemies))))

                    if lethal or end_run:
                        if lethal:
                            kill()                        # finalize + death animation
                        else:                             # ESC / time-up: finalize only
                            game_over = True
                            fever = False
                            accumulator = 0.0
                            if daily_mode:
                                daily.record(score)
                            elif not zen:
                                record_score(score, PLAYER_NAME)
                                online.submit_async(PLAYER_NAME, score, 5)
                            leaderboard = top_scores(5)
                        break   # leave the step loop; the game-over screen renders next frame

                    snake.insert(0, new_head)

                    if will_grow:
                        mult = 2 if "double" in effects else 1
                        gx = new_head[0] + CELL_SIZE // 2
                        gy = new_head[1] + CELL_SIZE // 2
                        if ate_bonus:
                            if fever:
                                fever_timer = FEVER_DURATION   # bonus keeps the fever alive
                            gained = BONUS_POINTS * combo * mult * (FEVER_MULT if fever else 1)
                            score += gained
                            play_sound("bonus")
                            bonus = None
                            shake_timer, shake_mag = 5, 5.0
                            combo_timer = COMBO_WINDOW   # keep the chain alive
                            bc = FEVER_COLORS[1] if fever else (255, 210, 70)
                            fx.burst(gx, gy, bc, count=28 if fever else 24,
                                     speed=4.0 if fever else 3.5, size=7 if fever else 6, life=44)
                            popups.add(gx, gy - 6, f"+{gained}", (255, 210, 70))
                        else:
                            combo = min(combo + 1, COMBO_MAX) if combo_timer > 0 else 1
                            # Ignite (or sustain) fever once the combo hits its peak.
                            if combo >= FEVER_TRIGGER:
                                if not fever:
                                    fever = True
                                    fever_flash = 8
                                    shake_timer, shake_mag = 9, 8.0
                                    play_sound("fever")
                                    award("on_fire")
                                fever_timer = FEVER_DURATION
                            gained = combo * mult * (FEVER_MULT if fever else 1)
                            score += gained
                            play_eat(combo)
                            combo_timer = COMBO_WINDOW
                            if fever:
                                fx.burst(gx, gy, FEVER_COLORS[1], count=26, speed=4.2, size=7, life=44)
                            else:
                                fx.burst(gx, gy, ACCENT, count=14, speed=3.0, size=5, life=36)
                            popups.add(gx, gy - 6, f"+{gained}", FEVER_COLORS[0] if fever else ACCENT)

                        if score > high_score:
                            high_score = score
                            save_high_score(high_score)

                        if ate_food:
                            food = random_safe_position(snake, food, enemies)
                            # Keep the apple off the Warden's body so it stays reachable.
                            if boss_active and boss is not None:
                                guard = 0
                                while tuple(food) in boss.solid_cells() and guard < 40:
                                    food = random_safe_position(snake, food, enemies)
                                    guard += 1
                            if bonus is None and random.random() < BONUS_CHANCE:
                                bonus = random_safe_position(snake, food, enemies)
                                bonus_timer = BONUS_LIFETIME

                            # Eating an apple during the fight drains the Warden.
                            if boss_active and boss is not None:
                                bx, by = boss.center_px()
                                if boss.hit():        # defeated
                                    score += BOSS_BONUS
                                    fx.burst(bx, by, (255, 120, 200), count=60, speed=6.0, size=8, life=60)
                                    fx.burst(bx, by, (255, 255, 255), count=30, speed=4.0, size=6, life=48)
                                    popups.add(bx, by, f"+{BOSS_BONUS}", (255, 200, 80))
                                    shake_timer, shake_mag = 20, 13.0
                                    fever_flash = 8
                                    play_sound("bonus")
                                    award("void_slayer")
                                    boss_active = False
                                    boss_done = True
                                    boss = None
                                    boss_banner = 170
                                    boss_banner_text = "WARDEN DEFEATED  +500"
                                    if score > high_score:
                                        high_score = score
                                        save_high_score(high_score)
                                else:                 # flinch
                                    fx.burst(bx, by, (255, 120, 200), count=18, speed=4.0, size=6, life=34)
                                    shake_timer, shake_mag = 7, 6.5
                                    play_sound("powerup")
                    else:
                        snake.pop()

                    # Collect a power-up if the head lands on it (does not grow the snake).
                    if powerup is not None and new_head == powerup:
                        effects[powerup_kind] = POWERUP_EFFECTS[powerup_kind]["duration"]
                        play_sound("powerup")
                        pc = POWERUP_EFFECTS[powerup_kind]["color"]
                        gx = new_head[0] + CELL_SIZE // 2
                        gy = new_head[1] + CELL_SIZE // 2
                        fx.burst(gx, gy, pc, count=26, speed=3.5, size=6, life=42)
                        popups.add(gx, gy - 6, POWERUP_EFFECTS[powerup_kind]["label"], pc)
                        powerup = None
                        spawn_cooldown = POWERUP_COOLDOWN

                # Interpolate render positions so the snake glides between cells
                # at 60 FPS instead of jumping a whole cell each step.
                if not game_over:
                    t = min(1.0, accumulator / step_interval)
                    render_positions = []
                    for i, cur in enumerate(snake):
                        prv = prev_snake[i] if i < len(prev_snake) else cur
                        dx = cur[0] - prv[0]
                        dy = cur[1] - prv[1]
                        if abs(dx) > CELL_SIZE or abs(dy) > CELL_SIZE:   # wrapped edge -> snap
                            render_positions.append([cur[0], cur[1]])
                        else:
                            render_positions.append([prv[0] + dx * t, prv[1] + dy * t])

            # ---- per-frame visual updates (smooth at 60 FPS) ----
            fx.update()
            popups.update()

            # ---- fever-mode timing + pulse values ----
            if fever and not paused and not game_over:
                fever_timer -= 1
                fever_phase += frame_ms / 1000.0
                if fever_timer <= 0:
                    fever = False
            if fever_flash > 0 and not paused:
                fever_flash -= 1

            # ---- Void Warden per-frame update ----
            if boss_active and boss is not None and not paused and not game_over:
                if boss.advance(frame_ms):       # True on the frame a radial burst fires
                    play_sound("fever")
                    shake_timer, shake_mag = 9, 7.5
                if tuple(snake[0]) in boss.projectile_cells():
                    kill()                # a projectile caught the stationary head
            if boss_banner > 0 and not paused:
                boss_banner -= 1

            # Evolving biomes: shift the board palette as the score climbs.
            if not paused and not game_over:
                target_biome = (score // BIOME_EVERY) % len(BIOMES)
                if target_biome != biome_idx:
                    biome_idx = target_biome
                    b = BIOMES[biome_idx]
                    biome_bg, biome_grid, biome_tint = b["bg"], b["grid"], b["tint"]
                    biome_weights = b.get("weights")
                    biome_name = b["name"]
                    biome_flash = 12
                    biome_banner = 150
                    if biome_idx == len(BIOMES) - 1:
                        award("globetrotter")
                        # First arrival in THE VOID (outside Zen) wakes the Warden.
                        if not zen and not boss_done and not boss_active:
                            boss = Boss(WIDTH, HEIGHT)
                            boss_active = True
                            enemies.clear()
                            boss_banner = 175
                            boss_banner_text = "THE VOID WARDEN"
                            shake_timer, shake_mag = 14, 9.0
                            play_sound("fever")
            if biome_flash > 0 and not paused:
                biome_flash -= 1
            if biome_banner > 0 and not paused:
                biome_banner -= 1

            # Time Attack: run the clock down; at zero the run ends.
            if time_attack and not paused and not game_over:
                time_left -= frame_ms
                if time_left <= 0:
                    time_left = 0
                    end_run = True

            # Achievement checks (award() is a no-op once unlocked).
            if not game_over and not paused:
                if score >= 10:
                    award("first_blood")
                if score >= 100:
                    award("century")
                if score >= 250:
                    award("survivor")
                if combo >= COMBO_MAX:
                    award("combo_master")
                if "ghost" in effects:
                    award("phase_shift")
                if time_attack and score >= 50:
                    award("beat_clock")
                if zen and len(snake) >= 50:
                    award("zen_master")

            pulse = 0.0
            fever_color = FEVER_COLORS[0]
            if fever:
                pulse = 0.5 + 0.5 * math.sin(fever_phase * 9.0)      # fast strobe 0..1
                sweep = 0.5 + 0.5 * math.sin(fever_phase * 2.5)      # slow magenta<->cyan
                fever_color = lerp_color(FEVER_COLORS[0], FEVER_COLORS[1], sweep)

            # ---- render (every frame) ----
            draw_background(screen, WIDTH, HEIGHT, CELL_SIZE, HUD_HEIGHT, biome_bg, biome_grid, HUD_BG, INK)
            if fever:
                draw_fever_tint(screen, WIDTH, HEIGHT, HUD_HEIGHT, fever_color, 26 + 30 * pulse)
            draw_food(screen, food, CELL_SIZE, sprites)
            draw_active_bonus()
            if powerup is not None and not game_over:
                draw_powerup(screen, powerup, powerup_kind, CELL_SIZE, sprites)
            draw_enemies(screen, enemies, CELL_SIZE, sprites)
            if "ghost" in effects and not game_over:   # phasing aura
                aura = 0.26 + 0.10 * math.sin(pygame.time.get_ticks() * 0.02)
                draw_fever_glow(screen, render_positions if render_positions else snake,
                                CELL_SIZE, (90, 200, 255), aura)
            if fever:
                draw_fever_glow(screen, render_positions if render_positions else snake,
                                CELL_SIZE, fever_color, 0.35 + 0.45 * pulse)
            draw_snake(screen, snake, CELL_SIZE, sprites, direction, render_positions)
            fx.draw(screen)
            if boss_active and boss is not None and not game_over:
                draw_boss(screen, boss, CELL_SIZE)
            if fever:
                draw_fever_vignette(screen, WIDTH, HEIGHT, HUD_HEIGHT, fever_color, 120 + 90 * pulse)
            if not game_over and not paused:
                popups.draw(screen)

            if time_attack:
                secs = int(max(0, time_left) // 1000)
                tcol = (235, 90, 90) if secs <= 10 else INK   # red in the final 10s
                draw_hud(screen, score, high_score, enemies, font, big_font, INK,
                         timer=f"{secs // 60}:{secs % 60:02d}", timer_color=tcol)
            elif zen:
                draw_hud(screen, score, high_score, enemies, font, big_font, INK,
                         right_override="ZEN", right_color=(150, 200, 255))
            elif daily_mode:
                draw_hud(screen, score, high_score, enemies, font, big_font, INK,
                         right_override="DAILY", right_color=(210, 170, 90))
            else:
                draw_hud(screen, score, high_score, enemies, font, big_font, INK)

            if game_over:
                if daily_mode:
                    board = daily.history(5)
                    sk = daily.streak()
                    board_title = f"DAILY {daily.today_str()[5:]}   STREAK {sk}"
                    draw_game_over_panel(screen, score, high_score, font, big_font, HUD_BG, INK,
                                         board, ACCENT, go_sel, board_title, None)
                else:
                    ostate = online.STATE
                    if ostate["status"] == "online":
                        board, board_title = ostate["scores"], "GLOBAL TOP 5"
                    else:
                        board, board_title = leaderboard, "LOCAL TOP 5"
                    draw_game_over_panel(screen, score, high_score, font, big_font, HUD_BG, INK,
                                         board, ACCENT, go_sel, board_title, ostate["status"])
            elif paused:
                draw_text_center(screen, "PAUSED", 340, big_font, ACCENT)
                draw_text_center(screen, "Press P to resume", 430, font, INK)
            else:
                if fever:
                    draw_fever_banner(screen, FEVER_MULT, fever_color, big_font, 170 + 85 * pulse, HUD_HEIGHT)
                    draw_fever_meter(screen, fever_timer / FEVER_DURATION, fever_color, WIDTH, HUD_HEIGHT)
                elif combo > 1:
                    draw_combo(screen, combo, combo_timer, COMBO_WINDOW, font, ACCENT)
                for i, (name, ticks) in enumerate(effects.items()):
                    cfg = POWERUP_EFFECTS[name]
                    draw_effect(screen, cfg["label"], ticks, cfg["duration"], font, cfg["color"], row=i)
                if boss_active and boss is not None:
                    draw_boss_hp(screen, boss, small_font, WIDTH, HEIGHT)
                if is_muted():
                    draw_text_center(screen, "MUTED", HEIGHT - 36, font, (120, 124, 150))

            if fever_flash > 0:
                draw_flash(screen, 200 * fever_flash / 8)

            if biome_flash > 0:
                draw_overlay(screen, biome_tint, int(85 * biome_flash / 12))
            if biome_banner > 0 and not game_over:
                a = 255 if biome_banner > 40 else int(255 * biome_banner / 40)
                img = big_font.render(biome_name, True, biome_tint)
                img.set_alpha(a)
                screen.blit(img, ((WIDTH - img.get_width()) // 2, HUD_HEIGHT + 22))

            if boss_banner > 0 and not game_over:
                a = 255 if boss_banner > 50 else int(255 * boss_banner / 50)
                img = big_font.render(boss_banner_text, True, (255, 110, 200))
                img.set_alpha(a)
                screen.blit(img, ((WIDTH - img.get_width()) // 2, HEIGHT // 2 - 28))

            # Achievement toasts (stacked at the bottom, newest lowest).
            ty = HEIGHT - 70
            for toast in toasts:
                name, timer = toast
                a = 255 if timer > 40 else int(255 * timer / 40)
                label = small_font.render(f"ACHIEVEMENT   {name}", True, (16, 18, 28))
                pad = 18
                w = label.get_width() + pad * 2
                pill = pygame.Surface((w, 34), pygame.SRCALPHA)
                pygame.draw.rect(pill, (*ACCENT, a), pill.get_rect(), border_radius=9)
                px = (WIDTH - w) // 2
                screen.blit(pill, (px, ty))
                label.set_alpha(a)
                screen.blit(label, (px + pad, ty + 9))
                toast[1] -= 1
                ty -= 42
            toasts[:] = [t for t in toasts if t[1] > 0]

            draw_fps(screen, clock, small_font)
            draw_border(screen, WIDTH, HEIGHT, INK)

            # Screen shake: re-blit the finished frame at a decaying random offset.
            if shake_timer > 0 and not paused:
                shake_timer -= 1
                m = int(shake_mag)
                if m > 0:
                    buf = screen.copy()
                    screen.fill((0, 0, 0))
                    screen.blit(buf, (random.randint(-m, m), random.randint(-m, m)))
                shake_mag *= 0.8

            if not did_fade_in:
                fade_in_current()
                did_fade_in = True
            else:
                pygame.display.update()

class VSnake:
    """A player snake for versus mode (smooth interpolation, no-reverse turns)."""

    def __init__(self, cells, direction, color, dark):
        self.cells = [list(c) for c in cells]
        self.prev = [list(c) for c in self.cells]
        self.dir = list(direction)
        self.next_dir = list(direction)
        self.alive = True
        self.color = color
        self.dark = dark

    @property
    def head(self):
        return self.cells[0]

    @property
    def dir_name(self):
        return _DIR_NAME.get((self.dir[0], self.dir[1]), "RIGHT")

    def turn(self, d):
        if [-self.dir[0], -self.dir[1]] != list(d):   # can't instantly reverse
            self.next_dir = list(d)

    def positions(self, t):
        out = []
        for i, cur in enumerate(self.cells):
            prv = self.prev[i] if i < len(self.prev) else cur
            dx, dy = cur[0] - prv[0], cur[1] - prv[1]
            if abs(dx) > CELL_SIZE or abs(dy) > CELL_SIZE:
                out.append([cur[0], cur[1]])
            else:
                out.append([prv[0] + dx * t, prv[1] + dy * t])
        return out


def _vs_wrap(p):
    span = HEIGHT - HUD_HEIGHT
    return [p[0] % WIDTH, (p[1] - HUD_HEIGHT) % span + HUD_HEIGHT]


def _versus_step(a, b, food, wrap):
    """Advance both snakes one step simultaneously; returns (dead_a, dead_b, ate_a, ate_b)."""
    a.dir, b.dir = list(a.next_dir), list(b.next_dir)
    ah = [a.head[0] + a.dir[0], a.head[1] + a.dir[1]]
    bh = [b.head[0] + b.dir[0], b.head[1] + b.dir[1]]

    awall = bwall = False
    if wrap:
        ah, bh = _vs_wrap(ah), _vs_wrap(bh)
    else:
        awall = ah[0] < 0 or ah[0] >= WIDTH or ah[1] < HUD_HEIGHT or ah[1] >= HEIGHT
        bwall = bh[0] < 0 or bh[0] >= WIDTH or bh[1] < HUD_HEIGHT or bh[1] >= HEIGHT

    ate_a = (not awall) and ah == list(food)
    ate_b = (not bwall) and bh == list(food)
    abody = a.cells if ate_a else a.cells[:-1]      # tail vacates unless growing
    bbody = b.cells if ate_b else b.cells[:-1]
    occ = {tuple(c) for c in abody} | {tuple(c) for c in bbody}

    dead_a = awall or tuple(ah) in occ or ah == bh   # ah==bh -> head-on, both die
    dead_b = bwall or tuple(bh) in occ or bh == ah

    a.prev = [list(c) for c in a.cells]
    b.prev = [list(c) for c in b.cells]
    if not dead_a:
        a.cells.insert(0, ah)
        if not ate_a:
            a.cells.pop()
    if not dead_b:
        b.cells.insert(0, bh)
        if not ate_b:
            b.cells.pop()
    a.alive, b.alive = not dead_a, not dead_b
    return dead_a, dead_b, ate_a, ate_b


def _vs_food(p1, p2):
    occ = {tuple(c) for c in p1.cells} | {tuple(c) for c in p2.cells}
    cols, rows = WIDTH // CELL_SIZE, (HEIGHT - HUD_HEIGHT) // CELL_SIZE
    while True:
        c = [random.randrange(cols) * CELL_SIZE, HUD_HEIGHT + random.randrange(rows) * CELL_SIZE]
        if tuple(c) not in occ:
            return c


def _vs_setup(wrap):
    midy = HUD_HEIGHT + ((HEIGHT - HUD_HEIGHT) // CELL_SIZE // 2) * CELL_SIZE
    p1 = VSnake([[CELL_SIZE * (5 - i), midy] for i in range(4)], (CELL_SIZE, 0), VS_P1, VS_P1_D)
    rx = WIDTH - CELL_SIZE * 5
    p2 = VSnake([[rx + CELL_SIZE * i, midy] for i in range(4)], (-CELL_SIZE, 0), VS_P2, VS_P2_D)
    return p1, p2, _vs_food(p1, p2)


def _vs_render(p1, p2, food, p1w, p2w, round_num, t):
    draw_background(screen, WIDTH, HEIGHT, CELL_SIZE, HUD_HEIGHT, BG, GRID, HUD_BG, INK)
    draw_food(screen, food, CELL_SIZE, sprites)
    draw_snake(screen, p1.cells, CELL_SIZE, sprites, p1.dir_name, p1.positions(t))
    draw_snake(screen, p2.cells, CELL_SIZE, sprites_p2, p2.dir_name, p2.positions(t))
    fx.draw(screen)
    s1 = font.render(f"P1  {p1w}", True, VS_P1)
    screen.blit(s1, (24, 28))
    s2 = font.render(f"{p2w}  P2", True, VS_P2)
    screen.blit(s2, (WIDTH - 24 - s2.get_width(), 28))
    draw_text_center(screen, f"ROUND {round_num}   FIRST TO {VS_WINS_TARGET}", 28, font, INK)
    if is_muted():
        draw_text_center(screen, "MUTED", HEIGHT - 36, font, (120, 124, 150))


def _versus_round(wrap, p1w, p2w, round_num):
    p1, p2, food = _vs_setup(wrap)
    acc = 0.0

    for label in ("3", "2", "1", "GO!"):
        end = pygame.time.get_ticks() + 550
        while pygame.time.get_ticks() < end:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    return "quit"
                if e.type == pygame.KEYDOWN and e.key == pygame.K_m:
                    toggle_mute()
            _vs_render(p1, p2, food, p1w, p2w, round_num, 0.0)
            draw_text_center(screen, label, HEIGHT // 2 - 30, big_font, ACCENT)
            draw_border(screen, WIDTH, HEIGHT, INK)
            pygame.display.update()
            clock.tick(60)

    turns = {pygame.K_UP: (0, -CELL_SIZE), pygame.K_DOWN: (0, CELL_SIZE),
             pygame.K_LEFT: (-CELL_SIZE, 0), pygame.K_RIGHT: (CELL_SIZE, 0)}
    wasd = {pygame.K_w: (0, -CELL_SIZE), pygame.K_s: (0, CELL_SIZE),
            pygame.K_a: (-CELL_SIZE, 0), pygame.K_d: (CELL_SIZE, 0)}

    while p1.alive and p2.alive:
        frame_ms = clock.tick(60)
        acc = min(acc + frame_ms, 250.0)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return "quit"
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_m:
                    toggle_mute()
                elif e.key in turns:
                    p1.turn(turns[e.key])
                elif e.key in wasd:
                    p2.turn(wasd[e.key])

        while acc >= VS_STEP_MS and p1.alive and p2.alive:
            acc -= VS_STEP_MS
            da, db, ea, eb = _versus_step(p1, p2, food, wrap)
            for snake, ate in ((p1, ea), (p2, eb)):
                if ate:
                    fx.burst(snake.head[0] + CELL_SIZE // 2, snake.head[1] + CELL_SIZE // 2,
                             snake.color, count=14, speed=3.0, size=5, life=34)
                    play_eat(1)
            if ea or eb:
                food = _vs_food(p1, p2)
            if da or db:
                play_sound("death")
                for snake, dead in ((p1, da), (p2, db)):
                    if dead:
                        fx.burst(snake.head[0] + CELL_SIZE // 2, snake.head[1] + CELL_SIZE // 2,
                                 (235, 70, 84), count=30, speed=4.5, size=6, life=44)

        fx.update()
        t = min(1.0, acc / VS_STEP_MS)
        _vs_render(p1, p2, food, p1w, p2w, round_num, t)
        draw_border(screen, WIDTH, HEIGHT, INK)
        pygame.display.update()

    winner = 0 if (not p1.alive and not p2.alive) else (1 if p1.alive else 2)
    banner = {0: "DRAW!", 1: "GREEN WINS THE ROUND", 2: "ORANGE WINS THE ROUND"}[winner]
    bcolor = {0: INK, 1: VS_P1, 2: VS_P2}[winner]
    end = pygame.time.get_ticks() + 1300
    while pygame.time.get_ticks() < end:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return "quit"
        fx.update()
        _vs_render(p1, p2, food, p1w, p2w, round_num, 1.0)
        draw_text_center(screen, banner, HEIGHT // 2 - 30, font, bcolor)
        draw_border(screen, WIDTH, HEIGHT, INK)
        pygame.display.update()
        clock.tick(60)
    return winner


def versus(wrap):
    """2-player couch versus: first to VS_WINS_TARGET round wins takes the match."""
    while True:                                   # rematch loop
        p1w = p2w = 0
        round_num = 0
        fx.clear()
        while max(p1w, p2w) < VS_WINS_TARGET:
            round_num += 1
            r = _versus_round(wrap, p1w, p2w, round_num)
            if r == "quit":
                return "quit"
            if r == 1:
                p1w += 1
            elif r == 2:
                p2w += 1

        champ = 1 if p1w > p2w else 2
        sel = 0
        decided = None
        while decided is None:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    return "quit"
                if e.type == pygame.KEYDOWN:
                    if e.key in (pygame.K_UP, pygame.K_DOWN):
                        sel = (sel + 1) % 2
                    elif e.key == pygame.K_m:
                        toggle_mute()
                    elif e.key == pygame.K_RETURN:
                        decided = "rematch" if sel == 0 else "menu"
            draw_background(screen, WIDTH, HEIGHT, CELL_SIZE, HUD_HEIGHT, BG, GRID, HUD_BG, INK)
            col = VS_P1 if champ == 1 else VS_P2
            name = "GREEN" if champ == 1 else "ORANGE"
            draw_text_center(screen, f"{name} WINS!", 190, big_font, col)
            draw_text_center(screen, f"{p1w}  -  {p2w}", 280, big_font, INK)
            for i, o in enumerate(["REMATCH", "MAIN MENU"]):
                c = ACCENT if i == sel else INK
                draw_text_center(screen, f"> {o} <" if i == sel else o, 400 + i * 46, font, c)
            draw_border(screen, WIDTH, HEIGHT, INK)
            pygame.display.update()
            clock.tick(60)
        if decided == "menu":
            fade_out_current()
            return "menu"
        # rematch -> outer loop starts a fresh match


def main():
    while True:
        choice = start_menu()
        if choice is None:              # window closed at the menu
            break
        wrap, difficulty, mode, players = choice
        result = versus(wrap) if players == 2 else game(wrap, difficulty, mode)
        if result == "quit":            # window closed or QUIT chosen in-game
            break
        # result == "menu" -> loop back to the start menu
    pygame.quit()


main()