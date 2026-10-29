import streamlit as st
from solver import solve, board_is_consistent
from solve_button import solve_clicked, water_button

st.set_page_config(page_title="Sudoku Solver", page_icon="🧩", layout="centered")

from login_page import show_login
try:
    from background import add_background
except ImportError:
    def add_background():  # background.py missing: the site still works, just without the animation
        pass

# Three ready-made puzzles (0 = empty box). The button cycles through them.
PUZZLES = [
    # Easy
    [
        [0, 0, 0, 0, 1, 9, 0, 5, 8],
        [0, 5, 8, 2, 3, 0, 1, 0, 0],
        [1, 4, 0, 5, 0, 8, 3, 0, 6],
        [0, 6, 3, 0, 5, 1, 2, 0, 0],
        [2, 8, 7, 6, 4, 0, 0, 0, 1],
        [5, 0, 1, 0, 2, 7, 0, 0, 3],
        [6, 0, 2, 3, 0, 4, 0, 0, 5],
        [9, 0, 0, 1, 8, 0, 6, 0, 2],
        [0, 1, 0, 0, 6, 2, 0, 3, 0],
    ],
    # Medium
    [
        [8, 0, 0, 7, 3, 0, 2, 4, 0],
        [0, 3, 0, 2, 1, 0, 0, 9, 0],
        [2, 0, 0, 8, 0, 9, 0, 5, 0],
        [0, 8, 0, 9, 0, 0, 5, 0, 0],
        [5, 0, 3, 0, 8, 0, 0, 0, 0],
        [0, 0, 6, 0, 2, 3, 4, 0, 8],
        [0, 0, 0, 0, 4, 2, 0, 0, 0],
        [3, 0, 2, 1, 9, 8, 6, 0, 0],
        [1, 9, 0, 0, 0, 0, 3, 0, 0],
    ],
    # Hard
    [
        [2, 7, 0, 0, 0, 0, 0, 0, 3],
        [1, 3, 9, 0, 0, 0, 6, 0, 0],
        [0, 0, 0, 0, 9, 0, 0, 2, 0],
        [0, 0, 0, 9, 0, 0, 0, 0, 0],
        [0, 0, 0, 6, 0, 0, 3, 0, 4],
        [0, 4, 0, 0, 7, 1, 8, 6, 0],
        [0, 6, 0, 0, 0, 9, 0, 8, 0],
        [8, 0, 2, 0, 0, 6, 0, 7, 0],
        [0, 0, 0, 8, 0, 5, 4, 3, 0],
    ],
]

# ---------- styling: makes the 9x9 grid look like a real Sudoku board ----------
st.markdown("""
<style>
/* ---- input board: one square grid, thin grey lines, thick lines between 3x3 boxes ---- */
.st-key-board { max-width: 480px; margin: 0 auto; border: 4px solid #ffffff; background: #f4f4f6;
    gap: 0 !important; padding: 0 !important; box-shadow: 0 0 22px rgba(255,255,255,0.45); }
.st-key-board * { border-radius: 0 !important; box-shadow: none !important; }
.st-key-board [data-testid="stVerticalBlock"] { gap: 0 !important; }
.st-key-board [data-testid="stHorizontalBlock"] { gap: 0 !important; flex-wrap: nowrap !important; }
.st-key-board [data-testid="stColumn"] { min-width: 0 !important; flex: 1 1 0 !important; width: auto !important; padding: 0 !important; }
.st-key-board [data-testid="stElementContainer"] { border: 1px solid #9a9aa2; box-sizing: border-box; width: 100% !important; margin: 0 !important; padding: 0 !important; }
.st-key-board [data-testid="stTextInput"], .st-key-board [data-testid="stTextInputRootElement"],
.st-key-board [data-baseweb="input"], .st-key-board [data-baseweb="base-input"] {
    background: transparent !important; border: none !important; outline: none !important; width: 100% !important; }
.st-key-board input {
    color: #111 !important; -webkit-text-fill-color: #111 !important; background: #f4f4f6 !important;
    text-align: center; font-size: 1.4rem; font-weight: 700; height: 54px; padding: 0 !important; caret-color: #111; }
.st-key-board input:focus { background: #d6e9ff !important; }
.st-key-board [data-testid="InputInstructions"] { display: none !important; }
/* thick dark lines between the 3x3 boxes */
.st-key-board [class*="_c2_"], .st-key-board [class*="_c5_"] { border-right: 3px solid #111 !important; }
.st-key-board [class*="cell_r2_"], .st-key-board [class*="cell_r5_"] { border-bottom: 3px solid #111 !important; }

/* ---- solved board ---- */
table.sudoku { border-collapse: collapse; margin: 0 auto; border: 4px solid #fff; box-shadow: 0 0 22px rgba(255,255,255,0.45); background: #f4f4f6; table-layout: fixed; width: 100%; max-width: 480px; }
table.sudoku td { border: 1px solid #9a9aa2; text-align: center; height: 54px; font-size: 1.4rem; font-weight: 700; color: #1b6fd1; padding: 0; }
table.sudoku td.given { color: #111; }
table.sudoku td.bR { border-right: 3px solid #111; }
table.sudoku td.bB { border-bottom: 3px solid #111; }
</style>
""", unsafe_allow_html=True)


def board_html(solved, original):
    rows = ""
    for r in range(9):
        cells = ""
        for c in range(9):
            cls = []
            if original[r][c] != 0: cls.append("given")
            if c in (2, 5): cls.append("bR")
            if r in (2, 5): cls.append("bB")
            cells += f'<td class="{" ".join(cls)}">{solved[r][c]}</td>'
        rows += f"<tr>{cells}</tr>"
    return f'<table class="sudoku">{rows}</table>'


# ---------- session state ----------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "page" not in st.session_state:
    st.session_state.page = "login"
if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "signin"
if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "grid" not in st.session_state:
    st.session_state.grid = [[0]*9 for _ in range(9)]
if "version" not in st.session_state:
    st.session_state.version = 0   # changing this resets the input boxes
if "puzzle_no" not in st.session_state:
    st.session_state.puzzle_no = -1   # -1 = none loaded yet, so the first click gives puzzle 0
if "result" not in st.session_state:
    st.session_state.result = None   # what to show under the button
if "solved" not in st.session_state:
    st.session_state.solved = False  # True = water has drained, False = glass is full


def reset_puzzle():
    """Used by Clear grid / Load example: forget the old answer and refill the water."""
    st.session_state.result = None
    st.session_state.solved = False


def go_to(page):
    st.session_state.page = page


def sign_out():
    st.session_state.logged_in = False
    st.session_state.page = "login"
    st.session_state.auth_mode = "signin"


def top_bar(step, title):
    """Small header shown on pages 2 and 3."""
    c1, c2 = st.columns([3, 1])
    c1.caption(f"Step {step} of 3  ·  Welcome, {st.session_state.user_name}")
    c2.button("Sign out", on_click=sign_out, key=f"signout_{step}")
    st.title(title)


# ---------- PAGE 1: login ----------
def page_login():
    show_login()


# ---------- PAGE 2: what is sudoku ----------
def page_learn():
    add_background()
    top_bar(2, "🧩 What is Sudoku?")
    st.write("Sudoku is a number puzzle on a 9 x 9 grid. Some boxes already have numbers. "
             "Your goal is to fill every empty box.")
    st.subheader("The rules")
    st.markdown("""
1. Use only the digits **1 to 9**.
2. No digit repeats in any **row**.
3. No digit repeats in any **column**.
4. No digit repeats in any **3x3 box**.
""")
    st.subheader("How our program works")
    st.markdown("""
**Input**: the puzzle you type in (empty boxes are blank).

**Process**: it finds an empty box, **guesses** a digit, **checks** the rules,
and if it gets stuck it **undoes** the guess and tries another one (this is called *backtracking*).

**Output**: the finished grid with every box filled.
""")
    st.caption("Made by Anya Patel, Hiranmayi G and Alankrita Soni")
    st.button("Next: Solve a puzzle  →", type="primary", on_click=go_to, args=("solve",), key="to_solve")


# ---------- PAGE 3: solve a puzzle ----------
def page_solve():
    add_background()
    top_bar(3, "🧩 Solve a Puzzle")
    st.write("Type the numbers you know (1-9). Leave empty boxes blank.")
    c1, c2 = st.columns(2)
    if c1.button("Load example puzzle"):
        st.session_state.puzzle_no = (st.session_state.puzzle_no + 1) % len(PUZZLES)   # next puzzle
        st.session_state.grid = [row[:] for row in PUZZLES[st.session_state.puzzle_no]]
        st.session_state.version += 1
        reset_puzzle()
    if c2.button("Clear grid"):
        st.session_state.grid = [[0]*9 for _ in range(9)]
        st.session_state.version += 1
        reset_puzzle()

    # 9x9 input boxes (inside a container so the CSS above can style them as one board)
    board = [[0]*9 for _ in range(9)]
    v = st.session_state.version
    with st.container(key="board"):
        for r in range(9):
            cols = st.columns(9, gap="small")
            for c in range(9):
                start = st.session_state.grid[r][c]
                text = cols[c].text_input(
                    f"r{r}c{c}", value=str(start) if start else "",
                    max_chars=1, label_visibility="collapsed",
                    key=f"cell_r{r}_c{c}_v{v}")
                board[r][c] = int(text) if text in list("123456789") else 0

    st.write("")
    button_area = st.container()      # the water button is drawn here, once we know the answer
    if solve_clicked():
        if not board_is_consistent(board):
            st.session_state.result = ("error", "These starting numbers already break a Sudoku rule. Please check your puzzle.")
            st.session_state.solved = False
        else:
            with st.spinner("Thinking..."):
                solved = [row[:] for row in board]
                ok = solve(solved)
            if ok:
                st.session_state.result = ("solved", solved, [row[:] for row in board])
                st.session_state.solved = True       # -> the water drains away
            else:
                st.session_state.result = ("warning", "No solution found for this puzzle.")
                st.session_state.solved = False
    with button_area:
        water_button(drained=st.session_state.solved)

    result = st.session_state.result
    if result:
        if result[0] == "error":
            st.error(result[1])
        elif result[0] == "warning":
            st.warning(result[1])
        else:
            st.success("Solved!  (black = your numbers, blue = filled in by the program)")
            st.markdown(board_html(result[1], result[2]), unsafe_allow_html=True)
    st.write("")
    st.button("←  Back to What is Sudoku?", on_click=go_to, args=("learn",), key="to_learn")


# ---------- router: login always comes first ----------
if not st.session_state.logged_in:
    st.session_state.page = "login"

if st.session_state.page == "login":
    page_login()
elif st.session_state.page == "learn":
    page_learn()
else:
    page_solve()