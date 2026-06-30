import random

from game.settings import WIDTH, HEIGHT, CELL_SIZE, HUD_HEIGHT
from game.enemies import Enemy, weighted_choice


def random_position():
    x = random.randrange(0, WIDTH, CELL_SIZE)
    y = random.randrange(HUD_HEIGHT, HEIGHT, CELL_SIZE)
    return [x, y]


def random_safe_position(snake, food, enemies):
    """A free cell, avoiding the snake, the food, and every enemy cell."""
    occupied = {tuple(e.pos) for e in enemies}
    while True:
        position = random_position()
        if position not in snake and position != food and tuple(position) not in occupied:
            return position


def spawn_enemy(enemies, snake, food, weights=None):
    """Add a new enemy of a randomly weighted kind in a free cell."""
    pos = random_safe_position(snake, food, enemies)
    enemies.append(Enemy(pos, weighted_choice(weights)))
