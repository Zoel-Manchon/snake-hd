import random

from game.settings import WIDTH, HEIGHT, CELL_SIZE, HUD_HEIGHT


def random_position():
    x = random.randrange(0, WIDTH, CELL_SIZE)
    y = random.randrange(HUD_HEIGHT, HEIGHT, CELL_SIZE)
    return [x, y]


def random_safe_position(snake, food, enemies):
    while True:
        position = random_position()

        if position not in snake and position != food and position not in enemies:
            return position


def spawn_enemy(enemies, snake, food):
    enemies.append(random_safe_position(snake, food, enemies))