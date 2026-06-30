"""The Void Warden - the boss that awakens in THE VOID biome.

A 3x3 pulsing eye fixed near the top of the board. Its pupil tracks the snake's
head and it fires aimed projectiles on a cooldown. You can't kill it by ramming
it (the body is solid); you drain it by *eating food* while you dodge - each
apple eaten deals one point of damage. At low HP it enrages: it fires faster and
throws a three-way spread.

Projectiles live in pixel space (smooth 60fps motion); collision with the snake
is resolved per grid cell, the same way the rest of the game works.
"""

import math

from game.settings import (
    CELL_SIZE, WIDTH, HEIGHT, HUD_HEIGHT,
    BOSS_MAX_HP, BOSS_FIRE_INTERVAL, BOSS_PROJ_SPEED, BOSS_ENRAGE_HP,
    BOSS_BURST_COUNT, BOSS_BURST_INTERVAL, BOSS_BURST_CHARGE, BOSS_BURST_SPEED,
)


class Boss:
    def __init__(self, width=WIDTH, height=HEIGHT):
        cols = width // CELL_SIZE
        self.cx = (cols // 2) * CELL_SIZE        # top-left x of the centre cell
        self.cy = HUD_HEIGHT + 2 * CELL_SIZE     # top-left y of the centre cell
        self.width = width
        self.height = height
        self.max_hp = BOSS_MAX_HP
        self.hp = BOSS_MAX_HP
        self.projectiles = []        # each: [px, py, vx, vy] in pixel coords
        self.fire_cd = BOSS_FIRE_INTERVAL
        self.burst_cd = BOSS_BURST_INTERVAL   # steps until the next radial burst
        self.charge = 0.0            # seconds left on the burst telegraph (0 = idle)
        self.phase = 0.0             # advances each frame -> pulsing visuals
        self.flash = 0.0             # seconds of white flinch after a hit
        self.look = (0.0, 1.0)       # pupil aim direction (unit vector)

    @property
    def enraged(self):
        return self.hp <= BOSS_ENRAGE_HP

    @property
    def charge_frac(self):
        """1.0 at the start of a charge -> 0.0 at release; 0 when idle."""
        return (self.charge / BOSS_BURST_CHARGE) if (BOSS_BURST_CHARGE and self.charge > 0) else 0.0

    def center_px(self):
        return (self.cx + CELL_SIZE // 2, self.cy + CELL_SIZE // 2)

    def solid_cells(self):
        """The 3x3 block of grid cells the body occupies (lethal to ram)."""
        return {(self.cx + i * CELL_SIZE, self.cy + j * CELL_SIZE)
                for i in (-1, 0, 1) for j in (-1, 0, 1)}

    def projectile_cells(self):
        """Grid cells currently covered by a projectile (lethal to touch)."""
        cells = set()
        for px, py, _, _ in self.projectiles:
            gx = int(px // CELL_SIZE) * CELL_SIZE
            gy = HUD_HEIGHT + int((py - HUD_HEIGHT) // CELL_SIZE) * CELL_SIZE
            cells.add((gx, gy))
        return cells

    def _aim(self, target):
        """Unit vector from the eye toward the centre of the head cell."""
        cxp, cyp = self.center_px()
        dx = (target[0] + CELL_SIZE / 2) - cxp
        dy = (target[1] + CELL_SIZE / 2) - cyp
        d = math.hypot(dx, dy) or 1.0
        return dx / d, dy / d

    def on_step(self, target):
        """Called once per snake step: refresh aim and fire on cooldown."""
        self.look = self._aim(target)
        self.fire_cd -= 1
        if self.fire_cd <= 0:
            self._fire(target)
            self.fire_cd = max(2, BOSS_FIRE_INTERVAL // 2) if self.enraged else BOSS_FIRE_INTERVAL
        # Enraged: periodically wind up a full radial burst (released in advance()).
        if self.enraged:
            self.burst_cd -= 1
            if self.burst_cd <= 0 and self.charge <= 0:
                self.charge = BOSS_BURST_CHARGE
                self.burst_cd = BOSS_BURST_INTERVAL

    def _fire(self, target):
        cxp, cyp = self.center_px()
        ux, uy = self._aim(target)
        spread = (-0.32, 0.0, 0.32) if self.enraged else (0.0,)
        for s in spread:
            cos_s, sin_s = math.cos(s), math.sin(s)
            vx = (ux * cos_s - uy * sin_s) * BOSS_PROJ_SPEED
            vy = (ux * sin_s + uy * cos_s) * BOSS_PROJ_SPEED
            self.projectiles.append([float(cxp), float(cyp), vx, vy])

    def _radial_burst(self):
        """Fire a full ring of evenly-spaced projectiles from the eye."""
        cxp, cyp = self.center_px()
        n = BOSS_BURST_COUNT
        off = self.phase            # rotate each burst a little so they differ
        for k in range(n):
            ang = off + 2 * math.pi * k / n
            self.projectiles.append([float(cxp), float(cyp),
                                     math.cos(ang) * BOSS_BURST_SPEED,
                                     math.sin(ang) * BOSS_BURST_SPEED])

    def advance(self, dt_ms):
        """Called every frame: move projectiles, drop off-board, advance pulse,
        and release a charged radial burst when the telegraph completes.
        Returns True on the frame a burst is released (so the caller can react)."""
        released = False
        self.phase += dt_ms / 1000.0
        if self.flash > 0:
            self.flash = max(0.0, self.flash - dt_ms / 1000.0)
        if self.charge > 0:
            self.charge -= dt_ms / 1000.0
            if self.charge <= 0:
                self.charge = 0.0
                self._radial_burst()
                released = True
        alive = []
        for p in self.projectiles:
            p[0] += p[2]
            p[1] += p[3]
            if (-CELL_SIZE <= p[0] <= self.width + CELL_SIZE and
                    HUD_HEIGHT - CELL_SIZE <= p[1] <= self.height + CELL_SIZE):
                alive.append(p)
        self.projectiles = alive
        return released

    def hit(self):
        """Take one point of damage. Returns True when defeated."""
        self.hp -= 1
        self.flash = 0.18
        return self.hp <= 0
