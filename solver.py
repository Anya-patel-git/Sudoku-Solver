# solver.py - the brain of the project (no website code in here)

def is_valid(board, row, col, num):
    """Can `num` go at (row, col)? Checks the row, the column and the 3x3 box."""
    for i in range(9):
        if board[row][i] == num or board[i][col] == num:
            return False
    box_row, box_col = 3 * (row // 3), 3 * (col // 3)
    for r in range(box_row, box_row + 3):
        for c in range(box_col, box_col + 3):
            if board[r][c] == num:
                return False
    return True


def solve(board):
    """Solves the board in place. Returns True if solved, False if stuck."""
    for row in range(9):
        for col in range(9):
            if board[row][col] == 0:              # found an empty box
                for num in range(1, 10):          # GUESS 1 to 9
                    if is_valid(board, row, col, num):   # CHECK
                        board[row][col] = num
                        if solve(board):          # move on to the next empty box
                            return True
                        board[row][col] = 0       # UNDO (backtrack)
                return False                      # no digit fits: dead end
    return True                                   # no empty boxes left: solved


def board_is_consistent(board):
    """True if the starting numbers don't already break a rule."""
    for r in range(9):
        for c in range(9):
            n = board[r][c]
            if n != 0:
                board[r][c] = 0
                ok = is_valid(board, r, c, n)
                board[r][c] = n
                if not ok:
                    return False
    return True