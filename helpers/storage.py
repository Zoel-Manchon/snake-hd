"""Persist the high score between runs in a small text file."""

HIGH_SCORE_FILE = "highscore.txt"


def load_high_score(path=HIGH_SCORE_FILE):
    """Return the saved high score, or 0 if it's missing or unreadable."""
    try:
        with open(path, "r") as handle:
            return int(handle.read().strip())
    except (FileNotFoundError, ValueError, OSError):
        return 0


def save_high_score(score, path=HIGH_SCORE_FILE):
    """Write the high score to disk. Failures here are non-critical."""
    try:
        with open(path, "w") as handle:
            handle.write(str(int(score)))
    except OSError:
        pass