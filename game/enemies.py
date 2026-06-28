"""Enemy types and their behaviour.

Three kinds, all sharing one grid-aligned model so the rest of the game can
treat them uniformly (each exposes `.pos` and `.is_solid()`):

* mine     - the classic: never moves, always deadly.
* drifter  - slides one cell on a slow cadence, bouncing off edges. Always
             deadly, but predictable, so it's a moving hazard you can read.
* blinker  - stays put but phases between solid (deadly) and faded (safe to
             pass through). Adds timing-based navigation.
"""

import random

from game.settings import (
    WIDTH, HEIGHT, CELL_SIZE, HUD_HEIGHT,
    ENEMY_WEIGHTS, DRIFTER_INTERVAL, BLINKER_PERIOD, BLINKER_SOLID,
)

# Orthogonal one-cell steps used by drifters.
_STEPS = [(CELL_SIZE, 0), (-CELL_SIZE, 0), (0, CELL_SIZE), (0, -CELL_SIZE)]


def weighted_choice():
    """Pick an enemy kind using the spawn weights from settings."""
    kinds = list(ENEMY_WEIGHTS.keys())
    weights = list(ENEMY_WEIGHTS.values())
    return random.choices(kinds, weights=weights, k=1)[0]


class Enemy:
    def __init__(self, pos, kind):
        self.pos = list(pos)
        self.kind = kind
        self.timer = 0
        if kind == "drifter":
            self.vx, self.vy = random.choice(_STEPS)
        elif kind == "blinker":
            self.phase = random.randrange(BLINKER_PERIOD)   # desync blinkers

    def is_solid(self):
        """True when the enemy is currently lethal to touch."""
        if self.kind == "blinker":
            return self.phase < BLINKER_SOLID
        return True   # mines and drifters are always solid

    def update(self, snake, food, occupied):
        """Advance this enemy one tick.

        `occupied` is the set of all enemy cells (as tuples) this tick, used so
        a drifter won't slide on top of another enemy.
        """
        if self.kind == "drifter":
            self.timer += 1
            if self.timer < DRIFTER_INTERVAL:
                return
            self.timer = 0

            nx = self.pos[0] + self.vx
            ny = self.pos[1] + self.vy
            # Bounce off the play-area edges (HUD counts as the top wall).
            if nx < 0 or nx >= WIDTH:
                self.vx = -self.vx
                nx = self.pos[0] + self.vx
            if ny < HUD_HEIGHT or ny >= HEIGHT:
                self.vy = -self.vy
                ny = self.pos[1] + self.vy

            cand = [nx, ny]
            blocked = (cand == list(food) or cand in snake
                       or tuple(cand) in occupied)
            if blocked:
                # Path is taken: pick a fresh heading and wait for next move.
                self.vx, self.vy = random.choice(_STEPS)
            else:
                self.pos = cand

        elif self.kind == "blinker":
            self.phase = (self.phase + 1) % BLINKER_PERIOD
        # mine: nothing to do.
