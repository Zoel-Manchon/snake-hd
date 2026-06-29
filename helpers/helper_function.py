import math
import os
import pygame

# Sprites are authored facing RIGHT. pygame.transform.rotate is counter-clockwise.
ROT = {"RIGHT": 0, "UP": 90, "LEFT": 180, "DOWN": 270}

# Single-image sprites vs. horizontal animation strips (square frames).
STATIC_SPRITES = ("head", "body", "tail", "pu_slowmo", "pu_double", "pu_magnet", "pu_ghost")
ANIMATED_SPRITES = ("food", "bonus", "mine")
ANIM_MS = 130   # milliseconds each animation frame is shown


def load_sprites(cell_size, base_dir="assets/sprites"):
    """Load sprites, pre-scaled to the cell size.

    Static sprites map to a single Surface; animated ones map to a list of
    frame Surfaces sliced from a horizontal strip.
    """
    sprites = {}

    for name in STATIC_SPRITES:
        image = pygame.image.load(os.path.join(base_dir, f"{name}.png")).convert_alpha()
        sprites[name] = pygame.transform.scale(image, (cell_size, cell_size))

    for name in ANIMATED_SPRITES:
        sheet = pygame.image.load(os.path.join(base_dir, f"{name}.png")).convert_alpha()
        size = sheet.get_height()                      # square frames
        count = max(1, sheet.get_width() // size)
        frames = []
        for i in range(count):
            frame = sheet.subsurface(pygame.Rect(i * size, 0, size, size))
            frames.append(pygame.transform.scale(frame, (cell_size, cell_size)))
        sprites[name] = frames

    return sprites


def current_frame(frames):
    """Pick the active animation frame from a list, based on real time."""
    return frames[(pygame.time.get_ticks() // ANIM_MS) % len(frames)]


def draw_text(screen, text, x, y, font, big_font, color, use_big_font=False):
    selected_font = big_font if use_big_font else font
    image = selected_font.render(text, True, color)
    screen.blit(image, (x, y))


_BG_CACHE = None
_BG_KEY = None


def draw_background(screen, width, height, cell_size, hud_height, nokia_bg, nokia_grid, hud_bg, dark_green):
    # The background is static, so render it once and just blit the cached
    # surface each frame. Redrawing ~50 grid lines every frame was the main
    # thing keeping the loop from holding a steady 60 FPS.
    global _BG_CACHE, _BG_KEY
    key = (width, height, cell_size, hud_height, nokia_bg, nokia_grid, hud_bg, dark_green)
    if _BG_CACHE is None or _BG_KEY != key:
        surf = pygame.Surface((width, height))
        surf.fill(nokia_bg)
        pygame.draw.rect(surf, hud_bg, pygame.Rect(0, 0, width, hud_height))
        pygame.draw.line(surf, dark_green, (0, hud_height), (width, hud_height), 3)
        for x in range(0, width, cell_size):
            pygame.draw.line(surf, nokia_grid, (x, hud_height), (x, height))
        for y in range(hud_height, height, cell_size):
            pygame.draw.line(surf, nokia_grid, (0, y), (width, y))
        _BG_CACHE = surf
        _BG_KEY = key
    screen.blit(_BG_CACHE, (0, 0))


def draw_text_center(screen, text, y, font, color):
    """Render text horizontally centered on the screen at vertical pos y."""
    image = font.render(text, True, color)
    x = (screen.get_width() - image.get_width()) // 2
    screen.blit(image, (x, y))


def draw_border(screen, width, height, dark_green):
    pygame.draw.rect(screen, dark_green, pygame.Rect(0, 0, width, height), 6)


def draw_overlay(screen, color, alpha):
    """Blit a translucent full-screen color wash (used for the death flash)."""
    overlay = pygame.Surface(screen.get_size())
    overlay.fill(color)
    overlay.set_alpha(alpha)
    screen.blit(overlay, (0, 0))


def draw_hud(screen, score, high_score, enemies, font, big_font, dark_green):
    width = screen.get_width()
    score_img = font.render(f"SCORE {score}", True, dark_green)
    danger_img = font.render(f"DANGER {len(enemies)}", True, dark_green)
    y = 28
    screen.blit(score_img, (30, y))
    draw_text_center(screen, f"BEST {high_score}", y, font, dark_green)
    screen.blit(danger_img, (width - danger_img.get_width() - 30, y))


def draw_game_over_panel(screen, score, high_score, font, big_font, hud_bg,
                         dark_green, leaderboard=None, accent=None, selected=0):
    accent = accent or dark_green
    width, height = screen.get_width(), screen.get_height()
    panel_width, panel_height = 640, 520
    panel_x = (width - panel_width) // 2
    panel_y = (height - panel_height) // 2

    pygame.draw.rect(screen, hud_bg, pygame.Rect(panel_x, panel_y, panel_width, panel_height), border_radius=12)
    pygame.draw.rect(screen, accent, pygame.Rect(panel_x, panel_y, panel_width, panel_height), 5, border_radius=12)

    draw_text_center(screen, "GAME OVER", panel_y + 34, big_font, accent)
    draw_text_center(screen, f"SCORE {score}", panel_y + 104, font, dark_green)
    draw_text_center(screen, f"BEST {high_score}", panel_y + 140, font, dark_green)

    pygame.draw.line(screen, accent, (panel_x + 40, panel_y + 178),
                     (panel_x + panel_width - 40, panel_y + 178), 2)
    draw_text_center(screen, "LEADERBOARD", panel_y + 190, font, accent)

    rows = (leaderboard or [])[:5]
    if rows:
        for i, (name, sc) in enumerate(rows):
            color = accent if sc == score else dark_green   # highlight this run
            img = font.render(f"{i + 1}. {sc:>5}  {name}", True, color)
            screen.blit(img, (panel_x + 78, panel_y + 226 + i * 30))
    else:
        draw_text_center(screen, "- no scores yet -", panel_y + 240, font, dark_green)

    pygame.draw.line(screen, accent, (panel_x + 40, panel_y + 388),
                     (panel_x + panel_width - 40, panel_y + 388), 2)

    options = ["RESTART", "MAIN MENU", "QUIT"]
    for i, label in enumerate(options):
        if i == selected:
            draw_text_center(screen, f"> {label} <", panel_y + 410 + i * 34, font, accent)
        else:
            draw_text_center(screen, label, panel_y + 410 + i * 34, font, dark_green)


def draw_fps(screen, clock, font):
    """Small dim frames-per-second readout in the bottom-left corner."""
    img = font.render(f"FPS {int(clock.get_fps())}", True, (120, 124, 150))
    screen.blit(img, (12, screen.get_height() - img.get_height() - 12))


# ---------------------------------------------------------------------------
# Sprite-based drawing
# ---------------------------------------------------------------------------

def _segment_dir(from_cell, to_cell):
    """Direction pointing from one grid cell toward an adjacent one."""
    dx = to_cell[0] - from_cell[0]
    dy = to_cell[1] - from_cell[1]
    if dx > 0:
        return "RIGHT"
    if dx < 0:
        return "LEFT"
    if dy > 0:
        return "DOWN"
    return "UP"


def draw_food(screen, food, cell_size, sprites):
    screen.blit(current_frame(sprites["food"]), (food[0], food[1]))


def draw_bonus(screen, bonus, cell_size, sprites):
    screen.blit(current_frame(sprites["bonus"]), (bonus[0], bonus[1]))


def draw_powerup(screen, powerup, kind, cell_size, sprites):
    screen.blit(sprites["pu_" + kind], (powerup[0], powerup[1]))


def draw_effect(screen, label, ticks, max_ticks, font, color, row=0):
    """Active-effect indicator (icon label + depleting bar) on the left."""
    img = font.render(label, True, color)
    x, y = 30, 92 + row * 38
    screen.blit(img, (x, y))
    bar_w = 160
    frac = max(0.0, min(1.0, ticks / max_ticks))
    pygame.draw.rect(screen, color, pygame.Rect(x, y + img.get_height() + 6, int(bar_w * frac), 6))


def draw_combo(screen, combo, combo_timer, window, font, color):
    """Show 'COMBO xN' with a depleting timer bar, just below the HUD."""
    label = font.render(f"COMBO x{combo}", True, color)
    x = (screen.get_width() - label.get_width()) // 2
    y = 90
    screen.blit(label, (x, y))

    bar_w = 220
    frac = max(0.0, min(1.0, combo_timer / window))
    bx = (screen.get_width() - bar_w) // 2
    by = y + label.get_height() + 6
    pygame.draw.rect(screen, color, pygame.Rect(bx, by, int(bar_w * frac), 6))


def draw_enemies(screen, enemies, cell_size, sprites):
    frame = current_frame(sprites["mine"])
    r = cell_size // 2 - 3
    for enemy in enemies:
        x, y = enemy.pos
        cx, cy = x + cell_size // 2, y + cell_size // 2

        if enemy.kind == "blinker" and not enemy.is_solid():
            # Faded + hollow ring: currently safe to pass through.
            ghost = frame.copy()
            ghost.set_alpha(70)
            screen.blit(ghost, (x, y))
            pygame.draw.circle(screen, (90, 150, 175), (cx, cy), r, 2)
            continue

        screen.blit(frame, (x, y))
        if enemy.kind == "drifter":
            pygame.draw.circle(screen, (90, 200, 220), (cx, cy), r, 2)   # moving
        elif enemy.kind == "blinker":
            pygame.draw.circle(screen, (235, 120, 90), (cx, cy), r, 2)   # solid = deadly now
        elif enemy.kind == "chaser":
            pygame.draw.circle(screen, (235, 70, 70), (cx, cy), r, 2)        # hunter
            pygame.draw.circle(screen, (235, 70, 70), (cx, cy), max(2, r - 5), 1)


_DIR_VEC = {"RIGHT": (1, 0), "LEFT": (-1, 0), "UP": (0, -1), "DOWN": (0, 1)}


def _draw_tongue(screen, head_cell, cell_size, direction):
    """Flick a little forked tongue out of the head on a slow cycle."""
    phase = pygame.time.get_ticks() % 1400
    if phase > 220:                      # tongue only shows ~220ms of each 1.4s
        return

    dx, dy = _DIR_VEC[direction]
    cx = head_cell[0] + cell_size // 2
    cy = head_cell[1] + cell_size // 2
    sx = cx + dx * (cell_size // 2 - 2)  # start at the front edge of the head
    sy = cy + dy * (cell_size // 2 - 2)
    reach = int(cell_size * 0.55)
    ex = cx + dx * reach                 # tip of the tongue
    ey = cy + dy * reach

    fork = max(3, cell_size // 8)
    px, py = -dy, dx                     # perpendicular, for the fork
    red = (224, 64, 84)
    pygame.draw.line(screen, red, (sx, sy), (ex, ey), 3)
    pygame.draw.line(screen, red, (ex, ey),
                     (ex + dx * fork - px * fork, ey + dy * fork - py * fork), 3)
    pygame.draw.line(screen, red, (ex, ey),
                     (ex + dx * fork + px * fork, ey + dy * fork + py * fork), 3)


def draw_snake(screen, snake, cell_size, sprites, direction, positions=None):
    # `positions` are smooth (interpolated) render coords parallel to `snake`.
    # Sprite choice and rotation still come from the logical grid cells.
    pos = positions if positions is not None else snake
    last = len(snake) - 1

    for index, part in enumerate(snake):
        if index == 0:
            image = pygame.transform.rotate(sprites["head"], ROT[direction])
        elif index == last and last > 0:
            tail_dir = _segment_dir(snake[index], snake[index - 1])
            image = pygame.transform.rotate(sprites["tail"], ROT[tail_dir])
        else:
            image = sprites["body"]

        screen.blit(image, (int(pos[index][0]), int(pos[index][1])))

    _draw_tongue(screen, pos[0], cell_size, direction)


# ---------------------------------------------------------------------------
# Fever mode visuals.  All effects reuse cached scratch surfaces so they cost
# almost nothing per frame, and pulse via values computed in the game loop.
# ---------------------------------------------------------------------------
_SCRATCH = {}
_SCRATCH_ALPHA = {}


def _scratch(size):
    s = _SCRATCH.get(size)
    if s is None:
        s = pygame.Surface(size)
        _SCRATCH[size] = s
    return s


def _scratch_alpha(size):
    s = _SCRATCH_ALPHA.get(size)
    if s is None:
        s = pygame.Surface(size, pygame.SRCALPHA)
        _SCRATCH_ALPHA[size] = s
    s.fill((0, 0, 0, 0))
    return s


def lerp_color(a, b, t):
    t = max(0.0, min(1.0, t))
    return (int(a[0] + (b[0] - a[0]) * t),
            int(a[1] + (b[1] - a[1]) * t),
            int(a[2] + (b[2] - a[2]) * t))


def draw_fever_tint(screen, width, height, hud_height, color, alpha):
    """Faint electric wash over the playfield (under the snake)."""
    surf = _scratch((width, height - hud_height))
    surf.fill(color)
    surf.set_alpha(int(alpha))
    screen.blit(surf, (0, hud_height))


def draw_fever_glow(screen, positions, cell, color, intensity):
    """Additive halo behind each snake segment; `intensity` is 0..1."""
    size = cell + 10
    g = _scratch((size, size))
    g.fill((int(color[0] * intensity), int(color[1] * intensity), int(color[2] * intensity)))
    off = (size - cell) // 2
    for p in positions:
        screen.blit(g, (int(p[0]) - off, int(p[1]) - off), special_flags=pygame.BLEND_RGB_ADD)


def draw_fever_vignette(screen, width, height, hud_height, color, alpha):
    """Pulsing electric border framing the playfield."""
    surf = _scratch_alpha((width, height - hud_height))
    rect = surf.get_rect()
    alpha = int(alpha)
    for i, a in enumerate((alpha, alpha * 2 // 3, alpha // 3)):
        pygame.draw.rect(surf, (*color, a), rect.inflate(-i * 16, -i * 16), 6, border_radius=6)
    screen.blit(surf, (0, hud_height))


def draw_fever_banner(screen, mult, color, big_font, alpha, hud_height):
    img = big_font.render(f"FEVER  x{mult}", True, color)
    img.set_alpha(int(alpha))
    x = (screen.get_width() - img.get_width()) // 2
    screen.blit(img, (x, hud_height + 14))


def draw_fever_meter(screen, ratio, color, width, hud_height):
    ratio = max(0.0, min(1.0, ratio))
    x, y, full = 120, hud_height + 70, width - 240
    pygame.draw.rect(screen, (38, 40, 60), (x, y, full, 10), border_radius=5)
    if ratio > 0:
        pygame.draw.rect(screen, color, (x, y, int(full * ratio), 10), border_radius=5)


def draw_flash(screen, alpha):
    s = _scratch(screen.get_size())
    s.fill((255, 255, 255))
    s.set_alpha(int(alpha))
    screen.blit(s, (0, 0))


def draw_wave_text(screen, text, center_x, base_y, font, color, phase, amp=10, spacing=6):
    """Render text glyph-by-glyph with a travelling vertical sine wave."""
    widths = [font.size(ch)[0] for ch in text]
    total = sum(widths) + spacing * (len(text) - 1)
    x = center_x - total // 2
    for i, ch in enumerate(text):
        img = font.render(ch, True, color)
        y = base_y + int(amp * math.sin(phase + i * 0.7))
        screen.blit(img, (x, y))
        x += widths[i] + spacing
