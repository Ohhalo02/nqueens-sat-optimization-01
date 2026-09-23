def validate_solution(solution, n):
    """Validate that a solution to N-Queens is correct."""
    if solution is None:
        return False
    if len(solution) != n:
        return False
    rows = set()
    cols = set()
    diag1 = set()  # r - c
    diag2 = set()  # r + c
    for r, c in solution:
        if r in rows or c in cols or (r-c) in diag1 or (r+c) in diag2:
            return False
        rows.add(r)
        cols.add(c)
        diag1.add(r - c)
        diag2.add(r + c)
    return True

def print_board(solution, n):
    """Print the board with queens."""
    board = [['.' for _ in range(n)] for _ in range(n)]
    if solution:
        for r, c in solution:
            board[r][c] = 'Q'
    for row in board:
        print(' '.join(row))
    print()
