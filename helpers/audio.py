"""Sound effects with a global mute toggle.

Designed to never crash the game: if there is no audio device, or a file is
missing, the calls simply do nothing and play stays silent.
"""

import os
import pygame

_sounds = {}
_muted = False
_enabled = False


def init_audio(base_dir="assets/sounds"):
    """Initialise the mixer and load the effects. Safe to call once at startup."""
    global _enabled
    try:
        pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
    except pygame.error:
        _enabled = False
        return

    for name in ("eat", "gameover", "bonus"):
        try:
            _sounds[name] = pygame.mixer.Sound(os.path.join(base_dir, f"{name}.wav"))
        except (pygame.error, FileNotFoundError):
            pass

    _enabled = True


def play_sound(name):
    if not _enabled or _muted:
        return
    sound = _sounds.get(name)
    if sound is not None:
        sound.play()


def toggle_mute():
    global _muted
    _muted = not _muted
    return _muted


def is_muted():
    return _muted
