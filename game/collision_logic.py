from game.settings import WIDTH, HEIGHT, HUD_HEIGHT


def hit_self(new_head, snake):
    return new_head in snake


def hit_enemy(new_head, enemies):
    return new_head in enemies


def hit_wall(new_head):
    """True when the head has left the play area (used in walls mode)."""
    x, y = new_head
    return x < 0 or x >= WIDTH or y < HUD_HEIGHT or y >= HEIGHT
