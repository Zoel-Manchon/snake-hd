"""Sound effects + looping background music, with a global mute toggle.

Designed to never crash the game: if there is no audio device, or a file is
missing, the calls simply do nothing and play stays silent. The music loop,
the combo "eat" ladder, and the death sting are pre-generated WAVs.
"""

import os

import pygame

_sounds = {}
_eat_ladder = []          # eat_1 (low) .. eat_N (high), pitch rises with combo
_muted = False
_enabled = False
_music_loaded = False
_music_volume = 0.45

# If a named effect is missing, fall back to a similar one.
_FALLBACK = {"death": "gameover"}


def init_audio(base_dir="assets/sounds"):
    """Initialise the mixer and load every clip. Safe to call once at startup."""
    global _enabled, _music_loaded
    try:
        pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
    except pygame.error:
        _enabled = False
        return

    for name in ("eat", "gameover", "bonus", "powerup", "death"):
        try:
            _sounds[name] = pygame.mixer.Sound(os.path.join(base_dir, f"{name}.wav"))
        except (pygame.error, FileNotFoundError):
            pass

    i = 1
    while os.path.exists(os.path.join(base_dir, f"eat_{i}.wav")):
        try:
            _eat_ladder.append(pygame.mixer.Sound(os.path.join(base_dir, f"eat_{i}.wav")))
        except (pygame.error, FileNotFoundError):
            break
        i += 1

    try:
        pygame.mixer.music.load(os.path.join(base_dir, "music.wav"))
        _music_loaded = True
    except (pygame.error, FileNotFoundError):
        _music_loaded = False

    _enabled = True


def start_music():
    """Begin the looping background track (no-op if already playing)."""
    if _enabled and _music_loaded and not pygame.mixer.music.get_busy():
        pygame.mixer.music.set_volume(0.0 if _muted else _music_volume)
        pygame.mixer.music.play(-1)


def play_sound(name):
    if not _enabled or _muted:
        return
    sound = _sounds.get(name) or _sounds.get(_FALLBACK.get(name, ""))
    if sound is not None:
        sound.play()


def play_eat(combo):
    """Eat blip whose pitch rises with the combo multiplier."""
    if not _enabled or _muted:
        return
    if _eat_ladder:
        idx = min(max(int(combo), 1), len(_eat_ladder)) - 1
        _eat_ladder[idx].play()
    elif "eat" in _sounds:
        _sounds["eat"].play()


def toggle_mute():
    global _muted
    _muted = not _muted
    if _enabled and _music_loaded:
        pygame.mixer.music.set_volume(0.0 if _muted else _music_volume)
    return _muted


def is_muted():
    return _muted
