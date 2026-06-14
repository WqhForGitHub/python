"""
PyVim - 纯 Python 标准库实现的 Vim 风格终端文本编辑器
======================================================

仅依赖 `curses` (Linux/macOS 自带；Windows 需 `pip install windows-curses`)。

支持的核心特性
----------------
- 模式：NORMAL / INSERT / VISUAL / COMMAND
- 移动：h j k l  w b e  0 $  gg G  Ctrl-d Ctrl-u
- 编辑：i a o O x dd dw yy p P u（撤销）Ctrl-r（重做）
- 搜索：/pattern  n  N
- 替换：:%s/old/new/g
- 命令行：:w :q :wq :q! :e file :set number :set nonumber
- 可视模式：v 选择 -> y 复制 / d 删除
- 行号、状态栏、颜色高亮（搜索结果）

用法
----
    python pyvim.py [文件名]

按 i 进入插入模式，Esc 回到 NORMAL，:wq 保存退出。
"""

from __future__ import annotations

import curses
import os
import re
import sys
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path


# ----------------------------------------------------------------------------
# 编辑器状态
# ----------------------------------------------------------------------------
@dataclass
class Buffer:
    lines: list[str] = field(default_factory=lambda: [""])
    filename: str | None = None
    dirty: bool = False
    cy: int = 0           # 光标行
    cx: int = 0           # 光标列
    top: int = 0          # 可见区域起始行
    left: int = 0         # 横向滚动列
    last_search: str = ""
    show_lineno: bool = True
    yanked: list[str] = field(default_factory=list)
    yanked_linewise: bool = True

    def load(self, path: str):
        self.filename = path
        if Path(path).exists():
            text = Path(path).read_text(encoding="utf-8", errors="replace")
            self.lines = text.split("\n") or [""]
            if self.lines[-1] == "" and len(self.lines) > 1:
                # 保留最后一行（避免末尾换行带来空行）
                pass
        else:
            self.lines = [""]
        self.dirty = False
        self.cy = self.cx = self.top = self.left = 0

    def save(self) -> int:
        if not self.filename:
            return -1
        text = "\n".join(self.lines)
        Path(self.filename).write_text(text, encoding="utf-8")
        self.dirty = False
        return len(text)


class History:
    """简单的撤销/重做：每次「修改」前 push 整个 lines 快照。"""
    def __init__(self):
        self.undo: list[tuple[list[str], int, int]] = []
        self.redo: list[tuple[list[str], int, int]] = []

    def push(self, buf: Buffer):
        self.undo.append((deepcopy(buf.lines), buf.cy, buf.cx))
        self.redo.clear()

    def do_undo(self, buf: Buffer):
        if not self.undo:
            return
        self.redo.append((deepcopy(buf.lines), buf.cy, buf.cx))
        lines, cy, cx = self.undo.pop()
        buf.lines, buf.cy, buf.cx = lines, cy, cx

    def do_redo(self, buf: Buffer):
        if not self.redo:
            return
        self.undo.append((deepcopy(buf.lines), buf.cy, buf.cx))
        lines, cy, cx = self.redo.pop()
        buf.lines, buf.cy, buf.cx = lines, cy, cx


# ----------------------------------------------------------------------------
# 主编辑器
# ----------------------------------------------------------------------------
NORMAL, INSERT, VISUAL, COMMAND = "NORMAL", "INSERT", "VISUAL", "COMMAND"


class Editor:
    def __init__(self, stdscr, filename: str | None = None):
        self.scr = stdscr
        self.buf = Buffer()
        self.hist = History()
        self.mode = NORMAL
        self.cmdline = ""
        self.message = "PyVim - press : for commands, i to insert, /search, :wq to save+quit"
        self.visual_anchor: tuple[int, int] | None = None
        self.pending = ""             # multi-key 等待 (gg / dd / yy / dw)
        self.search_hits: list[tuple[int, int, int]] = []  # (line, start, end)
        if filename:
            self.buf.load(filename)
        self._init_curses()

    def _init_curses(self):
        curses.curs_set(1)
        self.scr.keypad(True)
        try:
            curses.start_color()
            curses.use_default_colors()
            curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_YELLOW)  # search
            curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLUE)    # status
            curses.init_pair(3, curses.COLOR_CYAN, -1)                     # lineno
            curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_CYAN)    # visual
        except curses.error:
            pass

    # ------------------------------------------------------------------ draw
    def draw(self):
        self.scr.erase()
        h, w = self.scr.getmaxyx()
        edit_h = h - 2  # status + cmdline

        gutter = (len(str(len(self.buf.lines))) + 1) if self.buf.show_lineno else 0
        body_w = w - gutter

        # 调整滚动
        if self.buf.cy < self.buf.top:
            self.buf.top = self.buf.cy
        if self.buf.cy >= self.buf.top + edit_h:
            self.buf.top = self.buf.cy - edit_h + 1
        if self.buf.cx < self.buf.left:
            self.buf.left = self.buf.cx
        if self.buf.cx >= self.buf.left + body_w:
            self.buf.left = self.buf.cx - body_w + 1

        # 文本
        for i in range(edit_h):
            ln = self.buf.top + i
            if ln >= len(self.buf.lines):
                self.scr.addstr(i, 0, "~", curses.color_pair(3))
                continue
            if self.buf.show_lineno:
                num = f"{ln + 1:>{gutter - 1}} "
                self.scr.addstr(i, 0, num, curses.color_pair(3))
            line = self.buf.lines[ln]
            visible = line[self.buf.left:self.buf.left + body_w]
            try:
                self.scr.addstr(i, gutter, visible)
            except curses.error:
                pass
            # 高亮搜索结果
            for sln, s, e in self.search_hits:
                if sln != ln:
                    continue
                vs = max(s - self.buf.left, 0)
                ve = min(e - self.buf.left, body_w)
                if ve > vs:
                    try:
                        self.scr.addstr(i, gutter + vs, line[max(s, self.buf.left):
                                        min(e, self.buf.left + body_w)],
                                        curses.color_pair(1))
                    except curses.error:
                        pass
            # 高亮可视选区
            if self.mode == VISUAL and self.visual_anchor is not None:
                sel = self._visual_range()
                self._draw_visual(i, ln, sel, gutter, body_w, line)

        # 状态栏
        fname = self.buf.filename or "[No Name]"
        dirty = "[+]" if self.buf.dirty else ""
        status = f" {self.mode} | {fname} {dirty} | {self.buf.cy + 1}:{self.buf.cx + 1} "
        status = status.ljust(w)[:w]
        try:
            self.scr.addstr(h - 2, 0, status, curses.color_pair(2))
        except curses.error:
            pass

        # 命令行 / 消息
        if self.mode == COMMAND:
            line = ":" + self.cmdline
        else:
            line = self.message
        try:
            self.scr.addstr(h - 1, 0, line[:w - 1])
        except curses.error:
            pass

        # 光标定位
        if self.mode == COMMAND:
            self.scr.move(h - 1, min(len(self.cmdline) + 1, w - 1))
        else:
            cy_screen = self.buf.cy - self.buf.top
            cx_screen = self.buf.cx - self.buf.left + gutter
            try:
                self.scr.move(min(cy_screen, edit_h - 1),
                              min(cx_screen, w - 1))
            except curses.error:
                pass

        self.scr.refresh()

    def _visual_range(self) -> tuple[tuple[int, int], tuple[int, int]]:
        a = self.visual_anchor or (0, 0)
        b = (self.buf.cy, self.buf.cx)
        if a > b:
            a, b = b, a
        return a, b

    def _draw_visual(self, i, ln, sel, gutter, body_w, line):
        (sy, sx), (ey, ex) = sel
        if ln < sy or ln > ey:
            return
        s = sx if ln == sy else 0
        e = (ex + 1) if ln == ey else len(line)
        vs = max(s - self.buf.left, 0)
        ve = min(e - self.buf.left, body_w)
        if ve > vs:
            try:
                self.scr.addstr(i, gutter + vs,
                                line[max(s, self.buf.left):min(e, self.buf.left + body_w)],
                                curses.color_pair(4))
            except curses.error:
                pass

    # ------------------------------------------------------------- run loop
    def run(self):
        while True:
            self.draw()
            try:
                ch = self.scr.get_wch()
            except KeyboardInterrupt:
                continue
            except curses.error:
                continue
            if self.mode == COMMAND:
                if not self.handle_command(ch):
                    return
            elif self.mode == INSERT:
                self.handle_insert(ch)
            elif self.mode == VISUAL:
                self.handle_visual(ch)
            else:
                if not self.handle_normal(ch):
                    return

    # ------------------------------------------------------------- helpers
    def line(self) -> str:
        return self.buf.lines[self.buf.cy]

    def clamp(self):
        self.buf.cy = max(0, min(self.buf.cy, len(self.buf.lines) - 1))
        line = self.buf.lines[self.buf.cy]
        max_x = len(line) - 1 if self.mode != INSERT else len(line)
        self.buf.cx = max(0, min(self.buf.cx, max(0, max_x)))

    def msg(self, m: str):
        self.message = m

    # --------------------------------------------------------- NORMAL mode
    def handle_normal(self, ch) -> bool:
        self.message = ""

        if isinstance(ch, str):
            # 多键序列
            if self.pending:
                seq = self.pending + ch
                self.pending = ""
                self._handle_multikey(seq)
                return True
            if ch in ("g", "d", "y"):
                # 等下一键
                self.pending = ch
                # 但 G 单独是另一回事
                return True

            if ch == ":":
                self.mode = COMMAND
                self.cmdline = ""
            elif ch == "i":
                self.mode = INSERT
            elif ch == "I":
                self.buf.cx = 0
                self.mode = INSERT
            elif ch == "a":
                self.buf.cx = min(self.buf.cx + 1, len(self.line()))
                self.mode = INSERT
            elif ch == "A":
                self.buf.cx = len(self.line())
                self.mode = INSERT
            elif ch == "o":
                self.hist.push(self.buf)
                self.buf.lines.insert(self.buf.cy + 1, "")
                self.buf.cy += 1
                self.buf.cx = 0
                self.buf.dirty = True
                self.mode = INSERT
            elif ch == "O":
                self.hist.push(self.buf)
                self.buf.lines.insert(self.buf.cy, "")
                self.buf.cx = 0
                self.buf.dirty = True
                self.mode = INSERT
            elif ch == "x":
                self.hist.push(self.buf)
                line = self.line()
                if line:
                    self.buf.lines[self.buf.cy] = line[:self.buf.cx] + line[self.buf.cx + 1:]
                    self.buf.dirty = True
                    self.clamp()
            elif ch == "h":
                self.buf.cx = max(0, self.buf.cx - 1)
            elif ch == "l":
                self.buf.cx = min(len(self.line()) - 1, self.buf.cx + 1)
                self.buf.cx = max(0, self.buf.cx)
            elif ch == "j":
                self.buf.cy = min(len(self.buf.lines) - 1, self.buf.cy + 1)
                self.clamp()
            elif ch == "k":
                self.buf.cy = max(0, self.buf.cy - 1)
                self.clamp()
            elif ch == "0":
                self.buf.cx = 0
            elif ch == "$":
                self.buf.cx = max(0, len(self.line()) - 1)
            elif ch == "w":
                self._word_forward()
            elif ch == "b":
                self._word_back()
            elif ch == "e":
                self._word_end()
            elif ch == "G":
                self.buf.cy = len(self.buf.lines) - 1
                self.clamp()
            elif ch == "p":
                self._paste(after=True)
            elif ch == "P":
                self._paste(after=False)
            elif ch == "u":
                self.hist.do_undo(self.buf)
                self.clamp()
            elif ch == "v":
                self.mode = VISUAL
                self.visual_anchor = (self.buf.cy, self.buf.cx)
            elif ch == "/":
                self.mode = COMMAND
                self.cmdline = "/"
            elif ch == "n":
                self._next_search(forward=True)
            elif ch == "N":
                self._next_search(forward=False)
            elif ch == "\x12":  # Ctrl-R
                self.hist.do_redo(self.buf)
                self.clamp()
            elif ch == "\x04":  # Ctrl-D
                self.buf.cy = min(len(self.buf.lines) - 1, self.buf.cy + 10)
                self.clamp()
            elif ch == "\x15":  # Ctrl-U
                self.buf.cy = max(0, self.buf.cy - 10)
                self.clamp()
            elif ch == "\x1b":  # ESC
                pass
        return True

    def _handle_multikey(self, seq: str):
        if seq == "gg":
            self.buf.cy = 0
            self.clamp()
        elif seq == "dd":
            self.hist.push(self.buf)
            self.buf.yanked = [self.buf.lines.pop(self.buf.cy)]
            self.buf.yanked_linewise = True
            if not self.buf.lines:
                self.buf.lines = [""]
            self.buf.cy = min(self.buf.cy, len(self.buf.lines) - 1)
            self.buf.dirty = True
            self.clamp()
        elif seq == "yy":
            self.buf.yanked = [self.line()]
            self.buf.yanked_linewise = True
            self.msg("1 line yanked")
        elif seq == "dw":
            self.hist.push(self.buf)
            line = self.line()
            i = self.buf.cx
            n = len(line)
            while i < n and not line[i].isspace():
                i += 1
            while i < n and line[i].isspace():
                i += 1
            self.buf.lines[self.buf.cy] = line[:self.buf.cx] + line[i:]
            self.buf.dirty = True
            self.clamp()

    def _word_forward(self):
        line = self.line()
        i = self.buf.cx
        n = len(line)
        while i < n and not line[i].isspace():
            i += 1
        while i < n and line[i].isspace():
            i += 1
        if i >= n and self.buf.cy < len(self.buf.lines) - 1:
            self.buf.cy += 1
            self.buf.cx = 0
        else:
            self.buf.cx = min(i, max(0, n - 1))

    def _word_back(self):
        line = self.line()
        i = self.buf.cx - 1
        while i > 0 and line[i].isspace():
            i -= 1
        while i > 0 and not line[i - 1].isspace():
            i -= 1
        self.buf.cx = max(0, i)

    def _word_end(self):
        line = self.line()
        i = self.buf.cx + 1
        n = len(line)
        while i < n and line[i].isspace():
            i += 1
        while i < n - 1 and not line[i + 1].isspace():
            i += 1
        self.buf.cx = min(i, max(0, n - 1))

    def _paste(self, after: bool):
        if not self.buf.yanked:
            return
        self.hist.push(self.buf)
        if self.buf.yanked_linewise:
            ins = self.buf.cy + 1 if after else self.buf.cy
            for j, l in enumerate(self.buf.yanked):
                self.buf.lines.insert(ins + j, l)
            self.buf.cy = ins
            self.buf.cx = 0
        else:
            line = self.line()
            text = self.buf.yanked[0]
            pos = self.buf.cx + 1 if after else self.buf.cx
            self.buf.lines[self.buf.cy] = line[:pos] + text + line[pos:]
            self.buf.cx = pos + len(text) - 1
        self.buf.dirty = True
        self.clamp()

    # --------------------------------------------------------- INSERT mode
    def handle_insert(self, ch):
        if isinstance(ch, str):
            if ch == "\x1b":  # ESC
                self.mode = NORMAL
                self.buf.cx = max(0, self.buf.cx - 1)
                self.clamp()
                return
            if ch in ("\n", "\r"):
                self.hist.push(self.buf)
                line = self.line()
                self.buf.lines[self.buf.cy] = line[:self.buf.cx]
                self.buf.lines.insert(self.buf.cy + 1, line[self.buf.cx:])
                self.buf.cy += 1
                self.buf.cx = 0
                self.buf.dirty = True
                return
            if ch in ("\b", "\x7f", "\x08"):
                self.hist.push(self.buf)
                if self.buf.cx > 0:
                    line = self.line()
                    self.buf.lines[self.buf.cy] = line[:self.buf.cx - 1] + line[self.buf.cx:]
                    self.buf.cx -= 1
                elif self.buf.cy > 0:
                    prev = self.buf.lines[self.buf.cy - 1]
                    self.buf.cx = len(prev)
                    self.buf.lines[self.buf.cy - 1] = prev + self.buf.lines.pop(self.buf.cy)
                    self.buf.cy -= 1
                self.buf.dirty = True
                return
            if ch == "\t":
                ch = "    "
            if ch.isprintable() or ch == " ":
                self.hist.push(self.buf)
                line = self.line()
                self.buf.lines[self.buf.cy] = line[:self.buf.cx] + ch + line[self.buf.cx:]
                self.buf.cx += len(ch)
                self.buf.dirty = True
                return
        else:
            # 方向键
            if ch == curses.KEY_LEFT:
                self.buf.cx = max(0, self.buf.cx - 1)
            elif ch == curses.KEY_RIGHT:
                self.buf.cx = min(len(self.line()), self.buf.cx + 1)
            elif ch == curses.KEY_UP:
                self.buf.cy = max(0, self.buf.cy - 1)
                self.clamp()
            elif ch == curses.KEY_DOWN:
                self.buf.cy = min(len(self.buf.lines) - 1, self.buf.cy + 1)
                self.clamp()
            elif ch == curses.KEY_BACKSPACE:
                self.handle_insert("\b")

    # --------------------------------------------------------- VISUAL mode
    def handle_visual(self, ch):
        if isinstance(ch, str):
            if ch == "\x1b":
                self.mode = NORMAL
                self.visual_anchor = None
                return
            if ch in "hjkl0$wbeG":
                self.handle_normal(ch)
                return
            if ch == "y":
                self._visual_yank(delete=False)
            elif ch == "d" or ch == "x":
                self._visual_yank(delete=True)
            self.mode = NORMAL
            self.visual_anchor = None

    def _visual_yank(self, delete: bool):
        (sy, sx), (ey, ex) = self._visual_range()
        if sy == ey:
            line = self.buf.lines[sy]
            self.buf.yanked = [line[sx:ex + 1]]
            self.buf.yanked_linewise = False
            if delete:
                self.hist.push(self.buf)
                self.buf.lines[sy] = line[:sx] + line[ex + 1:]
                self.buf.cy, self.buf.cx = sy, sx
                self.buf.dirty = True
        else:
            chunks = [self.buf.lines[sy][sx:]]
            for ln in range(sy + 1, ey):
                chunks.append(self.buf.lines[ln])
            chunks.append(self.buf.lines[ey][:ex + 1])
            self.buf.yanked = chunks
            self.buf.yanked_linewise = False
            if delete:
                self.hist.push(self.buf)
                first = self.buf.lines[sy][:sx]
                last = self.buf.lines[ey][ex + 1:]
                self.buf.lines[sy:ey + 1] = [first + last]
                self.buf.cy, self.buf.cx = sy, sx
                self.buf.dirty = True
        self.clamp()

    # --------------------------------------------------------- COMMAND
    def handle_command(self, ch) -> bool:
        if isinstance(ch, str):
            if ch == "\x1b":
                self.mode = NORMAL
                self.cmdline = ""
                return True
            if ch in ("\n", "\r"):
                cmd = self.cmdline
                self.cmdline = ""
                self.mode = NORMAL
                return self.exec_command(cmd)
            if ch in ("\b", "\x7f", "\x08"):
                self.cmdline = self.cmdline[:-1]
                if not self.cmdline:
                    self.mode = NORMAL
                return True
            if ch.isprintable():
                self.cmdline += ch
        return True

    def exec_command(self, cmd: str) -> bool:
        if cmd.startswith("/"):
            return self._do_search(cmd[1:])
        # :%s/old/new/g
        m = re.match(r"%s/(.*)/(.*)/(g?)$", cmd)
        if m:
            return self._do_replace_all(m.group(1), m.group(2), bool(m.group(3)))

        parts = cmd.split()
        if not parts:
            return True
        head = parts[0]
        arg = " ".join(parts[1:])

        if head in ("q", "quit"):
            if self.buf.dirty:
                self.msg("E37: No write since last change (use :q!)")
                return True
            return False
        if head == "q!":
            return False
        if head in ("w", "write"):
            if arg:
                self.buf.filename = arg
            n = self.buf.save()
            if n < 0:
                self.msg("E32: No file name")
            else:
                self.msg(f'"{self.buf.filename}" {len(self.buf.lines)}L, {n}B written')
            return True
        if head in ("wq", "x"):
            self.buf.save()
            return False
        if head in ("e", "edit"):
            if arg:
                self.buf.load(arg)
                self.msg(f"loaded {arg}")
            return True
        if head == "set":
            if arg == "number":
                self.buf.show_lineno = True
            elif arg == "nonumber":
                self.buf.show_lineno = False
            return True
        if head.isdigit():
            self.buf.cy = max(0, min(len(self.buf.lines) - 1, int(head) - 1))
            self.clamp()
            return True

        self.msg(f"E492: Not an editor command: {cmd}")
        return True

    def _do_search(self, pat: str) -> bool:
        if not pat:
            pat = self.buf.last_search
        if not pat:
            return True
        self.buf.last_search = pat
        self._refresh_search()
        if self.search_hits:
            # 跳到光标后的第一个
            for ln, s, e in self.search_hits:
                if (ln, s) >= (self.buf.cy, self.buf.cx):
                    self.buf.cy, self.buf.cx = ln, s
                    break
            else:
                ln, s, _ = self.search_hits[0]
                self.buf.cy, self.buf.cx = ln, s
            self.clamp()
        else:
            self.msg(f"E486: Pattern not found: {pat}")
        return True

    def _refresh_search(self):
        self.search_hits = []
        if not self.buf.last_search:
            return
        try:
            rx = re.compile(self.buf.last_search)
        except re.error:
            return
        for i, line in enumerate(self.buf.lines):
            for m in rx.finditer(line):
                if m.start() == m.end():
                    continue
                self.search_hits.append((i, m.start(), m.end()))

    def _next_search(self, forward: bool):
        if not self.search_hits:
            return
        cur = (self.buf.cy, self.buf.cx)
        if forward:
            for ln, s, _ in self.search_hits:
                if (ln, s) > cur:
                    self.buf.cy, self.buf.cx = ln, s
                    break
            else:
                ln, s, _ = self.search_hits[0]
                self.buf.cy, self.buf.cx = ln, s
        else:
            prev = None
            for ln, s, _ in self.search_hits:
                if (ln, s) >= cur:
                    break
                prev = (ln, s)
            if prev is None:
                ln, s, _ = self.search_hits[-1]
                self.buf.cy, self.buf.cx = ln, s
            else:
                self.buf.cy, self.buf.cx = prev
        self.clamp()

    def _do_replace_all(self, pat: str, rep: str, global_: bool) -> bool:
        try:
            rx = re.compile(pat)
        except re.error as e:
            self.msg(f"E33: regex: {e}")
            return True
        self.hist.push(self.buf)
        n = 0
        for i, line in enumerate(self.buf.lines):
            count = 0 if global_ else 1
            new, k = rx.subn(rep, line, count=count)
            if k:
                self.buf.lines[i] = new
                n += k
        if n:
            self.buf.dirty = True
        self.msg(f"{n} substitution(s)")
        return True


# ----------------------------------------------------------------------------
# entry
# ----------------------------------------------------------------------------
def main():
    filename = sys.argv[1] if len(sys.argv) > 1 else None

    def _wrap(stdscr):
        ed = Editor(stdscr, filename)
        ed.run()

    # 在 Windows 下 curses 需要 windows-curses
    try:
        curses.wrapper(_wrap)
    except curses.error as e:
        print(f"curses error: {e}", file=sys.stderr)
        if os.name == "nt":
            print("Windows users: pip install windows-curses", file=sys.stderr)


if __name__ == "__main__":
    main()
