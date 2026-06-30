"""Daily Challenge: a date-seeded run with per-day best tracking and a streak.

The run is seeded by today's date so each attempt on a given day is reproducible
and everyone is playing the same daily seed. Best scores per day are persisted so
you can chase your record and keep a play streak going (Wordle-style).
"""

import datetime
import json
import os

_PATH = "daily_scores.json"


def today_str():
    return datetime.date.today().isoformat()        # "2026-06-30"


def today_seed():
    d = datetime.date.today()
    return d.year * 10000 + d.month * 100 + d.day    # 20260630


def _load():
    try:
        with open(_PATH) as f:
            data = json.load(f)
            if isinstance(data, dict):
                return {k: int(v) for k, v in data.items()}
    except (OSError, ValueError, TypeError):
        pass
    return {}


def _save(data):
    try:
        with open(_PATH, "w") as f:
            json.dump(data, f)
    except OSError:
        pass


def record(score):
    """Record an attempt for today. Returns (is_new_best, best_today)."""
    data = _load()
    key = today_str()
    prev = data.get(key, 0)
    best = max(prev, int(score))
    data[key] = best
    _save(data)
    return (best > prev, best)


def best_today():
    return _load().get(today_str(), 0)


def history(n=5):
    """The most recent n recorded days as (label, best), newest first."""
    data = _load()
    return [(key[5:], data[key]) for key in sorted(data, reverse=True)[:n]]


def streak():
    """Number of consecutive days up to today that have a recorded entry."""
    data = _load()
    if not data:
        return 0
    d = datetime.date.today()
    count = 0
    while d.isoformat() in data:
        count += 1
        d -= datetime.timedelta(days=1)
    return count
