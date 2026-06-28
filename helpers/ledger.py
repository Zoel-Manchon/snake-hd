"""Tamper-evident score ledger.

Every completed run is appended as a *block* in a hash chain. Each block's
SHA-256 hash covers its own fields plus the previous block's hash — exactly
like a blockchain. Editing any past score (without re-mining every block that
follows it) breaks the chain, and `verify()` reports the first broken block.

The ledger is stored as plain JSON (`scores.json`) so you can open it and try
to tamper with it yourself.

CLI:
    python -m helpers.ledger show      # print the whole chain
    python -m helpers.ledger top       # print the top 10 scores
    python -m helpers.ledger verify    # check the chain is intact
"""

import hashlib
import json
import sys
from datetime import datetime, timezone

LEDGER_FILE = "scores.json"
GENESIS_PREV = "0" * 64


def _hash_block(index, timestamp, name, score, prev_hash):
    """SHA-256 over the block's canonical fields (order fixed, not JSON-order)."""
    payload = f"{index}|{timestamp}|{name}|{score}|{prev_hash}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load(path=LEDGER_FILE):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
            return data if isinstance(data, list) else []
    except (FileNotFoundError, ValueError, OSError):
        return []


def _save(blocks, path=LEDGER_FILE):
    try:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(blocks, fh, indent=2)
    except OSError:
        pass


def record_score(score, name="PLAYER", path=LEDGER_FILE):
    """Append a score as a new block linked to the previous one. Returns it
    (or None for a non-positive score, which we don't bother recording)."""
    score = int(score)
    if score <= 0:
        return None

    blocks = load(path)
    prev_hash = blocks[-1]["hash"] if blocks else GENESIS_PREV
    index = len(blocks)
    timestamp = datetime.now(timezone.utc).isoformat()

    block = {
        "index": index,
        "timestamp": timestamp,
        "name": name,
        "score": score,
        "prev_hash": prev_hash,
    }
    block["hash"] = _hash_block(index, timestamp, name, score, prev_hash)
    blocks.append(block)
    _save(blocks, path)
    return block


def verify(path=LEDGER_FILE):
    """Walk the chain. Returns (ok, first_bad_index); index is None when ok."""
    blocks = load(path)
    prev_hash = GENESIS_PREV
    for i, b in enumerate(blocks):
        try:
            recomputed = _hash_block(
                b["index"], b["timestamp"], b["name"], b["score"], b["prev_hash"]
            )
        except (KeyError, TypeError):
            return False, i
        if b.get("prev_hash") != prev_hash:   # link to the previous block is wrong
            return False, i
        if b.get("hash") != recomputed:        # this block's contents were altered
            return False, i
        prev_hash = b["hash"]
    return True, None


def top_scores(n=10, path=LEDGER_FILE):
    blocks = load(path)
    ranked = sorted(blocks, key=lambda b: (-int(b["score"]), b["index"]))
    return [(b["name"], int(b["score"])) for b in ranked[:n]]


def _cli(argv):
    cmd = argv[1] if len(argv) > 1 else "verify"
    if cmd == "show":
        for b in load():
            print(f'#{b["index"]:>3}  {b["score"]:>6}  {b["name"]:<10}  '
                  f'{b["hash"][:12]}\u2026  (prev {b["prev_hash"][:8]}\u2026)')
    elif cmd == "top":
        rows = top_scores()
        if not rows:
            print("no scores yet")
        for rank, (name, score) in enumerate(rows, 1):
            print(f"{rank:>2}. {score:>6}  {name}")
    else:  # verify
        ok, bad = verify()
        if ok:
            print(f"chain OK \u2014 {len(load())} block(s), every hash links up")
        else:
            print(f"CHAIN BROKEN at block #{bad} \u2014 a score was tampered with")
            sys.exit(1)


if __name__ == "__main__":
    _cli(sys.argv)
