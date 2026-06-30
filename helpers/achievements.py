"""Persistent achievements for Snake HD.

Unlocked achievements are stored as a small JSON list so progress carries across
sessions. Every file operation is wrapped so a missing/unwritable file never
breaks the game.
"""

import json
import os

_PATH = "achievements.json"

# (id, display name, description) - order is the display order.
ACHIEVEMENTS = [
    ("first_blood",  "FIRST BLOOD",    "Score your first 10 points"),
    ("combo_master", "COMBO MASTER",   "Reach a x5 combo"),
    ("on_fire",      "ON FIRE",        "Ignite Fever Mode"),
    ("phase_shift",  "PHASE SHIFT",    "Grab the Ghost power-up"),
    ("century",      "CENTURY",        "Score 100 in a single run"),
    ("survivor",     "SURVIVOR",       "Score 250 in a single run"),
    ("globetrotter", "GLOBETROTTER",   "Reach THE VOID biome"),
    ("beat_clock",   "BEAT THE CLOCK", "Score 50+ in Time Attack"),
    ("zen_master",   "ZEN MASTER",     "Grow to length 50 in Zen"),
]
NAME = {a[0]: a[1] for a in ACHIEVEMENTS}
DESC = {a[0]: a[2] for a in ACHIEVEMENTS}
_IDS = {a[0] for a in ACHIEVEMENTS}


def _load():
    try:
        with open(_PATH) as f:
            return set(json.load(f)) & _IDS
    except (OSError, ValueError):
        return set()


def _save(unlocked):
    try:
        with open(_PATH, "w") as f:
            json.dump(sorted(unlocked), f)
    except OSError:
        pass


_unlocked = _load()


def unlock(aid):
    """Mark an achievement unlocked. Returns True only if newly unlocked."""
    if aid not in _IDS or aid in _unlocked:
        return False
    _unlocked.add(aid)
    _save(_unlocked)
    return True


def is_unlocked(aid):
    return aid in _unlocked


def unlocked_count():
    return len(_unlocked)


def total():
    return len(ACHIEVEMENTS)


def all_list():
    return [(aid, NAME[aid], DESC[aid], aid in _unlocked) for aid, _, _ in ACHIEVEMENTS]
