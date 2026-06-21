# -*- coding: utf-8 -*-
"""
图形界面计算器（tkinter）
- 纯 Python 标准库实现
- 支持 + - * / ( ) . 以及小数运算
- 支持清空 (C)、退格 (←)、求值 (=)
"""
import tkinter as tk
from tkinter import messagebox


class Calculator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("计算器")
        self.resizable(False, False)
        self.configure(bg="#222")

        self.expression = tk.StringVar(value="")

        self._build_ui()

    def _build_ui(self):
        # 显示屏
        display = tk.Entry(
            self,
            textvariable=self.expression,
            font=("Consolas", 22),
            bd=0,
            justify="right",
            bg="#111",
            fg="#0f0",
            insertbackground="#0f0",
        )
        display.grid(row=0, column=0, columnspan=4, sticky="nsew", padx=8, pady=10, ipady=10)

        buttons = [
            ("C", 1, 0), ("(", 1, 1), (")", 1, 2), ("/", 1, 3),
            ("7", 2, 0), ("8", 2, 1), ("9", 2, 2), ("*", 2, 3),
            ("4", 3, 0), ("5", 3, 1), ("6", 3, 2), ("-", 3, 3),
            ("1", 4, 0), ("2", 4, 1), ("3", 4, 2), ("+", 4, 3),
            ("←", 5, 0), ("0", 5, 1), (".", 5, 2), ("=", 5, 3),
        ]

        for (text, r, c) in buttons:
            if text == "=":
                bg, fg = "#ff8800", "#fff"
            elif text in "+-*/()":
                bg, fg = "#444", "#fff"
            elif text in ("C", "←"):
                bg, fg = "#a33", "#fff"
            else:
                bg, fg = "#666", "#fff"

            btn = tk.Button(
                self,
                text=text,
                font=("Microsoft YaHei", 14, "bold"),
                bg=bg,
                fg=fg,
                bd=0,
                width=4,
                height=2,
                activebackground="#888",
                command=lambda t=text: self.on_click(t),
            )
            btn.grid(row=r, column=c, padx=4, pady=4, sticky="nsew")

        for i in range(4):
            self.grid_columnconfigure(i, weight=1)

        # 键盘绑定
        self.bind("<Key>", self.on_key)

    def on_click(self, text):
        if text == "C":
            self.expression.set("")
        elif text == "←":
            self.expression.set(self.expression.get()[:-1])
        elif text == "=":
            self.calculate()
        else:
            self.expression.set(self.expression.get() + text)

    def on_key(self, event):
        if event.keysym == "Return":
            self.calculate()
        elif event.keysym == "BackSpace":
            self.expression.set(self.expression.get()[:-1])
        elif event.keysym == "Escape":
            self.expression.set("")
        elif event.char in "0123456789+-*/().":
            self.expression.set(self.expression.get() + event.char)

    def calculate(self):
        expr = self.expression.get().strip()
        if not expr:
            return
        # 仅允许安全字符
        allowed = set("0123456789+-*/(). ")
        if any(ch not in allowed for ch in expr):
            messagebox.showerror("错误", "包含非法字符")
            return
        try:
            # 使用受限的 eval
            result = eval(expr, {"__builtins__": {}}, {})
            self.expression.set(str(result))
        except ZeroDivisionError:
            messagebox.showerror("错误", "除数不能为 0")
        except Exception as e:
            messagebox.showerror("错误", f"表达式错误: {e}")


if __name__ == "__main__":
    Calculator().mainloop()
