# Qbit Quest: Escape Room, Future Computing

The digital version of the future computing component of MESA's 2026 MacDiarmid outreach escape room.

These puzzles were designed by Lekshmi Dinachandran, James Stevens, and Elouan Hay-Fourmond in 2026.
The app was coded with the help of Claude Opus 5.5 and designed by Elouan Hay-Fourmond.
To access the app simply click on the following link: https://mesa-escape-room.streamlit.app/

---

## Contents

- [How to play](#how-to-play)
- [Running a session](#running-a-session)
- [Changing the passwords and final code](#changing-the-passwords-and-final-code)
- [Adding and editing puzzles](#adding-and-editing-puzzles)
- [Changing speeds and appearance](#changing-speeds-and-appearance)
- [Running the app on your own computer](#running-the-app-on-your-own-computer)
- [Updating the live app](#updating-the-live-app)
- [Project files](#project-files)

---

## How to play

1. **Open the link** on a phone, tablet or computer. On a phone, turn it sideways: the game is designed for landscape.
2. **Log in.** Type the password into the login screen. The password you use decides the difficulty (easy, medium or hard), which is shown on a badge at the top of the screen.
3. **Solve each puzzle.** Every puzzle is a small circuit. Signals travel along the wires from left to right, pass through gates, and arrive at the goal squares on the right. Your job is to work out which signals to send in.
   - **Tap a dashed square** on the left to choose its input. Each tap flips it between black and white.
   - **Press Confirm** once every square is chosen. The signals travel through the circuit and the gates light up as they pass.
   - **Green glow:** every goal matches, and the next puzzle starts automatically.
   - **Red glow and shake:** at least one goal doesn't match. The red squares show which. Change your inputs and try again.
4. **Stuck?** Tap the circled **?** in the bottom-left corner for a hint, if the puzzle has one. When it blinks, it's worth a look.
5. **Escape!** After the last puzzle, the victory screen shows your time and, if one is set, a code to unlock something in the room.

### What the symbols mean

| Symbol | Meaning |
| --- | --- |
| White | A signal of **1** |
| Black | A signal of **0** |
| Black-and-white stripes, or a half-white, half-black square | A **superposition**: both 0 and 1 at once |
| Yellow triangle | **Flips** its wire: 1 becomes 0, and 0 becomes 1 |
| Blue octagon pointing at a triangle | A **control**: the triangle only flips if the octagon's wire is 1 |
| Red-and-yellow gem (the Superflippy) | Turns a 0 or 1 into a **superposition**, and turns a superposition back again |

### Good to know

- **Progress is saved** in each browser tab, so an accidental refresh won't send players back to the start. A new tab, or the **Play again** button on the victory screen, starts a fresh game.
- Every device plays independently, so a whole class can use the same link at once.
- Passwords ignore capital letters and spaces. After three wrong tries, a password hint appears (if one is set).

---

## Running a session

- **Wake the app up first.** The free hosting puts the app to sleep after a period without visitors. Open the link yourself shortly before the session; if you see a button to wake the app, press it and wait about a minute.
- **Share the link as a QR code** on the board or a worksheet, so nobody has to type it.
- **Between groups**, press **Play again** on the victory screen (or open the link in a new tab) to return to the login screen.
- **Don't update the app during a session.** If puzzles are added or reordered while people are playing, anyone who refreshes may land on a different puzzle.

---

## Changing the passwords and final code

These live in `escape_room.json`:

```json
{
  "passwords": {
    "easy": "your-easy-password",
    "medium": "your-medium-password",
    "hard": "your-hard-password"
  },
  "password_hint": "Shown after three wrong tries. Use \"\" for no hint.",
  "final_code": "1234"
}
```

- **Each difficulty plays its own puzzles plus all the easier ones**, so hard plays every puzzle. Remove a line from `"passwords"` to make that difficulty unavailable.
- Every password must be different.
- `final_code` is shown on the victory screen, for example to open a padlock. Use `""` to hide it.

> **Note:** this repository is public, so anyone who finds it can read `escape_room.json`, and a determined player could also find the passwords in the page's source code. That's fine for an outreach game, but never reuse a real password here.

---

## Adding and editing puzzles

Each puzzle is one `.json` file in the `Puzzles` folder. To add a puzzle, copy an existing file, give it a new name, and edit it. For example:

```json
{
  "id": "chain-reaction",
  "level": 3,
  "difficulty": "medium",
  "mode": "find_inputs",
  "num_qubits": 3,
  "gates": [
    {"type": "CNOT", "control": 2, "target": 1},
    {"type": "CNOT", "control": 1, "target": 0}
  ],
  "outputs": [1, 0, 0],
  "hint": {
    "text": "Start with the bottom wire: nothing changes it.",
    "pulse_on_start": false,
    "pulse_on_fail": true
  }
}
```

| Field | What it does |
| --- | --- |
| `id` | A unique name for the puzzle. |
| `level` | Puzzles are played in order of level, lowest first. Decimals such as `1.1`, `1.2` are useful for grouping by theme (see below). |
| `difficulty` | `"easy"`, `"medium"` or `"hard"`. Optional: puzzles without one count as easy. |
| `mode` | Always `"find_inputs"` for now: the player chooses the inputs. |
| `num_qubits` | How many wires the circuit has. Wire `0` is the top wire. |
| `gates` | The gates, in order from left to right (see below). |
| `outputs` | The goal for each wire, top to bottom: `1` (white), `0` (black) or `"S"` (superposition). |
| `hint` | Optional. Either just the text, `"hint": "Try the bottom wire first."`, or an object with `text` plus the blinking settings below. Leave it out to hide the hint button for that puzzle. |

**Hint blinking:** `"pulse_on_start": true` makes the hint button blink from the start of the puzzle, and `"pulse_on_fail": true` makes it blink after a wrong answer. Both are optional and off unless set, and the blinking stops once the hint is opened.

### Gates

| Gate | How to write it | Looks like |
| --- | --- | --- |
| Flip | `{"type": "X", "target": 0}` | Yellow triangle |
| Controlled flip | `{"type": "CNOT", "control": 2, "target": 1}` | Blue octagon pointing at a triangle |
| Double-controlled flip | `{"type": "CCNOT", "controls": [0, 2], "target": 1}` | Two octagons pointing at a triangle |
| Superflippy | `{"type": "H", "target": 0}` | Red-and-yellow gem |

### Tips

- **You never write the answer.** The app simulates the circuit with the player's inputs and compares the result with `outputs`, so a puzzle can't have a wrong answer, and puzzles with more than one solution just work.
- **Mistakes are reported on the page.** If a puzzle file has an error (a typo in a gate type, a wire that doesn't exist, an unknown hint setting), the app shows a red message naming the file and the problem, skips that puzzle, and keeps the rest working.
- **Levels with decimals:** write them as numbers, without quotes (`"level": 1.2`, not `"level": "1.2"`). If a theme might have ten or more puzzles, use two decimal places from the start (`1.01`, `1.02`, … `1.10`), because `1.10` is the same number as `1.1`.

---

## Changing speeds and appearance

| What | Where | Setting |
| --- | --- | --- |
| Speed of the circuit animation | `app.py`, near the top | `ANIMATION_SPEED`: `1` is normal, `2` is twice as fast, `0.5` is half speed |
| Individual timings (signal travel, gate glow, pause after solving, welcome message) | `app.py`, near the top | `ANIMATION_SECONDS` |
| Moving background (speed, grid brightness, number of shapes) | `game.html`, near the top of the script | `BACKGROUND_MOTION` |
| Colours of wires, gates and boxes | `game.html`, near the top of the script | `COLOUR` |

Every setting has a comment next to it explaining what it does.

---

## Running the app on your own computer

You'll need Python 3.12 or newer. In a terminal, from the project folder:

```bash
python -m venv .venv
source .venv/bin/activate        # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Or, if you use [uv](https://docs.astral.sh/uv/):

```bash
uv venv
uv pip install -r requirements.txt
uv run streamlit run app.py
```

The app opens in your browser. Refresh the page to see changes to puzzle files or settings.

---

## Updating the live app

The live app is hosted on Streamlit Community Cloud and updates itself from this repository:

1. Make and test your changes locally.
2. Commit and push to the `main` branch.
3. Within a minute or two, the app at https://mesa-escape-room.streamlit.app/ updates automatically.

Small edits, like changing a hint or a password, can also be made directly on GitHub using the pencil icon on any file.

If you add a Python package, regenerate `requirements.txt` before pushing:

```bash
uv export --format requirements-txt --no-hashes --no-emit-project > requirements.txt
```

If something goes wrong after an update, the error appears under **Manage app** on the Streamlit page, and any bad change can be undone by reverting its commit on GitHub.

---

## Project files

| File | What it is |
| --- | --- |
| `app.py` | Loads and checks the puzzles and settings, then shows the game. Also holds the animation speed settings. |
| `game.html` | The game itself: login screen, puzzles, animation and victory screen. Runs in the player's browser. |
| `escape_room.json` | Passwords, password hint and final code. |
| `Puzzles/` | One `.json` file per puzzle. |
| `requirements.txt` | The Python packages the app needs. |

---

## Licence

This project is released under the [MIT Licence](LICENSE).
