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
    draw_combo,
    draw_enemies,
    draw_snake,
    load_sprites,
)

from helpers.storage import load_high_score, save_high_score
from helpers.audio import init_audio, play_sound, toggle_mute, is_muted

from game.settings import *
from game.snake_logic import move_snake_head
from game.collision_logic import hit_self, hit_enemy, hit_wall
from game.spawn_logic import random_position, random_safe_position, spawn_enemy

pygame.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Snake HD")

clock = pygame.time.Clock()

init_audio()

font = pygame.font.Font("assets/PressStart2P.ttf", 22)
big_font = pygame.font.Font("assets/PressStart2P.ttf", 44)

# Load the sprite set once (needs the display to exist for convert_alpha).
sprites = load_sprites(CELL_SIZE)

high_score = load_high_score()


def start_menu():
    modes = [("SCREEN WRAP", True), ("WALLS", False)]
    mode_idx = 0
    diff_idx = DIFFICULTY_ORDER.index("NORMAL")
    row = 0  # 0 = mode row, 1 = difficulty row

    while True:
        draw_background(screen, WIDTH, HEIGHT, CELL_SIZE, HUD_HEIGHT, BG, GRID, HUD_BG, INK)

        draw_text_center(screen, "SNAKE", 150, big_font, ACCENT)

        mode_color = ACCENT if row == 0 else INK
        diff_color = ACCENT if row == 1 else INK
        draw_text_center(screen, f"MODE:   < {modes[mode_idx][0]} >", 300, font, mode_color)
        draw_text_center(screen, f"DIFFICULTY:   < {DIFFICULTY_ORDER[diff_idx]} >", 350, font, diff_color)

        draw_text_center(screen, "UP/DOWN select    LEFT/RIGHT change", 460, font, INK)
        draw_text_center(screen, "ENTER start    P pauses", 505, font, INK)
        sound_label = "M: SOUND OFF" if is_muted() else "M: SOUND ON"
        draw_text_center(screen, sound_label, 550, font, INK)

        draw_border(screen, WIDTH, HEIGHT, INK)
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
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
                    return modes[mode_idx][1], DIFFICULTY_ORDER[diff_idx]


def game(wrap, difficulty):
    global high_score

    cfg = DIFFICULTIES[difficulty]
    base_speed = cfg["base_speed"]
    speed_cap = cfg["speed_cap"]
    enemy_interval = cfg["enemy_interval"]
    start_enemies = cfg["start_enemies"]

    # Outer loop lets us restart cleanly without recursion.
    while True:
        # Grid-aligned starting state (all multiples of CELL_SIZE, below the HUD).
        snake = [[CELL_SIZE * 7, HUD_HEIGHT + CELL_SIZE * 5]]
        direction = "RIGHT"
        next_direction = "RIGHT"

        food = random_position()
        bonus = None          # golden apple position, or None when inactive
        bonus_timer = 0       # ticks remaining before it vanishes
        combo = 1             # current score multiplier
        combo_timer = 0       # ticks left to keep the combo alive

        # Initial mines placed below the snake's starting row (out of its path),
        # scaled by the chosen difficulty.
        enemies = [
            [CELL_SIZE * (8 + 3 * i), HUD_HEIGHT + CELL_SIZE * 9]
            for i in range(start_enemies)
        ]

        enemy_timer = 0
        score = 0

        running = True
        game_over = False
        paused = False
        restart = False

        def draw_active_bonus():
            # Blink during the final ~15 ticks to signal it's about to vanish.
            if bonus is not None and (bonus_timer > 15 or bonus_timer % 2 == 0):
                draw_bonus(screen, bonus, CELL_SIZE, sprites)

        while running:
            draw_background(screen, WIDTH, HEIGHT, CELL_SIZE, HUD_HEIGHT, BG, GRID, HUD_BG, INK)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return

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

                    if game_over and event.key == pygame.K_SPACE:
                        restart = True
                        running = False

            if restart:
                break

            if game_over:
                draw_food(screen, food, CELL_SIZE, sprites)
                draw_active_bonus()
                draw_enemies(screen, enemies, CELL_SIZE, sprites)
                draw_snake(screen, snake, CELL_SIZE, sprites, direction)
                draw_hud(screen, score, high_score, enemies, font, big_font, INK)
                draw_game_over_panel(screen, score, high_score, font, big_font, HUD_BG, INK)
                draw_border(screen, WIDTH, HEIGHT, INK)
                pygame.display.update()
                clock.tick(15)
                continue

            if paused:
                draw_hud(screen, score, high_score, enemies, font, big_font, INK)
                draw_text_center(screen, "PAUSED", 340, big_font, ACCENT)
                draw_text_center(screen, "Press P to resume", 430, font, INK)
                draw_border(screen, WIDTH, HEIGHT, INK)
                pygame.display.update()
                clock.tick(5)
                continue

            enemy_timer += 1

            if enemy_timer >= enemy_interval:
                spawn_enemy(enemies, snake, food)
                enemy_timer = 0

            if bonus is not None:
                bonus_timer -= 1
                if bonus_timer <= 0:
                    bonus = None

            if combo_timer > 0:
                combo_timer -= 1
                if combo_timer == 0:
                    combo = 1

            direction = next_direction
            new_head = move_snake_head(snake, direction, wrap)

            # The tail vacates its cell this tick unless we eat, so moving
            # into the current tail cell is only fatal when the snake grows.
            ate_food = new_head == food
            ate_bonus = bonus is not None and new_head == bonus
            will_grow = ate_food or ate_bonus
            body_to_check = snake if will_grow else snake[:-1]

            wall_death = (not wrap) and hit_wall(new_head)

            if wall_death or hit_self(new_head, body_to_check) or hit_enemy(new_head, enemies):
                game_over = True
                play_sound("gameover")

                # Quick red impact flash over the frozen scene before the panel.
                for alpha in (200, 150, 105, 65, 30, 0):
                    draw_background(screen, WIDTH, HEIGHT, CELL_SIZE, HUD_HEIGHT, BG, GRID, HUD_BG, INK)
                    draw_food(screen, food, CELL_SIZE, sprites)
                    draw_active_bonus()
                    draw_enemies(screen, enemies, CELL_SIZE, sprites)
                    draw_snake(screen, snake, CELL_SIZE, sprites, direction)
                    draw_hud(screen, score, high_score, enemies, font, big_font, INK)
                    draw_overlay(screen, (220, 60, 60), alpha)
                    draw_border(screen, WIDTH, HEIGHT, INK)
                    pygame.display.update()
                    clock.tick(40)

                continue

            snake.insert(0, new_head)

            if will_grow:
                if ate_bonus:
                    score += BONUS_POINTS * combo
                    play_sound("bonus")
                    bonus = None
                    combo_timer = COMBO_WINDOW   # keep the chain alive
                else:
                    # Consecutive quick eats raise the multiplier.
                    combo = min(combo + 1, COMBO_MAX) if combo_timer > 0 else 1
                    score += combo
                    play_sound("eat")
                    combo_timer = COMBO_WINDOW

                if score > high_score:
                    high_score = score
                    save_high_score(high_score)

                if ate_food:
                    food = random_safe_position(snake, food, enemies)
                    # Occasionally drop a golden apple worth bonus points.
                    if bonus is None and random.random() < BONUS_CHANCE:
                        bonus = random_safe_position(snake, food, enemies)
                        bonus_timer = BONUS_LIFETIME
            else:
                snake.pop()

            draw_food(screen, food, CELL_SIZE, sprites)
            draw_active_bonus()
            draw_enemies(screen, enemies, CELL_SIZE, sprites)
            draw_snake(screen, snake, CELL_SIZE, sprites, direction)

            draw_hud(screen, score, high_score, enemies, font, big_font, INK)
            if combo > 1:
                draw_combo(screen, combo, combo_timer, COMBO_WINDOW, font, ACCENT)
            if is_muted():
                draw_text_center(screen, "MUTED", HEIGHT - 36, font, (120, 124, 150))
            draw_border(screen, WIDTH, HEIGHT, INK)

            pygame.display.update()

            # Speed scales with score but is capped per difficulty.
            speed = min(base_speed + score, speed_cap)
            clock.tick(speed)


menu_choice = start_menu()
if menu_choice is not None:
    game(*menu_choice)