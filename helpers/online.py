"""Optional online leaderboard client for the Snake HD Rust/Axum server.

Speaks the server's REST API (`POST /scores`, `GET /scores?n=`). Every call is
wrapped so a missing or unreachable server never breaks the game - it simply
falls back to the local hash-chain ledger. Network work runs on a daemon thread
so the game loop never blocks waiting on a socket.

Uses only the Python standard library (urllib), so the game's runtime
dependency stays "pygame only".
"""

import json
import threading
import urllib.error
import urllib.request

try:
    from game.settings import ONLINE_ENABLED, SERVER_URL
except Exception:                       # settings import shouldn't ever break the game
    ONLINE_ENABLED, SERVER_URL = False, "http://127.0.0.1:8080"

TIMEOUT = 1.0   # seconds; keep short so the background thread settles quickly

# Shared state the game-over panel reads each frame.
#   status: "idle" | "loading" | "online" | "offline"
#   scores: list of (name, score) tuples, already sorted high -> low
STATE = {"status": "idle", "scores": []}


def _post(path, payload):
    url = SERVER_URL.rstrip("/") + path
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode("utf-8"))


def _get(path):
    url = SERVER_URL.rstrip("/") + path
    with urllib.request.urlopen(url, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode("utf-8"))


def submit_score(name, score):
    """POST one score. Returns the created block dict, or None on any failure."""
    try:
        return _post("/scores", {"name": str(name)[:12], "score": int(score)})
    except (urllib.error.URLError, OSError, ValueError, json.JSONDecodeError):
        return None


def fetch_top(n=5):
    """GET the global top N. Returns a list of (name, score), or None if offline."""
    try:
        blocks = _get(f"/scores?n={int(n)}")
        return [(b.get("name", "ANON"), int(b.get("score", 0))) for b in blocks]
    except (urllib.error.URLError, OSError, ValueError, TypeError, json.JSONDecodeError):
        return None


def _worker(name, score, n):
    global STATE
    submit_score(name, score)           # best effort; the returned block is ignored
    rows = fetch_top(n)
    STATE = {"status": "offline", "scores": []} if rows is None \
        else {"status": "online", "scores": rows}


def submit_async(name, score, n=5):
    """Submit a score and refresh the global board on a daemon thread (non-blocking)."""
    global STATE
    if not ONLINE_ENABLED:
        STATE = {"status": "idle", "scores": []}
        return
    STATE = {"status": "loading", "scores": []}
    threading.Thread(target=_worker, args=(name, score, n), daemon=True).start()


def reset():
    global STATE
    STATE = {"status": "idle", "scores": []}


# Separate slot for the title-screen global board (fetched, never submitted).
BOARD = {"status": "idle", "scores": []}


def fetch_board_async(n=5):
    """Refresh the global board for the menu on a daemon thread (non-blocking)."""
    global BOARD
    if not ONLINE_ENABLED:
        BOARD = {"status": "idle", "scores": []}
        return
    BOARD = {"status": "loading", "scores": []}

    def _w():
        global BOARD
        rows = fetch_top(n)
        BOARD = {"status": "offline", "scores": []} if rows is None \
            else {"status": "online", "scores": rows}

    threading.Thread(target=_w, daemon=True).start()
