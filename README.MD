# Snake HD 🐍

A modernized Snake game built with Python and Pygame.

This project started as a simple Nokia-style Snake clone and evolved into a
modular, sprite-based retro arcade game with persistent high scores, custom
graphics, sound, selectable game modes and difficulty, a combo system, and a
scalable code architecture.

![Snake HD](assets/screenshot.png)

## Features

* Pixel-art sprite system (HD resolution)
* Animated items — a pulsing apple, a twinkling gold bonus, and blinking mines
* Two game modes: **Screen Wrap** or **Walls** (edges are deadly)
* Three difficulties: **Easy / Normal / Hard** (speed, mine rate, starting mines)
* **Combo multiplier** — chain quick eats for up to x5 points
* **Bonus golden apple** — appears occasionally, worth extra points, stacks with your combo
* Sound effects with an in-game mute toggle
* Red death-flash **and screen shake** on game over
* Persistent high score saving
* Enemy mines that spawn over time
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
git clone https://github.com/zr00t-1001/snake-hd.git
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

As the game progresses the snake speeds up and more enemy mines appear. Avoid
your own body and the mines — and in Walls mode, the edges too.

## Project Structure

```text
snake-hd/
│
├── snake.py                 # Entry point + main game loop
│
├── assets/
│   ├── PressStart2P.ttf
│   ├── PressStart2P-OFL.txt # Font license (SIL OFL 1.1)
│   ├── screenshot.png
│   ├── sprites/             # head, body, tail + animated food, bonus, mine
│   └── sounds/              # eat, bonus, gameover
│
├── game/
│   ├── settings.py          # Resolution, palette, difficulty & combo tunables
│   ├── snake_logic.py
│   ├── collision_logic.py
│   └── spawn_logic.py
│
├── helpers/
│   ├── helper_function.py   # Drawing helpers + sprite animation
│   ├── storage.py           # High-score persistence
│   └── audio.py             # Sound effects + mute
│
├── requirements.txt
├── LICENSE
└── README.MD
```

## Future Improvements

* Snake head animation (blinking eyes / tongue flick)
* Particle effects
* Multiple enemy types
* Leaderboard system
* Mobile version

## Built With

* Python
* Pygame

## Credits & License

* **Code, sprites, and sound effects:** released under the [MIT License](LICENSE).
  *(Remember to replace `[Your Name]` in the `LICENSE` file.)*
* **Font:** [Press Start 2P](https://fonts.google.com/specimen/Press+Start+2P)
  by CodeMan38, licensed under the SIL Open Font License v1.1
  (see `assets/PressStart2P-OFL.txt`). It is **not** covered by the MIT license.
