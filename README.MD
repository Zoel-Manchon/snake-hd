# Snake HD 🐍

A modernized Snake game built with Python and Pygame — plus a companion
Rust/Axum service for a tamper-evident online leaderboard.

This project started as a simple Nokia-style Snake clone and evolved into a
modular, sprite-based retro arcade game: persistent high scores, custom
graphics, sound, selectable modes and difficulty, a combo system, particle
juice, three enemy types, a SHA-256 score ledger, and a steady 60 FPS loop.

![Snake HD](docs/screenshots/snake_hd.gif)


## Features

* Custom sprite art (HD, supersampled) — snake, apple, golden bonus, mine, power-ups
* Animated items — a shining apple, a twinkling gold bonus, and a pulsing mine
* Animated snake head with a **flicking tongue**
* **Smooth 60 FPS loop** — rendering is decoupled from movement via a time accumulator
* Two game modes: **Screen Wrap** or **Walls** (edges are deadly)
* Three difficulties: **Easy / Normal / Hard** (speed, mine rate, starting mines)
* **Three enemy types** — static **mines**, **drifters** that slide and bounce, and **blinkers** that phase between deadly and safe-to-pass
* **Combo multiplier** — chain quick eats for up to x5 points
* **Bonus golden apple** — appears occasionally, worth extra points, stacks with your combo
* Three **power-ups** — Slow-Mo, x2 Points, and Magnet
* **Particle bursts** on every eat, bonus, power-up, and death
* **Floating score popups** (`+N`) that rise and fade where you eat
* Red death-flash **and screen shake** on game over
* **Tamper-evident leaderboard** — each run is a SHA-256-linked block; the top 5 show on the game-over screen
* On-screen **FPS** readout
* Sound effects with an in-game mute toggle
* Persistent high score saving
* Start menu, pause, and game-over / restart flow
* Modular code structure and a retro pixel font

## Controls

| Key       | Action                                   |
| --------- | ---------------------------------------- |
| ↑ ↓ ← →   | Move the snake                           |
| ↑ ↓       | In menu: move between settings           |
| ← →       | In menu: change the selected setting     |
| ENTER     | Start the game                           |
| P         | Pause / resume                           |
| M         | Mute / unmute sound                      |
| SPACE     | Restart after game over                  |

## Installation

Clone the repository:

```bash
git clone https://github.com/Zoel-Manchon/snake-hd.git
cd snake-hd
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the game (from the project root, so the asset paths resolve):

```bash
python snake.py
```

The high score is saved to `highscore.txt` in the project folder. That file is
git-ignored, so each player keeps their own.

## Gameplay

Eat apples to grow and score. Eat several in quick succession to build a combo
multiplier (shown under the HUD with a countdown bar) — the higher the combo,
the more each apple is worth. Watch for the golden bonus apple, which is worth
extra and multiplies with your current combo before it vanishes.

As the game progresses the snake speeds up and more enemies appear. Drifters
slide around, blinkers are only deadly while solid, and mines never move. Avoid
your own body and any solid enemy — and in Walls mode, the edges too.

## Score ledger (tamper-evident)

Every run is appended to `scores.json` as a block whose SHA-256 hash covers its
fields plus the previous block's hash — a small blockchain. Editing a past score
without re-mining every block after it breaks the chain.

```bash
python -m helpers.ledger show     # the whole chain
python -m helpers.ledger top      # the leaderboard
python -m helpers.ledger verify   # "chain OK" — or the first broken block
```

## Online leaderboard server (optional)

`server/` holds a Rust/Axum service that enforces the same hash chain
server-side, so multiple players can share one board.

```bash
cd server
cargo run     # http://0.0.0.0:8080, persists to scores.json
```

| Method | Path        | Body / Query          | Returns                          |
| ------ | ----------- | --------------------- | -------------------------------- |
| GET    | `/health`   | —                     | `ok`                             |
| POST   | `/scores`   | `{ "name", "score" }` | the new block (or `null` if ≤ 0) |
| GET    | `/scores`   | `?n=10`               | top N blocks by score            |
| GET    | `/verify`   | —                     | `{ ok, first_bad_index }`        |

> The backend is ready; wiring the game's game-over screen to it is in progress.

## Project Structure

```text
snake-hd/
│
├── snake.py                 # Entry point + 60 FPS accumulator game loop
│
├── assets/
│   ├── PressStart2P.ttf
│   ├── PressStart2P-OFL.txt # Font license (SIL OFL 1.1)
│   ├── screenshot.png
│   ├── sprites/             # head, body, tail + animated food, bonus, mine + power-ups
│   └── sounds/              # eat, bonus, gameover, powerup
│
├── game/
│   ├── settings.py          # Resolution, palette, difficulty, combo & enemy tunables
│   ├── snake_logic.py
│   ├── collision_logic.py
│   ├── spawn_logic.py
│   └── enemies.py           # Mine / drifter / blinker behaviour
│
├── helpers/
│   ├── helper_function.py   # Drawing helpers + sprite animation (cached background)
│   ├── fx.py                # Particle bursts + floating score popups
│   ├── ledger.py            # SHA-256 hash-chain score ledger + CLI
│   ├── storage.py           # High-score persistence
│   └── audio.py             # Sound effects + mute
│
├── server/                  # Rust/Axum tamper-evident leaderboard service
│   ├── Cargo.toml
│   ├── README.md
│   └── src/main.rs
│
├── requirements.txt
├── LICENSE
└── README.MD
```

## Future Improvements

* Wire the game UI to the leaderboard server (submit + show the global board)
* Smooth movement interpolation (slide segments between cells at 60 FPS)
* Local 2-player versus (WASD vs arrows)
* Mobile / Android build

## Built With

* Python + Pygame (game)
* Rust + Axum (leaderboard server)

## Credits & License

* **Code, sprites, and sound effects:** released under the [MIT License](LICENSE).

* **Font:** [Press Start 2P](https://fonts.google.com/specimen/Press+Start+2P)
  by CodeMan38, licensed under the SIL Open Font License v1.1
  (see `assets/PressStart2P-OFL.txt`). It is **not** covered by the MIT license.
