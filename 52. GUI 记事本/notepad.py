# -*- coding: utf-8 -*-
"""
GUI 记事本
- tkinter 实现
- 功能：新建、打开、保存、另存为、退出、撤销、重做、查找
"""
import os
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog


class Notepad(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("记事本 - 未命名")
        self.geometry("800x600")
        self.file_path = None

        self._build_menu()
        self._build_text()
        self._build_status()

        self.protocol("WM_DELETE_WINDOW", self.on_exit)

    def _build_menu(self):
        menubar = tk.Menu(self)

        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="新建", accelerator="Ctrl+N", command=self.new_file)
        file_menu.add_command(label="打开...", accelerator="Ctrl+O", command=self.open_file)
        file_menu.add_command(label="保存", accelerator="Ctrl+S", command=self.save_file)
        file_menu.add_command(label="另存为...", accelerator="Ctrl+Shift+S", command=self.save_as)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.on_exit)
        menubar.add_cascade(label="文件", menu=file_menu)

        edit_menu = tk.Menu(menubar, tearoff=False)
        edit_menu.add_command(label="撤销", accelerator="Ctrl+Z", command=lambda: self.text.event_generate("<<Undo>>"))
        edit_menu.add_command(label="重做", accelerator="Ctrl+Y", command=lambda: self.text.event_generate("<<Redo>>"))
        edit_menu.add_separator()
        edit_menu.add_command(label="剪切", command=lambda: self.text.event_generate("<<Cut>>"))
        edit_menu.add_command(label="复制", command=lambda: self.text.event_generate("<<Copy>>"))
        edit_menu.add_command(label="粘贴", command=lambda: self.text.event_generate("<<Paste>>"))
        edit_menu.add_separator()
        edit_menu.add_command(label="查找...", accelerator="Ctrl+F", command=self.find_text)
        menubar.add_cascade(label="编辑", menu=edit_menu)

        about_menu = tk.Menu(menubar, tearoff=False)
        about_menu.add_command(label="关于", command=lambda: messagebox.showinfo("关于", "Tkinter 记事本 Demo"))
        menubar.add_cascade(label="帮助", menu=about_menu)

        self.config(menu=menubar)

        # 快捷键
        self.bind_all("<Control-n>", lambda e: self.new_file())
        self.bind_all("<Control-o>", lambda e: self.open_file())
        self.bind_all("<Control-s>", lambda e: self.save_file())
        self.bind_all("<Control-Shift-S>", lambda e: self.save_as())
        self.bind_all("<Control-f>", lambda e: self.find_text())

    def _build_text(self):
        frame = tk.Frame(self)
        frame.pack(fill="both", expand=True)
        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side="right", fill="y")

        self.text = tk.Text(frame, undo=True, wrap="word", font=("Consolas", 12),
                            yscrollcommand=scrollbar.set)
        self.text.pack(fill="both", expand=True)
        scrollbar.config(command=self.text.yview)

        self.text.bind("<KeyRelease>", lambda e: self.update_status())

    def _build_status(self):
        self.status = tk.Label(self, text="行: 1  列: 1", anchor="e", bd=1, relief="sunken")
        self.status.pack(side="bottom", fill="x")

    def update_status(self):
        line, col = self.text.index("insert").split(".")
        self.status.config(text=f"行: {line}  列: {int(col)+1}")

    # ---- 文件操作 ----
    def new_file(self):
        if self._maybe_save():
            self.text.delete("1.0", "end")
            self.file_path = None
            self.title("记事本 - 未命名")

    def open_file(self):
        if not self._maybe_save():
            return
        path = filedialog.askopenfilename(filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(path, "r", encoding="gbk", errors="ignore") as f:
                content = f.read()
        self.text.delete("1.0", "end")
        self.text.insert("1.0", content)
        self.file_path = path
        self.title(f"记事本 - {os.path.basename(path)}")

    def save_file(self):
        if self.file_path is None:
            return self.save_as()
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                f.write(self.text.get("1.0", "end-1c"))
            return True
        except Exception as e:
            messagebox.showerror("保存失败", str(e))
            return False

    def save_as(self):
        path = filedialog.asksaveasfilename(defaultextension=".txt",
                                            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")])
        if not path:
            return False
        self.file_path = path
        self.title(f"记事本 - {os.path.basename(path)}")
        return self.save_file()

    def _maybe_save(self):
        if self.text.edit_modified():
            ans = messagebox.askyesnocancel("提示", "当前文件已修改，是否保存？")
            if ans is None:
                return False
            if ans:
                if not self.save_file():
                    return False
            self.text.edit_modified(False)
        return True

    def find_text(self):
        target = simpledialog.askstring("查找", "输入要查找的文本：")
        if not target:
            return
        self.text.tag_remove("find", "1.0", "end")
        idx = "1.0"
        count = 0
        while True:
            idx = self.text.search(target, idx, nocase=True, stopindex="end")
            if not idx:
                break
            end_idx = f"{idx}+{len(target)}c"
            self.text.tag_add("find", idx, end_idx)
            idx = end_idx
            count += 1
        self.text.tag_config("find", background="yellow", foreground="black")
        messagebox.showinfo("查找", f"共找到 {count} 处")

    def on_exit(self):
        if self._maybe_save():
            self.destroy()


if __name__ == "__main__":
    Notepad().mainloop()
