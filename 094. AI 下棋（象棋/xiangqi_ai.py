"""
AI 下棋（中国象棋）- 纯 Python 实现
=====================================
实现一个简化版中国象棋（Xiangqi）+ Minimax + Alpha-Beta AI。
特性：
- 完整 9x10 棋盘和初始布局
- 7 种棋子的合法走法（车/马/相/士/将/炮/兵）
- 红方/黑方双方对弈
- 基于材料价值 + 位置加权的评估函数
- Alpha-Beta 剪枝搜索（默认 depth=3）

棋子表示（红方大写，黑方小写）：
  车 R/r   马 N/n   相象 B/b   士 A/a
  将帅 K/k 炮 C/c   兵卒 P/p
"""

import copy


# ---------- 棋盘常量 ----------
BOARD_W, BOARD_H = 9, 10

INIT_BOARD = [
    list("rnbakabnr"),
    list("........."),
    list(".c.....c."),
    list("p.p.p.p.p"),
    list("........."),
    list("........."),
    list("P.P.P.P.P"),
    list(".C.....C."),
    list("........."),
    list("RNBAKABNR"),
]

PIECE_VALUES = {
    "K": 10000, "R": 600, "N": 270, "B": 120, "A": 120, "C": 285, "P": 30,
    "k": 10000, "r": 600, "n": 270, "b": 120, "a": 120, "c": 285, "p": 30,
}


def is_red(p): return p.isupper()
def is_black(p): return p.islower() and p != "."
def opposite(red): return not red


# ---------- 棋盘操作 ----------
def in_board(x, y):
    return 0 <= x < BOARD_W and 0 <= y < BOARD_H


def in_palace(x, y, red):
    if red:
        return 3 <= x <= 5 and 7 <= y <= 9
    return 3 <= x <= 5 and 0 <= y <= 2


def own_river(y, red):
    return y >= 5 if red else y <= 4


def get(board, x, y):
    return board[y][x]


def set_cell(board, x, y, p):
    board[y][x] = p


# ---------- 走法生成 ----------
def gen_moves(board, red):
    moves = []
    for y in range(BOARD_H):
        for x in range(BOARD_W):
            p = board[y][x]
            if p == ".":
                continue
            if is_red(p) != red:
                continue
            kind = p.upper()
            if kind == "R":
                moves.extend(_rook_moves(board, x, y, red))
            elif kind == "C":
                moves.extend(_cannon_moves(board, x, y, red))
            elif kind == "N":
                moves.extend(_knight_moves(board, x, y, red))
            elif kind == "B":
                moves.extend(_bishop_moves(board, x, y, red))
            elif kind == "A":
                moves.extend(_advisor_moves(board, x, y, red))
            elif kind == "K":
                moves.extend(_king_moves(board, x, y, red))
            elif kind == "P":
                moves.extend(_pawn_moves(board, x, y, red))
    # 过滤"将帅照面"非法
    valid = []
    for m in moves:
        nb = apply_move(board, m)
        if not _kings_face(nb):
            valid.append(m)
    return valid


def _rook_moves(board, x, y, red):
    moves = []
    for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
        nx, ny = x + dx, y + dy
        while in_board(nx, ny):
            t = board[ny][nx]
            if t == ".":
                moves.append((x, y, nx, ny))
            else:
                if is_red(t) != red:
                    moves.append((x, y, nx, ny))
                break
            nx += dx
            ny += dy
    return moves


def _cannon_moves(board, x, y, red):
    moves = []
    for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
        nx, ny = x + dx, y + dy
        # 移动（无吃）
        while in_board(nx, ny) and board[ny][nx] == ".":
            moves.append((x, y, nx, ny))
            nx += dx
            ny += dy
        # 越过一个炮架后吃子
        if in_board(nx, ny):
            nx += dx
            ny += dy
            while in_board(nx, ny):
                t = board[ny][nx]
                if t != ".":
                    if is_red(t) != red:
                        moves.append((x, y, nx, ny))
                    break
                nx += dx
                ny += dy
    return moves


def _knight_moves(board, x, y, red):
    moves = []
    # (脚位置, 落点)
    deltas = [
        ((0, -1), (-1, -2)), ((0, -1), (1, -2)),
        ((0, 1), (-1, 2)),   ((0, 1), (1, 2)),
        ((-1, 0), (-2, -1)), ((-1, 0), (-2, 1)),
        ((1, 0), (2, -1)),   ((1, 0), (2, 1)),
    ]
    for (lx, ly), (mx, my) in deltas:
        bx, by = x + lx, y + ly
        nx, ny = x + mx, y + my
        if not in_board(nx, ny):
            continue
        if not in_board(bx, by) or board[by][bx] != ".":
            continue
        t = board[ny][nx]
        if t == "." or is_red(t) != red:
            moves.append((x, y, nx, ny))
    return moves


def _bishop_moves(board, x, y, red):
    moves = []
    for dx, dy in [(2, 2), (2, -2), (-2, 2), (-2, -2)]:
        nx, ny = x + dx, y + dy
        bx, by = x + dx // 2, y + dy // 2
        if not in_board(nx, ny):
            continue
        if not own_river(ny, red):  # 不能过河
            continue
        if board[by][bx] != ".":     # 塞象眼
            continue
        t = board[ny][nx]
        if t == "." or is_red(t) != red:
            moves.append((x, y, nx, ny))
    return moves


def _advisor_moves(board, x, y, red):
    moves = []
    for dx, dy in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
        nx, ny = x + dx, y + dy
        if not in_board(nx, ny) or not in_palace(nx, ny, red):
            continue
        t = board[ny][nx]
        if t == "." or is_red(t) != red:
            moves.append((x, y, nx, ny))
    return moves


def _king_moves(board, x, y, red):
    moves = []
    for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
        nx, ny = x + dx, y + dy
        if not in_board(nx, ny) or not in_palace(nx, ny, red):
            continue
        t = board[ny][nx]
        if t == "." or is_red(t) != red:
            moves.append((x, y, nx, ny))
    return moves


def _pawn_moves(board, x, y, red):
    moves = []
    forward = -1 if red else 1
    candidates = [(0, forward)]
    if not own_river(y, red):  # 已过河可左右
        candidates.append((1, 0))
        candidates.append((-1, 0))
    for dx, dy in candidates:
        nx, ny = x + dx, y + dy
        if not in_board(nx, ny):
            continue
        t = board[ny][nx]
        if t == "." or is_red(t) != red:
            moves.append((x, y, nx, ny))
    return moves


def _kings_face(board):
    """检查双将是否同列对面"""
    rk = bk = None
    for y in range(BOARD_H):
        for x in range(BOARD_W):
            if board[y][x] == "K":
                rk = (x, y)
            elif board[y][x] == "k":
                bk = (x, y)
    if not rk or not bk:
        return False
    if rk[0] != bk[0]:
        return False
    x = rk[0]
    for y in range(min(rk[1], bk[1]) + 1, max(rk[1], bk[1])):
        if board[y][x] != ".":
            return False
    return True


def apply_move(board, m):
    nb = [row[:] for row in board]
    x1, y1, x2, y2 = m
    nb[y2][x2] = nb[y1][x1]
    nb[y1][x1] = "."
    return nb


def king_alive(board, red):
    target = "K" if red else "k"
    for row in board:
        if target in row:
            return True
    return False


# ---------- 评估 ----------
def evaluate(board):
    """红方为正"""
    score = 0
    for y in range(BOARD_H):
        for x in range(BOARD_W):
            p = board[y][x]
            if p == ".":
                continue
            v = PIECE_VALUES.get(p, 0)
            # 简单位置分：兵过河+15
            if p == "P" and y <= 4:
                v += 15
            elif p == "p" and y >= 5:
                v += 15
            score += v if is_red(p) else -v
    return score


# ---------- Alpha-Beta ----------
def search(board, depth, red, alpha=-1e9, beta=1e9):
    if depth == 0 or not king_alive(board, True) or not king_alive(board, False):
        return evaluate(board), None

    moves = gen_moves(board, red)
    if not moves:
        return evaluate(board), None

    best_move = None
    if red:
        best = -1e9
        for m in moves:
            nb = apply_move(board, m)
            v, _ = search(nb, depth - 1, False, alpha, beta)
            if v > best:
                best = v
                best_move = m
            alpha = max(alpha, best)
            if alpha >= beta:
                break
        return best, best_move
    else:
        best = 1e9
        for m in moves:
            nb = apply_move(board, m)
            v, _ = search(nb, depth - 1, True, alpha, beta)
            if v < best:
                best = v
                best_move = m
            beta = min(beta, best)
            if alpha >= beta:
                break
        return best, best_move


# ---------- 显示 ----------
PIECE_CHARS = {
    "R": "車", "N": "馬", "B": "相", "A": "仕", "K": "帥", "C": "炮", "P": "兵",
    "r": "车", "n": "马", "b": "象", "a": "士", "k": "将", "c": "砲", "p": "卒",
    ".": "·",
}


def print_board(board):
    print("  " + " ".join(str(i) for i in range(BOARD_W)))
    for y, row in enumerate(board):
        print(f"{y} " + " ".join(PIECE_CHARS[p] for p in row))


def move_str(m):
    return f"({m[0]},{m[1]}) -> ({m[2]},{m[3]})"


def demo():
    board = [row[:] for row in INIT_BOARD]
    print("=" * 50)
    print("中国象棋 AI 演示（红方 vs 黑方，AI 自我对弈）")
    print("=" * 50)
    print("\n初始棋盘：")
    print_board(board)

    red_turn = True
    for step in range(8):
        score, move = search(board, depth=2, red=red_turn)
        if not move:
            print(f"\n第{step+1}步: {'红方' if red_turn else '黑方'} 无棋可走")
            break
        x1, y1, x2, y2 = move
        piece = board[y1][x1]
        captured = board[y2][x2]
        board = apply_move(board, move)
        side = "红方" if red_turn else "黑方"
        cap_msg = f" 吃 {PIECE_CHARS[captured]}" if captured != "." else ""
        print(f"\n第{step+1}步 {side}: {PIECE_CHARS[piece]} {move_str(move)}{cap_msg}  评分={score}")
        print_board(board)
        if not king_alive(board, red_turn):
            print(f"\n{'红' if red_turn else '黑'}方失去主将，{'黑' if red_turn else '红'}方胜！")
            break
        red_turn = not red_turn
    print("\n演示结束。")


if __name__ == "__main__":
    demo()
