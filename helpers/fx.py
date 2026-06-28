"""Lightweight visual FX: particle bursts and floating score text.

Pure pygame, no external dependencies. Particle colours fade toward the
background colour (and shrink) instead of using per-particle alpha surfaces,
so the system stays cheap even with many particles on screen.

Usage:
    fx = ParticleSystem(BG)
    fx.burst(x, y, (255, 210, 70), count=22, speed=7)
    fx.update(); fx.draw(screen)

    popups = FloatingTextSystem(font)
    popups.add(x, y, "+5", (255, 210, 70))
    popups.update(); popups.draw(screen)
"""

import math
import random

import pygame

GRAVITY = 0.18  # downward pull applied to every particle each tick


def _lerp(a, b, t):
    """Linear blend from a to b (t in 0..1), rounded to an int channel value."""
    return int(a + (b - a) * t)


class ParticleSystem:
    """A simple pool of short-lived particles drawn as fading circles."""

    def __init__(self, bg):
        self.bg = bg
        # Each particle is a flat list for speed:
        # [x, y, vx, vy, life, max_life, color, size]
        self.parts = []

    def clear(self):
        self.parts.clear()

    def burst(self, x, y, color, count=14, speed=6.0, size=5, life=26):
        """Spray `count` particles outward from (x, y)."""
        for _ in range(count):
            ang = random.uniform(0.0, math.tau)
            spd = random.uniform(speed * 0.25, speed)
            ml = max(6, life + random.randint(-6, 6))
            self.parts.append([
                float(x), float(y),
                math.cos(ang) * spd, math.sin(ang) * spd,
                ml, ml, color, size + random.randint(-1, 1),
            ])

    def update(self):
        for p in self.parts:
            p[0] += p[2]
            p[1] += p[3]
            p[3] += GRAVITY
            p[2] *= 0.96          # mild air drag
            p[4] -= 1
        self.parts = [p for p in self.parts if p[4] > 0]

    def draw(self, screen):
        bg = self.bg
        for p in self.parts:
            t = p[4] / p[5]                      # 1.0 fresh -> 0.0 dead
            col = (
                _lerp(bg[0], p[6][0], t),
                _lerp(bg[1], p[6][1], t),
                _lerp(bg[2], p[6][2], t),
            )
            r = max(1, int(p[7] * t))
            pygame.draw.circle(screen, col, (int(p[0]), int(p[1])), r)


class FloatingTextSystem:
    """Short '+N' style labels that rise a little and fade out."""

    def __init__(self, font):
        self.font = font
        # [x, y, text, life, max_life, color]
        self.items = []

    def clear(self):
        self.items.clear()

    def add(self, x, y, text, color=(255, 255, 255), life=34):
        self.items.append([float(x), float(y), str(text), life, life, color])

    def update(self):
        for it in self.items:
            it[1] -= 1.4          # drift upward
            it[3] -= 1
        self.items = [it for it in self.items if it[3] > 0]

    def draw(self, screen):
        for it in self.items:
            t = it[3] / it[4]
            img = self.font.render(it[2], True, it[5])
            img.set_alpha(int(255 * t))
            screen.blit(img, (int(it[0] - img.get_width() / 2), int(it[1])))
