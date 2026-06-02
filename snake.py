import pygame

from helpers.helper_function import (
    draw_text_center,
    draw_background,
    draw_border,
    draw_hud,
    draw_game_over_panel,
    draw_food,
    draw_enemies,
    draw_snake,
    load_sprites,
)

from helpers.storage import load_high_score, save_high_score

from game.settings import *
from game.snake_logic import move_snake_head
from game.collision_logic import hit_self, hit_enemy
from game.spawn_logic import random_position, random_safe_position, spawn_enemy

pygame.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Snake HD")

clock = pygame.time.Clock()

font = pygame.font.Font("assets/PressStart2P.ttf", 22)
big_font = pygame.font.Font("assets/PressStart2P.ttf", 44)

# Load the sprite set once (needs the display to exist for convert_alpha).
sprites = load_sprites(CELL_SIZE)

high_score = load_high_score()


def start_menu():
    while True:
        draw_background(screen, WIDTH, HEIGHT, CELL_SIZE, HUD_HEIGHT, BG, GRID, HUD_BG, INK)

        draw_text_center(screen, "SNAKE", 240, big_font, ACCENT)
        draw_text_center(screen, "Press ENTER to start", 380, font, INK)
        draw_text_center(screen, "Arrow keys to move", 430, font, INK)
        draw_text_center(screen, "P to pause", 470, font, INK)

        draw_border(screen, WIDTH, HEIGHT, INK)
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return True


def game():
    global high_score

    # Outer loop lets us restart cleanly without recursion.
    while True:
        # Grid-aligned starting state (all multiples of CELL_SIZE, below the HUD).
        snake = [[CELL_SIZE * 7, HUD_HEIGHT + CELL_SIZE * 5]]
        direction = "RIGHT"
        next_direction = "RIGHT"

        food = random_position()

        enemies = [
            [CELL_SIZE * 15, HUD_HEIGHT + CELL_SIZE * 6],
            [CELL_SIZE * 18, HUD_HEIGHT + CELL_SIZE * 6],
            [CELL_SIZE * 21, HUD_HEIGHT + CELL_SIZE * 6],
        ]

        enemy_timer = 0
        score = 0

        running = True
        game_over = False
        paused = False
        restart = False

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

                    if game_over and event.key == pygame.K_SPACE:
                        restart = True
                        running = False

            if restart:
                break

            if game_over:
                draw_food(screen, food, CELL_SIZE, sprites)
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

            if enemy_timer >= 80:
                spawn_enemy(enemies, snake, food)
                enemy_timer = 0

            direction = next_direction
            new_head = move_snake_head(snake, direction)

            # The tail vacates its cell this tick unless we eat, so moving
            # into the current tail cell is only fatal when the snake grows.
            will_grow = new_head == food
            body_to_check = snake if will_grow else snake[:-1]

            if hit_self(new_head, body_to_check) or hit_enemy(new_head, enemies):
                game_over = True

            snake.insert(0, new_head)

            if will_grow:
                score += 1

                if score > high_score:
                    high_score = score
                    save_high_score(high_score)

                food = random_safe_position(snake, food, enemies)
            else:
                snake.pop()

            draw_food(screen, food, CELL_SIZE, sprites)
            draw_enemies(screen, enemies, CELL_SIZE, sprites)
            draw_snake(screen, snake, CELL_SIZE, sprites, direction)

            draw_hud(screen, score, high_score, enemies, font, big_font, INK)
            draw_border(screen, WIDTH, HEIGHT, INK)

            pygame.display.update()

            # Speed scales with score but is capped so it stays playable.
            speed = min(10 + score, 22)
            clock.tick(speed)


if start_menu():
    game()