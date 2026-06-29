# Snake HD — online leaderboard

A small Rust/Axum service that stores high scores as a **tamper-evident hash
chain**, enforced server-side. Each submitted score becomes a block whose
SHA-256 hash covers its fields plus the previous block's hash — the same
mechanism as the game's local `helpers/ledger.py`, but as a shared backend.

## Run

```bash
cd server
cargo run        # listens on 0.0.0.0:8080, persists to scores.json
```

## Endpoints

| Method | Path             | Body / Query            | Returns                          |
| ------ | ---------------- | ----------------------- | -------------------------------- |
| GET    | `/health`        | —                       | `ok`                             |
| POST   | `/scores`        | `{ "name", "score" }`   | the new block (or `null` if ≤ 0) |
| GET    | `/scores`        | `?n=10`                 | top N blocks by score            |
| GET    | `/verify`        | —                       | `{ ok, first_bad_index }`        |

## Try it

```bash
curl -X POST localhost:8080/scores -H 'content-type: application/json' \
  -d '{"name":"ZOEL","score":130}'

curl localhost:8080/scores?n=5
curl localhost:8080/verify
```

Then edit a score in `scores.json` by hand and hit `/verify` again — it reports
the first broken block. You can't rewrite history without re-mining the chain.

## Next

Wire the game's game-over screen to `POST /scores` and pull `GET /scores` for a
global board (currently the game keeps its own local ledger).
