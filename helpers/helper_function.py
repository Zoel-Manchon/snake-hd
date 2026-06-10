import os
import pygame

# Sprites are authored facing RIGHT. pygame.transform.rotate is counter-clockwise.
ROT = {"RIGHT": 0, "UP": 90, "LEFT": 180, "DOWN": 270}

# Single-image sprites vs. horizontal animation strips (square frames).
STATIC_SPRITES = ("head", "body", "tail", "pu_slowmo", "pu_double")
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


def draw_background(screen, width, height, cell_size, hud_height, nokia_bg, nokia_grid, hud_bg, dark_green):
    screen.fill(nokia_bg)

    pygame.draw.rect(screen, hud_bg, pygame.Rect(0, 0, width, hud_height))
    pygame.draw.line(screen, dark_green, (0, hud_height), (width, hud_height), 3)

    for x in range(0, width, cell_size):
        pygame.draw.line(screen, nokia_grid, (x, hud_height), (x, height))

    for y in range(hud_height, height, cell_size):
        pygame.draw.line(screen, nokia_grid, (0, y), (width, y))


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


def draw_game_over_panel(screen, score, high_score, font, big_font, hud_bg, dark_green):
    width, height = screen.get_width(), screen.get_height()
    panel_width, panel_height = 620, 320
    panel_x = (width - panel_width) // 2
    panel_y = (height - panel_height) // 2

    pygame.draw.rect(screen, hud_bg, pygame.Rect(panel_x, panel_y, panel_width, panel_height), border_radius=12)
    pygame.draw.rect(screen, dark_green, pygame.Rect(panel_x, panel_y, panel_width, panel_height), 5, border_radius=12)

    draw_text_center(screen, "GAME OVER", panel_y + 45, big_font, dark_green)
    draw_text_center(screen, f"FINAL SCORE: {score}", panel_y + 140, font, dark_green)
    draw_text_center(screen, f"BEST SCORE: {high_score}", panel_y + 185, font, dark_green)
    draw_text_center(screen, "SPACE - RESTART", panel_y + 250, font, dark_green)


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
    for enemy in enemies:
        screen.blit(frame, (enemy[0], enemy[1]))


def draw_snake(screen, snake, cell_size, sprites, direction):
    last = len(snake) - 1

    for index, part in enumerate(snake):
        if index == 0:
            image = pygame.transform.rotate(sprites["head"], ROT[direction])
        elif index == last and last > 0:
            tail_dir = _segment_dir(snake[index], snake[index - 1])
            image = pygame.transform.rotate(sprites["tail"], ROT[tail_dir])
        else:
            image = sprites["body"]

        screen.blit(image, (part[0], part[1]))
