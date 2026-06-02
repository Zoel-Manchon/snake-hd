def hit_self(new_head, snake):
    return new_head in snake


def hit_enemy(new_head, enemies):
    return new_head in enemies