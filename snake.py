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
)

from helpers.storage import load_high_score, save_high_score
from helpers.audio import init_audio, play_sound, play_eat, start_music, toggle_mute, is_muted
from helpers.fx import ParticleSystem, FloatingTextSystem
from helpers.ledger import record_score, top_scores

from game.settings import *
from game.snake_logic import move_snake_head
from game.collision_logic import hit_self, hit_enemy, hit_wall
from game.spawn_logic import random_position, random_safe_position, spawn_enemy
from game.enemies import Enemy

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


def start_menu():
    modes = [("SCREEN WRAP", True), ("WALLS", False)]
    mode_idx = 0
    diff_idx = DIFFICULTY_ORDER.index("NORMAL")
    row = 0  # 0 = mode row, 1 = difficulty row

    demo = DemoSnake()
    phase = 0.0
    faded_in = False

    while True:
        dt = clock.tick(60)
        phase += dt / 1000.0
        demo.update(dt)

        draw_background(screen, WIDTH, HEIGHT, CELL_SIZE, HUD_HEIGHT, BG, GRID, HUD_BG, INK)

        # The menu is alive: a self-driving snake chases a roaming apple.
        draw_food(screen, demo.target, CELL_SIZE, sprites)
        draw_snake(screen, demo.cells, CELL_SIZE, sprites, demo.dir_name, demo.positions())

        # Dim panel so the text stays readable over the moving snake.
        panel = pygame.Surface((780, 340), pygame.SRCALPHA)
        panel.fill((10, 12, 22, 185))
        pygame.draw.rect(panel, (*ACCENT, 70), panel.get_rect(), 2, border_radius=14)
        screen.blit(panel, ((WIDTH - 780) // 2, 248))

        # Animated logo: a travelling wave + a gentle green shimmer.
        title_color = lerp_color(ACCENT, (170, 245, 180), 0.5 + 0.5 * math.sin(phase * 2.2))
        draw_wave_text(screen, "SNAKE", WIDTH // 2, 140, big_font, title_color, phase * 3.5, amp=12)

        mode_color = ACCENT if row == 0 else INK
        diff_color = ACCENT if row == 1 else INK
        draw_text_center(screen, f"MODE:   < {modes[mode_idx][0]} >", 300, font, mode_color)
        draw_text_center(screen, f"DIFFICULTY:   < {DIFFICULTY_ORDER[diff_idx]} >", 350, font, diff_color)

        draw_text_center(screen, "UP/DOWN select    LEFT/RIGHT change", 460, font, INK)
        draw_text_center(screen, "ENTER start    P pauses", 505, font, INK)
        sound_label = "M: SOUND OFF" if is_muted() else "M: SOUND ON"
        draw_text_center(screen, sound_label, 550, font, INK)

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
                if event.key in (pygame.K_UP, pygame.K_DOWN):
                    row = (row + 1) % 2
                elif event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                    step = 1 if event.key == pygame.K_RIGHT else -1
                    if row == 0:
                        mode_idx = (mode_idx + step) % len(modes)
                    else:
                        diff_idx = (diff_idx + step) % len(DIFFICULTY_ORDER)
                elif event.key == pygame.K_m:
                    toggle_mute()
                elif event.key == pygame.K_RETURN:
                    fade_out_current()
                    return modes[mode_idx][1], DIFFICULTY_ORDER[diff_idx]


def game(wrap, difficulty):
    global high_score

    cfg = DIFFICULTIES[difficulty]
    base_speed = cfg["base_speed"]
    speed_cap = cfg["speed_cap"]
    enemy_interval = cfg["enemy_interval"]
    start_enemies = cfg["start_enemies"]

    did_fade_in = False   # fade the first frame in from black once per entry

    # Outer loop lets us restart cleanly without recursion.
    while True:
        # Grid-aligned starting state (all multiples of CELL_SIZE, below the HUD).
        snake = [[CELL_SIZE * 7, HUD_HEIGHT + CELL_SIZE * 5]]
        prev_snake = [list(seg) for seg in snake]   # pre-step positions, for smooth rendering
        direction = "RIGHT"
        next_direction = "RIGHT"

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
                    if enemy_timer >= enemy_interval:
                        spawn_enemy(enemies, snake, food)
                        enemy_timer = 0

                    # Drifters slide, blinkers phase on/off.
                    occupied = {tuple(e.pos) for e in enemies}
                    for e in enemies:
                        e.update(snake, food, occupied)

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

                    if wall_death or (not ghost and (hit_self(new_head, body_to_check)
                                                     or hit_enemy(new_head, enemies))):
                        game_over = True
                        fever = False
                        accumulator = 0.0
                        play_sound("death")
                        record_score(score, PLAYER_NAME)
                        leaderboard = top_scores(5)

                        # Burst of debris from the head where it died.
                        hx = snake[0][0] + CELL_SIZE // 2
                        hy = snake[0][1] + CELL_SIZE // 2
                        fx.burst(hx, hy, (235, 70, 84), count=34, speed=4.5, size=6, life=46)

                        # Quick red flash + screen shake over the frozen scene.
                        for alpha in (200, 150, 105, 65, 30, 0):
                            buf = pygame.Surface((WIDTH, HEIGHT))
                            draw_background(buf, WIDTH, HEIGHT, CELL_SIZE, HUD_HEIGHT, BG, GRID, HUD_BG, INK)
                            draw_food(buf, food, CELL_SIZE, sprites)
                            if bonus is not None:
                                draw_bonus(buf, bonus, CELL_SIZE, sprites)
                            draw_enemies(buf, enemies, CELL_SIZE, sprites)
                            draw_snake(buf, snake, CELL_SIZE, sprites, direction)
                            fx.update()
                            fx.draw(buf)
                            draw_hud(buf, score, high_score, enemies, font, big_font, INK)
                            draw_overlay(buf, (220, 60, 60), alpha)
                            draw_border(buf, WIDTH, HEIGHT, INK)
                            mag = int(14 * (alpha / 200))
                            dx = random.randint(-mag, mag) if mag else 0
                            dy = random.randint(-mag, mag) if mag else 0
                            screen.fill(BG)
                            screen.blit(buf, (dx, dy))
                            pygame.display.update()
                            clock.tick(40)
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
                            if bonus is None and random.random() < BONUS_CHANCE:
                                bonus = random_safe_position(snake, food, enemies)
                                bonus_timer = BONUS_LIFETIME
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

            pulse = 0.0
            fever_color = FEVER_COLORS[0]
            if fever:
                pulse = 0.5 + 0.5 * math.sin(fever_phase * 9.0)      # fast strobe 0..1
                sweep = 0.5 + 0.5 * math.sin(fever_phase * 2.5)      # slow magenta<->cyan
                fever_color = lerp_color(FEVER_COLORS[0], FEVER_COLORS[1], sweep)

            # ---- render (every frame) ----
            draw_background(screen, WIDTH, HEIGHT, CELL_SIZE, HUD_HEIGHT, BG, GRID, HUD_BG, INK)
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
            if fever:
                draw_fever_vignette(screen, WIDTH, HEIGHT, HUD_HEIGHT, fever_color, 120 + 90 * pulse)
            if not game_over and not paused:
                popups.draw(screen)

            draw_hud(screen, score, high_score, enemies, font, big_font, INK)

            if game_over:
                draw_game_over_panel(screen, score, high_score, font, big_font, HUD_BG, INK, leaderboard, ACCENT, go_sel)
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
                if is_muted():
                    draw_text_center(screen, "MUTED", HEIGHT - 36, font, (120, 124, 150))

            if fever_flash > 0:
                draw_flash(screen, 200 * fever_flash / 8)

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

def main():
    while True:
        choice = start_menu()
        if choice is None:          # window closed at the menu
            break
        result = game(*choice)
        if result == "quit":        # window closed or QUIT chosen in-game
            break
        # result == "menu" -> loop back to the start menu
    pygame.quit()


main()