"""
Qbit Quest: a quantum circuit puzzle game for school kids.

HOW THE PROJECT FITS TOGETHER
-----------------------------
    app.py      <- this file. Loads the puzzles, checks them for mistakes,
                   and hands them to the game page.
    game.html   <- the game itself: drawing, clicking, the Confirm button,
                   the simulation and the animation all run here, in the
                   player's browser.
    puzzles/    <- one .json file per puzzle. Add as many as you like.
    escape_room.json <- the login password and the end-of-game settings.

WHAT THE PLAYERS SEE
--------------------
    1. A computer login screen asking for a password.
    2. The puzzles, one after another, in order of "level".
       Each one must be solved to move on.
    3. A "you have beaten the escape room" screen.

ESCAPE ROOM SETTINGS (escape_room.json)
---------------------------------------
    {
      "password": "qubit",                 needed to get past the login screen
                                           (not case sensitive)
      "password_hint": "It's in the name", shown after 3 wrong tries ("" = never)
      "final_code": "4721"                 shown on the victory screen, e.g. for a
                                           padlock in the room ("" = don't show one)
    }
    Note: a determined player could find the password by viewing the page
    source. That's fine for a classroom game, but don't reuse a real password.

WRITING A PUZZLE FILE
---------------------
    {
      "id": "chain-reaction",     a unique name for the puzzle
      "level": 3,                 puzzles are shown in order of level
      "mode": "find_inputs",      the player picks the inputs (only mode so far)
      "num_qubits": 3,            how many wires (qubit 0 is the top wire)
      "gates": [                  gates in time order, left to right
        {"type": "CNOT", "control": 2, "target": 1},
        {"type": "CNOT", "control": 1, "target": 0}
      ],
      "outputs": [1, 0, 0]        the goal for each wire: 1, 0 or "S"
    }

    Signals:  1 = white,  0 = black,  "S" = superposition (half white, half black)

    Gate types:
      "X"      yellow triangle: flips its wire (1 -> 0, 0 -> 1)
      "CNOT"   blue octagon on the "control" wire pointing at a triangle on
               the "target" wire: flips the target only if the control is 1
      "CCNOT"  like CNOT but with two octagons: "controls": [a, b]
      "H"      the Superflippy gem: turns a 0 or 1 into a superposition
               (and turns a superposition back again!)

The answer is never stored in the file: the game simulates the circuit with
the player's inputs and compares the result with "outputs". So you can't
write a puzzle with a wrong answer, and puzzles with several answers just work.
"""

import json
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

# ---------------------------------------------------------------------------
# File locations (relative to this file, so it works locally AND when hosted)
# ---------------------------------------------------------------------------
HERE = Path(__file__).parent
PUZZLE_DIR = HERE / "puzzles"
GAME_PAGE = HERE / "game.html"
SETTINGS_FILE = HERE / "escape_room.json"

# Background colour shared by the page and the game, so they look like one
# screen. Must match --background in game.html.
BACKGROUND = "#0e1124"

# ---------------------------------------------------------------------------
# ANIMATION SPEED: change these to make the game faster or slower
# ---------------------------------------------------------------------------
# One knob for the circuit animation: 1 = normal, 2 = twice as fast,
# 0.5 = half speed (good for explaining things slowly to a class).
ANIMATION_SPEED = 1.0

# Fine-tuning, in seconds. Only "wire" and "gate" are affected by
# ANIMATION_SPEED; the two pauses always last exactly as long as set here.
ANIMATION_SECONDS = {
    "wire": 1,       # a signal travelling from one gate to the next
    "gate": 1,       # pause while a gate glows before the signals move on
    "celebrate": 2.4,   # pause after a solved puzzle before the next one starts
    "welcome": 1.3,     # "Welcome, agent..." after the right password
}


def animation_timing():
    """Turn the settings above into milliseconds for the game page."""
    if ANIMATION_SPEED <= 0:
        raise ValueError("ANIMATION_SPEED must be more than 0")
    timing = {}
    for name, seconds in ANIMATION_SECONDS.items():
        if name in ("wire", "gate"):
            seconds = seconds / ANIMATION_SPEED   # the speed knob only affects these two
        timing[name] = round(seconds * 1000)      # the game counts in milliseconds
    return timing


# Which gate types exist, and which control settings each one needs
GATES_WITHOUT_CONTROLS = {"X", "H"}
GATES_WITH_ONE_CONTROL = {"CNOT"}
GATES_WITH_TWO_CONTROLS = {"CCNOT"}
ALL_GATES = GATES_WITHOUT_CONTROLS | GATES_WITH_ONE_CONTROL | GATES_WITH_TWO_CONTROLS


# ---------------------------------------------------------------------------
# Checking puzzle files for mistakes
# ---------------------------------------------------------------------------
def find_problems(puzzle):
    """Return a list of human-readable problems with a puzzle (empty = OK)."""
    problems = []

    # 1. Every required field must be present
    for field in ("id", "level", "num_qubits", "gates", "outputs"):
        if field not in puzzle:
            problems.append(f'missing "{field}"')
    if problems:
        return problems  # can't check anything else without these

    n = puzzle["num_qubits"]

    def is_wire(q):
        """True if q is a valid wire number for this puzzle."""
        return isinstance(q, int) and 0 <= q < n

    # 2. There must be exactly one goal per wire, and each must be 0, 1 or "S"
    if len(puzzle["outputs"]) != n:
        problems.append(f'"outputs" has {len(puzzle["outputs"])} values but there are {n} qubits')
    for value in puzzle["outputs"]:
        if value not in (0, 1, "S"):
            problems.append(f'output {value!r} should be 0, 1 or "S"')

    # 3. Every gate must be a known type, on real wires, with the right controls
    for number, gate in enumerate(puzzle["gates"], start=1):
        kind = gate.get("type")
        where = f"gate {number} ({kind})"

        if kind not in ALL_GATES:
            problems.append(f'{where}: unknown type, use one of {sorted(ALL_GATES)}')
            continue

        # Work out which wires this gate touches
        if kind in GATES_WITH_ONE_CONTROL:
            controls = [gate.get("control")]
        elif kind in GATES_WITH_TWO_CONTROLS:
            controls = gate.get("controls", [])
            if len(controls) != 2:
                problems.append(f'{where}: needs "controls": [a, b]')
        else:
            controls = []
        wires = [gate.get("target")] + controls

        if not all(is_wire(q) for q in wires):
            problems.append(f"{where}: every wire must be a number from 0 to {n - 1}")
        elif len(set(wires)) != len(wires):
            problems.append(f"{where}: a gate can't use the same wire twice")

    return problems


def load_puzzles():
    """Read every puzzle file. Not cached on purpose: new or edited files
    show up as soon as you refresh the page."""
    good, bad = [], []
    for path in sorted(PUZZLE_DIR.glob("*.json")):
        try:
            puzzle = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            bad.append((path.name, [f"not valid JSON: {error}"]))
            continue
        problems = find_problems(puzzle)
        if problems:
            bad.append((path.name, problems))
        else:
            good.append(puzzle)
    good.sort(key=lambda p: (p["level"], p["id"]))  # easiest first
    return good, bad


def load_settings():
    """Read escape_room.json. Returns (settings, problem); problem is None if OK."""
    if not SETTINGS_FILE.exists():
        return None, f"{SETTINGS_FILE.name} is missing"
    try:
        settings = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        return None, f"{SETTINGS_FILE.name} is not valid JSON: {error}"
    if not str(settings.get("password", "")).strip():
        return None, f'{SETTINGS_FILE.name} needs a "password"'
    # Fill in the optional settings so the game can rely on them existing
    settings.setdefault("password_hint", "")
    settings.setdefault("final_code", "")
    return settings, None


# ---------------------------------------------------------------------------
# Page styling: full screen, no Streamlit chrome, forced landscape on phones
# ---------------------------------------------------------------------------
PAGE_CSS = f"""
<style>
/* Hide Streamlit's own header, toolbar, decoration bar and footer */
header[data-testid="stHeader"], [data-testid="stToolbar"],
[data-testid="stDecoration"], footer {{ display: none !important; }}

/* Remove the padding and gaps around the game so it fills the screen */
.block-container, [data-testid="stMainBlockContainer"] {{
    padding: 0 !important; max-width: none !important;
}}
[data-testid="stVerticalBlock"] {{ gap: 0 !important; }}

/* Same background behind the game as inside it */
.stApp {{ background: {BACKGROUND}; }}

/* Make the game exactly one screen tall (dvh ignores the phone's URL bar) */
iframe {{
    display: block; border: none;
    height: calc(100vh - 4px) !important;
    height: calc(100dvh - 4px) !important;
}}

/* FORCE LANDSCAPE: browsers don't let a web page lock the screen rotation,
   so when a phone is held upright we turn the whole app sideways instead.
   The app is made as wide as the screen is tall, rotated 90 degrees,
   then slid back into view. Kids just turn the phone to play. */
@media (orientation: portrait) and (max-width: 820px) {{
    .stApp {{
        position: fixed !important; top: 0; left: 0;
        width: 100vh !important;  width: 100dvh !important;
        height: 100vw !important;
        transform-origin: top left;
        transform: translateX(100vw) rotate(90deg);
        overflow: hidden;
    }}
    /* After rotating, the screen's width is the game's height */
    iframe {{ height: calc(100vw - 4px) !important; }}
}}
</style>
"""


# ---------------------------------------------------------------------------
# The app itself
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Qbit Quest", page_icon="🧩", layout="wide")
st.markdown(PAGE_CSS, unsafe_allow_html=True)

puzzles, broken = load_puzzles()
settings, settings_problem = load_settings()

if settings_problem:
    st.error(settings_problem)
    st.stop()

# Tell the puzzle author about any broken files (players never see this
# unless a file is broken, and the good puzzles still load)
for filename, problems in broken:
    st.error(f"**{filename}** was skipped: " + "; ".join(problems))

if not puzzles:
    st.warning(f"No puzzles found. Add .json files to {PUZZLE_DIR}.")
    st.stop()

# Put the puzzles, settings and animation timing into the game page. The
# page has three placeholders, /*PUZZLES*/[], /*SETTINGS*/{} and /*TIMING*/{},
# which we swap for the real data. Replacing "</" stops any text from accidentally closing the page's
# <script> tag.
def as_script_data(data):
    return json.dumps(data).replace("</", "<\\/")

page = (
    GAME_PAGE.read_text(encoding="utf-8")
    .replace("/*PUZZLES*/[]", as_script_data(puzzles))
    .replace("/*SETTINGS*/{}", as_script_data(settings))
    .replace("/*TIMING*/{}", as_script_data(animation_timing()))
)

# Show the game in a frame. The height here is only a starting value: the
# CSS above stretches it to fill the screen. st.iframe is the modern way;
# older Streamlit versions only have components.html, so fall back to that.
if hasattr(st, "iframe"):
    st.iframe(page, height=500)
else:
    components.html(page, height=500)
