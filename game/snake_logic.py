from game.settings import WIDTH, HEIGHT, CELL_SIZE, HUD_HEIGHT


def move_snake_head(snake, direction):
    head_x, head_y = snake[0]

    if direction == "UP":
        head_y -= CELL_SIZE
    elif direction == "DOWN":
        head_y += CELL_SIZE
    elif direction == "LEFT":
        head_x -= CELL_SIZE
    elif direction == "RIGHT":
        head_x += CELL_SIZE

    if head_x < 0:
        head_x = WIDTH - CELL_SIZE
    elif head_x >= WIDTH:
        head_x = 0

    if head_y < HUD_HEIGHT:
        head_y = HEIGHT - CELL_SIZE
    elif head_y >= HEIGHT:
        head_y = HUD_HEIGHT

    return [head_x, head_y]