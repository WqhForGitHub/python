# -*- coding: utf-8 -*-
"""
GUI 文件管理器
- tkinter 实现
- 树形显示目录、双击进入、返回上级
- 显示文件大小、修改时间
- 支持新建文件夹、删除、重命名、刷新
- 双击文件用系统默认程序打开
"""
import os
import shutil
import time
import subprocess
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog


def human_size(n):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


class FileManager(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("文件管理器")
        self.geometry("900x600")

        self.cur_path = tk.StringVar(value=os.path.expanduser("~"))

        self._build_toolbar()
        self._build_tree()
        self._build_status()

        self.refresh()

    def _build_toolbar(self):
        bar = tk.Frame(self)
        bar.pack(side="top", fill="x", padx=4, pady=4)

        tk.Button(bar, text="⬆ 上级", command=self.go_up).pack(side="left", padx=2)
        tk.Button(bar, text="🔄 刷新", command=self.refresh).pack(side="left", padx=2)
        tk.Button(bar, text="📁 新建文件夹", command=self.new_folder).pack(side="left", padx=2)
        tk.Button(bar, text="✏ 重命名", command=self.rename).pack(side="left", padx=2)
        tk.Button(bar, text="🗑 删除", command=self.delete).pack(side="left", padx=2)
        tk.Button(bar, text="📋 复制路径", command=self.copy_path).pack(side="left", padx=2)

        entry = tk.Entry(bar, textvariable=self.cur_path)
        entry.pack(side="left", fill="x", expand=True, padx=4)
        entry.bind("<Return>", lambda e: self.refresh())

        tk.Button(bar, text="转到", command=self.refresh).pack(side="left", padx=2)
        tk.Button(bar, text="选目录", command=self.choose_dir).pack(side="left", padx=2)

    def _build_tree(self):
        cols = ("name", "size", "mtime", "type")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", selectmode="browse")
        self.tree.heading("name", text="名称")
        self.tree.heading("size", text="大小")
        self.tree.heading("mtime", text="修改时间")
        self.tree.heading("type", text="类型")
        self.tree.column("name", width=380)
        self.tree.column("size", width=100, anchor="e")
        self.tree.column("mtime", width=180)
        self.tree.column("type", width=100)

        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.tree.bind("<Double-1>", self.on_double)

    def _build_status(self):
        self.status = tk.Label(self, text="", anchor="w", bd=1, relief="sunken")
        self.status.pack(side="bottom", fill="x")

    # ---- 操作 ----
    def refresh(self):
        path = self.cur_path.get()
        if not os.path.isdir(path):
            messagebox.showerror("错误", f"路径无效：{path}")
            return
        for i in self.tree.get_children():
            self.tree.delete(i)

        try:
            entries = os.listdir(path)
        except PermissionError:
            messagebox.showerror("错误", "无访问权限")
            return

        # 先目录后文件
        dirs, files = [], []
        for name in entries:
            full = os.path.join(path, name)
            if os.path.isdir(full):
                dirs.append(name)
            else:
                files.append(name)
        dirs.sort()
        files.sort()

        count = 0
        for name in dirs + files:
            full = os.path.join(path, name)
            try:
                st = os.stat(full)
                size = "<DIR>" if os.path.isdir(full) else human_size(st.st_size)
                mtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st.st_mtime))
                tp = "文件夹" if os.path.isdir(full) else (os.path.splitext(name)[1] or "文件")
                self.tree.insert("", "end", values=(name, size, mtime, tp))
                count += 1
            except OSError:
                continue

        self.status.config(text=f"{path}  共 {count} 项")
        self.title(f"文件管理器 - {path}")

    def go_up(self):
        path = self.cur_path.get()
        parent = os.path.dirname(path.rstrip(os.sep))
        if parent and parent != path:
            self.cur_path.set(parent)
            self.refresh()

    def selected_path(self):
        sel = self.tree.selection()
        if not sel:
            return None
        name = self.tree.item(sel[0], "values")[0]
        return os.path.join(self.cur_path.get(), name)

    def on_double(self, event):
        full = self.selected_path()
        if not full:
            return
        if os.path.isdir(full):
            self.cur_path.set(full)
            self.refresh()
        else:
            try:
                if sys.platform.startswith("win"):
                    os.startfile(full)
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", full])
                else:
                    subprocess.Popen(["xdg-open", full])
            except Exception as e:
                messagebox.showerror("打开失败", str(e))

    def new_folder(self):
        name = simpledialog.askstring("新建文件夹", "名称：")
        if not name:
            return
        try:
            os.makedirs(os.path.join(self.cur_path.get(), name))
            self.refresh()
        except Exception as e:
            messagebox.showerror("失败", str(e))

    def rename(self):
        full = self.selected_path()
        if not full:
            return
        old = os.path.basename(full)
        new = simpledialog.askstring("重命名", "新名称：", initialvalue=old)
        if not new or new == old:
            return
        try:
            os.rename(full, os.path.join(os.path.dirname(full), new))
            self.refresh()
        except Exception as e:
            messagebox.showerror("失败", str(e))

    def delete(self):
        full = self.selected_path()
        if not full:
            return
        if not messagebox.askyesno("确认", f"确定删除：{full} ?"):
            return
        try:
            if os.path.isdir(full):
                shutil.rmtree(full)
            else:
                os.remove(full)
            self.refresh()
        except Exception as e:
            messagebox.showerror("失败", str(e))

    def copy_path(self):
        full = self.selected_path() or self.cur_path.get()
        self.clipboard_clear()
        self.clipboard_append(full)
        self.status.config(text=f"已复制路径：{full}")

    def choose_dir(self):
        d = filedialog.askdirectory(initialdir=self.cur_path.get())
        if d:
            self.cur_path.set(d)
            self.refresh()


if __name__ == "__main__":
    FileManager().mainloop()
